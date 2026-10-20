import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { mkdir, readdir, readFile, rename, writeFile } from "fs/promises";
import path from "path";
import consola from "consola";
import { WebSocket } from "ws";
import * as z from "zod";

let mainWindow;

// Open sockets, keyed by `Device.id`
const connectedDevices = new Map();

const notifyDashboard = (channel, payload) => {
  mainWindow?.webContents.send(channel, payload);
};

const sendDeviceUpdate = (id, status, error) => {
  notifyDashboard("device-update", { id, status, error });
};

// Returns whether the command was sent
const sendCommandToDevice = (id, command) => {
  const ws = connectedDevices.get(id);
  if (ws?.readyState !== WebSocket.OPEN) {
    consola.error(`Cannot send: Device ${id} is not connected.`);
    return false;
  }
  ws.send(JSON.stringify(command));
  return true;
};

// ----- Device messages -----

// Not strict, so a device can add fields without breaking older dashboards
const count = z.int().nonnegative();
const DeviceMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("log"),
    level: z.enum(["trace", "debug", "info", "warning", "error", "critical"]),
    timestamp: z.number(),
    message: z.string(),
  }),
  z.object({
    type: z.literal("test_state"),
    test: z.string(),
    state: z.enum(["running", "passed", "failed"]),
  }),
  z.object({
    type: z.literal("input_state"),
    state: z.record(z.string(), z.boolean()),
  }),
  // Elapsed times are measured when the device sends the message
  z.object({
    type: z.literal("experiment_state"),
    state: z.enum(["idle", "running", "completed", "stopped"]),
    experiment_name: z.string().default(""),
    animal_id: z.string().default(""),
    experiment_elapsed_ms: count,
    trial: z.object({ index: count, id: z.string(), elapsed_ms: count }).nullable(),
    statistics: z.object({
      trials: count,
      nose_pokes: count,
      left_lever_presses: count,
      right_lever_presses: count,
      water_deliveries: count,
    }),
  }),
  z.object({
    type: z.literal("data_file"),
    name: z.string().min(1),
    contents: z.string(),
  }),
  z.object({
    type: z.literal("data_sync_complete"),
    error: z.string().optional(),
  }),
]);

const deviceMessageHandlers = {
  log: (id, { level, timestamp, message }) => notifyDashboard("device-log", { id, level, timestamp, message }),
  test_state: (id, { test, state }) => notifyDashboard("device-test-state", { id, test, state }),
  input_state: (id, { state }) => notifyDashboard("device-input-state", { id, state }),
  // Stamped on arrival so the renderer can run its timers between updates
  experiment_state: (id, { type, ...state }) => notifyDashboard("device-experiment-state", { id, received_at: Date.now(), ...state }),
  data_file: (id, file) => receiveDataFile(id, file),
  data_sync_complete: (id, { error }) => completeDataSync(id, error),
};

// ----- Device connections -----

ipcMain.on("device-connect", (event, device) => {
  const url = `ws://${device.network.ip}:${device.network.port}`;
  consola.start(`Connecting to: ${url}`);

  // Replace any existing connection, otherwise its socket would leak
  const existing = connectedDevices.get(device.id);
  if (existing) {
    existing.removeAllListeners();
    existing.terminate();
    connectedDevices.delete(device.id);
    finishDataSync(device.id, { status: "error", message: "Device reconnected during sync" });
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

    if (!Object.hasOwn(deviceMessageHandlers, message?.type)) {
      consola.info(`Unhandled message from ${url}:`, message);
      return;
    }
    const parsed = DeviceMessageSchema.safeParse(message);
    if (!parsed.success) {
      consola.warn(`Invalid "${message.type}" message from ${url}:`, z.prettifyError(parsed.error));
      return;
    }
    deviceMessageHandlers[parsed.data.type](device.id, parsed.data);
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
      finishDataSync(device.id, { status: "error", message: "Device disconnected during sync" });
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

// ----- Data sync -----
// The dashboard lists the files it already has, and the device sends each missing
// file followed by `data_sync_complete`. The device keeps its own copies.

const DATA_SYNC_TIMEOUT_MS = 30000;

// Syncs in progress, keyed by `Device.id`
const dataSyncs = new Map();

ipcMain.handle("device-data-sync", async (event, device) => {
  if (dataSyncs.has(device.id)) {
    return { status: "error", message: "A sync is already in progress for this device" };
  }

  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    title: `Sync Files from ${device.name}`,
    buttonLabel: "Sync Here",
    properties: ["openDirectory", "createDirectory"],
  });
  if (canceled || filePaths.length === 0) {
    return { status: "canceled" };
  }
  const directory = filePaths[0];

  let existing;
  try {
    existing = await listFiles(directory);
  } catch (error) {
    return { status: "error", message: `Could not read ${directory}: ${error.message}` };
  }

  // The device may have disconnected while the folder picker was open
  if (!sendCommandToDevice(device.id, { command: "data_sync", exclude: existing })) {
    return { status: "error", message: "Device is not connected" };
  }

  consola.start(`Syncing files from ${device.id} to ${directory}`);
  return new Promise((resolve) => {
    const sync = { directory, writes: [], resolve, timer: undefined };
    dataSyncs.set(device.id, sync);
    resetDataSyncTimer(device.id, sync);
  });
});

// Relative, `/`-separated paths of every file under `directory`, as the device names them
const listFiles = async (directory) => {
  const entries = await readdir(directory, { recursive: true, withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile())
    .map((entry) => path.relative(directory, path.join(entry.parentPath, entry.name)).split(path.sep).join("/"));
};

// Each file from the device restarts the timeout
const resetDataSyncTimer = (id, sync) => {
  clearTimeout(sync.timer);
  sync.timer = setTimeout(() => finishDataSync(id, { status: "error", message: "Device stopped responding during sync" }), DATA_SYNC_TIMEOUT_MS);
};

// Never writes outside the sync folder or over an existing file
const receiveDataFile = (id, { name, contents }) => {
  const sync = dataSyncs.get(id);
  if (!sync) {
    consola.warn(`Ignoring data file "${name}" from ${id}, no sync in progress`);
    return;
  }
  resetDataSyncTimer(id, sync);

  const target = path.resolve(sync.directory, name);
  const relative = path.relative(sync.directory, target);
  if (relative === "" || relative.startsWith("..") || path.isAbsolute(relative)) {
    consola.warn(`Ignoring data file with unsafe name from ${id}: ${name}`);
    sync.writes.push(Promise.resolve({ name, status: "failed" }));
    return;
  }

  sync.writes.push(
    mkdir(path.dirname(target), { recursive: true })
      .then(() => writeFile(target, contents, { encoding: "utf8", flag: "wx" }))
      .then(() => ({ name, status: "written" }))
      .catch((error) => {
        if (error.code === "EEXIST") return { name, status: "skipped" };
        consola.error(`Failed to write data file: ${target}`, error);
        return { name, status: "failed" };
      })
  );
};

const completeDataSync = async (id, error) => {
  const sync = dataSyncs.get(id);
  if (!sync) return;
  clearTimeout(sync.timer);

  const results = await Promise.all(sync.writes);
  if (error) {
    finishDataSync(id, { status: "error", message: `Device reported: ${error}` });
    return;
  }
  finishDataSync(id, {
    status: "synced",
    directory: sync.directory,
    written: results.filter((result) => result.status === "written").length,
    failed: results.filter((result) => result.status === "failed").map((result) => result.name),
  });
};

const finishDataSync = (id, result) => {
  const sync = dataSyncs.get(id);
  if (!sync) return;
  clearTimeout(sync.timer);
  dataSyncs.delete(id);
  consola.info(`Sync from ${id} finished:`, result);
  sync.resolve(result);
};

// ----- Experiment files -----

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

// ----- Stored devices -----
// Only configuration is stored, connection status and version are runtime state

const devicesFilePath = () => path.join(app.getPath("userData"), "devices.json");

const DevicesFileSchema = z.object({
  devices: z.array(
    z.object({
      id: z.string().min(1),
      name: z.string().min(1),
      network: z.object({
        ip: z.string().min(1),
        port: z.int().min(1).max(65535),
      }),
    })
  ),
});

ipcMain.handle("devices-load", async () => {
  const filePath = devicesFilePath();
  let contents;
  try {
    contents = await readFile(filePath, "utf8");
  } catch (error) {
    // No devices have been added yet
    if (error.code === "ENOENT") return { status: "loaded", devices: [] };
    consola.error(`Failed to read devices: ${filePath}`, error);
    return { status: "error", message: error.message, devices: [] };
  }

  let parsed;
  try {
    parsed = DevicesFileSchema.safeParse(JSON.parse(contents));
  } catch (error) {
    parsed = { success: false, error };
  }
  if (!parsed.success) {
    // Move the unreadable file aside so the next save doesn't overwrite it
    const backupPath = `${filePath}.invalid-${Date.now()}`;
    await rename(filePath, backupPath).catch(() => {});
    consola.error(`Invalid devices file, moved to: ${backupPath}`, parsed.error);
    return { status: "error", message: `Devices file was invalid and has been moved to ${backupPath}`, devices: [] };
  }

  return { status: "loaded", devices: parsed.data.devices };
});

ipcMain.handle("devices-save", async (event, devices) => {
  const filePath = devicesFilePath();
  const parsed = DevicesFileSchema.safeParse({ devices });
  if (!parsed.success) {
    consola.error("Refusing to save invalid devices", parsed.error);
    return { status: "error", message: z.prettifyError(parsed.error) };
  }

  // Write then rename, so a failed write can't corrupt the existing file
  const tempPath = `${filePath}.tmp`;
  try {
    await writeFile(tempPath, JSON.stringify(parsed.data, null, 2), "utf8");
    await rename(tempPath, filePath);
    return { status: "saved" };
  } catch (error) {
    consola.error(`Failed to save devices: ${filePath}`, error);
    return { status: "error", message: error.message };
  }
});

// ----- Window -----

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 800,
    icon: path.join(import.meta.dirname, "icon.png"),
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
  // macOS ignores the window icon, and packaged builds use the bundle icon
  if (process.platform === "darwin" && !app.isPackaged) app.dock.setIcon(path.join(import.meta.dirname, "icon-mac.png"));
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
