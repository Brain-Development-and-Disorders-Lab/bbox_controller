"""
Filename: shared/__init__.py
Author: Henry Burgess
Date: 2025-07-29
Description: Shared library for the bbox_controller project, contains common constants, models, and managers used by both the control panel and device
License: MIT
"""

from .constants import *
from .models import *
from .managers import *

# Single source of truth for version number
__version__ = "1.1.1"

# Version info for easy access
VERSION = __version__
