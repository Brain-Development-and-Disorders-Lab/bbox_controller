// React
import { useState } from "react";

// Blueprint components
import { Button, Card, Colors, MenuItem, Tab, Tabs, TextArea } from "@blueprintjs/core";
import { ItemRenderer, Select } from "@blueprintjs/select";

// Custom components
import StatusIndicator from "../StatusIndicator";

// Custom types
import { Device, Experiment } from "../../../types";

// Utilities
import _ from "lodash";
import ExperimentEditDialog from "../ExperimentEditDialog";

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

const renderExperiment: ItemRenderer<Experiment> = (experiment, { handleClick, handleFocus, modifiers, query }) => {
    if (!modifiers.matchesPredicate) {
      return null;
    }
    return (
      <MenuItem
        active={modifiers.active}
        disabled={modifiers.disabled}
        key={experiment.id}
        onClick={handleClick}
        onFocus={handleFocus}
        roleStructure={"listoption"}
        text={experiment.name}
      />
    );
};

const DeviceStatusTab = (props: { device: Device, experiments: Experiment[] }) => {
  // Device status state
  const [animalID, setAnimalID] = useState("");
  const [experiments, setExperiments] = useState(props.experiments);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment>();
  const [consoleOutput, setConsoleOutput] = useState("");
  
  // Create, edit experiment state
  const [experimentEditOpen, setExperimentEditOpen] = useState(false);
  
  const onExperimentSave = (experiment: Experiment) => {
    console.info("Experiment:", experiment);
  };
  
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", height: "100%" }}>
      <p style={{ marginBottom: "0px" }}>Experiment Management</p>
      <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Animal ID:</p>
          <input type={"text"} placeholder={"Enter animal ID"} style={{ minWidth: "320px" }} value={animalID} onChange={(event) => setAnimalID(event.target.value)} />
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <p style={{ marginBottom: "0px" }}>Experiment:</p>
          <Select<Experiment>
            items={EXAMPLE_EXPERIMENTS}
            itemRenderer={renderExperiment}
            noResults={<MenuItem disabled={true} text={"No results."} roleStructure={"listoption"} />}
            onItemSelect={setSelectedExperiment}
          >
            <Button text={selectedExperiment?.name ?? "Select an Experiment"} endIcon={"double-caret-vertical"} style={{ width: "100%" }} />
          </Select>
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
          <Button text={"New Experiment"} icon={"add"} size={"small"} onClick={() => setExperimentEditOpen(true)} />
          <Button text={"Edit Experiment"} icon={"edit"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name) || experiments.length === 0} />
          <Button text={"Start Experiment"} icon={"play"} intent={"success"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name)} />
          <Button text={"Stop Experiment"} icon={"stop"} intent={"danger"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name)} />
        </div>
      </Card>
      
      {/* Status Group */}
      <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
        {/* Input Status */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "20%" }}>
          <p style={{ marginBottom: "0px" }}>Input Status</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Left Lever</p>
              <StatusIndicator status={"bad"} />
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Left Lever Light</p>
              <StatusIndicator status={"bad"} />
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Right Lever</p>
              <StatusIndicator status={"bad"} />
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Right Lever Light</p>
              <StatusIndicator status={"bad"} />
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Nose Poke</p>
              <StatusIndicator status={"bad"} />
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Nose Light</p>
              <StatusIndicator status={"bad"} />
            </div>
          </Card>
        </div>

        {/* Test Status */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "40%" }}>
          <p style={{ marginBottom: "0px" }}>Test Status</p>
          <Card style={{ display: "flex", flexDirection: "column", gap:"8px", padding: "8px" }}>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Water Delivery</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={1000} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Levers</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Lever Lights</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={1000} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test IR</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Nose Light</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={1000} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px" }}>Test Displays</p>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type={"number"} style={{ width: "60px" }} value={1000} />
                <p style={{ marginBottom: "0px" }}>ms</p>
                <div style={{ width: "2px" }} />
                <StatusIndicator />
                <div style={{ width: "2px" }} />
                <Button text={"Test"} size={"small"} />
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
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%", height: "100%" }}>
        <p style={{ marginBottom: "0px" }}>Console</p>
        <TextArea style={{ backgroundColor: "black", color: "white", fontSize: "10px", minHeight: "240px", width: "100%", resize: "none" }} value={consoleOutput} readOnly />
      </div>
      
      <ExperimentEditDialog isOpen={experimentEditOpen} setIsOpen={setExperimentEditOpen} onSave={onExperimentSave} />
    </div>
  );
};

const DeviceStatusPanel = (props: { devices: Device[] }) => {
  return (
    <div style={{ padding: "8px", width: "100%", height: "100%" }}>
      <Tabs id={"DeviceTabs"} animate>
        {props.devices.map((device) => {
          return (
            <Tab id={device.id} title={device.name} style={{ height: "100%" }} panel={<DeviceStatusTab device={device} experiments={EXAMPLE_EXPERIMENTS} />} />
          );
        })}
      </Tabs>
    </div>
  );
};

export default DeviceStatusPanel;
