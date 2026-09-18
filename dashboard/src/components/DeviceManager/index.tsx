import { Button } from "@blueprintjs/core";
import { Cell, Column, Table } from "@blueprintjs/table";
import { useEffect, useRef, useState } from "react";

const DeviceManager = () => {  
  const containerRef = useRef<HTMLDivElement>(null);
  const [columnWidths, setColumnWidths] = useState<number[]>([180, 180]);

  useEffect(() => {
    if (!containerRef.current) return;
    
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const containerWidth = entry.contentRect.width;
        const totalFixedWidth = columnWidths.slice(0, -1).reduce((a, b) => a + b, 0);
        const remainingSpace = containerWidth - totalFixedWidth - 16; 

        setColumnWidths((prevWidths) => {
          const nextWidths = [...prevWidths];
          nextWidths[nextWidths.length - 1] = Math.max(remainingSpace, 100);
          return nextWidths;
        });
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [columnWidths]);
  
  const nameCellRenderer = (rowIndex: number) => {
    return (
      <Cell>
        <div style={{ height: "48px", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ marginBottom: "0px", fontWeight: "bold", width: "auto" }}>Device {rowIndex + 1}</p>
          <Button size={"small"} intent={"none"} text={"Edit"} />
        </div>
      </Cell>
    );
  };

  const statusCellRenderer = (rowIndex: number) => {
    return (
      <Cell style={{ height: "100%", width: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap", gap: "2px", alignItems: "center", justifyContent: "space-between"}}>
        <p style={{ marginBottom: "0px", fontWeight: "bold", color: "red" }}>Disconnected</p>
      </Cell>
    );
  };
  
  return (
    <div style={{ padding: "10px", minWidth: "30%", height: "100%", display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", flexDirection: "row", gap: "8px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
        <p style={{ marginBottom: "0px", fontWeight: "bold", fontSize: "16px" }}>Devices</p>
        <Button size={"small"} intent={"primary"} text={"Add Device"} />
      </div>

      {/* Devices table */}
      <div style={{ maxHeight: "240px" }} ref={containerRef}>
        <p>Showing 10 devices:</p>
        <Table numRows={10} enableRowHeader={false} enableRowResizing={false} enableColumnResizing={false} enableMultipleSelection={false} defaultRowHeight={48} defaultColumnWidth={180} columnWidths={columnWidths}>
          <Column cellRenderer={nameCellRenderer} name={"Name"} />
          <Column cellRenderer={statusCellRenderer} name={"Status"} />
        </Table>
      </div>
      
      {/* Device information */}
      <div style={{ display: "flex" }}>
        <p>Device Information</p>
      </div>
    </div>
  );
};

export default DeviceManager;
