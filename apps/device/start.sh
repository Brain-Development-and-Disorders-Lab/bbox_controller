#!/bin/bash

# Behavior Box: Device Startup Script
# Author: Henry Burgess <henry.burgess@wustl.edu>
# Date: 2025-10-31
# Description:
#   This script acts as a single entry point to start the device controller software,
#   setting up the Python environment and starting the device controller process.

set -e

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$(dirname "$APP_DIR")")"
LOGFILE="$APP_DIR/logs/device.log"
RUN_PID=""

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

# Cleanup routine to stop background processes
cleanup() {
    if [ -n "$RUN_PID" ] && kill -0 "$RUN_PID" 2>/dev/null; then
        log INFO "Stopping device controller process PID: $RUN_PID"
        kill "$RUN_PID" 2>/dev/null || true
    fi
}

# Initialize logging
mkdir -p "$APP_DIR/logs"
log INFO "Behavior Box: Device Controller Startup"
log INFO "Repository root: $REPO_DIR"

# Check if running as root (required for GPIO access on Raspberry Pi)
if [[ $EUID -ne 0 ]]; then
    log ERROR "This script must be run as root (use sudo)"
    exit 1
fi

# Set up trap for cleanup on exit
trap cleanup EXIT SIGINT SIGTERM

# Activate Python virtual environment if present
VENV_PATH="$REPO_DIR/venvs/device"
if [ -d "$VENV_PATH" ]; then
    log INFO "Activating Python virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
else
    log WARN "No virtual environment found, using system Python"
fi

# Change to packages directory and start device controller in background
cd "$REPO_DIR/packages"
log INFO "Starting device controller with PYTHONPATH: $REPO_DIR/packages"
PYTHONPATH="$REPO_DIR/packages" python device/main.py &
RUN_PID=$!
log INFO "Device controller started with PID: $RUN_PID"
log INFO "Logs: $LOGFILE"

# Wait for device controller process to complete
wait $RUN_PID
