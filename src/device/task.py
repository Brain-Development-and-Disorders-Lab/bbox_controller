import json
import time

# Controllers
from controllers.IOController import IOController

class Task():
  def __init__(self, animal_id=None):
    """
    Initializes the example task.
    """
    self.io = IOController()
    self.trials = []

    # Load the configuration file
    with open("config.json") as config_file:
        self.variables = json.load(config_file)["task"]

    if animal_id is None:
      raise ValueError("`animal_id` is required")

  def check_inputs(self):
    """
    Checks the inputs from the IOController.
    """
    input_states = self.io.get_input_states()
    print(input_states)

  def run(self):
    """
    Runs the example task.
    """
    import pygame

    # Check if pygame is already initialized
    if pygame.get_init():
      pygame.quit()

    # Initialize Pygame
    pygame.init()

    # Get the screen info
    screen_info = pygame.display.Info()

    # Set up fullscreen display
    screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h), pygame.FULLSCREEN)

    # Fill screen with black
    screen.fill((0, 0, 0))

    # Set up the font
    font_size = 72  # Large font size
    try:
      font = pygame.font.SysFont("Arial", font_size)
    except:
      font = pygame.font.Font(None, font_size)  # Fallback to default font

    # Create the text surface
    text = font.render("Test Experiment", True, (255, 255, 255))

    # Get the text rectangle and center it
    text_rect = text.get_rect(center=(screen_info.current_w/2, screen_info.current_h/2))

    # Draw the text
    screen.blit(text, text_rect)
    pygame.display.flip()

    # Get start time
    start_time = time.time()
    running = True

    try:
      while running:
        # Handle events
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            running = False
          elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
              running = False

        # Check if 30 seconds have passed
        if time.time() - start_time >= 30:
          running = False

        # Check inputs
        input_states = self.io.get_input_states()
        if input_states["right_lever"]:
          running = False

        pygame.time.delay(10)

    finally:
      # Ensure cleanup happens even if there's an error
      pygame.display.quit()
      pygame.quit()

if __name__ == "__main__":
  # Run the experiment from the command line
  experiment = Task("test_animal_0")
  experiment.run()
