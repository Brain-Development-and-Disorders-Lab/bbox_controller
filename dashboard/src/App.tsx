// React
import { useEffect, useRef, useState } from "react";

// Blueprint components
import { Button, Card, Colors, Icon, Intent, OverlayToaster, Tab, Tabs } from "@blueprintjs/core";
import { Cell, Column, SelectionModes, Table } from "@blueprintjs/table";

// Custom components
import DeviceEditDialog from "./components/DeviceEditDialog";
import DeviceTab from "./components/DeviceTab";
import EmptyState from "./components/EmptyState";

// Custom types
import { Device, DeviceUpdate, StoredDevice } from "../types";

// Utility functions
import { DEVICE_ICON, formatBytes } from "./lib/util";

// Utility libraries
import _ from "lodash";

// Stored devices have no runtime state until connected
const fromStoredDevice = (stored: StoredDevice): Device => ({ ...stored, status: "disconnected" });
const toStoredDevice = ({ id, name, network }: Device): StoredDevice => ({ id, name, network });

// Tab icon reflects the device state, pulsing while connecting or running a session
const tabIconStyle = (status: Device["status"], isRunning: boolean) => {
  if (status === "connected") return { color: Colors.GREEN3, className: isRunning ? "status-pulse" : undefined };
  if (status === "connecting") return { color: Colors.ORANGE3, className: "status-pulse" };
  return { color: Colors.RED3, className: undefined };
};

const App = () => {
  // Single source of truth for device state, including connection status
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<Device["id"]>();
  const selectedDevice: Device | undefined = devices.find((device) => device.id === selectedDeviceId) ?? devices[0];
  const isBusy = selectedDevice?.status === "connecting" || selectedDevice?.status === "disconnecting";

  // UI state
  const [deviceDialog, setDeviceDialog] = useState({ isOpen: false, isEditing: false });
  const toasterRef = useRef<OverlayToaster>(null);

  // Devices with a file sync in progress
  const [syncingDeviceIds, setSyncingDeviceIds] = useState<Set<Device["id"]>>(new Set());

  // Devices with a session running
  const [runningDeviceIds, setRunningDeviceIds] = useState<Set<Device["id"]>>(new Set());
  useEffect(() => {
    return window.dashboardAPI.onDeviceSessionState((update) => {
      setRunningDeviceIds((current) => {
        const next = new Set(current);
        if (update.state === "running") next.add(update.id);
        else next.delete(update.id);
        return next;
      });
    });
  }, []);

  // Load the stored devices once on mount
  useEffect(() => {
    window.dashboardAPI.devicesLoad().then((result) => {
      setDevices(result.devices.map(fromStoredDevice));
      if (result.status === "error") {
        toasterRef.current?.show({
          message: `Could not load devices: ${result.message}`,
          intent: Intent.DANGER,
          icon: "error",
          timeout: 6000
        });
      }
    });
  }, []);

  const storeDevices = async (updated: Device[]) => {
    const result = await window.dashboardAPI.devicesSave(updated.map(toStoredDevice));
    if (result.status === "error") {
      toasterRef.current?.show({
        message: `Could not save devices: ${result.message}`,
        intent: Intent.DANGER,
        icon: "error",
        timeout: 6000
      });
    }
  };

  // Functional update, since the IPC listener registered on mount would otherwise see stale state
  const setDeviceStatus = (id: Device["id"], status: Device["status"]) => {
    setDevices((current) => current.map((device) => device.id === id ? { ...device, status } : device));
  };

  // Device info is only current while connected
  useEffect(() => {
    return window.dashboardAPI.onDeviceInfo(({ id, info }) => {
      setDevices((current) => current.map((device) => device.id === id ? { ...device, info } : device));
    });
  }, []);

  useEffect(() => {
    return window.dashboardAPI.onDeviceUpdate((update: DeviceUpdate) => {
      setDeviceStatus(update.id, update.status);
      if (update.status === "disconnected") {
        setDevices((current) => current.map((device) => device.id === update.id ? { ...device, info: undefined } : device));
      }
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

  const handleSyncClick = async (device: Device) => {
    setSyncingDeviceIds((current) => new Set(current).add(device.id));
    const result = await window.dashboardAPI.deviceDataSync(device);
    setSyncingDeviceIds((current) => {
      const updated = new Set(current);
      updated.delete(device.id);
      return updated;
    });

    if (result.status === "error") {
      toasterRef.current?.show({ message: `Sync Failed: ${result.message}`, intent: Intent.DANGER, icon: "error", timeout: 6000 });
    } else if (result.status === "synced" && result.failed.length > 0) {
      toasterRef.current?.show({
        message: `Synced ${result.written} files, but ${result.failed.length} could not be written: ${result.failed.join(", ")}`,
        intent: Intent.WARNING,
        icon: "warning-sign",
        timeout: 8000
      });
    } else if (result.status === "synced") {
      toasterRef.current?.show({
        message: result.written > 0 ? `Synced ${result.written} new files to ${result.directory}` : "No new files to sync",
        intent: Intent.SUCCESS,
        icon: "tick-circle",
        timeout: 4000
      });
    }
  };

  const handleDeviceEditClick = (rowIndex: number) => {
    setSelectedDeviceId(devices[rowIndex].id);
    setDeviceDialog({ isOpen: true, isEditing: true });
  };

  const handleDeviceAddClick = () => {
    setDeviceDialog({ isOpen: true, isEditing: false });
  };

  const onDeviceSave = (updated: Device) => {
    const isNew = !devices.some((device) => device.id === updated.id);
    const replace = (current: Device[]) => isNew
      ? [...current, updated]
      : current.map((device) => device.id === updated.id ? updated : device);

    setDevices(replace);
    storeDevices(replace(devices));
    if (isNew) setSelectedDeviceId(updated.id);
  };

  // Only disconnected devices can be edited, so there is no connection to close
  const onDeviceRemove = (removed: Device) => {
    const remove = (current: Device[]) => current.filter((device) => device.id !== removed.id);
    setDevices(remove);
    storeDevices(remove(devices));
  };
  
  // Device table column widths
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

  const selectedRowClassName = (rowIndex: number) => {
    return devices[rowIndex].id === selectedDevice?.id ? "device-row-selected" : undefined;
  };

  const deviceNameCellRenderer = (rowIndex: number) => {
    const isSelected = devices[rowIndex].id === selectedDevice?.id;
    return (
      <Cell className={isSelected ? "device-row-selected device-row-accent" : undefined}>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <Icon icon={DEVICE_ICON} />
            <p style={{ marginBottom: "0px", fontWeight: "bold", width: "auto" }}>{devices[rowIndex].name}</p>
          </div>
          <div style={{ display: "flex", gap: "8px", marginRight: "4px" }}>
            <Button size={"small"} intent={isSelected ? "primary" : "none"} icon={"select"} text={"Select"} active={isSelected} onClick={() => setSelectedDeviceId(devices[rowIndex].id)} />
            <Button size={"small"} intent={"none"} icon={"edit"} text={"Edit"} disabled={devices[rowIndex].status !== "disconnected"} onClick={() => handleDeviceEditClick(rowIndex)} />
          </div>
        </div>
      </Cell>
    );
  };

  const deviceStatusCellRenderer = (rowIndex: number) => {
    return (
      <Cell className={selectedRowClassName(rowIndex)} style={{ height: "100%", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "2px", alignItems: "center", justifyContent: "space-between"}} interactive={true}>
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
            <Button size={"small"} intent={"primary"} icon={"add"} text={"Add Device"} onClick={handleDeviceAddClick} />
          </div>

          {/* Devices table */}
          <div style={{ display: "flex", flexDirection: "column", maxHeight: "240px" }} ref={containerRef}>
            {devices.length > 0 ? (
              <Table key={devices.map((device) => `${device.id}:${device.name}:${device.status}`).join(",")} numRows={devices.length} selectionModes={SelectionModes.NONE} enableRowHeader={false} enableRowResizing={false} enableColumnResizing={false} enableMultipleSelection={false} defaultRowHeight={48} defaultColumnWidth={120} columnWidths={columnWidths} cellRendererDependencies={[selectedDevice?.id]}>
                <Column cellRenderer={deviceNameCellRenderer} name={"Name"} />
                <Column cellRenderer={deviceStatusCellRenderer} name={"Status"} />
              </Table>
            ) : (
              <Card style={{ padding: "8px" }}>
                <EmptyState icon={DEVICE_ICON} message={"No Devices Added"} />
              </Card>
            )}
          </div>
          
          {/* Device information */}
          <div style={{ display: "flex" }}>
            <Card style={{ width: "100%", padding: "8px", gap: "8px", display: "flex", flexDirection: "column" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "14px" }}>Device Information</p>

              {selectedDevice ? (
                <>
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

                  {/* Reported by the device, only shown while connected */}
                  {selectedDevice.info && [
                    ["Software Version", selectedDevice.info.version],
                    ["Platform", selectedDevice.info.simulated ? "Simulated" : "Raspberry Pi"],
                    ["Hostname", selectedDevice.info.hostname],
                    ["Operating System", selectedDevice.info.os],
                    ["Running Since", new Date(selectedDevice.info.started_at).toLocaleString()],
                    ["Free Storage", formatBytes(selectedDevice.info.storage_free_bytes)],
                  ].map(([label, value]) => (
                    <div key={label} style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
                      <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "12px" }}>{label}:</p>
                      <p style={{ marginBottom: "0px", fontSize: "12px" }}>{value}</p>
                    </div>
                  ))}

                  {/* Device action buttons */}
                  <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                    <Button size={"small"} intent={"success"} icon={"play"} text={"Connect"} disabled={selectedDevice.status === "connected" || isBusy} onClick={() => handleConnectClick(selectedDevice)} />
                    <Button size={"small"} intent={"danger"} icon={"stop"} text={"Disconnect"} disabled={selectedDevice.status === "disconnected" || isBusy} onClick={() => handleDisconnectClick(selectedDevice)} />
                    <Button size={"small"} intent={"primary"} text={"Sync Data"} icon={"refresh"} loading={syncingDeviceIds.has(selectedDevice.id)} disabled={selectedDevice.status !== "connected"} onClick={() => handleSyncClick(selectedDevice)} />
                  </div>
                </>
              ) : (
                <EmptyState icon={"info-sign"} message={"No Device Selected"} />
              )}
            </Card>
          </div>
          
          <DeviceEditDialog
            isOpen={deviceDialog.isOpen}
            device={deviceDialog.isEditing ? selectedDevice : undefined}
            devices={devices}
            onClose={() => setDeviceDialog((current) => ({ ...current, isOpen: false }))}
            onSave={onDeviceSave}
            onRemove={onDeviceRemove}
          />
        </div>
      </div>

      {/* Right: Device state */}
      <div style={{ width: "70%", height: "100%" }}>
        <div style={{ padding: "8px", width: "100%", height: "100%" }}>
          {devices.length > 0 ? (
          <Tabs id={"DeviceTabs"} className={"device-tabs"} selectedTabId={selectedDevice?.id} onChange={(id) => setSelectedDeviceId(String(id))} animate>
            {devices.map((device) => {
              const tabIcon = tabIconStyle(device.status, runningDeviceIds.has(device.id));
              return (
                <Tab
                  key={device.id}
                  id={device.id}
                  title={
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <Icon icon={DEVICE_ICON} />
                      {device.name}
                      <Icon icon={"offline"} color={tabIcon.color} className={tabIcon.className} />
                    </div>
                  }
                  panelClassName={"device-tab-panel"}
                  panel={<DeviceTab device={device} />}
                />
              );
            })}
          </Tabs>
          ) : (
            <EmptyState icon={DEVICE_ICON} message={'Use "Add Device" to get started.'} />
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
