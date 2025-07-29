"""
Filename: shared/managers/CommunicationMessageBuilder.py
Author: Henry Burgess
Date: 2025-07-29
Description: Utility class for building standardized messages for communication between the device and control panel
License: MIT
"""

from typing import Dict, Any

class CommunicationMessageBuilder:
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
    def experiment_status(status: str, trial: str = None) -> Dict[str, Any]:
        """Build a experiment status message"""
        message = {
            "type": "experiment_status",
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
    def experiment_upload(experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a experiment upload message"""
        return {
            "type": "experiment_upload",
            "data": experiment_data
        }

    @staticmethod
    def experiment_validation(success: bool, message: str) -> Dict[str, Any]:
        """Build a experiment validation message"""
        return {
            "type": "experiment_validation",
            "success": success,
            "message": message
        }

    @staticmethod
    def experiment_error(message: str) -> Dict[str, Any]:
        """Build a experiment error message"""
        return {
            "type": "experiment_error",
            "message": message
        }

    @staticmethod
    def start_experiment(animal_id: str) -> Dict[str, Any]:
        """Build a start experiment message"""
        return {
            "type": "start_experiment",
            "animal_id": animal_id
        }

    @staticmethod
    def statistics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a statistics message"""
        return {
            "type": "statistics",
            "data": data
        }
