import type { PipelineResponseEnvelope } from "../types/api";

export interface CanonicalReportSections {
  abstract?: string;
  introduction?: string;
  literature_review?: string;
  methodology?: string;
  findings?: any[];
  discussion?: string;
  conclusion?: string;
  references?: any[];
}

export interface CanonicalReport {
  title: string;
  research_domain?: string;
  generated_at?: string;
  sections: CanonicalReportSections;
}

/**
 * Normalize a raw backend report object into the CanonicalReport
 * shape used by all templates on the frontend.
 */
function normalizeReport(raw: any): CanonicalReport | null {
  if (!raw || typeof raw !== "object") return null;

  const sections = raw.sections ?? {};

  return {
    title: raw.title ?? "Untitled report",
    research_domain: raw.research_domain,
    generated_at: raw.generated_at,
    sections: {
      abstract: sections.abstract,
      introduction: sections.introduction,
      literature_review: sections.literature_review,
      methodology: sections.methodology,
      findings: sections.findings ?? [],
      discussion: sections.discussion,
      conclusion: sections.conclusion,
      references: sections.references ?? [],
    },
  };
}

/**
 * Extract the canonical report object from either a lite or full
 * pipeline response envelope.
 *
 * - Lite pipeline:   envelope.raw.data.report
 * - Full pipeline:   envelope.raw.report_result.data.report
 */
export function extractCanonicalReport(
  envelope: PipelineResponseEnvelope | null
): CanonicalReport | null {
  if (!envelope || !envelope.raw) return null;

  const raw = envelope.raw;

  // Lite pipeline route shape:
  //   {
  //     success, pipeline_id, status,
  //     result: { success, data: { report, ... }, ... },
  //     data: { ... },
  //   }
  const liteResult = raw?.result;
  const liteReport = liteResult?.data?.report;
  if (liteReport && liteReport.sections) {
    return normalizeReport(liteReport);
  }

  // Full pipeline route shape:
  //   {
  //     success, pipeline_id, status,
  //     result: { ..., report_result: { data: { report, ... } } },
  //     data: { ... },
  //   }
  const fullReport = liteResult?.report_result?.data?.report;
  if (fullReport && fullReport.sections) {
    return normalizeReport(fullReport);
  }

  // Direct service shapes (for completeness / future use):
  const serviceLite = raw?.data?.report;
  if (serviceLite && serviceLite.sections) {
    return normalizeReport(serviceLite);
  }

  const serviceFull = raw?.report_result?.data?.report;
  if (serviceFull && serviceFull.sections) {
    return normalizeReport(serviceFull);
  }

  const nested = raw?.data?.report_result?.data?.report;
  if (nested && nested.sections) {
    return normalizeReport(nested);
  }

  return null;
}


