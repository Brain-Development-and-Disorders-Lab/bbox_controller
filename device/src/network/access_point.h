#pragma once

#include <string>

/// Switches the Pi's Wi-Fi to a WPA2 access point with `name` as both the SSID and password, using NetworkManager.
/// Blocks until the access point is up, replacing any Wi-Fi network the Pi was connected to.
/// @param name A name accepted by `isValidDeviceName()`
/// @return False if the access point could not be started
bool startAccessPoint(const std::string& name);
