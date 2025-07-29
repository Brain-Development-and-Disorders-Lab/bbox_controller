"""
Shared library for bbox_controller project
Contains common constants, models, and utilities used by both control panel and device
"""

from .constants import *
from .models import *
from .managers import *

# Single source of truth for version number
__version__ = "1.1.1"

# Version info for easy access
VERSION = __version__
