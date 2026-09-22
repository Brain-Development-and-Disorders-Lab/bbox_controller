import { app, BrowserWindow, ipcMain } from "electron";
import path from "path";
import consola from "consola";
import { WebSocket } from "ws";

let mainWindow;
const connectedDevices = new Map();

ipcMain.on("device-connect", (event, device) => {
  const url = `ws://${device.network.ip}:${device.network.port}`;
  const targetKey = `${device.network.ip}:${device.network.port}`;
  consola.start(`Connecting to: ${url}`);

  // Close any existing connection to this target before opening a new one,
  // otherwise repeated connect attempts leak sockets that are never closed.
  const existing = connectedDevices.get(targetKey);
  if (existing) {
    existing.removeAllListeners();
    existing.terminate();
    connectedDevices.delete(targetKey);
  }

  try {
    const ws = new WebSocket(url);

    ws.on("open", () => {
      consola.success(`Successfully connected to device: ${url}`);
      connectedDevices.set(targetKey, ws);
      mainWindow.webContents.send("device-update", `Connected to ${targetKey}`);
    });

    ws.on("message", (data) => {
      consola.info(`Data from ${targetKey}:`, data.toString());
    });

    ws.on("close", () => {
      consola.info(`Disconnected from ${targetKey}`);
      connectedDevices.delete(targetKey);
      mainWindow.webContents.send("device-update", "Disconnected");
    });

    ws.on("error", (err) => {
      consola.error(`Socket error on ${targetKey}:`, err.message !== "" ? err.message : "No additional information.");
      mainWindow.webContents.send("device-update", `Error: ${err.message !== "" ? err.message : "No additional information."}`);
    });

  } catch (error) {
    mainWindow.webContents.send("device-update", `Failed to initialize: ${error.message}`);
  }
});

ipcMain.on("device-disconnect", (event, device) => {
  const targetKey = `${device.network.ip}:${device.network.port}`;
  const ws = connectedDevices.get(targetKey);

  if (!ws) {
    consola.warn(`No active connection to disconnect: ${targetKey}`);
    return;
  }

  consola.start(`Disconnecting from: ${targetKey}`);
  ws.close();
});

// Helper function to target specific device
const sendCommandToDevice = (deviceId, commandObject) => {
  const ws = connectedDevices.get(deviceId);
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify(commandObject));
  } else {
    consola.error(`Cannot send: Device ${deviceId} is not connected.`);
  }
};

// Helper function to broadcast a command to ALL connected devices at once
const broadcastCommand = (commandObject) => {
  const payload = JSON.stringify(commandObject);
  connectedDevices.forEach((ws, deviceId) => {
    if (ws.readyState === 1) {
      ws.send(payload);
    }
  });
};

// Helper to push updates to the Electron UI window
const notifyDashboard = (channel, payload) => {
  if (mainWindow) {
    mainWindow.webContents.send(channel, payload);
  }
};

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(import.meta.dirname, "preload.js"),
    },
  });

  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(import.meta.dirname, "../dist/index.html"));
  }
  mainWindow.on("closed", () => (mainWindow = null));
};

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
