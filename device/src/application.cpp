#include "application.h"

#include <SDL3_ttf/SDL_ttf.h>
#include <spdlog/spdlog.h>

#include "hardware/pi_gpio.h"
#include "network/network_info.h"
#include "simulation/banner.h"
#include "simulation/controls.h"
#include "simulation/status_view.h"

namespace {
    constexpr const char* kDataDirectory = "data";

    std::unique_ptr<Gpio> createGpio(bool simulate) {
        if (simulate) {
            return std::make_unique<MockGpio>();
        }
        return std::make_unique<PiGpio>();
    }
}

Application::Application(int port, bool simulate, std::shared_ptr<DashboardSink> logSink)
    : simulate_(simulate),
      address_(localIpAddress() + ":" + std::to_string(port)),
      gpio_(createGpio(simulate)),
      server_(port, std::move(logSink)),
      storage_(kDataDirectory),
      tests_(*gpio_, displays_,
             [this](const std::string& test, const std::string& state) {
                 server_.broadcast({{"type", "test_state"}, {"test", test}, {"state", state}});
             }),
      experiment_(*gpio_) {
    if (simulate_) {
        mockGpio_ = static_cast<MockGpio*>(gpio_.get());
    }
}

int Application::run() {
    if (!SDL_Init(SDL_INIT_VIDEO) || !TTF_Init()) {
        spdlog::error("[Display] Failed to initialize SDL: {}", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    if (!displays_.open(simulate_) || !server_.start()) {
        displays_.close();
        TTF_Quit();
        SDL_Quit();
        return 1;
    }

    while (running_) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            handleEvent(event);
        }

        for (const auto& message : server_.takeMessages()) {
            handleMessage(message);
        }

        tests_.update();
        experiment_.update();
        syncClients();
        publishInputState();
        render();
    }

    spdlog::info("Shutting down...");
    experiment_.stop();
    gpio_->resetOutputs();
    server_.stop();
    displays_.close();
    TTF_Quit();
    SDL_Quit();
    return 0;
}

void Application::handleEvent(const SDL_Event& event) {
    if (event.type == SDL_EVENT_QUIT) {
        running_ = false;
        return;
    }

    // When simulating, held keys represent for the device inputs and lights
    const bool keyDown = event.type == SDL_EVENT_KEY_DOWN;
    if (!mockGpio_ || !(keyDown || event.type == SDL_EVENT_KEY_UP) || event.key.repeat) {
        return;
    }

    for (const Control& control : kControls) {
        if (control.key != event.key.scancode) {
            continue;
        }
        if (const auto* input = std::get_if<Input>(&control.channel)) {
            mockGpio_->simulate(*input, keyDown);
        } else {
            mockGpio_->write(std::get<Output>(control.channel), keyDown);
        }
    }
}

void Application::handleMessage(const nlohmann::json& message) {
    const std::string command = message.value("command", "");

    if (command == "experiment_start") {
        try {
            auto experiment = message.at("experiment").get<Experiment>();
            storage_.save("experiments/" + experiment.id + ".json", message.at("experiment"));
            experiment_.start(std::move(experiment), message.value("animal_id", ""));
        } catch (const nlohmann::json::exception& error) {
            spdlog::error("[Experiment] Invalid experiment: {}", error.what());
        }
    } else if (command == "experiment_stop") {
        experiment_.stop();
    } else if (!tests_.start(command, message.value("parameter", 0))) {
        spdlog::warn("[Networking] Unknown command: {}", message.dump());
    }
}

void Application::syncClients() {
    // Input state is only sent when it changes, so new dashboards need a fresh copy
    const int connectionCount = server_.connectionCount();
    if (connectionCount != lastConnectionCount_) {
        lastConnectionCount_ = connectionCount;
        lastInputState_ = nullptr;
    }

    const int clientCount = server_.clientCount();
    if (clientCount != lastClientCount_) {
        lastClientCount_ = clientCount;
        displays_.setMessage({clientCount > 0 ? "Connected to Dashboard" : "Waiting for connection...", address_});
    }
}

void Application::publishInputState() {
    nlohmann::json state;
    for (size_t i = 0; i < kInputCount; i++) {
        state[kInputNames[i]] = gpio_->read(static_cast<Input>(i));
    }
    for (size_t i = 0; i < kOutputCount; i++) {
        state[kOutputNames[i]] = gpio_->state(static_cast<Output>(i));
    }

    if (state != lastInputState_) {
        server_.broadcast({{"type", "input_state"}, {"state", state}});
        lastInputState_ = std::move(state);
    }
}

void Application::render() {
    if (mockGpio_) {
        displays_.render([this](SDL_Renderer* renderer, TextRenderer& text) {
            const float bannerHeight = drawSimulationBanner(renderer, text);
            drawStatusView(renderer, text, *gpio_, bannerHeight);
        });
    } else {
        displays_.render();
    }
}
