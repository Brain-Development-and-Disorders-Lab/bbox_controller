#include <cstdlib>
#include <memory>

#include <spdlog/async.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/spdlog.h>

#include "application.h"
#include "network/dashboard_sink.h"
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

    // Optional first argument overrides the listening port
    const int port = argc > 1 ? std::atoi(argv[1]) : kDefaultPort;
    if (port <= 0 || port > 65535) {
        spdlog::error("Invalid port: {}", argv[1]);
        spdlog::shutdown();
        return 1;
    }

    const int result = Application(port, kSimulate, dashboardSink).run();
    spdlog::shutdown();
    return result;
}
