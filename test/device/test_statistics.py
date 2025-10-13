#!/usr/bin/env python3
"""
Filename: test/device/test_statistics.py
Author: Henry Burgess
Date: 2025-07-29
Description: Test for statistics tracking functionality
"""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from device.app import Device
from shared.managers import CommunicationMessageBuilder

class TestStatistics(unittest.TestCase):
    """Test statistics tracking functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Change to shared directory
        device_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared')
        original_dir = os.getcwd()
        os.chdir(device_dir)

        try:
            self.device = Device()
        finally:
            os.chdir(original_dir)

    def test_initial_statistics(self):
        """Test that statistics start at zero"""
        stats = self.device.get_statistics()
        expected = {
            "nose_pokes": 0,
            "left_lever_presses": 0,
            "right_lever_presses": 0,
            "trial_count": 0,
            "water_deliveries": 0
        }
        self.assertEqual(stats, expected)

    def test_reset_statistics(self):
        """Test that statistics can be reset"""
        # Set some non-zero values
        self.device._statistics = {
            "nose_pokes": 5,
            "left_lever_presses": 3,
            "right_lever_presses": 2,
            "trial_count": 10,
            "water_deliveries": 8
        }

        # Reset statistics
        self.device.reset_statistics()

        # Check they're back to zero
        stats = self.device.get_statistics()
        expected = {
            "nose_pokes": 0,
            "left_lever_presses": 0,
            "right_lever_presses": 0,
            "trial_count": 0,
            "water_deliveries": 0
        }
        self.assertEqual(stats, expected)

    def test_statistics_message_builder(self):
        """Test that statistics messages can be built"""
        stats = {
            "nose_pokes": 5,
            "left_lever_presses": 3,
            "right_lever_presses": 2,
            "trial_count": 10,
            "water_deliveries": 8
        }

        message = CommunicationMessageBuilder.statistics(stats)
        self.assertEqual(message["type"], "statistics")
        self.assertEqual(message["data"], stats)

    def test_trial_counting_on_exit(self):
        """Test that trial counting happens in on_exit method"""
        # Change to shared directory
        device_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared')
        original_dir = os.getcwd()
        os.chdir(device_dir)

        try:
            from device.core.Trials import Interval
            from device.hardware.GPIOController import GPIOController
            from shared.managers import StatisticsManager
            stats_controller = StatisticsManager()
            gpio = GPIOController()

            # Create trial with statistics manager
            trial = Interval(statistics=stats_controller, gpio=gpio)

            # Verify initial trial count
            initial_count = stats_controller.get_statistics()["trial_count"]

            # Call on_exit to simulate trial completion
            trial.on_exit()

            # Verify trial count was incremented
            final_count = stats_controller.get_statistics()["trial_count"]
            self.assertEqual(final_count, initial_count + 1)
        finally:
            os.chdir(original_dir)

    def test_statistics_controller(self):
        """Test the StatisticsManager functionality"""
        from shared.managers import StatisticsManager

        # Create statistics manager
        stats = StatisticsManager()

        # Test initial state
        initial_stats = stats.get_statistics()
        self.assertEqual(initial_stats["trial_count"], 0)
        self.assertEqual(initial_stats["nose_pokes"], 0)
        self.assertEqual(initial_stats["left_lever_presses"], 0)
        self.assertEqual(initial_stats["right_lever_presses"], 0)
        self.assertEqual(initial_stats["water_deliveries"], 0)

        # Test incrementing
        stats.increment_trial_count()
        stats.increment_nose_pokes()
        stats.increment_left_lever_presses()
        stats.increment_right_lever_presses()
        stats.increment_water_deliveries()

        # Verify increments
        updated_stats = stats.get_statistics()
        self.assertEqual(updated_stats["trial_count"], 1)
        self.assertEqual(updated_stats["nose_pokes"], 1)
        self.assertEqual(updated_stats["left_lever_presses"], 1)
        self.assertEqual(updated_stats["right_lever_presses"], 1)
        self.assertEqual(updated_stats["water_deliveries"], 1)

        # Test reset
        stats.reset_statistics()
        reset_stats = stats.get_statistics()
        self.assertEqual(reset_stats["trial_count"], 0)
        self.assertEqual(reset_stats["nose_pokes"], 0)
        self.assertEqual(reset_stats["left_lever_presses"], 0)
        self.assertEqual(reset_stats["right_lever_presses"], 0)
        self.assertEqual(reset_stats["water_deliveries"], 0)

        # Test generic increment method
        stats.increment_stat("trial_count")
        stats.increment_stat("nose_pokes")
        generic_stats = stats.get_statistics()
        self.assertEqual(generic_stats["trial_count"], 1)
        self.assertEqual(generic_stats["nose_pokes"], 1)

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.device, 'cleanup'):
            self.device.cleanup()

if __name__ == '__main__':
    unittest.main()
