"""
Filename: device/hardware/DisplayController.py
Author: Matt Gaidica, Henry Burgess
Date: 2025-07-29
Description: Handles the display of information on the behavior box
License: MIT
"""

from device.hardware.constants import DISPLAY_ADDRESS_LEFT, DISPLAY_ADDRESS_RIGHT
from device.utils.logger import log

from PIL import Image, ImageDraw, ImageFont
import os
import math

try:
  from board import SCL, SDA
  import busio
  import adafruit_ssd1306
  SIMULATION_MODE = False
except (ImportError, NotImplementedError):
  log("Display interfaces not available, using simulated displays", "warning")
  SIMULATION_MODE = True

class DisplayController:
  def __init__(self):
    self._simulate_displays = SIMULATION_MODE

    if not self._simulate_displays:
      try:
        # Setup I2C
        i2c = busio.I2C(SCL, SDA)

        # Try to initialize each display independently
        self.display_left = self._init_display(i2c, DISPLAY_ADDRESS_LEFT, "left")
        self.display_right = self._init_display(i2c, DISPLAY_ADDRESS_RIGHT, "right")
      except (ValueError, OSError) as e:
        log(f"Failed to initialize I2C bus: {e}", "error")
        self._init_simulated_displays()
    else:
      self._init_simulated_displays()

    self.width = 128
    self.height = 64

    # Create blank images for drawing
    self.image_left = Image.new("1", (self.width, self.height))
    self.image_right = Image.new("1", (self.width, self.height))

    # Create drawing objects
    self.draw_left = ImageDraw.Draw(self.image_left)
    self.draw_right = ImageDraw.Draw(self.image_right)

    try:
      # Try system fonts in different locations
      font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux
        "/System/Library/Fonts/Helvetica.ttc", # macOS
        "C:/Windows/Fonts/arial.ttf" # Windows
      ]
      for path in font_paths:
        if os.path.exists(path):
          self.font = ImageFont.truetype(path, 16)
          break
      else:
        self.font = ImageFont.load_default()
    except:
      self.font = ImageFont.load_default()

  def is_simulating_displays(self):
    """Check if the displays are in simulation mode"""
    return self._simulate_displays

  def _init_display(self, i2c, address, name):
    """Initialize a single display, return DummyDisplay if fails"""
    try:
      display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)
      log(f"Successfully initialized {name} display at address 0x{address:02X}", "success")
      return display
    except (ValueError, OSError) as e:
      log(f"Failed to initialize {name} display at address 0x{address:02X}: {e}", "error")
      log(f"Using simulation mode for {name} display", "warning")
      return DummyDisplay(128, 64)

  def _init_simulated_displays(self):
    log("Initializing simulated displays...", "info")
    self.display_left = DummyDisplay(128, 64)
    self.display_right = DummyDisplay(128, 64)
    log("Simulated displays initialized successfully", "success")

  def draw_test_pattern(self, side="both"):
    if side in ["left", "both"]:
      self.draw_left.rectangle((0, 0, self.width, self.height), outline=1, fill=0)
      self.draw_left.text((5, 5), "Left Display", font=self.font, fill=1)
      self.draw_left.rectangle((20, 30, 108, 50), outline=1, fill=1)
      self.display_left.image(self.image_left)
      self.display_left.show()

    if side in ["right", "both"]:
      self.draw_right.rectangle((0, 0, self.width, self.height), outline=1, fill=0)
      self.draw_right.text((5, 5), "Right Display", font=self.font, fill=1)
      self.draw_right.ellipse((20, 30, 108, 50), outline=1, fill=1)
      self.display_right.image(self.image_right)
      self.display_right.show()

  def _draw_circle_stripes(self, draw_obj, orientation, circle_center_x, circle_center_y, circle_radius, num_stripes, stripe_width):
    """Helper method to draw circle stripes for either orientation"""
    for i in range(num_stripes):
      # Calculate position and distance from center
      pos = i * stripe_width
      distance_from_center = abs(pos - (circle_center_x if orientation == "vertical" else circle_center_y))

      # Calculate stripe length using circle equation
      if distance_from_center <= circle_radius:
        stripe_length = 2 * int(math.sqrt(circle_radius**2 - distance_from_center**2))
      else:
        continue  # Skip stripes outside circle

      if orientation == "vertical":
        # Draw vertical stripe
        y_start = circle_center_y - stripe_length // 2
        y_end = circle_center_y + stripe_length // 2
        y_start = max(0, y_start)
        y_end = min(self.height, y_end)
        draw_obj.rectangle((pos, y_start, pos + stripe_width - 1, y_end), outline=0, fill=1)
      else:
        # Draw horizontal stripe
        x_start = circle_center_x - stripe_length // 2
        x_end = circle_center_x + stripe_length // 2
        x_start = max(0, x_start)
        x_end = min(self.width, x_end)
        draw_obj.rectangle((x_start, pos, x_end, pos + stripe_width - 1), outline=0, fill=1)

  def draw_alternating_pattern(self, side="both", stripe_orientation="vertical"):
    """Draw circles using stripes with varying lengths to create circular appearance"""
    # Common parameters
    circle_center_x = self.width // 2
    circle_center_y = self.height // 2
    circle_radius = 25
    num_stripes = 24
    stripe_width = self.width // num_stripes

    if side in ["left", "both"]:
      self.draw_left.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
      self._draw_circle_stripes(self.draw_left, stripe_orientation, circle_center_x, circle_center_y, circle_radius, num_stripes, stripe_width)
      self.display_left.image(self.image_left)
      self.display_left.show()

    if side in ["right", "both"]:
      self.draw_right.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
      self._draw_circle_stripes(self.draw_right, stripe_orientation, circle_center_x, circle_center_y, circle_radius, num_stripes, stripe_width)
      self.display_right.image(self.image_right)
      self.display_right.show()

  def clear_displays(self):
    self.draw_left.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
    self.draw_right.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
    self.display_left.fill(0)
    self.display_right.fill(0)
    self.display_left.show()
    self.display_right.show()

class DummyDisplay:
  def __init__(self, width, height):
    self.width = width
    self.height = height

  def fill(self, color):
    pass

  def show(self):
    pass

  def image(self, img):
    pass
