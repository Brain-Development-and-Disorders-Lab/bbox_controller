#!/usr/bin/env python3

import sys
import os
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
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6 import uic


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

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Device name cannot be empty.")
            return

        if not ip:
            QMessageBox.warning(self, "Invalid Input", "IP address cannot be empty.")
            return

        if not self.validate_ip_address(ip):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid IP address (e.g., 192.168.1.100)")
            return

        self.accept()

    def get_device_data(self):
        return {
            'name': self.name_field.text().strip(),
            'ip_address': self.ip_field.text().strip()
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

        self.devices_file = os.path.join(
            os.path.dirname(__file__),
            'config',
            'devices.json'
        )
        self.devices = []

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
                    self.devices = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.devices = []

        self.update_devices_table()
        self.update_tabs()

    def save_devices(self):
        """Save devices to file"""
        try:
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
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
                'status': 'Disconnected'
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
            from PyQt6.QtGui import QColor
            if status_text == "Connected":
                status_item.setForeground(QColor("#00AA00"))  # Subdued green
            else:
                status_item.setForeground(QColor("#AA0000"))
            self.devicesTable.setItem(row, 1, status_item)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, idx=row: self.edit_device(idx))
            self.devicesTable.setCellWidget(row, 2, edit_btn)

        if len(self.devices) > 0:
            self.devicesTable.selectRow(0)

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
        from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget

        while self.deviceInfoLayout.count():
            child = self.deviceInfoLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                for i in range(child.layout().count()):
                    item = child.layout().itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()

        selected_row = self.devicesTable.currentRow()

        if selected_row >= 0 and selected_row < len(self.devices):
            device = self.devices[selected_row]

            name_widget = QWidget()
            name_layout = QHBoxLayout(name_widget)
            name_layout.setContentsMargins(0, 0, 0, 0)
            name_layout.addWidget(QLabel("<b>Name:</b>"))
            name_value = QLabel(device['name'])
            name_value.setStyleSheet("font-weight: bold;")
            name_layout.addWidget(name_value)
            name_layout.addStretch()
            self.deviceInfoLayout.addWidget(name_widget)

            ip_widget = QWidget()
            ip_layout = QHBoxLayout(ip_widget)
            ip_layout.setContentsMargins(0, 0, 0, 0)
            ip_layout.addWidget(QLabel("<b>IP Address:</b>"))
            ip_layout.addWidget(QLabel(device['ip_address']))
            ip_layout.addStretch()
            self.deviceInfoLayout.addWidget(ip_widget)

            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.addWidget(QLabel("<b>Status:</b>"))
            status_value = QLabel(device.get('status', 'Disconnected'))
            if status_value.text() == "Connected":
                status_color = "#00AA00"
            else:
                status_color = "#AA0000"
            status_value.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            status_layout.addWidget(status_value)
            status_layout.addStretch()
            self.deviceInfoLayout.addWidget(status_widget)

            version_widget = QWidget()
            version_layout = QHBoxLayout(version_widget)
            version_layout.setContentsMargins(0, 0, 0, 0)
            version_layout.addWidget(QLabel("<b>Software Version:</b>"))
            version_layout.addWidget(QLabel(device.get('version', 'Unknown')))
            version_layout.addStretch()
            self.deviceInfoLayout.addWidget(version_widget)

            self.deviceInfoLayout.addSpacing(10)

            buttons_widget = QWidget()
            buttons_layout = QHBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)

            connect_btn = QPushButton("Connect")
            connect_btn.setEnabled(device.get('status') != 'Connected')
            connect_btn.clicked.connect(lambda: self.connect_to_device(selected_row))
            buttons_layout.addWidget(connect_btn)

            disconnect_btn = QPushButton("Disconnect")
            disconnect_btn.setEnabled(device.get('status') == 'Connected')
            disconnect_btn.clicked.connect(lambda: self.disconnect_from_device(selected_row))
            buttons_layout.addWidget(disconnect_btn)

            buttons_layout.addStretch()
            self.deviceInfoLayout.addWidget(buttons_widget)
        else:
            placeholder = QLabel("No Devices\n\nAdd a device to get started")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #999999;")
            self.deviceInfoLayout.addWidget(placeholder)

    def connect_to_device(self, device_index):
        """Connect to the selected device"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            print(f"Connecting to {device['name']} at {device['ip_address']}")
            # TODO: Implement WebSocket connection logic

            # Update status
            device['status'] = 'Connected'
            self.save_devices()
            self.update_devices_table()

    def disconnect_from_device(self, device_index):
        """Disconnect from the selected device"""
        if device_index >= 0 and device_index < len(self.devices):
            device = self.devices[device_index]
            print(f"Disconnecting from {device['name']}")
            # TODO: Implement WebSocket disconnection logic

            # Update status
            device['status'] = 'Disconnected'
            self.save_devices()
            self.update_devices_table()

    def update_tabs(self):
        """Update the tab widget based on current devices"""
        self.rightPanel.blockSignals(True)

        for i in range(self.rightPanel.count() - 1, -1, -1):
            self.rightPanel.removeTab(i)

        if not self.devices:
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

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
                self.rightPanel.addTab(tab, device['name'])

        self.rightPanel.blockSignals(False)

        if self.rightPanel.count() > 0:
            self.rightPanel.setCurrentIndex(0)

    def create_device_tab(self):
        """Create a tab widget for a device"""
        from PyQt6.QtWidgets import (
            QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout,
            QFormLayout, QPushButton, QComboBox, QLineEdit, QTextEdit,
            QGridLayout, QSizePolicy
        )

        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        exp_mgmt_box = QGroupBox("Experiment Management")
        exp_mgmt_layout = QVBoxLayout()

        animal_id_layout = QHBoxLayout()
        animal_id_layout.addWidget(QLabel("Animal ID:"))
        animal_id_input = QLineEdit()
        animal_id_input.setPlaceholderText("Enter animal ID")
        animal_id_layout.addWidget(animal_id_input)
        exp_mgmt_layout.addLayout(animal_id_layout)

        experiment_layout = QHBoxLayout()
        experiment_layout.addWidget(QLabel("Experiment:"))
        experiment_combo = QComboBox()
        experiment_combo.addItems(["No experiments available"])
        experiment_layout.addWidget(experiment_combo)
        exp_mgmt_layout.addLayout(experiment_layout)

        new_exp_btn = QPushButton("New Experiment")
        edit_exp_btn = QPushButton("Edit Experiment")
        start_btn = QPushButton("Start")
        stop_btn = QPushButton("Stop")

        new_exp_btn.clicked.connect(lambda: self.open_experiment_editor(widget, new=True))
        edit_exp_btn.clicked.connect(lambda: self.open_experiment_editor(widget, new=False))

        exp_buttons_layout = QHBoxLayout()
        exp_buttons_layout.addWidget(new_exp_btn)
        exp_buttons_layout.addWidget(edit_exp_btn)
        exp_buttons_layout.addWidget(start_btn)
        exp_buttons_layout.addWidget(stop_btn)
        exp_mgmt_layout.addLayout(exp_buttons_layout)

        exp_mgmt_box.setLayout(exp_mgmt_layout)
        main_layout.addWidget(exp_mgmt_box)

        status_panels = QHBoxLayout()
        status_panels.setSpacing(10)

        input_status_box = QGroupBox("Input Status")
        input_status_layout = QVBoxLayout()
        input_status_layout.setSpacing(5)

        input_states = [
            "Left Lever", "Left Lever Light",
            "Right Lever", "Right Lever Light",
            "Nose Poke", "Nose Light"
        ]

        for state in input_states:
            state_layout = QHBoxLayout()
            label = QLabel(state)
            label.setMinimumWidth(120)  # Fixed width for labels
            state_layout.addWidget(label)
            indicator = QLabel("●")
            indicator.setStyleSheet("color: red; font-size: 16pt;")
            state_layout.addWidget(indicator)
            state_layout.addStretch()
            input_status_layout.addLayout(state_layout)

        input_status_box.setLayout(input_status_layout)
        status_panels.addWidget(input_status_box)

        test_status_box = QGroupBox("Test Status")
        test_status_layout = QVBoxLayout()
        test_status_layout.setSpacing(5)

        test_tests = [
            ("Test Water Delivery", True),
            ("Test Levers", False),
            ("Test Lever Lights", True),
            ("Test IR", False),
            ("Test Nose Light", True),
            ("Test Displays", True)
        ]

        for test_name, has_duration in test_tests:
            test_layout = QHBoxLayout()

            label = QLabel(test_name)
            label.setMinimumWidth(130)
            test_layout.addWidget(label)

            if has_duration:
                duration_layout = QHBoxLayout()
                duration_label = QLabel("Duration:")
                duration_label.setMinimumWidth(60)
                duration_layout.addWidget(duration_label)
                duration_input = QLineEdit("2000")
                duration_input.setMaximumWidth(50)
                duration_layout.addWidget(duration_input)
                test_layout.addLayout(duration_layout)
            else:
                spacer = QWidget()
                spacer.setFixedWidth(110)
                test_layout.addWidget(spacer)

            indicator = QLabel("●")
            indicator.setStyleSheet("color: blue; font-size: 16pt;")
            test_layout.addWidget(indicator)

            test_btn = QPushButton("Test")
            test_btn.setMaximumWidth(60)
            test_layout.addWidget(test_btn)
            test_layout.addStretch()
            test_status_layout.addLayout(test_layout)

        reset_btn = QPushButton("Reset")
        test_status_layout.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignRight)

        test_status_box.setLayout(test_status_layout)
        status_panels.addWidget(test_status_box)

        stats_box = QGroupBox("Experiment Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        statistics = [
            "Total Experiment Time", "Active Trial Time", "Active Trial",
            "Total Trials", "Total Nose Pokes",
            "Total Left Lever Presses", "Total Right Lever Presses",
            "Total Water Deliveries"
        ]

        for stat in statistics:
            stat_layout = QHBoxLayout()

            label = QLabel(stat + ":")
            label.setMinimumWidth(200)
            stat_layout.addWidget(label)

            value_label = QLabel("0")
            value_label.setMinimumWidth(60)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(value_label)

            stat_layout.addStretch()
            stats_layout.addLayout(stat_layout)

        stats_box.setLayout(stats_layout)
        status_panels.addWidget(stats_box)

        input_status_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        input_status_box.setMaximumWidth(250)
        test_status_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        stats_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        stats_box.setMaximumWidth(300)

        main_layout.addLayout(status_panels)

        console_box = QGroupBox("Console")
        console_layout = QVBoxLayout()

        console = QTextEdit()
        console.setReadOnly(True)
        console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        console.setText("Console ready...\n")
        console_layout.addWidget(console)

        console_box.setLayout(console_layout)
        main_layout.addWidget(console_box)

        console_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        console.setMaximumHeight(200)

        widget.setLayout(main_layout)
        return widget

    def open_experiment_editor(self, tab_widget, new=False):
        """Open the experiment editor dialog"""
        import sys
        import os

        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        from dashboard.components.experiment_editor import ExperimentEditor
        from shared.managers import ExperimentManager

        experiments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'experiments')
        if not os.path.exists(experiments_dir):
            os.makedirs(experiments_dir)

        experiment_manager = ExperimentManager(experiments_dir)
        editor = ExperimentEditor(self, experiment_manager=experiment_manager)
        editor.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

