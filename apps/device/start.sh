#!/bin/bash

# Behavior Box: Device Startup Script
# Author: Henry Burgess <henry.burgess@wustl.edu>
# Date: 2025-10-31
# Description:
#   This script acts as a single entry point to start the device controller software,
#   setting up the Python environment and starting the device controller process.

# Configuration
set -e
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # apps/device
REPO_DIR="$(dirname "$(dirname "$APP_DIR")")"
PACKAGES_DIR="$REPO_DIR/packages/device" # packages/device
LOGFILE="$APP_DIR/logs/device.log"

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

# Start device controller
start_device_controller() {
    # Activate Python virtual environment if present
    if [ -d "$REPO_DIR/venvs/device" ]; then
        log INFO "Activating Python virtual environment: $REPO_DIR/venvs/device"
        source "$REPO_DIR/venvs/device/bin/activate"
    else
        log WARN "No virtual environment found, using system Python"
    fi

    # Change to the script directory
    cd "$PACKAGES_DIR"

    # Set PYTHONPATH to include `packages/device` directory and run the device controller
    log INFO "Starting device controller with PYTHONPATH: $PACKAGES_DIR"
    PYTHONPATH="$PACKAGES_DIR" python main.py
}

# Cleanup routine to stop background processes
cleanup() {
    log INFO "Cleaning up background processes..."

    # Kill any background jobs
    if [ -n "$(jobs -p)" ]; then
        kill $(jobs -p) 2>/dev/null || true
    fi

    if [ -n "$RUN_PID" ] && kill -0 $RUN_PID 2>/dev/null; then
        kill $RUN_PID
        log INFO "Stopped device controller process PID: $RUN_PID"
    fi
}

# Initialize logging
mkdir -p "$APP_DIR/logs"

log INFO "Behavior Box: Device Controller Startup"
log INFO "Repository root: $REPO_DIR"
log INFO "Application directory: $APP_DIR"
log INFO "Packages directory: $PACKAGES_DIR"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log ERROR "This script must be run as root"
    exit 1
fi

# Set up trap for cleanup
trap cleanup EXIT SIGINT SIGTERM

log INFO "Starting device controller..."
start_device_controller &
RUN_PID=$!
log INFO "Device controller started with PID: $RUN_PID"
log INFO "Logs: $APP_DIR/logs/device.log"

# Wait for device controller process to complete
wait $RUN_PID
