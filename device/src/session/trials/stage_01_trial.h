#pragma once

#include "session/timer.h"
#include "session/trial.h"

// Training stage 01: after a random inter-trial interval both lever lights turn on (the go cue), and pressing either
// lever switches them off and delivers water
class Stage01Trial final : public Trial {
public:
    void begin(TrialContext& context) override;
    void update(TrialContext& context) override;

private:
    enum class Phase { Iti, Response, Reward };

    Phase phase_ = Phase::Iti;
    Timer timer_;
};
