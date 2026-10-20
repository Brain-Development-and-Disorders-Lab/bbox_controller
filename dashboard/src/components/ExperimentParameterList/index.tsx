// Blueprint components
import { Card } from "@blueprintjs/core";

// Custom types
import { ExperimentParameterListProps, ExperimentParameters } from "../../../types";

// Experiment format
import { PARAMETER_LABELS } from "../../lib/experiment";

// Experiment-wide parameters, editable when `onChange` is given
const ExperimentParameterList = (props: ExperimentParameterListProps) => {
  return (
    <Card style={{ padding: "8px", height: "100%" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "4px", width: "100%" }}>
        {(Object.keys(PARAMETER_LABELS) as (keyof ExperimentParameters)[]).map((key) => (
          <div key={key} style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ marginBottom: "0px" }}>{PARAMETER_LABELS[key]}</p>
            {props.onChange ? (
              <div style={{ display: "flex", flexDirection: "row", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                {/* An empty input becomes `NaN`, which validation reports on save */}
                <input type={"number"} min={0} style={{ width: "80px" }} value={Number.isNaN(props.parameters[key]) ? "" : props.parameters[key]} onChange={(event) => props.onChange?.(key, parseInt(event.target.value))} />
                <p style={{ marginBottom: "0px" }}>ms</p>
              </div>
            ) : (
              <p style={{ marginBottom: "0px", fontWeight: "bold" }}>{props.parameters[key]} ms</p>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default ExperimentParameterList;
