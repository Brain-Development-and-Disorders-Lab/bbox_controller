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

// `Experiment` type to manage experiment information
export type Experiment = {
  id: string;
  name: string;
};

// `DeviceEditDialog` component props
export type DeviceEditDialogProps = {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  device: Device;
  onSave: (device: Device) => void;
};
