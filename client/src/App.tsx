import React from "react";
import { Routes, Route } from "react-router-dom";
import { PipelineView } from "./components/PipelineView";
import { AdminView } from "./components/AdminView";

const App: React.FC = () => {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<PipelineView />} />
        <Route path="/admin" element={<AdminView />} />
      </Routes>
    </div>
  );
};

export default App;


