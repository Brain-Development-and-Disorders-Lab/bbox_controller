#pragma once

#include "session/timer.h"
#include "session/trial.h"

// Waits for a fixed duration with all outputs off and blank displays
class IntervalTrial final : public Trial {
public:
    /// @param duration How long the interval lasts
    explicit IntervalTrial(Milliseconds duration) : duration_(duration) {}

    void begin(TrialContext& context) override;
    void update(TrialContext& context) override;

private:
    Milliseconds duration_;
    Timer timer_;
};
