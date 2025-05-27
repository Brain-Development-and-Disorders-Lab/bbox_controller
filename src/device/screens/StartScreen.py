"""
Initial screen shown when experiment starts
"""

import pygame
from screens.BaseScreen import BaseScreen

class StartScreen(BaseScreen):
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "start_screen"
    self.start_time = None

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    # Check if 2 seconds have passed
    if pygame.time.get_ticks() - self.start_time > 2000:
      self.add_data("waited_2_seconds", True)
      return False

    # Handle any events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
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
