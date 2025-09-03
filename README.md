# Behavior Box Controller

This repository contains the code to control a behavior box utilizing IO and displays.

## Control Panel

The control panel facilitates wireless monitoring and control via Websockets. To launch the control panel, run `./start.sh`, located in the `control_panel` directory.

Use the *Connection* frame to connect to the device using an IP address and port number. The *Console* frame shows the live console output from the device. The *Input Status* frame shows the current state of the device IO with low latency. The *Test Status* frame allows the IO to be tested, specifically the water delivery, levers, and the IR beam.

### Experiment Management

**Basic Experiments**: To run a basic experiment, enter the animal ID in the *Experiment Management* frame and click the *Start* button.

**Timeline Experiments**: For advanced experiment protocols, use the timeline management system:

1. Click *Edit Timeline* to open the timeline editor
2. Create custom experiment protocols with multiple trial types
3. Save and manage timelines

## Device

### Simulation

You can run the device in simulation mode for development and testing without physical hardware. Simulation mode is activated automatically if hardware libraries (e.g., gpiozero) are unavailable.

### Controls in Simulation Mode

- **1**: Left Lever (hold to press)
- **2**: Right Lever (hold to press)
- **3**: Nose Poke (hold to activate)
- **Space**: Nose Poke (alternative)
- **J**: Left Lever Light
- **K**: Nose Poke Light
- **L**: Left Lever Light
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

## Data Files

Data files are stored under the `src/device/data` directory in individual JSON files named `[Animal ID]_[Date]_[Time].json`. A data file is generated for *each* experiment run. Currently, data files are only stored locally and must be copied via USB or uploaded online to platforms such as Box or RIS. All timestamps use ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.microseconds`). The major headings within a data file are listed below, and an example is also shown.

### `experiment_metadata`

Contains metadata about the experiment session including animal identification, timing, configuration parameters, and the experiment definition with trial specifications.

### `experiment_trials`

Records all trials during the experiment, including behavioral events, trial outcomes, and timings. Each trial contains a chronological sequence of events with timestamps.

### `experiment_statistics`

Provides summary statistics for the entire experiment session, including counts of lever presses, nose pokes, and water deliveries.

Example Output:

```json
{
  "experiment_metadata": {
    "animal_id": "test_00",
    "experiment_start": "2025-08-29T11:12:18.836449",
    "experiment_end": "2025-08-29T11:12:35.709546",
    "config": {
      "iti_minimum": 100,
      "iti_maximum": 1000,
      "response_limit": 1000,
      "cue_minimum": 5000,
      "cue_maximum": 10000,
      "hold_minimum": 100,
      "hold_maximum": 1000,
      "valve_open": 100,
      "punish_time": 1000
    },
    "experiment_file": {
      "name": "Test Experiment",
      "trials": [
        {
          "type": "Stage3",
          "id": "Stage3_0",
          "parameters": {
            "cue_duration": 5000,
            "response_limit": 1000,
            "water_delivery_duration": 2000
          }
        }
      ],
      "version": "1.0",
      "loop": true
    }
  },
  "experiment_trials": [
    {
      "trial_outcome": "success",
      "events": [
        {
          "type": "left_lever_press",
          "timestamp": "2025-08-29T11:12:26.558849"
        },
        {
          "type": "nose_port_entry",
          "timestamp": "2025-08-29T11:12:28.607925"
        },
        {
          "type": "reward_triggered",
          "timestamp": "2025-08-29T11:12:30.101765"
        }
      ],
      "trial_start": "2025-08-29T11:12:31.892916",
      "trial_end": "2025-08-29T11:12:31.892917",
      "trial_type": "trial_stage_3"
    }
  ],
  "experiment_statistics": {
    "nose_pokes": 3,
    "left_lever_presses": 2,
    "right_lever_presses": 2,
    "trial_count": 4,
    "water_deliveries": 1
  }
}
```

### Version Tracking

The device code includes version tracking to help identify which version is running on the device. The version is stored in the shared module and is displayed on the device screen and logged in the control panel.

## Issues and Feedback

Please contact **Henry Burgess** <henry.burgess@wustl.edu> for all code-related issues and feedback.

## License

<!-- CC BY-NC-SA 4.0 License -->
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
  <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" />
</a>
<br />
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.
