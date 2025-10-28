#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QListWidget, QPushButton, QGroupBox, QMessageBox, QFileDialog,
    QComboBox, QSpinBox, QTextEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, Callable

# Import shared modules
_script_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(os.path.dirname(_script_dir))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from shared.models import Experiment, Config
from shared.managers import ExperimentManager
from shared.constants import AVAILABLE_TRIAL_TYPES


class ExperimentEditor(QDialog):
    """Experiment editor dialog for creating and editing experiments"""

    experiment_saved = pyqtSignal(object)  # Signal emitted when experiment is saved

    def __init__(self, parent=None, experiment_manager: Optional[ExperimentManager] = None,
                 current_experiment: Optional[Experiment] = None,
                 on_experiment_save: Optional[Callable] = None):
        super().__init__(parent)

        self.experiment_manager = experiment_manager
        self.current_experiment = current_experiment
        self.on_experiment_save = on_experiment_save

        self.setWindowTitle("Experiment Editor")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )
        self.resize(700, 650)
        self.setModal(True)

        self.create_widgets()
        self.create_layout()

        if self.current_experiment:
            self.update_ui()
        else:
            self.new_experiment()

    def create_widgets(self):
        """Create all UI widgets"""
        # Experiment info section
        self.info_group = QGroupBox("Experiment Information")
        info_layout = QFormLayout()

        self.name_field = QLineEdit()
        info_layout.addRow("Name:", self.name_field)

        self.description_field = QLineEdit()
        info_layout.addRow("Description:", self.description_field)

        self.loop_checkbox = QCheckBox("Loop experiment when completed")
        info_layout.addRow(self.loop_checkbox)

        self.info_group.setLayout(info_layout)

        # Main content layout (trials on left, config on right)
        content_layout = QHBoxLayout()

        # Left panel - Timeline Management
        self.timeline_group = QGroupBox("Timeline Management")
        timeline_layout = QVBoxLayout()

        # Trial list
        self.trial_list = QListWidget()
        self.trial_list.setMaximumWidth(250)
        self.trial_list.currentRowChanged.connect(self.on_trial_selected)
        timeline_layout.addWidget(QLabel("Trials:"))
        timeline_layout.addWidget(self.trial_list)

        # Trial control buttons
        button_layout = QHBoxLayout()
        self.add_trial_btn = QPushButton("Add Trial")
        self.remove_trial_btn = QPushButton("Remove Trial")
        self.move_up_btn = QPushButton("Move Up")
        self.move_down_btn = QPushButton("Move Down")

        button_layout.addWidget(self.add_trial_btn)
        button_layout.addWidget(self.remove_trial_btn)
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)

        timeline_layout.addLayout(button_layout)
        self.timeline_group.setLayout(timeline_layout)

        # Right panel - Experiment Configuration
        self.config_group = QGroupBox("Experiment Configuration")
        config_layout = QVBoxLayout()

        # Config fields
        self.config_fields = QFormLayout()
        self.config_widgets = {}

        config_fields = [
            ("iti_minimum", "ITI Minimum (ms):", 100),
            ("iti_maximum", "ITI Maximum (ms):", 1000),
            ("response_limit", "Response Limit (ms):", 1000),
            ("cue_minimum", "Cue Minimum (ms):", 5000),
            ("cue_maximum", "Cue Maximum (ms):", 10000),
            ("hold_minimum", "Hold Minimum (ms):", 100),
            ("hold_maximum", "Hold Maximum (ms):", 1000),
            ("valve_open", "Valve Open (ms):", 100),
            ("punish_time", "Punishment Time (ms):", 1000)
        ]

        for field, label, default in config_fields:
            spin_box = QSpinBox()
            spin_box.setMinimum(0)
            spin_box.setMaximum(999999)
            spin_box.setValue(default)
            self.config_fields.addRow(label, spin_box)
            self.config_widgets[field] = spin_box

        config_layout.addLayout(self.config_fields)

        # Reset config button
        reset_btn = QPushButton("Reset to Defaults")
        config_layout.addWidget(reset_btn)

        # Validation
        config_layout.addWidget(QLabel("Validation:"))
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(80)
        config_layout.addWidget(self.validation_text)

        self.config_group.setLayout(config_layout)

        # Combine panels
        content_layout.addWidget(self.timeline_group)
        content_layout.addWidget(self.config_group)

        # Action buttons
        self.action_layout = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.load_btn = QPushButton("Load")
        self.save_btn = QPushButton("Save")
        self.export_btn = QPushButton("Export")

        self.action_layout.addWidget(self.new_btn)
        self.action_layout.addWidget(self.load_btn)
        self.action_layout.addWidget(self.save_btn)
        self.action_layout.addWidget(self.export_btn)
        self.action_layout.addStretch()

        # Connect signals
        self.add_trial_btn.clicked.connect(self.add_trial)
        self.remove_trial_btn.clicked.connect(self.remove_trial)
        self.move_up_btn.clicked.connect(self.move_trial_up)
        self.move_down_btn.clicked.connect(self.move_trial_down)
        reset_btn.clicked.connect(self.reset_config_to_defaults)
        self.new_btn.clicked.connect(self.new_experiment)
        self.load_btn.clicked.connect(self.load_experiment)
        self.save_btn.clicked.connect(self.save_experiment)
        self.export_btn.clicked.connect(self.export_experiment)

    def create_layout(self):
        """Create the main layout"""
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.info_group)

        # Content area with side-by-side panels
        content_widget = QVBoxLayout()
        row_layout = QHBoxLayout()

        row_layout.addWidget(self.timeline_group)
        row_layout.addWidget(self.config_group)

        content_widget.addLayout(row_layout)
        main_layout.addLayout(content_widget)

        main_layout.addLayout(self.action_layout)

        self.setLayout(main_layout)

    def new_experiment(self):
        """Create a new experiment"""
        config = Config()
        self.current_experiment = Experiment(name="New Experiment", config=config)
        self.update_ui()

    def load_experiment(self):
        """Load an existing experiment"""
        if not self.experiment_manager:
            QMessageBox.warning(self, "No Manager", "Experiment manager not available.")
            return

        experiment_names = self.experiment_manager.list_experiments()
        if not experiment_names:
            QMessageBox.information(self, "No Experiments", "No saved experiments found.")
            return

        # Show selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Experiment")
        dialog.resize(250, 200)
        layout = QVBoxLayout()

        label = QLabel("Select an experiment to load:")
        layout.addWidget(label)

        listbox = QListWidget()
        for name in experiment_names:
            listbox.addItem(name)
        layout.addWidget(listbox)

        button_layout = QHBoxLayout()

        def on_load():
            items = listbox.selectedItems()
            if items:
                experiment_name = items[0].text()
                experiment = self.experiment_manager.load_experiment(experiment_name)
                if experiment:
                    self.current_experiment = experiment
                    self.update_ui()
                    dialog.accept()

        load_btn = QPushButton("Load")
        cancel_btn = QPushButton("Cancel")
        load_btn.clicked.connect(on_load)
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(load_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        if dialog.exec():
            pass

    def save_experiment(self):
        """Save the current experiment"""
        if not self.current_experiment:
            return

        self.update_experiment_from_ui()

        is_valid, errors = self.current_experiment.validate()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error",
                                "Experiment validation failed:\n" + "\n".join(errors))
            return

        if self.experiment_manager and self.experiment_manager.save_experiment(self.current_experiment):
            QMessageBox.information(self, "Success",
                                  f"Experiment '{self.current_experiment.name}' saved successfully.")
            if self.on_experiment_save:
                self.on_experiment_save(self.current_experiment)
            self.experiment_saved.emit(self.current_experiment)
        else:
            QMessageBox.critical(self, "Error", "Failed to save experiment.")

    def export_experiment(self):
        """Export experiment to a file"""
        if not self.current_experiment:
            return

        self.update_experiment_from_ui()

        is_valid, errors = self.current_experiment.validate()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error",
                               "Experiment validation failed:\n" + "\n".join(errors))
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Experiment",
            "",
            "JSON files (*.json);;All files (*.*)"
        )

        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.current_experiment.to_json())
                QMessageBox.information(self, "Success", f"Experiment exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export experiment: {str(e)}")

    def add_trial(self):
        """Add a new trial to the timeline"""
        # TODO: Implement add trial dialog
        pass

    def remove_trial(self):
        """Remove the selected trial"""
        # TODO: Implement remove trial
        pass

    def move_trial_up(self):
        """Move the selected trial up"""
        # TODO: Implement move trial up
        pass

    def move_trial_down(self):
        """Move the selected trial down"""
        # TODO: Implement move trial down
        pass

    def on_trial_selected(self, row):
        """Handle trial selection in listbox"""
        self.update_validation()

    def update_ui(self):
        """Update the UI to reflect the current experiment"""
        if not self.current_experiment:
            return

        self.name_field.setText(self.current_experiment.name)
        self.description_field.setText(self.current_experiment.description)
        self.loop_checkbox.setChecked(self.current_experiment.loop)

        # Update trial list
        self.trial_list.clear()
        for trial in self.current_experiment.timeline.trials:
            self.trial_list.addItem(f"{trial.id} ({trial.type})")

        # Update configuration
        for field, widget in self.config_widgets.items():
            value = getattr(self.current_experiment.config, field, 0)
            widget.setValue(value)

        self.update_validation()

    def update_experiment_from_ui(self):
        """Update the experiment from UI values"""
        if not self.current_experiment:
            return

        self.current_experiment.name = self.name_field.text().strip()
        self.current_experiment.description = self.description_field.text().strip()
        self.current_experiment.loop = self.loop_checkbox.isChecked()

        # Update configuration
        for field, widget in self.config_widgets.items():
            value = widget.value()
            setattr(self.current_experiment.config, field, value)

    def reset_config_to_defaults(self):
        """Reset all configuration fields to their default values"""
        default_config = Config()
        for field, widget in self.config_widgets.items():
            value = getattr(default_config, field, 0)
            widget.setValue(value)
        QMessageBox.information(self, "Configuration Reset",
                               "All configuration fields have been reset to their default values.")
        self.update_validation()

    def update_validation(self):
        """Update the validation display"""
        if not self.current_experiment:
            self.validation_text.clear()
            return

        is_valid, errors = self.current_experiment.validate()

        self.validation_text.clear()
        if is_valid:
            self.validation_text.setPlainText("✓ Experiment is valid")
        else:
            text = "✗ Experiment validation failed:\n"
            for error in errors:
                text += f"• {error}\n"
            self.validation_text.setPlainText(text)

