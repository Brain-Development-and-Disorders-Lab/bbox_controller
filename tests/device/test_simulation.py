#!/usr/bin/env python3
"""
Filename: test/device/test_simulation.py
Author: Henry Burgess
Date: 2025-07-29
Description: Test script for simulation mode, tests the extended simulation functionality
License: MIT
"""

from device.hardware.GPIOController import GPIOController

def test_simulation():
    """Test the simulation mode functionality"""
    print("Testing simulation mode...")

    # Create IO controller (should be in simulation mode)
    gpio = GPIOController()

    # Check if we're in simulation mode
    assert hasattr(gpio, '_simulate_gpio') and gpio._simulate_gpio, "Should be running in simulation mode"
    print("✓ Running in simulation mode")

    # Test initial states
    initial_states = gpio.get_gpio_state()
    print(f"Initial states: {initial_states}")

    # Test left lever simulation
    print("\nTesting left lever simulation...")
    gpio.simulate_input_lever_left(True)
    states = gpio.get_gpio_state()
    assert states['input_lever_left'], "Left lever simulation should work"
    print("✓ Left lever simulation works")

    gpio.simulate_input_lever_left(False)
    states = gpio.get_gpio_state()
    assert not states['input_lever_left'], "Left lever release should work"
    print("✓ Left lever release works")

    # Test right lever simulation
    print("\nTesting right lever simulation...")
    gpio.simulate_input_lever_right(True)
    states = gpio.get_gpio_state()
    assert states['input_lever_right'], "Right lever simulation should work"
    print("✓ Right lever simulation works")

    gpio.simulate_input_lever_right(False)
    states = gpio.get_gpio_state()
    assert not states['input_lever_right'], "Right lever release should work"
    print("✓ Right lever release works")

    # Test nose poke simulation
    print("\nTesting nose poke simulation...")
    gpio.simulate_input_ir(True)
    states = gpio.get_gpio_state()
    assert states['input_ir'], "Nose poke simulation should work"
    print("✓ Nose poke simulation works")

    gpio.simulate_input_ir(False)
    states = gpio.get_gpio_state()
    assert not states['input_ir'], "Nose poke release should work"
    print("✓ Nose poke release works")

    # Test water port control
    print("\nTesting water port control...")
    gpio.set_input_port(True)
    states = gpio.get_gpio_state()
    assert states['input_port'], "Water port control should work"
    print("✓ Water port control works")

    gpio.set_input_port(False)
    states = gpio.get_gpio_state()
    assert not states['input_port'], "Water port release should work"
    print("✓ Water port release works")

    print("\n✓ All simulation tests passed!")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
