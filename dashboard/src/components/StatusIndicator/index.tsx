// Blueprint colors
import { Colors } from "@blueprintjs/core";

// Custom types
import { StatusIndicatorProps } from "../../../types";

const STATUS_COLORS = { good: Colors.GREEN3, neutral: Colors.ORANGE3, bad: Colors.RED3 };

// Blue when there is no status yet
const StatusIndicator = (props: StatusIndicatorProps) => {
  const color = props.status ? STATUS_COLORS[props.status] : Colors.BLUE3;

  return (
    <div style={{ width: "12px", height: "12px", borderRadius: "12px", backgroundColor: color }} />
  );
};

export default StatusIndicator;
