"""
Filename: shared/managers/StatisticsManager.py
Author: Henry Burgess
Date: 2025-07-29
Description: Manager for experiment statistics, tracking inputs and number of trials completed
License: MIT
"""

from typing import Dict, Any

class StatisticsManager:
    """Manager for experiment statistics"""

    def __init__(self):
        self._statistics = {
            "nose_pokes": 0,
            "left_lever_presses": 0,
            "right_lever_presses": 0,
            "trial_count": 0,
            "water_deliveries": 0
        }

    def increment_trial_count(self):
        """Increment the trial counter"""
        self._statistics["trial_count"] += 1

    def increment_nose_pokes(self):
        """Increment nose pokes counter"""
        self._statistics["nose_pokes"] += 1

    def increment_left_lever_presses(self):
        """Increment left lever presses counter"""
        self._statistics["left_lever_presses"] += 1

    def increment_right_lever_presses(self):
        """Increment right lever presses counter"""
        self._statistics["right_lever_presses"] += 1

    def increment_water_deliveries(self):
        """Increment water deliveries counter"""
        self._statistics["water_deliveries"] += 1

    def increment_stat(self, stat_name: str):
        """Generic method to increment any statistic"""
        if stat_name in self._statistics:
            self._statistics[stat_name] += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self._statistics.copy()

    def get_all_stats(self) -> Dict[str, Any]:
        """Get current statistics (alias for get_statistics)"""
        return self._statistics.copy()

    def reset_statistics(self):
        """Reset all statistics to zero"""
        self._statistics = {
            "nose_pokes": 0,
            "left_lever_presses": 0,
            "right_lever_presses": 0,
            "trial_count": 0,
            "water_deliveries": 0
        }

    def reset_all_stats(self):
        """Reset all statistics to zero (alias for reset_statistics)"""
        self.reset_statistics()
