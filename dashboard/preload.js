const { contextBridge, ipcRenderer, webUtils } = require("electron");

// Subscribe to a main process channel. Returns an unsubscribe function so multiple
// components can listen to the same channel independently.
const subscribe = (channel, callback) => {
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
};

contextBridge.exposeInMainWorld("dashboardAPI", {
  deviceConnect: (device) => ipcRenderer.send("device-connect", device),
  deviceDisconnect: (device) => ipcRenderer.send("device-disconnect", device),
  deviceCommand: (device, command) => ipcRenderer.send("device-command", device, command),
  experimentSave: (defaultPath, contents) => ipcRenderer.invoke("experiment-save", defaultPath, contents),
  getFilePath: (file) => webUtils.getPathForFile(file),
  onDeviceUpdate: (callback) => subscribe("device-update", callback),
  onDeviceLog: (callback) => subscribe("device-log", callback),
  onDeviceTestState: (callback) => subscribe("device-test-state", callback),
  onDeviceInputState: (callback) => subscribe("device-input-state", callback),
});
