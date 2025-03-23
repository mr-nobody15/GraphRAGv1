import React from "react";
import ReactDOM from "react-dom/client"; // ✅ Import 'createRoot'
import App from "./App";
import "./index.css";

const root = ReactDOM.createRoot(document.getElementById("root")); // ✅ Fix here
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
