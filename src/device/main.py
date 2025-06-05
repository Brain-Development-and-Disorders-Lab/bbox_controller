import asyncio
import threading
import time
import websockets
import json
import queue
import pygame
from controllers.IOController import IOController
from controllers.DisplayController import DisplayController
from controllers.DataController import DataController
from trials import Interval, Stage1, Stage2, Stage3
from logger import log, set_message_queue

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

# Other variables
HOST = ""  # Listen on all available interfaces
PORT = 8765
INPUT_TEST_TIMEOUT = 10 # seconds

# Create a global device and message queue
_device = None
_device_message_queue = None

class Device:
  def __init__(self):
    # Initialize controllers
    self._io = IOController()
    self._display = DisplayController()
    self._data = None

    # Setup display state
    self._display_state = {
      "mini_display_1": {
        "state": False,
      },
      "mini_display_2": {
        "state": False,
      },
    }

    # Test state
    self._test_state = {
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

    self._input_states = {
      "left_lever": False,
      "right_lever": False,
      "nose_poke": False,
      "water_port": False,
    }

    # Experiment
    self._current_experiment = None
    self._experiment_log_queue = None
    self._experiment_io_queue = None

    # Start experiment message listener thread
    self._experiment_message_thread = None
    self._experiment_message_running = False

    # Initialize pygame in the new process
    pygame.init()

    # Setup screen
    screen_info = pygame.display.Info()
    screen = pygame.display.set_mode(
      (screen_info.current_w, screen_info.current_h),
      pygame.FULLSCREEN
    )
    screen.fill((0, 0, 0))

    # Setup trials
    self._current_trial = None
    self._trials = [
      Stage1(),
      Interval(),
      Stage2(),
      Interval(),
      Stage3(),
    ]
    font = pygame.font.SysFont("Arial", 64)
    for trial in self._trials:
      trial.screen = screen
      trial.font = font
      trial.width = screen_info.current_w
      trial.height = screen_info.current_h
      trial.io = self._io
      trial.display = self._display

  async def _test_water_delivery(self):
    try:
      self._io.set_water_port(True)
      await asyncio.sleep(2) # Non-blocking sleep
      self._io.set_water_port(False)
    except Exception as e:
      self._test_state["test_water_delivery"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log(f"Could not activate water delivery: {str(e)}", "error")

    if self._test_state["test_water_delivery"]["state"] == TEST_STATES["RUNNING"]:
      self._test_state["test_water_delivery"]["state"] = TEST_STATES["PASSED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Test water delivery passed", "success")

  def test_water_delivery(self):
    log("Testing water delivery", "start")
    self._test_state["test_water_delivery"]["state"] = TEST_STATES["RUNNING"]
    asyncio.create_task(self._test_water_delivery())

  def _test_actuators(self):
    # Step 2: Test that the left actuator can be moved to 1.0
    log("Testing left actuator", "start")
    log("Waiting for left actuator input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self._io.get_input_states()
      if input_state["left_lever"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
        _device_message_queue.put({"type": "test_state", "data": self._test_state})
        log("Left actuator input timed out", "error")
        return

    if input_state["left_lever"] != True:
      self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Left actuator did not move to 1.0", "error")
      return

    log("Left actuator test passed", "success")

    # Step 3: Test that the right actuator can be moved to 1.0
    running_input_test = True
    running_input_test_start_time = time.time()
    log("Testing right actuator", "start")
    log("Waiting for right actuator input...", "info")
    while running_input_test:
      input_state = self._io.get_input_states()
      if input_state["right_lever"] == True:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
        _device_message_queue.put({"type": "test_state", "data": self._test_state})
        log("Right actuator input timed out", "error")
        return

    if input_state["right_lever"] != True:
      self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Right actuator did not move to 1.0", "error")
      return

    log("Right actuator test passed", "success")

    # Set test to passed
    if self._test_state["test_actuators"]["state"] == TEST_STATES["RUNNING"]:
      self._test_state["test_actuators"]["state"] = TEST_STATES["PASSED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Actuators test passed", "success")

  def test_actuators(self):
    log("Testing actuators", "start")
    self._test_state["test_actuators"]["state"] = TEST_STATES["RUNNING"]

    # Step 1: Test that both actuators default to 0.0
    input_state = self._io.get_input_states()
    if input_state["left_lever"] != False:
      self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Left actuator did not default to 0.0", "error")
      return

    if input_state["right_lever"] != False:
      self._test_state["test_actuators"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("Right actuator did not default to 0.0", "error")
      return

    log("Actuators defaulted to 0.0", "success")

    # Run the test in a separate thread
    actuator_test_thread = threading.Thread(target=self._test_actuators)
    actuator_test_thread.start()

  def _test_ir(self):
    # Step 1: Test that the IR is broken
    log("Waiting for IR input...", "info")
    running_input_test = True
    running_input_test_start_time = time.time()
    while running_input_test:
      input_state = self._io.get_input_states()
      if input_state["nose_poke"] == False:
        running_input_test = False

      # Ensure test doesn't run indefinitely
      if time.time() - running_input_test_start_time > INPUT_TEST_TIMEOUT:
        self._test_state["test_ir"]["state"] = TEST_STATES["FAILED"]
        _device_message_queue.put({"type": "test_state", "data": self._test_state})
        log("Timed out while waiting for IR input", "error")
        return

    if input_state["nose_poke"] != False:
      self._test_state["test_ir"]["state"] = TEST_STATES["FAILED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("No IR input detected", "error")
      return

    # Set test to passed
    if self._test_state["test_ir"]["state"] == TEST_STATES["RUNNING"]:
      self._test_state["test_ir"]["state"] = TEST_STATES["PASSED"]
      _device_message_queue.put({"type": "test_state", "data": self._test_state})
      log("IR test passed", "success")

  def test_ir(self):
    log("Testing IR", "start")
    self._test_state["test_ir"]["state"] = TEST_STATES["RUNNING"]

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

    if self._current_experiment and self._current_experiment.process.is_alive():
      log("Experiment already running", "warning")
      return

    if primary_command == "start_experiment":
      # Initialize data controller
      self._data = DataController(arguments[0])

      # Load config
      with open("config.json") as config_file:
        variables = json.load(config_file)["task"]
        self._data.add_task_data({"config": variables})

      # Run first screen
      self._current_trial = self._trials.pop(0)
      self._current_trial.on_enter()

      # Send initial message that task has started
      _device_message_queue.put({
        "type": "task_status",
        "data": {
          "status": "started",
          "trial": self._current_trial.title
        }
      })

      running = True
      try:
        while running:
          events = pygame.event.get()

          # Handle screen events
          if not self._current_trial.update(events):
            # Screen is complete, run next screen
            self._current_trial.on_exit()

            # Save screen data before moving to next screen
            trial_data = self._current_trial.get_data()
            if trial_data:
              self._data.add_trial_data(self._current_trial.title, trial_data)

            log("Finished trial: " + self._current_trial.title, "info")

            # Send message about trial completion
            _device_message_queue.put({
              "type": "trial_complete",
              "data": {
                "trial": self._current_trial.title,
                "data": trial_data
              }
            })

            if len(self._trials) > 0:
              self._current_trial = self._trials.pop(0)
              self._current_trial.on_enter()

              # Send message about new trial starting
              _device_message_queue.put({
                "type": "trial_start",
                "data": {
                  "trial": self._current_trial.title
                }
              })
            else:
              running = False
              # Send message that task is complete
              _device_message_queue.put({
                "type": "task_status",
                "data": {
                  "status": "completed"
                }
              })

          # Render
          self._current_trial.render()
          pygame.display.flip()

          # Cap frame rate
          pygame.time.wait(16)

      finally:
        log("Experiment finished", "info")
        if not self._data.save():
          log("Failed to save data", "error")
        else:
          log("Data saved", "success")

        pygame.quit()

  def stop_experiment(self):
    """Stop the current experiment"""
    if self.current_experiment:
      self.current_experiment.stop()
      self.current_experiment = None

      # Stop the message listener and cleanup
      self._stop_experiment_message_listener()
      self.experiment_log_queue = None
      self.experiment_io_queue = None

      log("Stopped current experiment", "info")

async def send_queued_messages(websocket):
  """
  Sends messages from the message queue to the control panel.
  """
  while True:
    try:
      # Check if there are messages in the queue
      while not _device_message_queue.empty():
        message_data = _device_message_queue.get()
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
      await websocket.send(json.dumps({"type": "input_state", "data": _device.get_io_input_state()}))
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
        _device.run_test(message)
      elif primary_command in EXPERIMENT_COMMANDS:
        _device.run_experiment(message)
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
  global _device, _device_message_queue

  # Initialize the device
  _device = Device()
  _device_message_queue = queue.Queue()

  # Set the message queue in the logging module
  set_message_queue(_device_message_queue)

  # Start the listener
  log("Starting listener...", "start")
  asyncio.run(listen())

if __name__ == "__main__":
  main()
