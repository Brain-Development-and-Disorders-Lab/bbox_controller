#!/bin/bash

# This script is used to start the Raspberry Pi in AP mode and the device controller on startup

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================"
echo "Behavior Box: Startup Script"
echo "============================"
echo "Script directory: $SCRIPT_DIR"
echo "Timestamp: $(date)"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Change to the script directory
cd "$SCRIPT_DIR"

# Update the code from the repository after switching to the `main` branch
echo "Updating code from repository..."
git checkout main
git pull

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/../logs"

# Run the setup_ap.sh script in the background
echo "Starting WiFi access point setup..."
sudo "$SCRIPT_DIR/setup_ap.sh" > "$SCRIPT_DIR/../logs/setup_ap.log" 2>&1 &
SETUP_AP_PID=$!

# Wait a bit for the AP to start
sleep 10

# Run the run.sh script in the background
echo "Starting device controller..."
sudo "$SCRIPT_DIR/run.sh" > "$SCRIPT_DIR/../logs/device_controller.log" 2>&1 &
RUN_PID=$!

echo "Startup complete. PIDs: setup_ap=$SETUP_AP_PID, run=$RUN_PID"
echo "Logs available at:"
echo "  - $SCRIPT_DIR/../logs/setup_ap.log"
echo "  - $SCRIPT_DIR/../logs/device_controller.log"
