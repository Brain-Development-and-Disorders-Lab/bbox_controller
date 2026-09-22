// React
import { useEffect, useRef, useState } from "react";

// Blueprint components
import { Button, Card, Intent, OverlayToaster, Toaster } from "@blueprintjs/core";
import { Cell, Column, SelectionModes, Table } from "@blueprintjs/table";

// Custom components
import DeviceEditDialog from "../DeviceEditDialog";

// Custom types
import { Device } from "../../../types";

// Utilities
import _ from "lodash";
import consola from "consola";

const DeviceManager = (props: { devices: Device[] }) => {
  // Manage state for devices
  const [devices, setDevices] = useState(props.devices);
  const [selectedDevice, setSelectedDevice] = useState<Device>(props.devices[0]);
  const [selectedDeviceStatus, setSelectedDeviceStatus] = useState(selectedDevice.status);
  
  // Network state
  const [isLoading, setIsLoading] = useState(false);
  
  // UI state
  const [editDeviceOpen, setEditDeviceOpen] = useState(false);
  const toasterRef = useRef<OverlayToaster>(null);
  
  useEffect(() => {
    window.dashboardAPI.onDeviceUpdate((event, status: string) => {
      if (status.startsWith("Connected")) {
        setSelectedDeviceStatus("connected");
        setIsLoading(false);
        toasterRef.current?.show({
          message: "Successfully connected!",
          intent: Intent.SUCCESS,
          icon: "tick-circle",
          timeout: 2000
        });
      } else if (!status.startsWith("Disconnected")) {
        setSelectedDeviceStatus("disconnected");
        setIsLoading(false);
        toasterRef.current?.show({
          message: `Connection Failed: ${status.replace('Error: ', '')}`,
          intent: Intent.DANGER,
          icon: "error",
          timeout: 4000
        });
      } else {
        setSelectedDeviceStatus("disconnected");
        setIsLoading(false);
      }
    });

    return () => {
      window.dashboardAPI.removeDeviceListeners();
    };
  }, []);

  const handleConnectClick = async (device: Device) => {
    setIsLoading(true);
    setSelectedDeviceStatus("connecting");
    window.dashboardAPI.deviceConnect(device);
  };

  const handleDisconnectClick = async (device: Device) => {
    setIsLoading(true);
    setSelectedDeviceStatus("disconnecting");
    window.dashboardAPI.deviceDisconnect(device);
  };
  
  /**
   * Handle clicking the `Edit` button within a Device row
   * @param {number} rowIndex The index of the currently selected Device
   */
  const handleDeviceEditClick = (rowIndex: number) => {
    setSelectedDevice(devices[rowIndex]);
    setEditDeviceOpen(true);
  };
  
  /**
   * Apply updates to `Device` instances
   * @param {Device} updated Instance of `Device` that contains updated information
   */
  const onDeviceSave = (updated: Device) => {
    const updatedDevices = devices.map(device => device.id === updated.id ? updated : device);
    setDevices([...updatedDevices]);
    setSelectedDevice(updated);
  };
  
  // Manage device table column widths
  const containerRef = useRef<HTMLDivElement>(null);
  const [columnWidths, setColumnWidths] = useState<number[]>([320, 180]);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const containerWidth = entry.contentRect.width;
        const totalFixedWidth = columnWidths.slice(0, -1).reduce((a, b) => a + b, 0);
        const remainingSpace = containerWidth - totalFixedWidth - 16; 

        setColumnWidths((prevWidths) => {
          const nextWidths = [...prevWidths];
          nextWidths[nextWidths.length - 1] = Math.max(remainingSpace, 100);
          return nextWidths;
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [columnWidths]);
  
  const nameCellRenderer = (rowIndex: number) => {
    return (
      <Cell>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", width: "auto" }}>{devices[rowIndex].name}</p>
          <div style={{ display: "flex", gap: "8px", marginRight: "4px" }}>
            <Button size={"small"} intent={"none"} icon={"list-detail-view"} text={"View"} onClick={() => setSelectedDevice(devices[rowIndex])} />
            <Button size={"small"} intent={"none"} icon={"edit"} text={"Edit"} onClick={() => handleDeviceEditClick(rowIndex)} />
          </div>
        </div>
      </Cell>
    );
  };

  const statusCellRenderer = (rowIndex: number) => {
    return (
      <Cell style={{ height: "100%", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "2px", alignItems: "center", justifyContent: "space-between"}} interactive={true}>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", color: devices[rowIndex].status === "connected" ? "green" : "red" }}>{_.capitalize(devices[rowIndex].status)}</p>
        </div>
      </Cell>
    );
  };
  
  return (
    <div style={{ padding: "10px", display: "flex", flexDirection: "column", gap: "10px" }}>
      <OverlayToaster ref={toasterRef} position={"bottom-right"} />

      <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
        <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "16px" }}>Devices</p>
        <Button size={"small"} intent={"primary"} icon={"add"} text={"Add Device"} />
      </div>

      {/* Devices table */}
      <div style={{ display: "flex", flexDirection: "column", maxHeight: "240px" }} ref={containerRef}>
        <Table key={devices.map((device) => `${device.id}:${device.name}:${device.status}`).join(",")} numRows={devices.length} selectionModes={SelectionModes.NONE} enableRowHeader={false} enableRowResizing={false} enableColumnResizing={false} enableMultipleSelection={false} defaultRowHeight={48} defaultColumnWidth={120} columnWidths={columnWidths}>
          <Column cellRenderer={nameCellRenderer} name={"Name"} />
          <Column cellRenderer={statusCellRenderer} name={"Status"} />
        </Table>
      </div>
      
      {/* Device information */}
      <div style={{ display: "flex" }}>
        <Card style={{ width: "100%", padding: "8px", gap: "8px", display: "flex", flexDirection: "column" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "14px" }}>Device Information</p>

          <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>Name:</p>
            <p style={{ marginBottom: "0px", fontSize: "12px" }}>{selectedDevice.name}</p>
          </div>

          <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>Network Address:</p>
            <p style={{ marginBottom: "0px", fontSize: "12px" }}>{selectedDevice.network.ip}:{selectedDevice.network.port}</p>
          </div>

          <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>Status:</p>
            <p style={{ marginBottom: "0px", fontSize: "12px", color: selectedDeviceStatus === "connected" ? "green" : "red" }}>{_.capitalize(selectedDeviceStatus)}</p>
          </div>

          <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>Software Version:</p>
            <p style={{ marginBottom: "0px", fontSize: "12px" }}>{selectedDevice.version}</p>
          </div>

          {/* Device action buttons */}
          <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
            <Button size={"small"} intent={"success"} icon={"play"} text={"Connect"} disabled={selectedDeviceStatus === "connected" || isLoading} onClick={() => handleConnectClick(selectedDevice)} />
            <Button size={"small"} intent={"danger"} icon={"stop"} text={"Disconnect"} disabled={selectedDeviceStatus === "disconnected" || isLoading} onClick={() => handleDisconnectClick(selectedDevice)} />
            <Button size={"small"} intent={"primary"} text={"Sync Files"} icon={"refresh"} disabled={selectedDeviceStatus === "disconnected"} />
          </div>
        </Card>
      </div>
      
      <DeviceEditDialog isOpen={editDeviceOpen} setIsOpen={setEditDeviceOpen} device={selectedDevice} onSave={onDeviceSave} />
    </div>
  );
};

export default DeviceManager;
