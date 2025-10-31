#!/bin/bash

# Behavior Box: Dashboard Startup Script
# Author: Henry Burgess <henry.burgess@wustl.edu>
# Date: 2025-10-31
# Description:
#   This script acts as a single entry point to start the dashboard software,
#   setting up the Python environment and starting the dashboard process.

# Configuration
set -e
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # apps/dashboard
REPO_DIR="$(dirname "$(dirname "$APP_DIR")")"
PACKAGES_DIR="$REPO_DIR/packages/dashboard" # packages/dashboard
LOGFILE="$APP_DIR/logs/dashboard.log"

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

# Start dashboard
start_dashboard() {
    # Activate Python virtual environment if present
    if [ -d "$REPO_DIR/venvs/dashboard" ]; then
        log INFO "Activating Python virtual environment: $REPO_DIR/venvs/dashboard"
        source "$REPO_DIR/venvs/dashboard/bin/activate"
    else
        log WARN "No virtual environment found, using system Python"
    fi

    # Change to the script directory
    cd "$PACKAGES_DIR"

    # Set PYTHONPATH to include `packages/dashboard` directory and run the dashboard
    log INFO "Starting dashboard with PYTHONPATH: $PACKAGES_DIR"
    PYTHONPATH="$PACKAGES_DIR" python main.py
}

# Cleanup routine to stop background processes
cleanup() {
    log INFO "Cleaning up background processes..."

    # Kill any background jobs
    if [ -n "$(jobs -p)" ]; then
        kill $(jobs -p) 2>/dev/null || true
    fi
}

# Initialize logging
mkdir -p "$APP_DIR/logs"

log INFO "Behavior Box: Dashboard Startup"
log INFO "Repository root: $REPO_DIR"
log INFO "Application directory: $APP_DIR"
log INFO "Packages directory: $PACKAGES_DIR"

log INFO "Starting dashboard..."
start_dashboard &
RUN_PID=$!
log INFO "Dashboard started with PID: $RUN_PID"
log INFO "Logs: $APP_DIR/logs/dashboard.log"

# Wait for dashboard process to complete
wait $RUN_PID
