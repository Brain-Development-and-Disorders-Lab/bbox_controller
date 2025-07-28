#!/bin/bash

# =============================================================================
# Behavior Box: Control Panel Script
# =============================================================================
# This script sets up the Python path and starts the control panel application
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Logging function
log() {
    local level="$1"; shift
    local msg="$@"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "$ts [$level] $msg"
}

# =============================================================================
# PYTHON ENVIRONMENT SETUP
# =============================================================================

setup_python_environment() {
    log INFO "Setting up Python environment..."

    # Check for and activate Python virtual environment if present
    VENV_PATH=""
    CURRENT_DIR="$REPO_ROOT"
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

    # Set PYTHONPATH to include the src directory
    export PYTHONPATH="$REPO_ROOT/src:$PYTHONPATH"
    log INFO "PYTHONPATH set to: $PYTHONPATH"
}

# =============================================================================
# CONTROL PANEL STARTUP
# =============================================================================

start_control_panel() {
    log INFO "Starting control panel application..."

    # Change to the script directory
    cd "$SCRIPT_DIR"

    # Run the control panel
    python main.py
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

log INFO "======================================================"
log INFO "    Behavior Box: Control Panel Startup Script       "
log INFO "======================================================"
log INFO "Directory: $SCRIPT_DIR"
log INFO "Repository root: $REPO_ROOT"
log INFO "Timestamp: $(date)"

# Setup Python environment
setup_python_environment

# Start control panel
start_control_panel
