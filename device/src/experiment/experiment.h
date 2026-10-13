#pragma once

#include <string>
#include <vector>

#include <nlohmann/json.hpp>

// Experiment definitions sent by the dashboard
struct Trial {
    std::string id;
    std::string name;
    std::string type;  // "standard", "interval", or "end"
    std::string description;
};

struct Experiment {
    std::string id;
    std::string name;
    std::vector<Trial> trials;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Trial, id, name, type, description)
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Experiment, id, name, trials)
