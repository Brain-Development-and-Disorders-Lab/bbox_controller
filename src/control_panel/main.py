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
import datetime
import threading
import atexit
import queue
import websocket
import time

# Variables
PADDING = 2
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
    "run_experiment_test",
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

        # Setup state
        self.display_state = {
            "mini_display_1": {
                "state": False,
                "button_text": tk.StringVar(self.master, "Enable"),
            },
            "mini_display_2": {
                "state": False,
                "button_text": tk.StringVar(self.master, "Enable"),
            },
        }

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
            "left_lever": tk.StringVar(self.master, "Left Actuator: False"),
            "right_lever": tk.StringVar(self.master, "Right Actuator: False"),
        }

        # Create the layout
        self.create_layout()

        # Handle exiting
        atexit.register(self.on_exit)

    def create_layout(self):
        """
        Creates the layout of the control panel.
        """
        # Configure the grid
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=0)
        self.master.grid_columnconfigure(2, weight=0)
        self.master.grid_columnconfigure(3, weight=0)

        # Set the UI to resize with the window
        self.master.grid_propagate(True)

        # Heading
        tk.Label(self.master, text="Behavior Box - Control Panel", font="Arial 18").grid(row=0, column=0, padx=5, pady=5, columnspan=6, sticky="ew")

        # UI components for IP address and port
        self.ip_address_var = tk.StringVar(self.master, "localhost")
        self.port_var = tk.StringVar(self.master, "8765")

        # Frame for IP and Port inputs
        connection_frame = tk.Frame(self.master)
        connection_frame.grid(row=1, column=0, padx=PADDING, pady=PADDING, columnspan=3, sticky="ew")

        tk.Label(connection_frame, text="IP Address:").pack(side=tk.LEFT)
        tk.Entry(connection_frame, textvariable=self.ip_address_var).pack(side=tk.LEFT)

        tk.Label(connection_frame, text="Port:").pack(side=tk.LEFT)
        tk.Entry(connection_frame, textvariable=self.port_var).pack(side=tk.LEFT)

        self.connect_button = tk.Button(connection_frame, text="Connect", command=self.connect_to_device)
        self.connect_button.pack(side=tk.LEFT)
        self.disconnect_button = tk.Button(connection_frame, text="Disconnect", command=self.disconnect_from_device, state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT)

        # Large display
        tk.Label(
            self.master,
            text="Displays",
            font="Arial 12",
            width=COLUMN_WIDTH
        ).grid(row=2, column=0, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Canvas(
            self.master,
            width=PANEL_WIDTH / 5 - 50,
            height=(PANEL_WIDTH / 5 - 50) * 0.75,
            bg="black"
        ).grid(row=3, column=0, columnspan=2, padx=PADDING, pady=PADDING)

        # Mini displays
        tk.Label(
            self.master,
            text="Mini Displays",
            font="Arial 12",
        ).grid(row=4, column=0, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Canvas(
            self.master,
            width=100,
            height=60,
            bg="black"
        ).grid(row=5, column=0, padx=PADDING, pady=PADDING, sticky="w")
        self.mini_display_one_button = tk.Button(
            self.master,
            textvariable=self.display_state["mini_display_1"]["button_text"],
            font="Arial 10",
            command=lambda: self.execute_command("toggle_display:mini_display_1"),
            state=tk.DISABLED
        )
        self.mini_display_one_button.grid(row=5, column=1, padx=PADDING, pady=PADDING, sticky="w")
        tk.Canvas(
            self.master,
            width=100,
            height=60,
            bg="black"
        ).grid(row=6, column=0, padx=PADDING, pady=PADDING, sticky="w")
        self.mini_display_two_button = tk.Button(
            self.master,
            textvariable=self.display_state["mini_display_2"]["button_text"],
            font="Arial 10",
            command=lambda: self.execute_command("toggle_display:mini_display_2"),
            state=tk.DISABLED
        )
        self.mini_display_two_button.grid(row=6, column=1, padx=PADDING, pady=PADDING, sticky="w")

        # Inputs
        tk.Label(
            self.master,
            text="Input States",
            font="Arial 12",
            width=COLUMN_WIDTH
        ).grid(row=2, column=2, padx=PADDING, pady=PADDING)

        # Setup frame for input labels
        input_labels_frame = tk.Frame(self.master)
        input_labels_frame.grid(row=3, column=2, padx=PADDING, pady=PADDING, sticky="n")

        left_actuator_label_frame = tk.Frame(input_labels_frame)
        left_actuator_label_frame.pack(side=tk.TOP, fill=tk.X)
        self.left_actuator_label = tk.Label(
            left_actuator_label_frame,
            textvariable=self.input_label_states["left_lever"],
            font="Arial 10"
        )
        self.left_actuator_label.pack(side=tk.LEFT, padx=1, pady=2, anchor=tk.W)
        right_actuator_label_frame = tk.Frame(input_labels_frame)
        right_actuator_label_frame.pack(side=tk.TOP, fill=tk.X)
        self.right_actuator_label = tk.Label(
            right_actuator_label_frame,
            textvariable=self.input_label_states["right_lever"],
            font="Arial 10"
        )
        self.right_actuator_label.pack(side=tk.LEFT, padx=1, pady=2, anchor=tk.W)

        # Commands
        tk.Label(
            self.master,
            text="Commands",
            font="Arial 12"
        ).grid(row=4, column=2, padx=PADDING, pady=PADDING)

        # Setup frame for buttons
        commands_button_frame = tk.Frame(self.master)
        commands_button_frame.grid(row=5, column=2, padx=PADDING, pady=PADDING, sticky="n")

        self.release_water_button = tk.Button(
            commands_button_frame,
            text="Release Water",
            font="Arial 10",
            command=lambda: self.execute_command("release_water"),
            state=tk.DISABLED
        )
        self.release_water_button.pack(side=tk.TOP, padx=2, pady=2, anchor="w")

        # Run experiment button
        self.run_experiment_button = tk.Button(
            commands_button_frame,
            text="Run Experiment",
            font="Arial 10",
            command=lambda: self.execute_command("run_experiment_test"),
            state=tk.DISABLED
        )
        self.run_experiment_button.pack(side=tk.TOP, padx=2, pady=2, anchor="w")

        # Console
        tk.Label(
            self.master,
            text="Console",
            font="Arial 12"
        ).grid(row=2, column=3, padx=PADDING, pady=PADDING)
        self.console = tk.Text(self.master, font="Arial 10", wrap=tk.NONE, height=10, width=50, bg="black", fg="white")
        self.console.grid(row=3, column=3, padx=PADDING, pady=PADDING, sticky="n")
        self.console.config(state=tk.DISABLED)

        # Add tags for the console message levels
        self.console.tag_config("error", foreground="red")
        self.console.tag_config("warning", foreground="yellow")
        self.console.tag_config("success", foreground="green")
        self.console.tag_config("info", foreground="white")
        self.log("Console initialized")

        # Tests
        tk.Label(
            self.master,
            text="Test Functions",
            font="Arial 12"
        ).grid(row=4, column=3, padx=PADDING, pady=PADDING)

        # Setup frame for buttons
        test_buttons_frame = tk.Frame(self.master)
        test_buttons_frame.grid(row=5, column=3, padx=PADDING, pady=PADDING, sticky="n")

        # Setup test water delivery button and indicator
        test_water_delivery_pair_frame = tk.Frame(test_buttons_frame)
        test_water_delivery_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_water_delivery_indicator = tk.Canvas(test_water_delivery_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_water_delivery_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="blue")
        self.test_water_delivery_button = tk.Button(
            test_water_delivery_pair_frame,
            text="Test Water Delivery",
            font="Arial 10",
            command=lambda: self.execute_command("test_water_delivery"),
            state=tk.DISABLED
        )
        self.test_water_delivery_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

        # Setup test actuators button and indicator
        test_actuators_pair_frame = tk.Frame(test_buttons_frame)
        test_actuators_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_actuators_indicator = tk.Canvas(test_actuators_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_actuators_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="blue")
        self.test_actuators_button = tk.Button(
            test_actuators_pair_frame,
            text="Test Actuators",
            font="Arial 10",
            command=lambda: self.execute_command("test_actuators"),
            state=tk.DISABLED
        )
        self.test_actuators_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

        # Setup test IR button and indicator
        test_ir_pair_frame = tk.Frame(test_buttons_frame)
        test_ir_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_ir_indicator = tk.Canvas(test_ir_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_ir_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_ir_indicator.create_oval(2, 2, 15, 15, fill="blue")
        self.test_ir_button = tk.Button(
            test_ir_pair_frame,
            text="Test IR",
            font="Arial 10",
            command=lambda: self.execute_command("test_ir"),
            state=tk.DISABLED
        )
        self.test_ir_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

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

    def toggle_display(self, display_name):
        """
        Toggles the state of a display.

        Parameters:
        display_name (str): The name of the display to toggle.
        """
        self.display_state[display_name]["state"] = not self.display_state[display_name]["state"]
        self.display_state[display_name]["button_text"].set("Disable" if self.display_state[display_name]["state"] else "Enable")

    def update_state_labels(self):
        """
        Updates the state labels for the input states.
        """
        self.input_label_states["left_lever"].set(f"Left Actuator: {self.input_states['left_lever']}")
        self.input_label_states["right_lever"].set(f"Right Actuator: {self.input_states['right_lever']}")

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
        for command_name, command_state in self.test_state.items():
            # Determine which indicator to update
            if command_name == "test_water_delivery":
                indicator = self.test_water_delivery_indicator
            elif command_name == "test_actuators":
                indicator = self.test_actuators_indicator
            elif command_name == "test_ir":
                indicator = self.test_ir_indicator

            # Update the indicator
            if command_state["state"] == TEST_STATES["FAILED"]:
                indicator.create_oval(2, 2, 15, 15, fill="red")
                self.set_test_buttons_disabled(False)
            elif command_state["state"] == TEST_STATES["PASSED"]:
                indicator.create_oval(2, 2, 15, 15, fill="green")
                self.set_test_buttons_disabled(False)
            elif command_state["state"] == TEST_STATES["RUNNING"]:
                indicator.create_oval(2, 2, 15, 15, fill="yellow")

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

        Parameters:
        disabled (bool): Whether to disable the experiment buttons.
        """
        # Disable experiment buttons
        if disabled:
            self.run_experiment_button.config(state=tk.DISABLED)
        else:
            # Enable experiment buttons
            self.run_experiment_button.config(state=tk.NORMAL)

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

        # Display buttons
        self.mini_display_one_button.config(state=tk.NORMAL)
        self.mini_display_two_button.config(state=tk.NORMAL)

        # Release water button
        self.release_water_button.config(state=tk.NORMAL)

        # Run experiment button
        self.run_experiment_button.config(state=tk.NORMAL)

        # Disconnect button
        self.disconnect_button.config(state=tk.NORMAL)

    def on_disconnect(self):
        """
        Resets the state of the control panel and disables all buttons.
        """
        self.reset_state()

        self.is_connected = False

        # Enable all buttons
        self.connect_button.config(state=tk.NORMAL)

        # Test buttons
        self.test_water_delivery_button.config(state=tk.DISABLED)
        self.test_actuators_button.config(state=tk.DISABLED)
        self.test_ir_button.config(state=tk.DISABLED)

        # Display buttons
        self.mini_display_one_button.config(state=tk.DISABLED)
        self.mini_display_two_button.config(state=tk.DISABLED)

        # Release water button
        self.release_water_button.config(state=tk.DISABLED)

        # Run experiment button
        self.run_experiment_button.config(state=tk.DISABLED)

        # Connect button
        self.connect_button.config(state=tk.NORMAL)

        # Disconnect button
        self.disconnect_button.config(state=tk.DISABLED)
        self.log("Disconnected from the device", "success")

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
                self.test_state = received_message["data"]
                self.update_test_state_indicators()
            else:
                self.log(f"Received message: {received_message}", "info")

    def on_error(self, ws, error):
        """
        Handles errors from the WebSocket.

        Parameters:
        ws (websocket.WebSocketApp): The WebSocket application.
        error (str): The error to handle.
        """
        self.log(f"WebSocket error: {error}", "error")

    def on_close(self, ws):
        """
        Handles the closing of the WebSocket connection.

        Parameters:
        ws (websocket.WebSocketApp): The WebSocket application.
        """
        self.log("Connection closed", "info")

        # Perform opposite of on_connect
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

    def execute_command(self, command_name):
        """
        Executes a command on the device.

        Parameters:
        command_name (str): The name of the command to execute.
        """
        # Send the command to the device
        if command_name in TEST_COMMANDS:
            self.send_command(command_name)
            self.update_test_state(command_name, TEST_STATES["RUNNING"])
            self.set_test_buttons_disabled(True)
        elif command_name in EXPERIMENT_COMMANDS:
            self.send_command(command_name)
            self.set_experiment_buttons_disabled(True)
        else:
            self.log(f"Invalid command: {command_name}", "error")

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
        # Invoke the close method, which will trigger the on_close method
        self.ws.close()

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

    def run_websocket(self):
        self.ws.run_forever()

def main():
    root = tk.Tk()
    root.resizable(False, False)
    view = ControlPanel(root)
    view.master.title("Control Panel")
    view.mainloop()

if __name__ == "__main__":
    main()
