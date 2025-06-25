#!/bin/bash

# This script creates a WiFi access point using the `linux-router` tool

set -e

# Configuration
SSID="BehaviorBox_0"
PASSWORD="behaviorbox0"
INTERFACE="wlan0"
CHANNEL="7"
COUNTRY="US"

echo "====================================="
echo "Behavior Box: WiFi Access Point Setup"
echo "====================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Install dependencies if not present
if ! command -v curl >/dev/null 2>&1; then
    echo "Installing curl..."
    apt update && apt install -y curl iptables
fi

# Download linux-router if not present
if [ ! -f "/tmp/lnxrouter" ]; then
    echo "Downloading linux-router..."
    curl -L -o /tmp/lnxrouter https://raw.githubusercontent.com/garywill/linux-router/master/lnxrouter
    chmod +x /tmp/lnxrouter
fi

# Stop any existing access point
echo "Stopping any existing access point..."
/tmp/lnxrouter --stop "$INTERFACE" 2>/dev/null || true
sleep 2

# Start the WiFi access point
echo "Starting WiFi access point..."
echo "SSID: $SSID"
echo "Password: $PASSWORD"
echo "IP Address: 192.168.4.1"
echo ""

/tmp/lnxrouter --ap "$INTERFACE" "$SSID" -p "$PASSWORD" \
    -c "$CHANNEL" \
    --country "$COUNTRY" \
    -g 192.168.4.1 \
    --dhcp-dns 8.8.8.8,8.8.4.4

echo ""
echo "WiFi access point is running!"
echo "Connect to '$SSID' with password '$PASSWORD'"
echo "Device will be available at 192.168.4.1:8765"
echo ""
echo "To stop: sudo /tmp/lnxrouter --stop $INTERFACE"
