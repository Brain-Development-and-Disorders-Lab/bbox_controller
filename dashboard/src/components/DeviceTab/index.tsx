// React
import { useEffect, useRef, useState } from "react";

// Blueprint components
import { Button, Card, Colors, FileInput, Tag, TextArea } from "@blueprintjs/core";

// Custom components
import StatusIndicator from "../StatusIndicator";
import ExperimentEditDialog from "../ExperimentEditDialog";
import ExperimentLoadDialog from "../ExperimentLoadDialog";

// Custom types
import { DeviceLog, DeviceTabProps, DeviceTestState, InputChannel, InputChannelRow, LoadedExperiment, PendingExperimentFile, StatusIndicatorProps } from "../../../types";

// Experiment format
import { fileNameFromPath, parseExperiment } from "../../lib/experiment";

// Utility libraries
import consola from "consola";
import _ from "lodash";

// Valid commands
import { TEST_COMMANDS, EXPERIMENT_COMMANDS } from "../../../../shared/commands.json";

// Oldest console lines are dropped past this limit
const MAX_CONSOLE_LINES = 1000;

// Rows of the "Input Status" card, in display order
const INPUT_CHANNELS: InputChannelRow[] = [
  { channel: "left_lever", label: "Left Lever" },
  { channel: "left_lever_light", label: "Left Lever Light" },
  { channel: "right_lever", label: "Right Lever" },
  { channel: "right_lever_light", label: "Right Lever Light" },
  { channel: "nose_poke", label: "Nose Poke" },
  { channel: "nose_light", label: "Nose Light" },
  { channel: "water_valve", label: "Water Valve" },
];

// Untested tests keep the indicator's default color
const testIndicatorStatus = (state?: DeviceTestState["state"]): StatusIndicatorProps["status"] => {
  if (state === "running") return "neutral";
  if (state === "passed") return "good";
  if (state === "failed") return "bad";
  return undefined;
};

const formatLog = (log: DeviceLog) => {
  const time = new Date(log.timestamp);
  const milliseconds = String(time.getMilliseconds()).padStart(3, "0");
  // Pad the level to the longest name ("critical") so messages start in the same column
  const level = `[${log.level}]`.padEnd(10);
  return `${time.toTimeString().slice(0, 8)}.${milliseconds}\t${level} ${log.message}`;
};

const DeviceTab = (props: DeviceTabProps) => {
  const { device } = props;
  const [animalID, setAnimalID] = useState("");

  // The experiment loaded onto this device
  const [loadedExperiment, setLoadedExperiment] = useState<LoadedExperiment>();

  // Experiment file under review. Kept after the review closes so the dialog doesn't empty mid-transition.
  const [pendingFile, setPendingFile] = useState<PendingExperimentFile>();
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  // Create or edit dialog. `isEditing` is kept after closing for the same reason.
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

  // Console state
  const [consoleLines, setConsoleLines] = useState<string[]>([]);
  const consoleRef = useRef<HTMLTextAreaElement>(null);
  const consoleAtBottom = useRef(true);
  
  // Append live logs from this device
  useEffect(() => {
    return window.dashboardAPI.onDeviceLog((log) => {
      if (log.id !== device.id) return;
      setConsoleLines((current) => [...current, formatLog(log)].slice(-MAX_CONSOLE_LINES));
    });
  }, [device.id]);
  
  // Live input and test state from this device
  const [inputState, setInputState] = useState<Partial<Record<InputChannel, boolean>>>({});
  const [testStates, setTestStates] = useState<Record<string, DeviceTestState["state"]>>({});

  useEffect(() => {
    const unsubscribeInput = window.dashboardAPI.onDeviceInputState((update) => {
      if (update.id === device.id) setInputState(update.state);
    });
    const unsubscribeTest = window.dashboardAPI.onDeviceTestState((update) => {
      if (update.id === device.id) setTestStates((current) => ({ ...current, [update.test]: update.state }));
    });
    return () => {
      unsubscribeInput();
      unsubscribeTest();
    };
  }, [device.id]);

  // The device replays its recent history on connect, so start each connection fresh
  useEffect(() => {
    if (device.status === "connecting") {
      setConsoleLines([]);
      setInputState({});
      setTestStates({});
    }
  }, [device.status]);
  
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
  
  // Test parameters
  const [testWaterDuration, setTestWaterDuration] = useState(1000);
  const [testLeverLightDuration, setTestLeverLightDuration] = useState(1000);
  const [testNoseLightDuration, setTestNoseLightDuration] = useState(1000);
  const [testDisplayDuration, setTestDisplayDuration] = useState(1000);
  
  const sendTestCommand = (command: string, parameter?: number) => {
    if (TEST_COMMANDS.includes(command)) {
      window.dashboardAPI.deviceCommand(device, { command: command, parameter: parameter ?? 0 });
    } else {
      consola.error("Unknown test command:", command);
    }
  };
  
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1, minHeight: 0 }}>
      <p style={{ marginBottom: "0px" }}>Experiment Management</p>
      <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Animal ID:</p>
          <input type={"text"} placeholder={"Enter animal ID"} style={{ minWidth: "320px" }} value={animalID} onChange={(event) => setAnimalID(event.target.value)} />
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Experiment:</p>
          {loadedExperiment ? (
            <Tag icon={"document"} size={"large"} minimal onRemove={() => setLoadedExperiment(undefined)} title={loadedExperiment.filePath}>
              {fileNameFromPath(loadedExperiment.filePath)}
            </Tag>
          ) : (
            <FileInput text={"Choose an experiment file..."} inputProps={{ accept: ".json,application/json" }} onInputChange={onExperimentFileChange} style={{ minWidth: "320px" }} />
          )}
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
          <Button text={"New Experiment"} icon={"add"} size={"small"} disabled={!_.isUndefined(loadedExperiment)} onClick={() => setExperimentDialog({ isOpen: true, isEditing: false })} />
          <Button text={"Edit Experiment"} icon={"edit"} size={"small"} disabled={_.isUndefined(loadedExperiment)} onClick={() => setExperimentDialog({ isOpen: true, isEditing: true })} />
          <Button text={"Start Experiment"} icon={"play"} intent={"success"} size={"small"} disabled={_.isUndefined(loadedExperiment)} />
          <Button text={"Stop Experiment"} icon={"stop"} intent={"danger"} size={"small"} disabled={_.isUndefined(loadedExperiment)} />
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
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Water Delivery</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={testWaterDuration} onChange={(event) => setTestWaterDuration(parseInt(event.target.value))} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator status={testIndicatorStatus(testStates["test_water_delivery"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_water_delivery", testWaterDuration)} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Levers</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <StatusIndicator status={testIndicatorStatus(testStates["test_input_levers"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_input_levers")} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Lever Lights</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={testLeverLightDuration} onChange={(event) => setTestLeverLightDuration(parseInt(event.target.value))} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator status={testIndicatorStatus(testStates["test_led_levers"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_led_levers", testLeverLightDuration)} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test IR</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <StatusIndicator status={testIndicatorStatus(testStates["test_input_ir"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_input_ir")} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Nose Light</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={testNoseLightDuration} onChange={(event) => setTestNoseLightDuration(parseInt(event.target.value))} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator status={testIndicatorStatus(testStates["test_led_port"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_led_port", testNoseLightDuration)} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Displays</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={testDisplayDuration} onChange={(event) => setTestDisplayDuration(parseInt(event.target.value))} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator status={testIndicatorStatus(testStates["test_displays"])} />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} disabled={device.status !== "connected"} onClick={() => sendTestCommand("test_displays", testDisplayDuration)} />
              </div>
            </div>
          </Card>
        </div>

        {/* Experiment Statistics */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "40%" }}>
          <p style={{ marginBottom: "0px" }}>Experiment Statistics</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Total Trials</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>0</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Total Nose Pokes</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>0</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Total Left Lever Presses</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>0</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Total Right Lever Presses</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>0</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Total Water Deliveries</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>0</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Trial Time</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold", color: Colors.BLUE3 }}>00:00:00</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Active Trial</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>None</p>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Time</p>
              <p style={{ marginBottom: "0px", fontWeight: "bold", color: Colors.BLUE3 }}>00:00:00</p>
            </div>
          </Card>
        </div>
      </div>

      {/* Console */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%", flex: 1, minHeight: 0 }}>
        <p style={{ marginBottom: "0px" }}>Console</p>
        <TextArea style={{ backgroundColor: "black", color: "white", fontFamily: "monospace", fontSize: "10px", flex: 1, minHeight: "240px", width: "100%", resize: "none" }} value={consoleLines.join("\n")} inputRef={consoleRef} onScroll={onConsoleScroll} readOnly />
      </div>
      
      {/* A saved experiment has just been validated, so it loads without review */}
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
