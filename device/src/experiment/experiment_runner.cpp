#include "experiment/experiment_runner.h"

#include <spdlog/spdlog.h>

ExperimentRunner::ExperimentRunner(Gpio& gpio) : gpio_(gpio) {}

void ExperimentRunner::start(Experiment experiment, std::string animalId) {
    spdlog::info("[Experiment] Starting \"{}\" ({} trials) for animal {}", experiment.name,
                 experiment.trials.size(), animalId);
    experiment_ = std::move(experiment);
    animalId_ = std::move(animalId);
    trialIndex_ = 0;
}

void ExperimentRunner::stop() {
    if (!experiment_) {
        return;
    }
    spdlog::info("[Experiment] Stopped \"{}\"", experiment_->name);
    experiment_.reset();
    gpio_.resetOutputs();
}

void ExperimentRunner::update() {
    if (!experiment_) {
        return;
    }
    // TODO: Run the trial at `trialIndex_` and advance when it completes
}
