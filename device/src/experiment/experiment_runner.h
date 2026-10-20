#pragma once

#include <optional>
#include <string>

#include "experiment/experiment.h"
#include "hardware/gpio.h"

// Steps through an experiment's trials, one at a time, from the main loop
class ExperimentRunner {
public:
    explicit ExperimentRunner(Gpio& gpio);

    void start(Experiment experiment, std::string animalId);
    void stop();

    // Call once per frame to advance the active trial
    void update();

    bool running() const { return experiment_.has_value(); }

private:
    Gpio& gpio_;
    std::optional<Experiment> experiment_;
    std::string animalId_;
    size_t trialIndex_ = 0;
};
