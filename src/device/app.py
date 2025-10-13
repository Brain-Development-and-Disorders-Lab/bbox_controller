#!/usr/bin/env python3
"""
Filename: device/app.py
Author: Henry Burgess
Date: 2025-07-29
Description: Main application for the device script, handles hardware control, display, and communication with control panel
License: MIT
"""

import pygame
import json
import time
import threading
import asyncio
import websockets
import queue
import subprocess

from shared.constants import *
from shared.models import Config
from shared.managers import CommunicationMessageBuilder, CommunicationMessageParser, TestStateManager, StatisticsManager
from shared import VERSION

from device.hardware.GPIOController import GPIOController
from device.hardware.DisplayController import DisplayController
from device.hardware.DataController import DataController
from device.core.ExperimentProcessor import ExperimentProcessor
from device.utils.logger import log, set_message_queue
from device.utils.helpers import Randomness

# Global device and message queue
_device = None
_device_message_queue = None

# Constants
HOST = DEFAULT_HOST
PORT = DEFAULT_PORT

class Device:
  def __init__(self):
    self._data = None

    self.version = VERSION
    self.config = None

    self.randomness = Randomness()
    self.gpio = GPIOController()
    self.display = DisplayController()
    self.experiment_processor = ExperimentProcessor(self)
    self.statistics_controller = StatisticsManager()
    self.test_state_manager = TestStateManager()

    # Input states
    self._input_states = {
      "input_lever_left": False,
      "input_lever_right": False,
      "input_ir": False,
      "input_port": False,
      "led_port": False,
      "led_lever_left": False,
      "led_lever_right": False
    }
    self._previous_input_states = {
      "input_lever_left": False,
      "input_lever_right": False,
      "input_ir": False,
      "input_port": False,
      "led_port": False,
      "led_lever_left": False,
      "led_lever_right": False
    }

    # Initialize pygame
    pygame.init()
    screen_info = pygame.display.Info()
    is_simulation = self.gpio.is_simulating_gpio()

    if is_simulation:
      # Windowed mode for simulation
      self.width = 800
      self.height = 600
      display_flags = 0
    else:
      self.width = screen_info.current_w
      self.height = screen_info.current_h
      display_flags = pygame.FULLSCREEN

    self.screen = pygame.display.set_mode(
      (self.width, self.height),
      display_flags
    )
    self.screen.fill((0, 0, 0))
    self.font = pygame.font.SysFont("Arial", 64)

    # Trial management
    self._current_trial = None
    self._trials = []
    self._trial_configs = []
    self._should_loop = False

    # Experiment state
    self._experiment_started = False
    self._running = True
    self._websocket_server = None

    # Connection state
    self._control_panel_connected = False

  def _get_local_ip(self):
    """Get the local IP address of the device for LAN connections"""
    try:
      # Method 1: Try hostname -I
      result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=1)
      if result.returncode == 0:
        ips = result.stdout.strip().split()
        for ip in ips:
          if ip and not ip.startswith('127.') and not ip.startswith('::'):
            return ip
    except:
      pass

    try:
      # Method 2: Try ifconfig
      result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=1)
      if result.returncode == 0:
        for line in result.stdout.split('\n'):
          if 'inet ' in line and '127.0.0.1' not in line:
            parts = line.split()
            ip = parts[1] if len(parts) > 1 else None
            if ip and not ip.startswith('127.'):
              return ip
    except:
      pass

    return "127.0.0.1"

  def _render_waiting_screen(self):
    """Render the waiting screen with timeline upload message"""
    self.screen.fill((0, 0, 0))

    # Check for hardware simulation warnings
    simulated_components = []
    if self.gpio.is_simulating_gpio():
      simulated_components.append("GPIO")
    if self.display.is_simulating_displays():
      simulated_components.append("Displays")

    # Draw orange warning banner if any components are simulated
    banner_height = 40
    if simulated_components:
      # Orange banner background
      banner_rect = pygame.Rect(0, 0, self.width, banner_height)
      pygame.draw.rect(self.screen, (255, 165, 0), banner_rect)  # Orange color

      # Warning text
      warning_font = pygame.font.SysFont("Arial", 24)
      warning_text = f"Simulated: {', '.join(simulated_components)}"
      warning_surface = warning_font.render(warning_text, True, (0, 0, 0))  # Black text
      warning_rect = warning_surface.get_rect(center=(self.width // 2, banner_height // 2))
      self.screen.blit(warning_surface, warning_rect)

    # Status text in center (adjusted for banner)
    main_font = pygame.font.SysFont("Arial", 48)
    if self._control_panel_connected:
      main_text = main_font.render("Ready", True, (255, 255, 255))
    else:
      main_text = main_font.render("Waiting for connection...", True, (255, 255, 255))

    # Adjust center position if banner is present
    center_y = self.height // 2
    if simulated_components:
      center_y = (self.height - banner_height) // 2 + banner_height

    main_rect = main_text.get_rect(center=(self.width // 2, center_y))
    self.screen.blit(main_text, main_rect)

    # IP address beneath main text
    ip_address = self._get_local_ip()
    ip_font = pygame.font.SysFont("Arial", 32)
    ip_text = ip_font.render(ip_address, True, (255, 255, 255))
    ip_rect = ip_text.get_rect(center=(self.width // 2, center_y + 60))
    self.screen.blit(ip_text, ip_rect)

    # Version at bottom of screen
    version_font = pygame.font.SysFont("Arial", 20)
    version_text = version_font.render(f"Version: {self.version}", True, (255, 255, 255))
    version_rect = version_text.get_rect(center=(self.width // 2, self.height - 30))
    self.screen.blit(version_text, version_rect)

    # Simulation indicators in top left corner (if in simulation mode)
    if hasattr(self.gpio, '_simulated_inputs') and self.gpio._simulated_inputs:
      sim_font = pygame.font.SysFont("Arial", 16)
      input_states = self.gpio.get_gpio_state()
      state_text = [
        f"Left Lever: {'PRESSED' if input_states['input_lever_left'] else 'RELEASED'}",
        f"Right Lever: {'PRESSED' if input_states['input_lever_right'] else 'RELEASED'}",
        f"Nose Poke: {'ACTIVE' if input_states['input_ir'] else 'INACTIVE'}",
        f"Water Port: {'ON' if input_states['input_port'] else 'OFF'}",
        f"Left Lever Light: {'ON' if input_states['led_lever_left'] else 'OFF'}",
        f"Nose Light: {'ON' if input_states['led_port'] else 'OFF'}",
        f"Right Lever Light: {'ON' if input_states['led_lever_right'] else 'OFF'}"
      ]

      # Adjust top position if banner is present
      top_y = 20
      if simulated_components:
        top_y = banner_height + 20

      for i, line in enumerate(state_text):
        if 'PRESSED' in line or 'ACTIVE' in line or 'ON' in line:
          color = (0, 255, 0)
        else:
          color = (255, 100, 100)

        line_surface = sim_font.render(line, True, color)
        line_rect = line_surface.get_rect(topleft=(20, top_y + i * 20))
        self.screen.blit(line_surface, line_rect)

    pygame.display.flip()

  def update(self):
    """Update device state and handle events"""
    events = pygame.event.get()

    for event in events:
      if event.type == pygame.QUIT:
        self._running = False
        return False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          self._running = False
          return False
        elif self.gpio.is_simulating_gpio():
          if event.key == pygame.K_1: # Left lever press
            self.gpio.simulate_input_lever_left(True)
          elif event.key == pygame.K_2: # Right lever press
            self.gpio.simulate_input_lever_right(True)
          elif event.key == pygame.K_3: # Nose poke entry
            self.gpio.simulate_input_ir(False)
          elif event.key == pygame.K_SPACE: # Nose poke entry (existing)
            self.gpio.simulate_input_ir(False)
          elif event.key == pygame.K_j: # Left lever light
            self.gpio.simulate_led_lever_left(True)
          elif event.key == pygame.K_k: # Nose light
            self.gpio.simulate_led_port(True)
          elif event.key == pygame.K_l: # Right lever light
            self.gpio.simulate_led_lever_right(True)
      elif event.type == pygame.KEYUP:
        if self.gpio.is_simulating_gpio():
          if event.key == pygame.K_1: # Left lever release
            self.gpio.simulate_input_lever_left(False)
          elif event.key == pygame.K_2: # Right lever release
            self.gpio.simulate_input_lever_right(False)
          elif event.key == pygame.K_3: # Nose poke exit
            self.gpio.simulate_input_ir(True)
          elif event.key == pygame.K_SPACE: # Nose poke exit (existing)
            self.gpio.simulate_input_ir(True)
          elif event.key == pygame.K_j: # Left lever light
            self.gpio.simulate_led_lever_left(False)
          elif event.key == pygame.K_k: # Nose light
            self.gpio.simulate_led_port(False)
          elif event.key == pygame.K_l: # Right lever light
            self.gpio.simulate_led_lever_right(False)

    self._update_input_states_and_statistics()

    if not self._experiment_started:
      self._render_waiting_screen()
    elif self._current_trial:
      if not self._current_trial.update(events):
        self._current_trial.on_exit()

        # Save trial data
        trial_data = self._current_trial.get_data()
        if trial_data and self._data:
          self._data.add_trial_data(self._current_trial.title, trial_data)
        log("Finished trial: " + self._current_trial.title, "info")

        # Send message about trial completion
        _device_message_queue.put(CommunicationMessageBuilder.trial_complete(self._current_trial.title, trial_data))

        if len(self._trials) > 0:
          self._current_trial = self._trials.pop(0)
          self._current_trial.on_enter()
          _device_message_queue.put(CommunicationMessageBuilder.trial_start(self._current_trial.title))
        else:
          if self._should_loop:
            # Reset trials for next loop by creating new trial instances
            self._trials = []
            for config in self._trial_configs:
              trial = self.experiment_processor.trial_factory.create_trial(
                config["type"],
                config["kwargs"],
                screen=self.screen,
                font=self.font,
                width=self.width,
                height=self.height,
                gpio=self.gpio,
                display=self.display,
                statistics=self.statistics_controller,
                config=self.config
              )
              self._trials.append(trial)

            self._current_trial = self._trials.pop(0)
            self._current_trial.on_enter()

            log("Timeline loop completed, starting next iteration", "info")
            _device_message_queue.put(CommunicationMessageBuilder.trial_start(self._current_trial.title))
          else:
            if self._data:
              # Save final statistics
              self._data.add_statistics(self.get_statistics())
              if not self._data.save():
                log("Failed to save data", "error")
              else:
                log("Data saved successfully", "success")

            self._experiment_started = False
            self._current_trial = None
            self._trial_configs = []
            self._trials = []
            self._should_loop = False
            log("Experiment completed, timeline cleared, returning to waiting state", "info")
            _device_message_queue.put(CommunicationMessageBuilder.experiment_status("completed"))

      if self._current_trial:
        self._current_trial.render()
        pygame.display.flip()

    return True

  def _update_input_states_and_statistics(self):
    """Update input states and track statistics based on changes"""
    current_input_states = self.gpio.get_gpio_state()
    self._input_states = current_input_states.copy()

    if self._experiment_started:
      # Check for changes and update statistics
      if not self._previous_input_states["input_ir"] and current_input_states["input_ir"]:
        self.statistics_controller.increment_stat("nose_pokes")
      if not self._previous_input_states["input_lever_left"] and current_input_states["input_lever_left"]:
        self.statistics_controller.increment_stat("left_lever_presses")
      if not self._previous_input_states["input_lever_right"] and current_input_states["input_lever_right"]:
        self.statistics_controller.increment_stat("right_lever_presses")
      if not self._previous_input_states["input_port"] and current_input_states["input_port"]:
        self.statistics_controller.increment_stat("water_deliveries")
    self._previous_input_states = current_input_states.copy()

  def get_statistics(self):
    """Get current statistics"""
    return self.statistics_controller.get_all_stats()

  def reset_statistics(self):
    """Reset all statistics to zero"""
    self.statistics_controller.reset_all_stats()

  def start_experiment(self, animal_id, trials, trial_configs, config=None, loop=False, experiment_file=None):
    """Start the experiment with a custom timeline"""
    if self._experiment_started:
      log("Experiment already running", "warning")
      return

    self.reset_statistics()
    log(f"Starting timeline experiment with animal ID: {animal_id}, {len(trials)} trials", "info")
    self._data = DataController(animal_id)

    if config is None:
        log("Warning: No experiment config provided, using default values", "warning")
        config = Config()

    # Store the experiment config
    self.experiment_config = config

    # Store the complete experiment file data if provided
    if experiment_file:
        self._data.add_experiment_file(experiment_file)

    # Set trials from timeline
    self._trials = trials.copy() # Store original trials\
    self._trial_configs = trial_configs.copy() # Store trial configs, reused for looped experiments
    self._should_loop = loop  # Set loop flag

    self._current_trial = self._trials.pop(0)
    self._current_trial.on_enter()
    self._experiment_started = True

    _device_message_queue.put(CommunicationMessageBuilder.experiment_status("started", self._current_trial.title))
    log("Timeline experiment started", "info")

  def stop_experiment(self):
    """Stop the current experiment"""
    if not self._experiment_started:
      log("No experiment running", "warning")
      return

    # Reset all output IO
    self.gpio.reset_all_outputs()
    self.display.clear_displays()

    # Stop the current experiment
    self._experiment_started = False
    self._current_trial = None
    self._trials = []

    if self._data:
      self._data.add_statistics(self.get_statistics())
      if not self._data.save():
        log("Failed to save data", "error")
      else:
        log("Data saved", "success")

    _device_message_queue.put(CommunicationMessageBuilder.experiment_status("stopped"))
    log("Experiment stopped", "info")

  async def _test_water_delivery(self, duration_ms=2000):
    try:
      self.gpio.set_input_port(True)
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.gpio.set_input_port(False)
    except Exception as e:
      self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not activate water delivery: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_water_delivery") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Test water delivery passed (duration: {duration_ms}ms)", "success")

  def test_water_delivery(self, duration_ms=2000):
    log(f"Testing water delivery for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_water_delivery", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_water_delivery(duration_ms))

  def _test_levers(self):
    # Step 2: Test that the left lever can be moved to 1.0
    log("Testing left lever", "start")
    log("Waiting for left lever input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self.gpio.get_gpio_state()
      if input_state["input_lever_left"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
        _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Left lever input timed out", "error")
        return

    if input_state["input_lever_left"] != True:
      self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Left lever did not move to 1.0", "error")
      return

    log("Left lever test passed", "success")

    # Step 3: Test that the right lever can be moved to 1.0
    running_input_test = True
    running_input_test_start_time = time.time()
    log("Testing right lever", "start")
    log("Waiting for right lever input...", "info")
    while running_input_test:
      input_state = self.gpio.get_gpio_state()
      if input_state["input_lever_right"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
        _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Right lever input timed out", "error")
        return

    if input_state["input_lever_right"] != True:
      self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Right lever did not move to 1.0", "error")
      return

    log("Right lever test passed", "success")
    if self.test_state_manager.get_test_state("test_levers") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_levers", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Levers test passed", "success")

  def test_levers(self):
    log("Testing levers", "start")
    self.test_state_manager.set_test_state("test_levers", TEST_STATES["RUNNING"])

    # Step 1: Test that both levers default to 0.0
    input_state = self.gpio.get_gpio_state()
    if input_state["input_lever_left"] != False:
      self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Left lever did not default to 0.0", "error")
      return

    if input_state["input_lever_right"] != False:
      self.test_state_manager.set_test_state("test_levers", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("Right lever did not default to 0.0", "error")
      return

    log("Levers defaulted to 0.0", "success")

    # Run the test in a separate thread
    lever_test_thread = threading.Thread(target=self._test_levers)
    lever_test_thread.start()

  def _test_ir(self):
    # Step 1: Test that the IR is broken
    log("Waiting for IR input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self.gpio.get_gpio_state()
      if input_state["input_ir"] == False:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self.test_state_manager.set_test_state("test_ir", TEST_STATES["FAILED"])
        _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
        log("Timed out while waiting for IR input", "error")
        return

    if input_state["input_ir"] != False:
      self.test_state_manager.set_test_state("test_ir", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log("No IR input detected", "error")
      return

    # Set test to passed
    if self.test_state_manager.get_test_state("test_ir") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_ir", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
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
      self.gpio.set_led_port(True)
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.gpio.set_led_port(False)
    except Exception as e:
      self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not control nose light: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_nose_light") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Nose light test passed (duration: {duration_ms}ms)", "success")

  def test_nose_light(self, duration_ms=2000):
    log(f"Testing nose light for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_nose_light", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_nose_light(duration_ms))

  async def _test_lever_lights(self, duration_ms=2000):
    try:
      # Turn on the lever lights
      self.gpio.set_led_lever_left(True)
      self.gpio.set_led_lever_right(True)
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.gpio.set_led_lever_left(False)
      self.gpio.set_led_lever_right(False)
    except Exception as e:
      self.test_state_manager.set_test_state("test_lever_lights", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not control lever lights: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_lever_lights") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_lever_lights", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Lever lights test passed (duration: {duration_ms}ms)", "success")

  def test_lever_lights(self, duration_ms=2000):
    log(f"Testing lever lights for {duration_ms}ms", "start")
    self.test_state_manager.set_test_state("test_lever_lights", TEST_STATES["RUNNING"])
    asyncio.create_task(self._test_lever_lights(duration_ms))

  async def _test_displays(self, duration_ms=2000):
    try:
      # Draw test pattern on both displays
      self.display.draw_test_pattern("both")
      await asyncio.sleep(duration_ms / 1000)  # Convert milliseconds to seconds
      self.display.clear_displays()
    except Exception as e:
      self.test_state_manager.set_test_state("test_displays", TEST_STATES["FAILED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
      log(f"Could not control displays: {str(e)}", "error")

    if self.test_state_manager.get_test_state("test_displays") == TEST_STATES["RUNNING"]:
      self.test_state_manager.set_test_state("test_displays", TEST_STATES["PASSED"])
      _device_message_queue.put(CommunicationMessageBuilder.test_state(self.test_state_manager.get_all_test_states()))
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
        self.test_water_delivery()
    elif command == "test_levers":
      self.test_levers()
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
        self.test_nose_light()
    elif command == "test_lever_lights":
      self.test_lever_lights()
    elif command.startswith("test_lever_lights"):
      # Parse duration from command: "test_lever_lights <duration_ms>"
      parts = command.split(" ")
      if len(parts) > 1:
        try:
          duration_ms = int(parts[1])
          self.test_lever_lights(duration_ms)
        except ValueError:
          log(f"Invalid duration for lever lights test: {parts[1]}", "error")
      else:
        self.test_lever_lights()
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
        self.test_displays()

  def cleanup(self):
    """Clean up resources before shutdown"""
    if self._experiment_started:
      self.stop_experiment()
    self._control_panel_connected = False
    pygame.quit()

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
      await asyncio.sleep(0.05)
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def send_state_message(websocket):
  """
  Sends the current state of the device to the control panel.
  """
  while True:
    try:
      state_data = CommunicationMessageBuilder.input_state(_device.gpio.get_gpio_state(), _device.version)
      await websocket.send(json.dumps(state_data))
      if _device._experiment_started:
        stats_data = CommunicationMessageBuilder.statistics(_device.get_statistics())
        await websocket.send(json.dumps(stats_data))
      await asyncio.sleep(0.05)
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def handle_connection(websocket, device: Device):
  """Handle a single websocket connection"""
  try:
    device._control_panel_connected = True

    message_sender_task = asyncio.create_task(send_queued_messages(websocket))
    state_sender_task = asyncio.create_task(send_state_message(websocket))

    async for message in websocket:
      # Handle incoming messages
      try:
        message_data = CommunicationMessageParser.parse_message(message)
        if message_data and "type" in message_data:
          await handle_json_message(websocket, device, message_data)
          continue

        command = message.strip()
        if CommunicationMessageParser.parse_test_command(command)[0] in TEST_COMMANDS:
          device.run_test(command)
        elif CommunicationMessageParser.parse_experiment_command(command)[0] in EXPERIMENT_COMMANDS:
          if command == "stop_experiment":
            device.stop_experiment()
          else:
            log(f"Unknown experiment command: {command}", "error")
        else:
          log(f"Unknown command: {command}", "error")
      except Exception as e:
        log(f"Error handling message: {str(e)}", "error")

    message_sender_task.cancel()
    state_sender_task.cancel()
    try:
      await asyncio.wait_for(asyncio.gather(message_sender_task, state_sender_task), timeout=1.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
      pass
  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    device._control_panel_connected = False
    device.reset_test_state()
    await websocket.close()

async def handle_json_message(websocket, device: Device, message_data: dict):
  """Handle JSON messages from the control panel"""
  message_type = message_data.get("type")
  if message_type == "experiment_upload":
    # Handle experiment upload
    experiment_data = message_data.get("data", {})
    success, message = device.experiment_processor.process_experiment_upload(experiment_data)
    response = CommunicationMessageBuilder.experiment_validation(success, message)
    await websocket.send(json.dumps(response))

    if success:
      log(f"Experiment uploaded successfully: {message}", "success")
    else:
      log(f"Experiment upload failed: {message}", "error")
  elif message_type == "start_experiment":
    # Handle experiment start
    animal_id = message_data.get("animal_id", "")
    if not animal_id:
      response = CommunicationMessageBuilder.experiment_error("Animal ID is required")
      await websocket.send(json.dumps(response))
      return

    success, message = device.experiment_processor.execute_experiment(animal_id)
    if success:
      response = CommunicationMessageBuilder.experiment_validation(success, message)
    else:
      response = CommunicationMessageBuilder.experiment_error(message)
    await websocket.send(json.dumps(response))

    if success:
      log(f"Experiment started: {message}", "success")
    else:
      log(f"Experiment failed: {message}", "error")
  else:
    log(f"Unknown JSON message type: {message_type}", "warning")

async def main_loop(device):
  """Main loop that runs both pygame and websocket communication"""
  log("Starting main loop", "info")
  server = await websockets.serve(
    lambda ws: handle_connection(ws, device),
    HOST,
    PORT
  )
  device._websocket_server = server

  try:
    while device._running:
      if not device.update():
        log("Initiating shutdown...", "info")
        break
      await asyncio.sleep(0)
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
          except (asyncio.TimeoutError, Exception):
            log("Error closing connection, connection may already be closed", "warning")

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

    set_message_queue(_device_message_queue)
    asyncio.run(main_loop(_device))
  except KeyboardInterrupt:
    log("Keyboard interrupt received", "info")
  except asyncio.TimeoutError:
    log("Main loop timed out", "error")
  except Exception as e:
    log(f"Error in main loop: {str(e)}", "error")
  finally:
    if _device:
      _device.cleanup()

if __name__ == "__main__":
  main()
