"""
Shared test management utilities for bbox_controller project
"""

from typing import Dict, Any
from .constants import TEST_COMMANDS, TEST_STATES


class TestStateManager:
    """Manages test states across the application"""

    def __init__(self):
        self._test_state = {
            "test_water_delivery": {
                "state": TEST_STATES["NOT_TESTED"],
            },
            "test_actuators": {
                "state": TEST_STATES["NOT_TESTED"],
            },
            "test_ir": {
                "state": TEST_STATES["NOT_TESTED"],
            },
            "test_nose_light": {
                "state": TEST_STATES["NOT_TESTED"],
            },
        }

    def get_test_state(self, test_name: str) -> int:
        """Get the current state of a test"""
        if test_name in self._test_state:
            return self._test_state[test_name]["state"]
        return TEST_STATES["NOT_TESTED"]

    def set_test_state(self, test_name: str, state: int):
        """Set the state of a test"""
        if test_name in self._test_state:
            self._test_state[test_name]["state"] = state

    def get_all_test_states(self) -> Dict[str, Any]:
        """Get all test states"""
        return self._test_state.copy()

    def reset_test_states(self):
        """Reset all test states to NOT_TESTED"""
        for test_name in self._test_state:
            self._test_state[test_name]["state"] = TEST_STATES["NOT_TESTED"]

    def is_test_running(self, test_name: str) -> bool:
        """Check if a test is currently running"""
        return self.get_test_state(test_name) == TEST_STATES["RUNNING"]

    def is_test_completed(self, test_name: str) -> bool:
        """Check if a test has completed (passed or failed)"""
        state = self.get_test_state(test_name)
        return state in [TEST_STATES["PASSED"], TEST_STATES["FAILED"]]

    def get_running_tests(self) -> list[str]:
        """Get list of currently running tests"""
        return [test_name for test_name in self._test_state
                if self.is_test_running(test_name)]

    def get_completed_tests(self) -> list[str]:
        """Get list of completed tests"""
        return [test_name for test_name in self._test_state
                if self.is_test_completed(test_name)]


class TestCommandValidator:
    """Validates test commands and parameters"""

    @staticmethod
    def is_valid_test_command(command: str) -> bool:
        """Check if a command is a valid test command"""
        base_command = command.split()[0]
        return base_command in TEST_COMMANDS

    @staticmethod
    def validate_test_parameters(command: str) -> tuple[bool, str]:
        """Validate test command parameters"""
        parts = command.split()
        base_command = parts[0]

        if base_command not in TEST_COMMANDS:
            return False, f"Unknown test command: {base_command}"

        # Validate duration parameters for commands that support them
        if base_command in ["test_water_delivery", "test_nose_light"]:
            if len(parts) > 1:
                try:
                    duration = int(parts[1])
                    if duration <= 0:
                        return False, f"Duration must be positive: {duration}"
                except ValueError:
                    return False, f"Invalid duration value: {parts[1]}"

        return True, ""

    @staticmethod
    def get_supported_test_commands() -> list[str]:
        """Get list of supported test commands"""
        return TEST_COMMANDS.copy()


class TestStateFormatter:
    """Formats test states for display"""

    @staticmethod
    def get_state_name(state: int) -> str:
        """Get the human-readable name for a test state"""
        for name, value in TEST_STATES.items():
            if value == state:
                return name
        return "UNKNOWN"

    @staticmethod
    def get_state_color(state: int) -> str:
        """Get the color for a test state (for UI display)"""
        if state == TEST_STATES["PASSED"]:
            return "green"
        elif state == TEST_STATES["FAILED"]:
            return "red"
        elif state == TEST_STATES["RUNNING"]:
            return "yellow"
        else:
            return "gray"

    @staticmethod
    def format_test_summary(test_states: Dict[str, Any]) -> str:
        """Format a summary of test states"""
        passed = 0
        failed = 0
        running = 0
        not_tested = 0

        for test_data in test_states.values():
            state = test_data.get("state", TEST_STATES["NOT_TESTED"])
            if state == TEST_STATES["PASSED"]:
                passed += 1
            elif state == TEST_STATES["FAILED"]:
                failed += 1
            elif state == TEST_STATES["RUNNING"]:
                running += 1
            else:
                not_tested += 1

        return f"Tests: {passed} passed, {failed} failed, {running} running, {not_tested} not tested"
