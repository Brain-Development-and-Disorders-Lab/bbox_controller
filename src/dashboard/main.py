#!/usr/bin/env python3
"""
Filename: dashboard/main.py
Author: Henry Burgess
Date: 2025-07-29
Description: Entry point for the dashboard script, executed directly from the command line
License: MIT
"""

import sys
import os

# Add the 'src' directory to Python path to enable imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dashboard.app import main

if __name__ == "__main__":
    main()
