#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

// The device's data root, `~/bbox_data`. Sessions are stored under it in IBL's ALF layout,
// `Subjects/<subject>/<yyyy-mm-dd>/<NNN>/`
class Storage {
public:
    /// Uses `~/bbox_data`, or `bbox_data` in the working directory if `HOME` isn't set
    Storage();

    const std::filesystem::path& root() const { return root_; }

    /// Every file under the root, as `/`-separated paths relative to it
    std::vector<std::string> list() const;

    /// Contents of a file named as by `list()`, empty if it can't be read
    std::optional<std::string> read(const std::string& name) const;

private:
    std::filesystem::path root_;
};
