// Blueprint colors
import { Colors } from "@blueprintjs/core";

// Custom types
import { StatusIndicatorProps } from "../../../types";

const StatusIndicator = (props: StatusIndicatorProps) => {
  // Set the indicator color
  let color = Colors.BLUE3;
  if (props.status === "good") color = Colors.GREEN3;
  if (props.status === "neutral") color = Colors.ORANGE3;
  if (props.status === "bad") color = Colors.RED3;

  return (
    <div style={{ width: "12px", height: "12px", borderRadius: "12px", backgroundColor: color }} />
  );
};

export default StatusIndicator;
