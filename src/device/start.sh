#!/bin/bash

# =============================================================================
# Behavior Box: Device Startup Script
# =============================================================================
# This script acts as a single entry point to start the device controller
# software, setting up the Python environment.
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/device.log"

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


# =============================================================================
# DEVICE CONTROLLER SETUP
# =============================================================================

# Start device controller
start_device_controller() {
    log INFO "Preparing to start device controller..."

    # Activate Python virtual environment if present
    REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
    if [ -d "$REPO_ROOT/src/device/venv" ]; then
        log INFO "Activating Python virtual environment: $REPO_ROOT/src/device/venv"
        source "$REPO_ROOT/src/device/venv/bin/activate"
    else
        log WARN "No virtual environment found, using system Python"
    fi

    log INFO "Starting device controller..."

    # Change to the script directory
    cd "$SCRIPT_DIR"

    # Set PYTHONPATH to include `src` directory and run the device
    log INFO "Repository root: $REPO_ROOT"
    log INFO "PYTHONPATH: $REPO_ROOT/src"
    PYTHONPATH="$REPO_ROOT/src" python main.py
}

# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

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

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Initialize logging
mkdir -p "$SCRIPT_DIR/logs"

log INFO "Behavior Box: Device Controller Startup"
log INFO "Directory: $SCRIPT_DIR"

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
log INFO "Logs: $SCRIPT_DIR/logs/device.log"

# Wait for device controller process to complete
wait $RUN_PID
