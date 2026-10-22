#pragma once

#include <functional>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include <SDL3/SDL.h>

#include "display/text_renderer.h"

// Which display a stimulus is shown on, Left is the primary display
enum class DisplaySide { Left, Right, Both };

// Stimulus displays, on the Pi each connected display gets a fullscreen window. When simulating, two windows stand
// in for the Pi's primary (L) and secondary (R) displays.
class DisplayManager {
public:
    // Called after each display's content is drawn, for debug overlays. `index` is 0 for the primary display.
    using Overlay = std::function<void(size_t index, SDL_Renderer* renderer, TextRenderer& text)>;

    ~DisplayManager();

    /// Opens a fullscreen window per connected display, or two windows when simulating
    /// @return False if no display could be opened
    bool open(bool simulate);
    /// Destroys every window and its textures
    void close();

    /// Sets the lines of text centered on every display, below its title
    void setMessage(std::vector<std::string> lines);

    /// Shows or hides the title and message, hidden while a session runs so only stimuli are shown
    void setMessageVisible(bool visible);

    /// Shows an image scaled to fit, drawn over any fill
    /// @param image File name in `assets/stimuli`, PNG or BMP
    void showImage(DisplaySide side, const std::string& image);
    /// Sets the background color behind any image
    void fill(DisplaySide side, SDL_Color color);
    /// Removes the image and resets the background to black
    void clearStimuli(DisplaySide side = DisplaySide::Both);

    /// Fills every display with white for the display test, hiding everything else
    void setTestPattern(bool enabled);

    /// Draws and presents a frame on every display, paced to the primary display's refresh rate
    /// @param overlay Drawn last on each display, for debug overlays
    void render(const Overlay& overlay = {});

private:
    struct Display {
        SDL_Window* window = nullptr;
        SDL_Renderer* renderer = nullptr;
        std::unique_ptr<TextRenderer> text;
        std::string title;

        // Current stimulus, black with no image when cleared
        SDL_Color background = {0, 0, 0, 255};
        std::string image;

        // Loaded on first use, a failed load is cached as null so it is only reported once
        std::map<std::string, SDL_Texture*> textures;
    };

    /// Opens two windows side by side on the Mac's main screen
    /// @return False if a window couldn't be created
    bool openSimulated();
    /// Opens a fullscreen window on each connected display, skipping any that fail
    void openHardware();
    /// Takes ownership of the window and renderer, destroying them if the fonts fail to load
    /// @return False if the fonts failed to load
    bool addDisplay(SDL_Window* window, SDL_Renderer* renderer);
    /// Draws the title and message lines
    void drawMessage(Display& display) const;
    /// Draws the current image, loading and caching its texture on first use
    void drawImage(Display& display);

    /// Displays matching `side`, a missing right display is skipped
    std::vector<Display*> select(DisplaySide side);

    std::vector<Display> displays_;
    std::vector<std::string> message_;
    bool messageVisible_ = true;
    bool testPattern_ = false;
};
