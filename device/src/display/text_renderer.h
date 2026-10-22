#pragma once

#include <array>
#include <string>

#include <SDL3/SDL.h>
#include <SDL3_ttf/SDL_ttf.h>

// Text styles used on the device, all set in IBM Plex
enum class TextStyle { Message, Address, Heading, Label, Detail, Title };
constexpr size_t kTextStyleCount = 6;

// Draws text on one renderer with SDL3_ttf
class TextRenderer {
public:
    /// Loads a font for every style, check `ok()` afterwards
    /// @param scale Pixel density of the display, font sizes are multiplied by it
    TextRenderer(SDL_Renderer* renderer, float scale);
    ~TextRenderer();

    TextRenderer(const TextRenderer&) = delete;
    TextRenderer& operator=(const TextRenderer&) = delete;

    /// False if a font failed to load
    bool ok() const;
    float scale() const { return scale_; }

    /// Size of `text` in pixels
    SDL_FPoint measure(const std::string& text, TextStyle style);
    /// Draws `text` with its top-left corner at `x`, `y` in pixels
    void draw(const std::string& text, TextStyle style, float x, float y, SDL_Color color);

private:
    float scale_;
    TTF_TextEngine* engine_;
    std::array<TTF_Font*, kTextStyleCount> fonts_{};
};
