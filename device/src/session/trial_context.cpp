#include "session/trial_context.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace {
    constexpr double kNaN = std::numeric_limits<double>::quiet_NaN();

    size_t index(Input input) {
        return static_cast<size_t>(input);
    }

    size_t index(Output output) {
        return static_cast<size_t>(output);
    }

    const char* sideName(DisplaySide side) {
        switch (side) {
            case DisplaySide::Left:
                return "left";
            case DisplaySide::Right:
                return "right";
            case DisplaySide::Both:
                break;
        }
        return "both";
    }
}

bool Statistics::operator==(const Statistics& other) const {
    return n_trials == other.n_trials && n_correct_trials == other.n_correct_trials &&
           n_nose_pokes == other.n_nose_pokes && n_left_lever_presses == other.n_left_lever_presses &&
           n_right_lever_presses == other.n_right_lever_presses && n_rewards == other.n_rewards;
}

TrialContext::TrialContext(Gpio& gpio, DisplayManager& displays, Statistics& statistics)
    : gpio_(gpio), displays_(displays), statistics_(statistics) {}

bool TrialContext::pressed(Input input) const {
    return inputs_[index(input)] && !previousInputs_[index(input)];
}

bool TrialContext::released(Input input) const {
    return !inputs_[index(input)] && previousInputs_[index(input)];
}

bool TrialContext::held(Input input) const {
    return inputs_[index(input)];
}

bool TrialContext::anyLeverPressed() const {
    return pressed(Input::LeftLever) || pressed(Input::RightLever);
}

void TrialContext::setOutput(Output output, bool on) {
    // A manual change overrides any pulse in progress
    pulseEnds_[index(output)].reset();
    gpio_.write(output, on);
    recordOutputs();
}

void TrialContext::pulse(Output output, Milliseconds duration) {
    gpio_.write(output, true);
    pulseEnds_[index(output)] = Clock::now() + duration;
    recordOutputs();
}

bool TrialContext::pulsing(Output output) const {
    return pulseEnds_[index(output)].has_value();
}

void TrialContext::showImage(DisplaySide side, const std::string& image) {
    displays_.showImage(side, image);
    recordStimulus(side, {{"action", "image"}, {"image", image}});
}

void TrialContext::fillDisplay(DisplaySide side, SDL_Color color) {
    displays_.fill(side, color);
    recordStimulus(side, {{"action", "fill"}, {"color", {color.r, color.g, color.b, color.a}}});
}

void TrialContext::clearDisplays(DisplaySide side) {
    displays_.clearStimuli(side);
    recordStimulus(side, {{"action", "clear"}});
}

void TrialContext::enterState(const std::string& state) {
    const double now = trialTime();
    if (!record_.states.empty() && std::isnan(record_.states.back().second[1])) {
        record_.states.back().second[1] = now;
    }
    record_.states.push_back({state, {now, kNaN}});
}

void TrialContext::goCue() {
    if (!record_.goCueTime) {
        record_.goCueTime = sessionTime();
    }
    record_.events["go_cue"].push_back(trialTime());
}

void TrialContext::respond(Choice choice) {
    if (!record_.responseTime) {
        record_.responseTime = sessionTime();
        record_.choice = static_cast<int>(choice);
    }
}

void TrialContext::deliverWater() {
    pulse(Output::WaterValve, Milliseconds(parameters().valve_open_ms));
    statistics_.n_rewards++;
    record_.rewardValveTime += parameters().valve_open_ms / 1000.0;
    if (!record_.feedbackType) {
        record_.feedbackTime = sessionTime();
        record_.feedbackType = 1;
    }
}

bool TrialContext::waterFlowing() const {
    return pulsing(Output::WaterValve);
}

void TrialContext::errorFeedback() {
    if (!record_.feedbackType) {
        record_.feedbackTime = sessionTime();
        record_.feedbackType = -1;
    }
    record_.events["error_feedback"].push_back(trialTime());
}

Milliseconds TrialContext::elapsed() const {
    return std::chrono::duration_cast<Milliseconds>(Clock::now() - startedAt_);
}

Milliseconds TrialContext::randomDuration(int minimumMs, int maximumMs) {
    std::uniform_int_distribution<int> distribution(minimumMs, std::max(minimumMs, maximumMs));
    return Milliseconds(distribution(random_));
}

void TrialContext::begin(const TimelineItem& item, int trialNum, int itemRepetition, Clock::time_point sessionStart) {
    reset();
    item_ = &item;
    sessionStart_ = sessionStart;
    startedAt_ = Clock::now();
    completed_ = false;

    record_ = {};
    record_.trialNum = trialNum;
    record_.itemId = item.id;
    record_.itemRepetition = itemRepetition;
    record_.type = item.type;
    record_.stage = item.stage;
    record_.parameters = item.parameters;
    record_.startTime = sessionTime();
    // Training trials without a response are no-go trials, intervals have no choice to make
    if (item.type == TrialType::Training) {
        record_.choice = static_cast<int>(Choice::NoGo);
    }

    // Outputs were just switched off, so start tracking from their current state
    for (size_t i = 0; i < kOutputCount; i++) {
        outputs_[i] = gpio_.state(static_cast<Output>(i));
    }
}

void TrialContext::sample() {
    previousInputs_ = inputs_;
    for (size_t i = 0; i < kInputCount; i++) {
        inputs_[i] = gpio_.read(static_cast<Input>(i));
        if (inputs_[i] != previousInputs_[i]) {
            record_.events[std::string(kInputNames[i]) + (inputs_[i] ? "_on" : "_off")].push_back(trialTime());
        }
    }

    if (pressed(Input::NosePoke)) {
        statistics_.n_nose_pokes++;
        record_.nosePokes++;
    }
    if (pressed(Input::LeftLever)) {
        statistics_.n_left_lever_presses++;
        record_.leftLeverPresses++;
    }
    if (pressed(Input::RightLever)) {
        statistics_.n_right_lever_presses++;
        record_.rightLeverPresses++;
    }

    const auto now = Clock::now();
    for (size_t i = 0; i < kOutputCount; i++) {
        if (pulseEnds_[i] && now >= *pulseEnds_[i]) {
            pulseEnds_[i].reset();
            gpio_.write(static_cast<Output>(i), false);
        }
    }
    // Also catches outputs changed outside the trial, such as by hardware tests or simulator keys
    recordOutputs();
}

TrialRecord TrialContext::finish() {
    // Switch everything off first so those changes are recorded as part of this trial
    reset();
    recordOutputs();

    const double end = trialTime();
    if (!record_.states.empty() && std::isnan(record_.states.back().second[1])) {
        record_.states.back().second[1] = end;
    }
    record_.endTime = sessionTime();
    if (record_.stimOnTime && !record_.stimOffTime) {
        record_.stimOffTime = record_.endTime;
    }
    return std::move(record_);
}

void TrialContext::reset() {
    pulseEnds_.fill(std::nullopt);
    gpio_.resetOutputs();
    displays_.clearStimuli();
}

double TrialContext::sessionTime() const {
    return std::chrono::duration<double>(Clock::now() - sessionStart_).count();
}

double TrialContext::trialTime() const {
    return std::chrono::duration<double>(Clock::now() - startedAt_).count();
}

void TrialContext::recordOutputs() {
    for (size_t i = 0; i < kOutputCount; i++) {
        const bool on = gpio_.state(static_cast<Output>(i));
        if (on != outputs_[i]) {
            outputs_[i] = on;
            record_.events[std::string(kOutputNames[i]) + (on ? "_on" : "_off")].push_back(trialTime());
        }
    }
}

void TrialContext::recordStimulus(DisplaySide side, nlohmann::json stimulus) {
    const bool clearing = stimulus["action"] == "clear";
    if (!clearing && !record_.stimOnTime) {
        record_.stimOnTime = sessionTime();
    } else if (clearing && record_.stimOnTime && !record_.stimOffTime) {
        record_.stimOffTime = sessionTime();
    }

    stimulus["time"] = trialTime();
    stimulus["display"] = sideName(side);
    record_.stimuli.push_back(std::move(stimulus));
}
