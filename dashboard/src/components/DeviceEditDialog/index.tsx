// React
import { useEffect, useState } from "react";

// Blueprint components
import { Button, Dialog, DialogBody, DialogFooter } from "@blueprintjs/core";

// Custom types
import { Device, DeviceEditDialogProps } from "../../../types";

// Utility functions
import { isValidIPAddress } from "../../lib/util";

const DeviceEditDialog = (props: DeviceEditDialogProps) => {
  const [deviceName, setDeviceName] = useState(props.device.name);
  const [deviceAddress, setDeviceAddress] = useState(props.device.network.ip);
  const [devicePort, setDevicePort] = useState(props.device.network.port);
  
  // Synchronize the state
  useEffect(() => {
    setDeviceName(props.device.name);
    setDeviceAddress(props.device.network.ip);
    setDevicePort(props.device.network.port);
  }, [props.device]);
  
  const handleSaveClick = () => {
    const device: Device = {
      id: props.device.id,
      name: deviceName,
      network: {
        ip: deviceAddress,
        port: devicePort,
      },
      status: props.device.status,
      version: props.device.version,
    };
    
    props.onSave(device);
    props.setIsOpen(false);
  }

  return (
    <Dialog title={`Edit Device: ${props.device.name}`} icon={"edit"} isOpen={props.isOpen} style={{ width: "340px" }}>
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device Name:</p>
          <input type={"text"} value={deviceName} onChange={(event) => setDeviceName(event.target.value)} />
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device IP Address:</p>
          <input type={"text"} value={deviceAddress} onChange={(event) => setDeviceAddress(event.target.value)} />
          {!isValidIPAddress(deviceAddress) && <p style={{ marginBottom: "0px", fontSize: "12px", color: "red" }}>Must be a valid IP address or "localhost"</p>}
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px" }}>Device Port:</p>
          <input type={"number"} value={devicePort} onChange={(event) => setDevicePort(parseInt(event.target.value))} />
        </div>
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} onClick={() => props.setIsOpen(false)} />
            <Button intent={"success"} icon={"tick-circle"} text={"Save"} disabled={!isValidIPAddress(deviceAddress)} onClick={() => handleSaveClick()} />
          </div>
        }
      />
    </Dialog>
  );
};

export default DeviceEditDialog;
