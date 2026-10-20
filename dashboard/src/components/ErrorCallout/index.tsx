// Blueprint components
import { Callout } from "@blueprintjs/core";

// Custom types
import { ErrorCalloutProps } from "../../../types";

// List of problems, shown only when there are any
const ErrorCallout = (props: ErrorCalloutProps) => {
  if (props.errors.length === 0) return null;

  return (
    <Callout intent={"danger"} icon={"error"} title={props.title}>
      <ul style={{ margin: "0px", paddingLeft: "16px" }}>
        {props.errors.map((error, index) => <li key={index}>{error}</li>)}
      </ul>
    </Callout>
  );
};

export default ErrorCallout;
