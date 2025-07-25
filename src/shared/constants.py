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

# Timeline message types
TIMELINE_MESSAGE_TYPES = [
    "timeline_upload",
    "timeline_validation",
    "timeline_ready",
    "timeline_error",
    "timeline_progress",
    "timeline_complete"
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
TOTAL_WIDTH = 900 + (PADDING * 6)
PANEL_WIDTH = 900
PANEL_HEIGHT = 720
COLUMN_WIDTH = 30
HEADING_HEIGHT = 40
UPDATE_INTERVAL = 50  # milliseconds
