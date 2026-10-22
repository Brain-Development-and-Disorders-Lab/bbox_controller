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

    /// @param reporter Called with each change of a test's state, "running", "passed", or "failed"
    TestRunner(Gpio& gpio, DisplayManager& displays, Reporter reporter);

    /// Starts a hardware test, restarting it if it is already running
    /// @param test Command name from `shared/commands.json`, e.g. "test_water_delivery"
    /// @param durationMs How long an output test stays on, input tests wait up to 10 s regardless
    /// @return False if `test` isn't a known test
    bool start(const std::string& test, int durationMs);

    /// Finishes tests that have passed or timed out, call once per frame
    void update();

private:
    using Clock = std::chrono::steady_clock;

    struct ActiveTest {
        Clock::time_point deadline;
        std::function<bool()> passed;   // Input tests only, checked every frame
        std::function<void()> cleanup;  // Output tests only, switches the hardware back off
    };

    /// Switches an output on, passing once `durationMs` is up
    /// @param set Switches the output under test on or off
    void startOutputTest(const std::string& test, int durationMs, std::function<void(bool)> set);
    /// Waits for an input, failing if it isn't triggered before the timeout
    /// @param passed Checked every frame, true once the input has been triggered
    void startInputTest(const std::string& test, std::function<bool()> passed);
    /// Switches off any output under test and reports the result
    void finish(const std::string& test, bool passed);

    Gpio& gpio_;
    DisplayManager& displays_;
    Reporter reporter_;
    std::map<std::string, ActiveTest> active_;
};
