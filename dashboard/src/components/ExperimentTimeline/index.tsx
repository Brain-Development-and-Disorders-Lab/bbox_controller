// Blueprint components
import { Card, Colors, Icon, Tooltip } from "@blueprintjs/core";

// Custom types
import { ExperimentTimelineProps } from "../../../types";

// Experiment format
import { timelineItemDetails, timelineItemLabel } from "../../lib/experiment";

// Timeline items in run order, selectable when `onSelect` is given
const ExperimentTimeline = (props: ExperimentTimelineProps) => {
  const isSelectable = props.onSelect !== undefined;

  return (
    <Card style={{ padding: "8px", maxHeight: "360px", overflowY: "auto" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
        {props.items.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px", width: "100%", alignItems: "center", justifyContent: "center" }}>
            <Icon icon={"lab-test"} color={Colors.GRAY3} />
            <p style={{ marginBottom: "0px" }}>No Trials</p>
          </div>
        )}
        {props.items.map((item, index) => (
          <div key={item.id} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <div style={{
              display: "flex",
              flexDirection: "row",
              gap: "8px",
              padding: "4px",
              width: "100%",
              alignItems: "center",
              justifyContent: "space-between",
              backgroundColor: props.selectedIndex === index ? Colors.LIGHT_GRAY1 : Colors.LIGHT_GRAY4,
              borderRadius: "4px",
              userSelect: "none",
              cursor: isSelectable ? "pointer" : "default",
            }} onClick={() => props.onSelect?.(index)}>
              <div style={{ display: "flex", flexDirection: "row", gap: "8px" }}>
                <Icon icon={item.type === "interval" ? "stopwatch" : "lab-test"} color={Colors.GRAY3} />
                <div>{timelineItemLabel(item)}</div>
              </div>
              <Tooltip content={<div>{timelineItemDetails(item).map((line, lineIndex) => <div key={lineIndex}>{line}</div>)}</div>}>
                <Icon icon={"info-sign"} color={Colors.GRAY2} />
              </Tooltip>
            </div>
            {index < props.items.length - 1 && (
              <div style={{ display: "flex", width: "100%", justifyContent: "center" }}>
                <Icon icon={"arrow-down"} color={Colors.GRAY3} />
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default ExperimentTimeline;
