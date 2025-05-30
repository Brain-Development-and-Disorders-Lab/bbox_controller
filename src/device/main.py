import asyncio
import threading
import time
import websockets
import json
import queue
import multiprocessing

# Controllers
from controllers.IOController import IOController
from controllers.DisplayController import DisplayController

# Other imports
from experiment import Experiment
from util import log

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

# Variables
HOST = ""  # Listen on all available interfaces
PORT = 8765
INPUT_TEST_TIMEOUT = 10 # seconds

# Create a global message queue
message_queue = queue.Queue()

class Device:
  def __init__(self):
    # Initialize controllers
    self.io = IOController()
    self.display = DisplayController()

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

    # Experiment
    self.current_experiment = None
    self.experiment_message_queue = None

    # Start experiment message listener thread
    self.experiment_message_thread = None
    self.experiment_message_running = False

  def _start_experiment_message_listener(self):
    """Start a thread to listen for messages from the experiment process"""
    def message_listener():
      while self.experiment_message_running:
        try:
          if self.experiment_message_queue and not self.experiment_message_queue.empty():
            message = self.experiment_message_queue.get_nowait()
            # Add the message to the global message queue for the websocket
            message_queue.put(message)
        except queue.Empty:
          time.sleep(0.01)  # Small sleep to prevent busy waiting
        except Exception as e:
          log(f"Error in experiment message listener: {str(e)}", "error")

    self.experiment_message_running = True
    self.experiment_message_thread = threading.Thread(target=message_listener)
    self.experiment_message_thread.daemon = True  # Thread will exit when main program exits
    self.experiment_message_thread.start()

  def _stop_experiment_message_listener(self):
    """Stop the experiment message listener thread"""
    self.experiment_message_running = False
    if self.experiment_message_thread:
      self.experiment_message_thread.join(timeout=1.0)
      self.experiment_message_thread = None

  def get_io_input_state(self):
    return self.io.get_input_states()

  async def _test_water_delivery(self):
    try:
      self.io.set_water_port(True)
      await asyncio.sleep(2)  # Non-blocking sleep
      self.io.set_water_port(False)
    except Exception as e:
      self.test_state["test_water_delivery"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      log(f"Could not activate water delivery: {str(e)}", "error")

    if self.test_state["test_water_delivery"]["state"] == TEST_STATES["RUNNING"]:
      self.test_state["test_water_delivery"]["state"] = TEST_STATES["PASSED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      log("Test water delivery passed", "success")

  def test_water_delivery(self):
    log("Testing water delivery", "start")
    self.test_state["test_water_delivery"]["state"] = TEST_STATES["RUNNING"]

    # Run the test in the event loop instead of a separate thread
    asyncio.create_task(self._test_water_delivery())

  def _test_actuators(self):
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
        self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
        message_queue.put({"type": "test_state", "data": self.test_state})
        return

    if input_state["left_lever"] != True:
      log("Left actuator did not move to `True`", "error")
      self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
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
        self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
        message_queue.put({"type": "test_state", "data": self.test_state})
        return

    if input_state["right_lever"] != True:
      log("Right actuator did not move to `True`", "error")
      self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      return

    log("Right actuator test passed", "success")

    # Set test to passed
    if self.test_state["test_actuators"]["state"] == TEST_STATES["RUNNING"]:
          self.test_state["test_actuators"]["state"] = TEST_STATES["PASSED"]
          message_queue.put({"type": "test_state", "data": self.test_state})
          log("Actuators test passed", "success")

  def test_actuators(self):
    log("Testing actuators", "start")
    self.test_state["test_actuators"]["state"] = TEST_STATES["RUNNING"]

    # Step 1: Test that both actuators default to 0.0
    input_state = self.io.get_input_states()
    if input_state["left_lever"] != False:
      log("Left actuator did not default to `False`", "error")
      self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      return

    if input_state["right_lever"] != False:
      log("Right actuator did not default to `False`", "error")
      self.test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      return
    log("Actuators defaulted to `False`", "success")

    # Run the test in a separate thread
    actuator_test_thread = threading.Thread(target=self._test_actuators)
    actuator_test_thread.start()

  def _test_ir(self):
    # Step 1: Test that the IR is broken
    log("Waiting for IR input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self.io.get_input_states()
      log(f"IR input state: {input_state['nose_poke']}", "info")
      if input_state["nose_poke"] == False:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        log("Timed out while waiting for IR input", "error")
        self.test_state["test_ir"]["state"] = TEST_STATES["FAILED"]
        message_queue.put({"type": "test_state", "data": self.test_state})
        return

    if input_state["nose_poke"] != False:
      log("No IR input detected", "error")
      self.test_state["test_ir"]["state"] = TEST_STATES["FAILED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      return

    # Set test to passed
    if self.test_state["test_ir"]["state"] == TEST_STATES["RUNNING"]:
      self.test_state["test_ir"]["state"] = TEST_STATES["PASSED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      log("IR test passed", "success")

  def test_ir(self):
    log("Testing IR", "start")
    self.test_state["test_ir"]["state"] = TEST_STATES["RUNNING"]
    # Run the test in a separate thread
    ir_test_thread = threading.Thread(target=self._test_ir)
    ir_test_thread.start()

  def run_test(self, command):
    if command == "test_water_delivery":
      self.test_water_delivery()
    elif command == "test_actuators":
      self.test_actuators()
    elif command == "test_ir":
      self.test_ir()

  def run_experiment(self, command):
    primary_command = command.split(" ")[0]
    arguments = command.split(" ")[1:]

    if self.current_experiment and self.current_experiment.process.is_alive():
      log("Experiment already running", "warning")
      return

    if primary_command == "start_experiment":
      try:
        # Create a new message queue for this task
        self.experiment_message_queue = multiprocessing.Queue()

        # Start the message listener
        self._start_experiment_message_listener()

        # Import and instantiate the task with the message queue
        self.current_experiment = Experiment(arguments[0], self.experiment_message_queue)
        self.current_experiment.run()
        log("Started experiment", "success")
      except Exception as e:
        log(f"Failed to start experiment: {str(e)}", "error")
        self._stop_experiment_message_listener()
        self.experiment_message_queue = None

  def stop_experiment(self):
    """Stop the current experiment"""
    if self.current_experiment:
      self.current_experiment.stop()
      self.current_experiment = None

      # Stop the message listener and cleanup
      self._stop_experiment_message_listener()
      self.experiment_message_queue = None

      log("Stopped current experiment", "info")

DEVICE = Device()

async def send_queued_messages(websocket):
  """
  Sends messages from the message queue to the control panel.
  """
  while True:
    try:
      # Check if there are messages in the queue
      while not message_queue.empty():
        message_data = message_queue.get()
        await websocket.send(json.dumps(message_data))
      await asyncio.sleep(0.05)  # Sleep for 50ms
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def send_state_message(websocket):
  """
  Sends the current state of the device to the control panel.
  """
  while True:
    try:
      await websocket.send(json.dumps({"type": "input_state", "data": DEVICE.get_io_input_state()}))
      await asyncio.sleep(0.05)
    except websockets.exceptions.ConnectionClosed:
      log("Control panel connection closed", "warning")
      break

async def handle_message(websocket):
  """
  Handles incoming messages from the WebSocket connection.
  """
  # Log new connection
  log("Control panel connected", "info")

  # Start the periodic message sending in the background
  asyncio.create_task(send_queued_messages(websocket))
  asyncio.create_task(send_state_message(websocket))
  try:
    async for message in websocket:
      log(f"Received message: {message}", "info")

      # Parse the message
      primary_command = message.split(" ")[0]

      if primary_command in TEST_COMMANDS:
        DEVICE.run_test(message)
      elif primary_command in EXPERIMENT_COMMANDS:
        DEVICE.run_experiment(message)
      else:
        log(f"Unknown command: {message}", "error")
  except websockets.exceptions.ConnectionClosed:
    log("Control panel connection closed during message handling", "warning")

async def listen():
  """
  Listens for WebSocket connections and handles incoming messages.
  """
  async with websockets.serve(handle_message, HOST, PORT):
    log(f"Listening on port {PORT}", "success")
    await asyncio.Future()

def main():
  log("Starting listener...", "start")
  asyncio.run(listen())

if __name__ == "__main__":
  main()
