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
from util import log

class TrialStage1(TrialBase):
  def __init__(self, width, height):
    super().__init__(width, height)
    self.title = "trial_stage_1"
    self.start_time = None

    # Trial state
    self.nose_port_light = False
    self.delivered_water = False
    self.visual_cue = False
    self.nose_port_entry = False
    self.lever_press = False
    self.trial_end = False

    # Trial events
    self.events = []

  def on_enter(self):
    self.start_time = pygame.time.get_ticks()

    # Setup trial
    self.nose_port_light = True
    self.display.clear_displays()
    self.display.draw_test_pattern()
    log("Trial started", "info")

  def on_exit(self):
    self.add_data("events", self.events)

  def update(self, events):
    # Handle any PyGame events
    for event in events:
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          return False
        if event.key == pygame.K_SPACE:
          log("Trial canceled", "info")
          self.add_data("trial_canceled", True)
          return False

    # Handle any IO events
    self.nose_port_entry = self.get_io().get_input_states()["nose_poke"]
    if self.nose_port_entry:
      self.events.append({
        "type": "nose_port_entry",
        "timestamp": pygame.time.get_ticks()
      })
      log("Nose port entry", "info")
    self.lever_press = self.get_io().get_input_states()["left_lever"] or self.get_io().get_input_states()["right_lever"]
    if self.get_io().get_input_states()["left_lever"] == True:
      self.events.append({
        "type": "left_lever_press",
        "timestamp": pygame.time.get_ticks()
      })
      log("Left lever press", "info")
    if self.get_io().get_input_states()["right_lever"] == True:
      self.events.append({
        "type": "right_lever_press",
        "timestamp": pygame.time.get_ticks()
      })
      log("Right lever press", "info")

    return True

  def render(self):
    # Deliver water if trial has started
    if self.delivered_water == False and pygame.time.get_ticks() - self.start_time > 500:
      self.get_io().set_water_port(True)
    else:
      log("Water delivered", "success")
      self.delivered_water = True
      self.get_io().set_water_port(False)

    if self.nose_port_entry:
      self.visual_cue = False
      self.nose_port_light = False

    # Update visual state
    if self.visual_cue:
      self.display.draw_test_pattern()
    else:
      self.display.clear_displays()

    # Update nose port light
