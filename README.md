# Behavior Box Controller

Software for running behavioral training sessions on a behavior box. A Raspberry Pi in each box runs the device application, which reads the levers and nose poke, drives the lights, water valve, and stimulus displays, and records session data. The dashboard is a desktop application that connects to one or more devices over the network to run sessions, test hardware, and copy data.

![The dashboard connected to a simulated device, with a session running. The left panel lists devices and shows the selected device's information. The right panel shows session controls, input status, hardware tests, session statistics, and the device's console log.](dashboard.png)

## Repository Structure

```text
bbox_controller/
├── dashboard/   Electron desktop application (React, TypeScript)
├── device/      Device application (C++17, SDL3)
└── shared/      Message definitions and example protocol files used by both
```

| Component | Description | Documentation |
| --- | --- | --- |
| Device | Runs on the behavior box. Hosts a WebSocket server, runs sessions, and stores data. Runs in simulation mode on macOS. | [device/README.md](device/README.md) |
| Dashboard | Connects to devices, runs sessions, tests hardware, edits protocols, and syncs data. | [dashboard/README.md](dashboard/README.md) |
| Trials | How to implement new training stages and trial types on the device. | [device/src/session/trials/README.md](device/src/session/trials/README.md) |
| Messages | The WebSocket messages and protocol file format shared by both applications. | [shared/README.md](shared/README.md) |

## Getting Started

Both applications can run on one Mac for development, with the device in simulation mode.

1. Build and start the device:

   ```bash
   cd device
   make mac
   ./dist/mac/behavior_box_device
   ```

2. In another terminal, start the dashboard:

   ```bash
   cd dashboard
   yarn install
   yarn vite:dev
   ```

3. In a third terminal, open the dashboard window:

   ```bash
   cd dashboard
   yarn electron:dev
   ```

4. In the dashboard, click *Add Device*, keep the default address `localhost` and port `8765`, and click *Connect*.

## Sessions and Protocols

A session runs a task protocol for one subject. A protocol is a JSON file containing a timeline of training trials and intervals, along with the timing parameters the trials use. Protocols are created and edited in the dashboard. An example is in [shared/protocols/example.json](shared/protocols/example.json).

## Data

Each device stores session data under `~/bbox_data`, in the layout used by the International Brain Laboratory (IBL):

```text
~/bbox_data/Subjects/<subject>/<yyyy-mm-dd>/<NNN>/
├── raw_task_data_00/
│   ├── _bbox_taskData.raw.jsonable      One JSON object per trial
│   ├── _bbox_taskSettings.raw.json      Session settings and totals
│   └── _bbox_taskProtocol.raw.json      The protocol file as it was run
└── alf/
    └── _ibl_trials.table.csv            One row per trial, IBL trials columns
```

`<NNN>` is the session number for that subject and day, starting at `001`. The dashboard's *Sync Data* button copies new files from a device into a chosen folder. See [device/README.md](device/README.md#session-data) for details of each file.

## Versions

| Application | Version is set in |
| --- | --- |
| Device | `kDeviceVersion` in [device/src/version.h](device/src/version.h) |
| Dashboard | `version` in [dashboard/package.json](dashboard/package.json) |

The device version is printed at startup and shown in the dashboard's *Device Information* panel while connected. The dashboard version is saved in each protocol file it writes.

### Releases

Ready-to-use versions of the dashboard and device are available on the [Releases](https://github.com/Brain-Development-and-Disorders-Lab/bbox_controller/releases) page. Open the latest release and download the relevant file:

| Download | Platform |
| --- | --- |
| `bbox-dashboard-<version>-mac-arm64.dmg` | Dashboard on Macs with Apple silicon (M1 or later) |
| `bbox-dashboard-<version>-mac-x64.dmg` | Dashboard on Macs with Intel processors |
| `bbox-dashboard-<version>-win-x64.exe` | Dashboard on Windows |
| `bbox-device-<version>-pi-arm64.tar.gz` | Device on a behavior box's Raspberry Pi, running 64-bit Raspberry Pi OS Trixie or later |
| `bbox-device-<version>-mac-arm64.tar.gz` | Device in simulation mode on Macs with Apple silicon, for trying the software without a behavior box |

**Dashboard on macOS:** open the `.dmg` and drag *Behavior Box Dashboard* into *Applications*. The first time it is opened, macOS blocks it because it is not from an identified developer. Open *System Settings*, go to *Privacy & Security*, and click *Open Anyway*. If macOS instead says the app is damaged, run `xattr -cr "/Applications/Behavior Box Dashboard.app"` in Terminal, then open it again.

**Dashboard on Windows:** run the `.exe` installer. If Windows shows *Windows protected your PC*, click *More info*, then *Run anyway*.

**Device on the Raspberry Pi:** install the SDL libraries, then extract and run the device:

```bash
sudo apt install libsdl3-0 libsdl3-ttf0
tar -xzf bbox-device-<version>-pi-arm64.tar.gz
cd bbox-device-<version>-pi-arm64
./behavior_box_device
```

See [device/README.md](device/README.md#raspberry-pi) for setting the device's name and connecting to it over Wi-Fi.

**Device on macOS:** install SDL with [Homebrew](https://brew.sh) using `brew install sdl3 sdl3_ttf`, then extract the `.tar.gz` and run `./behavior_box_device` from the extracted folder.

## Issues and Feedback

Contact **Henry Burgess** <henry.burgess@wustl.edu> for code-related issues and feedback.

## License

[![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).
