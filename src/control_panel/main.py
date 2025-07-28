#!/usr/bin/env python3
"""
Main entry point for the control panel application
"""

import sys
import os

# Add the src directory to Python path to enable imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from control_panel.app import main

if __name__ == "__main__":
    main()
