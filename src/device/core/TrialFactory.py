"""
Filename: device/core/TrialFactory.py
Author: Henry Burgess
Date: 2025-07-29
Description: Factory for creating trial objects from timeline data
License: MIT
"""

from typing import Dict, Any

class TrialFactory:
    """Factory for creating trial objects from timeline data"""

    def __init__(self):
        self.trial_types = {
            "Stage1": "Stage1",
            "Stage2": "Stage2",
            "Stage3": "Stage3",
            "Interval": "Interval"
        }

    def create_trial(self, trial_type: str, parameters: Dict[str, Any], **kwargs):
        """Create a trial object from type and parameters"""
        if trial_type not in self.trial_types:
            raise ValueError(f"Unknown trial type: {trial_type}")

        if trial_type == "Stage1":
            from device.core.Trials import Stage1
            return Stage1(**parameters, **kwargs)
        elif trial_type == "Stage2":
            from device.core.Trials import Stage2
            return Stage2(**parameters, **kwargs)
        elif trial_type == "Stage3":
            from device.core.Trials import Stage3
            return Stage3(**parameters, **kwargs)
        elif trial_type == "Interval":
            from device.core.Trials import Interval
            return Interval(**parameters, **kwargs)
        else:
            raise ValueError(f"Unsupported trial type: {trial_type}")

    def is_valid_trial_type(self, trial_type: str) -> bool:
        """Check if a trial type is valid"""
        return trial_type in self.trial_types

