#!/usr/bin/env python3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from shared.constants import TEST_STATES, TEST_COMMANDS
from typing import Dict, Any
import time


class DeviceTab(QWidget):
    """Tab widget representing a single device with all its controls"""

    test_requested = pyqtSignal(str)  # Emitted when a test is requested
    experiment_start_requested = pyqtSignal(dict)  # Emitted when experiment should start
    experiment_stop_requested = pyqtSignal()  # Emitted when experiment should stop
    new_experiment_requested = pyqtSignal()  # Emitted when new experiment button clicked
    edit_experiment_requested = pyqtSignal(str)  # Emitted when edit experiment button clicked, emits experiment name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_experiment = None
        self.input_states = {}
        self.statistics = {}
        self.test_states = {}

        # Timer state
        self.experiment_start_time = None
        self.current_trial_start_time = None
        self.current_trial_type = "None"

        # Timer for updating displays every second
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timers)
        self.timer.start(1000)  # Update every second

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        """Create all UI widgets for the device tab"""

        self.animal_id_input = QLineEdit()
        self.animal_id_input.setPlaceholderText("Enter animal ID")

        self.experiment_combo = QComboBox()
        self.experiment_combo.addItems(["No experiments available"])

        self.new_exp_btn = QPushButton("New Experiment")
        self.edit_exp_btn = QPushButton("Edit Experiment")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")

        self.start_btn.clicked.connect(self._on_start_clicked)

        self.new_exp_btn.clicked.connect(self.new_experiment_requested.emit)
        self.edit_exp_btn.clicked.connect(self._on_edit_clicked)
        self.stop_btn.clicked.connect(self.experiment_stop_requested.emit)

        self._create_status_widgets()
        self._create_test_widgets()
        self._create_statistics_widgets()
        self._create_console_widget()

    def _create_status_widgets(self):
        """Create input status indicators"""
        self.input_indicators = {
            'input_lever_left': None,
            'input_lever_right': None,
            'input_ir': None,
            'led_port': None,
            'led_lever_left': None,
            'led_lever_right': None
        }

    def _create_test_widgets(self):
        """Create test control widgets"""
        self.test_buttons = {}
        self.test_indicators = {}
        self.reset_btn = None
        self.test_running = False

    def _create_statistics_widgets(self):
        """Create statistics display widgets"""
        self.stat_labels = {
            'nose_pokes': None,
            'left_lever_presses': None,
            'right_lever_presses': None,
            'trial_count': None,
            'water_deliveries': None
        }

    def _create_console_widget(self):
        """Create console output widget"""
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        self.log("Console ready...", "info")

    def _create_layout(self):
        """Create the main layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        exp_mgmt_box = QGroupBox("Experiment Management")
        exp_mgmt_layout = QVBoxLayout()

        animal_id_layout = QHBoxLayout()
        animal_id_layout.addWidget(QLabel("Animal ID:"))
        animal_id_layout.addWidget(self.animal_id_input)
        exp_mgmt_layout.addLayout(animal_id_layout)

        experiment_layout = QHBoxLayout()
        experiment_layout.addWidget(QLabel("Experiment:"))
        experiment_layout.addWidget(self.experiment_combo)
        exp_mgmt_layout.addLayout(experiment_layout)

        exp_buttons_layout = QHBoxLayout()
        exp_buttons_layout.addWidget(self.new_exp_btn)
        exp_buttons_layout.addWidget(self.edit_exp_btn)
        exp_buttons_layout.addWidget(self.start_btn)
        exp_buttons_layout.addWidget(self.stop_btn)
        exp_mgmt_layout.addLayout(exp_buttons_layout)

        exp_mgmt_box.setLayout(exp_mgmt_layout)
        main_layout.addWidget(exp_mgmt_box)

        status_panels = QHBoxLayout()
        status_panels.setSpacing(10)

        input_status_box = QGroupBox("Input Status")
        input_status_layout = QVBoxLayout()
        input_status_layout.setSpacing(5)

        input_states = [
            ("Left Lever", "input_lever_left"),
            ("Left Lever Light", "led_lever_left"),
            ("Right Lever", "input_lever_right"),
            ("Right Lever Light", "led_lever_right"),
            ("Nose Poke", "input_ir"),
            ("Nose Light", "led_port")
        ]

        for label, key in input_states:
            state_layout = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setMinimumWidth(120)
            state_layout.addWidget(lbl)

            indicator = QLabel("●")
            indicator.setStyleSheet("color: red; font-size: 16pt;")
            self.input_indicators[key] = indicator
            state_layout.addWidget(indicator)
            state_layout.addStretch()
            input_status_layout.addLayout(state_layout)

        input_status_box.setLayout(input_status_layout)
        status_panels.addWidget(input_status_box)
        input_status_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        input_status_box.setMaximumWidth(250)

        test_status_box = QGroupBox("Test Status")
        test_status_layout = QVBoxLayout()

        test_grid = QGridLayout()
        test_grid.setSpacing(5)

        test_tests = [
            ("Test Water Delivery", "test_water_delivery", True),
            ("Test Levers", "test_input_levers", False),
            ("Test Lever Lights", "test_led_levers", True),
            ("Test IR", "test_input_ir", False),
            ("Test Nose Light", "test_led_port", True),
            ("Test Displays", "test_displays", True)
        ]

        for row, (test_name, test_key, has_duration) in enumerate(test_tests):
            lbl = QLabel(test_name)
            lbl.setFixedWidth(130)
            test_grid.addWidget(lbl, row, 0)

            if has_duration:
                duration_label = QLabel("Duration:")
                duration_label.setFixedWidth(60)
                test_grid.addWidget(duration_label, row, 1)

                duration_input = QLineEdit("2000")
                duration_input.setFixedWidth(50)
                test_grid.addWidget(duration_input, row, 2)
            else:
                spacer1 = QWidget()
                spacer1.setFixedSize(60, 1)
                test_grid.addWidget(spacer1, row, 1)

                spacer2 = QWidget()
                spacer2.setFixedSize(50, 1)
                test_grid.addWidget(spacer2, row, 2)

            indicator = QLabel("●")
            indicator.setStyleSheet("color: blue; font-size: 16pt;")
            indicator.setFixedWidth(20)
            self.test_indicators[test_key] = indicator
            test_grid.addWidget(indicator, row, 3)

            test_btn = QPushButton("Test")
            test_btn.setFixedWidth(60)
            test_btn.clicked.connect(lambda checked, key=test_key: self._on_test_clicked(key))
            self.test_buttons[test_key] = test_btn
            test_grid.addWidget(test_btn, row, 4)

        test_status_layout.addLayout(test_grid)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._on_reset_clicked)
        self.reset_btn = reset_btn
        test_status_layout.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignRight)

        test_status_box.setLayout(test_status_layout)
        status_panels.addWidget(test_status_box)

        stats_box = QGroupBox("Experiment Statistics")
        stats_layout = QVBoxLayout()

        stats_grid = QGridLayout()
        stats_grid.setSpacing(2)
        stats_grid.setContentsMargins(0, 0, 0, 0)

        statistics = [
            ("Total Trials", "trial_count"),
            ("Total Nose Pokes", "nose_pokes"),
            ("Total Left Lever Presses", "left_lever_presses"),
            ("Total Right Lever Presses", "right_lever_presses"),
            ("Total Water Deliveries", "water_deliveries")
        ]

        for row, (stat_label, stat_key) in enumerate(statistics):
            lbl = QLabel(stat_label + ":")
            lbl.setMinimumWidth(200)
            stats_grid.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignLeft)

            value_label = QLabel("0")
            value_label.setMinimumWidth(60)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("font-weight: bold;")
            self.stat_labels[stat_key] = value_label
            stats_grid.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignRight)

        # Add timer labels
        timer_row = len(statistics)

        total_time_lbl = QLabel("Experiment Time:")
        total_time_lbl.setMinimumWidth(200)
        stats_grid.addWidget(total_time_lbl, timer_row, 0, Qt.AlignmentFlag.AlignLeft)

        self.total_experiment_time_label = QLabel("00:00:00")
        self.total_experiment_time_label.setMinimumWidth(60)
        self.total_experiment_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_experiment_time_label.setStyleSheet("font-weight: bold; color: #0066CC;")
        stats_grid.addWidget(self.total_experiment_time_label, timer_row, 1, Qt.AlignmentFlag.AlignRight)

        trial_row = timer_row + 1

        active_trial_lbl = QLabel("Active Trial:")
        active_trial_lbl.setMinimumWidth(200)
        stats_grid.addWidget(active_trial_lbl, trial_row, 0, Qt.AlignmentFlag.AlignLeft)

        self.active_trial_type_label = QLabel("None")
        self.active_trial_type_label.setMinimumWidth(100)
        self.active_trial_type_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.active_trial_type_label.setStyleSheet("font-weight: bold;")
        stats_grid.addWidget(self.active_trial_type_label, trial_row, 1, Qt.AlignmentFlag.AlignRight)

        trial_time_lbl = QLabel("Trial Time:")
        trial_time_lbl.setMinimumWidth(200)
        stats_grid.addWidget(trial_time_lbl, trial_row + 1, 0, Qt.AlignmentFlag.AlignLeft)

        self.active_trial_time_label = QLabel("00:00:00")
        self.active_trial_time_label.setMinimumWidth(60)
        self.active_trial_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.active_trial_time_label.setStyleSheet("font-weight: bold; color: #0066CC;")
        stats_grid.addWidget(self.active_trial_time_label, trial_row + 1, 1, Qt.AlignmentFlag.AlignRight)

        stats_layout.addLayout(stats_grid)

        stats_box.setLayout(stats_layout)
        status_panels.addWidget(stats_box)
        stats_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        stats_box.setMaximumWidth(300)

        main_layout.addLayout(status_panels)

        console_box = QGroupBox("Console")
        console_layout = QVBoxLayout()
        console_layout.addWidget(self.console)
        console_box.setLayout(console_layout)

        console_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.console.setMinimumHeight(200)

        main_layout.addWidget(console_box)
        self.setLayout(main_layout)

    def _on_test_clicked(self, test_key):
        """Handle test button click"""
        self.set_test_buttons_enabled(False)
        self.test_running = True
        self.test_requested.emit(test_key)

    def _on_reset_clicked(self):
        """Handle reset button click"""
        for test_key in self.test_indicators.keys():
            self.test_states[test_key] = TEST_STATES["NOT_TESTED"]
            self.update_test_state(test_key, TEST_STATES["NOT_TESTED"])
        self.set_test_buttons_enabled(True)
        self.test_running = False

    def update_input_state(self, state_key, value):
        """Update input state indicator"""
        if state_key in self.input_indicators:
            indicator = self.input_indicators[state_key]
            color = "green" if value else "red"
            indicator.setStyleSheet(f"color: {color}; font-size: 16pt;")

    def update_test_state(self, test_key, state):
        """Update test indicator"""
        if test_key in self.test_indicators:
            indicator = self.test_indicators[test_key]
            self.test_states[test_key] = state

            if state == TEST_STATES["FAILED"]:
                color = "red"
            elif state == TEST_STATES["PASSED"]:
                color = "green"
            elif state == TEST_STATES["RUNNING"]:
                color = "yellow"
            else:
                color = "blue"

            indicator.setStyleSheet(f"color: {color}; font-size: 16pt;")

            if state in [TEST_STATES["PASSED"], TEST_STATES["FAILED"]]:
                self.test_running = False
                self.set_test_buttons_enabled(True)

    def set_test_buttons_enabled(self, enabled):
        """Enable/disable all test buttons"""
        for btn in self.test_buttons.values():
            btn.setEnabled(enabled)
        if self.reset_btn:
            self.reset_btn.setEnabled(enabled)

    def update_statistics(self, stats):
        """Update statistics display"""
        for key, label in self.stat_labels.items():
            if label and key in stats:
                label.setText(str(stats[key]))

    def log(self, message, state="info"):
        """Add message to console with color formatting"""
        from datetime import datetime
        from PyQt6.QtGui import QColor
        from PyQt6.QtGui import QTextCursor

        timestamp = datetime.now().strftime('%H:%M:%S')

        log_state_map = {
            "info": ("Info", QColor(224, 224, 224)),
            "success": ("Success", QColor(0, 255, 0)),
            "error": ("Error", QColor(255, 68, 68)),
            "warning": ("Warning", QColor(255, 170, 0)),
            "debug": ("Debug", QColor(170, 170, 170))
        }

        state_text, color = log_state_map.get(state, ("Info", QColor(224, 224, 224)))

        text = f"[{timestamp}] [{state_text}] {message}\n"

        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.setTextColor(color)

        from PyQt6.QtGui import QFont
        font = self.console.font()
        font.setWeight(QFont.Weight.Medium)
        self.console.setFont(font)

        self.console.insertPlainText(text)

    def set_connection_state(self, connected):
        """Enable/disable controls based on connection state"""
        self.animal_id_input.setEnabled(connected)
        self.experiment_combo.setEnabled(connected)

        if not connected:
            self.set_test_buttons_enabled(False)
            self.test_running = False
        elif not self.test_running:
            self.set_test_buttons_enabled(True)

    def _on_start_clicked(self):
        """Handle start button click"""
        animal_id = self.animal_id_input.text().strip()
        experiment_name = self.experiment_combo.currentText()

        data = {
            'animal_id': animal_id,
            'experiment_name': experiment_name if experiment_name != "No experiments available" else None
        }
        self.experiment_start_requested.emit(data)

    def set_experiment_buttons(self, experiment_running):
        """Enable/disable experiment control buttons"""
        if experiment_running:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.new_exp_btn.setEnabled(False)
            self.edit_exp_btn.setEnabled(False)
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.new_exp_btn.setEnabled(True)
            self.edit_exp_btn.setEnabled(True)

    def set_experiment_list(self, experiments):
        """Update the experiment combo box"""
        self.experiment_combo.clear()
        if experiments:
            self.experiment_combo.addItems(experiments)
        else:
            self.experiment_combo.addItem("No experiments available")

    def set_current_experiment(self, experiment_name):
        """Set the current experiment in the combo box"""
        index = self.experiment_combo.findText(experiment_name)
        if index >= 0:
            self.experiment_combo.setCurrentIndex(index)

    def _on_edit_clicked(self):
        """Handle edit button click"""
        experiment_name = self.experiment_combo.currentText()
        if experiment_name != "No experiments available":
            self.edit_experiment_requested.emit(experiment_name)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Experiment", "Please select an experiment to edit.")

    def _update_timers(self):
        """Update timer displays every second"""
        if self.total_experiment_time_label:
            if self.experiment_start_time:
                elapsed = time.time() - self.experiment_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                self.total_experiment_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.total_experiment_time_label.setText("00:00:00")

        if self.active_trial_time_label:
            if self.current_trial_start_time:
                elapsed = time.time() - self.current_trial_start_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                self.active_trial_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.active_trial_time_label.setText("00:00:00")

    def set_experiment_started(self):
        """Mark experiment as started"""
        self.experiment_start_time = time.time()
        # If a trial has already started but timer hasn't, start it now
        if self.current_trial_type != "None" and self.current_trial_start_time is None:
            self.current_trial_start_time = time.time()

    def set_experiment_stopped(self):
        """Mark experiment as stopped"""
        self.experiment_start_time = None
        self.current_trial_start_time = None
        self.current_trial_type = "None"
        if self.active_trial_type_label:
            self.active_trial_type_label.setText("None")

    def set_trial_started(self, trial_name):
        """Mark trial as started"""
        if not trial_name:
            return

        self.current_trial_type = trial_name
        # Only start trial timer if experiment has already started
        if self.experiment_start_time:
            self.current_trial_start_time = time.time()
        if self.active_trial_type_label:
            self.active_trial_type_label.setText(trial_name)

    def set_trial_complete(self):
        """Mark trial as complete"""
        self.current_trial_start_time = None
        if self.active_trial_time_label:
            self.active_trial_time_label.setText("00:00:00")

