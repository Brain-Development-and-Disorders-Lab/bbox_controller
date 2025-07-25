"""
Test for statistics tracking functionality
"""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from device.app import Device
from shared.communication import MessageBuilder

class TestStatistics(unittest.TestCase):
    """Test statistics tracking functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Change to device directory to find config.json
        device_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'device')
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

        message = MessageBuilder.statistics(stats)

        self.assertEqual(message["type"], "statistics")
        self.assertEqual(message["data"], stats)

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.device, 'cleanup'):
            self.device.cleanup()

if __name__ == '__main__':
    unittest.main()
