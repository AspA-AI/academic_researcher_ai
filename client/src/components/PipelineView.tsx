import React, { useState } from "react";
import { PipelineForm, PipelineFormValues } from "./PipelineForm";
import { ResponsePanel } from "./ResponsePanel";
import { startFullPipeline, startLitePipeline } from "../api/client";
import type { PipelineResponseEnvelope } from "../types/api";

export const PipelineView: React.FC = () => {
  const [activeMode, setActiveMode] = useState<"full" | "lite">("lite");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<PipelineResponseEnvelope | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(true);

  const handleSubmit = async (values: PipelineFormValues) => {
    setIsSubmitting(true);
    setError(null);
    setResponse(null);
    setShowForm(false); // Hide form when pipeline starts

    try {
      const payload = {
        // Core request fields coming from the user
        query: values.query,
        research_domain: values.research_domain,
        max_results: values.max_results,
        limit: values.max_results,
        // Quality threshold is treated as an internal/admin-level knob.
        // For now we send the default used by the backend (0.6).
        quality_threshold: 0.6,
        mode: values.mode,
        sources: values.sources,
        enrich: "standard", // Always use standard enrichment (admin-controlled)
        year_from: values.year_from,
        year_to: values.year_to,

        // Always persist extracted content in the vector store.
        store: true,

        // Reliability knobs are treated as admin-level config and not exposed in the UI.
        // For now we use sensible defaults wired into pipeline_config.
        pipeline_config: {
          auto_retry_failed_steps: true,
          enable_supervisor: values.enable_supervisor,
          max_retries: 3,
          save_intermediate_results: true
        }
      };

      const res =
        activeMode === "full"
          ? await startFullPipeline(payload)
          : await startLitePipeline(payload);

      setResponse(res);
      if (!res.success) {
        setError(res.error || "Pipeline request failed.");
      } else {
        setShowForm(false); // Hide form when response is successful
      }
    } catch (e: any) {
      setError(e?.message || "Unexpected error while calling the pipeline.");
    } finally {
      setIsSubmitting(false);
    }
  };

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
          <h2 className="sidebar-title">Pipeline mode</h2>
          <div className="mode-toggle" role="tablist">
            <button
              type="button"
              className={`mode-toggle-btn ${activeMode === "lite" ? "active" : ""}`}
              onClick={() => setActiveMode("lite")}
            >
              Lite pipeline
              <span className="mode-pill">Fast</span>
            </button>
            <button
              type="button"
              className={`mode-toggle-btn ${activeMode === "full" ? "active" : ""}`}
              onClick={() => setActiveMode("full")}
            >
              Full thematic pipeline
              <span className="mode-pill neutral">In-depth</span>
            </button>
          </div>
          <p className="sidebar-caption">
            Lite: retrieval → literature review → report.
            <br />
            Full: adds coding, themes, and refinement.
          </p>
        </div>

        <div className="sidebar-section">
          <h2 className="sidebar-title">Quality controls</h2>
          <ul className="sidebar-list">
            <li>Academic-topic validator</li>
            <li>Smart retrieval & evidence gates</li>
            <li>Optional supervisor agent (per-step QC)</li>
            <li>JSON-first report output</li>
          </ul>
        </div>
      </aside>

      <main className="main">
        <header className="main-header">
          <div>
            <h2>
              {response || isSubmitting ? "Pipeline Results" : "New academic inquiry"}
            </h2>
            <p className="subtitle">
              {response || isSubmitting
                ? "Review your report, choose export format, and download in your preferred format."
                : "Configure your research topic, sources, and quality options. The backend pipeline will run the selected mode end-to-end and return a structured JSON report."}
            </p>
          </div>
          {(response || isSubmitting) && (
            <button
              type="button"
              className="toggle-form-btn"
              onClick={() => setShowForm(!showForm)}
              title={showForm ? "Hide form" : "Show form"}
            >
              <span>{showForm ? "←" : "⚙️"}</span>
              <span>{showForm ? "Hide Form" : "Show Form"}</span>
            </button>
          )}
        </header>

        <section className={`content-grid ${!showForm && (response || isSubmitting) ? "form-hidden" : ""}`}>
          {showForm && (
            <div className="content-column form-column">
              <PipelineForm
                mode={activeMode}
                disabled={isSubmitting}
                onSubmit={handleSubmit}
              />
            </div>
          )}
          <div className={`content-column response-column ${!showForm && (response || isSubmitting) ? "full-width" : ""}`}>
            <ResponsePanel
              loading={isSubmitting}
              error={error}
              response={response}
            />
          </div>
        </section>
      </main>
    </>
  );
};

