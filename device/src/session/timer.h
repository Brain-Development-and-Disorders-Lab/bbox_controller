#pragma once

#include <algorithm>
#include <chrono>

using Clock = std::chrono::steady_clock;
using Milliseconds = std::chrono::milliseconds;

// Countdown checked from the main loop, e.g. `timer.start(Milliseconds(500))` then `if (timer.expired())`
class Timer {
public:
    /// Restarts the countdown from now
    void start(Milliseconds duration) { deadline_ = Clock::now() + duration; }

    /// True once the duration has passed, and before the first `start()`
    bool expired() const { return Clock::now() >= deadline_; }

    /// Time left, zero once expired
    Milliseconds remaining() const {
        return std::max(Milliseconds(0), std::chrono::duration_cast<Milliseconds>(deadline_ - Clock::now()));
    }

private:
    Clock::time_point deadline_ = Clock::now();
};
