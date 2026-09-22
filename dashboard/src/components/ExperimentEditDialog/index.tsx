// React
import { useEffect, useState } from "react";

// Blueprint components
import { Button, Card, Colors, Dialog, DialogBody, DialogFooter, Icon, NonIdealState, Tooltip, Tree, TreeNodeInfo } from "@blueprintjs/core";

// Custom types
import { Device, Experiment, ExperimentEditDialogProps } from "../../../types";

// Utility libraries
import _ from "lodash";

const EXAMPLE_TRIALS = [
  {
    leftContent: <Icon icon={"lab-test"} color={Colors.GRAY3} />,
    label: <div>Training: Stage 01</div>,
    rightContent: <Icon icon={"info-sign"} color={Colors.GRAY2} />,
    tooltip: "Training stage 01, requiring...",
  },
  {
    leftContent: <Icon icon={"stopwatch"} color={Colors.GRAY3} />,
    label: <div>Interval (2000ms)</div>,
    rightContent: <Icon icon={"info-sign"} color={Colors.GRAY2} />,
    tooltip: "Inter-trial interval",
  },
  {
    leftContent: <Icon icon={"lab-test"} color={Colors.GRAY3} />,
    label: <div>Training: Stage 02</div>,
    rightContent: <Icon icon={"info-sign"} color={Colors.GRAY2} />,
    tooltip: "Training stage 02, requiring...",
  }
];

const ExperimentEditDialog = (props: ExperimentEditDialogProps) => {
  // Determine if creating or editing an Experiment
  const isCreating = _.isUndefined(props.experiment);
  
  // Experiment state
  const [experimentID,] = useState(props.experiment?.id ?? "test_00");
  const [experimentName, setExperimentName] = useState(props.experiment?.name ?? "");
  const isValidExperiment = experimentName !== "";
  
  // Timeline state
  const [trials, setTrials] = useState(EXAMPLE_TRIALS);
  const [selectedTrialIndex, setSelectedTrialIndex] = useState(-1);
  
  // Synchronize the state
  useEffect(() => {
    if (props.experiment) {
      setExperimentName(props.experiment.name);
    }
  }, [props.experiment]);
  
  const handleSaveClick = () => {
    const experiment: Experiment = {
      id: experimentID,
      name: experimentName,
      trials: [],
    };
    props.onSave(experiment);

    setSelectedTrialIndex(-1);
    props.setIsOpen(false);
  };
  
  const handleTrialMoveUp = () => {
    if (selectedTrialIndex === 0) return;
    
    // Get all trials around that index
    const selectedTrial = _.cloneDeep(trials[selectedTrialIndex]);
    const priorTrials = trials.slice(0, selectedTrialIndex);
    const immediatePriorTrial = priorTrials.pop();
    const remainingTrials = selectedTrialIndex < trials.length - 1 ? trials.slice(selectedTrialIndex + 1) : [];
    
    // Rebuild the trial order and update state
    if (_.isUndefined(immediatePriorTrial)) return;
    const updatedTrials = [...priorTrials, selectedTrial, immediatePriorTrial, ...remainingTrials];
    setTrials([...updatedTrials]);
    setSelectedTrialIndex(selectedTrialIndex - 1);
  };
  
  const handleTrialMoveDown = () => {
    if (selectedTrialIndex === trials.length - 1) return;
    
    // Get all trials around that index
    const selectedTrial = _.cloneDeep(trials[selectedTrialIndex]);
    const priorTrials = trials.slice(0, selectedTrialIndex);
    const remainingTrials = trials.slice(selectedTrialIndex + 1);
    
    // Handle cases near the end of the experiment timeline
    let updatedTrials = [];
    if (remainingTrials.length === 1) {
      updatedTrials = [...priorTrials, ...remainingTrials, selectedTrial];
    } else {
      const immediateRemainingTrial = _.cloneDeep(remainingTrials[0]);
      const reducedRemainingTrials = remainingTrials.slice(1);
      updatedTrials = [...priorTrials, immediateRemainingTrial, selectedTrial, ...reducedRemainingTrials];
    }

    setTrials([...updatedTrials]);
    setSelectedTrialIndex(selectedTrialIndex + 1);
  };
  
  const handleTrialRemove = () => {
    if (selectedTrialIndex === 0) {
      setTrials([...trials.slice(1)]);
    } else if (selectedTrialIndex === trials.length - 1) {
      setTrials([...trials.slice(0, trials.length - 2)]);
    } else {
      setTrials([...trials.slice(0, selectedTrialIndex), ...trials.slice(selectedTrialIndex + 1)]);
    }
  };

  return (
    <Dialog title={`${isCreating ? "Create" : "Edit"} Experiment`} icon={isCreating ? "add" : "edit"} isOpen={props.isOpen} style={{ width: "680px" }}>
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Name</p>
          <input type={"text"} style={{ width: "520px" }} value={experimentName} placeholder={"Specify an Experiment name"} onChange={(event) => setExperimentName(event.target.value)} />
        </div>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "nowrap", alignItems: "stretch" }}>
          <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Timeline</p>
            <Card style={{ padding: "8px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
                {trials.length === 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px", width: "100%", alignItems: "center", justifyContent: "center" }}>
                    <Icon icon={"lab-test"} color={Colors.GRAY3} />
                    <p style={{ marginBottom: "0px" }}>No Trials</p>
                  </div>
                )}
                {trials.map((trial, index) => {
                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <div style={{
                        display: "flex",
                        flexDirection: "row",
                        gap: "8px",
                        padding: "4px",
                        width: "100%",
                        alignItems: "center",
                        justifyContent: "space-between",
                        backgroundColor: selectedTrialIndex === index ? Colors.LIGHT_GRAY1 : Colors.LIGHT_GRAY4,
                        borderRadius: "4px",
                        userSelect: "none",
                        cursor: "pointer",
                      }} onClick={() => setSelectedTrialIndex(index)}>
                        <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                          {trial.leftContent}
                          {trial.label}
                        </div>
                        <Tooltip content={trial.tooltip}>
                          {trial.rightContent}
                        </Tooltip>
                      </div>
                      {index < trials.length - 1 && (
                        <div style={{ display: "flex", width: "100%", justifyContent: "center" }}>
                          <Icon icon={"arrow-down"} color={Colors.GRAY3} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
              <Button icon={"caret-up"} size={"small"} text={"Up"} disabled={selectedTrialIndex < 0 || trials.length === 0} onClick={handleTrialMoveUp} />
              <Button icon={"caret-down"} size={"small"} text={"Down"} disabled={selectedTrialIndex < 0 || trials.length === 0} onClick={handleTrialMoveDown} />
              <Button intent={"danger"} icon={"remove"} size={"small"} text={"Remove"} disabled={selectedTrialIndex < 0 || trials.length === 0} onClick={handleTrialRemove} />
              <Button intent={"success"} icon={"add"} size={"small"} text={"Add"} />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%", height: "100%" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Parameters</p>
            <Card style={{ padding: "8px", height: "100%" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>ITI Minimum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={100} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>ITI Maximum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={1000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Response Limit</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={1000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Cue Minimum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={5000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Cue Maximum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={10000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Hold Minimum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={100} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Hold Maximum</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={1000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Valve Open</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={100} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
                  <p style={{ marginBottom: "0px" }}>Punishment Time</p>
                  <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                    <input type={"number"} style={{ width: "80px" }} value={1000} />
                    <p style={{ marginBottom: "0px" }}>ms</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} onClick={() => props.setIsOpen(false)} />
            <Button intent={"success"} icon={"tick-circle"} text={"Save"} disabled={!isValidExperiment} onClick={() => handleSaveClick()} />
          </div>
        }
      />
    </Dialog>
  );
};

export default ExperimentEditDialog;
