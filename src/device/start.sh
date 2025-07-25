#!/bin/bash

# Behavior Box Device Controller Startup Script
# Sets up WiFi access point and starts the device controller

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/startup.log"

# WiFi Access Point Configuration
SSID="BehaviorBox_0"
PASSWORD="behaviorbox0"
INTERFACE="wlan0"
CHANNEL="7"
COUNTRY="US"

# =============================================================================
# COMMAND LINE ARGUMENTS
# =============================================================================

TEST_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --test|-t)
            TEST_MODE=true
            SSID="BehaviorBox_TEST"
            PASSWORD="behaviorboxtest"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--test]"
            echo "  --test    Use test SSID and password"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# =============================================================================
# SETUP AND VALIDATION
# =============================================================================

mkdir -p "$SCRIPT_DIR/logs"

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

log INFO "================================================"
log INFO "        Behavior Box: Device Controller         "
log INFO "================================================"
log INFO "Directory: $SCRIPT_DIR"
log INFO "Mode: $([ "$TEST_MODE" = true ] && echo "TEST" || echo "PRODUCTION")"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log ERROR "This script must be run as root"
    exit 1
fi

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Check for internet connectivity
check_internet() {
    ping -c 1 -W 2 github.com >/dev/null 2>&1
}

# Check if running on Raspberry Pi
is_raspberry_pi() {
    grep -q 'Raspberry Pi' /proc/device-tree/model 2>/dev/null || \
    grep -q 'Raspberry Pi' /sys/firmware/devicetree/base/model 2>/dev/null
}

# Find linux-router executable
find_linux_router() {
    for path in "/tmp/lnxrouter" "/usr/local/bin/lnxrouter" "/usr/bin/lnxrouter" "$SCRIPT_DIR/lnxrouter"; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

# =============================================================================
# WIFI ACCESS POINT SETUP
# =============================================================================

setup_wifi_ap() {
    log INFO "Setting up WiFi access point..."

    # Check internet connectivity
    if check_internet; then
        log INFO "Internet connectivity detected"
        ONLINE=true
    else
        log WARN "No internet connectivity detected"
        ONLINE=false
    fi

    # Install dependencies if needed
    if ! command -v curl >/dev/null 2>&1; then
        if [ "$ONLINE" = true ]; then
            log WARN "Installing missing dependencies..."
            apt update && apt install -y curl iptables
        else
            log WARN "Missing dependencies and no internet connection, exiting..."
            exit 1
        fi
    fi

    # Find or download linux-router
    LNXROUTER_PATH=$(find_linux_router)
    if [ -z "$LNXROUTER_PATH" ]; then
        if [ "$ONLINE" = true ]; then
            log WARN "Downloading linux-router..."
            if curl -L -o /tmp/lnxrouter https://raw.githubusercontent.com/garywill/linux-router/master/lnxrouter; then
                chmod +x /tmp/lnxrouter
                LNXROUTER_PATH="/tmp/lnxrouter"
                log INFO "Successfully downloaded linux-router"
            else
                log ERROR "Failed to download linux-router, exiting..."
                exit 1
            fi
        else
            log ERROR "No linux-router found and no internet connection, exiting..."
            exit 1
        fi
    else
        log INFO "Found linux-router at: $LNXROUTER_PATH"
    fi

    # Configure wireless interface
    log INFO "Configuring wireless interface..."
    ip link set $INTERFACE down
    sleep 2

    # Stop existing services
    "$LNXROUTER_PATH" --stop "$INTERFACE" 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    sleep 2

    # Start access point
    log INFO "Starting WiFi access point..."
    "$LNXROUTER_PATH" --ap "$INTERFACE" "$SSID" -p "$PASSWORD" \
        -c "$CHANNEL" \
        --country "$COUNTRY" \
        -g 192.168.4.1 \
        --dhcp-dns 8.8.8.8,8.8.4.4

    log INFO "WiFi access point started successfully"
}

# =============================================================================
# DEVICE CONTROLLER SETUP
# =============================================================================

start_device_controller() {
    log INFO "Starting device controller..."

    # Find and activate virtual environment
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
        log INFO "Activating virtual environment: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    else
        log WARN "No virtual environment found, using system Python"
    fi

    # Set up environment and start controller
    cd "$SCRIPT_DIR"
    REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
    PYTHONPATH="$REPO_ROOT/src" python main.py
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Start WiFi access point if on Raspberry Pi
if is_raspberry_pi; then
    log INFO "Raspberry Pi detected, starting WiFi access point..."
    setup_wifi_ap > "$SCRIPT_DIR/logs/setup_ap.log" 2>&1 &
    AP_PID=$!
    log INFO "WiFi access point started with PID: $AP_PID"

    log INFO "Please connect to WiFi (SSID: $SSID, Password: $PASSWORD)"
    read -p "[USER ACTION] Press Enter after connecting to WiFi..."
else
    log WARN "Not on Raspberry Pi, skipping WiFi setup"
    AP_PID="N/A"
fi

# Start device controller
start_device_controller > "$SCRIPT_DIR/logs/device_controller.log" 2>&1 &
CONTROLLER_PID=$!
log INFO "Device controller started with PID: $CONTROLLER_PID"

# =============================================================================
# CLEANUP AND MONITORING
# =============================================================================

log INFO "Startup complete - AP PID: $AP_PID, Controller PID: $CONTROLLER_PID"
log INFO "Logs: $SCRIPT_DIR/logs/"

cleanup() {
    log INFO "Cleaning up processes..."
    [ "$AP_PID" != "N/A" ] && [ -n "$AP_PID" ] && kill -0 $AP_PID 2>/dev/null && kill $AP_PID
    [ -n "$CONTROLLER_PID" ] && kill -0 $CONTROLLER_PID 2>/dev/null && kill $CONTROLLER_PID
}
trap cleanup EXIT SIGINT SIGTERM

# Wait for device controller to complete
wait $CONTROLLER_PID
