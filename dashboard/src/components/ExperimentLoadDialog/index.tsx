// Blueprint components
import { Button, Colors, Dialog, DialogBody, DialogFooter } from "@blueprintjs/core";

// Custom components
import ErrorCallout from "../ErrorCallout";
import ExperimentParameterList from "../ExperimentParameterList";
import ExperimentTimeline from "../ExperimentTimeline";

// Custom types
import { ExperimentLoadDialogProps } from "../../../types";

// Experiment format
import { fileNameFromPath } from "../../lib/experiment";

const formatDate = (timestamp: string) => new Date(timestamp).toLocaleString();

// Read-only review of an experiment file, shown before it is loaded onto a device
const ExperimentLoadDialog = (props: ExperimentLoadDialogProps) => {
  const result = props.file?.result;
  const experiment = result?.success ? result.experiment : undefined;

  const handleConfirmClick = () => {
    if (props.file && experiment) {
      props.onConfirm({ filePath: props.file.filePath, experiment });
    }
  };

  return (
    <Dialog title={"Load Experiment"} icon={"import"} isOpen={props.isOpen} onClose={props.onClose} style={{ width: "680px" }}>
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", alignItems: "center" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold" }}>File:</p>
          <p style={{ marginBottom: "0px", fontFamily: "monospace" }} title={props.file?.filePath}>{props.file && fileNameFromPath(props.file.filePath)}</p>
        </div>

        {result && !result.success && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <p style={{ marginBottom: "0px" }}>Select a different Experiment or resolve the following issues before continuing.</p>
            <ErrorCallout title={"Experiment file contains errors"} errors={result.errors} />
          </div>
        )}

        {experiment && (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Name</p>
                <p style={{ marginBottom: "0px" }}>{experiment.metadata.name}</p>
              </div>
              {experiment.metadata.description !== "" && (
                <p style={{ marginBottom: "0px", color: Colors.GRAY1 }}>{experiment.metadata.description}</p>
              )}
              <p style={{ marginBottom: "0px", fontSize: "12px", color: Colors.GRAY2 }}>
                {experiment.metadata.author !== "" && `${experiment.metadata.author} · `}
                Created {formatDate(experiment.metadata.created_at)} · Modified {formatDate(experiment.metadata.modified_at)}
                {experiment.metadata.dashboard_version && ` · Dashboard v${experiment.metadata.dashboard_version}`}
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "nowrap", alignItems: "stretch" }}>
              <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Timeline{experiment.timeline.loop && " (Looping)"}</p>
                <ExperimentTimeline items={experiment.timeline.items} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Parameters</p>
                <ExperimentParameterList parameters={experiment.parameters} />
              </div>
            </div>
          </>
        )}
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} onClick={props.onClose} />
            <Button intent={"success"} icon={"tick-circle"} text={"Confirm"} disabled={!experiment} onClick={handleConfirmClick} />
          </div>
        }
      />
    </Dialog>
  );
};

export default ExperimentLoadDialog;
