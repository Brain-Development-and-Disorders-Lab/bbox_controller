import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { writeFile } from "fs/promises";
import path from "path";
import consola from "consola";
import { WebSocket } from "ws";

let mainWindow;

// Active sockets, keyed by `Device.id`
const connectedDevices = new Map();

// Push a status update for a single device to the renderer
const sendDeviceUpdate = (id, status, error) => {
  if (mainWindow) {
    mainWindow.webContents.send("device-update", { id, status, error });
  }
};

// Forward a log record from a device to the renderer
const sendDeviceLog = (id, log) => {
  if (mainWindow) {
    mainWindow.webContents.send("device-log", { id, level: log.level, timestamp: log.timestamp, message: log.message });
  }
};

ipcMain.on("device-connect", (event, device) => {
  const url = `ws://${device.network.ip}:${device.network.port}`;
  consola.start(`Connecting to: ${url}`);

  // Close any existing connection to this device before opening a new one,
  // otherwise repeated connect attempts leak sockets that are never closed.
  const existing = connectedDevices.get(device.id);
  if (existing) {
    existing.removeAllListeners();
    existing.terminate();
    connectedDevices.delete(device.id);
  }

  let ws;
  try {
    ws = new WebSocket(url);
  } catch (error) {
    sendDeviceUpdate(device.id, "disconnected", error.message);
    return;
  }
  connectedDevices.set(device.id, ws);

  ws.on("open", () => {
    consola.success(`Successfully connected to device: ${url}`);
    sendDeviceUpdate(device.id, "connected");
  });

  ws.on("message", (data) => {
    let message;
    try {
      message = JSON.parse(data.toString());
    } catch {
      consola.warn(`Unparseable message from ${url}:`, data.toString());
      return;
    }

    if (message.type === "log") {
      sendDeviceLog(device.id, message);
    } else if (message.type === "test_state") {
      notifyDashboard("device-test-state", { id: device.id, test: message.test, state: message.state });
    } else if (message.type === "input_state") {
      notifyDashboard("device-input-state", { id: device.id, state: message.state });
    } else {
      consola.info(`Data from ${url}:`, message);
    }
  });

  ws.on("error", (err) => {
    const message = err.message !== "" ? err.message : "No additional information.";
    consola.error(`Socket error on ${url}:`, message);
    sendDeviceUpdate(device.id, "disconnected", message);
  });

  ws.on("close", () => {
    consola.info(`Disconnected from ${url}`);
    if (connectedDevices.get(device.id) === ws) {
      connectedDevices.delete(device.id);
    }
    sendDeviceUpdate(device.id, "disconnected");
  });
});

ipcMain.on("device-disconnect", (event, device) => {
  const ws = connectedDevices.get(device.id);
  if (!ws) {
    consola.warn(`No active connection to disconnect: ${device.id}`);
    sendDeviceUpdate(device.id, "disconnected");
    return;
  }

  consola.start(`Disconnecting from: ${device.id}`);
  ws.close();
});

ipcMain.on("device-command", (event, device, command) => {
  sendCommandToDevice(device.id, command);
});

// Ask where to save an experiment file then write it to the selected location
ipcMain.handle("experiment-save", async (event, defaultPath, contents) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    title: "Save Experiment",
    defaultPath: path.isAbsolute(defaultPath) ? defaultPath : path.join(app.getPath("documents"), defaultPath),
    filters: [{ name: "Experiment", extensions: ["json"] }],
  });
  if (canceled || !filePath) {
    return { status: "canceled" };
  }

  try {
    await writeFile(filePath, contents, "utf8");
    consola.success(`Saved experiment: ${filePath}`);
    return { status: "saved", filePath };
  } catch (error) {
    consola.error(`Failed to save experiment: ${filePath}`, error);
    return { status: "error", message: error.message };
  }
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
