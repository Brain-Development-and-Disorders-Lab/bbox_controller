// React
import { useEffect, useState } from "react";

// Blueprint components
import { Alert, Button, Dialog, DialogBody, DialogFooter } from "@blueprintjs/core";

// Custom types
import { Device, DeviceEditDialogProps } from "../../../types";

// Utility functions
import { isValidIPAddress, isValidPort } from "../../lib/util";

// Defaults for a newly added device
const DEFAULT_ADDRESS = "localhost";
const DEFAULT_PORT = 8765;

const DeviceEditDialog = (props: DeviceEditDialogProps) => {
  const [device, setDevice] = useState(props.device);
  const isAdding = device === undefined;

  const [deviceName, setDeviceName] = useState("");
  const [deviceAddress, setDeviceAddress] = useState(DEFAULT_ADDRESS);
  const [devicePort, setDevicePort] = useState(DEFAULT_PORT);
  const [isRemoveAlertOpen, setIsRemoveAlertOpen] = useState(false);

  useEffect(() => {
    if (props.isOpen) {
      setDevice(props.device);
      setDeviceName(props.device?.name ?? "");
      setDeviceAddress(props.device?.network.ip ?? DEFAULT_ADDRESS);
      setDevicePort(props.device?.network.port ?? DEFAULT_PORT);
    }
  }, [props.isOpen, props.device]);

  const isNameValid = deviceName.trim() !== "";
  const isAddressValid = isValidIPAddress(deviceAddress);
  const isPortValid = isValidPort(devicePort);

  const handleSaveClick = () => {
    const updated: Device = {
      id: device?.id ?? crypto.randomUUID(),
      name: deviceName.trim(),
      network: {
        ip: deviceAddress,
        port: devicePort,
      },
      status: device?.status ?? "disconnected",
      version: device?.version ?? "Unknown",
    };

    props.onSave(updated);
    props.onClose();
  };

  const handleRemoveConfirm = () => {
    if (device) props.onRemove(device);
    setIsRemoveAlertOpen(false);
    props.onClose();
  };

  return (
    <Dialog
      title={isAdding ? "Add Device" : `Edit Device: ${device?.name}`}
      icon={isAdding ? "add" : "edit"}
      isOpen={props.isOpen}
      onClose={props.onClose}
      style={{ width: "340px" }}
    >
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device Name:</p>
          <input type={"text"} placeholder={"Enter device name"} value={deviceName} onChange={(event) => setDeviceName(event.target.value)} autoFocus={isAdding} />
          {!isNameValid && <p style={{ marginBottom: "0px", fontSize: "12px", color: "red" }}>Must not be empty</p>}
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device IP Address:</p>
          <input type={"text"} value={deviceAddress} onChange={(event) => setDeviceAddress(event.target.value)} />
          {!isAddressValid && <p style={{ marginBottom: "0px", fontSize: "12px", color: "red" }}>Must be a valid IP address or "localhost"</p>}
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device Port:</p>
          <input type={"number"} min={1} max={65535} value={Number.isNaN(devicePort) ? "" : devicePort} onChange={(event) => setDevicePort(parseInt(event.target.value))} />
          {!isPortValid && <p style={{ marginBottom: "0px", fontSize: "12px", color: "red" }}>Must be a port between 1 and 65535</p>}
        </div>
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} onClick={props.onClose} />
            <Button
              intent={"success"}
              icon={"tick-circle"}
              text={isAdding ? "Add" : "Save"}
              disabled={!isNameValid || !isAddressValid || !isPortValid}
              onClick={handleSaveClick}
            />
          </div>
        }
      >
        {!isAdding && <Button intent={"danger"} variant={"minimal"} icon={"trash"} text={"Remove"} onClick={() => setIsRemoveAlertOpen(true)} />}
      </DialogFooter>
      <Alert
        isOpen={isRemoveAlertOpen}
        intent={"danger"}
        icon={"trash"}
        cancelButtonText={"Cancel"}
        confirmButtonText={"Remove"}
        onCancel={() => setIsRemoveAlertOpen(false)}
        onConfirm={handleRemoveConfirm}
      >
        <p>Are you sure you want to remove <b>{device?.name}</b>? This cannot be undone.</p>
      </Alert>
    </Dialog>
  );
};

export default DeviceEditDialog;
