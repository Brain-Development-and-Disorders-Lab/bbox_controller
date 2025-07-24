#!/bin/bash

# This script sets up the WiFi AP and starts the device controller, both in the background.
# It waits for the AP SSID to be visible before starting the device controller.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/startup.log"
SSID="BehaviorBox_0"
PASSWORD="behaviorbox0"
INTERFACE="wlan0"
CHANNEL="7"
COUNTRY="US"
MAX_ATTEMPTS=15
SLEEP_BETWEEN=2

set -e

mkdir -p "$SCRIPT_DIR/logs"

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

log INFO "============================"
log INFO "Behavior Box: Startup Script"
log INFO "============================"
log INFO "Script directory: $SCRIPT_DIR"
log INFO "Timestamp: $(date)"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log ERROR "This script must be run as root (use sudo)"
    exit 1
fi

# Function to check for internet connectivity
check_internet() {
    if ping -c 1 -W 2 github.com >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to set up AP (runs in background)
setup_ap() {
    log INFO "Setting up WiFi Access Point..."
    # Check for internet connectivity
    if check_internet; then
        ONLINE=1
        log INFO "Internet connectivity detected."
    else
        ONLINE=0
        log WARN "No internet connectivity detected. Running in offline mode."
    fi
    # Install dependencies if not present (only if online)
    if ! command -v curl >/dev/null 2>&1; then
        if [ $ONLINE -eq 1 ]; then
            log WARN "curl not found. Installing curl and iptables..."
            apt update && apt install -y curl iptables
        else
            log WARN "curl not found and no internet connection. Skipping install."
        fi
    fi
    # Download linux-router if not present (only if online)
    if [ ! -f "/tmp/lnxrouter" ]; then
        if [ $ONLINE -eq 1 ]; then
            log INFO "Downloading linux-router..."
            curl -L -o /tmp/lnxrouter https://raw.githubusercontent.com/garywill/linux-router/master/lnxrouter
            chmod +x /tmp/lnxrouter
        else
            log WARN "linux-router not found and no internet connection. Will attempt to use any existing local version."
        fi
    fi
    # Disable wireless connectivity
    log INFO "Disabling wireless connectivity on $INTERFACE..."
    ip link set $INTERFACE down
    sleep 2
    # Stop any existing access point
    log INFO "Stopping any existing access point on $INTERFACE..."
    /tmp/lnxrouter --stop "$INTERFACE" 2>/dev/null || true
    sleep 2
    # Stop any running instance of `dnsmasq`
    log INFO "Stopping any existing dnsmasq process..."
    systemctl stop dnsmasq 2>/dev/null || true
    sleep 2
    # Start the WiFi access point
    if [ -f "/tmp/lnxrouter" ]; then
        log INFO "Starting WiFi access point: SSID='$SSID', Password='$PASSWORD', Channel='$CHANNEL', Country='$COUNTRY'"
        /tmp/lnxrouter --ap "$INTERFACE" "$SSID" -p "$PASSWORD" \
            -c "$CHANNEL" \
            --country "$COUNTRY" \
            -g 192.168.4.1 \
            --dhcp-dns 8.8.8.8,8.8.4.4
        log INFO "WiFi access point process completed."
    else
        log ERROR "linux-router is not available. Cannot start AP."
        exit 1
    fi
}

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    grep -q 'Raspberry Pi' /proc/device-tree/model 2>/dev/null || \
    grep -q 'Raspberry Pi' /sys/firmware/devicetree/base/model 2>/dev/null
}

# Start AP setup in background only if on Raspberry Pi
if is_raspberry_pi; then
    log INFO "Raspberry Pi detected. Launching AP setup in background..."
    setup_ap > "$SCRIPT_DIR/logs/setup_ap.log" 2>&1 &
    AP_PID=$!
    log INFO "AP setup process started with PID $AP_PID."

    # Prompt user to connect to AP and wait for acknowledgment
    log INFO "Please connect your computer to the WiFi Access Point (SSID: $SSID, Password: $PASSWORD)."
    log INFO "Once connected, press Enter to continue."
    read -p "[User Action Required] Press Enter to continue after connecting to the AP..."
    log INFO "User acknowledged AP connection. Continuing with device controller startup."
else
    log WARN "Not running on a Raspberry Pi. Skipping AP setup."
    AP_PID="N/A"
fi

# Start device controller in background (merged logic from device_controller.sh)
start_device_controller() {
    log INFO "Preparing to start device controller..."
    # Check for and activate Python virtual environment if present
    VENV_PATH=""
    CURRENT_DIR="$SCRIPT_DIR"
    while [ "$CURRENT_DIR" != "/" ]; do
        if [ -d "$CURRENT_DIR/.venv" ]; then
            VENV_PATH="$CURRENT_DIR/.venv"
            break
        elif [ -d "$CURRENT_DIR/venv" ]; then
            VENV_PATH="$CURRENT_DIR/venv"
            break
        fi
        CURRENT_DIR="$(dirname "$CURRENT_DIR")"
    done
    if [ -n "$VENV_PATH" ]; then
        log INFO "Activating Python virtual environment: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
        log INFO "Virtual environment activated: $(which python)"
    else
        log WARN "No virtual environment found, using system Python"
    fi
    log INFO "==============================="
    log INFO "Behavior Box: Device Controller"
    log INFO "==============================="
    log INFO "Script directory: $SCRIPT_DIR"
    log INFO "Timestamp: $(date)"
    log INFO "Starting device controller..."
    # Change to the script directory
    cd "$SCRIPT_DIR"
    # Set PYTHONPATH to include the repository root (where .venv is located)
    REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
    log INFO "Repository root: $REPO_ROOT"
    log INFO "PYTHONPATH: $REPO_ROOT/src"
    # Set PYTHONPATH to include `src` directory and run the device
    PYTHONPATH="$REPO_ROOT/src" python main.py
}

log INFO "Starting device controller in background..."
start_device_controller > "$SCRIPT_DIR/logs/device_controller.log" 2>&1 &
RUN_PID=$!
log INFO "Device controller started with PID $RUN_PID."

log INFO "Startup complete. PIDs: ap=$AP_PID, run=$RUN_PID"
log INFO "Logs available at:"
log INFO "  - $SCRIPT_DIR/logs/startup.log (this file)"
log INFO "  - $SCRIPT_DIR/logs/setup_ap.log (AP setup)"
log INFO "  - $SCRIPT_DIR/logs/device_controller.log (device controller)"

# Cleanup routine to stop background processes
cleanup() {
    log INFO "Cleaning up background processes..."
    if [ "$AP_PID" != "N/A" ] && [ -n "$AP_PID" ] && kill -0 $AP_PID 2>/dev/null; then
        kill $AP_PID
        log INFO "Stopped AP process (PID $AP_PID)."
    fi
    if [ -n "$RUN_PID" ] && kill -0 $RUN_PID 2>/dev/null; then
        kill $RUN_PID
        log INFO "Stopped device controller process (PID $RUN_PID)."
    fi
}
trap cleanup EXIT SIGINT SIGTERM

# Optionally, wait for both processes (uncomment if you want the script to block)
wait $RUN_PID
