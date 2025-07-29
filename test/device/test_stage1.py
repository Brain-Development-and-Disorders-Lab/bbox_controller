#!/usr/bin/env python3
"""
Test script to demonstrate Stage1 nose port exit fix
This script shows that Stage1 now properly waits for nose port exit before ending
"""

import sys
import os
import time
import json
import pygame

# Change working directory to the shared directory
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'shared'))

# Initialize pygame for font support
pygame.init()

from device.core.trials import Stage1
from device.hardware.IOController import IOController
from device.utils.logger import log

def test_stage1_nose_port_exit():
    """Test that Stage1 properly waits for nose port exit"""
    print("Testing Stage1 nose port exit behavior...")

    # Create IO controller in simulation mode
    io = IOController()

    # Create Stage1 trial (config will be loaded automatically from current directory)
    trial = Stage1()
    trial.io = io

    # Mock screen and other required attributes
    trial.screen = None
    trial.width = 800
    trial.height = 600
    trial.font = None

    print("✓ Trial created")

    # Start the trial
    trial.on_enter()
    print("✓ Trial started")

    # Simulate nose port entry
    print("\n1. Simulating nose port entry...")
    io.simulate_nose_poke(False)  # False means nose is IN (entry)

    # Update trial
    trial.update([])
    print(f"   Nose port entry: {trial.nose_port_entry}")
    print(f"   Water delivery complete: {trial.water_delivery_complete}")
    print(f"   Nose port exit: {trial.nose_port_exit}")
    print(f"   Trial should continue: {trial.update([])}")

    # Wait for water delivery to complete
    print("\n2. Waiting for water delivery to complete...")
    time.sleep(2.1)  # Wait longer than valve_open duration

    # Update trial
    trial.update([])
    print(f"   Nose port entry: {trial.nose_port_entry}")
    print(f"   Water delivery complete: {trial.water_delivery_complete}")
    print(f"   Nose port exit: {trial.nose_port_exit}")
    print(f"   Trial should continue: {trial.update([])}")

    # Simulate nose port exit
    print("\n3. Simulating nose port exit...")
    io.simulate_nose_poke(True)  # True means nose is OUT (exit)

    # Update trial
    should_continue = trial.update([])
    print(f"   Nose port entry: {trial.nose_port_entry}")
    print(f"   Water delivery complete: {trial.water_delivery_complete}")
    print(f"   Nose port exit: {trial.nose_port_exit}")
    print(f"   Trial should continue: {should_continue}")

    assert not should_continue, "Trial should end after nose port exit"
    print("✓ Trial correctly ended after nose port exit!")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
