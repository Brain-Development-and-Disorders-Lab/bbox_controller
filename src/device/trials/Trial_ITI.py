"""
Stage ITI: Inter-trial interval
Description: After each trial, the mouse is given an ITI of variable duration.
"""

import pygame
from trials.Trial_Base import TrialBase

class TrialITI(TrialBase):
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "trial_iti"
    self.start_time = None
    self.iti_duration = 1000

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    # Check if the ITI duration has passed
    if pygame.time.get_ticks() - self.start_time > self.iti_duration:
      self.add_data("trial_iti_completed", True)
      return False

    # Handle any events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          return False
        if event.key == pygame.K_SPACE:
          self.add_data("trial_iti_canceled", True)
          return False

    return True

  def render(self):
    # Clear screen
    self.screen.fill((0, 0, 0))
