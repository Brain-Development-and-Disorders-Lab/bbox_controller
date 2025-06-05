import json
import multiprocessing

# Controllers
from controllers.DataController import DataController

# Trials
from trials import Interval, Stage1, Stage2, Stage3

# Other imports
from util import log

def run_experiment_process(animal_id, config_path, message_queue):
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
    Stage1(),
    Interval(),
    Stage2(),
    Interval(),
    Stage3(),
  ]
  font = pygame.font.SysFont("Arial", 64)
  for trial in trials:
    trial.screen = screen
    trial.font = font
    trial.width = screen_info.current_w
    trial.height = screen_info.current_h
    trial.message_queue = message_queue

  # Run first screen
  current_trial = trials.pop(0)
  current_trial.on_enter()

  # Send initial message that task has started
  message_queue.put({
    "type": "task_status",
    "data": {
      "status": "started",
      "trial": current_trial.title
    }
  })

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

        # Send message about trial completion
        message_queue.put({
          "type": "trial_complete",
          "data": {
            "trial": current_trial.title,
            "data": trial_data
          }
        })

        if len(trials) > 0:
          current_trial = trials.pop(0)
          current_trial.on_enter()

          # Send message about new trial starting
          message_queue.put({
            "type": "trial_start",
            "data": {
              "trial": current_trial.title
            }
          })
        else:
          running = False
          # Send message that task is complete
          message_queue.put({
            "type": "task_status",
            "data": {
              "status": "completed"
            }
          })

      # Render
      current_trial.render()
      pygame.display.flip()

      # Cap frame rate
      pygame.time.wait(16)

  finally:
    pygame.quit()
    log("Experiment finished", "info")
    data.save()

class Experiment:
  def __init__(self, animal_id=None, message_queue=None):
    """Initialize the experiment"""
    self.animal_id = animal_id
    if animal_id is None:
      raise ValueError("`animal_id` is required")

    self.process = None
    self.config_path = "config.json"  # Could be passed as parameter
    self.message_queue = message_queue

  def run(self):
    """Start the experiment in a new process"""
    if self.process and self.process.is_alive():
      return

    # Create and start the process
    self.process = multiprocessing.Process(
      target=run_experiment_process,
      args=(self.animal_id, self.config_path, self.message_queue)
    )
    self.process.start()

  def stop(self):
    """Stop the experiment process"""
    if self.process and self.process.is_alive():
      # Send message that experiment is being stopped
      if self.message_queue:
        self.message_queue.put({
          "type": "experiment_status",
          "data": {
            "status": "stopped"
          }
        })

      self.process.terminate()
      self.process.join(timeout=1.0)
      self.process = None
