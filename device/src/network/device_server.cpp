#include "network/device_server.h"

#include <utility>

#include <ixwebsocket/IXNetSystem.h>
#include <spdlog/spdlog.h>

namespace {
    constexpr const char* kBindHost = "0.0.0.0";
}

DeviceServer::DeviceServer(int port, std::shared_ptr<DashboardSink> logSink)
    : port_(port), server_(port, kBindHost), logSink_(std::move(logSink)) {
    server_.disablePerMessageDeflate();
    server_.setOnClientMessageCallback(
        [this](std::shared_ptr<ix::ConnectionState> connectionState, ix::WebSocket& webSocket,
               const ix::WebSocketMessagePtr& msg) { onMessage(std::move(connectionState), webSocket, msg); });
}

DeviceServer::~DeviceServer() {
    stop();
}

bool DeviceServer::start() {
    ix::initNetSystem();

    auto result = server_.listen();
    if (!result.first) {
        spdlog::error("[Networking] Failed to listen: {}", result.second);
        return false;
    }

    server_.start();
    spdlog::info("[Networking] Listening on ws://{}:{}", kBindHost, port_);
    return true;
}

void DeviceServer::stop() {
    server_.stop();
}

std::vector<nlohmann::json> DeviceServer::takeMessages() {
    std::lock_guard<std::mutex> lock(inboxMutex_);
    return std::exchange(inbox_, {});
}

void DeviceServer::broadcast(const nlohmann::json& message) {
    const std::string payload = message.dump();
    for (const auto& client : server_.getClients()) {
        client->sendUtf8Text(payload);
    }
}

void DeviceServer::onMessage(std::shared_ptr<ix::ConnectionState> connectionState, ix::WebSocket& webSocket,
                             const ix::WebSocketMessagePtr& msg) {
    if (msg->type == ix::WebSocketMessageType::Open) {
        logSink_->addClient(webSocket);
        clientCount_++;
        connectionCount_++;
        spdlog::info("[Networking] Client connected: {}", connectionState->getRemoteIp());
    } else if (msg->type == ix::WebSocketMessageType::Close) {
        logSink_->removeClient(webSocket);
        clientCount_--;
        spdlog::info("[Networking] Client disconnected");
    } else if (msg->type == ix::WebSocketMessageType::Message) {
        auto message = nlohmann::json::parse(msg->str, nullptr, false);
        if (message.is_discarded() || !message.is_object()) {
            spdlog::warn("[Networking] Ignoring malformed message: {}", msg->str);
            return;
        }
        std::lock_guard<std::mutex> lock(inboxMutex_);
        inbox_.push_back(std::move(message));
    }
}
