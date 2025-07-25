import asyncio
import threading
import time
import websockets
import json
import queue
import pygame
from dataclasses import asdict
from device.hardware.IOController import IOController
from device.hardware.DisplayController import DisplayController
from device.hardware.DataController import DataController
from device.utils.logger import log, set_message_queue
from device.utils.helpers import Randomness
from device.core.timeline_processor import TimelineProcessor
from shared.constants import TEST_COMMANDS, TEST_STATES, INPUT_TEST_TIMEOUT, DEFAULT_HOST, DEFAULT_PORT
from shared.communication import MessageBuilder, MessageParser, CommandParser
from shared.test_management import TestStateManager

# Other variables
HOST = DEFAULT_HOST
PORT = DEFAULT_PORT

# Create a global device and message queue
_device = None
_device_message_queue = None

class Device:
  def __init__(self):
    # Initialize controllers
    self.io = IOController()
    self.display = DisplayController()
    self._data = None

    # Randomness
    self.randomness = Randomness()

    # Timeline processor
    self.timeline_processor = TimelineProcessor(self)

    # Load config
    self.config = None
    self.version = None
    with open("config.json") as config_file:
      config_data = json.load(config_file)
      self.config = config_data["task"]
      self.version = config_data.get("version", "unknown")

    # Setup display state
    self._display_state = {
      "mini_display_1": {
        "state": False,
      },
      "mini_display_2": {
        "state": False,
      },
    }

    # Test state management
    self.test_state_manager = TestStateManager()

    self._input_states = {
      "left_lever": False,
      "right_lever": False,
      "nose_poke": False,
      "water_port": False,
      "nose_light": False,
    }

    # Statistics tracking
    self._statistics = {
      "nose_pokes": 0,
      "left_lever_presses": 0,
      "right_lever_presses": 0,
      "trial_count": 0,
      "water_deliveries": 0
    }

    # Track previous input states for detecting changes
    self._previous_input_states = {
      "left_lever": False,
      "right_lever": False,
      "nose_poke": False,
      "water_port": False,
      "nose_light": False,
    }

    # Initialize pygame in the new process
    pygame.init()

    # Setup screen - use windowed mode in simulation to avoid minimization issues
    screen_info = pygame.display.Info()

    # Use windowed mode if in simulation mode, fullscreen otherwise
    is_simulation = hasattr(self.io, '_simulated_inputs') and self.io._simulated_inputs

    if is_simulation:
      # Use a reasonable window size for simulation
      self.width = 800
      self.height = 600
      display_flags = 0
    else:
      # Use fullscreen for real hardware
      self.width = screen_info.current_w
      self.height = screen_info.current_h
      display_flags = pygame.FULLSCREEN

    self.screen = pygame.display.set_mode(
      (self.width, self.height),
      display_flags
    )
    self.screen.fill((0, 0, 0))
    self.font = pygame.font.SysFont("Arial", 64)

    # Setup trials - start with no timeline
    self._current_trial = None
    self._trials = []

    # Experiment state
    self._experiment_started = False
    self._running = True
    self._websocket_server = None  # Store reference to websocket server
    self._original_timeline_config = None  # Store original timeline configuration for looping
    self._should_loop = False  # Whether the timeline should loop

    # Experiment parameters (will be set when experiment starts)
    self._punishment_duration = 1000
    self._water_delivery_duration = 2000

  def _reset_trials(self):
    """Reset the trials list to its initial state"""
    self._trials = []
    for trial in self._trials:
      trial.screen = self.screen
      trial.font = self.font
      trial.width = self.width
      trial.height = self.height
      trial.io = self.io
      trial.display = self.display

    log(f"Trials reset: {len(self._trials)} trials ready for next experiment", "info")

  def _render_waiting_screen(self):
    """Render the waiting screen with timeline upload message"""
    self.screen.fill((0, 0, 0))

    # Main waiting text
    text = self.font.render("Waiting...", True, (255, 255, 255))
    text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
    self.screen.blit(text, text_rect)

    # Version text (smaller font)
    version_font = pygame.font.SysFont("Arial", 24)
    version_text = version_font.render(f"Version: {self.version}", True, (150, 150, 150))
    version_rect = version_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
    self.screen.blit(version_text, version_rect)

    # Show simulation controls if in simulation mode
    if hasattr(self.io, '_simulated_inputs') and self.io._simulated_inputs:
      # Create a smaller font for simulation controls
      sim_font = pygame.font.SysFont("Arial", 20)

      # Show current input states
      input_states = self.io.get_input_states()
      state_text = [
        f"Left Lever: {'PRESSED' if input_states['left_lever'] else 'RELEASED'}",
        f"Right Lever: {'PRESSED' if input_states['right_lever'] else 'RELEASED'}",
        f"Nose Poke: {'ACTIVE' if input_states['nose_poke'] else 'INACTIVE'}",
        f"Water Port: {'ON' if input_states['water_port'] else 'OFF'}"
      ]

      # Render state text
      for i, line in enumerate(state_text):
        if 'PRESSED' in line or 'ACTIVE' in line or 'ON' in line:
          color = (0, 255, 0) # Green
        else:
          color = (255, 100, 100) # Red

        line_surface = sim_font.render(line, True, color)
        line_rect = line_surface.get_rect(
          center=(self.width // 2, self.height // 2 + 100 + i * 25)
        )
        self.screen.blit(line_surface, line_rect)

    pygame.display.flip()

  def update(self):
    """Update device state and handle events"""
    events = pygame.event.get()

    # Handle quit event
    for event in events:
      if event.type == pygame.QUIT:
        self._running = False
        return False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          self._running = False
          return False
        # Simulation mode controls
        elif hasattr(self.io, '_simulated_inputs') and self.io._simulated_inputs:
          if event.key == pygame.K_1: # Left lever press
            self.io.simulate_left_lever(True)
          elif event.key == pygame.K_2: # Right lever press
            self.io.simulate_right_lever(True)
          elif event.key == pygame.K_3: # Nose poke entry
            self.io.simulate_nose_poke(False)
          elif event.key == pygame.K_SPACE: # Nose poke entry (existing)
            self.io.simulate_nose_poke(False)
      elif event.type == pygame.KEYUP:
        # Simulation mode controls - release
        if hasattr(self.io, '_simulated_inputs') and self.io._simulated_inputs:
          if event.key == pygame.K_1: # Left lever release
            self.io.simulate_left_lever(False)
          elif event.key == pygame.K_2: # Right lever release
            self.io.simulate_right_lever(False)
          elif event.key == pygame.K_3: # Nose poke exit
            self.io.simulate_nose_poke(True)
          elif event.key == pygame.K_SPACE: # Nose poke exit (existing)
            self.io.simulate_nose_poke(True)

    # Update input states and statistics
    self._update_input_states_and_statistics()

    if not self._experiment_started:
      # Show waiting screen
      self._render_waiting_screen()
    elif self._current_trial:
      # Update and render current trial
      if not self._current_trial.update(events):
        # Trial is complete, move to next trial
        self._current_trial.on_exit()

        # Increment trial count
        self._statistics["trial_count"] += 1

        # Save trial data
        trial_data = self._current_trial.get_data()
        if trial_data and self._data:
          self._data.add_trial_data(self._current_trial.title, trial_data)

        log("Finished trial: " + self._current_trial.title, "info")

        # Send message about trial completion
        _device_message_queue.put(MessageBuilder.trial_complete(self._current_trial.title, trial_data))

        if len(self._trials) > 0:
          self._current_trial = self._trials.pop(0)
          self._current_trial.on_enter()

          # Send message about new trial starting
          _device_message_queue.put(MessageBuilder.trial_start(self._current_trial.title))
        else:
          # All trials completed - check if we should loop
          if self._should_loop and self._original_timeline_config:
            # Reset trials for next loop by creating new trial instances
            self._trials = []
            for trial_config in self._original_timeline_config:
              # Create a new trial instance with the same parameters
              new_trial = self.timeline_processor.trial_factory.create_trial(
                trial_config["type"],  # Get the trial type name
                trial_config["kwargs"],  # Use the original parameters
                screen=self.screen,
                font=self.font,
                width=self.width,
                height=self.height,
                io=self.io,
                display=self.display
              )
              self._trials.append(new_trial)

            self._current_trial = self._trials.pop(0)
            self._current_trial.on_enter()

            log("Timeline loop completed, starting next iteration", "info")
            _device_message_queue.put(MessageBuilder.trial_start(self._current_trial.title))
          else:
            # All trials completed - save data before resetting
            if self._data:
              # Save final statistics
              self._data.add_statistics(self.get_statistics())
              if not self._data.save():
                log("Failed to save data", "error")
              else:
                log("Data saved successfully", "success")

            self._experiment_started = False
            self._current_trial = None

            # Clear trials - timeline must be re-uploaded for next experiment
            self._trials = []
            self._original_timeline_config = None
            self._should_loop = False
            log("Experiment completed, timeline cleared, returning to waiting state", "info")

            # Send message that task is complete
            _device_message_queue.put(MessageBuilder.task_status("completed"))

      # Render current trial
      if self._current_trial:
        self._current_trial.render()
        pygame.display.flip()

    return True

  def _update_input_states_and_statistics(self):
    """Update input states and track statistics based on changes"""
    # Get current input states
    current_input_states = self.io.get_input_states()

    # Update device input states
    self._input_states = current_input_states.copy()

    # Check for changes and update statistics
    if self._experiment_started:  # Only track during experiments
      # Check for nose poke activation (transition from True to False)
      if self._previous_input_states["nose_poke"] and not current_input_states["nose_poke"]:
        self._statistics["nose_pokes"] += 1

      # Check for left lever press (transition from False to True)
      if not self._previous_input_states["left_lever"] and current_input_states["left_lever"]:
        self._statistics["left_lever_presses"] += 1

      # Check for right lever press (transition from False to True)
      if not self._previous_input_states["right_lever"] and current_input_states["right_lever"]:
        self._statistics["right_lever_presses"] += 1

      # Check for water delivery (transition from False to True)
      if not self._previous_input_states["water_port"] and current_input_states["water_port"]:
        self._statistics["water_deliveries"] += 1

    # Update previous states for next comparison
    self._previous_input_states = current_input_states.copy()

  def get_statistics(self):
    """Get current statistics"""
    return self._statistics.copy()

  def reset_statistics(self):
    """Reset all statistics to zero"""
    self._statistics = {
      "nose_pokes": 0,
      "left_lever_presses": 0,
      "right_lever_presses": 0,
      "trial_count": 0,
      "water_deliveries": 0
    }

  def start_experiment(self, animal_id, punishment_duration=1000, water_delivery_duration=2000):
    """Start the experiment with the given animal ID and duration parameters"""
    if self._experiment_started:
      log("Experiment already running", "warning")
      return

    # Check if trials are available
    if not self._trials:
      log("No timeline available - please upload a timeline first", "error")
      return

    # Reset statistics for new experiment
    self.reset_statistics()

    # Store the experiment parameters
    self._punishment_duration = punishment_duration
    self._water_delivery_duration = water_delivery_duration

    # Log the parameters
    log(f"Starting experiment with animal ID: {animal_id}, punishment duration: {punishment_duration}ms, water delivery duration: {water_delivery_duration}ms", "info")

    # Initialize data controller with animal ID
    self._data = DataController(animal_id)

    # Convert ExperimentConfig to dictionary for JSON serialization
    if hasattr(self.config, '__dataclass_fields__'):
      # It's a dataclass (ExperimentConfig), convert to dict
      config_dict = asdict(self.config)
    else:
      # It's already a dict or other type
      config_dict = self.config

    self._data.add_task_data({"config": config_dict})

    # Add punishment duration to ITI trials
    for trial in self._trials:
      if trial.title == "trial_iti":
        trial.set_duration(trial.duration + self._punishment_duration)

    # Start first trial
    self._current_trial = self._trials.pop(0)
    self._current_trial.on_enter()
    self._experiment_started = True

    # Send initial message that task has started
    _device_message_queue.put(MessageBuilder.task_status("started", self._current_trial.title))

    log("Experiment started", "info")

  def start_experiment_with_timeline(self, animal_id, trials, config=None, loop=False, trial_configs=None):
    """Start the experiment with a custom timeline"""
    if self._experiment_started:
      log("Experiment already running", "warning")
      return

    # Reset statistics for new experiment
    self.reset_statistics()

    # Log the parameters
    log(f"Starting timeline experiment with animal ID: {animal_id}, {len(trials)} trials", "info")

    # Initialize data controller with animal ID
    self._data = DataController(animal_id)

    # Use provided config or fall back to default
    experiment_config = config or self.config

    # Convert ExperimentConfig to dictionary for JSON serialization
    if hasattr(experiment_config, '__dataclass_fields__'):
      # It's a dataclass (ExperimentConfig), convert to dict
      config_dict = asdict(experiment_config)
    else:
      # It's already a dict or other type
      config_dict = experiment_config

    self._data.add_task_data({"config": config_dict})

    # Set trials from timeline
    self._trials = trials.copy()
    self._original_timeline_config = trial_configs or []  # Store original timeline configuration
    self._should_loop = loop  # Set loop flag

    # Start first trial
    self._current_trial = self._trials.pop(0)
    self._current_trial.on_enter()
    self._experiment_started = True

    # Send initial message that task has started
    _device_message_queue.put(MessageBuilder.task_status("started", self._current_trial.title))

    log("Timeline experiment started", "info")

  def stop_experiment(self):
    """Stop the current experiment"""
    if not self._experiment_started:
      log("No experiment running", "warning")
      return

    # Stop the current experiment
    self._experiment_started = False
    self._current_trial = None

    # Clear trials - timeline must be re-uploaded for next experiment
    self._trials = []

    # Save data if available (fallback for manual stopping)
    if self._data:
      # Save final statistics
      self._data.add_statistics(self.get_statistics())
      if not self._data.save():
        log("Failed to save data", "error")
      else:
        log("Data saved", "success")

    # Send message that experiment has stopped
    _device_message_queue.put(MessageBuilder.task_status("stopped"))

    log("Experiment stopped", "info")

  async def _test_water_delivery(self, duration_ms=2000):
    try:
      self.io.set_water_port(True)
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.io.set_water_port(False)
    except Exception as e:
      self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not activate water delivery: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_water_delivery") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["PASSED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Test water delivery passed (duration: {duration_ms}ms)", "success")

  def test_water_delivery(self, duration_ms=2000):
    log(f"Testing water delivery for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_water_delivery(duration_ms))

  def _test_actuators(self):
    # Step 2: Test that the left actuator can be moved to 1.0
    log("Testing left actuator", "start")
    log("Waiting for left actuator input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self.io.get_input_states()
      if input_state["left_lever"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
        _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Left actuator input timed out", "error")
        return

    if input_state["left_lever"] != True:
      self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Left actuator did not move to 1.0", "error")
      return

    log("Left actuator test passed", "success")

    # Step 3: Test that the right actuator can be moved to 1.0
    running_input_test = True
    running_input_test_start_time = time.time()
    log("Testing right actuator", "start")
    log("Waiting for right actuator input...", "info")
    while running_input_test:
      input_state = self.io.get_input_states()
      if input_state["right_lever"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
        _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Right actuator input timed out", "error")
        return

    if input_state["right_lever"] != True:
      self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Right actuator did not move to 1.0", "error")
      return

    log("Right actuator test passed", "success")

    # Set test to passed
    if self.test_state_manager.get_test_state("test_actuators") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_actuators", TEST_STATES["PASSED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Actuators test passed", "success")

  def test_actuators(self):
    log("Testing actuators", "start")
    self.test_state_manager.set_test_state("test_actuators", TEST_STATES["RUNNING"])

    # Step 1: Test that both actuators default to 0.0
    input_state = self.io.get_input_states()
    if input_state["left_lever"] != False:
      self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Left actuator did not default to 0.0", "error")
      return

    if input_state["right_lever"] != False:
      self.test_state_manager.set_test_state("test_actuators", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Right actuator did not default to 0.0", "error")
      return

    log("Actuators defaulted to 0.0", "success")

    # Run the test in a separate thread
    actuator_test_thread = threading.Thread(target=self._test_actuators)
    actuator_test_thread.start()

  def _test_ir(self):
    # Step 1: Test that the IR is broken
    log("Waiting for IR input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self.io.get_input_states()
      if input_state["nose_poke"] == False:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_ir", TEST_STATES["FAILED"])
        _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Timed out while waiting for IR input", "error")
        return

    if input_state["nose_poke"] != False:
      self.test_state_manager.set_test_state("test_ir", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("No IR input detected", "error")
      return

    # Set test to passed
    if self.test_state_manager.get_test_state("test_ir") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_ir", TEST_STATES["PASSED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("IR test passed", "success")

  def test_ir(self):
    log("Testing IR", "start")
    self.test_state_manager.set_test_state("test_ir", TEST_STATES["RUNNING"])

    # Run the test in a separate thread
    ir_test_thread = threading.Thread(target=self._test_ir)
    ir_test_thread.start()

  async def _test_nose_light(self, duration_ms=2000):
    try:
      # Turn on the nose light
      self.io.set_nose_light(True)
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.io.set_nose_light(False)
    except Exception as e:
      self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not control nose light: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_nose_light") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["PASSED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Nose light test passed (duration: {duration_ms}ms)", "success")

  def test_nose_light(self, duration_ms=2000):
    log(f"Testing nose light for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_nose_light(duration_ms))

  async def _test_displays(self, duration_ms=2000):
    try:
      # Draw test pattern on both displays
      self.display.draw_test_pattern("both")
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      # Clear displays after test
      self.display.clear_displays()
    except Exception as e:
      self.test_state_manager.set_test_state("test_displays", TEST_STATES["FAILED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not control displays: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_displays") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_displays", TEST_STATES["PASSED"])
      _device_message_queue.put(MessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Display test passed (duration: {duration_ms}ms)", "success")

  def test_displays(self, duration_ms=2000):
    log(f"Testing displays for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_displays", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_displays(duration_ms))

  def run_test(self, command):
    if command == "test_water_delivery":
      self.test_water_delivery()
    elif command.startswith("test_water_delivery"):
      # Parse duration from command: "test_water_delivery <duration_ms>"
      parts = command.split(" ")
      if len(parts) > 1:
        try:
          duration_ms = int(parts[1])
          self.test_water_delivery(duration_ms)
        except ValueError:
          log(f"Invalid duration for water delivery test: {parts[1]}", "error")
      else:
        self.test_water_delivery()  # Use default duration
    elif command == "test_actuators":
      self.test_actuators()
    elif command == "test_ir":
      self.test_ir()
    elif command == "test_nose_light":
      self.test_nose_light()
    elif command.startswith("test_nose_light"):
      # Parse duration from command: "test_nose_light <duration_ms>"
      parts = command.split(" ")
      if len(parts) > 1:
        try:
          duration_ms = int(parts[1])
          self.test_nose_light(duration_ms)
        except ValueError:
          log(f"Invalid duration for nose light test: {parts[1]}", "error")
      else:
        self.test_nose_light()  # Use default duration
    elif command == "test_displays":
      self.test_displays()
    elif command.startswith("test_displays"):
      # Parse duration from command: "test_displays <duration_ms>"
      parts = command.split(" ")
      if len(parts) > 1:
        try:
          duration_ms = int(parts[1])
          self.test_displays(duration_ms)
        except ValueError:
          log(f"Invalid duration for display test: {parts[1]}", "error")
      else:
        self.test_displays()  # Use default duration

  def run_experiment(self, command):
    primary_command = command.split(" ")[0]
    arguments = command.split(" ")[1:]

    if primary_command == "start_experiment":
      # Extract parameters from command string: "start_experiment <animal_id> <punishment_duration> <water_delivery_duration>"
      animal_id = arguments[0] if len(arguments) > 0 else ""

      # Parse duration parameters with defaults
      punishment_duration = 1000  # Default 1000ms
      water_delivery_duration = 2000  # Default 2000ms

      if len(arguments) > 1:
        try:
          punishment_duration = int(arguments[1])
        except ValueError:
          log(f"Invalid punishment duration: {arguments[1]}, using default 1000ms", "warning")

      if len(arguments) > 2:
        try:
          water_delivery_duration = int(arguments[2])
        except ValueError:
          log(f"Invalid water delivery duration: {arguments[2]}, using default 2000ms", "warning")

      if animal_id:
        # Use the existing start_experiment method which properly integrates with the device flow
        self.start_experiment(animal_id, punishment_duration, water_delivery_duration)
      else:
        log("Missing animal ID for start_experiment command", "error")

    elif primary_command == "stop_experiment":
      self.stop_experiment()
    else:
      log(f"Unknown command: {command}", "error")

  def cleanup(self):
    """Clean up resources before shutdown"""
    # Stop any running experiment
    if self._experiment_started:
      self.stop_experiment()

    # Close pygame
    pygame.quit()

    # Clean up controllers
    if hasattr(self, 'io'):
      del self.io
    if hasattr(self, 'display'):
      del self.display

  def reset_test_state(self):
    """Reset all test states to NOT_TESTED"""
    self.test_state_manager.reset_test_states()
    log("Test states reset to NOT_TESTED", "info")

async def send_queued_messages(websocket):
  """
  Sends messages from the message queue to the control panel.
  """
  while True:
    try:
      # Check if there are messages in the queue
      while not _device_message_queue.empty():
        message_data = _device_message_queue.get()
        await websocket.send(json.dumps(message_data))
      await asyncio.sleep(0.05)  # Sleep for 50ms
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def send_state_message(websocket):
  """
  Sends the current state of the device to the control panel.
  """
  while True:
    try:
      state_data = MessageBuilder.input_state(_device.io.get_input_states(), _device.version)
      await websocket.send(json.dumps(state_data))

      # Also send statistics if experiment is running
      if _device._experiment_started:
        stats_data = MessageBuilder.statistics(_device.get_statistics())
        await websocket.send(json.dumps(stats_data))

      await asyncio.sleep(0.05)
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def handle_connection(websocket, device: Device):
  """Handle a single websocket connection"""
  try:
    # Start message sender tasks
    message_sender_task = asyncio.create_task(send_queued_messages(websocket))
    state_sender_task = asyncio.create_task(send_state_message(websocket))

    # Handle incoming messages
    async for message in websocket:
      try:
        # Try to parse as JSON first (for timeline messages)
        message_data = MessageParser.parse_message(message)
        if message_data and "type" in message_data:
          await handle_json_message(websocket, device, message_data)
          continue

        # Handle text commands (legacy)
        command = message.strip()
        if CommandParser.parse_test_command(command)[0] in TEST_COMMANDS:
          device.run_test(command)
        elif command.startswith("start_experiment"):
          device.run_experiment(command)
        elif command == "stop_experiment":
          device.stop_experiment()
        else:
          log(f"Unknown command: {command}", "error")
      except Exception as e:
        log(f"Error handling message: {str(e)}", "error")

    # Cleanup sender tasks
    message_sender_task.cancel()
    state_sender_task.cancel()
    try:
      await asyncio.wait_for(asyncio.gather(message_sender_task, state_sender_task), timeout=1.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
      pass
  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    # Reset test state when control panel disconnects
    device.reset_test_state()
    await websocket.close()

async def handle_json_message(websocket, device: Device, message_data: dict):
  """Handle JSON messages from the control panel"""
  message_type = message_data.get("type")

  if message_type == "timeline_upload":
    # Handle timeline upload
    timeline_data = message_data.get("data", {})
    success, message = device.timeline_processor.process_timeline_upload(timeline_data)

    # Send validation response
    response = MessageBuilder.timeline_validation(success, message)
    await websocket.send(json.dumps(response))

    if success:
      log(f"Timeline uploaded successfully: {message}", "success")
    else:
      log(f"Timeline upload failed: {message}", "error")

  elif message_type == "start_timeline_experiment":
    # Handle timeline experiment start
    animal_id = message_data.get("animal_id", "")
    if not animal_id:
      response = MessageBuilder.timeline_error("Animal ID is required")
      await websocket.send(json.dumps(response))
      return

    success, message = device.timeline_processor.execute_timeline(animal_id)

    if success:
      response = MessageBuilder.timeline_validation(success, message)
    else:
      response = MessageBuilder.timeline_error(message)
    await websocket.send(json.dumps(response))

    if success:
      log(f"Timeline experiment started: {message}", "success")
    else:
      log(f"Timeline experiment failed: {message}", "error")

  else:
    log(f"Unknown JSON message type: {message_type}", "warning")

async def main_loop(device):
  """Main loop that runs both pygame and websocket communication"""
  log("Starting main loop", "info")

  # Create websocket server
  server = await websockets.serve(
    lambda ws: handle_connection(ws, device),
    HOST,
    PORT
  )
  device._websocket_server = server

  try:
    # Main loop
    while device._running:
      # Update device state
      if not device.update():
        log("Initiating shutdown...", "info")
        break

      # Process websocket messages
      await asyncio.sleep(0)  # Allow other tasks to run
      await asyncio.sleep(1/60)
  finally:
    # Emergency data save on shutdown
    if device._data:
      log("Emergency data save before shutdown...", "info")
      try:
        if device._data.save():
          log("Emergency data save successful", "success")
        else:
          log("Emergency data save failed", "error")
      except Exception as e:
        log(f"Error during emergency data save: {str(e)}", "error")

    # Cleanup
    if device._websocket_server:
      active_connections = list(device._websocket_server.websockets)
      if active_connections:
        for websocket in active_connections:
          try:
            await asyncio.wait_for(websocket.close(), timeout=0.5)
          except (asyncio.TimeoutError, Exception) as e:
            log(f"Error closing connection, connection may already be closed", "warning")

      # Close the server immediately
      device._websocket_server.close()

    # Cancel any remaining tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
      log(f"Cancelling {len(tasks)} remaining tasks...", "info")
      for task in tasks:
        task.cancel()
        try:
          await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
          pass

    device.cleanup()
    log("Main loop stopped", "info")

def main():
  global _device, _device_message_queue

  try:
    # Initialize the device
    _device = Device()
    _device_message_queue = queue.Queue()

    # Set the message queue in the logging module
    set_message_queue(_device_message_queue)

    # Run the main loop
    asyncio.run(main_loop(_device))
  except KeyboardInterrupt:
    log("Keyboard interrupt received", "info")
  except asyncio.TimeoutError:
    log("Main loop timed out", "error")
  except Exception as e:
    log(f"Error in main loop: {str(e)}", "error")
  finally:
    # Ensure cleanup happens even if there's an error
    if _device:
      _device.cleanup()

if __name__ == "__main__":
  main()
