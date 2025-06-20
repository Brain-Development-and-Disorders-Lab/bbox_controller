"""
Handles data storage for the experiment
"""

import json
import os
from datetime import datetime

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

    # Create data directory if it doesn't exist
    self.data_dir = "data"
    os.makedirs(self.data_dir, exist_ok=True)

    # Generate filename based on animal_id and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    self.filename = f"{self.data_dir}/{animal_id}_{timestamp}.json"

  def add_trial_data(self, screen_name, data):
    """Add data for a specific screen"""
    # Add timestamp and trial type to the data
    data["timestamp"] = datetime.now().isoformat()
    data["trial_type"] = screen_name

    # Append to trials list
    self.data["trials"].append(data)

    # Add to trial history in metadata
    self.data["metadata"]["trials"].append({
      "name": screen_name,
      "timestamp": data["timestamp"]
    })

  def add_task_data(self, data):
    """Add task-level data"""
    # Add timestamp to the data
    data["timestamp"] = datetime.now().isoformat()
    self.data["task"].update(data)

  def save(self) -> bool:
    """Save the current data to file"""
    try:
      # Update end time
      self.data["metadata"]["end_time"] = datetime.now().isoformat()

      # Save to file
      with open(self.filename, "w") as f:
        json.dump(self.data, f, indent=2)

      return True
    except Exception as e:
      return False
