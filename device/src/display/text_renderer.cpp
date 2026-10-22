#include "display/text_renderer.h"

#include <spdlog/spdlog.h>

namespace {
    struct Style {
        const char* file;
        float pointSize;
    };

    // Indexed by `TextStyle`. Sizes are in points and scaled by the display's pixel density.
    constexpr std::array<Style, kTextStyleCount> kStyles = {{
        {"IBMPlexSans-SemiBold.ttf", 36.0f},  // Message
        {"IBMPlexMono-Regular.ttf", 20.0f},   // Address
        {"IBMPlexSans-SemiBold.ttf", 11.0f},  // Heading
        {"IBMPlexSans-Regular.ttf", 14.0f},   // Label
        {"IBMPlexMono-Regular.ttf", 12.0f},   // Detail
        {"IBMPlexSans-Regular.ttf", 22.0f},   // Title
    }};

    // Fonts are copied next to the executable by the makefile
    std::string fontPath(const char* file) {
        return std::string(SDL_GetBasePath()) + "assets/fonts/" + file;
    }
}

TextRenderer::TextRenderer(SDL_Renderer* renderer, float scale)
    : scale_(scale), engine_(TTF_CreateRendererTextEngine(renderer)) {
    for (size_t i = 0; i < kTextStyleCount; i++) {
        const std::string path = fontPath(kStyles[i].file);
        fonts_[i] = TTF_OpenFont(path.c_str(), kStyles[i].pointSize * scale);
        if (!fonts_[i]) {
            spdlog::error("[Display] Failed to load font {}: {}", path, SDL_GetError());
        }
    }
}

TextRenderer::~TextRenderer() {
    for (TTF_Font* font : fonts_) {
        TTF_CloseFont(font);
    }
    TTF_DestroyRendererTextEngine(engine_);
}

bool TextRenderer::ok() const {
    if (!engine_) {
        return false;
    }
    for (const TTF_Font* font : fonts_) {
        if (!font) {
            return false;
        }
    }
    return true;
}

SDL_FPoint TextRenderer::measure(const std::string& text, TextStyle style) {
    int width = 0;
    int height = 0;
    TTF_GetStringSize(fonts_[static_cast<size_t>(style)], text.c_str(), text.size(), &width, &height);
    return {static_cast<float>(width), static_cast<float>(height)};
}

void TextRenderer::draw(const std::string& text, TextStyle style, float x, float y, SDL_Color color) {
    // Glyphs are cached by the text engine, so creating a text object per draw is cheap
    TTF_Text* ttfText = TTF_CreateText(engine_, fonts_[static_cast<size_t>(style)], text.c_str(), text.size());
    if (!ttfText) {
        return;
    }
    TTF_SetTextColor(ttfText, color.r, color.g, color.b, color.a);
    TTF_DrawRendererText(ttfText, x, y);
    TTF_DestroyText(ttfText);
}
