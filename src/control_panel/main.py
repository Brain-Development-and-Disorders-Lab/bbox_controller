"""
Filename: main.py
Author: Henry Burgess
Date: 2025-03-07
Description: Main file for the control panel interface
License: MIT
"""

# GUI imports
import json
import tkinter as tk
from tkinter import ttk
import datetime
import threading
import atexit
import queue
import websocket
import time
import os

# Variables
PADDING = 10
SECTION_PADDING = 10
TOTAL_WIDTH = 1200 + (PADDING * 6)
PANEL_WIDTH = 1200
PANEL_HEIGHT = 720
COLUMN_WIDTH = 30
HEADING_HEIGHT = 40
UPDATE_INTERVAL = 50 # milliseconds
INPUT_TEST_TIMEOUT = 10 # seconds

# Log states
LOG_STATES = {
  "start": "Start",
  "success": "Success",
  "error": "Error",
  "warning": "Warning",
  "info": "Info",
  "debug": "Debug",
}

# Test commands
TEST_COMMANDS = [
  "test_water_delivery",
  "test_actuators",
  "test_ir",
]

# Experiment commands
EXPERIMENT_COMMANDS = [
  "start_experiment",
  "stop_experiment"
]

TEST_STATES = {
  "NOT_TESTED": 0,
  "FAILED": -1,
  "PASSED": 1,
  "RUNNING": 2,
}

class ControlPanel(tk.Frame):
  def __init__(self, master=None):
      super().__init__(master)
      self.master = master

      # Create a queue for input states
      self.input_queue = queue.Queue()

      # Connection state
      self.is_connected = False

      # UI variables
      self.ip_address_var = tk.StringVar(self.master, "localhost")
      self.port_var = tk.StringVar(self.master, "8765")
      self.animal_id_var = tk.StringVar(self.master, "")
      self.animal_id_var.trace_add("write", self.on_animal_id_change)

      # Test state
      self.test_state = {
        "test_water_delivery": {
          "state": TEST_STATES["NOT_TESTED"],
        },
        "test_actuators": {
          "state": TEST_STATES["NOT_TESTED"],
        },
        "test_ir": {
          "state": TEST_STATES["NOT_TESTED"],
        },
      }

      self.input_states = {
        "left_lever": False,
        "right_lever": False,
        "nose_poke": False,
        "water_port": False,
      }

      self.input_label_states = {
        "left_lever": tk.BooleanVar(self.master, False),
        "right_lever": tk.BooleanVar(self.master, False),
      }

      # Create the layout
      self.create_layout()

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

  def create_test_row(self, parent, label_text, command_name):
    """
    Creates a test row with a label, indicator, and test button.

    Parameters:
    parent: The parent widget
    label_text (str): The text to display
    command_name (str): The command to execute when the test button is clicked
    """
    # Container frame for the entire row
    container_frame = tk.Frame(parent)
    container_frame.pack(side=tk.TOP, fill=tk.X, expand=True, pady=2)

    # Colored background frame for label and indicator
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

    # State indicator (circle)
    indicator = tk.Canvas(colored_frame, width=15, height=15, bg="#f0f0f0", highlightthickness=0)
    indicator.grid(row=0, column=1, sticky="e")

    # Test button in the container frame
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
      state = self.test_state[command_name]["state"]
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
    self.connect_button = tk.Button(connection_frame, text="Connect", command=self.connect_to_device)
    self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
    self.disconnect_button = tk.Button(connection_frame, text="Disconnect", command=self.disconnect_from_device, state=tk.DISABLED)
    self.disconnect_button.pack(side=tk.LEFT)

    # Main content area
    content_frame = tk.Frame(main_frame)
    content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

    # Left column - Status Information
    status_frame = tk.Frame(content_frame)
    status_frame.grid(row=0, column=0, sticky="n", padx=(0, PADDING))

    # Display Status section
    displays_frame = tk.LabelFrame(status_frame, text="Display Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    displays_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, PADDING))

    # Display canvas with proper aspect ratio
    display_width = PANEL_WIDTH / 3 - 50
    display_height = display_width * (9/16) # Maintain 16:9 aspect ratio
    display_canvas = tk.Canvas(
      displays_frame,
      width=display_width,
      height=display_height,
      bg="black"
    )
    display_canvas.pack(pady=10)

    # Input Status section
    input_status_frame = tk.LabelFrame(status_frame, text="Input Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    input_status_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, PADDING))

    # Create input indicators
    self.create_state_indicator(input_status_frame, "Left Actuator", self.input_label_states["left_lever"])
    self.create_state_indicator(input_status_frame, "Right Actuator", self.input_label_states["right_lever"])

    # Test Status section
    test_status_frame = tk.LabelFrame(status_frame, text="Test Status", padx=SECTION_PADDING, pady=SECTION_PADDING)
    test_status_frame.pack(side=tk.TOP, fill=tk.X)

    # Create test rows
    self.create_test_row(test_status_frame, "Test Water Delivery", "test_water_delivery")
    self.create_test_row(test_status_frame, "Test Actuators", "test_actuators")
    self.create_test_row(test_status_frame, "Test IR", "test_ir")

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

    # Animal ID input frame
    animal_id_frame = tk.Frame(experiment_management_frame)
    animal_id_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

    tk.Label(animal_id_frame, text="Animal ID:").pack(side=tk.LEFT, pady=0)
    self.animal_id_input = tk.Entry(animal_id_frame, textvariable=self.animal_id_var, state=tk.DISABLED)
    self.animal_id_input.pack(side=tk.LEFT, pady=0, fill=tk.X, expand=True)

    # Experiment buttons frame
    experiment_buttons_frame = tk.Frame(experiment_management_frame)
    experiment_buttons_frame.pack(side=tk.TOP, fill=tk.X)

    self.start_experiment_button = tk.Button(
      experiment_buttons_frame,
      text="Start",
      font="Arial 10",
      command=lambda: self.execute_command("start_experiment " + self.animal_id_var.get()),
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

    self.console = tk.Text(console_frame, font="Arial 10", wrap=tk.NONE, bg="black", fg="white")
    self.console.grid(row=0, column=0, sticky="nsew")
    self.console.config(state=tk.DISABLED)

    # Add tags for the console message levels
    self.console.tag_config("error", foreground="red")
    self.console.tag_config("warning", foreground="yellow")
    self.console.tag_config("success", foreground="green")
    self.console.tag_config("info", foreground="white")
    self.log("Console initialized")

    # Store references to test buttons for later use
    self.test_water_delivery_button = self.test_indicators["test_water_delivery"]["button"]
    self.test_actuators_button = self.test_indicators["test_actuators"]["button"]
    self.test_ir_button = self.test_indicators["test_ir"]["button"]

  def log(self, message, state="info"):
    """
    Logs a message to the console with a timestamp.

    Parameters:
    message (str): The message to log.
    state (str): The state of the message.
    """
    self.console.config(state=tk.NORMAL)
    message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{LOG_STATES[state]}] {message}\n"
    self.console.insert(tk.END, message, state)
    print(message, end="")
    self.console.config(state=tk.DISABLED)
    self.console.see(tk.END)

  def update_state_labels(self):
    """
    Updates the state labels for the input states.
    """
    self.input_label_states["left_lever"].set(self.input_states["left_lever"])
    self.input_label_states["right_lever"].set(self.input_states["right_lever"])

  def update_test_state(self, command_name, state):
      """
      Updates the state of a test.

      Parameters:
      command_name (str): The name of the command to update.
      state (int): The state to set the command to.
      """
      self.test_state[command_name]["state"] = state
      self.update_test_state_indicators()

  def update_test_state_indicators(self):
    """
    Updates the state indicators for the test states.
    """
    for command_name in self.test_state:
      if command_name in self.test_indicators:
          self.test_indicators[command_name]["update"]()

  def set_test_buttons_disabled(self, disabled):
    """
    Disables or enables the test buttons.

    Parameters:
    disabled (bool): Whether to disable the test buttons.
    """
    # Disable test buttons
    if disabled:
      self.test_ir_button.config(state=tk.DISABLED)
      self.test_actuators_button.config(state=tk.DISABLED)
      self.test_water_delivery_button.config(state=tk.DISABLED)
    else:
      # Enable test buttons
      self.test_ir_button.config(state=tk.NORMAL)
      self.test_actuators_button.config(state=tk.NORMAL)
      self.test_water_delivery_button.config(state=tk.NORMAL)

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
    Enables the start experiment button only if animal_id_input is not empty.
    """
    if self.animal_id_var.get().strip():
      self.start_experiment_button.config(state=tk.NORMAL)
    else:
      self.start_experiment_button.config(state=tk.DISABLED)

  def parse_message(self, message):
    """
    Parses a message from the device.

    Parameters:
    message (str): The message to parse.
    """
    try:
      return json.loads(message)
    except json.JSONDecodeError:
      self.log("Invalid JSON message received", "error")
      return None

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
    self.reset_tests_button.config(state=tk.NORMAL)  # Enable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.NORMAL)

    # Disconnect button
    self.disconnect_button.config(state=tk.NORMAL)

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
    self.reset_tests_button.config(state=tk.DISABLED)  # Disable reset button

    # Animal ID input
    self.animal_id_input.config(state=tk.DISABLED)

    # Experiment buttons
    self.start_experiment_button.config(state=tk.DISABLED)
    self.stop_experiment_button.config(state=tk.DISABLED)

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
      if received_message["type"] == "input_state":
        self.input_states = received_message["data"]
        self.update_state_labels()
      elif received_message["type"] == "test_state":
        # Update only the specific test states that changed
        for test_name, test_data in received_message["data"].items():
          if test_name in self.test_state:
            self.test_state[test_name]["state"] = test_data["state"]
            # If any tests have completed, re-enable the test buttons
            if test_data["state"] in [TEST_STATES["PASSED"], TEST_STATES["FAILED"]]:
              self.set_test_buttons_disabled(False)
        self.update_test_state_indicators()
      elif received_message["type"] == "task_status":
        status = received_message["data"]["status"]
        self.log(f"Task status: {status}", "info")
        # Update experiment buttons based on task status
        if status == "completed":
          self.set_experiment_buttons_disabled(False)
      elif received_message["type"] == "trial_start":
        self.log(f"Trial start: {received_message['data']['trial']}", "info")
      elif received_message["type"] == "trial_complete":
        self.log(f"Trial complete: {received_message['data']['trial']}", "success")
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
    # Split the command and extract the primary instruction from any arguments
    command_groups = command.split(" ")
    primary_command = command_groups[0]

    # Send the command to the device
    if primary_command in TEST_COMMANDS:
      self.send_command(command)
      self.update_test_state(command, TEST_STATES["RUNNING"])
      self.set_test_buttons_disabled(True)
    elif primary_command in EXPERIMENT_COMMANDS:
      self.send_command(command)
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
    # Disable disconnect button immediately to prevent multiple clicks
    self.disconnect_button.config(state=tk.DISABLED)

    # Disable animal ID input
    self.animal_id_input.config(state=tk.DISABLED)

    # Reset tests before disconnecting
    self.reset_tests()

    # Invoke the close method, which will trigger the on_close method
    self.ws.close()

    self.log("Disconnected from the device", "success")

  def reset_tests(self):
    """
    Resets all test states and indicators to their initial state.
    """
    # Reset test states
    self.test_state = {
      "test_water_delivery": {
        "state": TEST_STATES["NOT_TESTED"],
      },
      "test_actuators": {
        "state": TEST_STATES["NOT_TESTED"],
      },
      "test_ir": {
        "state": TEST_STATES["NOT_TESTED"],
      },
    }

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
    }

    self.reset_tests()

  def run_websocket(self):
    self.ws.run_forever()

def main():
  root = tk.Tk()
  root.title("Behavior Box: Control Panel")
  root.resizable(False, False)

  # Set window icon
  try:
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    icon = tk.PhotoImage(file=icon_path)
    root.iconphoto(True, icon)
  except Exception as e:
    pass

  view = ControlPanel(root)
  view.master.title("Behavior Box: Control Panel")
  view.mainloop()

if __name__ == "__main__":
  main()
