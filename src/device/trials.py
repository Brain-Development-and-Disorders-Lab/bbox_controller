"""
Trial base class and all following trials.
"""

import pygame

# Controllers
from controllers.DisplayController import DisplayController, SIMULATION_MODE
from controllers.IOController import IOController

# Other imports
from util import log

class Base:
  """
  Base interface for all experiment trials.
  Each trial should implement update() and render() methods.
  """
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

    # Create a small font for simulation banner
    if SIMULATION_MODE:
      self.simulation_font = pygame.font.SysFont("Arial", 16, bold=True)

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

class Interval(Base):
  """
  Stage ITI: Inter-trial interval
  Description: After each trial, the mouse is given an ITI of variable duration.
  """
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "trial_iti"
    self.start_time = None
    self.iti_duration = 1000

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    # Check if the ITI duration has passed
    if pygame.time.get_ticks() - self.start_time > self.iti_duration:
      self.add_data("trial_iti_completed", True)
      return False

    # Handle any events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          return False
        if event.key == pygame.K_SPACE:
          self.add_data("trial_iti_canceled", True)
          return False

    return True

  def render(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

    # Add simulation mode banner if in simulation mode
    if SIMULATION_MODE and self.simulation_font:
      banner_text = f"[SIMULATION - {self.title}]"
      text_surface = self.simulation_font.render(banner_text, True, (255, 255, 255))
      # Center the text horizontally
      text_rect = text_surface.get_rect(center=(self.width // 2, 20))
      self.screen.blit(text_surface, text_rect)

class Stage1(Base):
  """
  Trial Stage 1: Nose port entry and lever press
  Description: At the beginning of each trial, lit up the nose port light and deliver water.
    In the same time, randomly display the visual cue on one of the side screens.
    After the mouse pokes into the nose port and retrieves water (withdraw from the
    nose port), this trial ended and start the ITI. Turn off the visual cue and nose
    port light upon mouse enters the nose port. Record all events time, such as
    nose port entry, lever press, etc.
  """
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "trial_stage_1"
    self.start_time = None

    # Trial state
    self.nose_port_light = False
    self.delivered_water = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.lever_press = False

    # Trial events
    self.events = []

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

    # Setup trial
    self.nose_port_light = True
    if not SIMULATION_MODE:
      self.display.clear_displays()
      self.display.draw_test_pattern()
    log("Trial started", "info")

  def on_exit(self):
    self.add_data("events", self.events)

  def update(self, events):
    # Condition for trial end
    if self.nose_port_entry and self.delivered_water:
      return False

    # Handle any PyGame events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          log("Trial canceled", "info")
          self.add_data("trial_canceled", True)
          return False
        if event.key == pygame.K_SPACE and SIMULATION_MODE:
          log("Simulated nose port entry", "success")
          self.nose_port_entry = True

    # Handle any IO events if not in simulation mode
    if not SIMULATION_MODE:
      self.nose_port_entry = not self.get_io().get_input_states()["nose_poke"]
      if self.nose_port_entry:
        self.events.append({
          "type": "nose_port_entry",
          "timestamp": pygame.time.get_ticks()
        })
        log("Nose port entry", "info")
      self.lever_press = self.get_io().get_input_states()["left_lever"] or self.get_io().get_input_states()["right_lever"]
      if self.get_io().get_input_states()["left_lever"] == True:
        self.events.append({
          "type": "left_lever_press",
          "timestamp": pygame.time.get_ticks()
        })
        log("Left lever press", "info")
      if self.get_io().get_input_states()["right_lever"] == True:
        self.events.append({
          "type": "right_lever_press",
          "timestamp": pygame.time.get_ticks()
        })
        log("Right lever press", "info")

    # Continue if no inputs or events
    return True

  def render(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

    # Deliver water if trial has started
    if self.delivered_water == False and pygame.time.get_ticks() - self.start_time > 500:
      self.get_io().set_water_port(True)
    elif self.delivered_water == False:
      log("Water delivered", "success")
      self.delivered_water = True
      self.get_io().set_water_port(False)

    if self.nose_port_entry:
      self.visual_cue = False
      self.nose_port_light = False

    # Update visual state
    if not SIMULATION_MODE:
      if self.visual_cue:
        self.display.draw_test_pattern()
      else:
        self.display.clear_displays()

    # TODO: Update nose port light

    # Add simulation mode banner if in simulation mode
    if SIMULATION_MODE and self.simulation_font:
      banner_text = f"[SIMULATION - {self.title}]"
      text_surface = self.simulation_font.render(banner_text, True, (255, 255, 255))
      # Center the text horizontally
      text_rect = text_surface.get_rect(center=(self.width // 2, 20))
      self.screen.blit(text_surface, text_rect)
