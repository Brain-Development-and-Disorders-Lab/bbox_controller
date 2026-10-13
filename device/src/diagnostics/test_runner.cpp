#include "diagnostics/test_runner.h"

#include <utility>
#include <vector>

#include <spdlog/spdlog.h>

namespace {
    constexpr std::chrono::seconds kInputTestTimeout{10};
}

TestRunner::TestRunner(Gpio& gpio, DisplayManager& displays, Reporter reporter)
    : gpio_(gpio), displays_(displays), reporter_(std::move(reporter)) {}

bool TestRunner::start(const std::string& test, int durationMs) {
    // Restarting a test cancels the previous run
    if (auto it = active_.find(test); it != active_.end()) {
        if (it->second.cleanup) {
            it->second.cleanup();
        }
        active_.erase(it);
    }

    if (test == "test_water_delivery") {
        startOutputTest(test, durationMs, [this](bool on) { gpio_.write(Output::WaterValve, on); });
    } else if (test == "test_led_levers") {
        startOutputTest(test, durationMs, [this](bool on) {
            gpio_.write(Output::LeftLeverLight, on);
            gpio_.write(Output::RightLeverLight, on);
        });
    } else if (test == "test_led_port") {
        startOutputTest(test, durationMs, [this](bool on) { gpio_.write(Output::NoseLight, on); });
    } else if (test == "test_displays") {
        startOutputTest(test, durationMs, [this](bool on) { displays_.setTestPattern(on); });
    } else if (test == "test_input_levers") {
        // Both levers need to be pressed at some point, not necessarily together
        startInputTest(test, [this, left = false, right = false]() mutable {
            left = left || gpio_.read(Input::LeftLever);
            right = right || gpio_.read(Input::RightLever);
            return left && right;
        });
    } else if (test == "test_input_ir") {
        startInputTest(test, [this]() { return gpio_.read(Input::NosePoke); });
    } else {
        return false;
    }

    spdlog::info("[Test] Started {}", test);
    reporter_(test, "running");
    return true;
}

void TestRunner::update() {
    const auto now = Clock::now();

    // Collect first, since finishing a test modifies `active_`
    std::vector<std::pair<std::string, bool>> finished;
    for (auto& [test, active] : active_) {
        if (active.passed && active.passed()) {
            finished.emplace_back(test, true);
        } else if (now >= active.deadline) {
            // Output tests pass once their duration is up, input tests fail if not triggered
            finished.emplace_back(test, !active.passed);
        }
    }

    for (const auto& [test, passed] : finished) {
        finish(test, passed);
    }
}

void TestRunner::startOutputTest(const std::string& test, int durationMs, std::function<void(bool)> set) {
    set(true);
    active_[test] = {Clock::now() + std::chrono::milliseconds(durationMs), nullptr, [set]() { set(false); }};
}

void TestRunner::startInputTest(const std::string& test, std::function<bool()> passed) {
    active_[test] = {Clock::now() + kInputTestTimeout, std::move(passed), nullptr};
}

void TestRunner::finish(const std::string& test, bool passed) {
    auto it = active_.find(test);
    if (it->second.cleanup) {
        it->second.cleanup();
    }
    active_.erase(it);

    if (passed) {
        spdlog::info("[Test] {} passed", test);
    } else {
        spdlog::warn("[Test] {} failed", test);
    }
    reporter_(test, passed ? "passed" : "failed");
}
