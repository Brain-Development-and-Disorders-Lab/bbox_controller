#pragma once

#include <array>

#include "hardware/gpio.h"
#include "hardware/pins.h"

// Raspberry Pi GPIO backend
class PiGpio final : public Gpio {
public:
    bool read(Input) const override { return false; }
    bool state(Output output) const override { return outputs_[static_cast<size_t>(output)]; }
    void write(Output output, bool on) override { outputs_[static_cast<size_t>(output)] = on; }

private:
    std::array<bool, kOutputCount> outputs_{};
};
