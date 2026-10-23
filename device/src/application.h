#pragma once

#include <chrono>
#include <memory>
#include <string>
#include <vector>

#include <SDL3/SDL.h>
#include <nlohmann/json.hpp>

#include "diagnostics/test_runner.h"
#include "display/display_manager.h"
#include "hardware/gpio.h"
#include "hardware/mock_gpio.h"
#include "network/device_server.h"
#include "session/session_runner.h"
#include "storage/storage.h"

// All device components and management of the the main loop
class Application {
public:
    /// @param name Device name, shown on the displays and sent to dashboards
    /// @param port WebSocket port the dashboard connects to
    /// @param simulate Use mock GPIO and windowed displays instead of the Pi hardware
    /// @param logSink Forwards log messages to connected dashboards
    Application(std::string name, int port, bool simulate, std::shared_ptr<DashboardSink> logSink);

    /// Opens the displays and server, then runs the main loop until a window is closed or Esc is pressed
    /// @return Process exit code, non-zero if startup failed
    int run();

private:
    /// Handles quitting (Esc or closing a window) and, when simulating, the keys standing in for the hardware
    void handleEvent(const SDL_Event& event);
    /// Dispatches a dashboard command to the session, data sync, or hardware tests
    void handleMessage(const nlohmann::json& message);
    /// Sends stored files as `data_file` messages, then `data_sync_complete`
    /// @param exclude Files the dashboard already has, named as by `Storage::list()`
    void syncData(const std::vector<std::string>& exclude);
    /// Brings new dashboards up to date and shows the connection state on the displays
    void syncClients();
    /// The `device_info` message sent to each dashboard when it connects
    nlohmann::json deviceInfo() const;
    /// Broadcasts every input and output state, only when one has changed
    void publishInputState();
    /// Draws a frame on every display, with the simulator overlays when simulating
    void render();

    std::string name_;
    bool simulate_;
    std::chrono::system_clock::time_point startedAt_ = std::chrono::system_clock::now();
    std::string address_;
    std::unique_ptr<Gpio> gpio_;
    MockGpio* mockGpio_ = nullptr;  // Set when simulating, for keyboard input
    DisplayManager displays_;
    DeviceServer server_;
    Storage storage_;
    TestRunner tests_;
    SessionRunner session_;

    bool running_ = true;
    int lastClientCount_ = -1;
    int lastConnectionCount_ = 0;
    nlohmann::json lastInputState_;
};
