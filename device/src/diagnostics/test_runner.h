#pragma once

#include <chrono>
#include <functional>
#include <map>
#include <string>

#include "display/display_manager.h"
#include "hardware/gpio.h"

// Runs the hardware tests requested from the dashboard
class TestRunner {
public:
    using Reporter = std::function<void(const std::string& test, const std::string& state)>;

    TestRunner(Gpio& gpio, DisplayManager& displays, Reporter reporter);

    bool start(const std::string& test, int durationMs);

    // Call once per frame to finish tests that have passed or timed out
    void update();

private:
    using Clock = std::chrono::steady_clock;

    struct ActiveTest {
        Clock::time_point deadline;
        std::function<bool()> passed;   // Input tests only, checked every frame
        std::function<void()> cleanup;  // Output tests only, switches the hardware back off
    };

    void startOutputTest(const std::string& test, int durationMs, std::function<void(bool)> set);
    void startInputTest(const std::string& test, std::function<bool()> passed);
    void finish(const std::string& test, bool passed);

    Gpio& gpio_;
    DisplayManager& displays_;
    Reporter reporter_;
    std::map<std::string, ActiveTest> active_;
};
