// Blueprint core components
import { Card, Elevation } from "@blueprintjs/core";

// Custom components
import DeviceManager from "./components/DeviceManager";

const App = () => {
  return (
    <div style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "row" }}>
      {/* Left: Device manager */}
      <DeviceManager />

      {/* Right: Device state */}
      <Card elevation={Elevation.TWO} style={{ width: "70%", height: "100%" }}>
        <h3>Device Information</h3>
      </Card>
    </div>
  );
};

export default App;
