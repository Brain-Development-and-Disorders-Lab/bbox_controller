#include "network/network_info.h"

#include <arpa/inet.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <netinet/in.h>

std::string localIpAddress() {
    std::string result = "127.0.0.1";

    ifaddrs* interfaces = nullptr;
    if (getifaddrs(&interfaces) != 0) {
        return result;
    }

    for (ifaddrs* entry = interfaces; entry; entry = entry->ifa_next) {
        const bool usable = entry->ifa_addr && entry->ifa_addr->sa_family == AF_INET &&
                            (entry->ifa_flags & IFF_UP) && !(entry->ifa_flags & IFF_LOOPBACK);
        if (!usable) {
            continue;
        }

        char address[INET_ADDRSTRLEN];
        const auto* ipv4 = reinterpret_cast<sockaddr_in*>(entry->ifa_addr);
        if (inet_ntop(AF_INET, &ipv4->sin_addr, address, sizeof(address))) {
            result = address;
            break;
        }
    }

    freeifaddrs(interfaces);
    return result;
}
