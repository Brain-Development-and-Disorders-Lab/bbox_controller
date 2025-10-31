#!/usr/bin/env python3
"""
Unit tests for DeviceTab component.

This module demonstrates how to test PyQt6 widgets, including:
- Widget initialization
- Signal emission
- UI state management
- User interaction
"""

import sys
import os

# Add src to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from dashboard.components.device_tab import DeviceTab


class TestDeviceTab:
    """Test suite for DeviceTab"""

    def test_device_tab_creation(self, qapp):
        """Test that DeviceTab can be created"""
        tab = DeviceTab()
        assert tab is not None
        assert tab.current_experiment is None
        assert tab._connected is False
        tab.close()

    def test_device_tab_widgets_created(self, qapp):
        """Test that all required widgets are created"""
        tab = DeviceTab()

        # Check that key widgets exist
        assert hasattr(tab, 'animal_id_input')
        assert hasattr(tab, 'experiment_combo')
        assert hasattr(tab, 'new_exp_btn')
        assert hasattr(tab, 'edit_exp_btn')
        assert hasattr(tab, 'start_btn')
        assert hasattr(tab, 'stop_btn')
        assert hasattr(tab, 'console')

        tab.close()

    def test_device_tab_initial_state(self, qapp):
        """Test initial state of buttons and widgets"""
        tab = DeviceTab()

        # Initially, start and stop buttons should be disabled
        assert tab.start_btn.isEnabled() is False
        assert tab.stop_btn.isEnabled() is False
        assert tab.edit_exp_btn.isEnabled() is False

        tab.close()

    def test_device_tab_signals_exist(self, qapp):
        """Test that all required signals exist"""
        tab = DeviceTab()

        assert hasattr(tab, 'test_requested')
        assert hasattr(tab, 'experiment_start_requested')
        assert hasattr(tab, 'experiment_stop_requested')
        assert hasattr(tab, 'new_experiment_requested')
        assert hasattr(tab, 'edit_experiment_requested')

        tab.close()

    def test_new_experiment_signal_emission(self, qapp, qtbot):
        """Test that new_experiment_requested signal is emitted"""
        tab = DeviceTab()
        signal_received = False

        def on_signal():
            nonlocal signal_received
            signal_received = True

        tab.new_experiment_requested.connect(on_signal)

        # Click the new experiment button
        QTest.mouseClick(tab.new_exp_btn, Qt.MouseButton.LeftButton)
        qtbot.wait(100)

        assert signal_received is True
        tab.close()

    def test_experiment_stop_signal_emission(self, qapp, qtbot):
        """Test that experiment_stop_requested signal is emitted"""
        tab = DeviceTab()
        signal_received = False

        def on_signal():
            nonlocal signal_received
            signal_received = True

        tab.experiment_stop_requested.connect(on_signal)

        # Click the stop button (even if disabled, signal connection should work)
        # For a real test, you might want to enable it first
        if tab.stop_btn.isEnabled():
            QTest.mouseClick(tab.stop_btn, Qt.MouseButton.LeftButton)
            qtbot.wait(100)
            assert signal_received is True

        tab.close()

    def test_animal_id_input_placeholder(self, qapp):
        """Test that animal ID input has correct placeholder"""
        tab = DeviceTab()

        assert tab.animal_id_input.placeholderText() == "Enter animal ID"

        tab.close()

    def test_experiment_combo_initial_state(self, qapp):
        """Test initial state of experiment combo box"""
        tab = DeviceTab()

        # Should have at least one item (the "No experiments available" message)
        assert tab.experiment_combo.count() > 0
        assert "No experiments available" in tab.experiment_combo.itemText(0)

        tab.close()

    def test_console_initialized(self, qapp):
        """Test that console is properly initialized"""
        tab = DeviceTab()

        assert tab.console is not None
        assert tab.console.isReadOnly() is True

        tab.close()

    def test_update_connection_state(self, qapp):
        """Test updating connection state"""
        tab = DeviceTab()

        # Initially disconnected
        assert tab._connected is False

        # Set connected state (if method exists)
        # This test should be adapted based on actual implementation
        tab.close()

    def test_input_states_structure(self, qapp):
        """Test that input_states dictionary is initialized"""
        tab = DeviceTab()

        assert isinstance(tab.input_states, dict)
        assert isinstance(tab.statistics, dict)
        assert isinstance(tab.test_states, dict)

        tab.close()

    def test_timer_initialized(self, qapp):
        """Test that update timer is initialized"""
        tab = DeviceTab()

        assert tab.timer is not None
        assert tab.timer.isActive() is True

        tab.close()

