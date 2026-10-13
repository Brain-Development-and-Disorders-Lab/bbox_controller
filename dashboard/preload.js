const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("dashboardAPI", {
  deviceConnect: (device) => ipcRenderer.send("device-connect", device),
  deviceDisconnect: (device) => ipcRenderer.send("device-disconnect", device),
  deviceCommand: (device, command) => ipcRenderer.send("device-command", device, command),
  onDeviceUpdate: (callback) => ipcRenderer.on("device-update", callback),
  removeDeviceListeners: () => ipcRenderer.removeAllListeners("device-update")
});
