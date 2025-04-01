"""
Filename: IOController.py
Author: Matt Gaidica, Henry Burgess
Date: 2025-03-07
Description: Handles the input and output of the behavior box
License: MIT
"""

try:
  from gpiozero import Button, DigitalOutputDevice
  SIMULATION_MODE = False
except (ImportError, NotImplementedError):
  print("Hardware interfaces not available - running in simulation mode")
  SIMULATION_MODE = True

class IOController:
  def __init__(self):
    # Define GPIO pins
    self.PIN_LEVER_RIGHT = 23
    self.PIN_LEVER_LEFT = 24
    self.PIN_NOSE_POKE = 17
    self.PIN_WATER = 25

    if not SIMULATION_MODE:
      try:
        # Setup GPIO inputs using gpiozero (pull_up=True by default)
        self.lever_right = Button(self.PIN_LEVER_RIGHT)
        self.lever_left = Button(self.PIN_LEVER_LEFT)
        self.nose_poke = Button(self.PIN_NOSE_POKE)

        # Setup water port output
        self.water_port = DigitalOutputDevice(self.PIN_WATER, initial_value=False)

        self._simulated_inputs = False
        print("GPIO inputs and outputs initialized successfully")

      except Exception as e:
        print(f"Failed to initialize GPIO: {e}")
        print("Switching to simulation mode for GPIO")
        self._init_simulated_inputs()
    else:
      self._init_simulation()

  def _init_simulated_inputs(self):
    """Initialize just the input simulation"""
    self._simulated_inputs = True
    self._simulated_states = {
      "right_lever": False,
      "left_lever": False,
      "nose_poke": False,
      "water_port": False
    }

  def _init_simulation(self):
    """Initialize full simulation mode with dummy hardware"""
    self._init_simulated_inputs()

  def get_input_states(self):
    if not hasattr(self, "_simulated_inputs") or not self._simulated_inputs:
      return {
        "right_lever": self.lever_right.is_pressed,
        "left_lever": self.lever_left.is_pressed,
        "nose_poke": self.nose_poke.is_pressed,
        "water_port": self.water_port.value
      }
    else:
      return self._simulated_states

  def set_water_port(self, state):
    """Control water port state"""
    if not hasattr(self, "_simulated_inputs") or not self._simulated_inputs:
      self.water_port.value = state
    else:
      self._simulated_states["water_port"] = state

  def __del__(self):
    """Cleanup GPIO on object destruction"""
    if not SIMULATION_MODE and not hasattr(self, "_simulated_inputs"):
      try:
        lgpio.gpiochip_close(self.gpio_handle)
      except:
        pass
