#!/bin/bash

# Behavior Box: Dashboard Startup Script
# Author: Henry Burgess <henry.burgess@wustl.edu>
# Date: 2025-10-31
# Description:
#   This script acts as a single entry point to start the dashboard software,
#   setting up the Python environment and starting the dashboard process.

set -e

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$(dirname "$APP_DIR")")"
LOGFILE="$APP_DIR/logs/dashboard.log"

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg" | tee -a "$LOGFILE"
}

# Initialize logging
mkdir -p "$APP_DIR/logs"
log INFO "Behavior Box: Dashboard Startup"
log INFO "Repository root: $REPO_DIR"

# Activate Python virtual environment if present
VENV_PATH="$REPO_DIR/venvs/dashboard"
if [ -d "$VENV_PATH" ]; then
    log INFO "Activating Python virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"

    # Set Qt plugin path for macOS (Python code in main.py also handles this as fallback)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        QT_PLUGINS="$VENV_PATH/lib/python3.11/site-packages/PyQt6/Qt6/plugins"
        if [ -d "$QT_PLUGINS" ]; then
            export QT_PLUGIN_PATH="$QT_PLUGINS"
            log INFO "Setting QT_PLUGIN_PATH: $QT_PLUGIN_PATH"
        fi
    fi
else
    log WARN "No virtual environment found, using system Python"
fi

# Change to packages directory and start dashboard
cd "$REPO_DIR/packages"
log INFO "Starting dashboard with PYTHONPATH: $REPO_DIR/packages"
PYTHONPATH="$REPO_DIR/packages" python dashboard/main.py
