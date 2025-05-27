import json
import multiprocessing

# Controllers
from controllers.IOController import IOController

# Screens
from screens.StartScreen import StartScreen
from screens.WaitScreen import WaitScreen

# Other imports
from util import log

def run_task_process(animal_id, config_path):
  """Function that runs in the separate process"""
  import pygame

  # Initialize pygame in the new process
  pygame.init()

  # Load config
  with open(config_path) as config_file:
    variables = json.load(config_file)["task"]

  # Setup screen
  screen_info = pygame.display.Info()
  screen = pygame.display.set_mode(
    (screen_info.current_w, screen_info.current_h),
    pygame.FULLSCREEN
  )
  screen.fill((0, 0, 0))

  # Setup screens
  screens = [
    StartScreen(0, 0),
    WaitScreen(0, 0)
  ]
  font = pygame.font.SysFont("Arial", 64)
  for s in screens:
    s.screen = screen
    s.font = font
    s.width = screen_info.current_w
    s.height = screen_info.current_h

  # Run first screen
  current_screen = screens.pop(0)
  current_screen.on_enter()

  running = True
  try:
    while running:
      events = pygame.event.get()

      # Handle screen events
      if not current_screen.update(events):
        # Screen is complete, run next screen
        current_screen.on_exit()
        log("Finished screen: " + current_screen.title, "info")

        if len(screens) > 0:
          current_screen = screens.pop(0)
          current_screen.on_enter()
        else:
          running = False

      # Render
      current_screen.render()
      pygame.display.flip()

      # Cap frame rate
      pygame.time.wait(16)

  finally:
    pygame.quit()
    log("Experiment finished", "info")

class Task:
  def __init__(self, animal_id=None):
    """Initialize the task"""
    self.animal_id = animal_id
    if animal_id is None:
      raise ValueError("`animal_id` is required")

    self.process = None
    self.config_path = "config.json"  # Could be passed as parameter

  def run(self):
    """Start the task in a new process"""
    if self.process and self.process.is_alive():
      return

    # Create and start the process
    self.process = multiprocessing.Process(
      target=run_task_process,
      args=(self.animal_id, self.config_path)
    )
    self.process.start()

  def stop(self):
    """Stop the task process"""
    if self.process and self.process.is_alive():
      self.process.terminate()
      self.process.join(timeout=1.0)
      self.process = None
