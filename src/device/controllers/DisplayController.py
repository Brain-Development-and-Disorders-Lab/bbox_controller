"""
Filename: DisplayController.py
Author: Matt Gaidica, Henry Burgess
Date: 2025-03-07
Description: Handles the display of information on the behavior box
License: MIT
"""

from PIL import Image, ImageDraw, ImageFont
import os
import pygame
import time

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

    def clear_displays(self):
        self.draw_left.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.draw_right.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.display_left.fill(0)
        self.display_right.fill(0)
        self.display_left.show()
        self.display_right.show()

    def start_fullscreen(self):
        # Initialize Pygame
        pygame.init()

        # Get the screen info
        screen_info = pygame.display.Info()

        # Set up fullscreen display
        screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h),
                                       pygame.FULLSCREEN)

        # Fill screen with black
        screen.fill((0, 0, 0))
        pygame.display.flip()

        # Wait for 5 seconds
        time.sleep(5)

        # Clean up
        pygame.quit()

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
