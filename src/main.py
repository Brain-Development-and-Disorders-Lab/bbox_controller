# Main file for the control panel interface
# GUI imports
import tkinter as tk
from tkinter import ttk

# Dimensions (px)
PADDING = 5
TOTAL_WIDTH = 1200 + (PADDING * 6)
PANEL_WIDTH = 1200
PANEL_HEIGHT = 720
HEADING_HEIGHT = 40


class ControlPanel(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_layout()

    def create_layout(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_columnconfigure(2, weight=1)
        self.master.grid_columnconfigure(3, weight=1)
        self.master.grid_columnconfigure(4, weight=1)
        self.master.grid_columnconfigure(5, weight=1)

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
        ).grid(row=4, column=0, padx=PADDING, pady=PADDING)
        tk.Button(
            self.master,
            text="Enable / Disable",
            font="Arial 10"
        ).grid(row=4, column=1, padx=PADDING, pady=PADDING)
        tk.Canvas(
            self.master,
            width=100,
            height=60,
            bg="black"
        ).grid(row=5, column=0, padx=PADDING, pady=PADDING)
        tk.Button(
            self.master,
            text="Enable / Disable",
            font="Arial 10"
        ).grid(row=5, column=1, padx=PADDING, pady=PADDING)

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
        ).grid(row=2, column=2, padx=PADDING, pady=PADDING)
        tk.Label(
            self.master,
            text="Actuator 2: 0.0",
            font="Arial 10"
        ).grid(row=2, column=3, padx=PADDING, pady=PADDING)
        tk.Label(
            self.master,
            text="Commands",
            font="Arial 12"
        ).grid(row=3, column=2, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Button(
            self.master,
            text="Release Water",
            font="Arial 10"
        ).grid(row=4, column=2, padx=PADDING, pady=PADDING)

        # Tests
        tk.Label(
            self.master,
            text="Test",
            font="Arial 12"
        ).grid(row=1, column=4, columnspan=2, padx=PADDING, pady=PADDING)
        tk.Button(
            self.master,
            text="Test Water Delivery",
            font="Arial 10"
        ).grid(row=2, column=4, padx=PADDING, pady=PADDING)
        tk.Button(
            self.master,
            text="Test Actuators",
            font="Arial 10"
        ).grid(row=2, column=5, padx=PADDING, pady=PADDING)


root = tk.Tk()
view = ControlPanel(root)
view.master.title("Control Panel")
view.master.geometry(f"{TOTAL_WIDTH}x{PANEL_HEIGHT}")
view.mainloop()
