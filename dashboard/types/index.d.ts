// `Device` type to manage device information
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

// Status update pushed from the main process over the `device-update` channel
export type DeviceUpdate = {
  id: Device["id"];
  status: "connected" | "disconnected";
  error?: string;
};

// Log record forwarded from a device over the `device-log` channel
export type DeviceLog = {
  id: Device["id"];
  level: "trace" | "debug" | "info" | "warning" | "error" | "critical";
  timestamp: number;
  message: string;
};

// Result of a hardware test forwarded over the `device-test-state` channel
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

// Row of the "Input Status" card
export type InputChannelRow = {
  channel: InputChannel;
  label: string;
};

// Experiment-wide task parameters, in milliseconds
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

// Fields shared by every timeline item
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

// Timeline items, discriminated by `type`
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

// Experiment with defaults applied
export type ExperimentParseResult =
  | { success: true; experiment: Experiment }
  | { success: false; errors: string[] };

// Experiment file that has been checked and loaded onto a device
export type LoadedExperiment = {
  filePath: string;
  experiment: Experiment;
};

// Experiment file picked for review prior to loading
export type PendingExperimentFile = {
  filePath: string;
  result: ExperimentParseResult;
};

// Outcome of saving an experiment file
export type ExperimentSaveResult =
  | { status: "saved"; filePath: string }
  | { status: "canceled" }
  | { status: "error"; message: string };

// `DeviceTab` component props
export type DeviceTabProps = {
  device: Device;
};

// `StatusIndicator` component props
export type StatusIndicatorProps = {
  status?: "good" | "neutral" | "bad";
};

// `ErrorCallout` component props
export type ErrorCalloutProps = {
  title: string;
  errors: string[];
};

// `ExperimentTimeline` component props
export type ExperimentTimelineProps = {
  items: TimelineItem[];
  selectedIndex?: number;
  onSelect?: (index: number) => void;
};

// `ExperimentParameterList` component props
export type ExperimentParameterListProps = {
  parameters: ExperimentParameters;
  onChange?: (key: keyof ExperimentParameters, value: number) => void;
};

// `DeviceEditDialog` component props
export type DeviceEditDialogProps = {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  device: Device;
  onSave: (device: Device) => void;
};

// `ExperimentEditDialog` component props. Creates a new experiment unless `loaded` is given.
export type ExperimentEditDialogProps = {
  isOpen: boolean;
  loaded?: LoadedExperiment;
  onClose: () => void;
  // Called with the saved file once it has been written
  onSave: (saved: LoadedExperiment) => void;
};

// `ExperimentLoadDialog` component props
export type ExperimentLoadDialogProps = {
  isOpen: boolean;
  file?: PendingExperimentFile;
  onClose: () => void;
  onConfirm: (loaded: LoadedExperiment) => void;
};

// API exposed to the renderer by `preload.js`
export type DashboardAPI = {
  deviceConnect: (device: Device) => void;
  deviceDisconnect: (device: Device) => void;
  deviceCommand: (device: Device, command: { command: string; parameter: number }) => void;
  // Shows a save dialog starting at `defaultPath`
  experimentSave: (defaultPath: string, contents: string) => Promise<ExperimentSaveResult>;
  // Full path of a file picked in a file input
  getFilePath: (file: File) => string;
  // Subscriptions return an unsubscribe function
  onDeviceUpdate: (callback: (update: DeviceUpdate) => void) => () => void;
  onDeviceLog: (callback: (log: DeviceLog) => void) => () => void;
  onDeviceTestState: (callback: (update: DeviceTestState) => void) => () => void;
  onDeviceInputState: (callback: (update: DeviceInputState) => void) => () => void;
};

declare global {
  interface Window {
    dashboardAPI: DashboardAPI;
  }
}
