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

def log(message, state="info"):
  """
  Logs a message to the console with a timestamp.

  Parameters:
  message (str): The message to log.
  state (str): The state of the message.
  """
  message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{LOG_STATES[state]}] {message}\n"
  print(message, end="")
