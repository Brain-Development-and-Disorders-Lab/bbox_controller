"""
Shared communication utilities for bbox_controller project
"""

import json
from typing import Dict, Any, Optional
from .constants import TIMELINE_MESSAGE_TYPES


class MessageBuilder:
    """Utility class for building standardized messages"""

    @staticmethod
    def input_state(data: Dict[str, Any], version: str = "unknown") -> Dict[str, Any]:
        """Build an input state message"""
        return {
            "type": "input_state",
            "data": data,
            "version": version
        }

    @staticmethod
    def test_state(data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a test state message"""
        return {
            "type": "test_state",
            "data": data
        }

    @staticmethod
    def task_status(status: str, trial: str = None) -> Dict[str, Any]:
        """Build a task status message"""
        message = {
            "type": "task_status",
            "data": {
                "status": status
            }
        }
        if trial:
            message["data"]["trial"] = trial
        return message

    @staticmethod
    def trial_start(trial: str) -> Dict[str, Any]:
        """Build a trial start message"""
        return {
            "type": "trial_start",
            "data": {
                "trial": trial
            }
        }

    @staticmethod
    def trial_complete(trial: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build a trial complete message"""
        message = {
            "type": "trial_complete",
            "data": {
                "trial": trial
            }
        }
        if data:
            message["data"]["data"] = data
        return message

    @staticmethod
    def device_log(message: str, state: str = "info") -> Dict[str, Any]:
        """Build a device log message"""
        return {
            "type": "device_log",
            "data": {
                "message": message,
                "state": state
            }
        }

    @staticmethod
    def timeline_upload(timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a timeline upload message"""
        return {
            "type": "timeline_upload",
            "data": timeline_data
        }

    @staticmethod
    def timeline_validation(success: bool, message: str) -> Dict[str, Any]:
        """Build a timeline validation message"""
        return {
            "type": "timeline_validation",
            "success": success,
            "message": message
        }

    @staticmethod
    def timeline_error(message: str) -> Dict[str, Any]:
        """Build a timeline error message"""
        return {
            "type": "timeline_error",
            "message": message
        }

    @staticmethod
    def start_timeline_experiment(animal_id: str) -> Dict[str, Any]:
        """Build a start timeline experiment message"""
        return {
            "type": "start_timeline_experiment",
            "animal_id": animal_id
        }


class MessageParser:
    """Utility class for parsing and validating messages"""

    @staticmethod
    def parse_message(message: str) -> Optional[Dict[str, Any]]:
        """Parse a message string into a dictionary"""
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def is_timeline_message(message_data: Dict[str, Any]) -> bool:
        """Check if a message is a timeline-related message"""
        message_type = message_data.get("type", "")
        return message_type in TIMELINE_MESSAGE_TYPES

    @staticmethod
    def is_command_message(message: str) -> bool:
        """Check if a message is a command (non-JSON)"""
        try:
            json.loads(message)
            return False
        except json.JSONDecodeError:
            return True

    @staticmethod
    def validate_message_structure(message_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate that a message has the required structure"""
        if not isinstance(message_data, dict):
            return False, "Message must be a dictionary"

        if "type" not in message_data:
            return False, "Message must have a 'type' field"

        return True, ""


class CommandParser:
    """Utility class for parsing command strings"""

    @staticmethod
    def parse_test_command(command: str) -> tuple[str, Dict[str, Any]]:
        """Parse a test command and extract parameters"""
        parts = command.split()
        base_command = parts[0]
        parameters = {}

        # Parse duration parameters for commands that support them
        if base_command in ["test_water_delivery", "test_nose_light"] and len(parts) > 1:
            try:
                parameters["duration_ms"] = int(parts[1])
            except ValueError:
                pass

        return base_command, parameters

    @staticmethod
    def parse_experiment_command(command: str) -> tuple[str, Dict[str, Any]]:
        """Parse an experiment command and extract parameters"""
        parts = command.split()
        base_command = parts[0]
        parameters = {}

        if base_command == "start_experiment":
            if len(parts) > 1:
                parameters["animal_id"] = parts[1]
            if len(parts) > 2:
                try:
                    parameters["punishment_duration"] = int(parts[2])
                except ValueError:
                    pass
            if len(parts) > 3:
                try:
                    parameters["water_delivery_duration"] = int(parts[3])
                except ValueError:
                    pass

        return base_command, parameters
