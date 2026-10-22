#pragma once

#include <functional>
#include <memory>
#include <optional>
#include <string>

#include <nlohmann/json.hpp>

#include "display/display_manager.h"
#include "hardware/gpio.h"
#include "session/protocol.h"
#include "session/session_writer.h"
#include "session/timer.h"
#include "session/trial.h"
#include "session/trial_context.h"

// Runs a session of a task protocol from the main loop, stepping through its timeline, running each item `repeat`
// times and starting over at the end if the timeline loops. Every trial is recorded with `SessionWriter`.
class SessionRunner {
public:
    // Sends `session_state` messages to the dashboard
    using Reporter = std::function<void(const nlohmann::json& message)>;

    /// @param dataRoot Where sessions are recorded, see `Storage`
    SessionRunner(Gpio& gpio, DisplayManager& displays, std::filesystem::path dataRoot, Reporter reporter);

    /// Starts recording and running the first trial, stopping any running session first
    /// @param protocolData The protocol file as sent, saved with the session
    /// @return False if the subject is empty, a timeline item isn't implemented, or the session can't be recorded
    bool start(Protocol protocol, const nlohmann::json& protocolData, std::string subject);
    /// Ends the session early, recording the interrupted trial
    void stop();

    /// Advances the active trial, call once per frame
    void update();

    /// Sends the current `session_state`, e.g. to a newly connected dashboard
    void publishState() const;

    bool running() const { return state_ == "running"; }

    /// Folder of the session being recorded relative to the data root, empty when not recording
    std::string activeSessionPath() const { return writer_.active() ? writer_.sessionPath() : ""; }

private:
    /// Creates and begins the trial for the current timeline item and repetition
    void startTrial();
    /// Records the active trial and updates the statistics
    void finishTrial();
    /// Moves to the next repetition or item, looping or completing at the end of the timeline
    void advance();
    /// Closes the recording and reports the final state
    /// @param state "completed" or "stopped"
    void finish(const std::string& state);
    /// Since the session started, frozen once it has finished
    int elapsedMs() const;

    DisplayManager& displays_;
    std::filesystem::path dataRoot_;
    Reporter reporter_;
    Statistics statistics_;
    TrialContext context_;
    SessionWriter writer_;

    std::optional<Protocol> protocol_;
    std::string subject_;
    std::string sessionPath_;
    std::string state_ = "idle";  // "idle", "running", "completed", or "stopped"
    Clock::time_point startedAt_;
    Milliseconds finalElapsed_{0};

    size_t itemIndex_ = 0;
    int repetition_ = 0;
    int trialNum_ = 0;
    std::unique_ptr<Trial> trial_;
};
