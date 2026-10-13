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

// Result of a hardware test, forwarded over the `device-test-state` channel
export type DeviceTestState = {
  id: Device["id"];
  test: string;
  state: "running" | "passed" | "failed";
};

// Every input and output on the device, keyed by name, forwarded over the `device-input-state` channel
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

export type Trial = {
  id: string;
  name: string;
  type: "standard" | "interval" | "end";
  description: string;
};

// `Experiment` type to manage experiment information
export type Experiment = {
  id: string;
  name: string;
  trials: Trial[],
};

// `DeviceEditDialog` component props
export type DeviceEditDialogProps = {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  device: Device;
  onSave: (device: Device) => void;
};

// `ExperimentEditDialog` component props
export type ExperimentEditDialogProps = {
  experiment?: Experiment;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  onSave: (experiment: Experiment) => void;
};

// API exposed to the renderer by `preload.js`
export type DashboardAPI = {
  deviceConnect: (device: Device) => void;
  deviceDisconnect: (device: Device) => void;
  deviceCommand: (device: Device, command: { command: string; parameter: number }) => void;
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
