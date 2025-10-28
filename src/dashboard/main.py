#!/usr/bin/env python3
"""
Entry point for the dashboard application.
"""

import sys
import os

# Add the 'src' directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from dashboard.app import main

if __name__ == '__main__':
    main()
