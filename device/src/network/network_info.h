#pragma once

#include <string>

/// First IPv4 address on an active, non-loopback interface, or "127.0.0.1" if there is none
std::string localIpAddress();
