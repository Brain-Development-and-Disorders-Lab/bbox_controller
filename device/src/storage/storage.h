#pragma once

#include <filesystem>
#include <optional>
#include <string>

#include <nlohmann/json.hpp>

// Reads and writes JSON files (experiments, configuration, and results) under a specified directory
class Storage {
public:
    explicit Storage(std::filesystem::path root);

    bool save(const std::string& name, const nlohmann::json& data) const;
    std::optional<nlohmann::json> load(const std::string& name) const;

private:
    std::filesystem::path root_;
};
