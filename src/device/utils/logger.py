"""
Filename: device/utils/logger.py
Author: Henry Burgess
Date: 2025-07-29
Description: Logger for the device script, handles logging to the console and message queue
License: MIT
"""

import datetime
import os

# Log states
LOG_STATES = {
    "start": "START",
    "success": "SUCCESS",
    "error": "ERROR",
    "warning": "WARN",
    "info": "INFO",
    "debug": "DEBUG",
}

# Global message queue reference
_device_message_queue = None

def set_message_queue(queue):
    """Set the global message queue reference"""
    global _device_message_queue
    _device_message_queue = queue

def log(message, state="info"):
    """
    Logs a message to the console, device.log file, and sends it to the message queue.

    Parameters:
    message (str): The message to log.
    state (str): The state of the message (must be one of LOG_STATES keys).
    """
    if state not in LOG_STATES:
        state = "info"  # Default to info if invalid state

    # Use consistent timestamp format
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"{timestamp} [{LOG_STATES[state]}] {message}"

    # Print to console
    print(formatted_message)

    # Write to device.log file
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    device_log_path = os.path.join(log_dir, 'device.log')
    with open(device_log_path, 'a') as f:
        f.write(formatted_message + '\n')

    # Send to message queue if available
    if _device_message_queue:
        _device_message_queue.put({
            "type": "device_log",
            "data": {
                "message": message,
                "state": state
            }
        })
