import datetime

# Log states
LOG_STATES = {
    "start": "Start",
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "info": "Info",
    "debug": "Debug",
}

# Global message queue reference
_device_message_queue = None

def set_message_queue(queue):
    """Set the global message queue reference"""
    global _device_message_queue
    _device_message_queue = queue

def log(message, state="info"):
    """
    Logs a message to the console with a timestamp and sends it to the message queue.

    Parameters:
    message (str): The message to log.
    state (str): The state of the message (must be one of LOG_STATES keys).
    """
    if state not in LOG_STATES:
        state = "info"  # Default to info if invalid state

    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    formatted_message = f"[{timestamp}] [{LOG_STATES[state]}] {message}\n"

    # Print to console
    print(formatted_message, end="")

    # Send to message queue if available
    if _device_message_queue:
        _device_message_queue.put({
            "type": "device_log",
            "data": {
                "message": formatted_message,
                "state": state
            }
        })
