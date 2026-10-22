#pragma once

#include <array>
#include <map>
#include <optional>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "display/display_manager.h"
#include "hardware/gpio.h"
#include "session/protocol.h"
#include "session/timer.h"

// Running totals for the active session, matching `SessionStatistics` in `dashboard/types/index.d.ts`
struct Statistics {
    int n_trials = 0;
    int n_correct_trials = 0;
    int n_nose_pokes = 0;
    int n_left_lever_presses = 0;
    int n_right_lever_presses = 0;
    int n_rewards = 0;

    bool operator==(const Statistics& other) const;
    bool operator!=(const Statistics& other) const { return !(*this == other); }
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Statistics, n_trials, n_correct_trials, n_nose_pokes, n_left_lever_presses,
                                   n_right_lever_presses, n_rewards)

// The subject's response, coded as IBL's `trials.choice`
enum class Choice { Left = -1, NoGo = 0, Right = 1 };

// Everything recorded about one trial. Values use IBL's `trials` definitions, an empty optional is NaN (not
// applicable). `*Time` values are seconds from session start, the raw `states`, `events`, and `stimuli` are seconds
// from trial start like Bpod's.
struct TrialRecord {
    int trialNum = 0;  // From 0, across the whole session
    std::string itemId;
    int itemRepetition = 0;  // From 0, within the timeline item
    TrialType type = TrialType::Training;
    std::optional<int> stage;
    Parameters parameters;

    double startTime = 0.0;  // intervals_0
    double endTime = 0.0;    // intervals_1
    std::optional<double> stimOnTime;
    std::optional<double> stimOffTime;
    std::optional<double> goCueTime;
    std::optional<double> responseTime;
    std::optional<double> feedbackTime;
    std::optional<int> choice;        // -1 left lever, 1 right lever, 0 no response, NaN for intervals
    std::optional<int> feedbackType;  // 1 reward, -1 error, NaN when no feedback was given
    std::optional<double> rewardVolume;  // uL, NaN until the water valve is calibrated
    double rewardValveTime = 0.0;        // Total seconds the valve was open for rewards

    int nosePokes = 0;
    int leftLeverPresses = 0;
    int rightLeverPresses = 0;

    std::vector<std::pair<std::string, std::array<double, 2>>> states;  // In the order entered
    std::map<std::string, std::vector<double>> events;
    nlohmann::json stimuli = nlohmann::json::array();
};

// Everything a trial can observe and control. Inputs are sampled once per frame, so `pressed()` stays true for the
// whole frame an input became active in. Each trial starts with all outputs off and blank displays, and every input
// change, output change, and stimulus is recorded with its time.
class TrialContext {
public:
    TrialContext(Gpio& gpio, DisplayManager& displays, Statistics& statistics);

    TrialContext(const TrialContext&) = delete;
    TrialContext& operator=(const TrialContext&) = delete;

    // ----- Inputs -----

    /// Became active this frame
    bool pressed(Input input) const;
    /// Became inactive this frame
    bool released(Input input) const;
    /// Currently active
    bool held(Input input) const;
    /// Either lever became active this frame
    bool anyLeverPressed() const;

    // ----- Outputs -----

    /// Switches an output on or off, cancelling any pulse on it
    void setOutput(Output output, bool on);
    /// Switches on for `duration`, then off automatically
    void pulse(Output output, Milliseconds duration);
    /// True until a pulse on `output` has ended
    bool pulsing(Output output) const;

    // ----- Displays -----

    /// Shows an image, the first stimulus shown sets `stimOn_times`
    /// @param image File name in `assets/stimuli`, PNG or BMP
    void showImage(DisplaySide side, const std::string& image);
    /// Fills with a color, the first stimulus shown sets `stimOn_times`
    void fillDisplay(DisplaySide side, SDL_Color color);
    /// Clears the stimuli, the first clear after a stimulus sets `stimOff_times`
    void clearDisplays(DisplaySide side = DisplaySide::Both);

    // ----- Task events, recorded with IBL's trials definitions -----

    /// Enters a named state, e.g. "iti" or "response", ending the previous one
    void enterState(const std::string& state);
    /// The cue telling the subject it can respond (`goCue_times`)
    void goCue();
    /// The subject's response (`response_times` and `choice`), only the first response is kept
    void respond(Choice choice);
    /// Opens the water valve for the trial's `valve_open_ms` (`feedback_times`, `feedbackType` 1)
    void deliverWater();
    /// True while the valve opened by `deliverWater()` is still open
    bool waterFlowing() const;
    /// Negative feedback for an incorrect or missing response (`feedback_times`, `feedbackType` -1)
    void errorFeedback();

    // ----- Timing -----

    /// The protocol's parameters with this trial's overrides applied
    const Parameters& parameters() const { return item_->parameters; }
    const TimelineItem& item() const { return *item_; }

    /// Since the trial began
    Milliseconds elapsed() const;
    /// Uniformly random between the bounds, inclusive, e.g. for ITI and cue durations
    Milliseconds randomDuration(int minimumMs, int maximumMs);

    // ----- Completion -----

    /// Ends the trial, the runner moves to the next one on the following frame
    void complete() { completed_ = true; }
    bool completed() const { return completed_; }

    // ----- Runner only -----

    /// Resets the hardware and starts recording a new trial
    /// @param trialNum From 0, across the whole session
    /// @param itemRepetition From 0, within the timeline item
    /// @param sessionStart Origin of the record's session times
    void begin(const TimelineItem& item, int trialNum, int itemRepetition, Clock::time_point sessionStart);
    /// Reads inputs, records changes, and ends expired pulses, call once per frame before updating the trial
    void sample();
    /// Resets the hardware and closes the trial's record
    /// @return The completed record, the context is left empty until the next `begin()`
    TrialRecord finish();
    /// Switches everything off and clears the displays
    void reset();

private:
    /// Seconds since the session started
    double sessionTime() const;
    /// Seconds since the trial began
    double trialTime() const;
    /// Records any output changes since the last call as events
    void recordOutputs();
    /// Adds a stimulus event with its time and display, setting the stimulus on and off times
    void recordStimulus(DisplaySide side, nlohmann::json stimulus);

    Gpio& gpio_;
    DisplayManager& displays_;
    Statistics& statistics_;
    std::mt19937 random_{std::random_device{}()};

    const TimelineItem* item_ = nullptr;
    Clock::time_point sessionStart_;
    Clock::time_point startedAt_;
    bool completed_ = false;
    TrialRecord record_;

    std::array<bool, kInputCount> inputs_{};
    std::array<bool, kInputCount> previousInputs_{};
    std::array<bool, kOutputCount> outputs_{};
    std::array<std::optional<Clock::time_point>, kOutputCount> pulseEnds_{};
};
