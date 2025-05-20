import json
import sys
import time

# Controllers
from controllers.IOController import IOController

# Other imports
from util import log

class Task():
  def __init__(self, animal_id=None):
    """
    Initializes the example task.
    """
    import pygame
    self.pygame = pygame

    # Store arguments
    self.animal_id = animal_id

    if animal_id is None:
      raise ValueError("`animal_id` is required")

    # Initialize controllers
    self.io = IOController()

    # Load the configuration file
    with open("config.json") as config_file:
        self.variables = json.load(config_file)["task"]

    # Set up the trial flow
    self.trials = [
      {
        "type": "splash",
        "duration": 5000,
      }
    ]

    # Trial state
    self.current_trial = None
    self.trial_start = 0
    self.trial_duration = 0
    self.trial_complete = True

  def check_inputs(self):
    """
    Checks the inputs from the IOController.
    """
    input_states = self.io.get_input_states()
    print(input_states)

  def run(self):
    if self.pygame.get_init():
      self.pygame.quit()
    self.pygame.init()

    # Setup the screen
    self.screen_info = self.pygame.display.Info()
    self.screen = self.pygame.display.set_mode((self.screen_info.current_w, self.screen_info.current_h), self.pygame.FULLSCREEN)
    self.screen.fill((0, 0, 0))

    # Launch the main loop
    running = True
    try:
      while running:
        # Handle events
        for event in self.pygame.event.get():
          if event.type == self.pygame.QUIT:
            running = False
          elif event.type == self.pygame.KEYDOWN:
            if event.key == self.pygame.K_ESCAPE:
              running = False

        if not self.trial_complete:
          # Update trial duration
          self.trial_duration = self.pygame.time.get_ticks() - self.trial_start
          self.update()

        # Handle a trial transition
        if self.trial_complete:
          self.on_trial_finish()

          # Start the next trial if others remain, else finish the experiment
          if len(self.trials) > 0:
            trial = self.trials.pop()
            self.run_trial(trial)
          else:
            log("All trials completed", "success")
            running = False

    finally:
      # Ensure cleanup happens even if there's an error
      self.pygame.display.quit()
      self.pygame.quit()
      self.on_experiment_finish()

  def run_trial(self, trial):
    # Reset the trial state
    log("Running trial: " + trial["type"], "info")
    self.trial_complete = False
    self.trial_start = self.pygame.time.get_ticks()
    self.current_trial = trial

    # Start the trial
    if (self.current_trial["type"] == "splash"):
      # Set up the font
      font_size = 64
      try:
        font = self.pygame.font.SysFont("Arial", font_size)
      except:
        font = self.pygame.font.Font(None, font_size)

      # Create the text surface
      text = font.render(self.animal_id, True, (255, 255, 255))

      # Get the text rectangle and center it
      text_rect = text.get_rect(center=(self.screen_info.current_w / 2, self.screen_info.current_h / 2))

      # Draw the text
      self.screen.blit(text, text_rect)
      self.pygame.display.flip()

  def update(self):
    """
    Standard update function to check the trial state.
    """
    if self.trial_complete:
      return

    # Update for each trial type
    if self.current_trial["type"] == "splash":
      # Check if the trial is still running
      if self.trial_duration >= self.current_trial["duration"]:
        log("Duration of trial has elapsed...", "info")
        self.trial_complete = True

  def on_trial_finish(self):
    """
    Called when the trial is finished.
    """
    log("Finished trial: " + self.current_trial["type"], "info")

  def on_experiment_finish(self):
    """
    Called when the task is finished.
    """
    log("Experiment finished", "info")
    sys.exit()

if __name__ == "__main__":
  # Run the experiment from the command line
  experiment = Task("test_animal_0")
  experiment.run()
