#!/usr/bin/env python3
"""
Filename: dashboard/app.py
Author: Henry Burgess
Date: 2025-07-29
Description: Main application for the dashboard script, provides a GUI for controlling and monitoring the device
License: MIT
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

      # UI variables
      self.ip_address_var = tk.StringVar(self.master, "localhost")
      self.port_var = tk.StringVar(self.master, "8765")
      self.animal_id_var = tk.StringVar(self.master, "")
      self.animal_id_var.trace_add("write", self.on_animal_id_change)

      # Test state management
      self.test_state_manager = TestStateManager()

      self.input_states = {
        "input_lever_left": False,
        "input_lever_right": False,
        "input_ir": False,
        "input_port": False,
        "led_port": False,
        "led_lever_left": False,
        "led_lever_right": False
      }

      self.input_label_states = {
        "input_lever_left": tk.BooleanVar(self.master, False),
        "input_lever_right": tk.BooleanVar(self.master, False),
        "input_ir": tk.BooleanVar(self.master, False),
        "led_port": tk.BooleanVar(self.master, False),
        "led_lever_left": tk.BooleanVar(self.master, False),
        "led_lever_right": tk.BooleanVar(self.master, False),
      }

      # Statistics tracking
      self.statistics = {
        "nose_pokes": 0,
        "left_lever_presses": 0,
        "right_lever_presses": 0,
        "trial_count": 0,
        "water_deliveries": 0
      }

      # Experiment timing tracking
      self.experiment_start_time = None
      self.current_trial_type = "None"
      self.current_trial_start_time = None

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

      # Start timer update loop
      self.update_timers()

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
      tk.Label(duration_frame, text="Duration:", font="Arial 8", bg="#f0f0f0").pack(side=tk.LEFT, padx=(0, 2))
      duration_var = tk.StringVar(value="2000")  # Default 2000ms
      duration_entry = tk.Entry(duration_frame, textvariable=duration_var, width=4, font="Arial 8")
      duration_entry.pack(side=tk.LEFT, padx=(0, 5))

    # State indicator (circle)
    indicator = tk.Canvas(colored_frame, width=15, height=15, bg="#f0f0f0", highlightthickness=0)
    indicator.grid(row=0, column=2 if has_duration_input else 1, sticky="e")

    # Test button in the container frame
    if has_duration_input:
      button = tk.Button(
        container_frame,
        text="Test",
        font="Arial 8",
        command=lambda: self.execute_command(f"{command_name} {duration_var.get()}"),
        state=tk.DISABLED
      )
    else:
      button = tk.Button(
        container_frame,
        text="Test",
        font="Arial 8",
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
    Creates the layout of the dashboard.
    """
    # Initialize test indicators dictionary
    self.test_indicators = {}

    # Configure the grid
    self.master.grid_columnconfigure(0, weight=1)  # Left column (connection)
    self.master.grid_columnconfigure(1, weight=2)  # Right column (experiment management) - wider
    self.master.grid_rowconfigure(0, weight=0)     # Top row (connection + experiment management)
    self.master.grid_rowconfigure(1, weight=1)     # Middle row (status panels)
    self.master.grid_rowconfigure(2, weight=1)     # Bottom row (console)

    # Set the UI to resize with the window
    self.master.grid_propagate(True)

    # Create a main container frame with padding
    main_frame = tk.Frame(self.master, padx=PADDING, pady=PADDING)
    main_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # Row 0: Connection section and Experiment Management
    connection_frame = tk.LabelFrame(main_frame, text="Connection", padx=SECTION_PADDING, pady=SECTION_PADDING)
    connection_frame.grid(row=0, column=0, sticky="nsew", pady=(0, PADDING), padx=(0, PADDING//2))

    # Configure grid for connection frame
    connection_frame.grid_columnconfigure(0, weight=1)  # Left side (IP/Port/Buttons)
    connection_frame.grid_columnconfigure(1, weight=1)  # Right side (Status/Versions)

    # Left side: IP Address, Port, and Buttons
    left_frame = tk.Frame(connection_frame)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING//2))

    # IP Address
    ip_frame = tk.Frame(left_frame)
    ip_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
    tk.Label(ip_frame, text="IP Address:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    tk.Entry(ip_frame, textvariable=self.ip_address_var, width=15).pack(side=tk.LEFT, padx=(5, 0))

    # Port
    port_frame = tk.Frame(left_frame)
    port_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
    tk.Label(port_frame, text="Port:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    tk.Entry(port_frame, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=(5, 0))

    # Connect/Disconnect buttons
    buttons_frame = tk.Frame(left_frame)
    buttons_frame.pack(side=tk.TOP, fill=tk.X)
    self.connect_button = tk.Button(buttons_frame, text="Connect", font="Arial 9", command=self.connect_websocket)
    self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
    self.disconnect_button = tk.Button(buttons_frame, text="Disconnect", font="Arial 9", command=self.disconnect_from_device, state=tk.DISABLED)
    self.disconnect_button.pack(side=tk.LEFT, padx=(0, 0))

    # Right side: Status and Version information
    right_frame = tk.Frame(connection_frame)
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(PADDING//2, 0))

    # Status
    status_frame = tk.Frame(right_frame)
    status_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(status_frame, text="Status:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.connection_status_label = tk.Label(status_frame, text="Disconnected", font=("Arial", 11), anchor="e", fg="red")
    self.connection_status_label.pack(side=tk.RIGHT)

    # Dashboard Version
    cp_version_frame = tk.Frame(right_frame)
    cp_version_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(cp_version_frame, text="Dashboard Version:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.control_panel_version_label = tk.Label(cp_version_frame, text=self.version, font=("Arial", 11), anchor="e")
    self.control_panel_version_label.pack(side=tk.RIGHT)

    # Device Version
    device_version_frame = tk.Frame(right_frame)
    device_version_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(device_version_frame, text="Device Version:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.device_version_label = tk.Label(device_version_frame, text="unknown", font=("Arial", 11), anchor="e")
    self.device_version_label.pack(side=tk.RIGHT)

    # Experiment Management section
    experiment_management_frame = tk.LabelFrame(main_frame, text="Experiment Management", padx=SECTION_PADDING, pady=SECTION_PADDING)
    experiment_management_frame.grid(row=0, column=1, sticky="nsew", padx=(PADDING//2, 0), pady=(0, PADDING))

    # Animal ID input frame
    animal_id_frame = tk.Frame(experiment_management_frame)
    animal_id_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    tk.Label(animal_id_frame, text="Animal ID:").pack(side=tk.LEFT, pady=0)
    self.animal_id_input = tk.Entry(animal_id_frame, textvariable=self.animal_id_var, state=tk.DISABLED)
    self.animal_id_input.pack(side=tk.LEFT, pady=0, fill=tk.X, expand=True)

    # Experiment selection
    experiment_selection_frame = tk.Frame(experiment_management_frame)
    experiment_selection_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

    tk.Label(experiment_selection_frame, text="Experiment:").pack(side=tk.LEFT, pady=0)
    self.experiment_var = tk.StringVar()
    self.experiment_combo = ttk.Combobox(experiment_selection_frame, textvariable=self.experiment_var, state="readonly", width=20)
    self.experiment_combo.pack(side=tk.LEFT, pady=0, padx=(5, 0))
    self.experiment_combo.bind("<<ComboboxSelected>>", self.on_experiment_selected)

    # Experiment buttons
    experiment_buttons_frame = tk.Frame(experiment_management_frame)
    experiment_buttons_frame.pack(side=tk.TOP, fill=tk.X)

    self.new_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="New Experiment",
      font="Arial 9",
      command=self.create_new_experiment,
      state=tk.NORMAL
    )
    self.new_experiment_button.pack(side=tk.LEFT, padx=(0, 5), pady=0)

    self.experiment_editor_button = tk.Button(
      experiment_buttons_frame,
      text="Edit Experiment",
      font="Arial 9",
      command=self.open_experiment_editor,
      state=tk.DISABLED
    )
    self.experiment_editor_button.pack(side=tk.LEFT, padx=(0, 5), pady=0)

    self.start_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="Start",
      font="Arial 9",
      command=self.start_experiment,
      state=tk.DISABLED
    )
    self.start_experiment_button.pack(side=tk.LEFT, padx=(0, 5), pady=0)

    self.stop_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="Stop",
      font="Arial 9",
      command=lambda: self.execute_command("stop_experiment"),
      state=tk.DISABLED
    )
    self.stop_experiment_button.pack(side=tk.LEFT, padx=(0, 0), pady=0)

    # Row 1: Status panels (Input Status, Test Status, Experiment Statistics)
    status_panels_frame = tk.Frame(main_frame)
    status_panels_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, PADDING))

    # Configure grid for status panels
    status_panels_frame.grid_columnconfigure(0, weight=1)  # Input Status
    status_panels_frame.grid_columnconfigure(1, weight=2)  # Test Status (wider)
    status_panels_frame.grid_columnconfigure(2, weight=1)  # Experiment Statistics

    # Input Status section
    input_status_frame = tk.LabelFrame(status_panels_frame, text="Input Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    input_status_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING//2))

    # Create input indicators
    self.create_state_indicator(input_status_frame, "Left Lever", self.input_label_states["input_lever_left"])
    self.create_state_indicator(input_status_frame, "Left Lever Light", self.input_label_states["led_lever_left"])
    self.create_state_indicator(input_status_frame, "Right Lever", self.input_label_states["input_lever_right"])
    self.create_state_indicator(input_status_frame, "Right Lever Light", self.input_label_states["led_lever_right"])
    self.create_state_indicator(input_status_frame, "Nose Poke", self.input_label_states["input_ir"])
    self.create_state_indicator(input_status_frame, "Nose Light", self.input_label_states["led_port"])

    # Test Status section
    test_status_frame = tk.LabelFrame(status_panels_frame, text="Test Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    test_status_frame.grid(row=0, column=1, sticky="nsew", padx=(PADDING//2, PADDING//2))

    # Create test rows
    self.create_test_row(test_status_frame, "Test Water Delivery", "test_water_delivery", True)
    self.create_test_row(test_status_frame, "Test Levers", "test_input_levers", False)
    self.create_test_row(test_status_frame, "Test Lever Lights", "test_led_levers", True)
    self.create_test_row(test_status_frame, "Test IR", "test_input_ir", False)
    self.create_test_row(test_status_frame, "Test Nose Light", "test_led_port", True)
    self.create_test_row(test_status_frame, "Test Displays", "test_displays", True)

    # Reset button
    self.reset_tests_button = tk.Button(
      test_status_frame,
      text="Reset",
      font="Arial 9",
      command=self.reset_tests,
      state=tk.DISABLED
    )
    self.reset_tests_button.pack(side=tk.RIGHT, padx=1, pady=(5, 0))

    # Statistics section
    statistics_frame = tk.LabelFrame(status_panels_frame, text="Experiment Statistics", padx=SECTION_PADDING, pady=SECTION_PADDING)
    statistics_frame.grid(row=0, column=2, sticky="nsew", padx=(PADDING//2, 0))

    # Create statistics display
    self.create_statistics_display(statistics_frame)

    # Row 2: Console section
    console_frame = tk.LabelFrame(main_frame, text="Console", padx=SECTION_PADDING, pady=SECTION_PADDING)
    console_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
    console_frame.grid_columnconfigure(0, weight=1)
    console_frame.grid_rowconfigure(0, weight=1)

    self.console = tk.Text(console_frame, font="Arial 10", wrap=tk.NONE, bg="black", fg="#E0E0E0", height=14)
    self.console.grid(row=0, column=0, sticky="nsew")
    self.console.config(state=tk.DISABLED)

    # Store references to test buttons for later use
    self.test_water_delivery_button = self.test_indicators["test_water_delivery"]["button"]
    self.test_input_levers_button = self.test_indicators["test_input_levers"]["button"]
    self.test_input_ir_button = self.test_indicators["test_input_ir"]["button"]
    self.test_led_port_button = self.test_indicators["test_led_port"]["button"]
    self.test_led_levers_button = self.test_indicators["test_led_levers"]["button"]
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
    self.input_label_states["input_lever_left"].set(self.input_states["input_lever_left"])
    self.input_label_states["input_lever_right"].set(self.input_states["input_lever_right"])
    self.input_label_states["input_ir"].set(self.input_states["input_ir"])
    self.input_label_states["led_port"].set(self.input_states["led_port"])
    self.input_label_states["led_lever_left"].set(self.input_states["led_lever_left"])
    self.input_label_states["led_lever_right"].set(self.input_states["led_lever_right"])

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
      self.test_input_ir_button.config(state=tk.DISABLED)
      self.test_input_levers_button.config(state=tk.DISABLED)
      self.test_water_delivery_button.config(state=tk.DISABLED)
      self.test_led_port_button.config(state=tk.DISABLED)
      self.test_displays_button.config(state=tk.DISABLED)
      self.test_led_levers_button.config(state=tk.DISABLED)

      # Disable duration inputs
      if "test_water_delivery" in self.test_indicators and "duration_entry" in self.test_indicators["test_water_delivery"]:
        self.test_indicators["test_water_delivery"]["duration_entry"].config(state=tk.DISABLED)
      if "test_led_port" in self.test_indicators and "duration_entry" in self.test_indicators["test_led_port"]:
        self.test_indicators["test_led_port"]["duration_entry"].config(state=tk.DISABLED)
      if "test_displays" in self.test_indicators and "duration_entry" in self.test_indicators["test_displays"]:
        self.test_indicators["test_displays"]["duration_entry"].config(state=tk.DISABLED)
      if "test_led_levers" in self.test_indicators and "duration_entry" in self.test_indicators["test_led_levers"]:
        self.test_indicators["test_led_levers"]["duration_entry"].config(state=tk.DISABLED)
    else:
      # Enable test buttons
      self.test_input_ir_button.config(state=tk.NORMAL)
      self.test_input_levers_button.config(state=tk.NORMAL)
      self.test_water_delivery_button.config(state=tk.NORMAL)
      self.test_led_port_button.config(state=tk.NORMAL)
      self.test_displays_button.config(state=tk.NORMAL)
      self.test_led_levers_button.config(state=tk.NORMAL)

      # Enable duration inputs
      if "test_water_delivery" in self.test_indicators and "duration_entry" in self.test_indicators["test_water_delivery"]:
        self.test_indicators["test_water_delivery"]["duration_entry"].config(state=tk.NORMAL)
      if "test_led_port" in self.test_indicators and "duration_entry" in self.test_indicators["test_led_port"]:
        self.test_indicators["test_led_port"]["duration_entry"].config(state=tk.NORMAL)
      if "test_displays" in self.test_indicators and "duration_entry" in self.test_indicators["test_displays"]:
        self.test_indicators["test_displays"]["duration_entry"].config(state=tk.NORMAL)
      if "test_led_levers" in self.test_indicators and "duration_entry" in self.test_indicators["test_led_levers"]:
        self.test_indicators["test_led_levers"]["duration_entry"].config(state=tk.NORMAL)

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

      # Disable the New Experiment and Edit Experiment buttons
      self.experiment_editor_button.config(state=tk.DISABLED)
      self.new_experiment_button.config(state=tk.DISABLED)
    else:
      # Enable Start button and disable Stop button
      self.start_experiment_button.config(state=tk.NORMAL)
      self.stop_experiment_button.config(state=tk.DISABLED)

      # Enable the New Experiment and Edit Experiment buttons
      self.experiment_editor_button.config(state=tk.NORMAL)
      self.new_experiment_button.config(state=tk.NORMAL)

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

    # Update connection status
    self.connection_status_label.config(text="Connected", fg="green")

    # Enable all buttons
    self.connect_button.config(state=tk.DISABLED)

    # Test buttons
    self.test_water_delivery_button.config(state=tk.NORMAL)
    self.test_input_levers_button.config(state=tk.NORMAL)
    self.test_input_ir_button.config(state=tk.NORMAL)
    self.test_led_port_button.config(state=tk.NORMAL)
    self.test_displays_button.config(state=tk.NORMAL)
    self.test_led_levers_button.config(state=tk.NORMAL)
    self.reset_tests_button.config(state=tk.NORMAL)  # Enable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.NORMAL)

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
    Resets the state of the dashboard and disables all buttons.
    Called when the connection is lost or manually disconnected.
    """
    self.reset_state()

    self.is_connected = False

    # Update connection status
    self.connection_status_label.config(text="Disconnected", fg="red")

    # Enable connect button and disable disconnect button
    self.connect_button.config(state=tk.NORMAL)
    self.disconnect_button.config(state=tk.DISABLED)

    # Test buttons
    self.test_water_delivery_button.config(state=tk.DISABLED)
    self.test_input_levers_button.config(state=tk.DISABLED)
    self.test_input_ir_button.config(state=tk.DISABLED)
    self.test_led_port_button.config(state=tk.DISABLED)
    self.test_displays_button.config(state=tk.DISABLED)
    self.test_led_levers_button.config(state=tk.DISABLED)
    self.reset_tests_button.config(state=tk.DISABLED)  # Disable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.DISABLED)

    # Experiment buttons - keep enabled for experiment management
    self.new_experiment_button.config(state=tk.NORMAL)
    self.experiment_editor_button.config(state=tk.NORMAL)

    # Experiment buttons
    self.start_experiment_button.config(state=tk.DISABLED)
    self.stop_experiment_button.config(state=tk.DISABLED)

    # Reset device version display
    self.device_version = "unknown"
    self.device_version_label.config(text="unknown")

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
          self.device_version_label.config(text=self.device_version)
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
          # Start experiment timer
          self.experiment_start_time = time.time()
        elif status == "completed" or status == "stopped":
          self.set_experiment_buttons_disabled(False)
          # Stop experiment timer
          self.experiment_start_time = None
          self.current_trial_type = "None"
          self.current_trial_start_time = None
      elif received_message["type"] == "trial_start":
        # Update trial start
        trial_name = received_message['data']['trial']
        self.log(f"Trial start: {trial_name}", "info")
        # Update active trial information
        self.current_trial_type = trial_name
        self.current_trial_start_time = time.time()
        if hasattr(self, 'active_trial_type_label'):
          self.active_trial_type_label.config(text=trial_name)
      elif received_message["type"] == "trial_complete":
        # Update trial complete with appropriate log level based on outcome
        trial_data = received_message.get('data', {}).get('data', {})
        trial_outcome = trial_data.get('trial_outcome', 'success')
        trial_name = received_message['data']['trial']

        if trial_outcome.startswith("failure"):
          self.log(f"Trial complete with errors: {trial_name}", "warning")
        else:
          self.log(f"Trial complete: {trial_name}", "success")

        # Reset active trial timer
        self.current_trial_start_time = None
        if hasattr(self, 'active_trial_time_label'):
          self.active_trial_time_label.config(text="00:00:00")
      elif received_message["type"] == "device_log":
        # Update device log
        self.log(received_message["data"]["message"], received_message["data"]["state"], "device")
      elif received_message["type"] == "experiment_validation":
        # Update experiment validation
        success = received_message.get("success", False)
        message = received_message.get("message", "")
        if success:
          self.log(f"Experiment validation: {message}", "success")
        else:
          self.log(f"Experiment validation failed: {message}", "error")
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

  def connect_websocket(self):
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
    else:
      self.log("Already connected to the device", "info")

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
    Resets the state of the dashboard.
    """
    self.is_connected = False
    self.input_states = {
      "input_lever_left": False,
      "input_lever_right": False,
      "input_ir": False,
      "input_port": False,
      "led_port": False,
      "led_lever_left": False,
      "led_lever_right": False,
    }

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
      self.experiment_editor_button.config(state=tk.DISABLED)
      self.on_animal_id_change()

  def on_experiment_selected(self, event=None):
    """Handle experiment selection"""
    selected_experiment = self.experiment_var.get()
    if selected_experiment:
      self.current_experiment = self.experiment_manager.load_experiment(selected_experiment)
      self.log(f"Selected experiment: {selected_experiment}", "info")
      self.experiment_editor_button.config(state=tk.NORMAL)
      self.on_animal_id_change()
    else:
      self.current_experiment = None
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

    # Upload experiment to device, ensuring updated timeline and config is sent
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
    # Total Experiment Time
    total_time_frame = tk.Frame(stats_frame)
    total_time_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(total_time_frame, text="Total Experiment Time:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.total_experiment_time_label = tk.Label(total_time_frame, text="00:00:00", font=("Arial", 11), anchor="e")
    self.total_experiment_time_label.pack(side=tk.RIGHT)

    # Active Trial Time
    active_trial_time_frame = tk.Frame(stats_frame)
    active_trial_time_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(active_trial_time_frame, text="Active Trial Time:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.active_trial_time_label = tk.Label(active_trial_time_frame, text="00:00:00", font=("Arial", 11), anchor="e")
    self.active_trial_time_label.pack(side=tk.RIGHT)

    # Active Trial Type
    active_trial_frame = tk.Frame(stats_frame)
    active_trial_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(active_trial_frame, text="Active Trial:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.active_trial_type_label = tk.Label(active_trial_frame, text="None", font=("Arial", 11), anchor="e")
    self.active_trial_type_label.pack(side=tk.RIGHT)

    # Trial Count
    trial_frame = tk.Frame(stats_frame)
    trial_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(trial_frame, text="Total Trials:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.trial_count_label = tk.Label(trial_frame, text="0", font=("Arial", 11), anchor="e")
    self.trial_count_label.pack(side=tk.RIGHT)

    # Nose Pokes
    nose_pokes_frame = tk.Frame(stats_frame)
    nose_pokes_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(nose_pokes_frame, text="Total Nose Pokes:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.nose_pokes_label = tk.Label(nose_pokes_frame, text="0", font=("Arial", 11), anchor="e")
    self.nose_pokes_label.pack(side=tk.RIGHT)

    # Left Lever Presses
    left_lever_frame = tk.Frame(stats_frame)
    left_lever_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(left_lever_frame, text="Total Left Lever Presses:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.left_lever_presses_label = tk.Label(left_lever_frame, text="0", font=("Arial", 11), anchor="e")
    self.left_lever_presses_label.pack(side=tk.RIGHT)

    # Right Lever Presses
    right_lever_frame = tk.Frame(stats_frame)
    right_lever_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(right_lever_frame, text="Total Right Lever Presses:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
    self.right_lever_presses_label = tk.Label(right_lever_frame, text="0", font=("Arial", 11), anchor="e")
    self.right_lever_presses_label.pack(side=tk.RIGHT)

    # Water Deliveries
    water_frame = tk.Frame(stats_frame)
    water_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
    tk.Label(water_frame, text="Total Water Deliveries:", font=("Arial", 11, "bold"), anchor="w").pack(side=tk.LEFT)
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

    # Reset timing variables
    self.experiment_start_time = None
    self.current_trial_type = "None"
    self.current_trial_start_time = None

    # Reset timer displays
    if hasattr(self, 'total_experiment_time_label'):
      self.total_experiment_time_label.config(text="00:00:00")
    if hasattr(self, 'active_trial_type_label'):
      self.active_trial_type_label.config(text="None")
    if hasattr(self, 'active_trial_time_label'):
      self.active_trial_time_label.config(text="00:00:00")

  def update_timers(self):
    """
    Updates the timer displays every second.
    """
    if hasattr(self, 'total_experiment_time_label'):
      # Update total experiment time
      if self.experiment_start_time:
        elapsed = time.time() - self.experiment_start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        self.total_experiment_time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
      else:
        self.total_experiment_time_label.config(text="00:00:00")

    if hasattr(self, 'active_trial_time_label'):
      # Update active trial time
      if self.current_trial_start_time:
        elapsed = time.time() - self.current_trial_start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        self.active_trial_time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
      else:
        self.active_trial_time_label.config(text="00:00:00")

    # Schedule next update in 1 second
    self.master.after(1000, self.update_timers)

def main():
  root = tk.Tk()
  root.title("Behavior Box: Dashboard")
  root.geometry("846x620")
  root.resizable(False, False)

  # Set window icon
  try:
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)
  except Exception:
    pass

  view = ControlPanel(root)
  view.master.title("Behavior Box: Dashboard")
  view.mainloop()

if __name__ == "__main__":
  main()
