#pragma once

#include <array>
#include <variant>

#include <SDL3/SDL_scancode.h>

#include "hardware/gpio.h"

using Channel = std::variant<Input, Output>;

// GPIO channel shown in the simulator's status view, with the corresponding key to activate it
struct Control {
    const char* label;
    SDL_Scancode key;
    const char* keyName;
    Channel channel;
};

constexpr std::array<Control, 7> kControls = {{
    {"Left Lever", SDL_SCANCODE_1, "1", Input::LeftLever},
    {"Left Lever Light", SDL_SCANCODE_J, "J", Output::LeftLeverLight},
    {"Right Lever", SDL_SCANCODE_2, "2", Input::RightLever},
    {"Right Lever Light", SDL_SCANCODE_L, "L", Output::RightLeverLight},
    {"Nose Poke", SDL_SCANCODE_SPACE, "Space", Input::NosePoke},
    {"Nose Light", SDL_SCANCODE_K, "K", Output::NoseLight},
    {"Water Valve", SDL_SCANCODE_UNKNOWN, nullptr, Output::WaterValve},
}};

inline bool isActive(const Gpio& gpio, const Channel& channel) {
    if (const auto* input = std::get_if<Input>(&channel)) {
        return gpio.read(*input);
    }
    return gpio.state(std::get<Output>(channel));
}
