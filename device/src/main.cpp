#include <cstdlib>
#include <memory>
#include <string>

#include <spdlog/async.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/spdlog.h>

#include "application.h"
#include "network/access_point.h"
#include "network/dashboard_sink.h"
#include "network/device_name.h"
#include "version.h"

namespace {
    constexpr int kDefaultPort = 8765;
    constexpr size_t kLogHistorySize = 200;

    #ifdef TARGET_PI
        constexpr bool kSimulate = false;
    #else
        constexpr bool kSimulate = true;
    #endif
}

int main(int argc, char* argv[]) {
    // Log to the console and to connected dashboards
    auto dashboardSink = std::make_shared<DashboardSink>(kLogHistorySize);
    spdlog::init_thread_pool(8192, 1);
    auto logger = std::make_shared<spdlog::async_logger>(
        "device",
        spdlog::sinks_init_list{std::make_shared<spdlog::sinks::stdout_color_sink_mt>(), dashboardSink},
        spdlog::thread_pool(),
        spdlog::async_overflow_policy::overrun_oldest);
    spdlog::set_default_logger(logger);

    spdlog::info("Behavior Box Device v{}", kDeviceVersion);
    if (kSimulate) {
        spdlog::info("[Target: macOS] Simulating hardware with the keyboard.");
    } else {
        spdlog::info("[Target: Raspberry Pi] Running on ARM Linux.");
    }

    // Arguments are `[--name <name>] [port]`
    int port = kDefaultPort;
    std::string name;
    for (int i = 1; i < argc; i++) {
        const std::string arg = argv[i];
        if (arg == "--name") {
            if (i + 1 >= argc) {
                spdlog::error("--name requires a value");
                spdlog::shutdown();
                return 1;
            }
            name = argv[++i];
        } else {
            port = std::atoi(arg.c_str());
            if (port <= 0 || port > 65535) {
                spdlog::error("Invalid port: {}", arg);
                spdlog::shutdown();
                return 1;
            }
        }
    }

    // Without --name the device names itself, so the name changes on each start
    if (name.empty()) {
        name = generateDeviceName();
    } else if (!isValidDeviceName(name)) {
        spdlog::error("Invalid name: \"{}\", it must be 8 to 32 letters, digits, '_', or '-'", name);
        spdlog::shutdown();
        return 1;
    }
    spdlog::info("Device name: {}", name);

    // The access point is started before the application so the displays show the access point's address. If it
    // fails the device keeps running on its existing network.
    if (!kSimulate) {
        startAccessPoint(name);
    }

    const int result = Application(name, port, kSimulate, dashboardSink).run();
    spdlog::shutdown();
    return result;
}
