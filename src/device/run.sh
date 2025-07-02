#!/bin/bash

# Run the behavior box device controller code
# This script sets the PYTHONPATH to include the `src` directory

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for and activate Python virtual environment if present
# Look for .venv in current directory and parent directories up to repository root
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
    echo "Activating Python virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated: $(which python)"
else
    echo "No virtual environment found, using system Python"
fi

echo "==============================="
echo "Behavior Box: Device Controller"
echo "==============================="
echo "Script directory: $SCRIPT_DIR"
echo "Timestamp: $(date)"

echo "Starting device controller..."

# Change to the script directory
cd "$SCRIPT_DIR"

# Set PYTHONPATH to include the repository root (where .venv is located)
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
echo "Repository root: $REPO_ROOT"
echo "PYTHONPATH: $REPO_ROOT/src"

# Set PYTHONPATH to include `src` directory and run the device
PYTHONPATH="$REPO_ROOT/src" python main.py
