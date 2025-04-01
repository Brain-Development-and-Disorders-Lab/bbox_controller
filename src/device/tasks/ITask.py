# Controllers
from controllers import IOController

class ITask:
  def __init__(self):
      self.io = IOController()
      self.trials = []

  def check_inputs(self):
      raise NotImplementedError("Subclasses must implement the `check_inputs` method")

  def run(self):
      raise NotImplementedError("Subclasses must implement the `run` method")

