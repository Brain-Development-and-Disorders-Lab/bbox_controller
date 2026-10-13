#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include <SDL3/SDL.h>

#include "display/text_renderer.h"

// Stimulus displays, on the Pi each connected display gets a fullscreen window, or a single window when simulating
class DisplayManager {
public:
    // Called after each display's content is drawn, for debug overlays
    using Overlay = std::function<void(SDL_Renderer* renderer, TextRenderer& text)>;

    ~DisplayManager();

    bool open(bool simulate);
    void close();

    // Lines of text centered on every display
    void setMessage(std::vector<std::string> lines);

    // Fill every display with white, used by the display test
    void setTestPattern(bool enabled);

    void render(const Overlay& overlay = {});

private:
    struct Display {
        SDL_Window* window;
        SDL_Renderer* renderer;
        std::unique_ptr<TextRenderer> text;
    };

    bool addDisplay(SDL_Window* window, SDL_Renderer* renderer);
    void drawMessage(Display& display) const;

    std::vector<Display> displays_;
    std::vector<std::string> message_;
    bool testPattern_ = false;
};
