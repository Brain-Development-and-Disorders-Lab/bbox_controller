#pragma once

#include <atomic>
#include <memory>
#include <mutex>
#include <vector>

#include <ixwebsocket/IXWebSocketServer.h>
#include <nlohmann/json.hpp>

#include "network/dashboard_sink.h"

// WebSocket server the dashboard connects to
class DeviceServer {
public:
    DeviceServer(int port, std::shared_ptr<DashboardSink> logSink);
    ~DeviceServer();

    bool start();
    void stop();

    // Messages received since the last call, oldest first
    std::vector<nlohmann::json> takeMessages();

    void broadcast(const nlohmann::json& message);
    int clientCount() const { return clientCount_; }

    // Total connections since starting, used to spot new clients even if another left
    int connectionCount() const { return connectionCount_; }
    int port() const { return port_; }

private:
    void onMessage(std::shared_ptr<ix::ConnectionState> connectionState, ix::WebSocket& webSocket,
                   const ix::WebSocketMessagePtr& msg);

    int port_;
    ix::WebSocketServer server_;
    std::shared_ptr<DashboardSink> logSink_;
    std::atomic<int> clientCount_{0};
    std::atomic<int> connectionCount_{0};

    std::mutex inboxMutex_;
    std::vector<nlohmann::json> inbox_;
};
