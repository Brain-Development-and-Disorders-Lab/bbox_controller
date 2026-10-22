#include "session/trials/interval_trial.h"

void IntervalTrial::begin(TrialContext& context) {
    context.enterState("interval");
    timer_.start(duration_);
}

void IntervalTrial::update(TrialContext& context) {
    if (timer_.expired()) {
        context.complete();
    }
}
