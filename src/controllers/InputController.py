# I/O imports
import gpiozero as gpio

class InputController:
  def __init__(self):
    self.buttons = []
    self.switches = []
    self.sensors = []
