#pragma once

#include <SDL3/SDL.h>

#include "display/text_renderer.h"

/// Draws an orange strip across the top of the window signalling that the device is running in simulation mode
/// @return Height of the banner in pixels, for placing content below it
float drawSimulationBanner(SDL_Renderer* renderer, TextRenderer& text);
