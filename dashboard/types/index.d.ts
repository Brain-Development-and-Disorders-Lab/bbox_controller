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
  version: string;
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

// Running totals for the active experiment
export type ExperimentStatistics = {
  trials: number;
  nose_pokes: number;
  left_lever_presses: number;
  right_lever_presses: number;
  water_deliveries: number;
};

// Elapsed times were measured when the device sent the update, `received_at` is when it arrived
export type DeviceExperimentState = {
  id: Device["id"];
  received_at: number;
  state: "idle" | "running" | "completed" | "stopped";
  experiment_name: string;
  animal_id: string;
  experiment_elapsed_ms: number;
  trial: { index: number; id: TimelineItem["id"]; elapsed_ms: number } | null;
  statistics: ExperimentStatistics;
};

// Device messages are defined in `main.js`
export type DeviceCommand =
  // Hardware tests, named in `shared/commands.json`
  | { command: string; parameter: number }
  | { command: "experiment_start"; animal_id: string; experiment: Experiment }
  | { command: "experiment_stop" };

// `failed` names files that could not be written
export type DataSyncResult =
  | { status: "synced"; directory: string; written: number; failed: string[] }
  | { status: "canceled" }
  | { status: "error"; message: string };

// ----- Experiments -----

// Task parameters, in milliseconds
export type ExperimentParameters = {
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
  parameters?: Partial<ExperimentParameters>;
};

export type IntervalTrial = TimelineItemBase & {
  type: "interval";
  duration_ms: number;
};

export type TimelineItem = TrainingTrial | IntervalTrial;

export type Experiment = {
  format: "bbox-experiment";
  format_version: 1;
  metadata: {
    name: string;
    description: string;
    author: string;
    created_at: string;
    modified_at: string;
    dashboard_version?: string;
  };
  parameters: ExperimentParameters;
  timeline: {
    loop: boolean;
    items: TimelineItem[];
  };
};

export type ExperimentParseResult =
  | { success: true; experiment: Experiment }
  | { success: false; errors: string[] };

// Checked and loaded onto a device
export type LoadedExperiment = {
  filePath: string;
  experiment: Experiment;
};

// Picked for review before loading
export type PendingExperimentFile = {
  filePath: string;
  result: ExperimentParseResult;
};

export type ExperimentSaveResult =
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

export type ExperimentTimelineProps = {
  items: TimelineItem[];
  selectedIndex?: number;
  onSelect?: (index: number) => void;
};

export type ExperimentParameterListProps = {
  parameters: ExperimentParameters;
  onChange?: (key: keyof ExperimentParameters, value: number) => void;
};

// Adds a new device unless `device` is given
export type DeviceEditDialogProps = {
  isOpen: boolean;
  device?: Device;
  onClose: () => void;
  onSave: (device: Device) => void;
  // Called once removal of the edited device has been confirmed
  onRemove: (device: Device) => void;
};

// Creates a new experiment unless `loaded` is given
export type ExperimentEditDialogProps = {
  isOpen: boolean;
  loaded?: LoadedExperiment;
  onClose: () => void;
  // Called with the saved file once it has been written
  onSave: (saved: LoadedExperiment) => void;
};

export type ExperimentLoadDialogProps = {
  isOpen: boolean;
  file?: PendingExperimentFile;
  onClose: () => void;
  onConfirm: (loaded: LoadedExperiment) => void;
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
  experimentSave: (defaultPath: string, contents: string) => Promise<ExperimentSaveResult>;
  // Full path of a file picked in a file input
  getFilePath: (file: File) => string;
  // Subscriptions return an unsubscribe function
  onDeviceUpdate: (callback: (update: DeviceUpdate) => void) => () => void;
  onDeviceLog: (callback: (log: DeviceLog) => void) => () => void;
  onDeviceTestState: (callback: (update: DeviceTestState) => void) => () => void;
  onDeviceInputState: (callback: (update: DeviceInputState) => void) => () => void;
  onDeviceExperimentState: (callback: (update: DeviceExperimentState) => void) => () => void;
};

declare global {
  interface Window {
    dashboardAPI: DashboardAPI;
  }
}
