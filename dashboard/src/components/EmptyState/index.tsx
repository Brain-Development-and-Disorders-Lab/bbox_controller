// Blueprint components
import { Colors, Icon } from "@blueprintjs/core";

// Custom types
import { EmptyStateProps } from "../../../types";

// Shown in place of content that doesn't exist yet
const EmptyState = (props: EmptyStateProps) => (
  <div style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px", width: "100%", height: "100%", alignItems: "center", justifyContent: "center" }}>
    <Icon icon={props.icon} color={Colors.GRAY3} />
    <p style={{ marginBottom: "0px" }}>{props.message}</p>
  </div>
);

export default EmptyState;
