#include <atomic>
#include <chrono>
#include <csignal>
#include <iostream>
#include <thread>

#include <ixwebsocket/IXNetSystem.h>
#include <ixwebsocket/IXWebSocketServer.h>

namespace {
    constexpr int kDefaultPort = 8765;
    constexpr const char* kBindHost = "0.0.0.0";

    std::atomic<bool> g_keepRunning{true};

    void HandleShutdownSignal(int) {
        g_keepRunning = false;
    }
}

int main() {
    std::iostream::sync_with_stdio(false);
    std::cout << "Behavior Box Device" << std::endl;

    #ifdef TARGET_PI
        std::cout << "[Target: Raspberry Pi] Running on ARM Linux." << std::endl;
    #else
        std::cout << "[Target: macOS] Simulating functionality on Mac." << std::endl;
    #endif

    std::signal(SIGINT, HandleShutdownSignal);
    std::signal(SIGTERM, HandleShutdownSignal);

    ix::initNetSystem();

    ix::WebSocketServer server(kDefaultPort, kBindHost);
    server.disablePerMessageDeflate();

    server.setOnClientMessageCallback(
        [](std::shared_ptr<ix::ConnectionState> connectionState, ix::WebSocket& webSocket,
           const ix::WebSocketMessagePtr& msg) {
            if (msg->type == ix::WebSocketMessageType::Open) {
                std::cout << "[Networking] Client connected: " << connectionState->getRemoteIp() << std::endl;
            } else if (msg->type == ix::WebSocketMessageType::Close) {
                std::cout << "[Networking] Client disconnected" << std::endl;
            } else if (msg->type == ix::WebSocketMessageType::Message) {
                std::cout << "[Networking] Received: " << msg->str << std::endl;
            }
        });

    auto result = server.listen();
    if (!result.first) {
        std::cerr << "[Networking] Failed to listen: " << result.second << std::endl;
        return 1;
    }

    std::cout << "[Networking] Listening on ws://" << kBindHost << ":" << kDefaultPort << std::endl;
    server.start();

    while (g_keepRunning) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    std::cout << "[Networking] Shutting down..." << std::endl;
    server.stop();

    return 0;
}
