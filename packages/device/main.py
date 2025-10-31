#!/usr/bin/env python3
"""
Filename: device/main.py
Author: Henry Burgess
Date: 2025-07-29
Description: Entry point for the device script, executed directly from the command line
License: MIT
"""

import sys
import os
import argparse

# Add packages to path
script_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.dirname(script_dir)
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

from device.app import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Behavior Box Device')
    parser.add_argument('--port', '-p', type=int, default=8765,
                        help='Port for dashboard connection (default: 8765)')
    args = parser.parse_args()

    main(port=args.port)
