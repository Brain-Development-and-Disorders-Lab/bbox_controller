import { IconName } from "@blueprintjs/core";

// ----- Devices -----

export type Device = {
  id: string;
  name: string;
  status: "disconnected" | "disconnecting" | "connected" | "connecting";
  network: {
    ip: string;
    port: number;
  };
  // Reported by the device when connected
  info?: DeviceInfo;
};

// Sent by the device when the dashboard connects
export type DeviceInfo = {
  version: string;
  simulated: boolean;
  hostname: string;
  os: string;
  started_at: number;
  // Free space at connection time, -1 if unknown
  storage_free_bytes: number;
};

// Persisted subset of `Device`
export type StoredDevice = Pick<Device, "id" | "name" | "network">;

export type DevicesLoadResult =
  | { status: "loaded"; devices: StoredDevice[] }
  | { status: "error"; message: string; devices: StoredDevice[] };

export type DevicesSaveResult =
  | { status: "saved" }
  | { status: "error"; message: string };

// ----- Device communication -----

export type DeviceUpdate = {
  id: Device["id"];
  status: "connected" | "disconnected";
  error?: string;
};

export type DeviceLog = {
  id: Device["id"];
  level: "trace" | "debug" | "info" | "warning" | "error" | "critical";
  timestamp: number;
  message: string;
};

export type DeviceTestState = {
  id: Device["id"];
  test: string;
  state: "running" | "passed" | "failed";
};

// Every input and output on the device
export type InputChannel =
  | "left_lever"
  | "left_lever_light"
  | "right_lever"
  | "right_lever_light"
  | "nose_poke"
  | "nose_light"
  | "water_valve";

export type DeviceInputState = {
  id: Device["id"];
  state: Record<InputChannel, boolean>;
};

// Running totals for the active session
export type SessionStatistics = {
  n_trials: number;
  n_correct_trials: number;
  n_nose_pokes: number;
  n_left_lever_presses: number;
  n_right_lever_presses: number;
  n_rewards: number;
};

// Elapsed times were measured when the device sent the update, `received_at` is when it arrived
export type DeviceSessionState = {
  id: Device["id"];
  received_at: number;
  state: "idle" | "running" | "completed" | "stopped";
  protocol_name: string;
  subject: string;
  // Relative to the device data root, e.g. `Subjects/M001/2026-10-20/001`. Empty before the first session.
  session_path: string;
  session_elapsed_ms: number;
  trial: { trial_num: number; item_id: TimelineItem["id"]; elapsed_ms: number } | null;
  statistics: SessionStatistics;
};

// Device messages are defined in `main.js`
export type DeviceCommand =
  // Hardware tests, named in `shared/commands.json`
  | { command: string; parameter: number }
  | { command: "session_start"; subject: string; protocol: Protocol }
  | { command: "session_stop" };

// `failed` names files that could not be written
export type DataSyncResult =
  | { status: "synced"; directory: string; written: number; failed: string[] }
  | { status: "canceled" }
  | { status: "error"; message: string };

// ----- Protocols -----

// Task parameters, in milliseconds
export type ProtocolParameters = {
  iti_minimum_ms: number;
  iti_maximum_ms: number;
  response_limit_ms: number;
  cue_minimum_ms: number;
  cue_maximum_ms: number;
  hold_minimum_ms: number;
  hold_maximum_ms: number;
  valve_open_ms: number;
  punishment_ms: number;
};

type TimelineItemBase = {
  id: string;
  description?: string;
  repeat: number;
};

export type TrainingTrial = TimelineItemBase & {
  type: "training";
  stage: number;
  parameters?: Partial<ProtocolParameters>;
};

export type IntervalTrial = TimelineItemBase & {
  type: "interval";
  duration_ms: number;
};

export type TimelineItem = TrainingTrial | IntervalTrial;

export type Protocol = {
  format: "bbox-protocol";
  format_version: 1;
  metadata: {
    name: string;
    description: string;
    author: string;
    created_at: string;
    modified_at: string;
    dashboard_version?: string;
  };
  parameters: ProtocolParameters;
  timeline: {
    loop: boolean;
    items: TimelineItem[];
  };
};

export type ProtocolParseResult =
  | { success: true; protocol: Protocol }
  | { success: false; errors: string[] };

// Checked and loaded onto a device
export type LoadedProtocol = {
  filePath: string;
  protocol: Protocol;
};

// Picked for review before loading
export type PendingProtocolFile = {
  filePath: string;
  result: ProtocolParseResult;
};

export type ProtocolSaveResult =
  | { status: "saved"; filePath: string }
  | { status: "canceled" }
  | { status: "error"; message: string };

// ----- Component props -----

export type DeviceTabProps = {
  device: Device;
};

export type EmptyStateProps = {
  icon: IconName;
  message: string;
};

export type StatusIndicatorProps = {
  status?: "good" | "neutral" | "bad";
};

export type ErrorCalloutProps = {
  title: string;
  errors: string[];
};

export type ProtocolTimelineProps = {
  items: TimelineItem[];
  selectedIndex?: number;
  onSelect?: (index: number) => void;
};

export type ProtocolParameterListProps = {
  parameters: ProtocolParameters;
  onChange?: (key: keyof ProtocolParameters, value: number) => void;
};

// Adds a new device unless `device` is given
export type DeviceEditDialogProps = {
  isOpen: boolean;
  device?: Device;
  // Existing devices, used to block duplicate addresses
  devices: Device[];
  onClose: () => void;
  onSave: (device: Device) => void;
  // Called once removal of the edited device has been confirmed
  onRemove: (device: Device) => void;
};

// Creates a new protocol unless `loaded` is given
export type ProtocolEditDialogProps = {
  isOpen: boolean;
  loaded?: LoadedProtocol;
  onClose: () => void;
  // Called with the saved file once it has been written
  onSave: (saved: LoadedProtocol) => void;
};

export type ProtocolLoadDialogProps = {
  isOpen: boolean;
  file?: PendingProtocolFile;
  onClose: () => void;
  onConfirm: (loaded: LoadedProtocol) => void;
};

// ----- Preload -----

// Exposed to the renderer by `preload.js`
export type DashboardAPI = {
  deviceConnect: (device: Device) => void;
  deviceDisconnect: (device: Device) => void;
  deviceCommand: (device: Device, command: DeviceCommand) => void;
  // Shows a folder picker, then copies the device's data files that aren't already there
  deviceDataSync: (device: Device) => Promise<DataSyncResult>;
  // Devices persisted between launches
  devicesLoad: () => Promise<DevicesLoadResult>;
  devicesSave: (devices: StoredDevice[]) => Promise<DevicesSaveResult>;
  // Shows a save dialog starting at `defaultPath`
  protocolSave: (defaultPath: string, contents: string) => Promise<ProtocolSaveResult>;
  // Full path of a file picked in a file input
  getFilePath: (file: File) => string;
  // Subscriptions return an unsubscribe function
  onDeviceUpdate: (callback: (update: DeviceUpdate) => void) => () => void;
  onDeviceInfo: (callback: (update: { id: Device["id"]; info: DeviceInfo }) => void) => () => void;
  onDeviceLog: (callback: (log: DeviceLog) => void) => () => void;
  onDeviceTestState: (callback: (update: DeviceTestState) => void) => () => void;
  onDeviceInputState: (callback: (update: DeviceInputState) => void) => () => void;
  onDeviceSessionState: (callback: (update: DeviceSessionState) => void) => () => void;
};

declare global {
  interface Window {
    dashboardAPI: DashboardAPI;
  }
}
