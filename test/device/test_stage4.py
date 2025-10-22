#!/usr/bin/env python3
"""
Filename: test/device/test_stage4.py
Author: Henry Burgess
Date: 2025-01-27
Description: Test script to verify Stage4 correct lever press behavior
"""

import os
import time
import pygame

# Change working directory to the shared directory
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared'))

# Initialize pygame for font support
pygame.init()

from device.core.Trials import Stage4
from device.hardware.GPIOController import GPIOController
from device.utils.helpers import TrialOutcome

def test_stage4_correct_lever():
    """Test that Stage4 only rewards correct lever press"""
    print("Testing Stage4 correct lever behavior...")

    # Create IO controller in simulation mode
    gpio = GPIOController()

    # Create Stage4 trial
    trial = Stage4(gpio=gpio)

    # Mock screen and other required attributes
    trial.screen = None
    trial.width = 800
    trial.height = 600
    trial.font = None

    print("✓ Trial created")
    print(f"✓ Cue side: {trial.cue_side}")

    # Start the trial
    trial.on_enter()
    print("✓ Trial started")

    # Simulate nose port entry
    print("\n1. Simulating nose port entry...")
    gpio.simulate_input_ir(True)  # True means nose is IN (entry)

    # Update trial
    trial.update([])
    print(f"   Nose port entry: {trial.nose_port_entry}")
    print(f"   Visual cue active: {trial.visual_cue}")
    print(f"   Trial should continue: {trial.update([])}")

    # Test correct lever press
    print(f"\n2. Testing correct lever press ({trial.cue_side} side)...")
    if trial.cue_side == "left":
        gpio.simulate_input_lever_left(True)
    else:
        gpio.simulate_input_lever_right(True)

    # Update trial
    should_continue = trial.update([])
    print(f"   Reward triggered: {trial.reward_triggered}")
    print(f"   Trial should continue: {should_continue}")
    print(f"   Trial outcome: {trial.get_data().get('trial_outcome', 'Not set')}")

    assert trial.reward_triggered, "Reward should be triggered for correct lever"
    assert should_continue, "Trial should continue after correct lever press"
    print("✓ Correct lever press triggered reward!")

def test_stage4_wrong_lever():
    """Test that Stage4 ends trial immediately on wrong lever press"""
    print("\nTesting Stage4 wrong lever behavior...")

    # Create IO controller in simulation mode
    gpio = GPIOController()

    # Create Stage4 trial
    trial = Stage4(gpio=gpio)

    # Mock screen and other required attributes
    trial.screen = None
    trial.width = 800
    trial.height = 600
    trial.font = None

    print("✓ Trial created")
    print(f"✓ Cue side: {trial.cue_side}")

    # Start the trial
    trial.on_enter()
    print("✓ Trial started")

    # Simulate nose port entry
    print("\n1. Simulating nose port entry...")
    gpio.simulate_input_ir(True)  # True means nose is IN (entry)

    # Update trial
    trial.update([])
    print(f"   Nose port entry: {trial.nose_port_entry}")
    print(f"   Visual cue active: {trial.visual_cue}")

    # Test wrong lever press
    print(f"\n2. Testing wrong lever press (opposite of {trial.cue_side} side)...")
    if trial.cue_side == "left":
        gpio.simulate_input_lever_right(True)  # Wrong lever
    else:
        gpio.simulate_input_lever_left(True)  # Wrong lever

    # Update trial
    should_continue = trial.update([])
    print(f"   Reward triggered: {trial.reward_triggered}")
    print(f"   Trial should continue: {should_continue}")
    print(f"   Trial outcome: {trial.get_data().get('trial_outcome', 'Not set')}")
    print(f"   Error trial: {trial.is_error_trial}")
    print(f"   Error type: {getattr(trial, 'error_type', 'Not set')}")

    assert not trial.reward_triggered, "Reward should NOT be triggered for wrong lever"
    assert not should_continue, "Trial should end immediately on wrong lever press"
    assert trial.is_error_trial, "Trial should be marked as error trial"
    assert trial.get_data().get('trial_outcome') == TrialOutcome.FAILURE_WRONGLEVER, "Trial outcome should be FAILURE_WRONGLEVER"
    print("✓ Wrong lever press correctly ended trial!")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
