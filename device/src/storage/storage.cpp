#include "storage/storage.h"

#include <cstdlib>
#include <fstream>
#include <sstream>

#include <spdlog/spdlog.h>

namespace {
    constexpr const char* kRootName = "bbox_data";
}

Storage::Storage() {
    const char* home = std::getenv("HOME");
    root_ = home ? std::filesystem::path(home) / kRootName : std::filesystem::current_path() / kRootName;
    spdlog::info("[Storage] Data root: {}", root_.string());
}

std::vector<std::string> Storage::list() const {
    std::vector<std::string> names;
    std::error_code error;
    for (auto it = std::filesystem::recursive_directory_iterator(root_, error);
         !error && it != std::filesystem::recursive_directory_iterator(); it.increment(error)) {
        if (it->is_regular_file()) {
            names.push_back(std::filesystem::relative(it->path(), root_).generic_string());
        }
    }
    return names;
}

std::optional<std::string> Storage::read(const std::string& name) const {
    std::ifstream file(root_ / name, std::ios::binary);
    if (!file) {
        spdlog::error("[Storage] Unable to read {}", (root_ / name).string());
        return std::nullopt;
    }
    std::ostringstream contents;
    contents << file.rdbuf();
    return contents.str();
}
