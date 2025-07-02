# Behavior Box Controller

This repository contains the code to control a behavior box utilizing IO and displays.

## Control Panel

The control panel facilitates wireless monitoring and control via Websockets. To launch the control panel, run `python3 src/control_panel/main.py`.

Use the *Connection* frame to connect to the device using an IP address and port number. The *Console* frame shows the live console output from the device. The *Input Status* frame shows the current state of the device IO with low latency. The *Test Status* frame allows the IO to be tested, specifically the water deliver, actuators, and the IR beam.

To run an experiment, enter the animal ID in the *Experiment Management* frame and click the *Start* button.

## Device

Both `input` and `output` controllers are implemented. Inputs include levers and other sensors, outputs include LEDs and display modules.

### Simulation

You can run the device in simulation mode for development and testing without physical hardware. Simulation mode is activated automatically if hardware libraries (e.g., gpiozero) are unavailable.

### Controls in Simulation Mode

- **1**: Left Lever (hold to press)
- **2**: Right Lever (hold to press)
- **3**: Nose Poke (hold to activate)
- **Space**: Nose Poke (alternative)
- **ESC**: Exit

### Hardware Usage

The device controller runs only on the device and the device controller must be on the same network as the control panel software in order to communicate. This is accomplished by setting the Raspberry Pi to act as a wireless access point (AP) and connecting to it directly.

To run the device controller code on the Raspberry Pi, run the `startup.sh` script, located under `src/device` with administrator permissions: `sudo ./startup.sh`

After a short delay, a notification that the wireless connectivity has been disabled should appear before the task starts in fullscreen.

#### Running individual scripts

First, turn off the wireless connectivity on the Raspberry Pi via the top menu bar. After setting execution permissions using `chmod +x`, running `sudo ./setup_ap.sh` starts the Raspberry Pi in AP mode.

In another terminal, use `run.sh` to start the device controller. It is highly recommended to setup the Raspberry Pi as a wireless access point, as it allows direct connectivity to the device without external networking equipment. The network SSID and password can be modified within the script.

Wireless Access Point Defaults:

- SSID: `BehaviorBox_0`
- Password: `behaviorbox0`
- IP Addresss: `192.168.4.1`

### Data Management

Datasets will be stored under the `src/device/data` directory in individual JSON format files with filenames: `[Animal ID]_[Date]_[Time].json`. Currently, datasets are only stored locally and must be copied via USB or uploaded online to platforms such as Box or RIS.

Datasets are the following format:

```text
{
  "metadata": {
    "animal_id": [Animal ID],
    "start_time": [Starting Timestamp],
    "end_time": [Ending Timestamp],
    "trials": [
      {
        "name": [Trial Name],
        "timestamp": [Starting Timestamp]
      },
      ...
    ]
  },
  "trials": [
    {
      "trial_outcome": [Outcome Code],
      "events": [
        {
          "type": [Event Type],
          "timestamp": [Event Timestamp]
        },
        ...
      ],
      "timestamp": [Starting Timestamp],
      "trial_type": [Trial Name]
      ... [Other Trial Parameters]
    },
    ...
  ],
  "task": {
    "config": {
      [Variable Name]: [Variable Value],
      ...
    },
    "timestamp": [Starting Task Timestamp]
  }
}
```

### Version Tracking

The device code includes version tracking to help identify which version is running on the device. The version is stored in `src/device/config.json` and is displayed on the device screen and logged in the control panel.

The version will be:

- Displayed on the device's waiting screen
- Sent to the control panel via WebSocket
- Logged in the control panel console when connected

## License

<!-- CC BY-NC-SA 4.0 License -->
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
  <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" />
</a>
<br />
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

## Issues and Feedback

Please contact **Henry Burgess** <[henry.burgess@wustl.edu](mailto:henry.burgess@wustl.edu)> for all code-related issues and feedback.
