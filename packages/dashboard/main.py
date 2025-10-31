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

# Set up Qt plugin paths for development mode (when not running from PyInstaller)
# This is needed for PyQt6 to find platform plugins on macOS
if not hasattr(sys, '_MEIPASS'):  # Not running from PyInstaller bundle
    try:
        import PyQt6
        pyqt6_dir = os.path.dirname(PyQt6.__file__)
        qt_plugins_dir = os.path.join(pyqt6_dir, 'Qt6', 'plugins')
        if os.path.exists(qt_plugins_dir):
            os.environ.setdefault('QT_PLUGIN_PATH', qt_plugins_dir)
    except ImportError:
        pass  # PyQt6 not installed, will fail later anyway

from dashboard.app import main

if __name__ == '__main__':
    main()
