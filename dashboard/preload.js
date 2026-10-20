const { contextBridge, ipcRenderer, webUtils } = require("electron");

// Returns an unsubscribe function, so components can listen to a channel independently
const subscribe = (channel, callback) => {
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
};

contextBridge.exposeInMainWorld("dashboardAPI", {
  deviceConnect: (device) => ipcRenderer.send("device-connect", device),
  deviceDisconnect: (device) => ipcRenderer.send("device-disconnect", device),
  deviceCommand: (device, command) => ipcRenderer.send("device-command", device, command),
  deviceDataSync: (device) => ipcRenderer.invoke("device-data-sync", device),
  devicesLoad: () => ipcRenderer.invoke("devices-load"),
  devicesSave: (devices) => ipcRenderer.invoke("devices-save", devices),
  protocolSave: (defaultPath, contents) => ipcRenderer.invoke("protocol-save", defaultPath, contents),
  getFilePath: (file) => webUtils.getPathForFile(file),
  onDeviceUpdate: (callback) => subscribe("device-update", callback),
  onDeviceLog: (callback) => subscribe("device-log", callback),
  onDeviceTestState: (callback) => subscribe("device-test-state", callback),
  onDeviceInputState: (callback) => subscribe("device-input-state", callback),
  onDeviceSessionState: (callback) => subscribe("device-session-state", callback),
});
