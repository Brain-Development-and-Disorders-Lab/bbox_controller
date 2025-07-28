"""
Trial base class and all following trials.
"""

import random
import pygame
import json
from device.hardware.DisplayController import DisplayController, SIMULATION_MODE
from device.hardware.IOController import IOController
from device.utils.logger import log
from device.utils.helpers import TrialOutcome

class Base:
  """
  Base interface for all experiment trials.
  Each trial should implement update() and render() methods.
  """
  def __init__(self, *args, **kwargs):
    # Screen properties
    self.screen = kwargs.get('screen')
    self.width = kwargs.get('width')
    self.height = kwargs.get('height')
    self.font = kwargs.get('font')

    # Arguments
    self.args = args
    self.kwargs = kwargs

    # Controllers
    self.io: IOController = kwargs.get('io')
    self.display: DisplayController = kwargs.get('display')

    # All trial data
    self.data = {}

    # Config
    self.config = json.load(open("config.json", "r"))["task"]

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

  def get_input_states(self):
    """Get current input states"""
    if self.io is None:
        # Default state if no updates received yet
        return {
            "right_lever": False,
            "left_lever": False,
            "nose_poke": False,
            "water_port": False,
            "nose_light": False,
        }
    return self.io.get_input_states()

class Interval(Base):
  """
  Stage ITI: Inter-trial interval
  Description: After each trial, the mouse is given an ITI of variable duration.
  """
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.title = "trial_iti"
    self.start_time = None

    # Duration
    if "duration" in self.kwargs:
      self.duration = self.kwargs["duration"]
      log("ITI duration provided, using provided duration of " + str(self.duration) + "ms", "success")
    else:
      log("No ITI duration provided, using default of 1000ms", "warning")
      self.duration = 1000

  def set_duration(self, duration):
    self.duration = duration
    log("ITI duration set to " + str(self.duration) + "ms", "success")

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    # Check if the ITI duration has passed
    if pygame.time.get_ticks() - self.start_time > self.duration:
      self.add_data("trial_iti_completed", True)
      self.add_data("trial_outcome", TrialOutcome.SUCCESS)
      return False

    # Handle any events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          return False
        if event.key == pygame.K_SPACE:
          self.add_data("trial_iti_canceled", True)
          self.add_data("trial_outcome", TrialOutcome.CANCELLED)
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
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.title = "trial_stage_1"
    self.start_time = None
    self.water_start_time = None

    # Trial state
    self.nose_port_light = False
    self.delivered_water = False
    self.water_delivery_complete = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.nose_port_exit = False
    self.lever_press = False

    # Trial parameters
    self.cue_side = random.choice(["left", "right"])

    # Trial events
    self.events = []

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()
    self.water_start_time = pygame.time.get_ticks() # Start water delivery immediately

    # Setup trial
    # Activate the nose port light
    self.nose_port_light = True
    self.visual_cue = True

    # Clear the displays and randomly select the display to show the visual cue
    if not SIMULATION_MODE:
      self.display.clear_displays()
      self.display.draw_alternating_pattern(self.cue_side)
      log("Visual cue displayed on the " + self.cue_side + " side", "success")

    log("Trial started", "info")

  def on_exit(self):
    self.add_data("events", self.events)

  def _update_water_delivery(self):
    current_time = pygame.time.get_ticks()

    # Start water delivery at trial start
    if not self.delivered_water:
      self.io.set_water_port(True)
      self.delivered_water = True
      log("Water delivery started", "success")
      self.events.append({
        "type": "water_delivery_start",
        "timestamp": current_time
      })

    # Check if water delivery duration has elapsed
    elif self.delivered_water and not self.water_delivery_complete:
      if current_time - self.water_start_time >= self.config["valve_open"]:
        self.io.set_water_port(False)
        self.water_delivery_complete = True
        log("Water delivery complete", "success")
        self.events.append({
          "type": "water_delivery_complete",
          "timestamp": current_time
        })

  def _update_nose_port_state(self):
    """Update nose port light and visual cue based on nose port entry"""
    if self.nose_port_entry:
      self.visual_cue = False
      self.nose_port_light = False

  def update(self, events):
    # Run update tasks
    self._update_water_delivery()

    # Handle PyGame events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          log("Trial canceled", "info")
          self.add_data("trial_canceled", True)
          self.add_data("trial_outcome", TrialOutcome.CANCELLED)
          return False

    # Track nose port state changes
    current_nose_state = self.get_input_states()["nose_poke"]

    if not current_nose_state and not self.nose_port_entry:
      # Detect nose port entry (nose_poke = False means nose is IN)
      self.nose_port_entry = True
      self.events.append({
        "type": "nose_port_entry",
        "timestamp": pygame.time.get_ticks()
      })
      log("Nose port entry detected", "info")
    elif current_nose_state and self.nose_port_entry and not self.nose_port_exit:
      # Detect nose port exit (nose_poke = True means nose is OUT)
      self.nose_port_exit = True
      self.events.append({
        "type": "nose_port_exit",
        "timestamp": pygame.time.get_ticks()
      })
      log("Nose port exit detected", "info")

    # Track lever presses
    left_lever = self.get_input_states()["left_lever"]
    right_lever = self.get_input_states()["right_lever"]

    if left_lever:
      self.events.append({
        "type": "left_lever_press",
        "timestamp": pygame.time.get_ticks()
      })

    if right_lever:
      self.events.append({
        "type": "right_lever_press",
        "timestamp": pygame.time.get_ticks()
      })

    # Condition for trial end - must have nose port entry, water delivery complete, AND nose port exit
    if self.nose_port_entry and self.water_delivery_complete and self.nose_port_exit:
      log("Trial complete: nose port entry, water delivery, and nose port exit", "success")
      self.add_data("trial_outcome", TrialOutcome.SUCCESS)
      return False

    # Update nose port state and light
    self._update_nose_port_state()
    self._update_nose_port_light()

    return True

  def _render_visual_cue(self):
    # Update visual state
    if not SIMULATION_MODE:
      if self.visual_cue:
        self.display.draw_alternating_pattern(self.cue_side)
      else:
        self.display.clear_displays()

  def _update_nose_port_light(self):
    # Update nose port light
    if not SIMULATION_MODE:
      self.io.set_nose_light(self.nose_port_light)

  def _pre_render_tasks(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

  def _post_render_tasks(self):
    # Add simulation mode banner if in simulation mode
    if SIMULATION_MODE and self.simulation_font:
      banner_text = f"[SIMULATION - {self.title}]"
      text_surface = self.simulation_font.render(banner_text, True, (255, 255, 255))
      text_rect = text_surface.get_rect(center=(self.width // 2, 20))
      self.screen.blit(text_surface, text_rect)

  def render(self):
    # Run pre-render tasks
    self._pre_render_tasks()

    # Run render tasks
    self._render_visual_cue()

    # Run post-render tasks
    self._post_render_tasks()

class Stage2(Base):
  """
  Trial Stage 2: Lever press for reward
  Description: At the beginning of each trial, randomly display the visual cue on one of the
    side screens. Either lever press will trigger reward water delivery. Turn off the visual
    cue upon lever press. Start the ITI counting after the mouse exits the nose port after
    obtaining water reward.
  """
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.title = "trial_stage_2"
    self.start_time = None
    self.water_start_time = None
    self.lever_press_start_time = None

    # Trial state
    self.nose_port_light = False
    self.delivered_water = False
    self.water_delivery_complete = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.nose_port_exit = False
    self.lever_press = False
    self.reward_triggered = False
    self.is_lever_pressed = False

    # Trial parameters
    self.cue_side = random.choice(["left", "right"])

    # Trial events
    self.events = []

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

    # Setup trial
    # Activate the nose port light and visual cue
    self.nose_port_light = True
    self.visual_cue = True

    # Clear the displays and randomly select the display to show the visual cue
    if not SIMULATION_MODE:
      self.display.clear_displays()
      self.display.draw_alternating_pattern(self.cue_side)
      log("Visual cue displayed on the " + self.cue_side + " side", "success")

    log("Trial started", "info")

  def on_exit(self):
    self.add_data("events", self.events)

  def update(self, events):
    current_time = pygame.time.get_ticks()

    # Condition for trial end
    if self.reward_triggered and self.water_delivery_complete and self.nose_port_exit:
      log("Trial ended after reward triggered, water delivery, and nose port exit", "success")
      self.add_data("trial_outcome", TrialOutcome.SUCCESS)
      return False

    # Handle any PyGame events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          log("Trial canceled", "info")
          self.add_data("trial_canceled", True)
          self.add_data("trial_outcome", TrialOutcome.CANCELLED)
          return False

    # Handle IO events (works for both real hardware and simulation)
    # Track nose port state changes
    current_nose_state = self.get_input_states()["nose_poke"]

    # Only consider nose port entry and exit if reward has been triggered
    if self.reward_triggered:
      if not current_nose_state and not self.nose_port_entry:
        self.nose_port_entry = True
        self.events.append({
          "type": "nose_port_entry",
          "timestamp": current_time
        })
        log("Nose port entry", "info")
      elif current_nose_state and self.nose_port_entry and not self.nose_port_exit:
        self.nose_port_exit = True
        self.events.append({
          "type": "nose_port_exit",
          "timestamp": current_time
        })
        log("Nose port exit", "info")

    # Track lever presses with minimum duration
    left_lever = self.get_input_states()["left_lever"]
    right_lever = self.get_input_states()["right_lever"]

    if (left_lever or right_lever) and not self.is_lever_pressed and not self.reward_triggered:
      # Check for lever press start
      self.is_lever_pressed = True
      self.lever_press_start_time = current_time
    elif self.is_lever_pressed and not (left_lever or right_lever):
      # Check for lever release or minimum duration
      self.is_lever_pressed = False
      self.lever_press_start_time = None
      log("Lever press released before minimum duration", "info")
    elif self.is_lever_pressed and not self.reward_triggered:
      if current_time - self.lever_press_start_time >= self.config["hold_minimum"]:
        self.reward_triggered = True
        self.is_lever_pressed = False
        self.lever_press_start_time = None
        log("Lever press held for minimum duration - reward triggered", "success")
        self.events.append({
          "type": "lever_press_reward",
          "timestamp": current_time
        })

    # Update water delivery
    self._update_water_delivery()
    self._update_nose_port_state()
    self._update_nose_port_light()
    self._update_visual_cue()

    return True

  def _update_water_delivery(self):
    current_time = pygame.time.get_ticks()

    # Start water delivery when reward is triggered
    if self.reward_triggered and not self.delivered_water:
      self.io.set_water_port(True)
      self.delivered_water = True
      self.water_start_time = current_time
      log("Water delivery started", "success")
      self.events.append({
        "type": "water_delivery_start",
        "timestamp": current_time
      })

    # Check if water delivery duration has elapsed
    elif self.delivered_water and not self.water_delivery_complete:
      if current_time - self.water_start_time >= self.config["valve_open"]:
        self.io.set_water_port(False)
        self.water_delivery_complete = True
        log("Water delivery complete", "success")
        self.events.append({
          "type": "water_delivery_complete",
          "timestamp": current_time
        })

  def _update_nose_port_state(self):
    """Update nose port light and visual cue based on nose port entry"""
    if self.nose_port_entry:
      self.visual_cue = False
      self.nose_port_light = False

  def _update_visual_cue(self):
    # Update visual state
    if not SIMULATION_MODE:
      if self.visual_cue:
        self.display.draw_alternating_pattern(self.cue_side)
      else:
        self.display.clear_displays()

  def _update_nose_port_light(self):
    # Update nose port light
    if not SIMULATION_MODE:
      self.io.set_nose_light(self.nose_port_light)

  def _pre_render_tasks(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

  def _post_render_tasks(self):
    # Add simulation mode banner if in simulation mode
    if SIMULATION_MODE and self.simulation_font:
      banner_text = f"[SIMULATION - {self.title}]"
      text_surface = self.simulation_font.render(banner_text, True, (255, 255, 255))
      text_rect = text_surface.get_rect(center=(self.width // 2, 20))
      self.screen.blit(text_surface, text_rect)

  def render(self):
    # Run pre-render tasks
    self._pre_render_tasks()

    # Run update tasks
    self._update_water_delivery()
    self._update_nose_port_state()
    self._update_visual_cue()
    self._update_nose_port_light()

    # Run post-render tasks
    self._post_render_tasks()

class Stage3(Base):
  """
  Trial Stage 3: Nose port entry followed by lever press for reward
  Description: At the beginning of each trial, lit up the nose port light. Upon the mouse entering
    the nose port, turn off the nose port light and randomly display the visual cue on one of the
    side screens. Either lever press will trigger reward water delivery while mouse keeps its nose
    in the nose port. Turn off the screen upon lever press. Or turn off the visual cue after the
    randomly generated cue display time between minimum and maximum cue display time if no lever
    pressing event detected. Premature nose withdraw will induce an error trial and terminate the trial.
  """
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.title = "trial_stage_3"
    self.start_time = None
    self.water_start_time = None
    self.cue_start_time = None
    self.lever_press_start_time = None

    # Trial state
    self.nose_port_light = False
    self.delivered_water = False
    self.water_delivery_complete = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.nose_port_exit = False
    self.lever_press = False
    self.reward_triggered = False
    self.is_error_trial = False
    self.is_lever_pressed = False

    # Trial parameters
    self.cue_side = random.choice(["left", "right"])
    self.cue_duration = random.randint(
      self.config["cue_minimum"],
      self.config["cue_maximum"]
    )

    # Trial events
    self.events = []

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

    # Setup trial
    # Activate the nose port light
    self.nose_port_light = True

    # Clear the displays
    if not SIMULATION_MODE:
      self.display.clear_displays()
    log("Trial started", "info")

  def on_exit(self):
    self.add_data("events", self.events)
    if self.is_error_trial:
      self.add_data("error_trial", True)
      self.add_data("error_type", "premature_withdrawal")

  def update(self, events):
    current_time = pygame.time.get_ticks()

    # Handle error trial condition - premature nose withdrawal
    if (
        self.nose_port_entry
        and not self.nose_port_exit
        and self.get_input_states()["nose_poke"]
        and not self.water_delivery_complete
    ):
      self.is_error_trial = True
      log("Error: Premature nose withdrawal", "error")
      self.add_data("trial_outcome", TrialOutcome.FAILURE_NOSEPORT)
      return False

    # Condition for trial end - when water delivery is complete and nose port is exited
    if self.water_delivery_complete and self.nose_port_exit:
      log("Trial ended after water delivery and nose port exit", "success")
      self.add_data("trial_outcome", TrialOutcome.SUCCESS)
      return False

    # Handle any PyGame events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          log("Trial canceled", "info")
          self.add_data("trial_canceled", True)
          self.add_data("trial_outcome", TrialOutcome.CANCELLED)
          return False

    # Handle IO events (works for both real hardware and simulation)
    # Track nose port state changes
    current_nose_state = self.get_input_states()["nose_poke"]

    if not current_nose_state and not self.nose_port_entry:
      # Detect nose port entry (nose_poke = False means nose is IN)
      self.nose_port_entry = True
      self.cue_start_time = current_time
      self.events.append({
        "type": "nose_port_entry",
        "timestamp": current_time
      })
      log("Nose port entry", "info")
    elif current_nose_state and self.nose_port_entry and not self.nose_port_exit:
      # Detect nose port exit (nose_poke = True means nose is OUT)
      self.nose_port_exit = True
      self.events.append({
        "type": "nose_port_exit",
        "timestamp": current_time
      })
      log("Nose port exit", "info")

    # Track lever presses with minimum duration
    left_lever = self.get_input_states()["left_lever"]
    right_lever = self.get_input_states()["right_lever"]

    if (left_lever or right_lever) and not self.is_lever_pressed and self.nose_port_entry and not self.reward_triggered:
      # Check for lever press start
      self.is_lever_pressed = True
      self.lever_press_start_time = current_time
    elif self.is_lever_pressed and not (left_lever or right_lever):
      # Check for lever release or minimum duration
      self.is_lever_pressed = False
      self.lever_press_start_time = None
      log("Lever press released before minimum duration", "info")
    elif self.is_lever_pressed and not self.reward_triggered:
      if current_time - self.lever_press_start_time >= self.config["hold_minimum"]:
        self.reward_triggered = True
        self.visual_cue = False
        if left_lever:
          self.events.append({
            "type": "left_lever_press",
            "timestamp": current_time,
            "duration": current_time - self.lever_press_start_time
          })
        if right_lever:
          self.events.append({
            "type": "right_lever_press",
            "timestamp": current_time,
            "duration": current_time - self.lever_press_start_time
          })

    # Update water delivery and other tasks
    self._update_water_delivery()
    self._update_nose_port_state()
    self._update_visual_cue()
    self._update_nose_port_light()

    # Check if cue duration has elapsed without lever press
    if self.nose_port_entry and not self.reward_triggered and self.cue_start_time:
      if current_time - self.cue_start_time >= self.cue_duration:
        self.visual_cue = False
        log("Cue duration elapsed without lever press", "info")
        self.events.append({
          "type": "cue_timeout",
          "timestamp": current_time
        })
        # Trial failure
        self.add_data("trial_outcome", TrialOutcome.FAILURE_NOLEVER)
        return False

    return True

  def _update_water_delivery(self):
    current_time = pygame.time.get_ticks()

    # Start water delivery when reward is triggered
    if self.reward_triggered and not self.delivered_water:
      self.io.set_water_port(True)
      self.delivered_water = True
      self.water_start_time = current_time
      log("Water delivery started", "success")
      self.events.append({
        "type": "water_delivery_start",
        "timestamp": current_time
      })

    # Check if water delivery duration has elapsed
    elif self.delivered_water and not self.water_delivery_complete:
      if current_time - self.water_start_time >= self.config["valve_open"]:
        self.io.set_water_port(False)
        self.water_delivery_complete = True
        log("Water delivery complete", "success")
        self.events.append({
          "type": "water_delivery_complete",
          "timestamp": current_time
        })

  def _update_nose_port_state(self):
    """Update nose port light and visual cue based on nose port entry"""
    if self.nose_port_entry:
      self.visual_cue = False
      self.nose_port_light = False

  def _update_visual_cue(self):
    # Update visual state
    if not SIMULATION_MODE:
      if self.visual_cue:
        self.display.draw_alternating_pattern(self.cue_side)
      else:
        self.display.clear_displays()

  def _update_nose_port_light(self):
    # Update nose port light
    if not SIMULATION_MODE:
      self.io.set_nose_light(self.nose_port_light)

  def _pre_render_tasks(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

  def _post_render_tasks(self):
    # Add simulation mode banner if in simulation mode
    if SIMULATION_MODE and self.simulation_font:
      banner_text = f"[SIMULATION - {self.title}]"
      text_surface = self.simulation_font.render(banner_text, True, (255, 255, 255))
      text_rect = text_surface.get_rect(center=(self.width // 2, 20))
      self.screen.blit(text_surface, text_rect)

  def render(self):
    # Run pre-render tasks
    self._pre_render_tasks()

    # Run update tasks
    self._update_water_delivery()
    self._update_nose_port_state()
    self._update_visual_cue()
    self._update_nose_port_light()

    # Run post-render tasks
    self._post_render_tasks()
