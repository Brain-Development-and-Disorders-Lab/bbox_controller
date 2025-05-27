"""
Base interface for all experiment screens.
Each screen should implement update() and render() methods.
"""

class BaseScreen:
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.screen = None
    self.font = None
    self.title = "base_screen"
    self.data = {}

  def update(self, events):
    """
    Update screen state based on events and time
    Args:
      events: List of pygame events to process
    Returns:
      bool: True if screen should continue, False if should exit
    """
    raise NotImplementedError("Screen must implement update()")

  def render(self):
    """
    Render the current screen state
    """
    raise NotImplementedError("Screen must implement render()")

  def on_enter(self):
    """
    Called when screen becomes active
    """
    pass

  def on_exit(self):
    """
    Called when screen is being exited
    """
    pass

  def add_data(self, key, value):
    """Add data to the screen's internal storage"""
    self.data[key] = value

  def get_data(self):
    """Get all data collected by this screen"""
    return self.data
