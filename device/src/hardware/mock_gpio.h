#pragma once

#include <array>

#include "hardware/gpio.h"

// In-memory GPIO used when simulating, inputs change through `simulate()` instead of sensors
class MockGpio final : public Gpio {
public:
    bool read(Input input) const override { return inputs_[static_cast<size_t>(input)]; }
    bool state(Output output) const override { return outputs_[static_cast<size_t>(output)]; }
    void write(Output output, bool on) override { outputs_[static_cast<size_t>(output)] = on; }

    /// Sets an input as if its sensor had changed, e.g. from a simulator key
    void simulate(Input input, bool active) { inputs_[static_cast<size_t>(input)] = active; }

private:
    std::array<bool, kInputCount> inputs_{};
    std::array<bool, kOutputCount> outputs_{};
};
