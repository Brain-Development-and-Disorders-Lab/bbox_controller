import json
from typing import Any, Dict, Optional


class CommunicationMessageParser:
    """Utility class for parsing and validating messages"""

    @staticmethod
    def parse_message(message: str) -> Optional[Dict[str, Any]]:
        """Parse a message string into a dictionary"""
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return None

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
