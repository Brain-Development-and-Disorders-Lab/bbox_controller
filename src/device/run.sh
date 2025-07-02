#!/bin/bash

# Run the behavior box device controller code
# This script sets the PYTHONPATH to include the `src` directory

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==============================="
echo "Behavior Box: Device Controller"
echo "==============================="
echo "Script directory: $SCRIPT_DIR"
echo "Timestamp: $(date)"

echo "Starting device controller..."

# Change to the script directory
cd "$SCRIPT_DIR"

# Set PYTHONPATH to include `src` directory and run the device
PYTHONPATH="$SCRIPT_DIR/../../src" python main.py
