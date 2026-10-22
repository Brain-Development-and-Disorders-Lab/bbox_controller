// Blueprint components
import { Card, Colors, Icon, Tooltip } from "@blueprintjs/core";

// Custom components
import EmptyState from "../EmptyState";

// Custom types
import { ProtocolTimelineProps } from "../../../types";

// Protocol format
import { timelineItemDetails, timelineItemLabel } from "../../lib/protocol";

// Timeline items in run order, selectable when `onSelect` is given
const ProtocolTimeline = (props: ProtocolTimelineProps) => {
  const isSelectable = props.onSelect !== undefined;

  return (
    <Card style={{ padding: "8px", maxHeight: "360px", overflowY: "auto" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
        {props.items.length === 0 && <EmptyState icon={"lab-test"} message={"No Trials"} />}
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
              backgroundColor: props.selectedIndex === index ? "rgba(45, 114, 210, 0.1)" : Colors.LIGHT_GRAY4,
              boxShadow: props.selectedIndex === index ? `inset 3px 0 0 ${Colors.BLUE3}` : "none",
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

export default ProtocolTimeline;
