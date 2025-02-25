# Main file for the control panel interface
# GUI imports
import tkinter as tk
from tkinter import ttk


# I/O imports
import lcd_i2c as lcd
import gpiozero as gpio


class ControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Control Panel")
        self.root.geometry("800x600")
        self.root.mainloop()


if __name__ == "__main__":
    ControlPanel()
