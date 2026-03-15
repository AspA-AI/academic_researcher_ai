import React, { useState } from "react";
import type { PipelineResponseEnvelope } from "../types/api";
import { ReportExportPanel } from "./ReportExportPanel";
import { extractCanonicalReport } from "../utils/report";

interface Props {
  loading: boolean;
  error: string | null;
  response: PipelineResponseEnvelope | null;
}

type TabType = "preview" | "json" | "export";

export const ResponsePanel: React.FC<Props> = ({ loading, error, response }) => {
  const [activeTab, setActiveTab] = useState<TabType>("preview");
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied">("idle");
  const [isJsonExpanded, setIsJsonExpanded] = useState(false);
  const [isRawJsonVisible, setIsRawJsonVisible] = useState(true);
  const status = response?.raw?.status ?? response?.status;
  const result = response?.raw?.result ?? response?.raw?.res ?? response?.raw;
  const jsonString = JSON.stringify(result ?? response?.raw, null, 2);
  const canonicalReport = extractCanonicalReport(response);
  // const canonicalReport = response?.raw?.result?.data?.report;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopyStatus("copied");
      setTimeout(() => setCopyStatus("idle"), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pipeline-result-${response?.pipeline_id || Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card response-card">
      <div className="card-header">
        <h3>Pipeline outcome</h3>
        <p className="card-subtitle">
          Live view of the last run. Inspect high-level status and dive into the JSON report payload
          returned by the backend.
        </p>
      </div>

      <div className="response-body">
        {loading && (
          <div className="response-state">
            <div className="spinner" aria-hidden="true" />
            <div>
              <p className="response-title">Pipeline is running…</p>
              <p className="response-caption">
                This may involve extraction, vector store retrieval, validation, and multi-agent
                reasoning. You can continue working while it completes.
              </p>
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="response-state error">
            <p className="response-title">Request failed</p>
            <p className="response-caption">{error}</p>
          </div>
        )}

        {!loading && !error && !response && (
          <div className="response-state">
            <p className="response-title">No run yet</p>
            <p className="response-caption">
              Configure a topic on the left and start a pipeline to see structured results here.
            </p>
          </div>
        )}

        {!loading && response && (
          <>
            <div className="status-summary">
              <div className="status-chip-row">
                <span
                  className={`status-chip ${
                    response.success ? "status-chip-success" : "status-chip-failure"
                  }`}
                >
                  {response.success ? "Success" : "Failed"}
                </span>
                {status && <span className="status-chip subtle">Status: {String(status)}</span>}
                {response?.pipeline_id && (
                  <span className="status-chip subtle">Pipeline ID: {response?.pipeline_id}</span>
                )}
              </div>
              {response.raw?.data?.query && (
                <div className="status-meta">
                  <div>
                    <span className="meta-label">Query</span>
                    <span className="meta-value">{response?.raw?.data?.query}</span>
                  </div>
                  <div>
                    <span className="meta-label">Research domain</span>
                    <span className="meta-value">{response?.raw?.data?.research_domain}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Raw JSON Section - Always Visible */}
            <div className="raw-json-section">
              <div className="raw-json-header">
                <div>
                  <h4>Raw JSON Response</h4>
                  <p className="raw-json-caption">
                    Complete pipeline response payload from the backend
                  </p>
                </div>
                <div className="raw-json-controls">
                  <button
                    type="button"
                    className="icon-btn small"
                    onClick={() => setIsRawJsonVisible(!isRawJsonVisible)}
                    title={isRawJsonVisible ? "Collapse" : "Expand"}
                  >
                    <span className="icon-btn-icon">{isRawJsonVisible ? "⬆️" : "⬇️"}</span>
                    <span>{isRawJsonVisible ? "Hide" : "Show"}</span>
                  </button>
                  <button
                    type="button"
                    className="icon-btn small"
                    onClick={handleCopy}
                    title="Copy to clipboard"
                  >
                    <span className="icon-btn-icon">{copyStatus === "copied" ? "✓" : "📋"}</span>
                    <span>{copyStatus === "copied" ? "Copied!" : "Copy"}</span>
                  </button>
                  <button
                    type="button"
                    className="icon-btn small"
                    onClick={handleDownload}
                    title="Download as JSON file"
                  >
                    <span className="icon-btn-icon">⬇️</span>
                    <span>Download</span>
                  </button>
                </div>
              </div>
              {isRawJsonVisible && (
                <div className="raw-json-content">
                  <pre className={`json-viewer ${isJsonExpanded ? "expanded" : ""}`}>
                    {jsonString}
                  </pre>
                  <button
                    type="button"
                    className="expand-json-btn"
                    onClick={() => setIsJsonExpanded(!isJsonExpanded)}
                  >
                    {isJsonExpanded ? "⬆️ Collapse" : "⬇️ Expand Full Height"}
                  </button>
                </div>
              )}
            </div>

            {/* Tab Navigation */}
            <div className="response-tabs">
              <button
                type="button"
                className={`response-tab ${activeTab === "preview" ? "active" : ""}`}
                onClick={() => setActiveTab("preview")}
              >
                <span className="tab-icon">👁️</span>
                <span>Preview</span>
              </button>
              <button
                type="button"
                className={`response-tab ${activeTab === "json" ? "active" : ""}`}
                onClick={() => setActiveTab("json")}
              >
                <span className="tab-icon">📄</span>
                <span>JSON Output</span>
              </button>
              <button
                type="button"
                className={`response-tab ${activeTab === "export" ? "active" : ""}`}
                onClick={() => setActiveTab("export")}
              >
                <span className="tab-icon">📥</span>
                <span>Export</span>
              </button>
            </div>

            {/* Tab Content */}
            <div className="tab-content-wrapper">
              {/* {activeTab === "preview" && ( */}
                <div className="tab-content preview-content">
                  <ReportExportPanel pipelineId={response?.pipeline_id} report={canonicalReport} />
                </div>
              {/* )} */}

              {activeTab === "json" && (
                <div className="tab-content json-content">
                  <div className="json-section-expanded">
                    <div className="json-header">
                      <div>
                        <h4>Raw JSON Output</h4>
                        <p className="json-caption">
                          This is the exact payload returned by the backend. It is the contract for any
                          future PDF/PowerPoint/HTML renderers.
                        </p>
                      </div>
                      <div className="json-actions">
                        <button
                          type="button"
                          className="icon-btn"
                          onClick={handleCopy}
                          title="Copy to clipboard"
                        >
                          <span className="icon-btn-icon">{copyStatus === "copied" ? "✓" : "📋"}</span>
                          <span>{copyStatus === "copied" ? "Copied!" : "Copy"}</span>
                        </button>
                        <button
                          type="button"
                          className="icon-btn"
                          onClick={handleDownload}
                          title="Download as JSON file"
                        >
                          <span className="icon-btn-icon">⬇️</span>
                          <span>Download</span>
                        </button>
                        <button
                          type="button"
                          className="icon-btn"
                          onClick={() => setIsJsonExpanded(!isJsonExpanded)}
                          title={isJsonExpanded ? "Collapse" : "Expand"}
                        >
                          <span className="icon-btn-icon">{isJsonExpanded ? "⬆️" : "⬇️"}</span>
                          <span>{isJsonExpanded ? "Collapse" : "Expand"}</span>
                        </button>
                      </div>
                    </div>
                    <pre className={`json-viewer ${isJsonExpanded ? "expanded" : ""}`}>
                      {jsonString}
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === "export" && (
                <div className="tab-content export-content">
                  <ReportExportPanel pipelineId={response.pipeline_id} report={canonicalReport} />
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};


