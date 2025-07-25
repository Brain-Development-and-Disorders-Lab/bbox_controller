#!/bin/bash

# =============================================================================
# Behavior Box: Device Script
# =============================================================================
# This script sets up a WiFi access point and starts the device controller
# on a Raspberry Pi device. It handles both online and offline scenarios.
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/startup.log"
INTERFACE="wlan0"
CHANNEL="7"
COUNTRY="US"

# Enable test mode if --test is present
if [[ "$1" == "--test" ]]; then
    # Use different SSID and password for test mode
    SSID="BehaviorBox_TEST"
    PASSWORD="behaviorboxtest"
    TEST_MODE=true
else
    SSID="BehaviorBox_0"
    PASSWORD="behaviorbox0"
    TEST_MODE=false
fi

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

# Function to check for internet connectivity
check_internet() {
    if ping -c 1 -W 2 github.com >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    grep -q 'Raspberry Pi' /proc/device-tree/model 2>/dev/null || \
    grep -q 'Raspberry Pi' /sys/firmware/devicetree/base/model 2>/dev/null
}

# =============================================================================
# WIFI ACCESS POINT SETUP
# =============================================================================

# Function to set up AP (runs in background)
setup_ap() {
    log INFO "Setting up WiFi Access Point..."

    # Check for internet connectivity
    if check_internet; then
        ONLINE=1
        log INFO "Internet connectivity detected"
    else
        ONLINE=0
        log WARN "No internet connectivity detected, running in offline mode"
    fi

    # Install dependencies if not present (only if online)
    if ! command -v curl >/dev/null 2>&1; then
        if [ $ONLINE -eq 1 ]; then
            log WARN "Dependencies not found, installing curl and iptables..."
            apt update && apt install -y curl iptables
        else
            log WARN "Dependencies not found and no internet connection, exiting..."
            exit 1
        fi
    fi

    # Download linux-router if not present (only if online)
    if [ ! -f "/tmp/lnxrouter" ]; then
        if [ $ONLINE -eq 1 ]; then
            log INFO "Downloading linux-router..."
            curl -L -o /tmp/lnxrouter https://raw.githubusercontent.com/garywill/linux-router/master/lnxrouter
            chmod +x /tmp/lnxrouter
        else
            log WARN "linux-router not found and no internet connection, exiting..."
            exit 1
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
        log INFO "WiFi access point process started..."
    else
        log ERROR "WiFi access point process failed to start, exiting..."
        exit 1
    fi
}

# =============================================================================
# DEVICE CONTROLLER SETUP
# =============================================================================

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
    else
        log WARN "No virtual environment found, using system Python"
    fi

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

# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

# Cleanup routine to stop background processes and restore WiFi
cleanup() {
    log INFO "Cleaning up background processes and restoring WiFi..."

    # Kill any waiting read command (user input prompt)
    if [ -n "$(jobs -p)" ]; then
        kill $(jobs -p) 2>/dev/null || true
    fi

    # Stop background processes
    if [ "$AP_PID" != "N/A" ] && [ -n "$AP_PID" ] && kill -0 $AP_PID 2>/dev/null; then
        kill $AP_PID
        log INFO "Stopped AP process PID: $AP_PID"
    fi
    if [ -n "$RUN_PID" ] && kill -0 $RUN_PID 2>/dev/null; then
        kill $RUN_PID
        log INFO "Stopped device controller process PID: $RUN_PID"
    fi

    # Restore WiFi interface to normal operation
    if is_raspberry_pi; then
        log INFO "Restoring WiFi interface $INTERFACE to normal operation..."

        # Stop any running access point
        if [ -f "/tmp/lnxrouter" ]; then
            log INFO "Stopping access point on $INTERFACE..."
            /tmp/lnxrouter --stop "$INTERFACE" 2>/dev/null || true
            sleep 2
        fi

        # Stop dnsmasq if it was started by the AP
        log INFO "Stopping dnsmasq service..."
        systemctl stop dnsmasq 2>/dev/null || true
        sleep 1

        # Bring interface back up
        log INFO "Bringing interface $INTERFACE back up..."
        ip link set $INTERFACE up 2>/dev/null || true
        sleep 1

        # Restart networking services if available
        if command -v systemctl >/dev/null 2>&1; then
            log INFO "Restarting networking services..."
            systemctl restart networking 2>/dev/null || true
            systemctl restart wpa_supplicant 2>/dev/null || true
        fi

        log INFO "WiFi interface restoration started, please allow 1-2 minutes to complete"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Initialize logging
mkdir -p "$SCRIPT_DIR/logs"

log INFO "======================================================"
log INFO "    Behavior Box: Device Controller Startup Script    "
log INFO "======================================================"
log INFO "Directory: $SCRIPT_DIR"
log INFO "Timestamp: $(date)"
if [ "$TEST_MODE" = true ]; then
    log INFO "Mode: TEST (SSID: $SSID)"
else
    log INFO "Mode: PRODUCTION (SSID: $SSID)"
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log ERROR "This script must be run as root"
    exit 1
fi

# Set up trap for cleanup
trap cleanup EXIT SIGINT SIGTERM

# Start AP setup in background only if on Raspberry Pi
if is_raspberry_pi; then
    log INFO "Raspberry Pi detected, launching AP setup in background..."
    setup_ap > "$SCRIPT_DIR/logs/ap.log" 2>&1 &
    AP_PID=$!
    log INFO "AP setup process started with PID: $AP_PID"

    # Prompt user to connect to AP and wait for acknowledgment
    log INFO "Please connect your computer to the WiFi Access Point (SSID: $SSID, Password: $PASSWORD)"
    read -p "[ACTION REQUIRED] Press Enter to continue after connecting to $SSID"
    log INFO "Continuing with device controller startup..."
else
    log WARN "Not running on a Raspberry Pi, skipping AP setup"
    AP_PID="N/A"
fi

log INFO "Starting device controller..."
start_device_controller > "$SCRIPT_DIR/logs/run.log" 2>&1 &
RUN_PID=$! # Store PID of device controller process
log INFO "Device controller started with PID: $RUN_PID"

log INFO "Startup complete, PIDS:"
log INFO "  - WiFi access point: $AP_PID"
log INFO "  - Device controller: $RUN_PID"
log INFO "Logs available at:"
log INFO "  - $SCRIPT_DIR/logs/startup.log"
log INFO "  - $SCRIPT_DIR/logs/ap.log"
log INFO "  - $SCRIPT_DIR/logs/run.log"

# Wait for device controller process to complete
wait $RUN_PID
