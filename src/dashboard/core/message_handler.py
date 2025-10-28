#!/usr/bin/env python3

from typing import Dict, Any, Optional, Callable
from shared.constants import TEST_STATES, LOG_STATES


class MessageHandler:
    """Handles parsing and routing of messages from devices"""

    def __init__(self):
        self.callbacks = {}

    def register_handler(self, message_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for a specific message type"""
        if message_type not in self.callbacks:
            self.callbacks[message_type] = []
        self.callbacks[message_type].append(callback)

    def unregister_handler(self, message_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a callback for a specific message type"""
        if message_type in self.callbacks and callback in self.callbacks[message_type]:
            self.callbacks[message_type].remove(callback)

    def handle_message(self, message: Dict[str, Any]):
        """Process and route a message to appropriate handlers"""
        if not isinstance(message, dict) or "type" not in message:
            return

        message_type = message.get("type")

        if message_type in self.callbacks:
            for callback in self.callbacks[message_type]:
                callback(message)

    @staticmethod
    def extract_version(message: Dict[str, Any]) -> Optional[str]:
        """Extract version information from a message"""
        return message.get("version")

    @staticmethod
    def is_test_complete(message: Dict[str, Any]) -> bool:
        """Check if message indicates a test is complete"""
        if message.get("type") != "test_state":
            return False

        test_data = message.get("data", {})
        for test_info in test_data.values():
            state = test_info.get("state")
            if state in [TEST_STATES["PASSED"], TEST_STATES["FAILED"]]:
                return True
        return False

    @staticmethod
    def is_experiment_running(message: Dict[str, Any]) -> bool:
        """Check if experiment is currently running based on message"""
        if message.get("type") == "experiment_status":
            status = message.get("data", {}).get("status")
            return status == "started"
        return False

    @staticmethod
    def parse_input_state(message: Dict[str, Any]) -> Optional[Dict[str, bool]]:
        """Extract input state data from message"""
        if message.get("type") == "input_state":
            return message.get("data")
        return None

    @staticmethod
    def parse_statistics(message: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract statistics data from message"""
        if message.get("type") == "statistics":
            return message.get("data")
        return None

    @staticmethod
    def parse_test_state(message: Dict[str, Any]) -> Optional[Dict[str, Dict[str, Any]]]:
        """Extract test state data from message"""
        if message.get("type") == "test_state":
            return message.get("data")
        return None

    @staticmethod
    def parse_device_log(message: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract device log message and state"""
        if message.get("type") == "device_log":
            data = message.get("data", {})
            return data.get("message"), data.get("state")
        return None, None

