"""
Filename: shared/constants.py
Author: Henry Burgess
Date: 2025-07-29
Description: Shared constants between the device and control panel
License: MIT
"""

# Test commands
TEST_COMMANDS = [
    "test_water_delivery",
    "test_levers",
    "test_ir",
    "test_nose_light",
    "test_displays",
    "test_lever_lights",
]

# Experiment commands
EXPERIMENT_COMMANDS = [
    "stop_experiment"
]

# Test states
TEST_STATES = {
    "NOT_TESTED": 0,
    "FAILED": -1,
    "PASSED": 1,
    "RUNNING": 2,
}

# Log states
LOG_STATES = {
    "start": "Start",
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "info": "Info",
    "debug": "Debug",
}

# Communication constants
DEFAULT_HOST = ""
DEFAULT_PORT = 8765
INPUT_TEST_TIMEOUT = 10  # Seconds

# UI constants
PADDING = 10
SECTION_PADDING = 10
TOTAL_WIDTH = 850 + (PADDING * 6)
PANEL_WIDTH = 850
PANEL_HEIGHT = 650
COLUMN_WIDTH = 30
HEADING_HEIGHT = 40
UPDATE_INTERVAL = 50  # milliseconds

# Available trial types for validation
AVAILABLE_TRIAL_TYPES = {
    "Stage1": {
        "description": "Basic nose poke training stage",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Stage2": {
        "description": "Basic lever press training stage",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Stage3": {
        "description": "Nose poke and lever press training stage",
        "default_parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
        }
    },
    "Interval": {
        "description": "Inter-trial interval",
        "default_parameters": {
            "duration": 800
        }
    }
}

# Event types
TRIAL_EVENTS = {
    # Lever events
    "LEFT_LEVER_PRESS": "left_lever_press",
    "LEFT_LEVER_RELEASE": "left_lever_release",
    "RIGHT_LEVER_PRESS": "right_lever_press",
    "RIGHT_LEVER_RELEASE": "right_lever_release",

    # Nose port events
    "NOSE_PORT_ENTRY": "nose_port_entry",
    "NOSE_PORT_EXIT": "nose_port_exit",

    # Water delivery events
    "WATER_DELIVERY_START": "water_delivery_start",
    "WATER_DELIVERY_COMPLETE": "water_delivery_complete",

    # Reward events
    "REWARD_TRIGGERED": "reward_triggered",

    # Visual cue events
    "VISUAL_CUE_START": "visual_cue_start",
    "VISUAL_CUE_END": "visual_cue_end",

    # Trial state events
    "TRIAL_START": "trial_start",
    "TRIAL_END": "trial_end",

    # Trial error events
    "TRIAL_CUE_TIMEOUT": "trial_cue_timeout",
}
