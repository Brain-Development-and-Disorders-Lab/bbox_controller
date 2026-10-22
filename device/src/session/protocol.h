#pragma once

#include <optional>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

// Task protocol files sent by the dashboard, the format is defined in `dashboard/src/lib/protocol.ts`

// Trial timing, all durations in milliseconds
struct Parameters {
    int iti_minimum_ms = 0;
    int iti_maximum_ms = 0;
    int response_limit_ms = 0;
    int cue_minimum_ms = 0;
    int cue_maximum_ms = 0;
    int hold_minimum_ms = 0;
    int hold_maximum_ms = 0;
    int valve_open_ms = 0;
    int punishment_ms = 0;
};

// Training trials are a task stage the subject responds to, intervals are a timed pause between them
enum class TrialType { Training, Interval };

/// Name used in protocol files and session data, e.g. "training"
const char* trialTypeName(TrialType type);

struct TimelineItem {
    std::string id;
    TrialType type = TrialType::Training;
    std::string description;
    int repeat = 1;
    std::optional<int> stage;  // Training only, from 1
    int durationMs = 0;     // Interval only
    Parameters parameters;  // Protocol parameters with this item's overrides applied
};

struct Protocol {
    std::string name;
    Parameters parameters;
    bool loop = false;
    std::vector<TimelineItem> items;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Parameters, iti_minimum_ms, iti_maximum_ms, response_limit_ms, cue_minimum_ms,
                                   cue_maximum_ms, hold_minimum_ms, hold_maximum_ms, valve_open_ms, punishment_ms)

/// Parses a protocol file, applying each timeline item's parameter overrides
/// @throws nlohmann::json::exception or std::invalid_argument if the protocol is malformed
Protocol parseProtocol(const nlohmann::json& data);
