"""
Filename: device/core/__init__.py
Author: Henry Burgess
Date: 2025-07-29
Description: Exports for the device core classes, including the experiment processor and trial management
License: MIT
"""

from .ExperimentProcessor import ExperimentProcessor
from .TrialFactory import TrialFactory
from .Trials import *

__all__ = ['ExperimentProcessor', 'TrialFactory']
