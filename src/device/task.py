import json
import multiprocessing

# Controllers
from controllers.DataController import DataController

# Trials
from trials import Stage1, Interval

# Other imports
from util import log

def run_task_process(animal_id, config_path):
  """Function that runs in the separate process"""
  import pygame

  # Initialize data controller
  data = DataController(animal_id)

  # Initialize pygame in the new process
  pygame.init()

  # Load config
  with open(config_path) as config_file:
    variables = json.load(config_file)["task"]
    data.add_task_data({"config": variables})

  # Setup screen
  screen_info = pygame.display.Info()
  screen = pygame.display.set_mode(
    (screen_info.current_w, screen_info.current_h),
    pygame.FULLSCREEN
  )
  screen.fill((0, 0, 0))

  # Setup trials
  trials = [
    Stage1(0, 0),
    Interval(0, 0),
  ]
  font = pygame.font.SysFont("Arial", 64)
  for trial in trials:
    trial.screen = screen
    trial.font = font
    trial.width = screen_info.current_w
    trial.height = screen_info.current_h

  # Run first screen
  current_trial = trials.pop(0)
  current_trial.on_enter()

  running = True
  try:
    while running:
      events = pygame.event.get()

      # Handle screen events
      if not current_trial.update(events):
        # Screen is complete, run next screen
        current_trial.on_exit()

        # Save screen data before moving to next screen
        trial_data = current_trial.get_data()
        if trial_data:
          data.add_trial_data(current_trial.title, trial_data)

        log("Finished trial: " + current_trial.title, "info")

        if len(trials) > 0:
          current_trial = trials.pop(0)
          current_trial.on_enter()
        else:
          running = False

      # Render
      current_trial.render()
      pygame.display.flip()

      # Cap frame rate
      pygame.time.wait(16)

  finally:
    pygame.quit()
    log("Experiment finished", "info")
    data.save()

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
