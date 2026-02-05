import React from "react";
import type { CanonicalReport } from "../utils/report";
import type { ReportFormat } from "../config/reportTemplates";

interface Props {
  report: CanonicalReport | null;
  templateId: string;
  format: ReportFormat;
}

const AcademicReportTemplate: React.FC<{ report: CanonicalReport }> = ({ report }) => {
  const { title, research_domain, generated_at, sections } = report;

  return (
    <article className="report-preview">
      <header className="report-preview-header">
        <h3 className="report-preview-title">{title}</h3>
        <div className="report-preview-meta">
          {research_domain && <span className="meta-pill">{research_domain}</span>}
          {generated_at && (
            <span className="meta-pill">
              Generated: {new Date(generated_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </header>

      <section className="report-preview-section">
        <h4>Abstract</h4>
        <p>{sections.abstract || "No abstract available."}</p>
      </section>

      {sections.introduction && (
        <section className="report-preview-section">
          <h4>Introduction</h4>
          <p>{sections.introduction}</p>
        </section>
      )}

      {sections.literature_review && (
        <section className="report-preview-section">
          <h4>Literature Review</h4>
          <p>{sections.literature_review}</p>
        </section>
      )}

      {sections.methodology && (
        <section className="report-preview-section">
          <h4>Methodology</h4>
          <p>{sections.methodology}</p>
        </section>
      )}

      {Array.isArray(sections.findings) && sections.findings.length > 0 && (
        <section className="report-preview-section">
          <h4>Findings (themes)</h4>
          <ul className="report-preview-list">
            {sections.findings.slice(0, 5).map((theme: any, idx: number) => (
              <li key={idx}>
                <strong>{theme.theme_name || `Theme ${idx + 1}`}</strong>
                {theme.precise_definition && <span>: {theme.precise_definition}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {sections.discussion && (
        <section className="report-preview-section">
          <h4>Discussion</h4>
          <p>{sections.discussion}</p>
        </section>
      )}

      {sections.conclusion && (
        <section className="report-preview-section">
          <h4>Conclusion</h4>
          <p>{sections.conclusion}</p>
        </section>
      )}
    </article>
  );
};

export const ReportPreview: React.FC<Props> = ({ report, templateId, format }) => {
  if (!report) {
    return (
      <div className="report-preview-empty">
        <p className="response-caption">
          No canonical report found in the JSON yet. Run a pipeline and make sure the response
          includes a report payload.
        </p>
      </div>
    );
  }

  // For now, all templates render the same academic layout.
  // Later we can branch on templateId to use different components.
  switch (templateId) {
    case "academic_full_v1":
    case "executive_summary_v1":
    case "slide_deck_outline_v1":
    default:
      return (
        <div className="report-preview-wrapper">
          <div className="report-preview-header-row">
            <span className="badge">Preview ({templateId}, {format})</span>
          </div>
          <AcademicReportTemplate report={report} />
        </div>
      );
  }
};


