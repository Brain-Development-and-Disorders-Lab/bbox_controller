#include "session/trial.h"

#include "session/trials/interval_trial.h"
#include "session/trials/stage_01_trial.h"

std::unique_ptr<Trial> createTrial(const TimelineItem& item) {
    if (item.type == TrialType::Interval) {
        return std::make_unique<IntervalTrial>(Milliseconds(item.durationMs));
    }

    // Training stages, each implemented in `trials/`
    switch (*item.stage) {
        case 1:
            return std::make_unique<Stage01Trial>();
        default:
            return nullptr;
    }
}
