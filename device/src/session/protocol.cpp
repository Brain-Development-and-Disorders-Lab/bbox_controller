#include "session/protocol.h"

#include <stdexcept>

namespace {
    constexpr const char* kFormat = "bbox-protocol";
    // Protocols were called experiments before adopting IBL terms, the structure is unchanged
    constexpr const char* kLegacyFormat = "bbox-experiment";
    constexpr int kFormatVersion = 1;

    TrialType parseTrialType(const std::string& name) {
        for (TrialType type : {TrialType::Training, TrialType::Interval}) {
            if (name == trialTypeName(type)) {
                return type;
            }
        }
        throw std::invalid_argument("unknown trial type \"" + name + "\"");
    }
}

const char* trialTypeName(TrialType type) {
    switch (type) {
        case TrialType::Training:
            return "training";
        case TrialType::Interval:
            break;
    }
    return "interval";
}

Protocol parseProtocol(const nlohmann::json& data) {
    const std::string format = data.value("format", "");
    if (format != kFormat && format != kLegacyFormat) {
        throw std::invalid_argument("not a protocol file");
    }
    if (const int version = data.value("format_version", 0); version != kFormatVersion) {
        throw std::invalid_argument("unsupported format version " + std::to_string(version));
    }

    Protocol protocol;
    protocol.name = data.at("metadata").at("name").get<std::string>();
    protocol.parameters = data.at("parameters").get<Parameters>();

    const auto& timeline = data.at("timeline");
    protocol.loop = timeline.value("loop", false);
    for (const auto& entry : timeline.at("items")) {
        TimelineItem item;
        item.id = entry.at("id").get<std::string>();
        item.type = parseTrialType(entry.at("type").get<std::string>());
        item.description = entry.value("description", "");
        item.repeat = entry.value("repeat", 1);
        if (item.type == TrialType::Training) {
            item.stage = entry.at("stage").get<int>();
        } else {
            item.durationMs = entry.at("duration_ms").get<int>();
        }

        // Overrides are a partial set of parameters, so merge them over the protocol's before converting
        nlohmann::json parameters = data.at("parameters");
        if (entry.contains("parameters")) {
            parameters.update(entry.at("parameters"));
        }
        item.parameters = parameters.get<Parameters>();

        if (item.repeat < 1) {
            throw std::invalid_argument("timeline item \"" + item.id + "\" must repeat at least once");
        }
        protocol.items.push_back(std::move(item));
    }

    if (protocol.items.empty()) {
        throw std::invalid_argument("timeline is empty");
    }
    return protocol;
}
