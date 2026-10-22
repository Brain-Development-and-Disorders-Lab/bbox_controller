#include "display/display_manager.h"

#include <algorithm>

#include <spdlog/spdlog.h>

namespace {
    // Each simulated display is sized so both fit side by side on a laptop screen
    constexpr int kSimulatorWidth = 720;
    constexpr int kSimulatorHeight = 450;
    constexpr int kSimulatorGap = 16;
    constexpr int kMaxDisplays = 2;

    // Stimulus images, copied next to the executable by the makefile
    constexpr const char* kStimuliDirectory = "assets/stimuli/";

    constexpr SDL_Color kTitleColor = {150, 150, 150, 255};
    constexpr SDL_Color kMessageColor = {255, 255, 255, 255};
    constexpr SDL_Color kAddressColor = {150, 150, 150, 255};
}

DisplayManager::~DisplayManager() {
    close();
}

bool DisplayManager::open(bool simulate) {
    if (simulate) {
        if (!openSimulated()) {
            return false;
        }
    } else {
        openHardware();
    }

    if (displays_.empty()) {
        return false;
    }

    // Pace the main loop to the first display's refresh rate
    SDL_SetRenderVSync(displays_.front().renderer, 1);
    spdlog::info("[Display] Opened {} display(s)", displays_.size());
    return true;
}

bool DisplayManager::openSimulated() {
    // Place the windows side by side, centered on the Mac's main screen, primary (L) on the left
    SDL_Rect usable = {0, 0, kSimulatorWidth * kMaxDisplays, kSimulatorHeight};
    SDL_GetDisplayUsableBounds(SDL_GetPrimaryDisplay(), &usable);
    const int totalWidth = kSimulatorWidth * kMaxDisplays + kSimulatorGap * (kMaxDisplays - 1);
    const int left = usable.x + std::max(0, (usable.w - totalWidth) / 2);
    const int top = usable.y + std::max(0, (usable.h - kSimulatorHeight) / 2);

    for (int i = 0; i < kMaxDisplays; i++) {
        const std::string title = "Behavior Box - Display " + std::to_string(i + 1) + (i == 0 ? " (L)" : " (R)");
        SDL_Window* window = nullptr;
        SDL_Renderer* renderer = nullptr;
        if (!SDL_CreateWindowAndRenderer(title.c_str(), kSimulatorWidth, kSimulatorHeight,
                                         SDL_WINDOW_HIGH_PIXEL_DENSITY, &window, &renderer)) {
            spdlog::error("[Display] Failed to create window: {}", SDL_GetError());
            return false;
        }
        SDL_SetWindowPosition(window, left + i * (kSimulatorWidth + kSimulatorGap), top);
        if (!addDisplay(window, renderer)) {
            return false;
        }
    }
    return true;
}

void DisplayManager::openHardware() {
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

void DisplayManager::close() {
    for (Display& display : displays_) {
        // Text and textures belong to the renderer, so release them first
        display.text.reset();
        for (auto& [name, texture] : display.textures) {
            SDL_DestroyTexture(texture);
        }
        SDL_DestroyRenderer(display.renderer);
        SDL_DestroyWindow(display.window);
    }
    displays_.clear();
}

void DisplayManager::setMessage(std::vector<std::string> lines) {
    message_ = std::move(lines);
}

void DisplayManager::setMessageVisible(bool visible) {
    messageVisible_ = visible;
}

void DisplayManager::showImage(DisplaySide side, const std::string& image) {
    for (Display* display : select(side)) {
        display->image = image;
    }
}

void DisplayManager::fill(DisplaySide side, SDL_Color color) {
    for (Display* display : select(side)) {
        display->background = color;
    }
}

void DisplayManager::clearStimuli(DisplaySide side) {
    for (Display* display : select(side)) {
        display->background = {0, 0, 0, 255};
        display->image.clear();
    }
}

void DisplayManager::setTestPattern(bool enabled) {
    testPattern_ = enabled;
}

void DisplayManager::render(const Overlay& overlay) {
    for (size_t i = 0; i < displays_.size(); i++) {
        Display& display = displays_[i];
        const SDL_Color background = testPattern_ ? SDL_Color{255, 255, 255, 255} : display.background;
        SDL_SetRenderDrawColor(display.renderer, background.r, background.g, background.b, background.a);
        SDL_RenderClear(display.renderer);

        if (!testPattern_) {
            drawImage(display);
            if (messageVisible_) {
                drawMessage(display);
            }
        }

        if (overlay) {
            overlay(i, display.renderer, *display.text);
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
    Display& display = displays_.emplace_back();
    display.window = window;
    display.renderer = renderer;
    display.text = std::move(text);
    display.title = "Display " + std::to_string(displays_.size());
    return true;
}

void DisplayManager::drawMessage(Display& display) const {
    int width = 0;
    int height = 0;
    SDL_GetCurrentRenderOutputSize(display.renderer, &width, &height);

    // The display's title sits above the headline, any lines after the headline are details in a monospaced font
    struct Line {
        const std::string& text;
        TextStyle style;
        SDL_Color color;
    };
    std::vector<Line> lines = {{display.title, TextStyle::Title, kTitleColor}};
    for (size_t i = 0; i < message_.size(); i++) {
        lines.push_back(i == 0 ? Line{message_[i], TextStyle::Message, kMessageColor}
                               : Line{message_[i], TextStyle::Address, kAddressColor});
    }

    TextRenderer& text = *display.text;
    const float gap = 12.0f * text.scale();
    float totalHeight = 0.0f;
    for (size_t i = 0; i < lines.size(); i++) {
        totalHeight += text.measure(lines[i].text, lines[i].style).y + (i > 0 ? gap : 0.0f);
    }

    float y = (height - totalHeight) / 2.0f;
    for (const Line& line : lines) {
        const SDL_FPoint size = text.measure(line.text, line.style);
        text.draw(line.text, line.style, (width - size.x) / 2.0f, y, line.color);
        y += size.y + gap;
    }
}

void DisplayManager::drawImage(Display& display) {
    if (display.image.empty()) {
        return;
    }

    auto it = display.textures.find(display.image);
    if (it == display.textures.end()) {
        const std::string path = std::string(SDL_GetBasePath()) + kStimuliDirectory + display.image;
        SDL_Texture* texture = nullptr;
        if (SDL_Surface* surface = SDL_LoadSurface(path.c_str())) {
            texture = SDL_CreateTextureFromSurface(display.renderer, surface);
            SDL_DestroySurface(surface);
        }
        if (!texture) {
            spdlog::error("[Display] Failed to load image {}: {}", path, SDL_GetError());
        }
        it = display.textures.emplace(display.image, texture).first;
    }
    if (!it->second) {
        return;
    }

    // Scale to fit, preserving the aspect ratio, and center
    int width = 0;
    int height = 0;
    SDL_GetCurrentRenderOutputSize(display.renderer, &width, &height);
    float imageWidth = 0.0f;
    float imageHeight = 0.0f;
    SDL_GetTextureSize(it->second, &imageWidth, &imageHeight);
    const float scale = std::min(width / imageWidth, height / imageHeight);
    const SDL_FRect destination = {
        (width - imageWidth * scale) / 2.0f,
        (height - imageHeight * scale) / 2.0f,
        imageWidth * scale,
        imageHeight * scale,
    };
    SDL_RenderTexture(display.renderer, it->second, nullptr, &destination);
}

std::vector<DisplayManager::Display*> DisplayManager::select(DisplaySide side) {
    std::vector<Display*> selected;
    for (size_t i = 0; i < displays_.size(); i++) {
        const bool left = i == 0;
        if (side == DisplaySide::Both || (side == DisplaySide::Left) == left) {
            selected.push_back(&displays_[i]);
        }
    }
    return selected;
}
