#!/usr/bin/env python3
"""
Control Panel for Behavior Box Controller
Provides a web interface for controlling and monitoring the device
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import queue
import websocket
import atexit
import time
from datetime import datetime

# Import shared modules
from shared import VERSION
from shared.constants import *
from shared.managers import CommunicationMessageParser, TestStateManager, ExperimentManager

# Import UI components
from .ui.experiment_editor import ExperimentEditor

class ControlPanel(tk.Frame):
  def __init__(self, master=None):
      super().__init__(master)
      self.master = master

      # Create a queue for input states
      self.input_queue = queue.Queue()

      # Connection state
      self.is_connected = False
      self.device_version = "unknown"

      # Experiment management
      base_dir = os.path.dirname(os.path.abspath(__file__))
      self.experiment_manager = ExperimentManager(os.path.join(base_dir, "experiments"))
      self.current_experiment = None
      self.experiment_uploaded_to_device = False

      # UI variables
      self.ip_address_var = tk.StringVar(self.master, "localhost")
      self.port_var = tk.StringVar(self.master, "8765")
      self.animal_id_var = tk.StringVar(self.master, "")
      self.animal_id_var.trace_add("write", self.on_animal_id_change)
      self.punishment_duration_var = tk.StringVar(self.master, "1000")
      self.water_delivery_duration_var = tk.StringVar(self.master, "2000")

      # Test state management
      self.test_state_manager = TestStateManager()

      self.input_states = {
        "left_lever": False,
        "right_lever": False,
        "nose_poke": False,
        "water_port": False,
        "nose_light": False,
      }

      self.input_label_states = {
        "left_lever": tk.BooleanVar(self.master, False),
        "right_lever": tk.BooleanVar(self.master, False),
        "nose_poke": tk.BooleanVar(self.master, False),
        "nose_light": tk.BooleanVar(self.master, False),
      }

      # Statistics tracking
      self.statistics = {
        "nose_pokes": 0,
        "left_lever_presses": 0,
        "right_lever_presses": 0,
        "trial_count": 0,
        "water_deliveries": 0
      }

      # Configure source-specific colors
      self.source_colors = {
        "UI": "#0066CC",
        "DEVICE": "#CC6600",
        "SYSTEM": "#666666"
      }

      # Track which sources are enabled for logging
      self.enabled_sources = {
        "UI": tk.BooleanVar(value=True),
        "DEVICE": tk.BooleanVar(value=True),
        "SYSTEM": tk.BooleanVar(value=True)
      }

      # Store log history for filtering
      self.log_history = []

      # Set version from shared module
      self.version = VERSION

      # Create the layout
      self.create_layout()

      # Initialize experiment list after UI is created
      self.update_experiment_list()

      # Configure log text tags for different states and sources
      self.console.tag_configure("info", foreground="#E0E0E0")  # Light gray for info
      self.console.tag_configure("success", foreground="#00FF00")  # Bright green for success
      self.console.tag_configure("error", foreground="#FF4444")  # Bright red for error
      self.console.tag_configure("warning", foreground="#FFAA00")  # Bright orange for warning
      self.console.tag_configure("debug", foreground="#AAAAAA")  # Medium gray for debug

      # Configure source tags
      for source, color in self.source_colors.items():
        self.console.tag_configure(f"source_{source}", foreground=color, font=("TkDefaultFont", 9, "bold"))

      # Handle exiting
      atexit.register(self.on_exit)

  def create_state_indicator(self, parent, label_text, var):
    """
    Creates a state indicator with a label and colored circle.

    Parameters:
    parent: The parent widget
    label_text (str): The text to display
    var (tk.BooleanVar): The variable to track
    """
    frame = tk.Frame(parent, bg="#f0f0f0", padx=5, pady=3)  # Light gray background
    frame.pack(side=tk.TOP, fill=tk.X, expand=True, pady=2)
    frame.grid_columnconfigure(0, weight=1)  # Make the label column expandable

    label = tk.Label(
      frame,
      text=label_text,
      font=("Arial", 11, "bold"),
      bg="#f0f0f0",
      anchor="w"
    )
    label.grid(row=0, column=0, sticky="w", padx=(0, 5))

    # State indicator (circle)
    indicator = tk.Canvas(frame, width=15, height=15, bg="#f0f0f0", highlightthickness=0)
    indicator.grid(row=0, column=1, sticky="e")

    # Function to update indicator
    def update_indicator(*args):
      state = var.get()
      color = "green" if state else "red"
      indicator.delete("all")
      indicator.create_oval(2, 2, 13, 13, fill=color, outline="")

    # Initial state and trace
    var.trace_add("write", update_indicator)
    update_indicator()

    return frame

  def create_test_row(self, parent, label_text, command_name, has_duration_input=False):
    """
    Creates a test row with a label, indicator, optional duration input, and test button.

    Parameters:
    parent: The parent widget
    label_text (str): The text to display
    command_name (str): The command to execute when the test button is clicked
    has_duration_input (bool): Whether to include a duration input field
    """
    # Container frame for the entire row
    container_frame = tk.Frame(parent)
    container_frame.pack(side=tk.TOP, fill=tk.X, expand=True, pady=2)

    # Colored background frame for label, optional duration input, and indicator
    colored_frame = tk.Frame(container_frame, bg="#f0f0f0", padx=5, pady=3)
    colored_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    colored_frame.grid_columnconfigure(0, weight=1)  # Make the label column expandable

    label = tk.Label(
      colored_frame,
      text=label_text.replace("Test ", ""),
      font=("Arial", 11, "bold"),
      bg="#f0f0f0",
      anchor="w"
    )
    label.grid(row=0, column=0, sticky="w", padx=(0, 5))

    # Duration input (if requested)
    duration_var = None
    if has_duration_input:
      duration_frame = tk.Frame(colored_frame, bg="#f0f0f0")
      duration_frame.grid(row=0, column=1, sticky="e", padx=(0, 5))

      # Duration label and input
      tk.Label(duration_frame, text="Duration (ms):", font="Arial 9", bg="#f0f0f0").pack(side=tk.LEFT, padx=(0, 2))
      duration_var = tk.StringVar(value="2000")  # Default 2000ms
      duration_entry = tk.Entry(duration_frame, textvariable=duration_var, width=6, font="Arial 9")
      duration_entry.pack(side=tk.LEFT, padx=(0, 5))

    # State indicator (circle)
    indicator = tk.Canvas(colored_frame, width=15, height=15, bg="#f0f0f0", highlightthickness=0)
    indicator.grid(row=0, column=2 if has_duration_input else 1, sticky="e")

    # Test button in the container frame
    if has_duration_input:
      button = tk.Button(
        container_frame,
        text="Test",
        font="Arial 10",
        command=lambda: self.execute_command(f"{command_name} {duration_var.get()}"),
        state=tk.DISABLED
      )
    else:
      button = tk.Button(
        container_frame,
        text="Test",
        font="Arial 10",
        command=lambda: self.execute_command(command_name),
        state=tk.DISABLED
      )
    button.pack(side=tk.RIGHT, padx=(5, 0))

    # Function to update indicator
    def update_indicator(*args):
      state = self.test_state_manager.get_test_state(command_name)
      if state == TEST_STATES["FAILED"]:
        color = "red"
      elif state == TEST_STATES["PASSED"]:
        color = "green"
      elif state == TEST_STATES["RUNNING"]:
        color = "yellow"
      else:  # NOT_TESTED
        color = "blue"
      indicator.delete("all")
      indicator.create_oval(2, 2, 13, 13, fill=color, outline="")

    # Store the update function and indicator for later use
    self.test_indicators[command_name] = {
      "indicator": indicator,
      "update": update_indicator,
      "button": button
    }

    # Store duration input reference if it exists
    if has_duration_input:
      self.test_indicators[command_name]["duration_entry"] = duration_entry

    # Initial state
    update_indicator()

    return container_frame

  def create_layout(self):
    """
    Creates the layout of the control panel.
    """
    # Initialize test indicators dictionary
    self.test_indicators = {}

    # Configure the grid
    self.master.grid_columnconfigure(0, weight=1) # Left column (status)
    self.master.grid_columnconfigure(1, weight=1) # Right column (experiment)

    # Set the UI to resize with the window
    self.master.grid_propagate(True)

    # Create a main container frame with padding
    main_frame = tk.Frame(self.master, padx=PADDING, pady=PADDING)
    main_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # Connection section with border
    connection_frame = tk.LabelFrame(main_frame, text="Connection", padx=SECTION_PADDING, pady=SECTION_PADDING)
    connection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, PADDING))

    # Connection controls
    tk.Label(connection_frame, text="IP Address:").pack(side=tk.LEFT, padx=(0, 5))
    tk.Entry(connection_frame, textvariable=self.ip_address_var, width=15).pack(side=tk.LEFT, padx=(0, 15))
    tk.Label(connection_frame, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
    tk.Entry(connection_frame, textvariable=self.port_var, width=6).pack(side=tk.LEFT, padx=(0, 15))
    self.connect_button = tk.Button(connection_frame, text="Connect", font="Arial 10", command=self.connect_to_device)
    self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
    self.disconnect_button = tk.Button(connection_frame, text="Disconnect", font="Arial 10", command=self.disconnect_from_device, state=tk.DISABLED)
    self.disconnect_button.pack(side=tk.LEFT, padx=(0, 15))

    # Version information
    version_frame = tk.LabelFrame(connection_frame, text="Versions", font=("Arial", 9), fg="gray", padx=5, pady=2)
    version_frame.pack(side=tk.RIGHT, padx=(15, 0))
    tk.Label(version_frame, text=f"Control Panel: {self.version}", font=("Arial", 9), fg="gray").pack(side=tk.TOP, anchor="w")
    self.device_version_label = tk.Label(version_frame, text="Device: unknown", font=("Arial", 9), fg="gray")
    self.device_version_label.pack(side=tk.BOTTOM, anchor="w")

    # Main content area
    content_frame = tk.Frame(main_frame)
    content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

    # Left column - Status Information
    status_frame = tk.Frame(content_frame)
    status_frame.grid(row=0, column=0, sticky="n", padx=(0, PADDING))

    # Statistics section
    statistics_frame = tk.LabelFrame(status_frame, text="Experiment Statistics", padx=SECTION_PADDING, pady=SECTION_PADDING)
    statistics_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, PADDING))

    # Create statistics display
    self.create_statistics_display(statistics_frame)

    # Input Status section
    input_status_frame = tk.LabelFrame(status_frame, text="Input Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    input_status_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, PADDING))

    # Create input indicators
    self.create_state_indicator(input_status_frame, "Left Actuator", self.input_label_states["left_lever"])
    self.create_state_indicator(input_status_frame, "Right Actuator", self.input_label_states["right_lever"])
    self.create_state_indicator(input_status_frame, "Nose Poke", self.input_label_states["nose_poke"])
    self.create_state_indicator(input_status_frame, "Nose Light", self.input_label_states["nose_light"])

    # Test Status section
    test_status_frame = tk.LabelFrame(status_frame, text="Test Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    test_status_frame.pack(side=tk.TOP, fill=tk.X)

    # Create test rows
    self.create_test_row(test_status_frame, "Test Water Delivery", "test_water_delivery", True)
    self.create_test_row(test_status_frame, "Test Actuators", "test_actuators", False)
    self.create_test_row(test_status_frame, "Test IR", "test_ir", False)
    self.create_test_row(test_status_frame, "Test Nose Light", "test_nose_light", True)
    self.create_test_row(test_status_frame, "Test Displays", "test_displays", True)

    # Reset button
    self.reset_tests_button = tk.Button(
      test_status_frame,
      text="Reset",
      font="Arial 10",
      command=self.reset_tests,
      state=tk.DISABLED
    )
    self.reset_tests_button.pack(side=tk.RIGHT, padx=1, pady=(5, 0))

    # Right column - Experiment Management
    experiment_frame = tk.Frame(content_frame)
    experiment_frame.grid(row=0, column=1, sticky="nsew", rowspan=2)

    # Experiment Management section
    experiment_management_frame = tk.LabelFrame(experiment_frame, text="Experiment Management", padx=SECTION_PADDING, pady=SECTION_PADDING)
    experiment_management_frame.pack(side=tk.TOP, fill=tk.X)

    # Variables section
    variables_frame = tk.LabelFrame(experiment_management_frame, text="Variables", padx=8, pady=8)
    variables_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

    # Animal ID input frame
    animal_id_frame = tk.Frame(variables_frame)
    animal_id_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

    tk.Label(animal_id_frame, text="Animal ID:").pack(side=tk.LEFT, pady=0)
    self.animal_id_input = tk.Entry(animal_id_frame, textvariable=self.animal_id_var, state=tk.DISABLED)
    self.animal_id_input.pack(side=tk.LEFT, pady=0, fill=tk.X, expand=True)

    # Duration settings frame
    duration_settings_frame = tk.Frame(variables_frame)
    duration_settings_frame.pack(side=tk.TOP, fill=tk.X)

    # Punishment duration input
    punishment_frame = tk.Frame(duration_settings_frame)
    punishment_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    tk.Label(punishment_frame, text="Punishment Duration (ms):").pack(side=tk.LEFT, pady=0)
    self.punishment_duration_input = tk.Entry(punishment_frame, textvariable=self.punishment_duration_var, width=8, state=tk.DISABLED)
    self.punishment_duration_input.pack(side=tk.LEFT, pady=0, padx=(5, 0))

    # Water delivery duration input
    water_delivery_frame = tk.Frame(duration_settings_frame)
    water_delivery_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    tk.Label(water_delivery_frame, text="Water Delivery Duration (ms):").pack(side=tk.LEFT, pady=0)
    self.water_delivery_duration_input = tk.Entry(water_delivery_frame, textvariable=self.water_delivery_duration_var, width=8, state=tk.DISABLED)
    self.water_delivery_duration_input.pack(side=tk.LEFT, pady=0, padx=(5, 0))

    # Experiment section
    experiment_section_frame = tk.LabelFrame(experiment_management_frame, text="Experiment", padx=8, pady=8)
    experiment_section_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

    # Experiment selection
    experiment_selection_frame = tk.Frame(experiment_section_frame)
    experiment_selection_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    tk.Label(experiment_selection_frame, text="Experiment:").pack(side=tk.LEFT, pady=0)
    self.experiment_var = tk.StringVar()
    self.experiment_combo = ttk.Combobox(experiment_selection_frame, textvariable=self.experiment_var, state="readonly", width=18)
    self.experiment_combo.pack(side=tk.LEFT, pady=0, padx=(5, 0))
    self.experiment_combo.bind("<<ComboboxSelected>>", self.on_experiment_selected)

    # Experiment buttons
    experiment_buttons_frame = tk.Frame(experiment_section_frame)
    experiment_buttons_frame.pack(side=tk.TOP, fill=tk.X)

    self.new_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="New Experiment",
      font="Arial 10",
      command=self.create_new_experiment,
      state=tk.NORMAL
    )
    self.new_experiment_button.pack(side=tk.LEFT, padx=(0, 5), pady=0)

    self.experiment_editor_button = tk.Button(
      experiment_buttons_frame,
      text="Edit Experiment",
      font="Arial 10",
      command=self.open_experiment_editor,
      state=tk.DISABLED
    )
    self.experiment_editor_button.pack(side=tk.LEFT, padx=(0, 5), pady=0)

    # Experiment buttons frame
    experiment_buttons_frame = tk.Frame(experiment_management_frame)
    experiment_buttons_frame.pack(side=tk.TOP, fill=tk.X)

    self.start_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="Start",
      font="Arial 10",
      command=self.start_experiment,
      state=tk.DISABLED
    )
    self.start_experiment_button.pack(side=tk.RIGHT, padx=2, pady=0)

    self.stop_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="Stop",
      font="Arial 10",
      command=lambda: self.execute_command("stop_experiment"),
      state=tk.DISABLED
    )
    self.stop_experiment_button.pack(side=tk.RIGHT, padx=2, pady=0)

    # Console section
    console_frame = tk.LabelFrame(experiment_frame, text="Console", padx=SECTION_PADDING, pady=SECTION_PADDING)
    console_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    console_frame.grid_columnconfigure(0, weight=1)
    console_frame.grid_rowconfigure(0, weight=1)

    self.console = tk.Text(console_frame, font="Arial 10", wrap=tk.NONE, bg="black", fg="#E0E0E0", height=14)
    self.console.grid(row=0, column=0, sticky="nsew")
    self.console.config(state=tk.DISABLED)

    # Store references to test buttons for later use
    self.test_water_delivery_button = self.test_indicators["test_water_delivery"]["button"]
    self.test_actuators_button = self.test_indicators["test_actuators"]["button"]
    self.test_ir_button = self.test_indicators["test_ir"]["button"]
    self.test_nose_light_button = self.test_indicators["test_nose_light"]["button"]
    self.test_displays_button = self.test_indicators["test_displays"]["button"]

  def log(self, message, state="info", source="UI"):
    """
    Logs a message to the console with a timestamp.

    Parameters:
    message (str): The message to log.
    state (str): The state of the message.
    source (str): The source of the message.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    source_upper = source.upper()

    # Store log entry in history
    log_entry = {
      "timestamp": timestamp,
      "source": source_upper,
      "state": state,
      "message": message
    }
    self.log_history.append(log_entry)

    # Only display if source is enabled
    if self.enabled_sources[source_upper].get():
      self.console.config(state=tk.NORMAL)

      # Insert timestamp
      self.console.insert(tk.END, f"[{timestamp}] ", "info")

      # Insert source with custom color
      self.console.insert(tk.END, f"[{source_upper}] ", f"source_{source_upper}")

      # Insert state and message
      self.console.insert(tk.END, f"[{LOG_STATES[state]}] {message}\n", state)

      # Scroll to end and make read-only
      self.console.see(tk.END)
      self.console.config(state=tk.DISABLED)

    # Always print to console for backup
    print(f"[{timestamp}] [{source_upper}] [{LOG_STATES[state]}] {message}")

  def update_state_labels(self):
    """
    Updates the state labels for the input states.
    """
    self.input_label_states["left_lever"].set(self.input_states["left_lever"])
    self.input_label_states["right_lever"].set(self.input_states["right_lever"])
    self.input_label_states["nose_poke"].set(self.input_states["nose_poke"])
    self.input_label_states["nose_light"].set(self.input_states["nose_light"])

  def update_test_state(self, command_name, state):
      """
      Updates the state of a test.

      Parameters:
      command_name (str): The name of the command to update.
      state (int): The state to set the command to.
      """
      self.test_state_manager.set_test_state(command_name, state)
      self.update_test_state_indicators()

  def update_test_state_indicators(self):
    """
    Updates the state indicators for the test states.
    """
    for command_name in self.test_state_manager.get_all_test_states():
      if command_name in self.test_indicators:
          self.test_indicators[command_name]["update"]()

  def set_test_buttons_disabled(self, disabled):
    """
    Disables or enables the test buttons and duration inputs.

    Parameters:
    disabled (bool): Whether to disable the test buttons and duration inputs.
    """
    # Disable test buttons
    if disabled:
      self.test_ir_button.config(state=tk.DISABLED)
      self.test_actuators_button.config(state=tk.DISABLED)
      self.test_water_delivery_button.config(state=tk.DISABLED)
      self.test_nose_light_button.config(state=tk.DISABLED)
      self.test_displays_button.config(state=tk.DISABLED)

      # Disable duration inputs
      if "test_water_delivery" in self.test_indicators and "duration_entry" in self.test_indicators["test_water_delivery"]:
        self.test_indicators["test_water_delivery"]["duration_entry"].config(state=tk.DISABLED)
      if "test_nose_light" in self.test_indicators and "duration_entry" in self.test_indicators["test_nose_light"]:
        self.test_indicators["test_nose_light"]["duration_entry"].config(state=tk.DISABLED)
      if "test_displays" in self.test_indicators and "duration_entry" in self.test_indicators["test_displays"]:
        self.test_indicators["test_displays"]["duration_entry"].config(state=tk.DISABLED)
    else:
      # Enable test buttons
      self.test_ir_button.config(state=tk.NORMAL)
      self.test_actuators_button.config(state=tk.NORMAL)
      self.test_water_delivery_button.config(state=tk.NORMAL)
      self.test_nose_light_button.config(state=tk.NORMAL)
      self.test_displays_button.config(state=tk.NORMAL)

      # Enable duration inputs
      if "test_water_delivery" in self.test_indicators and "duration_entry" in self.test_indicators["test_water_delivery"]:
        self.test_indicators["test_water_delivery"]["duration_entry"].config(state=tk.NORMAL)
      if "test_nose_light" in self.test_indicators and "duration_entry" in self.test_indicators["test_nose_light"]:
        self.test_indicators["test_nose_light"]["duration_entry"].config(state=tk.NORMAL)
      if "test_displays" in self.test_indicators and "duration_entry" in self.test_indicators["test_displays"]:
        self.test_indicators["test_displays"]["duration_entry"].config(state=tk.NORMAL)

  def set_experiment_buttons_disabled(self, disabled):
    """
    Disables or enables the experiment buttons.
    When Start is enabled, Stop is disabled and vice versa.

    Parameters:
    disabled (bool): Whether to disable the Start button and enable the Stop button.
    """
    if disabled:
      # Disable Start button and enable Stop button
      self.start_experiment_button.config(state=tk.DISABLED)
      self.stop_experiment_button.config(state=tk.NORMAL)
    else:
      # Enable Start button and disable Stop button
      self.start_experiment_button.config(state=tk.NORMAL)
      self.stop_experiment_button.config(state=tk.DISABLED)

  def on_animal_id_change(self, *args):
    """
    Enables the start experiment button only if animal_id_input is not empty and experiment is selected.
    """
    animal_id = self.animal_id_var.get().strip()
    if animal_id and self.is_connected:
      # For experiment experiments, require both animal ID and a experiment to be selected
      if self.current_experiment:
        self.start_experiment_button.config(state=tk.NORMAL)
      else:
        # No experiment selected, disable start button
        self.start_experiment_button.config(state=tk.DISABLED)
    else:
      self.start_experiment_button.config(state=tk.DISABLED)

  def parse_message(self, message):
    """
    Parses a message from the device.

    Parameters:
    message (str): The message to parse.
    """
    return CommunicationMessageParser.parse_message(message)

  def on_connect(self):
    """
    Enables all buttons and sets the connection state to connected.
    """
    self.is_connected = True
    self.log("Connected to the device", "success")

    # Enable all buttons
    self.connect_button.config(state=tk.DISABLED)

    # Test buttons
    self.test_water_delivery_button.config(state=tk.NORMAL)
    self.test_actuators_button.config(state=tk.NORMAL)
    self.test_ir_button.config(state=tk.NORMAL)
    self.test_nose_light_button.config(state=tk.NORMAL)
    self.test_displays_button.config(state=tk.NORMAL)
    self.reset_tests_button.config(state=tk.NORMAL)  # Enable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.NORMAL)

    # Duration inputs
    self.punishment_duration_input.config(state=tk.NORMAL)
    self.water_delivery_duration_input.config(state=tk.NORMAL)

    # Experiment buttons - always enabled for experiment management
    self.new_experiment_button.config(state=tk.NORMAL)
    self.experiment_editor_button.config(state=tk.NORMAL)
    self.update_experiment_list()

    # Disconnect button
    self.disconnect_button.config(state=tk.NORMAL)

    # Update start button state based on current conditions
    self.on_animal_id_change()

  def on_disconnect(self):
    """
    Resets the state of the control panel and disables all buttons.
    Called when the connection is lost or manually disconnected.
    """
    self.reset_state()

    self.is_connected = False

    # Enable connect button and disable disconnect button
    self.connect_button.config(state=tk.NORMAL)
    self.disconnect_button.config(state=tk.DISABLED)

    # Test buttons
    self.test_water_delivery_button.config(state=tk.DISABLED)
    self.test_actuators_button.config(state=tk.DISABLED)
    self.test_ir_button.config(state=tk.DISABLED)
    self.test_nose_light_button.config(state=tk.DISABLED)
    self.test_displays_button.config(state=tk.DISABLED)
    self.reset_tests_button.config(state=tk.DISABLED)  # Disable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.DISABLED)

    # Duration inputs
    self.punishment_duration_input.config(state=tk.DISABLED)
    self.water_delivery_duration_input.config(state=tk.DISABLED)

    # Experiment buttons - keep enabled for experiment management
    self.new_experiment_button.config(state=tk.NORMAL)
    self.experiment_editor_button.config(state=tk.NORMAL)

    # Experiment buttons
    self.start_experiment_button.config(state=tk.DISABLED)
    self.stop_experiment_button.config(state=tk.DISABLED)

    # Reset device version display
    self.device_version = "unknown"
    self.device_version_label.config(text="Device: unknown")

    self.log("Disconnected from the device", "info")

  def on_message(self, ws, message):
    """
    Handles incoming messages from the WebSocket.

    Parameters:
    ws (websocket.WebSocketApp): The WebSocket application.
    message (str): The message to handle.
    """
    received_message = self.parse_message(message)
    if received_message:
      # Check if the device version has changed
      if "version" in received_message:
        new_version = received_message["version"]
        if new_version != self.device_version:
          self.device_version = new_version
          self.device_version_label.config(text=f"Device: {self.device_version}")
          self.log(f"Device version: {self.device_version}", "info", "SYSTEM")

      # Handle other message types
      if received_message["type"] == "input_state":
        # Update input states
        self.input_states = received_message["data"]
        self.update_state_labels()
      elif received_message["type"] == "statistics":
        # Update statistics
        self.statistics = received_message["data"]
        self.update_statistics(self.statistics)
      elif received_message["type"] == "test_state":
        # Update test states
        for test_name, test_data in received_message["data"].items():
          if test_name in self.test_state_manager.get_all_test_states():
            self.test_state_manager.set_test_state(test_name, test_data["state"])
            if test_data["state"] in [TEST_STATES["PASSED"], TEST_STATES["FAILED"]]:
              self.set_test_buttons_disabled(False)
        self.update_test_state_indicators()
      elif received_message["type"] == "experiment_status":
        # Update experiment status
        status = received_message["data"]["status"]
        self.log(f"Experiment status: {status}", "info")
        if status == "started":
          self.set_experiment_buttons_disabled(True)
          self.reset_statistics_display()
        elif status == "completed" or status == "stopped":
          self.set_experiment_buttons_disabled(False)
      elif received_message["type"] == "trial_start":
        # Update trial start
        self.log(f"Trial start: {received_message['data']['trial']}", "info")
      elif received_message["type"] == "trial_complete":
        # Update trial complete
        self.log(f"Trial complete: {received_message['data']['trial']}", "success")
      elif received_message["type"] == "device_log":
        # Update device log
        self.log(received_message["data"]["message"], received_message["data"]["state"], "device")
      elif received_message["type"] == "experiment_validation":
        # Update experiment validation
        success = received_message.get("success", False)
        message = received_message.get("message", "")
        if success:
          self.log(f"Experiment validation: {message}", "success")
          self.experiment_uploaded_to_device = True
        else:
          self.log(f"Experiment validation failed: {message}", "error")
          self.experiment_uploaded_to_device = False
      elif received_message["type"] == "experiment_error":
        message = received_message.get("message", "")
        self.log(f"Experiment error: {message}", "error")
      else:
        self.log(f"Received unhandled message: {received_message}", "warning")

  def on_error(self, ws, error):
    """
    Handles errors from the WebSocket.

    Parameters:
    ws (websocket.WebSocketApp): The WebSocket application.
    error (str): The error to handle.
    """
    self.log(f"WebSocket error: {error}", "error")

    # Disconnect from the device
    self.on_disconnect()

  def on_close(self, ws):
    """
    Handles the closing of the WebSocket connection.

    Parameters:
    ws (websocket.WebSocketApp): The WebSocket application.
    """
    self.log("Connection closed", "info")

    # Disconnect from the device
    self.on_disconnect()

  def send_command(self, command):
    """
    Sends a command to the device via WebSocket.

    Parameters:
    command (str): The command to send.
    """
    self.ws.send(command)

  def on_exit(self):
    """
    Closes the WebSocket connection and joins the WebSocket thread.
    """
    self.ws.close()  # Close WebSocket connection
    if hasattr(self, "ws_thread") and self.ws_thread is not None:
      self.ws_thread.join()

  def execute_command(self, command):
    """
    Executes a command on the device.

    Parameters:
    command (str): The entire command to execute.
    """
    base_command, parameters = CommunicationMessageParser.parse_test_command(command)

    if base_command in TEST_COMMANDS:
      self.send_command(command)
      self.update_test_state(base_command, TEST_STATES["RUNNING"])
      self.set_test_buttons_disabled(True)
    elif base_command in EXPERIMENT_COMMANDS:
      self.send_command(command)
      if base_command == "stop_experiment":
        self.set_experiment_buttons_disabled(False)
      else:
        self.set_experiment_buttons_disabled(True)
    else:
      self.log(f"Invalid command: {command}", "error")

  def connect_to_device(self):
    """
    Connects to the device.
    """
    if not self.is_connected:
      ip_address = self.ip_address_var.get()
      port = self.port_var.get()
      websocket_url = f"ws://{ip_address}:{port}"

    # Attempt to connect to the WebSocket service for 10 seconds
    self.log(f"Attempting to connect to {websocket_url}", "info")
    self.ws = websocket.WebSocketApp(websocket_url,
                                        on_message=self.on_message,
                                        on_error=self.on_error,
                                        on_close=self.on_close)
    self.ws_thread = threading.Thread(target=self.run_websocket)
    self.ws_thread.start()

    # Wait for connection attempt
    for _ in range(20):
      if self.ws.sock and self.ws.sock.connected:
        self.on_connect()
        return
      time.sleep(0.5)

    self.log("Failed to connect to the device within 10 seconds", "error")

  def disconnect_from_device(self):
    """
    Disconnects from the device.
    """
    self.disconnect_button.config(state=tk.DISABLED)
    self.animal_id_input.config(state=tk.DISABLED)

    self.reset_tests()
    self.ws.close()

    self.log("Disconnected from the device", "success")

  def reset_tests(self):
    """
    Resets all test states and indicators to their initial state.
    """
    # Reset test states
    self.test_state_manager.reset_test_states()

    # Reset the status icons
    self.update_test_state_indicators()

    # Enable test buttons if connected
    if self.is_connected:
      self.set_test_buttons_disabled(False)

  def reset_state(self):
    """
    Resets the state of the control panel.
    """
    self.is_connected = False
    self.input_states = {
      "left_lever": False,
      "right_lever": False,
      "nose_poke": False,
      "water_port": False,
      "nose_light": False,
    }

    # Reset experiment upload state
    self.experiment_uploaded_to_device = False

    self.reset_tests()

  def run_websocket(self):
    self.ws.run_forever()

  def update_experiment_list(self):
    """Update the experiment dropdown with available experiments"""
    experiments = self.experiment_manager.list_experiments()
    self.experiment_combo['values'] = experiments
    if experiments and not self.experiment_var.get():
      self.experiment_var.set(experiments[0])
      self.on_experiment_selected()
    elif not experiments:
      self.experiment_var.set("")
      self.current_experiment = None
      self.experiment_uploaded_to_device = False
      self.experiment_editor_button.config(state=tk.DISABLED)
      self.on_animal_id_change()

  def on_experiment_selected(self, event=None):
    """Handle experiment selection"""
    selected_experiment = self.experiment_var.get()
    if selected_experiment:
      self.current_experiment = self.experiment_manager.load_experiment(selected_experiment)
      self.log(f"Selected experiment: {selected_experiment}", "info")
      self.experiment_uploaded_to_device = False
      self.experiment_editor_button.config(state=tk.NORMAL)
      self.on_animal_id_change()
    else:
      self.current_experiment = None
      self.experiment_uploaded_to_device = False
      self.experiment_editor_button.config(state=tk.DISABLED)
      self.start_experiment_button.config(state=tk.DISABLED)

  def create_new_experiment(self):
    """Create a new experiment and open it in the editor"""
    # Create a new experiment with a default name
    experiment = self.experiment_manager.create_experiment("New Experiment")

    # Open the editor with the new experiment
    editor = ExperimentEditor(self.master, self.experiment_manager, self.on_experiment_saved)
    editor.current_experiment = experiment
    editor.update_ui()
    editor.grab_set()  # Make modal

  def open_experiment_editor(self):
    """Open the experiment editor window with the selected experiment"""
    if not self.current_experiment:
      messagebox.showerror("No Experiment", "Please select an experiment to edit.")
      return

    editor = ExperimentEditor(self.master, self.experiment_manager, self.on_experiment_saved)
    editor.current_experiment = self.current_experiment
    editor.update_ui()
    editor.grab_set()  # Make modal

  def on_experiment_saved(self, experiment):
    """Handle experiment save from editor"""
    self.update_experiment_list()
    if experiment.name == self.experiment_var.get():
      self.current_experiment = experiment
    self.log(f"Experiment '{experiment.name}' saved", "success")

    # Update button states
    self.on_animal_id_change()

  def start_experiment(self):
    """Start an experiment"""
    if not self.is_connected:
      messagebox.showerror("Not Connected", "Please connect to the device first.")
      return

    animal_id = self.animal_id_var.get().strip()
    if not animal_id:
      messagebox.showerror("No Animal ID", "Please enter an animal ID.")
      return

    # Check if we have a experiment selected (additional safety check)
    if not self.current_experiment:
      messagebox.showerror("No Experiment", "Please select an experiment to run.")
      return

    # Automatically upload experiment if not already uploaded
    if not self.experiment_uploaded_to_device:
      self.log("Uploading experiment to device...", "info")
      try:
        # Validate experiment
        is_valid, errors = self.current_experiment.validate()
        if not is_valid:
          error_msg = "Experiment validation failed:\n" + "\n".join(errors)
          messagebox.showerror("Validation Error", error_msg)
          return

        # Send experiment upload message
        message = {
          "type": "experiment_upload",
          "data": self.current_experiment.to_dict()
        }
        self.ws.send(json.dumps(message))

        # The device will validate and store the experiment before starting
        self.log("Experiment upload initiated, starting experiment...", "info")
      except Exception as e:
        messagebox.showerror("Upload Error", f"Failed to upload experiment: {str(e)}")
        return

    # Start experiment
    try:
      # Send experiment start message
      message = {
        "type": "start_experiment",
        "animal_id": animal_id
      }
      self.ws.send(json.dumps(message))
      self.log(f"Starting experiment with animal ID: {animal_id}", "info")
    except Exception as e:
      messagebox.showerror("Start Error", f"Failed to start experiment: {str(e)}")

  def create_statistics_display(self, parent):
    """
    Creates a frame to display live statistics.
    """
    # Create a frame to hold the statistics
    stats_frame = tk.Frame(parent)
    stats_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

    # Create labels for each statistic with proper alignment
    # Nose Pokes
    nose_pokes_frame = tk.Frame(stats_frame)
    nose_pokes_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(nose_pokes_frame, text="Nose Pokes:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.nose_pokes_label = tk.Label(nose_pokes_frame, text="0", font=("Arial", 11), anchor="e")
    self.nose_pokes_label.pack(side=tk.RIGHT)

    # Left Lever Presses
    left_lever_frame = tk.Frame(stats_frame)
    left_lever_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(left_lever_frame, text="Left Lever Presses:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.left_lever_presses_label = tk.Label(left_lever_frame, text="0", font=("Arial", 11), anchor="e")
    self.left_lever_presses_label.pack(side=tk.RIGHT)

    # Right Lever Presses
    right_lever_frame = tk.Frame(stats_frame)
    right_lever_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(right_lever_frame, text="Right Lever Presses:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.right_lever_presses_label = tk.Label(right_lever_frame, text="0", font=("Arial", 11), anchor="e")
    self.right_lever_presses_label.pack(side=tk.RIGHT)

    # Trial Count
    trial_frame = tk.Frame(stats_frame)
    trial_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(trial_frame, text="Trials:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.trial_count_label = tk.Label(trial_frame, text="0", font=("Arial", 11), anchor="e")
    self.trial_count_label.pack(side=tk.RIGHT)

    # Water Deliveries
    water_frame = tk.Frame(stats_frame)
    water_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(water_frame, text="Water Deliveries:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.water_deliveries_label = tk.Label(water_frame, text="0", font=("Arial", 11), anchor="e")
    self.water_deliveries_label.pack(side=tk.RIGHT)

  def update_statistics(self, stats):
    """
    Updates the live statistics display with new values.
    """
    self.nose_pokes_label.config(text=str(stats['nose_pokes']))
    self.left_lever_presses_label.config(text=str(stats['left_lever_presses']))
    self.right_lever_presses_label.config(text=str(stats['right_lever_presses']))
    self.trial_count_label.config(text=str(stats['trial_count']))
    self.water_deliveries_label.config(text=str(stats['water_deliveries']))

  def reset_statistics_display(self):
    """
    Resets the statistics display to zero.
    """
    self.statistics = {
      "nose_pokes": 0,
      "left_lever_presses": 0,
      "right_lever_presses": 0,
      "trial_count": 0,
      "water_deliveries": 0
    }
    self.update_statistics(self.statistics)

def main():
  root = tk.Tk()
  root.title("Behavior Box: Control Panel")
  root.geometry("864x672")
  root.resizable(False, False)

  # Set window icon
  try:
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)
  except Exception:
    pass

  view = ControlPanel(root)
  view.master.title("Behavior Box: Control Panel")
  view.mainloop()

if __name__ == "__main__":
  main()
