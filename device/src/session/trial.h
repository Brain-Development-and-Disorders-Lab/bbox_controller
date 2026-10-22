#pragma once

#include <memory>

#include "session/protocol.h"
#include "session/trial_context.h"

// A single trial, created fresh for every repetition of a timeline item. Trials are typically a small state machine:
// `begin()` sets up the first state, `update()` is called every frame to check inputs and timers, and the trial calls
// `context.complete()` when it is done. Calling `context.enterState()` on each change of state, and the task event
// functions (`goCue()`, `respond()`, `deliverWater()`, `errorFeedback()`) as they happen, fills in the trial's data.
// See `trials/stage_01_trial.cpp` for an example.
class Trial {
public:
    virtual ~Trial() = default;

    /// Sets up the first state, called once with fresh outputs and blank displays
    virtual void begin(TrialContext& context) = 0;
    /// Checks inputs and timers, called every frame until `context.complete()`
    virtual void update(TrialContext& context) = 0;
};

/// The trial implementing a timeline item, where new trial types are added
/// @return Null if that type or stage isn't implemented on the device yet
std::unique_ptr<Trial> createTrial(const TimelineItem& item);
