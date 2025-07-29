#!/usr/bin/env python3
"""
Filename: test/device/test_simulation.py
Author: Henry Burgess
Date: 2025-07-29
Description: Test script for simulation mode, tests the extended simulation functionality
License: MIT
"""

from device.hardware.IOController import IOController

def test_simulation():
    """Test the simulation mode functionality"""
    print("Testing simulation mode...")

    # Create IO controller (should be in simulation mode)
    io = IOController()

    # Check if we're in simulation mode
    assert hasattr(io, '_simulated_inputs') and io._simulated_inputs, "Should be running in simulation mode"
    print("✓ Running in simulation mode")

    # Test initial states
    initial_states = io.get_input_states()
    print(f"Initial states: {initial_states}")

    # Test left lever simulation
    print("\nTesting left lever simulation...")
    io.simulate_left_lever(True)
    states = io.get_input_states()
    assert states['left_lever'], "Left lever simulation should work"
    print("✓ Left lever simulation works")

    io.simulate_left_lever(False)
    states = io.get_input_states()
    assert not states['left_lever'], "Left lever release should work"
    print("✓ Left lever release works")

    # Test right lever simulation
    print("\nTesting right lever simulation...")
    io.simulate_right_lever(True)
    states = io.get_input_states()
    assert states['right_lever'], "Right lever simulation should work"
    print("✓ Right lever simulation works")

    io.simulate_right_lever(False)
    states = io.get_input_states()
    assert not states['right_lever'], "Right lever release should work"
    print("✓ Right lever release works")

    # Test nose poke simulation
    print("\nTesting nose poke simulation...")
    io.simulate_nose_poke(True)
    states = io.get_input_states()
    assert states['nose_poke'], "Nose poke simulation should work"
    print("✓ Nose poke simulation works")

    io.simulate_nose_poke(False)
    states = io.get_input_states()
    assert not states['nose_poke'], "Nose poke release should work"
    print("✓ Nose poke release works")

    # Test water port control
    print("\nTesting water port control...")
    io.set_water_port(True)
    states = io.get_input_states()
    assert states['water_port'], "Water port control should work"
    print("✓ Water port control works")

    io.set_water_port(False)
    states = io.get_input_states()
    assert not states['water_port'], "Water port release should work"
    print("✓ Water port release works")

    print("\n✓ All simulation tests passed!")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
