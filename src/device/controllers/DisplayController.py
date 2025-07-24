"""
Filename: DisplayController.py
Author: Matt Gaidica, Henry Burgess
Date: 2025-03-07
Description: Handles the display of information on the behavior box
License: MIT
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

try:
  from board import SCL, SDA
  import busio
  import adafruit_ssd1306
  SIMULATION_MODE = False
except (ImportError, NotImplementedError):
  print("Display interfaces not available - running in simulation mode")
  SIMULATION_MODE = True

class DisplayController:
  def __init__(self):
    self.width = 128
    self.height = 64

    # Create blank images for drawing
    self.image_left = Image.new("1", (self.width, self.height))
    self.image_right = Image.new("1", (self.width, self.height))

    # Create drawing objects
    self.draw_left = ImageDraw.Draw(self.image_left)
    self.draw_right = ImageDraw.Draw(self.image_right)

    if not SIMULATION_MODE:
      try:
        # Setup I2C
        i2c = busio.I2C(SCL, SDA)

        # Try to initialize each display independently
        self.display_left = self._init_display(i2c, 0x3C, "left")
        self.display_right = self._init_display(i2c, 0x3D, "right")
      except (ValueError, OSError) as e:
        print(f"Failed to initialize I2C bus: {e}")
        print("Switching to full simulation mode")
        self._init_simulation()

    # Load a font - modified for cross-platform compatibility
    try:
      # Try system fonts in different locations
      font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arial.ttf"  # Windows
      ]
      for path in font_paths:
        if os.path.exists(path):
          self.font = ImageFont.truetype(path, 16)
          break
      else:
        self.font = ImageFont.load_default()
    except:
      self.font = ImageFont.load_default()

  def _init_display(self, i2c, address, name):
    """Initialize a single display, return DummyDisplay if fails"""
    try:
      display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)
      print(f"Successfully initialized {name} display at address 0x{address:02X}")
      return display
    except (ValueError, OSError) as e:
      print(f"Failed to initialize {name} display at address 0x{address:02X}: {e}")
      print(f"Using simulation mode for {name} display")
      return DummyDisplay(128, 64)

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

  def draw_alternating_pattern(self, side="both"):
    """Draw horizontal alternating black and white lines with a circle of vertical lines"""
    if side in ["left", "both"]:
      # Clear the display
      self.draw_left.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

      # Draw 8 horizontal alternating black and white lines
      line_height = self.height // 16  # 16 total lines (8 black + 8 white)
      for i in range(16):
        y_start = i * line_height
        y_end = (i + 1) * line_height
        fill_color = 1 if i % 2 == 0 else 0  # Alternate between white (1) and black (0)
        self.draw_left.rectangle((0, y_start, self.width, y_end), outline=0, fill=fill_color)

      # Draw circle with vertical alternating lines at approximately 2/3 width
      circle_center_x = int(self.width * 2/3)  # Approximately 2/3 of display width
      circle_center_y = self.height // 2
      circle_radius = 15

      # Draw vertical lines in a circle pattern
      for angle in range(0, 360, 10):  # Every 10 degrees
        rad = angle * 3.14159 / 180
        x = circle_center_x + int(circle_radius * math.cos(rad))
        y = circle_center_y + int(circle_radius * math.sin(rad))

        # Alternate line color
        line_color = 1 if angle % 20 == 0 else 0

        # Draw vertical line segment
        line_length = 8
        y_start = max(0, y - line_length // 2)
        y_end = min(self.height, y + line_length // 2)
        self.draw_left.line((x, y_start, x, y_end), fill=line_color)

      self.display_left.image(self.image_left)
      self.display_left.show()

    if side in ["right", "both"]:
      # Clear the display
      self.draw_right.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

      # Draw 8 horizontal alternating black and white lines
      line_height = self.height // 16  # 16 total lines (8 black + 8 white)
      for i in range(16):
        y_start = i * line_height
        y_end = (i + 1) * line_height
        fill_color = 1 if i % 2 == 0 else 0  # Alternate between white (1) and black (0)
        self.draw_right.rectangle((0, y_start, self.width, y_end), outline=0, fill=fill_color)

      # Draw circle with vertical alternating lines at approximately 2/3 width
      circle_center_x = int(self.width * 2/3)  # Approximately 2/3 of display width
      circle_center_y = self.height // 2
      circle_radius = 15

      # Draw vertical lines in a circle pattern
      for angle in range(0, 360, 10):  # Every 10 degrees
        rad = angle * 3.14159 / 180
        x = circle_center_x + int(circle_radius * math.cos(rad))
        y = circle_center_y + int(circle_radius * math.sin(rad))

        # Alternate line color
        line_color = 1 if angle % 20 == 0 else 0

        # Draw vertical line segment
        line_length = 8
        y_start = max(0, y - line_length // 2)
        y_end = min(self.height, y + line_length // 2)
        self.draw_right.line((x, y_start, x, y_end), fill=line_color)

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
