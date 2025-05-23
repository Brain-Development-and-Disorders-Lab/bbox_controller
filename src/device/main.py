import asyncio
import threading
import time
import websockets
import json
import queue  # Import the queue module

from controllers.IOController import IOController
from controllers.DisplayController import DisplayController
from util import log

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

  def get_io_input_state(self):
    return self.io.get_input_states()

  def test_water_delivery_task(self):
    try:
      self.io.set_water_port(True)
      time.sleep(2)
      self.io.set_water_port(False)
    except:
      log("Could not activate water delivery", "error")
      self.test_state["test_water_delivery"]["state"] = TEST_STATES["FAILED"]

    if self.test_state["test_water_delivery"]["state"] == TEST_STATES["RUNNING"]:
      self.test_state["test_water_delivery"]["state"] = TEST_STATES["PASSED"]
      message_queue.put({"type": "test_state", "data": self.test_state})
      log("Test water delivery passed", "success")

  def test_water_delivery(self):
    log("Testing water delivery", "start")
    self.test_state["test_water_delivery"]["state"] = TEST_STATES["RUNNING"]

    # Run the test in a separate thread
    water_delivery_test_thread = threading.Thread(target=self.test_water_delivery_task)
    water_delivery_test_thread.start()

  def test_actuators_task(self):
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
    actuator_test_thread = threading.Thread(target=self.test_actuators_task)
    actuator_test_thread.start()

  def test_ir_task(self):
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
        self.test_state["test_ir"]["state"] = TEST_STATES["FAILED"]
        return

    if input_state["nose_poke"] != False:
      log("IR was not broken", "error")
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
    ir_test_thread = threading.Thread(target=self.test_ir_task)
    ir_test_thread.start()

  def run_test(self, command_name):
    if command_name == "test_water_delivery":
      self.test_water_delivery()
    elif command_name == "test_actuators":
      self.test_actuators()
    elif command_name == "test_ir":
      self.test_ir()

  def run_experiment_test(self):
    log("Running experiment: `test`", "start")
    self.display.start_fullscreen()

  def run_experiment(self, command_name):
    if command_name == "run_experiment_test":
      self.run_experiment_test()

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
      if message in TEST_COMMANDS:
        DEVICE.run_test(message)
      elif message in EXPERIMENT_COMMANDS:
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
