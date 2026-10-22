#pragma once

#include <filesystem>
#include <fstream>
#include <string>

#include <nlohmann/json.hpp>

#include "session/protocol.h"
#include "session/trial_context.h"

// Writes a session's data following IBL's iblrig and ALF conventions, under
// `<root>/Subjects/<subject>/<yyyy-mm-dd>/<NNN>/`:
//
// - `raw_task_data_00/_bbox_taskData.raw.jsonable`, one JSON object per trial, like iblrig's taskData
// - `raw_task_data_00/_bbox_taskSettings.raw.json`, session settings and totals, like iblrig's taskSettings
// - `raw_task_data_00/_bbox_taskProtocol.raw.json`, the protocol file as it was sent
// - `alf/_ibl_trials.table.csv`, one row per trial using IBL's trials columns, times in seconds from session start
//
// Each trial is written and flushed as soon as it finishes, so a crash loses at most the trial in progress.
class SessionWriter {
public:
    /// Creates the next numbered session folder for today and writes the initial files
    /// @param protocolData The protocol file as sent, saved unchanged
    /// @return False if any file can't be written
    bool open(const std::filesystem::path& root, const std::string& subject, const Protocol& protocol,
              const nlohmann::json& protocolData);
    /// Appends a trial to the task data and trials table, flushed immediately
    void writeTrial(const TrialRecord& record);
    /// Records the end time, final state, and totals, then closes the files
    /// @param state "completed" or "stopped"
    void close(const std::string& state, const Statistics& statistics);

    bool active() const { return active_; }
    /// Relative to the data root, e.g. "Subjects/M001/2026-10-20/001"
    const std::string& sessionPath() const { return sessionPath_; }

private:
    /// Rewrites the task settings file from `settings_`
    void writeSettings();

    bool active_ = false;
    std::filesystem::path directory_;
    std::string sessionPath_;
    nlohmann::json settings_;
    double rewardValveTime_ = 0.0;
    std::ofstream taskData_;
    std::ofstream trialsTable_;
};
