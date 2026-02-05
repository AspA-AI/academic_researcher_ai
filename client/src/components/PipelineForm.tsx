import React, { useState } from "react";
import type { PipelineMode } from "../types/api";

export interface PipelineFormValues {
  query: string;
  research_domain: string;
  max_results: number;
  year_from?: number | null;
  year_to?: number | null;
  mode: PipelineMode;
  sources: string[];
  enrich: "standard" | "deep" | "none";
  enable_supervisor: boolean;
}

interface Props {
  mode: "full" | "lite";
  disabled?: boolean;
  onSubmit: (values: PipelineFormValues) => void | Promise<void>;
}

const DEFAULT_SOURCES = ["openalex", "europe_pmc", "arxiv", "core"];

export const PipelineForm: React.FC<Props> = ({ mode, disabled, onSubmit }) => {
  const [values, setValues] = useState<PipelineFormValues>({
    query: "",
    research_domain: "",
    max_results: 20,
    year_from: 2020,
    year_to: 2024,
    mode: "auto",
    sources: DEFAULT_SOURCES,
    enrich: "standard",
    enable_supervisor: false
  });

  const handleChange = (patch: Partial<PipelineFormValues>) => {
    setValues((prev) => ({ ...prev, ...patch }));
  };

  const handleToggleSource = (source: string) => {
    setValues((prev) => {
      const exists = prev.sources.includes(source);
      if (exists) {
        return { ...prev, sources: prev.sources.filter((s) => s !== source) };
      }
      return { ...prev, sources: [...prev.sources, source] };
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(values);
  };

  const isManualMode = values.mode === "manual";

  return (
    <form className="card form-card" onSubmit={handleSubmit}>
      <div className="card-header">
        <h3>Configure pipeline</h3>
        <p className="card-subtitle">
          Define the academic topic, retrieval scope, and quality controls. The backend will handle
          extraction, retrieval, validation, and report generation.
        </p>
      </div>

      <div className="form-section">
        <h4>1. Research question</h4>
        <div className="field-grid">
          <label className="field">
            <span className="field-label">Research query</span>
            <input
              type="text"
              className="field-input"
              placeholder="e.g. Blockchain governance transparency"
              value={values.query}
              onChange={(e) => handleChange({ query: e.target.value })}
              disabled={disabled}
              required
            />
            <span className="field-hint">
              Use an academic-style query (e.g. phenomenon + context + outcome).
            </span>
          </label>

          <label className="field">
            <span className="field-label">Research domain</span>
            <input
              type="text"
              className="field-input"
              placeholder="e.g. Blockchain Technology"
              value={values.research_domain}
              onChange={(e) => handleChange({ research_domain: e.target.value })}
              disabled={disabled}
              required
            />
            <span className="field-hint">
              High-level academic area used for retrieval scoping and prompts.
            </span>
          </label>
        </div>
      </div>

      <div className="form-section">
        <h4>2. Retrieval scope</h4>
        <div className="field-grid">
          <label className="field">
            <span className="field-label">Max results</span>
            <input
              type="number"
              className="field-input"
              min={5}
              max={50}
              value={values.max_results}
              onChange={(e) => handleChange({ max_results: Number(e.target.value) || 10 })}
              disabled={disabled}
            />
            <span className="field-hint">
              Target number of relevant papers to keep after quality gating.
            </span>
          </label>
        </div>

        <div className="field-grid">
          <label className="field">
            <span className="field-label">Year range (from)</span>
            <input
              type="number"
              className="field-input"
              value={values.year_from ?? ""}
              onChange={(e) =>
                handleChange({
                  year_from: e.target.value ? Number(e.target.value) : null
                })
              }
              disabled={disabled}
            />
          </label>

          <label className="field">
            <span className="field-label">Year range (to)</span>
            <input
              type="number"
              className="field-input"
              value={values.year_to ?? ""}
              onChange={(e) =>
                handleChange({
                  year_to: e.target.value ? Number(e.target.value) : null
                })
              }
              disabled={disabled}
            />
          </label>
        </div>

        <div className="field-grid">
          <div className="field">
            <span className="field-label">Source selection</span>
            <div className="segmented">
              <button
                type="button"
                className={`segmented-btn ${values.mode === "auto" ? "active" : ""}`}
                onClick={() => handleChange({ mode: "auto", sources: DEFAULT_SOURCES })}
                disabled={disabled}
              >
                Auto (recommended)
              </button>
              <button
                type="button"
                className={`segmented-btn ${values.mode === "manual" ? "active" : ""}`}
                onClick={() => handleChange({ mode: "manual" })}
                disabled={disabled}
              >
                Manual
              </button>
            </div>
            <span className="field-hint">
              Auto uses all supported academic sources. Manual lets you enable/disable each source.
            </span>
          </div>

          <div className="field">
            <span className="field-label">Sources</span>
            <div className={`pill-row ${!isManualMode ? "pill-row-disabled" : ""}`}>
              {DEFAULT_SOURCES.map((source) => {
                const active =
                  isManualMode && values.sources.includes(source.toLowerCase());
                return (
                  <button
                    key={source}
                    type="button"
                    className={`pill ${active ? "pill-active" : ""}`}
                    onClick={() => isManualMode && handleToggleSource(source)}
                    disabled={disabled || !isManualMode}
                  >
                    {source}
                  </button>
                );
              })}
            </div>
            <span className="field-hint">
              When Auto is selected, the backend may still adapt per-topic.
            </span>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h4>3. Supervisor</h4>
        <div className="toggle-row">
          <label className="toggle">
            <input
              type="checkbox"
              checked={values.enable_supervisor}
              onChange={(e) => handleChange({ enable_supervisor: e.target.checked })}
              disabled={disabled}
            />
            <span className="toggle-indicator" />
            <span className="toggle-label">
              Enable supervisor agent for step-by-step quality control
            </span>
          </label>
          <p className="field-hint">
            Adds a supervising LLM between agents (retrieval, review, coding, themes, report) to
            approve, request revisions, or halt when quality is too low.
          </p>
        </div>
      </div>

      <div className="form-footer">
        <div className="form-footer-text">
          <span className="badge">
            {mode === "lite" ? "Lite pipeline: retrieval + review + report" : "Full pipeline: end-to-end thematic analysis"}
          </span>
          <p className="form-footer-caption">
            The backend will always return a JSON-first report. PDFs/PowerPoint exports can be layered
            on top of this contract later.
          </p>
        </div>
        <button
          type="submit"
          className="primary-btn"
          disabled={disabled}
        >
          {disabled ? "Running pipeline..." : "Run pipeline"}
        </button>
      </div>
    </form>
  );
};


