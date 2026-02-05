import React from "react";
import { AdminDashboard } from "./AdminDashboard";

export const AdminView: React.FC = () => {
  return (
    <>
      <aside className="sidebar">
        <div className="branding">
          <div className="logo-circle">AR</div>
          <div className="branding-text">
            <h1>AI Researcher Studio</h1>
            <p>Academic research assistant</p>
          </div>
        </div>

        <div className="sidebar-section">
          <h2 className="sidebar-title">Admin controls</h2>
          <ul className="sidebar-list">
            <li>Storage settings</li>
            <li>Reliability config</li>
            <li>Enrichment depth</li>
            <li>Quality thresholds</li>
            <li>Retrieval gates</li>
          </ul>
        </div>
      </aside>

      <main className="main">
        <AdminDashboard />
      </main>
    </>
  );
};

