// Blueprint components
import { Button, Colors, Dialog, DialogBody, DialogFooter } from "@blueprintjs/core";

// Custom components
import ErrorCallout from "../ErrorCallout";
import ProtocolParameterList from "../ProtocolParameterList";
import ProtocolTimeline from "../ProtocolTimeline";

// Custom types
import { ProtocolLoadDialogProps } from "../../../types";

// Protocol format
import { fileNameFromPath } from "../../lib/protocol";

const formatDate = (timestamp: string) => new Date(timestamp).toLocaleString();

// Read-only review of a protocol file, shown before it is loaded onto a device
const ProtocolLoadDialog = (props: ProtocolLoadDialogProps) => {
  const result = props.file?.result;
  const protocol = result?.success ? result.protocol : undefined;

  const handleConfirmClick = () => {
    if (props.file && protocol) {
      props.onConfirm({ filePath: props.file.filePath, protocol });
    }
  };

  return (
    <Dialog title={"Load Task Protocol"} icon={"import"} isOpen={props.isOpen} onClose={props.onClose} style={{ width: "680px" }}>
      <DialogBody style={{ display: "flex", flexDirection: "column", gap: "8px", padding: "8px" }}>
        <div style={{ display: "flex", flexDirection: "row", gap: "4px", alignItems: "end" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold" }}>File:</p>
          <p style={{ marginBottom: "0px", fontSize: "12px", fontFamily: "monospace" }} title={props.file?.filePath}>{props.file && fileNameFromPath(props.file.filePath)}</p>
        </div>

        {result && !result.success && (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <p style={{ marginBottom: "0px" }}>Select a different Protocol or resolve the following issues before continuing.</p>
            <ErrorCallout title={"Protocol file contains errors"} errors={result.errors} />
          </div>
        )}

        {protocol && (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <div style={{ display: "flex", flexDirection: "row", gap: "4px" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Protocol Name:</p>
                <p style={{ marginBottom: "0px" }}>{protocol.metadata.name}</p>
              </div>
              {protocol.metadata.description !== "" && (
                <p style={{ marginBottom: "0px", color: Colors.GRAY1 }}>{protocol.metadata.description}</p>
              )}
              <p style={{ marginBottom: "0px", fontSize: "12px", color: Colors.GRAY2 }}>
                {protocol.metadata.author !== "" && `${protocol.metadata.author} · `}
                Created {formatDate(protocol.metadata.created_at)} · Modified {formatDate(protocol.metadata.modified_at)}
                {protocol.metadata.dashboard_version && ` · Dashboard v${protocol.metadata.dashboard_version}`}
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "nowrap", alignItems: "stretch" }}>
              <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Protocol Timeline{protocol.timeline.loop && " (Looping)"}</p>
                <ProtocolTimeline items={protocol.timeline.items} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", flex: "1", gap: "8px", width: "50%" }}>
                <p style={{ marginBottom: "0px", fontWeight: "bold" }}>Protocol Parameters</p>
                <ProtocolParameterList parameters={protocol.parameters} />
              </div>
            </div>
          </>
        )}
      </DialogBody>
      <DialogFooter
        actions={
          <div>
            <Button intent={"danger"} icon={"cross-circle"} text={"Cancel"} onClick={props.onClose} />
            <Button intent={"success"} icon={"tick-circle"} text={"Confirm"} disabled={!protocol} onClick={handleConfirmClick} />
          </div>
        }
      />
    </Dialog>
  );
};

export default ProtocolLoadDialog;
