#include "display/display_manager.h"

#include <spdlog/spdlog.h>

namespace {
    constexpr int kSimulatorWidth = 1024;
    constexpr int kSimulatorHeight = 640;
    constexpr int kMaxDisplays = 2;

    constexpr SDL_Color kMessageColor = {255, 255, 255, 255};
    constexpr SDL_Color kAddressColor = {150, 150, 150, 255};
}

DisplayManager::~DisplayManager() {
    close();
}

bool DisplayManager::open(bool simulate) {
    if (simulate) {
        SDL_Window* window = nullptr;
        SDL_Renderer* renderer = nullptr;
        if (!SDL_CreateWindowAndRenderer("Behavior Box", kSimulatorWidth, kSimulatorHeight,
                                         SDL_WINDOW_HIGH_PIXEL_DENSITY, &window, &renderer)) {
            spdlog::error("[Display] Failed to create window: {}", SDL_GetError());
            return false;
        }
        if (!addDisplay(window, renderer)) {
            return false;
        }
    } else {
        int count = 0;
        SDL_DisplayID* ids = SDL_GetDisplays(&count);
        for (int i = 0; i < count && i < kMaxDisplays; i++) {
            SDL_Rect bounds;
            SDL_GetDisplayBounds(ids[i], &bounds);

            SDL_Window* window = SDL_CreateWindow("Behavior Box", bounds.w, bounds.h,
                                                  SDL_WINDOW_FULLSCREEN | SDL_WINDOW_BORDERLESS);
            SDL_Renderer* renderer = window ? SDL_CreateRenderer(window, nullptr) : nullptr;
            if (!renderer) {
                spdlog::error("[Display] Failed to open display {}: {}", i, SDL_GetError());
                SDL_DestroyWindow(window);
                continue;
            }
            SDL_SetWindowPosition(window, bounds.x, bounds.y);
            addDisplay(window, renderer);
        }
        SDL_free(ids);
        SDL_HideCursor();
    }

    if (displays_.empty()) {
        return false;
    }

    // Pace the main loop to the first display's refresh rate
    SDL_SetRenderVSync(displays_.front().renderer, 1);
    spdlog::info("[Display] Opened {} display(s)", displays_.size());
    return true;
}

void DisplayManager::close() {
    for (Display& display : displays_) {
        // Text resources belong to the renderer, so release them first
        display.text.reset();
        SDL_DestroyRenderer(display.renderer);
        SDL_DestroyWindow(display.window);
    }
    displays_.clear();
}

void DisplayManager::setMessage(std::vector<std::string> lines) {
    message_ = std::move(lines);
}

void DisplayManager::setTestPattern(bool enabled) {
    testPattern_ = enabled;
}

void DisplayManager::render(const Overlay& overlay) {
    for (Display& display : displays_) {
        if (testPattern_) {
            SDL_SetRenderDrawColor(display.renderer, 255, 255, 255, 255);
        } else {
            SDL_SetRenderDrawColor(display.renderer, 0, 0, 0, 255);
        }
        SDL_RenderClear(display.renderer);

        // Stimuli will be drawn here once experiments are implemented
        if (!testPattern_) {
            drawMessage(display);
        }

        if (overlay) {
            overlay(display.renderer, *display.text);
        }
        SDL_RenderPresent(display.renderer);
    }
}

bool DisplayManager::addDisplay(SDL_Window* window, SDL_Renderer* renderer) {
    auto text = std::make_unique<TextRenderer>(renderer, SDL_GetWindowPixelDensity(window));
    if (!text->ok()) {
        text.reset();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        return false;
    }
    displays_.push_back({window, renderer, std::move(text)});
    return true;
}

void DisplayManager::drawMessage(Display& display) const {
    if (message_.empty()) {
        return;
    }

    int width = 0;
    int height = 0;
    SDL_GetCurrentRenderOutputSize(display.renderer, &width, &height);

    // The first line is the headline, any following lines are details in a monospaced font
    TextRenderer& text = *display.text;
    const float gap = 12.0f * text.scale();
    float totalHeight = 0.0f;
    for (size_t i = 0; i < message_.size(); i++) {
        const TextStyle style = i == 0 ? TextStyle::Message : TextStyle::Address;
        totalHeight += text.measure(message_[i], style).y + (i > 0 ? gap : 0.0f);
    }

    float y = (height - totalHeight) / 2.0f;
    for (size_t i = 0; i < message_.size(); i++) {
        const TextStyle style = i == 0 ? TextStyle::Message : TextStyle::Address;
        const SDL_FPoint size = text.measure(message_[i], style);
        text.draw(message_[i], style, (width - size.x) / 2.0f, y, i == 0 ? kMessageColor : kAddressColor);
        y += size.y + gap;
    }
}
