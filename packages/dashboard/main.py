#!/usr/bin/env python3
"""
Entry point for the dashboard application.
"""

import sys
import os

# Add packages to path
script_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.dirname(script_dir)
if packages_dir not in sys.path:
    sys.path.insert(0, packages_dir)

from dashboard.app import main

if __name__ == '__main__':
    main()
