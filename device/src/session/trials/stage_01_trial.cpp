#include "session/trials/stage_01_trial.h"

void Stage01Trial::begin(TrialContext& context) {
    const Parameters& parameters = context.parameters();
    phase_ = Phase::Iti;
    context.enterState("iti");
    timer_.start(context.randomDuration(parameters.iti_minimum_ms, parameters.iti_maximum_ms));
}

void Stage01Trial::update(TrialContext& context) {
    switch (phase_) {
        case Phase::Iti:
            // Presses during the ITI are recorded but otherwise ignored
            if (timer_.expired()) {
                context.setOutput(Output::LeftLeverLight, true);
                context.setOutput(Output::RightLeverLight, true);
                context.enterState("response");
                context.goCue();
                phase_ = Phase::Response;
            }
            break;

        case Phase::Response:
            if (context.anyLeverPressed()) {
                context.respond(context.pressed(Input::LeftLever) ? Choice::Left : Choice::Right);
                context.setOutput(Output::LeftLeverLight, false);
                context.setOutput(Output::RightLeverLight, false);
                context.enterState("reward");
                context.deliverWater();
                phase_ = Phase::Reward;
            }
            break;

        case Phase::Reward:
            // Finish once the valve has closed, so the full reward is delivered
            if (!context.waterFlowing()) {
                context.complete();
            }
            break;
    }
}
