# Behavior Box Controller

This repository contains the code to control a behavior box utilizing IO and displays.

## Control Panel

The control panel facilitates wireless monitoring and control via Websockets. To launch the control panel, run `python3 src/control_panel/main.py`.

Use the *Connection* frame to connect to the device using an IP address and port number. The *Console* frame shows the live console output from the device. The *Input Status* frame shows the current state of the device IO with low latency. The *Test Status* frame allows the IO to be tested, specifically the water deliver, actuators, and the IR beam.

### Experiment Management

**Basic Experiments**: To run a basic experiment, enter the animal ID in the *Experiment Management* frame and click the *Start* button.

**Timeline Experiments**: For advanced experiment protocols, use the timeline management system:
1. Click *Edit Timeline* to open the timeline editor
2. Create custom experiment protocols with multiple trial types
3. Save and manage timelines
4. Upload timelines to the device
5. Execute timeline-based experiments

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

## Starting the Device and Access Point

The startup script is located in the `src/device` directory. To start both the WiFi Access Point and the device controller, run:

```bash
sudo ./start.sh
```

For testing to avoid SSID conflicts, use the `--test` flag:
```bash
sudo ./start.sh --test
```

This is the only script you need to run. It will automatically set up the AP, launch the device controller, and handle all dependencies and logging. All logs are saved in the `logs/` directory.

### Log Files

The startup script generates three log files in the `src/device/logs/` directory:

- **`startup.log`** - Main startup script execution and WiFi AP setup
- **`ap.log`** - WiFi access point configuration and status
- **`run.log`** - Device controller runtime output and experiment data

## Default WiFi Access Point Settings

- **SSID:** `BehaviorBox_0`
- **Password:** `behaviorbox0`
- **Device IP Address:** `192.168.4.1`

These are the default credentials for connecting to the device's WiFi network.

## Data Management

Datasets are stored under the `src/device/data` directory in individual JSON files named `[Animal ID]_[Date]_[Time].json`. Currently, datasets are only stored locally and must be copied via USB or uploaded online to platforms such as Box or RIS.

Datasets follow this format:

```json
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
      // ... Other Trial Parameters ...
    },
    ...
  ],
  "task": {
    "config": {
      // [Variable Name]: [Variable Value], ...
    },
    "timestamp": [Starting Task Timestamp]
  }
}
```

### Version Tracking

The device code includes version tracking to help identify which version is running on the device. The version is stored in `src/device/config.json` and is displayed on the device screen and logged in the control panel.

- Displayed on the device's waiting screen
- Sent to the control panel via WebSocket
- Logged in the control panel console when connected

## Issues and Feedback

Please contact **Henry Burgess** <henry.burgess@wustl.edu> for all code-related issues and feedback.

## License

<!-- CC BY-NC-SA 4.0 License -->
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
  <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" />
</a>
<br />
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.
