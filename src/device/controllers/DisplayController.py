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
    else:
      # Initialize simulation mode displays
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

  def _init_simulation(self):
    """Initialize dummy displays for simulation mode."""
    print("Initializing simulation mode displays...")
    self.display_left = DummyDisplay(128, 64)
    self.display_right = DummyDisplay(128, 64)
    print("Simulation mode displays initialized.")

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

  def draw_alternating_pattern(self, side="both", stripe_orientation="vertical"):
    """Draw circles using stripes with varying lengths to create circular appearance"""
    if side in ["left", "both"]:
      # Clear the display with black background
      self.draw_left.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

      # Circle parameters
      circle_center_x = self.width // 2
      circle_center_y = self.height // 2
      circle_radius = 25

      # Stripe parameters - ensure stripes cover full display
      num_stripes = 16  # Same number as current background
      stripe_width = self.width // num_stripes  # Calculate width to cover full display

      if stripe_orientation == "vertical":
        # Draw vertical stripes to create circle appearance
        for i in range(num_stripes):
          # Calculate x position for this stripe
          x = i * stripe_width

          # Calculate distance from center for this x position
          distance_from_center = abs(x - circle_center_x)

          # Calculate stripe length based on circle equation
          if distance_from_center <= circle_radius:
            # Use circle equation: y = sqrt(r^2 - x^2)
            # Stripe length is 2 * y (full height of circle at this x)
            stripe_length = 2 * int(math.sqrt(circle_radius**2 - distance_from_center**2))
          else:
            stripe_length = 0  # Outside circle, no stripe

          if stripe_length > 0:
            # Calculate y position to center the stripe
            y_start = circle_center_y - stripe_length // 2
            y_end = circle_center_y + stripe_length // 2

            # Ensure stripe stays within display bounds
            y_start = max(0, y_start)
            y_end = min(self.height, y_end)

            # Draw the stripe
            self.draw_left.rectangle((x, y_start, x + stripe_width - 1, y_end), outline=0, fill=1)
      else:  # horizontal
        # Draw horizontal stripes to create circle appearance
        for i in range(num_stripes):
          # Calculate y position for this stripe
          y = i * stripe_width

          # Calculate distance from center for this y position
          distance_from_center = abs(y - circle_center_y)

          # Calculate stripe length based on circle equation
          if distance_from_center <= circle_radius:
            # Use circle equation: x = sqrt(r^2 - y^2)
            # Stripe length is 2 * x (full width of circle at this y)
            stripe_length = 2 * int(math.sqrt(circle_radius**2 - distance_from_center**2))
          else:
            stripe_length = 0  # Outside circle, no stripe

          if stripe_length > 0:
            # Calculate x position to center the stripe
            x_start = circle_center_x - stripe_length // 2
            x_end = circle_center_x + stripe_length // 2

            # Ensure stripe stays within display bounds
            x_start = max(0, x_start)
            x_end = min(self.width, x_end)

            # Draw the stripe
            self.draw_left.rectangle((x_start, y, x_end, y + stripe_width - 1), outline=0, fill=1)

      self.display_left.image(self.image_left)
      self.display_left.show()

    if side in ["right", "both"]:
      # Clear the display with black background
      self.draw_right.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

      # Circle parameters
      circle_center_x = self.width // 2
      circle_center_y = self.height // 2
      circle_radius = 25

      # Stripe parameters - ensure stripes cover full display
      num_stripes = 16  # Same number as current background
      stripe_width = self.width // num_stripes  # Calculate width to cover full display

      if stripe_orientation == "vertical":
        # Draw vertical stripes to create circle appearance
        for i in range(num_stripes):
          # Calculate x position for this stripe
          x = i * stripe_width

          # Calculate distance from center for this x position
          distance_from_center = abs(x - circle_center_x)

          # Calculate stripe length based on circle equation
          if distance_from_center <= circle_radius:
            # Use circle equation: y = sqrt(r^2 - x^2)
            # Stripe length is 2 * y (full height of circle at this x)
            stripe_length = 2 * int(math.sqrt(circle_radius**2 - distance_from_center**2))
          else:
            stripe_length = 0  # Outside circle, no stripe

          if stripe_length > 0:
            # Calculate y position to center the stripe
            y_start = circle_center_y - stripe_length // 2
            y_end = circle_center_y + stripe_length // 2

            # Ensure stripe stays within display bounds
            y_start = max(0, y_start)
            y_end = min(self.height, y_end)

            # Draw the stripe
            self.draw_right.rectangle((x, y_start, x + stripe_width - 1, y_end), outline=0, fill=1)
      else:  # horizontal
        # Draw horizontal stripes to create circle appearance
        for i in range(num_stripes):
          # Calculate y position for this stripe
          y = i * stripe_width

          # Calculate distance from center for this y position
          distance_from_center = abs(y - circle_center_y)

          # Calculate stripe length based on circle equation
          if distance_from_center <= circle_radius:
            # Use circle equation: x = sqrt(r^2 - y^2)
            # Stripe length is 2 * x (full width of circle at this y)
            stripe_length = 2 * int(math.sqrt(circle_radius**2 - distance_from_center**2))
          else:
            stripe_length = 0  # Outside circle, no stripe

          if stripe_length > 0:
            # Calculate x position to center the stripe
            x_start = circle_center_x - stripe_length // 2
            x_end = circle_center_x + stripe_length // 2

            # Ensure stripe stays within display bounds
            x_start = max(0, x_start)
            x_end = min(self.width, x_end)

            # Draw the stripe
            self.draw_right.rectangle((x_start, y, x_end, y + stripe_width - 1), outline=0, fill=1)

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
