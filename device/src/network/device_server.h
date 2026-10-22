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
    /// @param logSink Has dashboards added and removed as they connect, so they receive the log
    DeviceServer(int port, std::shared_ptr<DashboardSink> logSink);
    ~DeviceServer();

    /// Starts listening on every interface in a background thread
    /// @return False if the port couldn't be bound
    bool start();
    void stop();

    /// Messages received since the last call, oldest first, safe to call from the main loop
    std::vector<nlohmann::json> takeMessages();

    /// Sends `message` to every connected dashboard
    void broadcast(const nlohmann::json& message);
    /// Dashboards currently connected
    int clientCount() const { return clientCount_; }

    /// Total connections since starting, used to spot new clients even if another left
    int connectionCount() const { return connectionCount_; }

private:
    /// Tracks connections and queues valid JSON objects for `takeMessages()`, runs on the server's threads
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
