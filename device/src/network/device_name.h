#pragma once

#include <string>

/// A new name of the form "bbox_device_<ID>", where ID is 8 random uppercase letters and digits
std::string generateDeviceName();

/// Whether `name` can be used as the device name. The name is also the access point's SSID and password, so it must be
/// 8 to 32 characters (the WPA2 password minimum and SSID maximum) of letters, digits, `_`, or `-`.
bool isValidDeviceName(const std::string& name);
