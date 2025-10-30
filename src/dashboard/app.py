#!/usr/bin/env python3

import sys
import os
import hashlib
from datetime import datetime
import json
import socket
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHeaderView,
    QTableWidgetItem,
    QPushButton,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6 import uic

from dashboard.core.connection_manager import DeviceConnectionManager
from dashboard.components.device_tab import DeviceTab
from dashboard.components.sync_dialog import SyncProgressDialog
from dashboard.components.experiment_editor import ExperimentEditor
from shared.managers import ExperimentManager, CommunicationMessageBuilder
from shared.constants import TEST_STATES


class DeviceDialog(QDialog):
    """Dialog for adding or editing a device"""
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.device = device
        self.delete_requested = False
        self.setWindowTitle("Add Device" if device is None else "Edit Device")
        self.setModal(True)

        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )

        layout = QFormLayout()

        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("e.g., Device 1")
        if device:
            self.name_field.setText(device.get('name', ''))
        layout.addRow("Device Name:", self.name_field)

        self.ip_field = QLineEdit()
        self.ip_field.setPlaceholderText("e.g., 192.168.1.100")
        if device:
            self.ip_field.setText(device.get('ip_address', ''))
        layout.addRow("IP Address:", self.ip_field)

        self.port_field = QLineEdit()
        self.port_field.setPlaceholderText("e.g., 8765")
        if device:
            self.port_field.setText(str(device.get('port', '8765')))
        else:
            self.port_field.setText('8765')
        layout.addRow("Port:", self.port_field)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        if device:
            delete_btn = buttons.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_btn.clicked.connect(self.delete_device)

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)

    def validate_ip_address(self, ip):
        """Validate IP address format"""
        if ip.lower() == "localhost":
            return True
        try:
            socket.inet_aton(ip)
            return True
        except OSError:
            return False

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        name = self.name_field.text().strip()
        ip = self.ip_field.text().strip()
        port = self.port_field.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Device name cannot be empty.")
            return

        if not ip:
            QMessageBox.warning(self, "Invalid Input", "IP address cannot be empty.")
            return

        if not self.validate_ip_address(ip):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid IP address (e.g., 192.168.1.100)")
            return

        if not port:
            QMessageBox.warning(self, "Invalid Input", "Port cannot be empty.")
            return

        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Port must be a number between 1 and 65535.")
            return

        self.accept()

    def get_device_data(self):
        return {
            'name': self.name_field.text().strip(),
            'ip_address': self.ip_field.text().strip(),
            'port': self.port_field.text().strip()
        }

    def delete_device(self):
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f"Are you sure you want to remove device '{self.device['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested = True
            self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = os.path.join(os.path.dirname(__file__), 'ui', 'form.ui')
        uic.loadUi(ui_file, self)

        self.destroyed.connect(self._on_destroyed)

        self.devices_file = os.path.join(
            os.path.dirname(__file__),
            'config',
            'devices.json'
        )
        self.devices = []
        self.connection_managers = {}  # device_name -> DeviceConnectionManager
        self.device_tabs = {}  # device_name -> DeviceTab

        # Store device info widgets and buttons
        self.device_connect_btn = None
        self.device_disconnect_btn = None
        self.device_sync_btn = None
        self.current_device_name = None

        self.setup_devices_table()
        self.addDeviceButton.clicked.connect(self.add_device)

        self.deviceInfoBox.setStyleSheet("""
            QGroupBox {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 0px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-size: 13pt;
                font-weight: bold;
                color: #333333;
            }
        """)

        self.deviceInfoLayout.setContentsMargins(10, 5, 10, 10)
        self.deviceInfoBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if hasattr(self, 'verticalSpacer'):
            self.verticalSpacer.changeSize(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.rightPanel.currentChanged.connect(self.on_tab_changed)
        self.load_devices()

    def setup_devices_table(self):
        """Configure the devices table with proper columns and styling"""
        headers = ['Name', 'Status', '']
        self.devicesTable.setColumnCount(len(headers))
        self.devicesTable.setHorizontalHeaderLabels(headers)

        header = self.devicesTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setDefaultSectionSize(100)
        self.devicesTable.setColumnWidth(2, 80)

        self.devicesTable.selectionModel().selectionChanged.connect(self.on_device_selection_changed)

        self.device_to_tab = {}

        self.devicesTable.setAlternatingRowColors(True)
        self.devicesTable.setShowGrid(False)
        self.devicesTable.verticalHeader().setVisible(False)

        self.devicesTable.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #d0d0d0;
                font-weight: bold;
            }
        """)

    def load_devices(self):
        """Load devices from file"""
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r') as f:
                    loaded_devices = json.load(f)
                    # Ensure all devices start with 'Disconnected' status
                    self.devices = []
                    for device in loaded_devices:
                        device['status'] = 'Disconnected'
                        self.devices.append(device)
            except (json.JSONDecodeError, IOError):
                self.devices = []

        self.update_devices_table()
        self.update_tabs()

    def save_devices(self):
        """Save devices to file"""
        try:
            # Remove 'status' from each device before saving since it should always start as 'Disconnected'
            devices_to_save = []
            for device in self.devices:
                device_copy = device.copy()
                if 'status' in device_copy:
                    del device_copy['status']
                devices_to_save.append(device_copy)

            with open(self.devices_file, 'w') as f:
                json.dump(devices_to_save, f, indent=2)
        except IOError:
            QMessageBox.warning(self, "Error", "Failed to save devices configuration.")

    def add_device(self):
        """Show dialog to add a new device"""
        dialog = DeviceDialog(self)
        if dialog.exec():
            device_data = dialog.get_device_data()

            device = {
                'name': device_data['name'],
                'ip_address': device_data['ip_address'],
                'port': device_data.get('port', '8765'),
                'status': 'Disconnected'  # Only in memory, not saved to file
            }
            self.devices.append(device)
            self.save_devices()
            self.update_devices_table()
            self.update_tabs()

    def edit_device(self, index):
        """Show dialog to edit a device"""
        device = self.devices[index]
        dialog = DeviceDialog(self, device=device)
        if dialog.exec():
            if dialog.delete_requested:
                device_name = self.devices[index]['name']

                if device_name in self.connection_managers:
                    try:
                        self.connection_managers[device_name].disconnect()
                    except Exception:
                        pass
                    del self.connection_managers[device_name]

                if device_name in self.device_tabs:
                    del self.device_tabs[device_name]

                self.devices.pop(index)
                self.save_devices()
                self.update_devices_table()
                self.update_tabs()
                return

            device_data = dialog.get_device_data()
            device['name'] = device_data['name']
            device['ip_address'] = device_data['ip_address']
            self.save_devices()
            self.update_devices_table()
            self.update_tabs()

    def update_devices_table(self):
        """Update the devices table with current devices"""
        self.devicesTable.setRowCount(len(self.devices))

        for row, device in enumerate(self.devices):
            name_item = QTableWidgetItem(device['name'])
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.devicesTable.setItem(row, 0, name_item)

            status_item = QTableWidgetItem(device.get('status', 'Disconnected'))
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            status_text = status_item.text()

            if status_text == "Connected":
                status_item.setForeground(QColor("#00AA00"))
            else:
                status_item.setForeground(QColor("#AA0000"))
            self.devicesTable.setItem(row, 1, status_item)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, idx=row: self.edit_device(idx))
            self.devicesTable.setCellWidget(row, 2, edit_btn)
            self.devicesTable.setRowHeight(row, 40)

        if len(self.devices) > 0:
            self.devicesTable.blockSignals(True)
            self.devicesTable.selectRow(0)
            self.devicesTable.blockSignals(False)

        self.update_device_info()

    def on_device_selection_changed(self):
        """Handle device selection changes in the table"""
        self.update_device_info()

        # Switch to corresponding tab
        selected_row = self.devicesTable.currentRow()
        if 0 <= selected_row < len(self.devices):
            device_name = self.devices[selected_row]['name']
            for i in range(self.rightPanel.count()):
                if self.rightPanel.tabText(i) == device_name:
                    self.rightPanel.blockSignals(True)
                    self.rightPanel.setCurrentIndex(i)
                    self.rightPanel.blockSignals(False)
                    break

    def on_tab_changed(self, tab_index):
        """Handle tab changes to select corresponding table row"""
        if not self.devices:
            return

        if 0 <= tab_index < self.rightPanel.count():
            tab_text = self.rightPanel.tabText(tab_index)

            if tab_text == "No Devices":
                return

            for row, device in enumerate(self.devices):
                if device['name'] == tab_text:
                    self.devicesTable.blockSignals(True)
                    self.devicesTable.selectRow(row)
                    self.devicesTable.blockSignals(False)
                    break

    def update_device_info(self):
        """Update the device info box with selected device information"""
        selected_indexes = self.devicesTable.selectionModel().selectedRows()

        if not selected_indexes or not self.devices:
            # Clear existing widgets if any
            if self.deviceInfoLayout.count() > 0:
                while self.deviceInfoLayout.count():
                    item = self.deviceInfoLayout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

            placeholder = QLabel("No Devices\n\nAdd a device to get started")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #999999;")
            self.deviceInfoLayout.addWidget(placeholder)
            self.current_device_name = None
            self.device_connect_btn = None
            self.device_disconnect_btn = None
            return

        selected_row = selected_indexes[0].row()
        if selected_row < 0 or selected_row >= len(self.devices):
            return

        device = self.devices[selected_row]
        device_name = device['name']

        # If already showing this device, just update the status
        if self.current_device_name == device_name and self.device_connect_btn and self.device_disconnect_btn:
            status = device.get('status', 'Disconnected')
            self.device_connect_btn.setEnabled(status != 'Connected')
            self.device_disconnect_btn.setEnabled(status == 'Connected')
            return

        # First time showing this device - create widgets
        if self.deviceInfoLayout.count() > 0:
            while self.deviceInfoLayout.count():
                item = self.deviceInfoLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Name
        name_label = QLabel(f"<b>Name:</b> {device['name']}")
        self.deviceInfoLayout.addWidget(name_label)

        # Network address
        port = device.get('port', '8765')
        if not isinstance(port, str):
            port = str(port)
        network_label = QLabel(f"<b>Network Address:</b> {device['ip_address']}:{port}")
        self.deviceInfoLayout.addWidget(network_label)

        # Status
        status = device.get('status', 'Disconnected')
        status_color = "#00AA00" if status == "Connected" else "#AA0000"
        status_label = QLabel(f"<b>Status:</b> <span style='color: {status_color}; font-weight: bold;'>{status}</span>")
        self.deviceInfoLayout.addWidget(status_label)

        # Version
        version_label = QLabel(f"<b>Software Version:</b> {device.get('version', 'Unknown')}")
        self.deviceInfoLayout.addWidget(version_label)

        self.deviceInfoLayout.addSpacing(10)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.device_connect_btn = QPushButton("Connect")
        self.device_connect_btn.setEnabled(status != 'Connected')
        self.device_connect_btn.clicked.connect(self._on_connect_clicked)
        buttons_layout.addWidget(self.device_connect_btn)

        self.device_disconnect_btn = QPushButton("Disconnect")
        self.device_disconnect_btn.setEnabled(status == 'Connected')
        self.device_disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        buttons_layout.addWidget(self.device_disconnect_btn)

        self.device_sync_btn = QPushButton("Sync Files")
        self.device_sync_btn.setEnabled(status == 'Connected')
        self.device_sync_btn.clicked.connect(self._on_sync_files_clicked)
        buttons_layout.addWidget(self.device_sync_btn)

        buttons_layout.addStretch()

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        self.deviceInfoLayout.addWidget(buttons_widget)

        self.current_device_name = device_name

    def _on_connect_clicked(self):
        """Handle connect button click"""
        if not self.current_device_name:
            return

        # Find the device by name
        device_index = -1
        for i, dev in enumerate(self.devices):
            if dev['name'] == self.current_device_name:
                device_index = i
                break

        if device_index >= 0:
            self.connect_to_device(device_index)

    def _on_disconnect_clicked(self):
        """Handle disconnect button click"""
        if not self.current_device_name:
            return

        # Find the device by name
        device_index = -1
        for i, dev in enumerate(self.devices):
            if dev['name'] == self.current_device_name:
                device_index = i
                break

        if device_index >= 0:
            self.disconnect_from_device(device_index)

    def connect_to_device(self, device_index):
        """Connect to the selected device"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            device_name = device['name']
            ip_address = device['ip_address']
            port = int(device.get('port', '8765')) if isinstance(device.get('port'), str) else device.get('port', 8765)

            try:
                # If connection manager exists and is already connected, just return
                if device_name in self.connection_managers:
                    existing_manager = self.connection_managers[device_name]
                    if existing_manager.is_connected:
                        return
                    else:
                        # Manager exists but not connected, just connect it
                        existing_manager.connect()
                        return

                # Create new manager
                manager = DeviceConnectionManager(device_name, ip_address, port)

                manager.connected.connect(lambda: self._on_device_connected(device_index))
                manager.disconnected.connect(lambda: self._on_device_disconnected(device_index))
                manager.message_received.connect(lambda msg, idx=device_index: self._on_device_message(idx, msg))

                self.connection_managers[device_name] = manager
                manager.connect()

            except Exception as e:
                QMessageBox.warning(self, "Connection Error",
                                   f"Failed to connect to {device_name}: {str(e)}")
                device['status'] = 'Disconnected'
                self.save_devices()
                self.update_devices_table()

    def _on_device_connected(self, device_index):
        """Handle successful device connection"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            device['status'] = 'Connected'

            device_name = device['name']
            if device_name in self.device_tabs:
                tab = self.device_tabs[device_name]
                tab.set_connection_state(True)
                tab.log(f"Connected to {device_name}", "success")

                from shared.managers import ExperimentManager
                experiments_dir = os.path.join(os.path.dirname(__file__), 'experiments')
                if os.path.exists(experiments_dir):
                    experiment_manager = ExperimentManager(experiments_dir)
                    experiments = experiment_manager.list_experiments()
                    tab.set_experiment_list(experiments)

            self.save_devices()
            self.update_devices_table()

            # Update button states if showing this device
            if self.current_device_name == device_name and self.device_connect_btn:
                self.device_connect_btn.setEnabled(False)
                self.device_disconnect_btn.setEnabled(True)
                if self.device_sync_btn:
                    self.device_sync_btn.setEnabled(True)

    def _on_device_disconnected(self, device_index):
        """Handle device disconnection"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            device['status'] = 'Disconnected'

            device_name = device['name']
            if device_name in self.device_tabs:
                self.device_tabs[device_name].set_connection_state(False)
                self.device_tabs[device_name].log("Disconnected from device", "info")

            self.save_devices()
            self.update_devices_table()

            # Update button states if showing this device
            if self.current_device_name == device_name and self.device_connect_btn:
                self.device_connect_btn.setEnabled(True)
                self.device_disconnect_btn.setEnabled(False)

    def _on_device_message(self, device_index, message):
        """Handle messages from device"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            device_name = device['name']

            if device_name not in self.device_tabs:
                return

            tab = self.device_tabs[device_name]
            msg_type = message.get('type')

            if msg_type == "input_state":
                states = message.get('data', {})
                for key, value in states.items():
                    tab.update_input_state(key, value)

                # Extract and store version information
                version = message.get('version', 'Unknown')
                device['version'] = version
                # Just update button states, don't recreate
                if self.current_device_name == device_name and self.device_connect_btn:
                    status = device.get('status', 'Disconnected')
                    self.device_connect_btn.setEnabled(status != 'Connected')
                    self.device_disconnect_btn.setEnabled(status == 'Connected')

            elif msg_type == "statistics":
                stats = message.get('data', {})
                tab.update_statistics(stats)

            elif msg_type == "test_state":
                test_data = message.get('data', {})
                for test_name, test_info in test_data.items():
                    state = test_info.get('state')
                    tab.update_test_state(test_name, state)

            elif msg_type == "device_log":
                log_data = message.get('data', {})
                tab.log(log_data.get('message', ''), log_data.get('state', 'info'))

            elif msg_type == "experiment_status":
                status = message.get('data', {}).get('status')
                tab.set_experiment_buttons(status == 'started')
                tab.log(f"Experiment status: {status}", "info")

                if status == "started":
                    tab.set_experiment_started()
                elif status in ["completed", "stopped"]:
                    tab.set_experiment_stopped()

            elif msg_type == "trial_start":
                trial_data = message.get('data', {})
                trial_name = trial_data.get('trial') if isinstance(trial_data, dict) else trial_data
                if trial_name:
                    tab.log(f"Trial start: {trial_name}", "info")
                    tab.set_trial_started(trial_name)

            elif msg_type == "trial_complete":
                trial_name = message.get('data', {}).get('trial')
                outcome = message.get('data', {}).get('data', {}).get('trial_outcome', 'success')
                log_level = "warning" if outcome.startswith("failure") else "success"
                tab.log(f"Trial complete: {trial_name}", log_level)
                tab.set_trial_complete()

            elif msg_type == "data_file_list":
                self._handle_data_file_list(device_name, message.get('data', {}).get('files', []))

            elif msg_type == "data_file_content":
                self._handle_data_file_content(device_name, message.get('data', {}))

    def _on_destroyed(self):
        """Cleanup when window is destroyed"""
        for manager in list(self.connection_managers.values()):
            try:
                manager.disconnect()
            except Exception:
                pass

    def disconnect_from_device(self, device_index):
        """Disconnect from the selected device"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            device_name = device['name']

            if device_name in self.connection_managers:
                manager = self.connection_managers[device_name]
                try:
                    manager.disconnect()
                except Exception as e:
                    pass

                del self.connection_managers[device_name]

            device['status'] = 'Disconnected'

            # Update the device tab state
            if device_name in self.device_tabs:
                self.device_tabs[device_name].set_connection_state(False)
                self.device_tabs[device_name].log("Disconnected from device", "info")

            self.save_devices()
            self.update_devices_table()

            # Update button states if showing this device
            if self.current_device_name == device_name and self.device_connect_btn:
                self.device_connect_btn.setEnabled(True)
                self.device_disconnect_btn.setEnabled(False)
                if self.device_sync_btn:
                    self.device_sync_btn.setEnabled(False)

    def _on_sync_files_clicked(self):
        """Handle sync files button click"""
        if not self.current_device_name:
            return

        device = None
        for d in self.devices:
            if d['name'] == self.current_device_name:
                device = d
                break

        if not device:
            return

        device_name = device['name']

        if device_name not in self.connection_managers:
            QMessageBox.warning(self, "Error", "Not connected to device")
            return

        # Create destination directory
        dest_base = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(dest_base, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_dir = os.path.join(dest_base, f"{device_name}_{timestamp}")

        dialog = SyncProgressDialog(self, device_name)

        # Store references for message handlers
        self._current_sync_dialog = dialog
        self._current_sync_device = device_name
        self._sync_destination_dir = dest_dir
        self._sync_files_to_download = []
        self._sync_files_downloaded = []

        # Request the list of files
        manager = self.connection_managers[device_name]
        manager.send_message(CommunicationMessageBuilder.request_data_files())

        # Show dialog
        dialog.exec()

    def _handle_data_file_list(self, device_name, files):
        """Handle incoming data file list"""
        if device_name != self._current_sync_device if hasattr(self, '_current_sync_device') else None:
            return

        if not files:
            if hasattr(self, '_current_sync_dialog'):
                self._current_sync_dialog.close()
                QMessageBox.information(self, "No Files", "No data files found on device")
            return

        # Store files to download
        self._sync_files_to_download = files
        dialog = self._current_sync_dialog
        dialog.set_total_files(len(files))

        # Request each file
        manager = self.connection_managers[device_name]

        for file_info in files:
            filename = file_info['filename']
            request_msg = CommunicationMessageBuilder.request_data_file(filename)
            manager.send_message(request_msg)

    def _handle_data_file_content(self, device_name, file_data):
        """Handle incoming data file content"""
        if device_name != self._current_sync_device if hasattr(self, '_current_sync_device') else None:
            return

        filename = file_data.get('filename')
        content = file_data.get('content')
        expected_checksum = file_data.get('checksum')

        if not filename or not content:
            return

        # Validate checksum if provided
        if expected_checksum:
            calculated = hashlib.md5(content.encode()).hexdigest()
            if calculated != expected_checksum:
                if hasattr(self, '_current_sync_dialog'):
                    self._current_sync_dialog.update_progress(
                        filename,
                        len(self._sync_files_downloaded) + 1,
                        len(self._sync_files_to_download),
                        "Checksum mismatch!"
                    )
                return

        # Save file
        try:
            os.makedirs(self._sync_destination_dir, exist_ok=True)
            filepath = os.path.join(self._sync_destination_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

            self._sync_files_downloaded.append(filename)

            if hasattr(self, '_current_sync_dialog'):
                self._current_sync_dialog.update_progress(
                    filename,
                    len(self._sync_files_downloaded),
                    len(self._sync_files_to_download),
                    "OK"
                )

                # Check if all files downloaded
                if len(self._sync_files_downloaded) == len(self._sync_files_to_download):
                    self._current_sync_dialog.set_finished(
                        len(self._sync_files_downloaded),
                        len(self._sync_files_to_download)
                    )
                    QMessageBox.information(
                        self,
                        "Sync Complete",
                        f"Successfully synced {len(self._sync_files_downloaded)} files to:\n{self._sync_destination_dir}"
                    )
        except Exception as e:
            if hasattr(self, '_current_sync_dialog'):
                self._current_sync_dialog.update_progress(
                    filename,
                    len(self._sync_files_downloaded) + 1,
                    len(self._sync_files_to_download),
                    f"Error: {str(e)}"
                )

    def update_tabs(self):
        """Update the tab widget based on current devices"""
        self.rightPanel.blockSignals(True)

        for i in range(self.rightPanel.count() - 1, -1, -1):
            self.rightPanel.removeTab(i)

        # Store device statuses before clearing tabs
        device_statuses = {}
        for device in self.devices:
            device_statuses[device['name']] = device.get('status', 'Disconnected')

        self.device_tabs.clear()

        if not self.devices:
            placeholder = QWidget()
            layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)

            spacer1 = QWidget()
            spacer1.setMinimumSize(0, 40)
            layout.addWidget(spacer1)

            label = QLabel("No Devices\n\nAdd a device to get started")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #999999; font-size: 24pt;")
            layout.addWidget(label)

            spacer2 = QWidget()
            spacer2.setMinimumSize(0, 40)
            layout.addWidget(spacer2)

            placeholder.setLayout(layout)
            self.rightPanel.addTab(placeholder, "No Devices")
        else:
            for device in self.devices:
                tab = self.create_device_tab()
                self.device_tabs[device['name']] = tab
                self.rightPanel.addTab(tab, device['name'])

                # If device was previously connected, reload experiments
                if device_statuses.get(device['name']) == 'Connected':
                    tab.set_connection_state(True)
                    tab.log(f"Reconnected to {device['name']}", "success")

                    # Load experiments for this device
                    experiments_dir = os.path.join(os.path.dirname(__file__), 'experiments')
                    if os.path.exists(experiments_dir):
                        experiment_manager = ExperimentManager(experiments_dir)
                        experiments = experiment_manager.list_experiments()
                        tab.set_experiment_list(experiments)

        self.rightPanel.blockSignals(False)

        if self.rightPanel.count() > 0:
            self.rightPanel.setCurrentIndex(0)

    def create_device_tab(self):
        """Create a tab widget for a device"""
        tab = DeviceTab()

        tab.test_requested.connect(self._on_test_requested)
        tab.experiment_stop_requested.connect(self._on_experiment_stop_requested)
        tab.experiment_start_requested.connect(self._on_experiment_start_requested)
        tab.new_experiment_requested.connect(lambda: self._on_experiment_new_requested())
        tab.edit_experiment_requested.connect(self._on_experiment_edit_requested)

        return tab

    def _on_test_requested(self, test_name):
        """Handle test request from device tab"""
        current_tab_idx = self.rightPanel.currentIndex()
        if current_tab_idx >= 0 and current_tab_idx < len(self.devices):
            device = self.devices[current_tab_idx]
            device_name = device['name']

            if device_name in self.connection_managers and device_name in self.device_tabs:
                tab = self.device_tabs[device_name]
                tab.update_test_state(test_name, TEST_STATES["RUNNING"])

                manager = self.connection_managers[device_name]
                try:
                    manager.send_command(test_name)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to send test command: {str(e)}")

    def _on_experiment_stop_requested(self):
        """Handle experiment stop request"""
        current_tab_idx = self.rightPanel.currentIndex()
        if current_tab_idx >= 0 and current_tab_idx < len(self.devices):
            device = self.devices[current_tab_idx]
            device_name = device['name']

            if device_name in self.connection_managers:
                manager = self.connection_managers[device_name]
                try:
                    manager.send_command("stop_experiment")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to stop experiment: {str(e)}")

    def _on_experiment_new_requested(self):
        """Handle new experiment request"""
        self.open_experiment_editor(None, new=True)

    def _on_experiment_edit_requested(self, experiment_name):
        """Handle edit experiment request"""
        self.open_experiment_editor(None, experiment_name=experiment_name)

    def _on_experiment_start_requested(self, data):
        """Handle experiment start request"""
        animal_id = data.get('animal_id')
        experiment_name = data.get('experiment_name')

        current_tab_idx = self.rightPanel.currentIndex()
        if current_tab_idx < 0 or current_tab_idx >= len(self.devices):
            return

        device = self.devices[current_tab_idx]
        device_name = device['name']

        if not animal_id:
            QMessageBox.warning(self, "No Animal ID", "Please enter an animal ID.")
            return

        if not experiment_name:
            QMessageBox.warning(self, "No Experiment", "Please select an experiment to run.")
            return

        if device_name not in self.connection_managers or device_name not in self.device_tabs:
            return

        manager = self.connection_managers[device_name]
        tab = self.device_tabs[device_name]

        experiments_dir = os.path.join(os.path.dirname(__file__), 'experiments')
        if not os.path.exists(experiments_dir):
            os.makedirs(experiments_dir)

        experiment_manager = ExperimentManager(experiments_dir)
        experiment = experiment_manager.load_experiment(experiment_name)

        if not experiment:
            QMessageBox.warning(self, "Error", f"Failed to load experiment '{experiment_name}'")
            return

        is_valid, errors = experiment.validate()
        if not is_valid:
            error_msg = "Experiment validation failed:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        try:
            upload_message = {
                "type": "experiment_upload",
                "data": experiment.to_dict()
            }
            manager.send_message(upload_message)

            tab.log("Experiment uploaded, starting experiment...", "info")

            start_message = {
                "type": "start_experiment",
                "animal_id": animal_id
            }
            manager.send_message(start_message)

            tab.log(f"Starting experiment with animal ID: {animal_id}", "info")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to start experiment: {str(e)}")
            tab.log(f"Failed to start experiment: {str(e)}", "error")

    def open_experiment_editor(self, tab_widget, new=False, experiment_name=None):
        """Open the experiment editor dialog"""
        import sys
        import os

        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        experiments_dir = os.path.join(os.path.dirname(__file__), 'experiments')
        if not os.path.exists(experiments_dir):
            os.makedirs(experiments_dir)

        experiment_manager = ExperimentManager(experiments_dir)
        editor = ExperimentEditor(self, experiment_manager=experiment_manager)

        if new:
            editor.new_experiment()
        elif experiment_name:
            experiment = experiment_manager.load_experiment(experiment_name)
            if experiment:
                editor.current_experiment = experiment
                editor.update_ui()

        result = editor.exec()

        if result == editor.DialogCode.Accepted:
            experiments = experiment_manager.list_experiments()

            for device_name, tab in self.device_tabs.items():
                tab.set_experiment_list(experiments)

            if editor.current_experiment:
                for device_name, tab in self.device_tabs.items():
                    tab.set_current_experiment(editor.current_experiment.name)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

