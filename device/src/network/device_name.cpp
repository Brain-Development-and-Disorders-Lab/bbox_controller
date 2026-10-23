#include "network/device_name.h"

#include <algorithm>
#include <cctype>
#include <random>

namespace {
    constexpr const char* kPrefix = "bbox_device_";
    constexpr const char kIdCharacters[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    constexpr size_t kIdLength = 8;
    constexpr size_t kMinLength = 8;
    constexpr size_t kMaxLength = 32;
}

std::string generateDeviceName() {
    std::random_device random;
    std::uniform_int_distribution<size_t> pick(0, sizeof(kIdCharacters) - 2);

    std::string name = kPrefix;
    for (size_t i = 0; i < kIdLength; i++) {
        name += kIdCharacters[pick(random)];
    }
    return name;
}

bool isValidDeviceName(const std::string& name) {
    if (name.size() < kMinLength || name.size() > kMaxLength) {
        return false;
    }
    return std::all_of(name.begin(), name.end(), [](unsigned char c) { return std::isalnum(c) || c == '_' || c == '-'; });
}
