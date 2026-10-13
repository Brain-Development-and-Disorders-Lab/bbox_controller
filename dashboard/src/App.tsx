// React
import { useEffect, useRef, useState } from "react";

// Blueprint components
import { Button, Card, Colors, Intent, MenuItem, OverlayToaster, Tab, Tabs, TextArea } from "@blueprintjs/core";
import { ItemRenderer, Select } from "@blueprintjs/select";
import { Cell, Column, SelectionModes, Table } from "@blueprintjs/table";

// Custom components
import DeviceEditDialog from "./components/DeviceEditDialog";
import DeviceTab from "./components/DeviceTab";

// Custom types
import { Device, DeviceUpdate, Experiment } from "../types";

// Utility libraries
import _ from "lodash";

const EXAMPLE_DEVICES: Device[] = [
  {
    id: "1",
    name: "Device 1",
    status: "disconnected",
    network: {
      ip: "localhost",
      port: 1111,
    },
    version: "1.0.0",
  },
  {
    id: "2",
    name: "Device 2",
    status: "disconnected",
    network: {
      ip: "localhost",
      port: 2222,
    },
    version: "1.0.0",
  },
];

const EXAMPLE_EXPERIMENTS: Experiment[] = [
  {
    id: "e_00",
    name: "Experiment 1",
    trials: [],
  },
  {
    id: "e_01",
    name: "Experiment 2",
    trials: [],
  },
];

const App = () => {
  // Manage state for devices
  // `devices` is the single source of truth for device state, including connection status
  const [devices, setDevices] = useState(EXAMPLE_DEVICES);
  const [selectedDeviceId, setSelectedDeviceId] = useState(EXAMPLE_DEVICES[0].id);
  const selectedDevice = devices.find((device) => device.id === selectedDeviceId) ?? devices[0];
  const isBusy = selectedDevice.status === "connecting" || selectedDevice.status === "disconnecting";

  // UI state
  const [editDeviceOpen, setEditDeviceOpen] = useState(false);
  const toasterRef = useRef<OverlayToaster>(null);

  /**
   * Set the status of a `Device`. Uses a functional state update, since this is also
   * called from the IPC listener registered on mount and would otherwise see stale state.
   * @param {Device["id"]} id The ID of the `Device` to update
   * @param {Device["status"]} status The new status
   */
  const setDeviceStatus = (id: Device["id"], status: Device["status"]) => {
    setDevices((current) => current.map((device) => device.id === id ? { ...device, status } : device));
  };

  useEffect(() => {
    return window.dashboardAPI.onDeviceUpdate((update: DeviceUpdate) => {
      setDeviceStatus(update.id, update.status);
      if (update.error) {
        toasterRef.current?.show({
          message: `Connection Failed: ${update.error}`,
          intent: Intent.DANGER,
          icon: "error",
          timeout: 4000
        });
      } else if (update.status === "connected") {
        toasterRef.current?.show({
          message: "Successfully connected!",
          intent: Intent.SUCCESS,
          icon: "tick-circle",
          timeout: 2000
        });
      }
    });
  }, []);

  const handleConnectClick = (device: Device) => {
    setDeviceStatus(device.id, "connecting");
    window.dashboardAPI.deviceConnect(device);
  };

  const handleDisconnectClick = (device: Device) => {
    setDeviceStatus(device.id, "disconnecting");
    window.dashboardAPI.deviceDisconnect(device);
  };

  /**
   * Handle clicking the `Edit` button within a Device row
   * @param {number} rowIndex The index of the currently selected Device
   */
  const handleDeviceEditClick = (rowIndex: number) => {
    setSelectedDeviceId(devices[rowIndex].id);
    setEditDeviceOpen(true);
  };

  /**
   * Apply updates to `Device` instances
   * @param {Device} updated Instance of `Device` that contains updated information
   */
  const onDeviceSave = (updated: Device) => {
    setDevices((current) => current.map((device) => device.id === updated.id ? updated : device));
  };
  
  // Manage device table column widths
  const containerRef = useRef<HTMLDivElement>(null);
  const [columnWidths, setColumnWidths] = useState<number[]>([320, 180]);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Stretch the last column to fill the container. Observe once on mount, and only
    // update state when the width actually changes, otherwise this re-renders forever.
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const containerWidth = entry.contentRect.width;

        setColumnWidths((prevWidths) => {
          const totalFixedWidth = prevWidths.slice(0, -1).reduce((a, b) => a + b, 0);
          const lastWidth = Math.max(containerWidth - totalFixedWidth - 16, 100);
          if (prevWidths[prevWidths.length - 1] === lastWidth) return prevWidths;

          const nextWidths = [...prevWidths];
          nextWidths[nextWidths.length - 1] = lastWidth;
          return nextWidths;
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);
  
  const deviceNameCellRenderer = (rowIndex: number) => {
    return (
      <Cell>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", width: "auto" }}>{devices[rowIndex].name}</p>
          <div style={{ display: "flex", gap: "8px", marginRight: "4px" }}>
            <Button size={"small"} intent={"none"} icon={"list-detail-view"} text={"View"} onClick={() => setSelectedDeviceId(devices[rowIndex].id)} />
            <Button size={"small"} intent={"none"} icon={"edit"} text={"Edit"} disabled={devices[rowIndex].status !== "disconnected"} onClick={() => handleDeviceEditClick(rowIndex)} />
          </div>
        </div>
      </Cell>
    );
  };

  const deviceStatusCellRenderer = (rowIndex: number) => {
    return (
      <Cell style={{ height: "100%", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "2px", alignItems: "center", justifyContent: "space-between"}} interactive={true}>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", color: devices[rowIndex].status === "connected" ? "green" : "red" }}>{_.capitalize(devices[rowIndex].status)}</p>
        </div>
      </Cell>
    );
  };
  
  return (
    <div style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "row" }}>
      {/* Left: Device manager */}
      <div style={{ width: "30%", height: "100%", background: Colors.LIGHT_GRAY3 }}>
        <div style={{ padding: "10px", display: "flex", flexDirection: "column", gap: "10px" }}>
          <OverlayToaster ref={toasterRef} position={"bottom-right"} />

          <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "16px" }}>Devices</p>
            <Button size={"small"} intent={"primary"} icon={"add"} text={"Add Device"} />
          </div>

          {/* Devices table */}
          <div style={{ display: "flex", flexDirection: "column", maxHeight: "240px" }} ref={containerRef}>
            <Table key={devices.map((device) => `${device.id}:${device.name}:${device.status}`).join(",")} numRows={devices.length} selectionModes={SelectionModes.NONE} enableRowHeader={false} enableRowResizing={false} enableColumnResizing={false} enableMultipleSelection={false} defaultRowHeight={48} defaultColumnWidth={120} columnWidths={columnWidths}>
              <Column cellRenderer={deviceNameCellRenderer} name={"Name"} />
              <Column cellRenderer={deviceStatusCellRenderer} name={"Status"} />
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
                <p style={{ marginBottom: "0px", fontSize: "12px", color: selectedDevice.status === "connected" ? "green" : "red" }}>{_.capitalize(selectedDevice.status)}</p>
              </div>

              <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>Software Version:</p>
                <p style={{ marginBottom: "0px", fontSize: "12px" }}>{selectedDevice.version}</p>
              </div>

              {/* Device action buttons */}
              <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                <Button size={"small"} intent={"success"} icon={"play"} text={"Connect"} disabled={selectedDevice.status === "connected" || isBusy} onClick={() => handleConnectClick(selectedDevice)} />
                <Button size={"small"} intent={"danger"} icon={"stop"} text={"Disconnect"} disabled={selectedDevice.status === "disconnected" || isBusy} onClick={() => handleDisconnectClick(selectedDevice)} />
                <Button size={"small"} intent={"primary"} text={"Sync Files"} icon={"refresh"} disabled={selectedDevice.status !== "connected"} />
              </div>
            </Card>
          </div>
          
          <DeviceEditDialog isOpen={editDeviceOpen} setIsOpen={setEditDeviceOpen} device={selectedDevice} onSave={onDeviceSave} />
        </div>
      </div>

      {/* Right: Device state */}
      <div style={{ width: "70%", height: "100%" }}>
        <div style={{ padding: "8px", width: "100%", height: "100%" }}>
          <Tabs id={"DeviceTabs"} className={"device-tabs"} animate>
            {devices.map((device) => {
              return (
                <Tab key={device.id} id={device.id} title={device.name} panelClassName={"device-tab-panel"} panel={<DeviceTab device={device} experiments={EXAMPLE_EXPERIMENTS} />} />
              );
            })}
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default App;
