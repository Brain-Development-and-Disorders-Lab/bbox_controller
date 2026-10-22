#include "session/session_runner.h"

#include <spdlog/spdlog.h>

SessionRunner::SessionRunner(Gpio& gpio, DisplayManager& displays, std::filesystem::path dataRoot, Reporter reporter)
    : displays_(displays),
      dataRoot_(std::move(dataRoot)),
      reporter_(std::move(reporter)),
      context_(gpio, displays, statistics_) {}

bool SessionRunner::start(Protocol protocol, const nlohmann::json& protocolData, std::string subject) {
    if (subject.empty()) {
        spdlog::error("[Session] A subject is required to start a session");
        return false;
    }

    // Check every item has an implementation before touching the hardware
    for (const TimelineItem& item : protocol.items) {
        if (!createTrial(item)) {
            spdlog::error("[Session] Timeline item \"{}\" (training stage {}) is not implemented on the device",
                          item.id, item.stage.value_or(0));
            return false;
        }
    }

    if (running()) {
        spdlog::warn("[Session] Stopping \"{}\" to start a new session", protocol_->name);
        stop();
    }

    if (!writer_.open(dataRoot_, subject, protocol, protocolData)) {
        return false;
    }

    spdlog::info("[Session] Starting \"{}\" ({} timeline items{}) for subject {}", protocol.name,
                 protocol.items.size(), protocol.loop ? ", looping" : "", subject);
    protocol_ = std::move(protocol);
    subject_ = std::move(subject);
    sessionPath_ = writer_.sessionPath();
    statistics_ = {};
    state_ = "running";
    startedAt_ = Clock::now();
    itemIndex_ = 0;
    repetition_ = 0;
    trialNum_ = 0;

    // Only stimuli are shown while running
    displays_.setMessageVisible(false);
    startTrial();
    return true;
}

void SessionRunner::stop() {
    if (!running()) {
        return;
    }
    spdlog::info("[Session] Stopped \"{}\"", protocol_->name);
    // The interrupted trial is still recorded, it ends now
    finishTrial();
    finish("stopped");
}

void SessionRunner::update() {
    if (!running()) {
        return;
    }

    const Statistics before = statistics_;
    context_.sample();
    trial_->update(context_);

    if (context_.completed()) {
        finishTrial();
        advance();
    } else if (statistics_ != before) {
        publishState();
    }
}

void SessionRunner::publishState() const {
    nlohmann::json trial = nullptr;
    if (running()) {
        trial = {
            {"trial_num", trialNum_},
            {"item_id", protocol_->items[itemIndex_].id},
            {"elapsed_ms", context_.elapsed().count()},
        };
    }

    reporter_({
        {"type", "session_state"},
        {"state", state_},
        {"protocol_name", protocol_ ? protocol_->name : ""},
        {"subject", subject_},
        {"session_path", sessionPath_},
        {"session_elapsed_ms", elapsedMs()},
        {"trial", trial},
        {"statistics", statistics_},
    });
}

void SessionRunner::startTrial() {
    const TimelineItem& item = protocol_->items[itemIndex_];
    trial_ = createTrial(item);
    context_.begin(item, trialNum_, repetition_, startedAt_);
    trial_->begin(context_);

    if (item.repeat > 1) {
        spdlog::info("[Session] Trial {}: \"{}\" ({}/{})", trialNum_, item.id, repetition_ + 1, item.repeat);
    } else {
        spdlog::info("[Session] Trial {}: \"{}\"", trialNum_, item.id);
    }
    publishState();
}

void SessionRunner::finishTrial() {
    const TrialRecord record = context_.finish();
    trial_.reset();

    // Intervals aren't counted as trials in the statistics, but are recorded like any other
    if (record.type == TrialType::Training) {
        statistics_.n_trials++;
        if (record.feedbackType == 1) {
            statistics_.n_correct_trials++;
        }
    }
    writer_.writeTrial(record);

    spdlog::info("[Session] Trial {} finished after {:.3f}s, choice: {}, feedback: {}", record.trialNum,
                 record.endTime - record.startTime, record.choice ? std::to_string(*record.choice) : "NaN",
                 record.feedbackType ? std::to_string(*record.feedbackType) : "NaN");
    trialNum_++;
}

void SessionRunner::advance() {
    if (++repetition_ < protocol_->items[itemIndex_].repeat) {
        startTrial();
        return;
    }

    repetition_ = 0;
    if (++itemIndex_ >= protocol_->items.size()) {
        if (!protocol_->loop) {
            spdlog::info("[Session] Completed \"{}\"", protocol_->name);
            finish("completed");
            return;
        }
        spdlog::info("[Session] Timeline finished, looping");
        itemIndex_ = 0;
    }
    startTrial();
}

void SessionRunner::finish(const std::string& state) {
    finalElapsed_ = std::chrono::duration_cast<Milliseconds>(Clock::now() - startedAt_);
    context_.reset();
    writer_.close(state, statistics_);
    displays_.setMessageVisible(true);
    state_ = state;
    publishState();
}

int SessionRunner::elapsedMs() const {
    if (running()) {
        return static_cast<int>(std::chrono::duration_cast<Milliseconds>(Clock::now() - startedAt_).count());
    }
    return static_cast<int>(finalElapsed_.count());
}
