# Shared Definitions

This folder holds definitions used by both the device and the dashboard.

| File | Contents |
| --- | --- |
| `commands.json` | Names of the commands the dashboard can send. The dashboard reads `TEST_COMMANDS` to decide which test commands to send. |
| `protocols/example.json` | An example protocol file |

## Messages

The device runs a WebSocket server, on port `8765` by default, and the dashboard connects to it as a client. Each message is a single JSON object sent as a text frame. Messages from the dashboard have a `command` field, and messages from the device have a `type` field.

### Dashboard to Device

| Command | Fields | Description |
| --- | --- | --- |
| `session_start` | `subject` (string), `protocol` (protocol file object) | Starts a session. A running session is stopped first. The device replies with `session_state`, or logs an error if the subject is empty, the protocol is invalid, a trial is not implemented, or the session files cannot be created. |
| `session_stop` | None | Stops the running session. The trial in progress is recorded. |
| `data_sync` | `exclude` (array of strings) | Requests every data file not named in `exclude`. Names are paths relative to the device's data folder, such as `Subjects/M001/2026-10-22/001/alf/_ibl_trials.table.csv`. The device replies with `data_file` messages followed by `data_sync_complete`. |
| `test_water_delivery` | `parameter` (integer, ms) | Opens the water valve for `parameter` milliseconds |
| `test_led_levers` | `parameter` (integer, ms) | Turns both lever lights on for `parameter` milliseconds |
| `test_led_port` | `parameter` (integer, ms) | Turns the nose light on for `parameter` milliseconds |
| `test_displays` | `parameter` (integer, ms) | Fills every display with white for `parameter` milliseconds |
| `test_input_levers` | `parameter` (ignored) | Passes once both levers have been pressed, or fails after 10 seconds |
| `test_input_ir` | `parameter` (ignored) | Passes once the nose poke is triggered, or fails after 10 seconds |

Sending a test command while that test is running restarts it. The device logs a warning for an unknown command and otherwise ignores it.

### Device to Dashboard

| Type | Fields | Description |
| --- | --- | --- |
| `device_info` | `version`, `simulated`, `hostname`, `os`, `started_at`, `storage_free_bytes` | Sent when a dashboard connects. `started_at` is milliseconds since the Unix epoch. `storage_free_bytes` is the free space on the data drive at connection time, or -1 if it cannot be read. |
| `log` | `level`, `timestamp`, `message` | A device log message. `level` is `trace`, `debug`, `info`, `warning`, `error`, or `critical`, and `timestamp` is milliseconds since the Unix epoch. |
| `test_state` | `test`, `state` | A hardware test changed state. `state` is `running`, `passed`, or `failed`. |
| `input_state` | `state` | The state of every input and output, as an object of booleans keyed `left_lever`, `right_lever`, `nose_poke`, `left_lever_light`, `right_lever_light`, `nose_light`, and `water_valve`. Sent when any of them changes. |
| `session_state` | `state`, `protocol_name`, `subject`, `session_path`, `session_elapsed_ms`, `trial`, `statistics` | The session's progress. Sent when a trial starts, when statistics change, and when the session ends. See below. |
| `data_file` | `name`, `contents` | One data file, in reply to `data_sync`. `name` is its path relative to the data folder, and `contents` is the file's text. |
| `data_sync_complete` | `error` (optional) | All files for a `data_sync` have been sent |

#### `session_state` Fields

| Field | Description |
| --- | --- |
| `state` | `idle`, `running`, `completed`, or `stopped` |
| `protocol_name` | Name of the protocol, empty before the first session |
| `subject` | Subject of the session, empty before the first session |
| `session_path` | The session's folder relative to the data folder, such as `Subjects/M001/2026-10-22/001`, empty before the first session |
| `session_elapsed_ms` | Time since the session started, measured when the message was sent |
| `trial` | While running, an object with `trial_num` (from 0), `item_id` (the timeline item's `id`), and `elapsed_ms`. Otherwise `null`. |
| `statistics` | `n_trials`, `n_correct_trials`, `n_nose_pokes`, `n_left_lever_presses`, `n_right_lever_presses`, `n_rewards` |

### On Connection

When a dashboard connects, the device sends:

1. Up to 200 recent `log` messages
2. `device_info`
3. `session_state`
4. `input_state`

## Protocol Files

A protocol file is a JSON object describing a session. The dashboard creates and validates these files, and sends the whole object to the device in `session_start`. See [protocols/example.json](protocols/example.json).

| Field | Description |
| --- | --- |
| `format` | Always `"bbox-protocol"`. Files with the earlier name `"bbox-experiment"` are also accepted. |
| `format_version` | Always `1` |
| `metadata` | `name` (required), `description`, `author`, `created_at`, `modified_at`, and `dashboard_version`. Only `name` is used by the device. |
| `parameters` | Default timing parameters for every training trial, in milliseconds. All nine are required. |
| `timeline.loop` | If `true`, the timeline restarts after the last item until the session is stopped |
| `timeline.items` | The timeline items, run in order. At least one is required. |

### Parameters

| Parameter | Description |
| --- | --- |
| `iti_minimum_ms`, `iti_maximum_ms` | Range of the inter-trial interval |
| `response_limit_ms` | Time allowed to respond |
| `cue_minimum_ms`, `cue_maximum_ms` | Range of the cue duration |
| `hold_minimum_ms`, `hold_maximum_ms` | Range of the hold duration |
| `valve_open_ms` | How long the water valve opens for a reward |
| `punishment_ms` | Length of the punishment timeout |

Each minimum must not be greater than its maximum.

### Timeline Items

Every item has an `id`, unique within the protocol, an optional `description`, and an optional `repeat` count (default 1).

| `type` | Additional fields | Description |
| --- | --- | --- |
| `training` | `stage` (1 to 6), `parameters` (optional) | One trial of a training stage. `parameters` overrides any of the protocol's parameters for this item. |
| `interval` | `duration_ms` | A pause with all outputs off and blank displays |
