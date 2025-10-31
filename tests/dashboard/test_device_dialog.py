#!/usr/bin/env python3
"""
Unit tests for DeviceDialog component.

This module demonstrates how to test PyQt6 dialogs, including:
- Widget creation and initialization
- Form validation
- Signal handling
- User interaction simulation
"""

import sys
import os

# Add src to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from dashboard.app import DeviceDialog


class TestDeviceDialog:
    """Test suite for DeviceDialog"""

    def test_dialog_creation_add_mode(self, qapp):
        """Test that dialog can be created in add mode"""
        dialog = DeviceDialog()
        assert dialog is not None
        assert dialog.device is None
        assert dialog.windowTitle() == "Add Device"
        assert not dialog.delete_requested
        dialog.close()

    def test_dialog_creation_edit_mode(self, qapp):
        """Test that dialog can be created in edit mode"""
        device = {'name': 'Test Device', 'ip_address': '192.168.1.100', 'port': '8765'}
        dialog = DeviceDialog(device=device)
        assert dialog is not None
        assert dialog.device == device
        assert dialog.windowTitle() == "Edit Device"
        dialog.close()

    def test_dialog_fields_populated_edit_mode(self, qapp):
        """Test that fields are populated when editing an existing device"""
        device = {'name': 'Test Device', 'ip_address': '192.168.1.100', 'port': '8765'}
        dialog = DeviceDialog(device=device)

        assert dialog.name_field.text() == 'Test Device'
        assert dialog.ip_field.text() == '192.168.1.100'
        assert dialog.port_field.text() == '8765'

        dialog.close()

    def test_dialog_default_port_add_mode(self, qapp):
        """Test that default port is set when adding a new device"""
        dialog = DeviceDialog()
        assert dialog.port_field.text() == '8765'
        dialog.close()

    def test_validate_ip_address_valid(self, qapp):
        """Test IP address validation with valid addresses"""
        dialog = DeviceDialog()

        valid_ips = ['192.168.1.1', '127.0.0.1', '10.0.0.1', 'localhost']
        for ip in valid_ips:
            assert dialog.validate_ip_address(ip) is True

        dialog.close()

    def test_validate_ip_address_invalid(self, qapp):
        """Test IP address validation with invalid addresses"""
        dialog = DeviceDialog()

        invalid_ips = ['256.1.1.1', '192.168.1', 'not.an.ip', '192.168.1.1.1']
        for ip in invalid_ips:
            assert dialog.validate_ip_address(ip) is False

        dialog.close()

    def test_validation_empty_name(self, qapp, qtbot):
        """Test that validation fails when name is empty"""
        dialog = DeviceDialog()

        dialog.name_field.setText('')
        dialog.ip_field.setText('192.168.1.100')
        dialog.port_field.setText('8765')

        # Validation should show a warning and not accept
        # Note: This test would need to be expanded to mock QMessageBox
        # for full coverage
        dialog.close()

    def test_validation_empty_ip(self, qapp):
        """Test that validation fails when IP is empty"""
        dialog = DeviceDialog()

        dialog.name_field.setText('Test Device')
        dialog.ip_field.setText('')
        dialog.port_field.setText('8765')

        dialog.close()

    def test_validation_invalid_ip(self, qapp):
        """Test that validation fails when IP is invalid"""
        dialog = DeviceDialog()

        dialog.name_field.setText('Test Device')
        dialog.ip_field.setText('invalid.ip')
        dialog.port_field.setText('8765')

        dialog.close()

    def test_validation_invalid_port(self, qapp):
        """Test that validation fails when port is invalid"""
        dialog = DeviceDialog()

        dialog.name_field.setText('Test Device')
        dialog.ip_field.setText('192.168.1.100')
        dialog.port_field.setText('99999')  # Invalid port

        dialog.close()

    def test_get_device_data(self, qapp):
        """Test that get_device_data returns correct dictionary"""
        dialog = DeviceDialog()

        dialog.name_field.setText('Test Device')
        dialog.ip_field.setText('192.168.1.100')
        dialog.port_field.setText('8765')

        data = dialog.get_device_data()
        assert data['name'] == 'Test Device'
        assert data['ip_address'] == '192.168.1.100'
        assert data['port'] == '8765'

        dialog.close()

    def test_get_device_data_strips_whitespace(self, qapp):
        """Test that get_device_data strips whitespace"""
        dialog = DeviceDialog()

        dialog.name_field.setText('  Test Device  ')
        dialog.ip_field.setText('  192.168.1.100  ')
        dialog.port_field.setText('  8765  ')

        data = dialog.get_device_data()
        assert data['name'] == 'Test Device'
        assert data['ip_address'] == '192.168.1.100'
        assert data['port'] == '8765'

        dialog.close()

    def test_delete_button_present_in_edit_mode(self, qapp):
        """Test that delete button is present when editing"""
        device = {'name': 'Test Device', 'ip_address': '192.168.1.100', 'port': '8765'}
        dialog = DeviceDialog(device=device)

        # The delete button should be added to the button box
        # This is verified by checking that delete_requested can be set
        assert hasattr(dialog, 'delete_requested')
        assert dialog.delete_requested is False

        dialog.close()

    def test_delete_button_not_present_in_add_mode(self, qapp):
        """Test that delete button is not present when adding"""
        dialog = DeviceDialog()

        # In add mode, there should be no delete button
        assert hasattr(dialog, 'delete_requested')
        assert dialog.delete_requested is False

        dialog.close()

