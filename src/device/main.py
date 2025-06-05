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
    self.io = IOController()
    self.display = DisplayController()
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

    # Initialize pygame in the new process
    pygame.init()

    # Setup screen
    screen_info = pygame.display.Info()
    self.screen = pygame.display.set_mode(
      (screen_info.current_w, screen_info.current_h),
      pygame.FULLSCREEN
    )
    self.screen.fill((0, 0, 0))
    self.width = screen_info.current_w
    self.height = screen_info.current_h
    self.font = pygame.font.SysFont("Arial", 64)

    # Setup trials
    self._current_trial = None
    self._trials = [
      Stage1(),
      Interval(),
      Stage2(),
      Interval(),
      Stage3(),
    ]
    for trial in self._trials:
      trial.screen = self.screen
      trial.font = self.font
      trial.width = self.width
      trial.height = self.height
      trial.io = self.io
      trial.display = self.display

    # Experiment state
    self._experiment_started = False
    self._running = True
    self._websocket_server = None  # Store reference to websocket server

  def _render_waiting_screen(self):
    """Render the waiting screen with 'Waiting for start...' text"""
    self.screen.fill((0, 0, 0))  # Black background
    text = self.font.render("Waiting for start...", True, (255, 255, 255))
    text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
    self.screen.blit(text, text_rect)
    pygame.display.flip()

  def update(self):
    """Update device state and handle events"""
    events = pygame.event.get()

    # Handle quit event
    for event in events:
      if event.type == pygame.QUIT:
        self._running = False
        return False
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          self._running = False
          return False

    if not self._experiment_started:
      # Show waiting screen
      self._render_waiting_screen()
    elif self._current_trial:
      # Update and render current trial
      if not self._current_trial.update(events):
        # Trial is complete, move to next trial
        self._current_trial.on_exit()

        # Save trial data
        trial_data = self._current_trial.get_data()
        if trial_data and self._data:
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
          self._experiment_started = False
          self._current_trial = None

          # Send message that task is complete
          _device_message_queue.put({
            "type": "task_status",
            "data": {
              "status": "completed"
            }
          })

      # Render current trial
      self._current_trial.render()
      pygame.display.flip()

    return True

  def start_experiment(self, animal_id):
    """Start the experiment with the given animal ID"""
    if self._experiment_started:
      log("Experiment already running", "warning")
      return

    # Initialize data controller with animal ID
    self._data = DataController(animal_id)

    # Load config
    with open("config.json") as config_file:
      variables = json.load(config_file)["task"]
      self._data.add_task_data({"config": variables})

    # Start first trial
    self._current_trial = self._trials.pop(0)
    self._current_trial.on_enter()
    self._experiment_started = True

    # Send initial message that task has started
    _device_message_queue.put({
      "type": "task_status",
      "data": {
        "status": "started",
        "trial": self._current_trial.title
      }
    })

    log("Experiment started", "info")

  def stop_experiment(self):
    """Stop the current experiment"""
    if not self._experiment_started:
      log("No experiment running", "warning")
      return

    # Stop the current experiment
    self._experiment_started = False
    self._current_trial = None

    # Save data if available
    if self._data:
      if not self._data.save():
        log("Failed to save data", "error")
      else:
        log("Data saved", "success")

    # Send message that experiment has stopped
    _device_message_queue.put({
      "type": "task_status",
      "data": {
        "status": "stopped"
      }
    })

    log("Experiment stopped", "info")

  async def _test_water_delivery(self):
    try:
      self.io.set_water_port(True)
      await asyncio.sleep(2) # Non-blocking sleep
      self.io.set_water_port(False)
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
      input_state = self.io.get_input_states()
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
      input_state = self.io.get_input_states()
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
    input_state = self.io.get_input_states()
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
      input_state = self.io.get_input_states()
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

  def cleanup(self):
    """Clean up resources before shutdown"""
    # Stop any running experiment
    if self._experiment_started:
      self.stop_experiment()

    # Close pygame
    pygame.quit()

    # Clean up controllers
    if hasattr(self, 'io'):
      del self.io
    if hasattr(self, 'display'):
      del self.display

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

async def handle_connection(websocket, device: Device):
  """Handle a single websocket connection"""
  try:
    # Start message sender tasks
    message_sender_task = asyncio.create_task(send_queued_messages(websocket))
    state_sender_task = asyncio.create_task(send_state_message(websocket))

    # Handle incoming messages
    async for message in websocket:
      try:
        command = message.strip()

        # Handle the command
        if command in TEST_COMMANDS:
          device.run_test(command)
        elif command.startswith("start_experiment"):
          # Extract animal_id from command string
          parts = command.split(" ")
          animal_id = parts[1] if len(parts) > 1 else ""
          if animal_id:
            device.start_experiment(animal_id)
          else:
            log("Missing animal ID for start_experiment command", "error")
        elif command == "stop_experiment":
          device.stop_experiment()
        else:
          log(f"Unknown command: {command}", "error")
      except Exception as e:
        log(f"Error handling message: {str(e)}", "error")

    # Cleanup sender tasks
    message_sender_task.cancel()
    state_sender_task.cancel()
    try:
      await asyncio.wait_for(asyncio.gather(message_sender_task, state_sender_task), timeout=1.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
      pass
  except websockets.exceptions.ConnectionClosed:
    pass
  finally:
    await websocket.close()

async def main_loop(device):
  """Main loop that runs both pygame and websocket communication"""
  log("Starting main loop", "info")

  # Create websocket server
  server = await websockets.serve(
    lambda ws: handle_connection(ws, device),
    HOST,
    PORT
  )
  device._websocket_server = server

  try:
    # Main loop
    while device._running:
      # Update device state
      if not device.update():
        log("Initiating shutdown...", "info")
        break

      # Process websocket messages
      await asyncio.sleep(0)  # Allow other tasks to run
      await asyncio.sleep(1/60)
  finally:
    if device._data:
      log("Saving data before shutdown...", "info")
      try:
        if device._data.save():
          log("Data saved successfully", "success")
        else:
          log("Failed to save data", "error")
      except Exception as e:
        log(f"Error while saving data: {str(e)}", "error")

    # Cleanup
    if device._websocket_server:
      active_connections = list(device._websocket_server.websockets)
      if active_connections:
        for websocket in active_connections:
          try:
            await asyncio.wait_for(websocket.close(), timeout=0.5)
          except (asyncio.TimeoutError, Exception) as e:
            log(f"Error closing connection, connection may already be closed", "warning")

      # Close the server immediately
      device._websocket_server.close()

    # Cancel any remaining tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
      log(f"Cancelling {len(tasks)} remaining tasks...", "info")
      for task in tasks:
        task.cancel()
        try:
          await asyncio.wait_for(task, timeout=0.5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
          pass

    device.cleanup()
    log("Main loop stopped", "info")

def main():
  global _device, _device_message_queue

  try:
    # Initialize the device
    _device = Device()
    _device_message_queue = queue.Queue()

    # Set the message queue in the logging module
    set_message_queue(_device_message_queue)

    # Run the main loop
    asyncio.run(main_loop(_device))
  except KeyboardInterrupt:
    log("Keyboard interrupt received", "info")
  except asyncio.TimeoutError:
    log("Main loop timed out", "error")
  except Exception as e:
    log(f"Error in main loop: {str(e)}", "error")
  finally:
    # Ensure cleanup happens even if there's an error
    if _device:
      _device.cleanup()

if __name__ == "__main__":
  main()
