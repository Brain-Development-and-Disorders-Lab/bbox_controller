#pragma once

#include <memory>
#include <string>

#include <SDL3/SDL.h>
#include <nlohmann/json.hpp>

#include "diagnostics/test_runner.h"
#include "display/display_manager.h"
#include "experiment/experiment_runner.h"
#include "hardware/gpio.h"
#include "hardware/mock_gpio.h"
#include "network/device_server.h"
#include "storage/storage.h"

// All device components and management of the the main loop
class Application {
public:
    Application(int port, bool simulate, std::shared_ptr<DashboardSink> logSink);

    int run();

private:
    void handleEvent(const SDL_Event& event);
    void handleMessage(const nlohmann::json& message);
    void syncClients();
    void publishInputState();
    void render();

    bool simulate_;
    std::string address_;
    std::unique_ptr<Gpio> gpio_;
    MockGpio* mockGpio_ = nullptr;  // Set when simulating, for keyboard input
    DisplayManager displays_;
    DeviceServer server_;
    Storage storage_;
    TestRunner tests_;
    ExperimentRunner experiment_;

    bool running_ = true;
    int lastClientCount_ = -1;
    int lastConnectionCount_ = 0;
    nlohmann::json lastInputState_;
};
