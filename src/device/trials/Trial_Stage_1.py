"""
Trial Stage 1: Nose port entry and lever press
Description: At the beginning of each trial, lit up the nose port light and deliver water.
  In the same time, randomly display the visual cue on one of the side screens.
  After the mouse pokes into the nose port and retrieves water (withdraw from the
  nose port), this trial ended and start the ITI. Turn off the visual cue and nose
  port light upon mouse enters the nose port. Record all events time, such as
  nose port entry, lever press, etc.
"""

import pygame
from trials.Trial_Base import TrialBase

class TrialStage1(TrialBase):
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "trial_stage_1"
    self.start_time = None

    # Trial state
    self.nose_port_light = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.lever_press = False
    self.trial_end = False

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

  def update(self, events):
    pass

  def render(self):
    pass
