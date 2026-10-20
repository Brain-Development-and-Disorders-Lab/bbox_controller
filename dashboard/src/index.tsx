// Blueprint styling
import "normalize.css/normalize.css";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@blueprintjs/icons/lib/css/blueprint-icons.css";
import "@blueprintjs/select/lib/css/blueprint-select.css";
import "@blueprintjs/table/lib/css/table.css";
import "./index.css";

// React imports
import React from "react";
import ReactDOM from "react-dom/client";

// Dashboard application
import App from "./App";

// Show the version in the window title
import { version } from "../package.json";
document.title = `Behavior Box Dashboard (v${version})`;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
