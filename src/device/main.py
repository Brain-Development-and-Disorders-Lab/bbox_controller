import datetime
import asyncio
import queue
import threading
import time
import websockets

from controllers import IOController

# Log states
LOG_STATES = {
    "start": "Start",
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "info": "Info",
    "debug": "Debug",
}

# Variables
HOST = "localhost"
PORT = 8765
INPUT_TEST_TIMEOUT = 10 # seconds

def log(message, state="info"):
    """
    Logs a message to the console with a timestamp.

    Parameters:
    message (str): The message to log.
    state (str): The state of the message.
    """
    message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{LOG_STATES[state]}] {message}\n"
    print(message, end="")

async def handle_message(websocket):
    """
    Handles incoming messages from the WebSocket connection.
    """
    async for message in websocket:
        log(f"Received message: {message}", "info")

async def listen():
    """
    Listens for WebSocket connections and handles incoming messages.
    """
    async with websockets.serve(handle_message, HOST, PORT):
        log(f"Listening on {HOST}:{PORT}", "success")
        await asyncio.Future()

class Device:
    def __init__(self):
        # Create a queue for input states
        self.input_queue = queue.Queue()

        # Initialize IO
        self.io = IOController()

        # Setup state
        self.display_state = {
            "mini_display_1": {
                "state": False,
            },
            "mini_display_2": {
                "state": False,
            },
        }

        # Test state
        self.test_state = {
            "test_water_delivery": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
            "test_left_actuator": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
            "test_right_actuator": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
            "test_ir": {
                "state": 0, # -1: failed, 0: not tested, 1: passed
            },
        }

        self.input_states = {
            "left_lever": False,
            "right_lever": False,
            "nose_poke": False,
            "water_port": False,
        }

    def test_water_delivery_task(self):
        # Set default state to passed
        self.test_state["test_water_delivery"]["state"] = 1

        # Show that test is running
        self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="yellow")

        try:
            self.io.set_water_port(True)
            time.sleep(2)
            self.io.set_water_port(False)
        except:
            log("Could not activate water delivery", "error")
            self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="red")
            self.test_state["test_water_delivery"]["state"] = 0

        self.set_test_buttons_disabled(False)

        if self.test_state["test_water_delivery"]["state"] == 1:
            self.test_water_delivery_indicator.create_oval(2, 2, 15, 15, fill="green")
            log("Test water delivery passed", "start")

    # Test functions
    def test_water_delivery(self):
        log("Testing water delivery", "start")

        # Disable test buttons
        self.set_test_buttons_disabled(True)

        # Run the test in a separate thread
        water_delivery_test_thread = threading.Thread(target=self.test_water_delivery_task)
        water_delivery_test_thread.start()

    def test_actuators_task(self):
        # Set default state to passed
        self.test_state["test_left_actuator"]["state"] = 1
        self.test_state["test_right_actuator"]["state"] = 1

        # Show that test is running
        self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="yellow")

        # Step 2: Test that the left actuator can be moved to 1.0
        log("Testing left actuator", "start")
        log("Waiting for left actuator input...", "info")
        running_input_test = True
        running_input_test_start_time = time.time()
        while running_input_test:
            input_state = self.io.get_input_states()
            if input_state["left_lever"] == True:
                running_input_test = False

            # Ensure test doesn't run indefinitely
            if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
                log("Left actuator did not move to 1.0", "error")
                self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
                self.test_state["test_left_actuator"]["state"] = -1
                self.set_test_buttons_disabled(False)
                return

        if input_state["left_lever"] != True:
            log("Left actuator did not move to `True`", "error")
            self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
            self.test_state["test_left_actuator"]["state"] = -1
            self.set_test_buttons_disabled(False)
            return

        log("Left actuator test passed", "success")

        # Step 3: Test that the right actuator can be moved to 1.0
        running_input_test = True
        running_input_test_start_time = time.time()
        log("Testing right actuator", "start")
        log("Waiting for right actuator input...", "info")
        while running_input_test:
            input_state = self.io.get_input_states()
            if input_state["right_lever"] == True:
                running_input_test = False

            # Ensure test doesn't run indefinitely
            if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
                log("Right actuator did not move to `True`", "error")
                self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
                self.test_state["test_right_actuator"]["state"] = -1
                self.set_test_buttons_disabled(False)
                return

        if input_state["right_lever"] != True:
            log("Right actuator did not move to `True`", "error")
            self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
            self.test_state["test_right_actuator"]["state"] = -1
            self.set_test_buttons_disabled(False)
            return

        log("Right actuator test passed", "success")

        # Set test to passed
        if self.test_state["test_left_actuator"]["state"] == 1 and self.test_state["test_right_actuator"]["state"] == 1:
            self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="green")
            log("Actuators test passed", "success")

        # Re-enable test buttons
        self.set_test_buttons_disabled(False)

    def test_actuators(self):
        log("Testing actuators", "start")

        # Step 1: Test that both actuators default to 0.0
        input_state = self.io.get_input_states()
        if input_state["left_lever"] != False:
            log("Left actuator did not default to `False`", "error")
            self.test_state["test_left_actuator"]["state"] = -1
            self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
            return
        if input_state["right_lever"] != False:
            log("Right actuator did not default to `False`", "error")
            self.test_state["test_right_actuator"]["state"] = -1
            self.test_actuators_indicator.create_oval(2, 2, 15, 15, fill="red")
            return
        log("Actuators defaulted to `False`", "success")

        # Disable test buttons
        self.set_test_buttons_disabled(True)

        # Run the test in a separate thread
        actuator_test_thread = threading.Thread(target=self.test_actuators_task)
        actuator_test_thread.start()

    def test_ir_task(self):
        # Set default state to passed
        self.test_state["test_ir"]["state"] = 1

        # Show that test is running
        self.test_ir_indicator.create_oval(2, 2, 15, 15, fill="yellow")

        # Step 1: Test that the IR is broken
        log("Waiting for IR input...", "info")
        running_input_test = True
        running_input_test_start_time = time.time()
        while running_input_test:
            input_state = self.io.get_input_states()
            if input_state["nose_poke"] == False:
                running_input_test = False

            # Ensure test doesn't run indefinitely
            if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
                log("IR was not broken", "error")
                self.test_ir_indicator.create_oval(2, 2, 15, 15, fill="red")
                self.test_state["test_ir"]["state"] = -1
                self.set_test_buttons_disabled(False)
                return

        if input_state["nose_poke"] != False:
            log("IR was not broken", "error")
            self.test_ir_indicator.create_oval(2, 2, 15, 15, fill="red")
            self.test_state["test_ir"]["state"] = -1
            self.set_test_buttons_disabled(False)
            return

        # Set test to passed
        if self.test_state["test_ir"]["state"] == 1:
            self.test_ir_indicator.create_oval(2, 2, 15, 15, fill="green")
            log("IR test passed", "success")

        # Re-enable test buttons
        self.set_test_buttons_disabled(False)

    def test_ir(self):
        log("Testing IR", "start")

        # Disable test buttons
        self.set_test_buttons_disabled(True)

        # Run the test in a separate thread
        ir_test_thread = threading.Thread(target=self.test_ir_task)
        ir_test_thread.start()

def main():
    log("Starting listener...", "start")
    asyncio.run(listen())

if __name__ == "__main__":
    main()
