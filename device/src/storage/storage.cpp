#include "storage/storage.h"

#include <fstream>

#include <spdlog/spdlog.h>

Storage::Storage(std::filesystem::path root) : root_(std::move(root)) {}

bool Storage::save(const std::string& name, const nlohmann::json& data) const {
    const auto path = root_ / name;
    std::error_code error;
    std::filesystem::create_directories(path.parent_path(), error);

    std::ofstream file(path);
    if (!file) {
        spdlog::error("[Storage] Unable to write {}", path.string());
        return false;
    }
    file << data.dump(2);
    return true;
}

std::optional<nlohmann::json> Storage::load(const std::string& name) const {
    const auto path = root_ / name;
    std::ifstream file(path);
    if (!file) {
        return std::nullopt;
    }

    auto data = nlohmann::json::parse(file, nullptr, false);
    if (data.is_discarded()) {
        spdlog::error("[Storage] Invalid JSON in {}", path.string());
        return std::nullopt;
    }
    return data;
}
