#include "network/access_point.h"

#include <cerrno>
#include <cstring>

#include <spawn.h>
#include <sys/wait.h>

#include <spdlog/spdlog.h>

extern char** environ;

namespace {
    constexpr const char* kInterface = "wlan0";
    // Reused on each start, so the Pi keeps a single hotspot connection whatever the name
    constexpr const char* kConnectionName = "bbox-hotspot";
}

bool startAccessPoint(const std::string& name) {
    spdlog::info("[Networking] Starting access point \"{}\" on {}", name, kInterface);

    // nmcli creates the connection, or updates it with the new SSID and password, then activates it. Arguments are
    // passed directly rather than through a shell.
    const char* args[] = {"nmcli",  "device",       "wifi", "hotspot",    "ifname",   kInterface,
                          "con-name", kConnectionName, "ssid", name.c_str(), "password", name.c_str(), nullptr};
    pid_t pid = 0;
    const int spawnError = posix_spawnp(&pid, args[0], nullptr, nullptr, const_cast<char* const*>(args), environ);
    if (spawnError != 0) {
        spdlog::error("[Networking] Unable to run nmcli: {}", std::strerror(spawnError));
        return false;
    }

    int status = 0;
    while (waitpid(pid, &status, 0) == -1) {
        if (errno != EINTR) {
            spdlog::error("[Networking] Unable to wait for nmcli: {}", std::strerror(errno));
            return false;
        }
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        spdlog::error("[Networking] nmcli failed to start the access point (exit status {})",
                      WIFEXITED(status) ? WEXITSTATUS(status) : -1);
        return false;
    }

    spdlog::info("[Networking] Access point \"{}\" started", name);
    return true;
}
