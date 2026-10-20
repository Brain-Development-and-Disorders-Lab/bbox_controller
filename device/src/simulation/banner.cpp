#include "simulation/banner.h"

#include <string>

namespace {
    constexpr float kHeight = 24.0f;
    constexpr const char* kText = "Simulation Mode Active";

    // Matches Blueprint's ORANGE3 used by the dashboard
    constexpr SDL_Color kBackgroundColor = {200, 118, 25, 255};
    constexpr SDL_Color kTextColor = {255, 255, 255, 255};
}

float drawSimulationBanner(SDL_Renderer* renderer, TextRenderer& text) {
    int width = 0;
    int height = 0;
    SDL_GetCurrentRenderOutputSize(renderer, &width, &height);

    const float bannerHeight = kHeight * text.scale();
    const SDL_FRect banner = {0.0f, 0.0f, static_cast<float>(width), bannerHeight};
    SDL_SetRenderDrawColor(renderer, kBackgroundColor.r, kBackgroundColor.g, kBackgroundColor.b, kBackgroundColor.a);
    SDL_RenderFillRect(renderer, &banner);

    const SDL_FPoint size = text.measure(kText, TextStyle::Heading);
    text.draw(kText, TextStyle::Heading, (width - size.x) / 2.0f, (bannerHeight - size.y) / 2.0f, kTextColor);
    return bannerHeight;
}
