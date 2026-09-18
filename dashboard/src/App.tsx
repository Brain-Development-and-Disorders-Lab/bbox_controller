// React
import { useState } from "react";

// Custom components
import DeviceManager from "./components/DeviceManager";
import DeviceStatusPanel from "./components/DeviceStatusPanel";

// Custom types
import { Device } from "../types";
import { Colors } from "@blueprintjs/core";

const EXAMPLE_DEVICES: Device[] = [
  {
    id: "1",
    name: "Device 1",
    status: "disconnected",
    network: {
      ip: "localhost",
      port: 1111,
    },
    version: "1.0.0",
  },
  {
    id: "2",
    name: "Device 2",
    status: "disconnected",
    network: {
      ip: "localhost",
      port: 2222,
    },
    version: "1.0.0",
  },
];

const App = () => {
  const [devices,] = useState(EXAMPLE_DEVICES);
  
  return (
    <div style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "row" }}>
      {/* Left: Device manager */}
      <div style={{ width: "30%", height: "100%", background: Colors.LIGHT_GRAY3 }}>
        <DeviceManager devices={devices} />
      </div>

      {/* Right: Device state */}
      <div style={{ width: "70%", height: "100%" }}>
        <DeviceStatusPanel devices={devices} />
      </div>
    </div>
  );
};

export default App;
