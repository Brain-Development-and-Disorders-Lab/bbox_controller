#!/bin/bash

# Run the behavior box device
# This script sets the PYTHONPATH to include the src directory
# so that the device module can be found

echo "Starting Behavior Box Controller..."

# Set PYTHONPATH to include src directory and run the device
PYTHONPATH=../../src python main.py
