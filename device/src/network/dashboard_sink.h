#pragma once

#include <chrono>
#include <mutex>
#include <set>
#include <string>

#include <ixwebsocket/IXWebSocket.h>
#include <nlohmann/json.hpp>
#include <spdlog/details/circular_q.h>
#include <spdlog/sinks/base_sink.h>

// spdlog sink that forwards log messages to connected dashboards as JSON messages:
//   { "type": "log", "level": "info", "timestamp": <ms since epoch>, "message": "..." }
// Recent messages are kept in a ring buffer and replayed to each dashboard when it connects
class DashboardSink final : public spdlog::sinks::base_sink<std::mutex> {
public:
    explicit DashboardSink(size_t historySize) : history_(historySize) {}

    // Replay history to `client`, then start forwarding live messages to it
    void addClient(ix::WebSocket& client) {
        std::lock_guard<std::mutex> lock(mutex_);
        for (size_t i = 0; i < history_.size(); i++) {
            client.sendUtf8Text(history_.at(i));
        }
        clients_.insert(&client);
    }

    void removeClient(ix::WebSocket& client) {
        std::lock_guard<std::mutex> lock(mutex_);
        clients_.erase(&client);
    }

protected:
    void sink_it_(const spdlog::details::log_msg& msg) override {
        const auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(msg.time.time_since_epoch());
        const auto level = spdlog::level::to_string_view(msg.level);
        const nlohmann::json record = {
            {"type", "log"},
            {"level", std::string(level.data(), level.size())},
            {"timestamp", timestamp.count()},
            {"message", std::string(msg.payload.data(), msg.payload.size())},
        };

        // Replace invalid UTF-8 rather than throwing from inside the logger
        std::string payload = record.dump(-1, ' ', false, nlohmann::json::error_handler_t::replace);

        for (ix::WebSocket* client : clients_) {
            client->sendUtf8Text(payload);
        }
        history_.push_back(std::move(payload));
    }

    void flush_() override {}

private:
    spdlog::details::circular_q<std::string> history_;
    std::set<ix::WebSocket*> clients_;
};
