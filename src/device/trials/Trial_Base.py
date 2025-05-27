"""
Base interface for all experiment trials.
Each trial should implement update() and render() methods.
"""

from controllers.DisplayController import DisplayController
from controllers.IOController import IOController

class TrialBase:
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.screen = None
    self.font = None
    self.title = "base_screen"
    self.data = {}

    # Controllers
    self.display = DisplayController()
    self.io = IOController()

  def update(self, events):
    """
    Update trial state based on events and time
    Args:
      events: List of pygame events to process
    Returns:
      bool: True if trial should continue, False if should exit
    """
    raise NotImplementedError("Trial must implement update()")

  def render(self):
    """
    Render the current trial state
    """
    raise NotImplementedError("Trial must implement render()")

  def on_enter(self):
    """
    Called when trial becomes active
    """
    pass

  def on_exit(self):
    """
    Called when trial is being exited
    """
    pass

  def add_data(self, key, value):
    """Add data to the trial's internal storage"""
    self.data[key] = value

  def get_data(self):
    """Get all data collected by this trial"""
    return self.data

  def get_display(self):
    """Get the display controller"""
    return self.display

  def get_io(self):
    """Get the IO controller"""
    return self.io

  def get_input(self):
    """Get the input from the IO controller"""
    return self.io.get_input()
