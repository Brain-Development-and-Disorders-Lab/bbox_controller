"""
Filename: shared/__init__.py
Author: Henry Burgess
Date: 2025-07-29
Description: Shared library for the bbox_controller project, contains common constants, models, and managers used by both the control panel and device
License: MIT
"""

import sys
from pathlib import Path

_repo_root = Path(__file__).parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from .constants import *
from .models import *
from .managers import *

from version import __version__, VERSION
