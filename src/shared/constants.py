"""
Shared constants for bbox_controller project
"""

# Test commands
TEST_COMMANDS = [
    "test_water_delivery",
    "test_actuators",
    "test_ir",
    "test_nose_light",
    "test_displays",
]

# Experiment commands
EXPERIMENT_COMMANDS = [
    "start_experiment",
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
