#include "application.h"

#include <filesystem>
#include <set>
#include <system_error>

#include <sys/utsname.h>
#include <unistd.h>

#include <SDL3_ttf/SDL_ttf.h>
#include <spdlog/spdlog.h>

#include "hardware/pi_gpio.h"
#include "network/network_info.h"
#include "simulation/banner.h"
#include "simulation/controls.h"
#include "simulation/status_view.h"
#include "version.h"

namespace {
    std::unique_ptr<Gpio> createGpio(bool simulate) {
        if (simulate) {
            return std::make_unique<MockGpio>();
        }
        return std::make_unique<PiGpio>();
    }
}

Application::Application(std::string name, int port, bool simulate, std::shared_ptr<DashboardSink> logSink)
    : name_(std::move(name)),
      simulate_(simulate),
      address_(localIpAddress() + ":" + std::to_string(port)),
      gpio_(createGpio(simulate)),
      server_(port, std::move(logSink)),
      tests_(*gpio_, displays_,
             [this](const std::string& test, const std::string& state) {
                 server_.broadcast({{"type", "test_state"}, {"test", test}, {"state", state}});
             }),
      session_(*gpio_, displays_, storage_.root(),
               [this](const nlohmann::json& message) { server_.broadcast(message); }) {
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
        session_.update();
        syncClients();
        publishInputState();
        render();
    }

    spdlog::info("Shutting down...");
    session_.stop();
    gpio_->resetOutputs();
    server_.stop();
    displays_.close();
    TTF_Quit();
    SDL_Quit();
    return 0;
}

void Application::handleEvent(const SDL_Event& event) {
    // Closing either simulator window shuts down the device, SDL only sends a quit event once every window is closed
    if (event.type == SDL_EVENT_QUIT || event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED) {
        running_ = false;
        return;
    }

    // Esc is the kill switch on every target, a running session is stopped and recorded as the device shuts down
    if (event.type == SDL_EVENT_KEY_DOWN && event.key.scancode == SDL_SCANCODE_ESCAPE) {
        spdlog::info("Esc pressed, quitting");
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

    if (command == "session_start") {
        try {
            const auto& data = message.at("protocol");
            session_.start(parseProtocol(data), data, message.value("subject", ""));
        } catch (const std::exception& error) {
            spdlog::error("[Session] Invalid protocol: {}", error.what());
        }
    } else if (command == "session_stop") {
        session_.stop();
    } else if (command == "data_sync") {
        syncData(message.value("exclude", std::vector<std::string>{}));
    } else if (!tests_.start(command, message.value("parameter", 0))) {
        // Only the name, other fields can be large
        spdlog::warn("[Networking] Unknown command: \"{}\"", command);
    }
}

void Application::syncData(const std::vector<std::string>& exclude) {
    const std::set<std::string> existing(exclude.begin(), exclude.end());

    // Files of a session still being recorded are left for the next sync, since the dashboard never overwrites
    const std::string activeSession = session_.activeSessionPath();
    if (!activeSession.empty()) {
        spdlog::warn("[Storage] Skipping {} until its session ends", activeSession);
    }

    int sent = 0;
    for (const std::string& name : storage_.list()) {
        if (existing.count(name) || (!activeSession.empty() && name.rfind(activeSession + "/", 0) == 0)) {
            continue;
        }
        const auto contents = storage_.read(name);
        if (!contents) {
            continue;
        }
        try {
            server_.broadcast({{"type", "data_file"}, {"name", name}, {"contents", *contents}});
            sent++;
        } catch (const nlohmann::json::exception& error) {
            spdlog::error("[Storage] Unable to send {}: {}", name, error.what());
        }
    }

    spdlog::info("[Storage] Data sync sent {} file(s)", sent);
    server_.broadcast({{"type", "data_sync_complete"}});
}

void Application::syncClients() {
    // New dashboards are sent the device info and session state, and a fresh copy of the input state since it is only sent when it changes
    const int connectionCount = server_.connectionCount();
    if (connectionCount != lastConnectionCount_) {
        lastConnectionCount_ = connectionCount;
        lastInputState_ = nullptr;
        server_.broadcast(deviceInfo());
        session_.publishState();
    }

    const int clientCount = server_.clientCount();
    if (clientCount != lastClientCount_) {
        lastClientCount_ = clientCount;
        displays_.setMessage({clientCount > 0 ? "Connected to Dashboard" : "Waiting for connection...", name_, address_});
    }
}

nlohmann::json Application::deviceInfo() const {
    char hostname[256] = {};
    gethostname(hostname, sizeof(hostname) - 1);

    utsname system{};
    const std::string os = uname(&system) == 0 ? std::string(system.sysname) + " " + system.release : "Unknown";

    // Free space is a snapshot at connection time, -1 if it can't be read
    std::error_code error;
    const auto space = std::filesystem::space(storage_.root(), error);
    const long long storageFree = error ? -1 : static_cast<long long>(space.available);

    return {
        {"type", "device_info"},
        {"name", name_},
        {"version", kDeviceVersion},
        {"simulated", simulate_},
        {"hostname", hostname},
        {"os", os},
        {"started_at", std::chrono::duration_cast<std::chrono::milliseconds>(startedAt_.time_since_epoch()).count()},
        {"storage_free_bytes", storageFree},
    };
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
        displays_.render([this](size_t index, SDL_Renderer* renderer, TextRenderer& text) {
            const float bannerHeight = drawSimulationBanner(renderer, text);
            // Input status is shared by both displays, so only show it on the primary
            if (index == 0) {
                drawStatusView(renderer, text, *gpio_, bannerHeight);
            }
        });
    } else {
        displays_.render();
    }
}
