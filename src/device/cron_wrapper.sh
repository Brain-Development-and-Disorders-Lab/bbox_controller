#!/bin/bash
# Cron wrapper script for Raspberry Pi
# This script sets up the proper environment for running the startup script

# Export the PATH for the cron job
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Set the working directory to the device folder
cd /home/pi/bbox_controller/src/device

# Ensure the script is executable
chmod a+x startup.sh

# Run the startup script
exec ./startup.sh
