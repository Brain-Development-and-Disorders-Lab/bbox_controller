#!/bin/bash

# Run the behavior box device controller code
# This script sets the PYTHONPATH to include the `src` directory

echo "==============================="
echo "Behavior Box: Device Controller"
echo "==============================="

echo "Starting device controller..."

# Set PYTHONPATH to include `src` directory and run the device
PYTHONPATH=../../src python main.py
