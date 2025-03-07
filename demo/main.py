# Imports
import logging
import pygame
from pygame.locals import *
import time
import threading


# Variables
# DISPLAY_FLAGS = pygame.FULLSCREEN
DISPLAY_FLAGS = 0
SYNC_INTERVAL = 1.0 # Seconds


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class StimulusManager:
  def __init__(self):
    # Logging
    self.logger = logging.getLogger(__name__)
    self.logger.info("Initializing StimulusManager")

    # Initialize pygame and synchronization thread
    pygame.init()
    self.last_sync_time = time.time()
    self.sync_thread = threading.Thread(target=self.send_sync_signal)

    # Get display information
    info = pygame.display.Info()
    self.screen_width, self.screen_height = info.current_w, info.current_h
    self.display = pygame.display.set_mode((self.screen_width, self.screen_height), DISPLAY_FLAGS)


  def send_sync_signal(self):
    if time.time() - self.last_sync_time > SYNC_INTERVAL:
      self.logger.info("Sync: {}".format(time.time()))
      self.last_sync_time = time.time()


  def draw_circle(self):
    pygame.draw.circle(self.display, (255, 255, 255), (self.screen_width / 2, self.screen_height / 2), 100)


  def clear_screen(self):
    self.logger.info("Clearing screen")
    self.display.fill((0, 0, 0))


  def handle_keyboard_events(self, event: pygame.event.Event):
    if event.key == pygame.K_ESCAPE:
      self.handle_quit()


  def handle_quit(self):
    self.sync_thread.join()
    pygame.quit()
    quit()


  def render(self):
    #  Render objects
    self.draw_circle()

    #  Update display
    pygame.display.update()

    # Send synchronization signal
    self.send_sync_signal()


  def run(self):
    # Start synchronization thread
    self.sync_thread.start()

    #  Main loop
    while True:
      # Handle pygame events
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.handle_quit()
        if event.type == pygame.KEYUP or event.type == pygame.KEYDOWN:
          self.handle_keyboard_events(event)

      # Main render loop
      self.render()


def main():
    manager = StimulusManager()
    manager.run()


if __name__ == "__main__":
    main()
