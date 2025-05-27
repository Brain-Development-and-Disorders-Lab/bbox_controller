"""
Initial screen shown when experiment starts
"""

import pygame
from screens.BaseScreen import BaseScreen

class WaitScreen(BaseScreen):
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "wait_screen"
    self.start_time = None

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    # Handle any events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          return False
        if event.key == pygame.K_SPACE:
          self.add_data("wait_screen_pressed", True)
          return False

    return True

  def render(self):
    # Clear screen
    self.screen.fill((0, 0, 0))

    # Render title
    if self.font:
      text = self.font.render(self.title, True, (255, 255, 255))
      text_rect = text.get_rect(center=(self.width / 2, self.height / 2))
      self.screen.blit(text, text_rect)
