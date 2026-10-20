// React
import { useEffect, useRef, useState } from "react";

// Blueprint components
import { Button, Card, Colors, FileInput, Tag, TextArea } from "@blueprintjs/core";

// Custom components
import StatusIndicator from "../StatusIndicator";
import ExperimentEditDialog from "../ExperimentEditDialog";
import ExperimentLoadDialog from "../ExperimentLoadDialog";

// Custom types
import {
  DeviceExperimentState,
  DeviceLog,
  DeviceTabProps,
  DeviceTestState,
  ExperimentStatistics,
  InputChannel,
  LoadedExperiment,
  PendingExperimentFile,
  StatusIndicatorProps,
} from "../../../types";

// Experiment format
import { fileNameFromPath, parseExperiment, timelineItemLabel } from "../../lib/experiment";

// Utility libraries
import consola from "consola";
import _ from "lodash";

// Valid commands
import { TEST_COMMANDS } from "../../../../shared/commands.json";

// Oldest console lines are dropped past this limit
const MAX_CONSOLE_LINES = 1000;

// Rows of the "Input Status" card, in display order
const INPUT_CHANNELS: { channel: InputChannel; label: string }[] = [
  { channel: "left_lever", label: "Left Lever" },
  { channel: "left_lever_light", label: "Left Lever Light" },
  { channel: "right_lever", label: "Right Lever" },
  { channel: "right_lever_light", label: "Right Lever Light" },
  { channel: "nose_poke", label: "Nose Poke" },
  { channel: "nose_light", label: "Nose Light" },
  { channel: "water_valve", label: "Water Valve" },
];

// Rows of the "Test Status" card. Output tests run for a duration, input tests wait for a trigger.
const TESTS: { command: string; label: string; hasDuration: boolean }[] = [
  { command: "test_water_delivery", label: "Test Water Delivery", hasDuration: true },
  { command: "test_input_levers", label: "Test Levers", hasDuration: false },
  { command: "test_led_levers", label: "Test Lever Lights", hasDuration: true },
  { command: "test_input_ir", label: "Test IR", hasDuration: false },
  { command: "test_led_port", label: "Test Nose Light", hasDuration: true },
  { command: "test_displays", label: "Test Displays", hasDuration: true },
];
const DEFAULT_TEST_DURATION_MS = 1000;

// Counters of the "Experiment Statistics" card
const STATISTICS_ROWS: { key: keyof ExperimentStatistics; label: string }[] = [
  { key: "trials", label: "Total Trials" },
  { key: "nose_pokes", label: "Total Nose Pokes" },
  { key: "left_lever_presses", label: "Total Left Lever Presses" },
  { key: "right_lever_presses", label: "Total Right Lever Presses" },
  { key: "water_deliveries", label: "Total Water Deliveries" },
];

// How often the experiment and trial timers redraw while running
const TIMER_INTERVAL_MS = 250;

// Untested tests keep the indicator's default color
const testIndicatorStatus = (state?: DeviceTestState["state"]): StatusIndicatorProps["status"] => {
  if (state === "running") return "neutral";
  if (state === "passed") return "good";
  if (state === "failed") return "bad";
  return undefined;
};

// Local time as `HH:MM:SS.mmm`
const formatTime = (timestamp: number) => {
  const time = new Date(timestamp);
  const milliseconds = String(time.getMilliseconds()).padStart(3, "0");
  return `${time.toTimeString().slice(0, 8)}.${milliseconds}`;
};

const formatLog = (log: DeviceLog) => {
  // Pad the level to the longest name ("critical") so messages start in the same column
  const level = `[${log.level}]`.padEnd(10);
  return `${formatTime(log.timestamp)}\t${level} ${log.message}`;
};

// Duration as `HH:MM:SS`
const formatDuration = (milliseconds: number) => {
  const seconds = Math.floor(milliseconds / 1000);
  return [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60].map((part) => String(part).padStart(2, "0")).join(":");
};

// Console line marking a connection change
const formatEvent = (event: string) => `----- ${event} at ${formatTime(Date.now())} -----`;

const DeviceTab = (props: DeviceTabProps) => {
  const { device } = props;

  // ----- Experiment -----

  const [animalID, setAnimalID] = useState("");
  const [loadedExperiment, setLoadedExperiment] = useState<LoadedExperiment>();

  // Kept after the review closes so the dialog doesn't empty mid-transition
  const [pendingFile, setPendingFile] = useState<PendingExperimentFile>();
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  // `isEditing` is kept after closing for the same reason
  const [experimentDialog, setExperimentDialog] = useState({ isOpen: false, isEditing: false });

  const onExperimentFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const input = event.currentTarget;
    const file = input.files?.[0];
    // Clear the input so selecting the same file again still fires a change
    input.value = "";
    if (!file) return;

    const filePath = window.dashboardAPI.getFilePath(file) || file.name;
    try {
      setPendingFile({ filePath, result: parseExperiment(await file.text()) });
    } catch (error) {
      setPendingFile({ filePath, result: { success: false, errors: [`Could not read file: ${(error as Error).message}`] } });
    }
    setIsReviewOpen(true);
  };

  const onExperimentConfirm = (loaded: LoadedExperiment) => {
    setLoadedExperiment(loaded);
    setIsReviewOpen(false);
  };

  // The device confirms with `experiment_state`, which enables stopping
  const startExperiment = () => {
    if (!loadedExperiment) return;
    window.dashboardAPI.deviceCommand(device, { command: "experiment_start", animal_id: animalID.trim(), experiment: loadedExperiment.experiment });
  };

  const stopExperiment = () => window.dashboardAPI.deviceCommand(device, { command: "experiment_stop" });

  // ----- Live device state -----

  const [inputState, setInputState] = useState<Partial<Record<InputChannel, boolean>>>({});
  const [testStates, setTestStates] = useState<Record<string, DeviceTestState["state"]>>({});
  const [experimentState, setExperimentState] = useState<DeviceExperimentState>();
  const isExperimentRunning = experimentState?.state === "running";

  useEffect(() => {
    const unsubscribeInput = window.dashboardAPI.onDeviceInputState((update) => {
      if (update.id === device.id) setInputState(update.state);
    });
    const unsubscribeTest = window.dashboardAPI.onDeviceTestState((update) => {
      if (update.id === device.id) setTestStates((current) => ({ ...current, [update.test]: update.state }));
    });
    const unsubscribeExperiment = window.dashboardAPI.onDeviceExperimentState((update) => {
      if (update.id === device.id) setExperimentState(update);
    });
    return () => {
      unsubscribeInput();
      unsubscribeTest();
      unsubscribeExperiment();
    };
  }, [device.id]);

  // Timers add the time since the last update to the device's elapsed times
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!isExperimentRunning) return;
    const interval = setInterval(() => setNow(Date.now()), TIMER_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isExperimentRunning]);

  const sinceUpdate = experimentState && isExperimentRunning ? Math.max(0, now - experimentState.received_at) : 0;
  const experimentElapsed = experimentState ? experimentState.experiment_elapsed_ms + sinceUpdate : 0;
  const trialElapsed = experimentState?.trial ? experimentState.trial.elapsed_ms + sinceUpdate : 0;

  // Named from the loaded timeline, falling back to the ID the device reported
  const activeTrial = experimentState?.trial;
  const activeTrialItem = activeTrial ? loadedExperiment?.experiment.timeline.items.find((item) => item.id === activeTrial.id) : undefined;
  const activeTrialLabel = activeTrial ? (activeTrialItem ? timelineItemLabel(activeTrialItem) : activeTrial.id) : "None";

  // Output test durations, keyed by command
  const [testDurations, setTestDurations] = useState<Record<string, number>>({});
  const testDuration = (command: string) => testDurations[command] ?? DEFAULT_TEST_DURATION_MS;

  const sendTestCommand = (command: string, parameter: number) => {
    if (TEST_COMMANDS.includes(command)) {
      window.dashboardAPI.deviceCommand(device, { command, parameter });
    } else {
      consola.error("Unknown test command:", command);
    }
  };

  // ----- Console -----

  const [consoleLines, setConsoleLines] = useState<string[]>([]);
  const consoleRef = useRef<HTMLTextAreaElement>(null);
  const consoleAtBottom = useRef(true);
  const appendConsoleLine = (line: string) => setConsoleLines((current) => [...current, line].slice(-MAX_CONSOLE_LINES));

  useEffect(() => {
    return window.dashboardAPI.onDeviceLog((log) => {
      if (log.id === device.id) appendConsoleLine(formatLog(log));
    });
  }, [device.id]);

  // Keep the console scrolled to the newest line, unless the user has scrolled up
  useEffect(() => {
    if (consoleRef.current && consoleAtBottom.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleLines]);

  const onConsoleScroll = () => {
    const element = consoleRef.current;
    if (element) {
      consoleAtBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 16;
    }
  };

  // Clear everything on a new connection, and mark connection changes in the console
  const previousStatus = useRef(device.status);
  useEffect(() => {
    const previous = previousStatus.current;
    previousStatus.current = device.status;
    if (device.status === previous) return;

    if (device.status === "connecting") {
      setConsoleLines([]);
      setInputState({});
      setTestStates({});
      setExperimentState(undefined);
    } else if (device.status === "connected") {
      appendConsoleLine(formatEvent("Connected"));
    } else if (device.status === "disconnected") {
      appendConsoleLine(formatEvent(previous === "connecting" ? "Connection failed" : "Disconnected"));
    }
  }, [device.status]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1, minHeight: 0 }}>
      <p style={{ marginBottom: "0px" }}>Experiment Management</p>
      <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Animal ID:</p>
          <input type={"text"} placeholder={"Enter animal ID"} style={{ minWidth: "320px" }} value={animalID} disabled={isExperimentRunning} onChange={(event) => setAnimalID(event.target.value)} />
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Experiment:</p>
          {loadedExperiment ? (
            <Tag icon={"document"} size={"large"} minimal onRemove={isExperimentRunning ? undefined : () => setLoadedExperiment(undefined)} title={loadedExperiment.filePath}>
              {fileNameFromPath(loadedExperiment.filePath)}
            </Tag>
          ) : (
            <FileInput text={"Choose an experiment file..."} inputProps={{ accept: ".json,application/json" }} onInputChange={onExperimentFileChange} style={{ minWidth: "320px" }} />
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
          <Button text={"New Experiment"} icon={"add"} size={"small"} disabled={!_.isUndefined(loadedExperiment)} onClick={() => setExperimentDialog({ isOpen: true, isEditing: false })} />
          <Button text={"Edit Experiment"} icon={"edit"} size={"small"} disabled={_.isUndefined(loadedExperiment) || isExperimentRunning} onClick={() => setExperimentDialog({ isOpen: true, isEditing: true })} />
          <Button text={"Start Experiment"} icon={"play"} intent={"success"} size={"small"} disabled={device.status !== "connected" || _.isUndefined(loadedExperiment) || animalID.trim() === "" || isExperimentRunning} onClick={startExperiment} />
          <Button text={"Stop Experiment"} icon={"stop"} intent={"danger"} size={"small"} disabled={device.status !== "connected" || !isExperimentRunning} onClick={stopExperiment} />
        </div>
      </Card>
      
      {/* Status Group */}
      <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
        {/* Input Status */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "20%" }}>
          <p style={{ marginBottom: "0px" }}>Input Status</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            {INPUT_CHANNELS.map(({ channel, label }) => (
              <div key={channel} style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                <p style={{ marginBottom: "0px" }}>{label}</p>
                <StatusIndicator status={inputState[channel] ? "good" : "bad"} />
              </div>
            ))}
          </Card>
        </div>

        {/* Test Status */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "40%" }}>
          <p style={{ marginBottom: "0px" }}>Test Status</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            {TESTS.map(({ command, label, hasDuration }) => (
              <div key={command} style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                <p style={{ marginBottom: "0px" }}>{label}</p>
                <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                  {hasDuration && (
                    <>
                      <input type={"number"} style={{ width: "60px" }} value={Number.isNaN(testDuration(command)) ? "" : testDuration(command)} onChange={(event) => setTestDurations((current) => ({ ...current, [command]: parseInt(event.target.value) }))} />
                      <p style={{ marginBottom: "0px" }}>ms</p>
                      <div style={{ width: "2px" }} />
                    </>
                  )}
                  <StatusIndicator status={testIndicatorStatus(testStates[command])} />
                  <div style={{ width: "2px" }} />
                  <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand(command, hasDuration ? testDuration(command) : 0)} />
                </div>
              </div>
            ))}
          </Card>
        </div>

        {/* Experiment Statistics */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "40%" }}>
          <p style={{ marginBottom: "0px" }}>Experiment Statistics</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            {STATISTICS_ROWS.map(({ key, label }) => (
              <div key={key} style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>{label}</p>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>{experimentState?.statistics[key] ?? 0}</p>
              </div>
            ))}
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Trial Time</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold", color: Colors.BLUE3 }}>{formatDuration(trialElapsed)}</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Active Trial</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>{activeTrialLabel}</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Time</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold", color: Colors.BLUE3 }}>{formatDuration(experimentElapsed)}</p>
            </div>
          </Card>
        </div>
      </div>

      {/* Console */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%", flex: 1, minHeight: 0 }}>
        <p style={{ marginBottom: "0px" }}>Console</p>
        <TextArea style={{ backgroundColor: "black", color: "white", fontFamily: "monospace", fontSize: "10px", flex: 1, minHeight: "240px", width: "100%", resize: "none" }} value={consoleLines.join("\n")} placeholder={"Connect to this device to see logs"} inputRef={consoleRef} onScroll={onConsoleScroll} readOnly />
      </div>

      <ExperimentEditDialog
        isOpen={experimentDialog.isOpen}
        loaded={experimentDialog.isEditing ? loadedExperiment : undefined}
        onClose={() => setExperimentDialog((current) => ({ ...current, isOpen: false }))}
        onSave={setLoadedExperiment}
      />
      <ExperimentLoadDialog isOpen={isReviewOpen} file={pendingFile} onClose={() => setIsReviewOpen(false)} onConfirm={onExperimentConfirm} />
    </div>
  );
};

export default DeviceTab;
