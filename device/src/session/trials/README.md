# Trials

A trial is one run of a timeline item in a protocol. This folder holds the trial implementations. Each training stage is a class here, as is the interval.

| File | Timeline item |
| --- | --- |
| `interval_trial.{h,cpp}` | `"type": "interval"`. Waits for `duration_ms` with all outputs off and blank displays. |
| `stage_01_trial.{h,cpp}` | `"type": "training", "stage": 1`. After a random inter-trial interval both lever lights turn on, and a press on either lever turns them off and delivers water. |

A protocol that uses a stage with no implementation is rejected when the session starts, and the device logs which timeline item is not implemented.

## How a Trial Runs

`SessionRunner` creates a new trial object for every repetition of a timeline item, so member variables start fresh each trial. For each trial:

1. The runner switches every output off, clears the displays, and starts a new record.
2. The runner calls `begin(context)` once.
3. Every frame, the runner reads the inputs, then calls `update(context)`.
4. When the trial calls `context.complete()`, the runner records the trial at the end of that frame and begins the next one.
5. If the session is stopped, the trial in progress is recorded as it is and `update()` is not called again.

`update()` runs once per display frame (about 60 times a second), so it should check state and return, never wait or sleep. Use `Timer` for anything time-based.

A trial is usually written as a small state machine: an `enum class Phase` member, a `Timer`, and a `switch` in `update()`.

## Adding a Training Stage

The dashboard already offers training stages 1 to 6. To implement stage X:

1. Create `stage_0X_trial.h`:

   ```cpp
   #pragma once

   #include "session/timer.h"
   #include "session/trial.h"

   // Training stage 0X: <one-line description of the task>
   class Stage0XTrial final : public Trial {
   public:
       void begin(TrialContext& context) override;
       void update(TrialContext& context) override;

   private:
       enum class Phase { Iti, Response, Reward };

       Phase phase_ = Phase::Iti;
       Timer timer_;
   };
   ```

2. Create `stage_0X_trial.cpp` with `begin()` and `update()`. `stage_01_trial.cpp` is a complete example.

3. Register the stage in `createTrial()` in [../trial.cpp](../trial.cpp):

   ```cpp
   #include "session/trials/stage_0X_trial.h"

   // ...

   switch (*item.stage) {
       case 1:
           return std::make_unique<Stage01Trial>();
       case 2:
           return std::make_unique<Stage0XTrial>();
       default:
           return nullptr;
   }
   ```

4. Run `make mac`. New `.cpp` files are compiled automatically.

5. Test it in simulation mode: create a protocol in the dashboard that uses the stage, start a session, and use the keyboard to press levers and trigger the nose poke. Check the trial rows in `~/bbox_data/Subjects/<subject>/<date>/<NNN>/alf/_ibl_trials.table.csv`.

## The Trial Context

`TrialContext` ([../trial_context.h](../trial_context.h)) is the only interface a trial needs. It controls the hardware and records everything the trial does.

### Inputs

Inputs are read once per frame, before `update()`.

| Function | Returns true when |
| --- | --- |
| `pressed(Input)` | The input became active this frame |
| `released(Input)` | The input became inactive this frame |
| `held(Input)` | The input is active |
| `anyLeverPressed()` | Either lever became active this frame |

Inputs are `Input::LeftLever`, `Input::RightLever`, and `Input::NosePoke`. Presses and nose pokes are counted in the session statistics automatically.

### Outputs

| Function | Effect |
| --- | --- |
| `setOutput(Output, bool)` | Switches an output on or off, cancelling any pulse on it |
| `pulse(Output, Milliseconds)` | Switches an output on, then off after the duration |
| `pulsing(Output)` | True until the pulse has ended |

Outputs are `Output::LeftLeverLight`, `Output::RightLeverLight`, `Output::NoseLight`, and `Output::WaterValve`. All outputs are switched off at the start and end of every trial.

### Displays

| Function | Effect |
| --- | --- |
| `showImage(DisplaySide, image)` | Shows an image from `assets/stimuli/`, scaled to fit |
| `fillDisplay(DisplaySide, SDL_Color)` | Fills the display with a color |
| `clearDisplays(DisplaySide)` | Clears the display to black |

`DisplaySide` is `Left`, `Right`, or `Both`. The first stimulus shown in a trial sets `stimOn_times`, and the first clear after it sets `stimOff_times`. A stimulus still showing when the trial ends sets `stimOff_times` to the trial's end.

### Task Events

These functions fill in the trial's IBL trials columns. Call them as the events happen.

| Function | Records |
| --- | --- |
| `enterState(name)` | Starts a named state such as `"iti"` or `"response"`, ending the previous one. States appear in `"States timestamps"`. |
| `goCue()` | `goCue_times`, the cue telling the subject it can respond |
| `respond(Choice)` | `response_times` and `choice`. Only the first response in a trial is kept. `Choice` is `Left`, `Right`, or `NoGo`. |
| `deliverWater()` | Opens the water valve for `valve_open_ms` and records `feedback_times` with `feedbackType` 1 |
| `waterFlowing()` | True while the valve opened by `deliverWater()` is open |
| `errorFeedback()` | Records `feedback_times` with `feedbackType` -1. It does not drive any output, so the trial applies its own punishment, such as a timeout. |

A training trial with no call to `respond()` is recorded with `choice` 0 (no-go). Only the first feedback in a trial sets `feedback_times` and `feedbackType`. A trial counts as correct in the session statistics when its `feedbackType` is 1.

### Parameters and Timing

| Function | Returns |
| --- | --- |
| `parameters()` | The protocol's parameters with this timeline item's overrides applied |
| `item()` | The timeline item being run |
| `elapsed()` | Time since the trial began |
| `randomDuration(min, max)` | A uniformly random duration between the bounds, inclusive |
| `complete()` | Ends the trial |

The parameters available are defined in `Parameters` in [../protocol.h](../protocol.h):

| Parameter | Meaning |
| --- | --- |
| `iti_minimum_ms`, `iti_maximum_ms` | Range of the inter-trial interval |
| `response_limit_ms` | Time allowed to respond |
| `cue_minimum_ms`, `cue_maximum_ms` | Range of the cue duration |
| `hold_minimum_ms`, `hold_maximum_ms` | Range of the hold duration |
| `valve_open_ms` | How long the water valve opens for a reward |
| `punishment_ms` | Length of the punishment timeout |

A trial uses only the parameters that apply to its task. Adding a parameter requires changes in both applications: `Parameters` and its `NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE` line in `protocol.h`, and the parameter definitions in `dashboard/src/lib/protocol.ts` and `ProtocolParameters` in `dashboard/types/index.d.ts`.

## Adding a Trial Type

Training stages cover most tasks. A new type is needed only for a timeline item that is not a training stage and needs its own fields, as the interval does with `duration_ms`.

On the device:

1. Add a value to `TrialType` in [../protocol.h](../protocol.h) and its name to `trialTypeName()` and `parseTrialType()` in [../protocol.cpp](../protocol.cpp).
2. Read any fields specific to the type in `parseProtocol()`, and add them to `TimelineItem`.
3. Create the trial class in this folder and return it from `createTrial()` in [../trial.cpp](../trial.cpp).
4. Check the places that treat training trials specially. `TrialContext::begin()` sets the no-go choice, and `SessionRunner::finishTrial()` counts trials in the statistics, both only for `TrialType::Training`.

In the dashboard:

1. Add a type to `TimelineItem` in `dashboard/types/index.d.ts`.
2. Add a schema to the `TimelineItemSchema` union in `dashboard/src/lib/protocol.ts`.
3. Add it to the timeline editor in `dashboard/src/components/ProtocolEditDialog` and `ProtocolTimeline`.

Then add the type to the protocol file format in [shared/README.md](../../../../shared/README.md).
