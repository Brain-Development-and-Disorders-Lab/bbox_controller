"""
Filename: device/hardware/DataController.py
Author: Henry Burgess
Date: 2025-07-29
Description: Handles data storage for the device and any running experiments
License: MIT
"""

import json
import os
from datetime import datetime
from device.utils.logger import log

class DataController:
  def __init__(self, animal_id):
    self.animal_id = animal_id
    self.data = {
      "metadata": {
        "animal_id": animal_id,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "trials": []
      },
      "trials": [],
      "task": {}
    }

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    self.data_dir = os.path.join(base_dir, "data")

    try:
      os.makedirs(self.data_dir, exist_ok=True)
      log(f"Data directory ready: {self.data_dir}", "info")
    except Exception as e:
      log(f"Failed to create data directory {self.data_dir}: {e}", "error")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    self.filename = os.path.join(self.data_dir, f"{animal_id}_{timestamp}.json")
    log(f"Data file will be saved to: {self.filename}", "info")

  def add_trial_data(self, screen_name, data):
    """Add data for a specific screen"""
    data["timestamp"] = datetime.now().isoformat()
    data["trial_type"] = screen_name

    self.data["trials"].append(data)
    self.data["metadata"]["trials"].append({
      "name": screen_name,
      "timestamp": data["timestamp"]
    })

  def add_task_data(self, data):
    """Add task-level data"""
    data["timestamp"] = datetime.now().isoformat()
    self.data["task"].update(data)

  def add_statistics(self, statistics):
    """Add statistics data"""
    self.data["statistics"] = statistics

  def save(self) -> bool:
    """Save the current data to file"""
    try:
      self.data["metadata"]["end_time"] = datetime.now().isoformat()

      if not os.path.exists(self.data_dir):
        log(f"Data directory does not exist: {self.data_dir}", "error")
        return False

      # Check if we can write to the directory
      if not os.access(self.data_dir, os.W_OK):
        log(f"No write permission for data directory: {self.data_dir}", "error")
        return False

      # Log data summary for debugging
      log(f"Data summary - Animal ID: {self.animal_id}, Trials: {len(self.data['trials'])}", "info")
      log(f"Attempting to save data to: {self.filename}", "info")
      with open(self.filename, "w") as f:
        json.dump(self.data, f, indent=2)

      log(f"Data saved successfully to: {self.filename}", "success")
      return True
    except PermissionError as e:
      log(f"Permission error saving data: {e}", "error")
      return False
    except OSError as e:
      log(f"OS error saving data: {e}", "error")
      return False
    except TypeError as e:
      log(f"Type error saving data (likely non-serializable object): {e}", "error")
      self._log_data_structure(self.data, "data")
      return False
    except Exception as e:
      log(f"Unexpected error saving data: {e}", "error")
      return False

  def _log_data_structure(self, obj, path=""):
    """Recursively log data structure to identify non-serializable objects"""
    try:
      if isinstance(obj, dict):
        for key, value in obj.items():
          current_path = f"{path}.{key}" if path else key
          try:
            json.dumps(value)
          except (TypeError, ValueError):
            log(f"Non-serializable object found at {current_path}: {type(value)} = {value}", "error")
          else:
            if isinstance(value, (dict, list)):
              self._log_data_structure(value, current_path)
      elif isinstance(obj, list):
        for i, value in enumerate(obj):
          current_path = f"{path}[{i}]"
          try:
            json.dumps(value)
          except (TypeError, ValueError):
            log(f"Non-serializable object found at {current_path}: {type(value)} = {value}", "error")
          else:
            if isinstance(value, (dict, list)):
              self._log_data_structure(value, current_path)
    except Exception as e:
      log(f"Error analyzing data structure: {e}", "error")
