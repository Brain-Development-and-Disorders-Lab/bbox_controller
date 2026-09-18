// React
import { useState } from "react";

// Blueprint components
import { Button, Card, MenuItem, Tab, Tabs } from "@blueprintjs/core";
import { ItemRenderer, Select } from "@blueprintjs/select";

// Custom types
import { Device, Experiment } from "../../../types";

// Utilities
import _ from "lodash";

const EXAMPLE_EXPERIMENTS: Experiment[] = [
  {
    id: "e_00",
    name: "Experiment 1",
  },
  {
    id: "e_01",
    name: "Experiment 2",
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
  const [experiments, setExperiments] = useState(props.experiments);
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment>();
  const [animalID, setAnimalID] = useState("");
  
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
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
          <Button text={"New Experiment"} icon={"add"} size={"small"} />
          <Button text={"Edit Experiment"} icon={"edit"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name) || experiments.length === 0} />
          <Button text={"Start Experiment"} icon={"play"} intent={"success"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name)} />
          <Button text={"Stop Experiment"} icon={"stop"} intent={"danger"} size={"small"} disabled={_.isUndefined(selectedExperiment?.name)} />
        </div>
      </Card>
    </div>
  )
};

const DeviceStatusPanel = (props: { devices: Device[] }) => {
  return (
    <div style={{ padding: "8px", width: "100%" }}>
      <Tabs id={"DeviceTabs"} animate>
        {props.devices.map((device) => {
          return (
            <Tab id={device.id} title={device.name} panel={<DeviceStatusTab device={device} experiments={EXAMPLE_EXPERIMENTS} />} />
          );
        })}
      </Tabs>
    </div>
  );
};

export default DeviceStatusPanel;
