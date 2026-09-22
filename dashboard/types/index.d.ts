// `Device` type to manage device information
export type Device = {
  id: string;
  name: string;
  status: "disconnected" | "connected" | "connecting";
  network: {
    ip: string;
    port: number;
  };
  version: string;
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
