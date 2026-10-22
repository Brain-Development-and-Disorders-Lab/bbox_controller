#include "session/session_writer.h"

#include <chrono>
#include <ctime>
#include <optional>

#include <spdlog/fmt/fmt.h>
#include <spdlog/spdlog.h>

namespace {
    constexpr const char* kRawCollection = "raw_task_data_00";
    constexpr const char* kTaskDataFile = "_bbox_taskData.raw.jsonable";
    constexpr const char* kTaskSettingsFile = "_bbox_taskSettings.raw.json";
    constexpr const char* kTaskProtocolFile = "_bbox_taskProtocol.raw.json";
    constexpr const char* kTrialsTableFile = "alf/_ibl_trials.table.csv";

    // IBL's trials columns first, then the device's own
    constexpr const char* kTrialsColumns =
        "intervals_0,intervals_1,stimOn_times,stimOff_times,goCue_times,response_times,choice,feedback_times,"
        "feedbackType,rewardVolume,trialNum,timelineItem,itemRepetition,trialType,stage,rewardValveTime,nosePokes,"
        "leftLeverPresses,rightLeverPresses";

    // Local wall-clock time, formatted like iblrig's `datetime.now().isoformat()`
    std::string isoTime(std::chrono::system_clock::time_point time) {
        const std::time_t seconds = std::chrono::system_clock::to_time_t(time);
        std::tm local{};
        localtime_r(&seconds, &local);
        char buffer[32];
        std::strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &local);
        const auto micros =
            std::chrono::duration_cast<std::chrono::microseconds>(time.time_since_epoch()).count() % 1000000;
        return fmt::format("{}.{:06d}", buffer, micros);
    }

    // Subject names become folder names, so replace anything that isn't safe in a path
    std::string safeName(std::string name) {
        for (char& c : name) {
            if (std::string("\\/:*?\"<>|").find(c) != std::string::npos) {
                c = '_';
            }
        }
        return name == "." || name == ".." ? "_" : name;
    }

    // One more than the highest numbered session folder for the day, like iblrig
    int nextSessionNumber(const std::filesystem::path& dateDirectory) {
        int highest = 0;
        std::error_code error;
        for (const auto& entry : std::filesystem::directory_iterator(dateDirectory, error)) {
            const std::string name = entry.path().filename().string();
            if (entry.is_directory() && !name.empty() && name.find_first_not_of("0123456789") == std::string::npos) {
                highest = std::max(highest, std::stoi(name));
            }
        }
        return highest + 1;
    }

    std::string number(std::optional<double> value) {
        return value ? fmt::format("{:.6f}", *value) : "NaN";
    }

    std::string integer(std::optional<int> value) {
        return value ? std::to_string(*value) : "NaN";
    }

    std::string text(const std::string& value) {
        std::string quoted = "\"";
        for (char c : value) {
            quoted += c == '"' ? "\"\"" : std::string(1, c);
        }
        return quoted + "\"";
    }

    nlohmann::json optionalJson(const std::optional<double>& value) {
        return value ? nlohmann::json(*value) : nlohmann::json(nullptr);
    }

    nlohmann::json optionalJson(const std::optional<int>& value) {
        return value ? nlohmann::json(*value) : nlohmann::json(nullptr);
    }
}

bool SessionWriter::open(const std::filesystem::path& root, const std::string& subject, const Protocol& protocol,
                         const nlohmann::json& protocolData) {
    const auto now = std::chrono::system_clock::now();
    const std::string startTime = isoTime(now);
    const std::string date = startTime.substr(0, 10);

    const auto dateDirectory = root / "Subjects" / safeName(subject) / date;
    const int sessionNumber = nextSessionNumber(dateDirectory);
    const std::string sessionFolder = fmt::format("{:03d}", sessionNumber);
    directory_ = dateDirectory / sessionFolder;
    sessionPath_ = "Subjects/" + safeName(subject) + "/" + date + "/" + sessionFolder;

    // Checked separately, since a later success would clear an earlier error
    for (const auto& folder : {directory_ / kRawCollection, directory_ / "alf"}) {
        std::error_code error;
        std::filesystem::create_directories(folder, error);
        if (error) {
            spdlog::error("[Storage] Unable to create {}: {}", folder.string(), error.message());
            return false;
        }
    }

    std::ofstream protocolFile(directory_ / kRawCollection / kTaskProtocolFile);
    protocolFile << protocolData.dump(2);

    taskData_.open(directory_ / kRawCollection / kTaskDataFile);
    trialsTable_.open(directory_ / kTrialsTableFile);
    if (!protocolFile || !taskData_ || !trialsTable_) {
        spdlog::error("[Storage] Unable to write session files in {}", directory_.string());
        taskData_.close();
        trialsTable_.close();
        return false;
    }
    trialsTable_ << kTrialsColumns << std::endl;

    rewardValveTime_ = 0.0;
    settings_ = {
        {"SUBJECT_NAME", subject},
        {"SESSION_DATE", date},
        {"SESSION_NUMBER", sessionNumber},
        {"SESSION_START_TIME", startTime},
        {"SESSION_END_TIME", nullptr},
        {"SESSION_END_STATE", nullptr},
        {"PROTOCOL_NAME", protocol.name},
        {"PROTOCOL_LOOP", protocol.loop},
        {"PARAMETERS", protocolData.at("parameters")},
        {"NTRIALS", 0},
        {"NTRIALS_CORRECT", 0},
        {"NREWARDS", 0},
        {"TOTAL_REWARD_VALVE_TIME", 0.0},
        {"TOTAL_WATER_DELIVERED", nullptr},  // uL, unknown until the water valve is calibrated
        {"TIMEBASE", "Seconds from SESSION_START_TIME, measured with the device's monotonic clock"},
    };
    writeSettings();

    active_ = true;
    spdlog::info("[Storage] Recording session to {}", directory_.string());
    return true;
}

void SessionWriter::writeTrial(const TrialRecord& record) {
    if (!active_) {
        return;
    }

    // Bpod stores each state as a list of [start, end] pairs, since a state can be entered more than once
    nlohmann::json states = nlohmann::json::object();
    for (const auto& [state, interval] : record.states) {
        states[state].push_back({interval[0], interval[1]});
    }

    std::optional<double> reactionTime;
    if (record.responseTime && record.goCueTime) {
        reactionTime = *record.responseTime - *record.goCueTime;
    }

    const nlohmann::json line = {
        {"trial_num", record.trialNum},
        {"timeline_item", record.itemId},
        {"item_repetition", record.itemRepetition},
        {"trial_type", trialTypeName(record.type)},
        {"stage", optionalJson(record.stage)},
        {"parameters", record.parameters},
        {"response_side", optionalJson(record.choice)},
        {"response_time", optionalJson(reactionTime)},
        {"trial_correct", record.feedbackType ? nlohmann::json(*record.feedbackType == 1) : nlohmann::json(nullptr)},
        {"reward_valve_time", record.rewardValveTime},
        {"reward_amount", optionalJson(record.rewardVolume)},
        {"behavior_data",
         {
             {"Trial start timestamp", record.startTime},
             {"Trial end timestamp", record.endTime},
             {"States timestamps", states},
             {"Events timestamps", record.events},
             {"Stimuli", record.stimuli},
         }},
    };
    taskData_ << line.dump() << std::endl;

    trialsTable_ << fmt::format("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}", number(record.startTime),
                                number(record.endTime), number(record.stimOnTime), number(record.stimOffTime),
                                number(record.goCueTime), number(record.responseTime), integer(record.choice),
                                number(record.feedbackTime), integer(record.feedbackType),
                                number(record.rewardVolume), record.trialNum, text(record.itemId),
                                record.itemRepetition, text(trialTypeName(record.type)), integer(record.stage),
                                number(record.rewardValveTime), record.nosePokes, record.leftLeverPresses,
                                record.rightLeverPresses)
                 << std::endl;

    rewardValveTime_ += record.rewardValveTime;
}

void SessionWriter::close(const std::string& state, const Statistics& statistics) {
    if (!active_) {
        return;
    }
    settings_["SESSION_END_TIME"] = isoTime(std::chrono::system_clock::now());
    settings_["SESSION_END_STATE"] = state;
    settings_["NTRIALS"] = statistics.n_trials;
    settings_["NTRIALS_CORRECT"] = statistics.n_correct_trials;
    settings_["NREWARDS"] = statistics.n_rewards;
    settings_["TOTAL_REWARD_VALVE_TIME"] = rewardValveTime_;
    writeSettings();

    taskData_.close();
    trialsTable_.close();
    active_ = false;
    spdlog::info("[Storage] Session saved to {}", directory_.string());
}

void SessionWriter::writeSettings() {
    std::ofstream file(directory_ / kRawCollection / kTaskSettingsFile);
    file << settings_.dump(4);
    if (!file) {
        spdlog::error("[Storage] Unable to write {}", (directory_ / kRawCollection / kTaskSettingsFile).string());
    }
}
