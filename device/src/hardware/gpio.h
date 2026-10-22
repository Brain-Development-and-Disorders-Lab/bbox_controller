#pragma once

#include <array>
#include <cstddef>

// Digital inputs read from the behavior box
enum class Input { LeftLever, RightLever, NosePoke };
constexpr size_t kInputCount = 3;

// Digital outputs driven by the device
enum class Output { LeftLeverLight, RightLeverLight, NoseLight, WaterValve };
constexpr size_t kOutputCount = 4;

// Names used in messages to the dashboard, matching `InputChannel` in `dashboard/types/index.d.ts`
constexpr std::array<const char*, kInputCount> kInputNames = {"left_lever", "right_lever", "nose_poke"};
constexpr std::array<const char*, kOutputCount> kOutputNames = {
    "left_lever_light", "right_lever_light", "nose_light", "water_valve"};

// Hardware-independent access to the box's inputs and outputs
class Gpio {
public:
    virtual ~Gpio() = default;

    /// True while the input is active, e.g. a lever is pressed
    virtual bool read(Input input) const = 0;
    /// True while the output is switched on
    virtual bool state(Output output) const = 0;
    virtual void write(Output output, bool on) = 0;

    /// Switches every output off
    void resetOutputs() {
        for (size_t i = 0; i < kOutputCount; i++) {
            write(static_cast<Output>(i), false);
        }
    }
};
