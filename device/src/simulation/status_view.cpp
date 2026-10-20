#include "simulation/status_view.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include "simulation/controls.h"

namespace {
    // Layout in points, scaled by the display's pixel density
    constexpr float kMargin = 16.0f;
    constexpr float kPadding = 14.0f;
    constexpr float kRowHeight = 26.0f;
    constexpr float kDotRadius = 5.0f;
    constexpr float kColumnGap = 10.0f;
    constexpr int kDotSegments = 24;

    // Matches Blueprint's GREEN3 and RED3 used by the dashboard's status indicators
    constexpr SDL_FColor kActiveColor = {0.137f, 0.522f, 0.318f, 1.0f};
    constexpr SDL_FColor kInactiveColor = {0.804f, 0.259f, 0.275f, 1.0f};

    constexpr SDL_Color kHeadingColor = {140, 140, 140, 255};
    constexpr SDL_Color kLabelColor = {235, 235, 235, 255};
    constexpr SDL_Color kKeyColor = {120, 120, 120, 255};

    std::string keyHint(const Control& control) {
        return control.keyName ? std::string(control.keyName) : "";
    }

    // SDL has no circle primitive, so draw the indicator as a triangle fan
    void fillCircle(SDL_Renderer* renderer, float cx, float cy, float radius, SDL_FColor color) {
        std::vector<SDL_Vertex> vertices;
        std::vector<int> indices;
        vertices.push_back({{cx, cy}, color, {0, 0}});
        for (int i = 0; i < kDotSegments; i++) {
            const float angle = 2.0f * static_cast<float>(M_PI) * i / kDotSegments;
            vertices.push_back({{cx + radius * std::cos(angle), cy + radius * std::sin(angle)}, color, {0, 0}});
            indices.insert(indices.end(), {0, i + 1, (i + 1) % kDotSegments + 1});
        }
        SDL_RenderGeometry(renderer, nullptr, vertices.data(), static_cast<int>(vertices.size()), indices.data(),
                           static_cast<int>(indices.size()));
    }
}

void drawStatusView(SDL_Renderer* renderer, TextRenderer& text, const Gpio& gpio, float top) {
    const float scale = text.scale();
    const float margin = kMargin * scale;
    const float padding = kPadding * scale;
    const float rowHeight = kRowHeight * scale;
    const float dotRadius = kDotRadius * scale;
    const float gap = kColumnGap * scale;

    // Size the columns to fit the widest label and key hint
    float labelWidth = 0.0f;
    float keyWidth = 0.0f;
    for (const Control& control : kControls) {
        labelWidth = std::max(labelWidth, text.measure(control.label, TextStyle::Label).x);
        keyWidth = std::max(keyWidth, text.measure(keyHint(control), TextStyle::Detail).x);
    }

    const std::string heading = "INPUT STATUS";
    const float headingHeight = text.measure(heading, TextStyle::Heading).y;
    const float contentWidth = std::max(dotRadius * 2 + gap + labelWidth + gap * 2 + keyWidth,
                                        text.measure(heading, TextStyle::Heading).x);
    const SDL_FRect panel = {
        margin,
        top + margin,
        contentWidth + padding * 2,
        padding * 2 + headingHeight + gap + rowHeight * kControls.size(),
    };

    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 24, 24, 24, 230);
    SDL_RenderFillRect(renderer, &panel);
    SDL_SetRenderDrawColor(renderer, 60, 60, 60, 255);
    SDL_RenderRect(renderer, &panel);

    const float left = panel.x + padding;
    const float right = panel.x + panel.w - padding;
    text.draw(heading, TextStyle::Heading, left, panel.y + padding, kHeadingColor);

    // Divider under the heading
    const float dividerY = panel.y + padding + headingHeight + gap / 2;
    SDL_RenderLine(renderer, left, dividerY, right, dividerY);

    float rowTop = dividerY + gap / 2;
    for (const Control& control : kControls) {
        const float centerY = rowTop + rowHeight / 2;
        fillCircle(renderer, left + dotRadius, centerY, dotRadius,
                   isActive(gpio, control.channel) ? kActiveColor : kInactiveColor);

        const SDL_FPoint labelSize = text.measure(control.label, TextStyle::Label);
        text.draw(control.label, TextStyle::Label, left + dotRadius * 2 + gap, centerY - labelSize.y / 2,
                  kLabelColor);

        // Key hints are right-aligned in their own column
        const std::string key = keyHint(control);
        const SDL_FPoint keySize = text.measure(key, TextStyle::Detail);
        text.draw(key, TextStyle::Detail, right - keySize.x, centerY - keySize.y / 2, kKeyColor);

        rowTop += rowHeight;
    }
}
