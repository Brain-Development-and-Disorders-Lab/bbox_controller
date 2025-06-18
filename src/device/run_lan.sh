#!/bin/bash

# Run the behavior box device when accessing on a local network (non-AP mode)
# This script sets the PYTHONPATH to include the src directory
# so that the device module can be found

echo "=================================="
echo "Behavior Box: Local Network"
echo "=================================="

echo "Starting device controller..."

# Set PYTHONPATH to include src directory and run the device
PYTHONPATH=../../src python main.py
