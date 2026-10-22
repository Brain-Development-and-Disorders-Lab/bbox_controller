#pragma once

#include <SDL3/SDL.h>

#include "display/text_renderer.h"
#include "hardware/gpio.h"

/// Draws a panel in the top left corner listing each GPIO channel with a green (active) or red (inactive) indicator
/// and the key that controls it when in simulation mode
/// @param top Distance from the top of the window in pixels, e.g. to sit below the banner
void drawStatusView(SDL_Renderer* renderer, TextRenderer& text, const Gpio& gpio, float top = 0.0f);
