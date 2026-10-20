#pragma once

#include <SDL3/SDL.h>

#include "display/text_renderer.h"

// Draws an orange strip across the top of the window signalling that device is running in simulation mode
float drawSimulationBanner(SDL_Renderer* renderer, TextRenderer& text);
