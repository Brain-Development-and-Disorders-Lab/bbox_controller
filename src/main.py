"""
Filename: main.py
Author: Henry Burgess
Date: 2025-03-07
Description: Main file for the control panel interface
License: MIT
"""

# GUI imports
import tkinter as tk
from tkinter import ttk
import datetime

# Dimensions (px)
PADDING = 2
TOTAL_WIDTH = 1200 + (PADDING * 6)
PANEL_WIDTH = 1200
PANEL_HEIGHT = 720
HEADING_HEIGHT = 40

class ControlPanel(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

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
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
            "test_actuators": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
            "test_led": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
        }

        # Create the layout
        self.create_layout()

    def create_layout(self):
        # Configure the grid
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=0)
        self.master.grid_columnconfigure(2, weight=0)
        self.master.grid_columnconfigure(3, weight=0)
        self.master.grid_columnconfigure(4, weight=0)
        self.master.grid_columnconfigure(5, weight=0)

        # Set the UI to resize with the window
        self.master.grid_propagate(True)

        # Heading
        tk.Label(self.master, text="Behavior Box - Control Panel", font="Arial 18").grid(row=0, column=0, padx=5, pady=5, columnspan=6, sticky="ew")

        # Large display
        tk.Label(
            self.master,
            text="Displays",
            font="Arial 12"
        ).grid(row=1, column=0, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Canvas(
            self.master,
            width=PANEL_WIDTH / 3 - 50,
            height=(PANEL_WIDTH / 3 - 50) * 0.75,
            bg="black"
        ).grid(row=2, column=0, columnspan=2, padx=PADDING, pady=PADDING)

        # Mini displays
        tk.Label(
            self.master,
            text="Mini Displays",
            font="Arial 12",
        ).grid(row=3, column=0, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Canvas(
            self.master,
            width=100,
            height=60,
            bg="black"
        ).grid(row=4, column=0, padx=PADDING, pady=PADDING, sticky="w")
        tk.Button(
            self.master,
            textvariable=self.display_state["mini_display_1"]["button_text"],
            font="Arial 10",
            command=lambda: self.toggle_display("mini_display_1")
        ).grid(row=4, column=1, padx=PADDING, pady=PADDING, sticky="w")
        tk.Canvas(
            self.master,
            width=100,
            height=60,
            bg="black"
        ).grid(row=5, column=0, padx=PADDING, pady=PADDING, sticky="w")
        tk.Button(
            self.master,
            textvariable=self.display_state["mini_display_2"]["button_text"],
            font="Arial 10",
            command=lambda: self.toggle_display("mini_display_2")
        ).grid(row=5, column=1, padx=PADDING, pady=PADDING, sticky="w")

        # Inputs
        tk.Label(
            self.master,
            text="Input States",
            font="Arial 12"
        ).grid(row=1, column=2, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Label(
            self.master,
            text="Actuator 1: 0.0",
            font="Arial 10"
        ).grid(row=2, column=2, padx=PADDING, pady=PADDING, sticky="n")
        tk.Label(
            self.master,
            text="Actuator 2: 0.0",
            font="Arial 10"
        ).grid(row=2, column=3, padx=PADDING, pady=PADDING, sticky="n")

        # Commands
        tk.Label(
            self.master,
            text="Commands",
            font="Arial 12"
        ).grid(row=3, column=2, columnspan=2, padx=PADDING, pady=PADDING)

        # Setup frame for buttons
        commands_button_frame = tk.Frame(self.master)
        commands_button_frame.grid(row=4, column=2, padx=PADDING, pady=PADDING, sticky="n")

        tk.Button(
            commands_button_frame,
            text="Release Water",
            font="Arial 10"
        ).pack(side=tk.TOP, padx=2, pady=2, anchor="w")

        # Tests
        tk.Label(
            self.master,
            text="Test Functions",
            font="Arial 12"
        ).grid(row=1, column=4, columnspan=2, padx=PADDING, pady=PADDING)

        # Setup frame for buttons
        test_buttons_frame = tk.Frame(self.master)
        test_buttons_frame.grid(row=2, column=4, padx=PADDING, pady=PADDING, sticky="n")

        # Setup test water delivery button and indicator
        test_water_delivery_pair_frame = tk.Frame(test_buttons_frame)
        test_water_delivery_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_water_delivery_indicator = tk.Canvas(test_water_delivery_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_water_delivery_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="blue")
        test_water_delivery_button = tk.Button(test_water_delivery_pair_frame, text="Test Water Delivery", font="Arial 10", command=self.test_water_delivery)
        test_water_delivery_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

        # Setup test actuators button and indicator
        test_actuators_pair_frame = tk.Frame(test_buttons_frame)
        test_actuators_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_actuators_indicator = tk.Canvas(test_actuators_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_actuators_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="blue")
        test_actuators_button = tk.Button(test_actuators_pair_frame, text="Test Actuators", font="Arial 10", command=self.test_actuators)
        test_actuators_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

        # Setup test LED button and indicator
        test_led_pair_frame = tk.Frame(test_buttons_frame)
        test_led_pair_frame.pack(side=tk.TOP, fill=tk.X)

        self.test_led_indicator = tk.Canvas(test_led_pair_frame, width=20, height=20, bg=self.master.cget("bg"), highlightthickness=0)
        self.test_led_indicator.pack(side=tk.RIGHT, padx=1, pady=2, anchor="center")
        self.test_led_indicator.create_oval(2, 2, 15, 15, fill="blue")
        test_led_button = tk.Button(test_led_pair_frame, text="Test LED", font="Arial 10", command=self.test_led)
        test_led_button.pack(side=tk.LEFT, padx=1, pady=2, anchor="center")

        # Console
        tk.Label(
            self.master,
            text="Console",
            font="Arial 12"
        ).grid(row=6, column=0, columnspan=6, padx=PADDING, pady=PADDING)
        self.console = tk.Text(self.master, font="Arial 10", wrap=tk.NONE, height=10, width=120, bg="black", fg="white")
        self.console.grid(row=7, column=0, columnspan=6, padx=PADDING, pady=PADDING, sticky="n")
        self.console.config(state=tk.DISABLED)
        self.log("Console initialized")

    def log(self, message):
        """
        Logs a message to the console with a timestamp.

        Parameters:
        message (str): The message to log.
        """
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.console.config(state=tk.DISABLED)
        self.console.see(tk.END)

    def toggle_display(self, display_name):
        self.display_state[display_name]["state"] = not self.display_state[display_name]["state"]
        self.display_state[display_name]["button_text"].set("Disable" if self.display_state[display_name]["state"] else "Enable")
        self.update_display_state()

    def update_display_state(self):
        self.log("Display state updated")

    # Test functions
    def test_water_delivery(self):
        self.log("Testing water delivery")

        # Simulate a successful test
        self.test_state["test_water_delivery"]["state"] = 1
        self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="green")

    def test_actuators(self):
        self.log("Testing actuators")

        # Simulate a successful test
        self.test_state["test_actuators"]["state"] = 1
        self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="green")

    def test_led(self):
        self.log("Testing LED")

        # Simulate a successful test
        self.test_state["test_led"]["state"] = 1
        self.test_led_indicator.create_oval(2, 2, 15, 15, fill="green")


root = tk.Tk()
root.resizable(False, False)
view = ControlPanel(root)
view.master.title("Control Panel")
view.mainloop()
