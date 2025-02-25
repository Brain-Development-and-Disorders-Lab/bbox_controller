# I/O imports
import lcd_i2c as lcd

class OutputController:
  def __init__(self):
    self.leds = []
    self.display = []
    self.lcd = []
