import React, { useState } from "react";

interface AdminSettings {
  // Storage settings
  store: boolean;
  
  // Reliability settings
  auto_retry_failed_steps: boolean;
  max_retries: number;
  save_intermediate_results: boolean;
  
  // Enrichment settings
  enrich: "standard" | "deep" | "none";
  
  // Quality thresholds (per agent type)
  quality_thresholds: {
    literature_review: { min_score: number; halt_threshold: number };
    initial_coding: { min_score: number; halt_threshold: number };
    thematic_grouping: { min_score: number; halt_threshold: number };
    theme_refinement: { min_score: number; halt_threshold: number };
    report_generation: { min_score: number; halt_threshold: number };
  };
  
  // Retrieval quality thresholds
  retrieval_thresholds: {
    min_quantity_ratio: number;
    min_certainty_score: number;
    min_recent_ratio: number;
    max_years_old: number;
  };
}

const DEFAULT_SETTINGS: AdminSettings = {
  store: true,
  auto_retry_failed_steps: true,
  max_retries: 3,
  save_intermediate_results: true,
  enrich: "standard",
  quality_thresholds: {
    literature_review: { min_score: 0.6, halt_threshold: 0.3 },
    initial_coding: { min_score: 0.6, halt_threshold: 0.3 },
    thematic_grouping: { min_score: 0.6, halt_threshold: 0.3 },
    theme_refinement: { min_score: 0.6, halt_threshold: 0.3 },
    report_generation: { min_score: 0.7, halt_threshold: 0.4 },
  },
  retrieval_thresholds: {
    min_quantity_ratio: 0.3,
    min_certainty_score: 0.7,
    min_recent_ratio: 0.2,
    max_years_old: 2,
  },
};

export const AdminDashboard: React.FC = () => {
  const [settings, setSettings] = useState<AdminSettings>(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const handleChange = (path: string, value: any) => {
    setSettings((prev) => {
      const keys = path.split(".");
      const newSettings = { ...prev };
      let current: any = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
    setHasChanges(true);
    setSaveStatus("idle");
  };

  const handleSave = async () => {
    setSaveStatus("saving");
    // TODO: Integrate with backend API when ready
    setTimeout(() => {
      setSaveStatus("saved");
      setHasChanges(false);
      setTimeout(() => setSaveStatus("idle"), 2000);
    }, 500);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    setHasChanges(false);
    setSaveStatus("idle");
  };

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <div>
          <h2>Admin Settings</h2>
          <p className="subtitle">
            Configure system-wide settings for storage, reliability, enrichment, and quality thresholds.
            These settings apply to all pipeline runs.
          </p>
        </div>
        <div className="admin-actions">
          <button
            type="button"
            className="secondary-btn"
            onClick={handleReset}
            disabled={!hasChanges}
          >
            Reset to defaults
          </button>
          <button
            type="button"
            className="primary-btn"
            onClick={handleSave}
            disabled={!hasChanges || saveStatus === "saving"}
          >
            {saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved ✓" : "Save changes"}
          </button>
        </div>
      </header>

      <div className="admin-content">
        {/* Storage Settings */}
        <section className="admin-section card">
          <div className="card-header">
            <h3>Storage Settings</h3>
            <p className="card-subtitle">
              Control whether extracted papers and chunks are persisted in the vector store (Weaviate).
            </p>
          </div>
          <div className="form-section">
            <div className="toggle-row">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.store}
                  onChange={(e) => handleChange("store", e.target.checked)}
                />
                <span className="toggle-indicator" />
                <span className="toggle-label">
                  Persist extracted papers & chunks in vector store
                </span>
              </label>
              <p className="field-hint">
                When enabled, all extracted content is stored in Weaviate for future retrieval.
                Disabling this will prevent storage but extraction will still run.
              </p>
            </div>
          </div>
        </section>

        {/* Reliability Settings */}
        <section className="admin-section card">
          <div className="card-header">
            <h3>Reliability Settings</h3>
            <p className="card-subtitle">
              Configure automatic retry behavior and intermediate result storage for pipeline steps.
            </p>
          </div>
          <div className="form-section">
            <div className="toggle-row">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.auto_retry_failed_steps}
                  onChange={(e) => handleChange("auto_retry_failed_steps", e.target.checked)}
                />
                <span className="toggle-indicator" />
                <span className="toggle-label">
                  Auto-retry failed steps
                </span>
              </label>
              <p className="field-hint">
                Automatically retry transient failures (e.g., network issues, API rate limits) during pipeline execution.
              </p>
            </div>

            <div className="field-grid">
              <label className="field">
                <span className="field-label">Max retries per step</span>
                <input
                  type="number"
                  min={0}
                  max={10}
                  className="field-input"
                  value={settings.max_retries}
                  onChange={(e) => handleChange("max_retries", Number(e.target.value) || 0)}
                  disabled={!settings.auto_retry_failed_steps}
                />
                <span className="field-hint">
                  Maximum number of automatic retry attempts for each failed step.
                </span>
              </label>
            </div>

            <div className="toggle-row">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.save_intermediate_results}
                  onChange={(e) => handleChange("save_intermediate_results", e.target.checked)}
                />
                <span className="toggle-indicator" />
                <span className="toggle-label">
                  Save intermediate agent outputs
                </span>
              </label>
              <p className="field-hint">
                Store each agent&apos;s JSON output (retrieval, review, coding, themes) for audit and debugging.
              </p>
            </div>
          </div>
        </section>

        {/* Enrichment Settings */}
        <section className="admin-section card">
          <div className="card-header">
            <h3>Enrichment Settings</h3>
            <p className="card-subtitle">
              Control which external enrichment services are used to enhance discovered papers.
            </p>
          </div>
          <div className="form-section">
            <label className="field">
              <span className="field-label">Enrichment depth</span>
              <div className="segmented">
                <button
                  type="button"
                  className={`segmented-btn ${settings.enrich === "standard" ? "active" : ""}`}
                  onClick={() => handleChange("enrich", "standard")}
                >
                  Standard
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${settings.enrich === "deep" ? "active" : ""}`}
                  onClick={() => handleChange("enrich", "deep")}
                >
                  Deep
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${settings.enrich === "none" ? "active" : ""}`}
                  onClick={() => handleChange("enrich", "none")}
                >
                  None
                </button>
              </div>
              <span className="field-hint">
                <strong>Standard:</strong> Crossref (publisher/journal) + Unpaywall (PDF URLs, OA status).
                <br />
                <strong>Deep:</strong> Adds Semantic Scholar (citation counts, fields of study).
                <br />
                <strong>None:</strong> No enrichment; papers come as-is from discovery sources.
              </span>
            </label>
          </div>
        </section>

        {/* Quality Thresholds */}
        <section className="admin-section card">
          <div className="card-header">
            <h3>Quality Thresholds</h3>
            <p className="card-subtitle">
              Configure minimum quality scores and halt thresholds for each agent type.
              Scores are normalized to 0.0–1.0.
            </p>
          </div>
          <div className="form-section">
            {Object.entries(settings.quality_thresholds).map(([agentType, thresholds]) => (
              <div key={agentType} className="threshold-group">
                <h4 className="threshold-title">
                  {agentType.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                </h4>
                <div className="field-grid">
                  <label className="field">
                    <span className="field-label">Min score (approve)</span>
                    <input
                      type="number"
                      step={0.05}
                      min={0}
                      max={1}
                      className="field-input"
                      value={thresholds.min_score}
                      onChange={(e) =>
                        handleChange(`quality_thresholds.${agentType}.min_score`, Number(e.target.value) || 0)
                      }
                    />
                    <span className="field-hint">
                      Minimum quality score to approve agent output and proceed.
                    </span>
                  </label>
                  <label className="field">
                    <span className="field-label">Halt threshold</span>
                    <input
                      type="number"
                      step={0.05}
                      min={0}
                      max={1}
                      className="field-input"
                      value={thresholds.halt_threshold}
                      onChange={(e) =>
                        handleChange(`quality_thresholds.${agentType}.halt_threshold`, Number(e.target.value) || 0)
                      }
                    />
                    <span className="field-hint">
                      Quality score below which the pipeline halts (too low to proceed).
                    </span>
                  </label>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Retrieval Quality Thresholds */}
        <section className="admin-section card">
          <div className="card-header">
            <h3>Retrieval Quality Thresholds</h3>
            <p className="card-subtitle">
              Configure evidence sufficiency gates for document retrieval.
            </p>
          </div>
          <div className="form-section">
            <div className="field-grid">
              <label className="field">
                <span className="field-label">Min quantity ratio</span>
                <input
                  type="number"
                  step={0.05}
                  min={0}
                  max={1}
                  className="field-input"
                  value={settings.retrieval_thresholds.min_quantity_ratio}
                  onChange={(e) =>
                    handleChange("retrieval_thresholds.min_quantity_ratio", Number(e.target.value) || 0)
                  }
                />
                <span className="field-hint">
                  Minimum percentage of requested results (e.g., 0.3 = 30% of requested).
                </span>
              </label>
              <label className="field">
                <span className="field-label">Min certainty score</span>
                <input
                  type="number"
                  step={0.05}
                  min={0}
                  max={1}
                  className="field-input"
                  value={settings.retrieval_thresholds.min_certainty_score}
                  onChange={(e) =>
                    handleChange("retrieval_thresholds.min_certainty_score", Number(e.target.value) || 0)
                  }
                />
                <span className="field-hint">
                  Minimum certainty score from vector store similarity search.
                </span>
              </label>
            </div>
            <div className="field-grid">
              <label className="field">
                <span className="field-label">Min recent ratio</span>
                <input
                  type="number"
                  step={0.05}
                  min={0}
                  max={1}
                  className="field-input"
                  value={settings.retrieval_thresholds.min_recent_ratio}
                  onChange={(e) =>
                    handleChange("retrieval_thresholds.min_recent_ratio", Number(e.target.value) || 0)
                  }
                />
                <span className="field-hint">
                  Minimum percentage of recent documents (within max_years_old).
                </span>
              </label>
              <label className="field">
                <span className="field-label">Max years old (for "recent")</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  className="field-input"
                  value={settings.retrieval_thresholds.max_years_old}
                  onChange={(e) =>
                    handleChange("retrieval_thresholds.max_years_old", Number(e.target.value) || 1)
                  }
                />
                <span className="field-hint">
                  Documents published within this many years are considered "recent".
                </span>
              </label>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

