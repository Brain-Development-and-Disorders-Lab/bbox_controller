# Dashboard

The dashboard is an Electron desktop application for running behavior box devices. It connects to devices over the network to run sessions, test hardware, create and edit task protocols, view device logs, and copy session data.

## Requirements

- Node.js
- Yarn

Install the dependencies from this folder:

```bash
yarn install
```

## Running

The dashboard runs in two parts during development: the Vite server for the interface, and Electron for the window. Start each in its own terminal:

```bash
yarn vite:dev
```

```bash
yarn electron:dev
```

The interface reloads when files in `src/` change. Changes to `main.js` or `preload.js` require restarting `yarn electron:dev`.

| Script | Description |
| --- | --- |
| `yarn vite:dev` | Starts the Vite development server on port 5173 |
| `yarn electron:dev` | Opens the dashboard window using the development server, with developer tools open |
| `yarn vite:build` | Builds the interface into `dist/` |
| `yarn electron:build` | Builds the interface and packages the application with electron-builder |

## Using the Dashboard

The left side of the window lists devices and shows information about the selected device. The right side has a tab for each device.

### Devices

Click *Add Device* and enter a name, IP address, and port. The device's address is shown on its displays. A device running on the same computer uses `localhost` and port `8765`. Two devices cannot have the same address and port. Devices are saved in `devices.json` in the application's user data folder and are loaded at startup.

Click *Select* on a device in the list to show its information and tab. Click *Edit* to change or remove a device. A device must be disconnected to edit it.

### Connecting

Select a device and click *Connect* under *Device Information*. The icon on the device's tab shows its state:

| Icon | State |
| --- | --- |
| Red | Disconnected |
| Pulsing orange | Connecting |
| Green | Connected |
| Pulsing green | Running a session |

While connected, *Device Information* shows the device's software version, platform, hostname, operating system, start time, and free storage.

### Device Tab

| Section | Description |
| --- | --- |
| Session controls | Subject, protocol, and *Start Session* and *Stop Session* buttons |
| Input Status | Live state of each lever, light, nose poke, and the water valve |
| Test Status | Hardware tests. Output tests run for the duration entered next to them. Input tests pass when the input is triggered within 10 seconds. |
| Session Statistics | Trial counts, presses, nose pokes, and rewards for the current session, the active trial, elapsed times, and the session's folder on the device |
| Console | Log messages from the device. Recent messages are sent when the dashboard connects. |

### Running a Session

1. Enter the subject.
2. Click *Choose a protocol file...*, select a protocol, review it, and click *Confirm*.
3. Click *Start Session*.

The session runs until the protocol's timeline finishes or *Stop Session* is clicked. If the timeline is set to loop, it runs until stopped. The device records the session to its own storage as it runs.

### Protocols

Click *New Protocol* to create a protocol, or *Edit Protocol* to change the loaded one. In the editor:

- Click *Add Trial* to add an interval or a training stage after the selected item.
- Select an item to change its repeat count, interval duration, or parameter overrides, move it up or down, or remove it.
- Set the protocol's default parameters.
- Check *Loop Protocol Timeline* to restart the timeline when it ends.

Click *Save* to write the protocol to a JSON file. The protocol is checked before saving, and any problems are listed in the editor. The file format is described in [shared/README.md](../shared/README.md#protocol-files).

### Syncing Data

Click *Sync Data* while connected and choose a folder. The device sends every file in its data folder that is not already in the chosen folder, and the files are written to the same paths under it, for example `<folder>/Subjects/<subject>/<date>/<NNN>/`. Existing files are never overwritten, and the device keeps its own copies. Files from a session that is still running are skipped until it ends.

## Source Layout

```text
dashboard/
├── main.js                  Electron main process: device connections, data sync, file access
├── preload.js               The `window.dashboardAPI` bridge between the main process and the interface
├── types/index.d.ts         Shared TypeScript types, including `DashboardAPI`
└── src/
    ├── App.tsx              Device list, device information, and device tabs
    ├── components/          Interface components, one folder each
    └── lib/
        ├── protocol.ts      Protocol defaults, validation, and serialization
        └── util.ts          Shared helpers
```

The main process holds one WebSocket connection per connected device. Messages from devices are validated in `main.js` and forwarded to the interface over IPC channels. The interface sends commands back through `window.dashboardAPI`.

The interface uses React with [Blueprint](https://blueprintjs.com/) components. Protocol files and device messages are validated with [Zod](https://zod.dev/).

## Extending the Dashboard

### Adding a Device Message

To receive a new message type from the device:

1. In `main.js`, add a schema for the message to `DeviceMessageSchema` and a handler to `deviceMessageHandlers`. The handler usually forwards the message to the interface with `notifyDashboard("<channel>", payload)`.
2. In `preload.js`, add a subscription function, for example `onDeviceExample: (callback) => subscribe("device-example", callback)`.
3. In `types/index.d.ts`, add the payload type and the function to `DashboardAPI`.
4. In a component, subscribe in a `useEffect` and return the unsubscribe function it gives back.
5. Document the message in [shared/README.md](../shared/README.md).

Messages with an unknown `type` are logged and ignored. Messages that fail their schema are logged with the reason and ignored.

### Adding a Device Command

Commands are sent with `window.dashboardAPI.deviceCommand(device, { command: "<name>", ... })`. Add the command to `DeviceCommand` in `types/index.d.ts`, to [shared/commands.json](../shared/commands.json), and to [shared/README.md](../shared/README.md). The device must also handle it (see [device/README.md](../device/README.md#dashboard-commands)).

### Adding a Hardware Test

Add the command to `TEST_COMMANDS` in [shared/commands.json](../shared/commands.json), add a row to `TESTS` in `src/components/DeviceTab/index.tsx`, and implement the test on the device in `TestRunner::start()`.

### Adding a Protocol Parameter or Timeline Item Type

Protocol defaults, labels, and schemas are in `src/lib/protocol.ts`, and the matching types are in `types/index.d.ts`. The device reads the same fields, so both applications need updating. See [device/src/session/trials/README.md](../device/src/session/trials/README.md#adding-a-trial-type).

### Version

Update `version` in `package.json` for each release. It is saved as `dashboard_version` in each protocol file the dashboard writes.
