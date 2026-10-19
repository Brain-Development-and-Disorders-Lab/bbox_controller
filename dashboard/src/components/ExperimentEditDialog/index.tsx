// React
import { useEffect, useState } from "react";

// Blueprint components
import { Button, Dialog, DialogBody, DialogFooter } from "@blueprintjs/core";

// Custom components
import ErrorCallout from "../ErrorCallout";
import ExperimentParameterList from "../ExperimentParameterList";
import ExperimentTimeline from "../ExperimentTimeline";

// Custom types
import { Experiment, ExperimentEditDialogProps, ExperimentParameters, TimelineItem } from "../../../types";

// Experiment format
import { createExperiment, experimentFileName, serializeExperiment, validateExperiment } from "../../lib/experiment";

const EXAMPLE_TRIALS: TimelineItem[] = [
  { id: "stage_1", type: "training", stage: 1, repeat: 1, description: "Training stage 01, requiring..." },
  { id: "interval_1", type: "interval", duration_ms: 2000, repeat: 1, description: "Inter-trial interval" },
  { id: "stage_2", type: "training", stage: 2, repeat: 1, description: "Training stage 02, requiring..." },
];

const ExperimentEditDialog = (props: ExperimentEditDialogProps) => {
  const isCreating = props.loaded === undefined;

  // The experiment being edited and the selected timeline item
  const [draft, setDraft] = useState<Experiment>(() => createExperiment("", EXAMPLE_TRIALS));
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const items = draft.timeline.items;

  // Save state
  const [isSaving, setIsSaving] = useState(false);
  const [saveErrors, setSaveErrors] = useState<string[]>([]);

  // Start from the loaded experiment or a new one each time the dialog opens
  useEffect(() => {
    if (props.isOpen) {
      setDraft(props.loaded?.experiment ?? createExperiment("", EXAMPLE_TRIALS));
      setSelectedIndex(-1);
      setSaveErrors([]);
    }
  }, [props.isOpen, props.loaded]);

  const setName = (name: string) => setDraft((current) => ({ ...current, metadata: { ...current.metadata, name } }));
  const setItems = (updated: TimelineItem[]) => setDraft((current) => ({ ...current, timeline: { ...current.timeline, items: updated } }));
  const setParameter = (key: keyof ExperimentParameters, value: number) => {
    setDraft((current) => ({ ...current, parameters: { ...current.parameters, [key]: value } }));
  };

  /**
   * Validate the experiment, then ask where to save it. Edits default to the file they were
   * loaded from. The dialog stays open if validation or saving fails, or the save is canceled.
   */
  const handleSaveClick = async () => {
    const result = validateExperiment(draft);
    if (!result.success) {
      setSaveErrors(result.errors);
      return;
    }

    setIsSaving(true);
    const defaultPath = props.loaded?.filePath ?? experimentFileName(result.experiment.metadata.name);
    const saved = await window.dashboardAPI.experimentSave(defaultPath, serializeExperiment(result.experiment));
    setIsSaving(false);

    if (saved.status === "error") {
      setSaveErrors([`Could not save file: ${saved.message}`]);
    } else if (saved.status === "saved") {
      props.onSave({ filePath: saved.filePath, experiment: result.experiment });
      props.onClose();
    }
  };

  // Swap the selected item with its neighbour, `offset` places away
  const handleTrialMove = (offset: number) => {
    const target = selectedIndex + offset;
    if (target < 0 || target >= items.length) return;

    const updated = [...items];
    [updated[selectedIndex], updated[target]] = [updated[target], updated[selectedIndex]];
    setItems(updated);
    setSelectedIndex(target);
  };

  const handleTrialRemove = () => {
    setItems(items.filter((_item, index) => index !== selectedIndex));
    setSelectedIndex(-1);
  };

  return (
    <Dialog title={`${isCreating ? "Create" : "Edit"} Experiment`} icon={isCreating ? "add" : "edit"} isOpen={props.isOpen} style={{ width: "680px" }}>
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Name</p>
          <input type={"text"} style={{ width: "520px" }} value={draft.metadata.name} placeholder={"Specify an Experiment name"} onChange={(event) => setName(event.target.value)} />
        </div>
        <ErrorCallout title={"Experiment not saved"} errors={saveErrors} />
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "nowrap", alignItems: "stretch" }}>
          <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Timeline</p>
            <ExperimentTimeline items={items} selectedIndex={selectedIndex} onSelect={setSelectedIndex} />
            <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
              <Button icon={"caret-up"} size={"small"} text={"Up"} disabled={selectedIndex <= 0} onClick={() => handleTrialMove(-1)} />
              <Button icon={"caret-down"} size={"small"} text={"Down"} disabled={selectedIndex < 0 || selectedIndex >= items.length - 1} onClick={() => handleTrialMove(1)} />
              <Button intent={"danger"} icon={"remove"} size={"small"} text={"Remove"} disabled={selectedIndex < 0} onClick={handleTrialRemove} />
              <Button intent={"success"} icon={"add"} size={"small"} text={"Add"} />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
            <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Parameters</p>
            <ExperimentParameterList parameters={draft.parameters} onChange={setParameter} />
          </div>
        </div>
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} disabled={isSaving} onClick={props.onClose} />
            <Button intent={"success"} icon={"floppy-disk"} text={"Save"} loading={isSaving} disabled={draft.metadata.name.trim() === ""} onClick={handleSaveClick} />
          </div>
        }
      />
    </Dialog>
  );
};

export default ExperimentEditDialog;
