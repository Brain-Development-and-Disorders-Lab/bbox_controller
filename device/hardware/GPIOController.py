"""
Filename: device/hardware/GPIOController.py
Author: Matt Gaidica, Henry Burgess
Date: 2025-07-29
Description: Handles the input and output of the behavior box
License: MIT
"""

from device.hardware.constants import LED_LEVER_LEFT, LED_LEVER_RIGHT, LED_PORT, INPUT_PORT, INPUT_IR, INPUT_LEVER_LEFT, INPUT_LEVER_RIGHT
from device.utils.logger import log

try:
  from gpiozero import Button, DigitalOutputDevice
  SIMULATION_MODE = False
except (ImportError, NotImplementedError):
  log("GPIO not available, using simulated GPIO", "warning")
  SIMULATION_MODE = True

class GPIOController:
  def __init__(self):
    self._simulate_gpio = SIMULATION_MODE

    if not self._simulate_gpio:
      try:
        # Setup GPIO inputs using gpiozero (initial_value=True by default)
        self.input_lever_left = Button(INPUT_LEVER_LEFT)
        self.input_lever_right = Button(INPUT_LEVER_RIGHT)
        self.input_ir = Button(INPUT_IR, pull_up=False)
        self.input_port = DigitalOutputDevice(INPUT_PORT, initial_value=False)

        # Setup LED outputs
        self.led_lever_left = DigitalOutputDevice(LED_LEVER_LEFT, initial_value=False)
        self.led_lever_right = DigitalOutputDevice(LED_LEVER_RIGHT, initial_value=False)
        self.led_port = DigitalOutputDevice(LED_PORT, initial_value=False)

        self._gpio_state = {
          "input_lever_left": self.input_lever_left.is_pressed,
          "input_lever_right": self.input_lever_right.is_pressed,
          "input_ir": self.input_ir.value,
          "input_port": self.input_port.value,
          "led_port": self.led_port.value,
          "led_lever_left": self.led_lever_left.value,
          "led_lever_right": self.led_lever_right.value
        }
        log("GPIO initialized successfully", "success")
      except Exception as e:
        log(f"Failed to initialize GPIO: {e}", "error")
        self._init_simulated_gpio()
    else:
      self._init_simulated_gpio()

  def is_simulating_gpio(self):
    """Check if the GPIO is in simulation mode"""
    return self._simulate_gpio

  def _init_simulated_gpio(self):
    log("Initializing simulated GPIO...", "info")
    self._simulate_gpio = True
    self._gpio_state = {
      "input_lever_left": False,
      "input_lever_right": False,
      "input_ir": False,
      "input_port": False,
      "led_port": False,
      "led_lever_left": False,
      "led_lever_right": False
    }
    log("Simulated GPIO initialized successfully", "success")

  def _update_gpio_state(self):
    """Update the GPIO state"""
    if not self._simulate_gpio:
      self._gpio_state = {
        "input_lever_left": self.input_lever_left.is_pressed,
        "input_lever_right": self.input_lever_right.is_pressed,
        "input_ir": self.input_ir.value,
        "input_port": self.input_port.value,
        "led_port": self.led_port.value,
        "led_lever_left": self.led_lever_left.value,
        "led_lever_right": self.led_lever_right.value
      }

  def get_gpio_state(self):
    """Get the GPIO state"""
    self._update_gpio_state()
    return self._gpio_state

  def set_input_port(self, state):
    """Control water port state"""
    self._gpio_state["input_port"] = state
    if not self._simulate_gpio:
      self.input_port.value = state

  def set_led_port(self, state):
    """Control nose port light LED state"""
    self._gpio_state["led_port"] = state
    if not self._simulate_gpio:
      self.led_port.value = state

  def set_led_lever_left(self, state):
    """Control left lever light LED state"""
    self._gpio_state["led_lever_left"] = state
    if not self._simulate_gpio:
      self.led_lever_left.value = state

  def set_led_lever_right(self, state):
    """Control right lever light LED state"""
    self._gpio_state["led_lever_right"] = state
    if not self._simulate_gpio:
      self.led_lever_right.value = state

  def simulate_input_lever_left(self, state):
    """Simulate left lever press/release"""
    if self._simulate_gpio:
      self._gpio_state["input_lever_left"] = state

  def simulate_input_lever_right(self, state):
    """Simulate right lever press/release"""
    if self._simulate_gpio:
      self._gpio_state["input_lever_right"] = state

  def simulate_input_ir(self, state):
    """Simulate nose poke entry/exit"""
    if self._simulate_gpio:
      self._gpio_state["input_ir"] = state

  def simulate_led_port(self, state):
    """Simulate nose port LED state"""
    if self._simulate_gpio:
      self._gpio_state["led_port"] = state

  def simulate_led_lever_left(self, state):
    """Simulate left lever LED state"""
    if self._simulate_gpio:
      self._gpio_state["led_lever_left"] = state

  def simulate_led_lever_right(self, state):
    """Simulate right lever LED state"""
    if self._simulate_gpio:
      self._gpio_state["led_lever_right"] = state

  def reset_all_outputs(self):
    """Reset all GPIO devices to off state"""
    self.set_input_port(False)
    self.set_led_port(False)
    self.set_led_lever_left(False)
    self.set_led_lever_right(False)

  def __del__(self):
    """Cleanup GPIO on object destruction"""
    if not self._simulate_gpio:
      try:
        lgpio.gpiochip_close(self.gpio_handle)
      except:
        pass
