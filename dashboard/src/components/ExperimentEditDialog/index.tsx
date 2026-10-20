// React
import { useEffect, useState } from "react";

// Blueprint components
import { Button, Card, Checkbox, Dialog, DialogBody, DialogFooter, Menu, MenuDivider, MenuItem, PopoverNext } from "@blueprintjs/core";

// Custom components
import EmptyState from "../EmptyState";
import ErrorCallout from "../ErrorCallout";
import ExperimentParameterList from "../ExperimentParameterList";
import ExperimentTimeline from "../ExperimentTimeline";

// Custom types
import { Experiment, ExperimentEditDialogProps, ExperimentParameters, TimelineItem } from "../../../types";

// Experiment format
import {
  INTERVAL_DESCRIPTION,
  TRAINING_STAGES,
  createExperiment,
  createIntervalTrial,
  createTrainingTrial,
  experimentFileName,
  formatStage,
  serializeExperiment,
  timelineItemLabel,
  validateExperiment,
} from "../../lib/experiment";

// Menu entry showing a timeline component and its description
const ComponentMenuText = (props: { title: string; description: string }) => (
  <div>
    <div>{props.title}</div>
    <small className={"bp6-text-muted"}>{props.description}</small>
  </div>
);

const ExperimentEditDialog = (props: ExperimentEditDialogProps) => {
  const isCreating = props.loaded === undefined;

  // The experiment being edited and the selected timeline item
  const [draft, setDraft] = useState<Experiment>(() => createExperiment(""));
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const items = draft.timeline.items;
  const selectedItem: TimelineItem | undefined = items[selectedIndex];

  // Save state
  const [isSaving, setIsSaving] = useState(false);
  const [saveErrors, setSaveErrors] = useState<string[]>([]);

  // Start from the loaded experiment or a new one each time the dialog opens
  useEffect(() => {
    if (props.isOpen) {
      setDraft(props.loaded?.experiment ?? createExperiment(""));
      setSelectedIndex(-1);
      setSaveErrors([]);
    }
  }, [props.isOpen, props.loaded]);

  const setName = (name: string) => setDraft((current) => ({ ...current, metadata: { ...current.metadata, name } }));
  const setLoop = (loop: boolean) => setDraft((current) => ({ ...current, timeline: { ...current.timeline, loop } }));
  const setItems = (updated: TimelineItem[]) => setDraft((current) => ({ ...current, timeline: { ...current.timeline, items: updated } }));
  const setParameter = (key: keyof ExperimentParameters, value: number) => {
    setDraft((current) => ({ ...current, parameters: { ...current.parameters, [key]: value } }));
  };

  // Edits default to the file they were loaded from. Stays open if the save fails or is canceled.
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

  // Insert after the selected item
  const handleTrialAdd = (item: TimelineItem) => {
    const index = selectedIndex < 0 ? items.length : selectedIndex + 1;
    setItems([...items.slice(0, index), item, ...items.slice(index)]);
    setSelectedIndex(index);
  };

  const handleTrialChange = (changes: Partial<TimelineItem>) => {
    setItems(items.map((item, index) => (index === selectedIndex ? ({ ...item, ...changes } as TimelineItem) : item)));
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
        <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "nowrap", alignItems: "flex-start" }}>
          <div style={{ display: "flex", flexDirection: "column", flex: "1", minWidth: "0px", gap: "8px" }}>
            <div style={{ display: "flex", flexDirection: "row", gap: "8px", alignItems: "center", justifyContent: "space-between" }}>
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Experiment Timeline</p>
              <PopoverNext
                placement={"bottom-end"}
                content={
                  <Menu>
                    <MenuItem icon={"stopwatch"} multiline text={<ComponentMenuText title={"Interval"} description={INTERVAL_DESCRIPTION} />} onClick={() => handleTrialAdd(createIntervalTrial(items))} />
                    <MenuDivider title={"Training"} />
                    {TRAINING_STAGES.map(({ stage, description }) => (
                      <MenuItem key={stage} icon={"lab-test"} multiline text={<ComponentMenuText title={`Stage ${formatStage(stage)}`} description={description} />} onClick={() => handleTrialAdd(createTrainingTrial(stage, items))} />
                    ))}
                  </Menu>
                }
              >
                <Button intent={"success"} icon={"add"} size={"small"} text={"Add Trial"} />
              </PopoverNext>
            </div>
            <ExperimentTimeline items={items} selectedIndex={selectedIndex} onSelect={setSelectedIndex} />
            <Card style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px" }}>
              {selectedItem ? (
                <>
                  <div style={{ display: "flex", flexDirection: "row", gap: "8px", alignItems: "center", justifyContent: "space-between" }}>
                    <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Edit Trial {timelineItemLabel(selectedItem)}</p>
                    <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
                      <Button icon={"caret-up"} size={"small"} title={"Move up"} disabled={selectedIndex <= 0} onClick={() => handleTrialMove(-1)} />
                      <Button icon={"caret-down"} size={"small"} title={"Move down"} disabled={selectedIndex >= items.length - 1} onClick={() => handleTrialMove(1)} />
                      <Button intent={"danger"} icon={"trash"} size={"small"} title={"Remove"} onClick={handleTrialRemove} />
                    </div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <p style={{ marginBottom: "0px" }}>Description</p>
                    <textarea rows={2} style={{ resize: "vertical" }} value={selectedItem.description ?? ""} onChange={(event) => handleTrialChange({ description: event.target.value })} />
                  </div>
                  {selectedItem.type === "interval" && (
                    <div style={{ display: "flex", flexDirection: "row", gap: "8px", alignItems: "center", justifyContent: "space-between" }}>
                      <p style={{ marginBottom: "0px" }}>Duration</p>
                      <div style={{ display: "flex", flexDirection: "row", gap: "4px", alignItems: "center" }}>
                        {/* An empty input becomes `NaN`, which validation reports on save */}
                        <input type={"number"} min={0} style={{ width: "80px" }} value={Number.isNaN(selectedItem.duration_ms) ? "" : selectedItem.duration_ms} onChange={(event) => handleTrialChange({ duration_ms: parseInt(event.target.value) })} />
                        <p style={{ marginBottom: "0px" }}>ms</p>
                      </div>
                    </div>
                  )}
                  <div style={{ display: "flex", flexDirection: "row", gap: "8px", alignItems: "center", justifyContent: "space-between" }}>
                    <p style={{ marginBottom: "0px" }}>Repeat</p>
                    <div style={{ display: "flex", flexDirection: "row", gap: "4px", alignItems: "center" }}>
                      <input type={"number"} min={1} style={{ width: "80px" }} value={Number.isNaN(selectedItem.repeat) ? "" : selectedItem.repeat} onChange={(event) => handleTrialChange({ repeat: parseInt(event.target.value) })} />
                      <p style={{ marginBottom: "0px" }}>times</p>
                    </div>
                  </div>
                </>
              ) : items.length === 0 ? (
                <EmptyState icon={"add"} message={"Add Trials to Experiment Timeline"} />
              ) : (
                <EmptyState icon={"select"} message={"Select a Trial"} />
              )}
            </Card>
            <Checkbox style={{ marginBottom: "0px" }} label={"Loop Experiment Timeline"} checked={draft.timeline.loop} onChange={(event) => setLoop(event.currentTarget.checked)} />
          </div>

          {/* Overall Experiment parameters */}
          <div style={{ display: "flex", flexDirection: "column", flex: "0 0 auto", gap: "8px" }}>
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
