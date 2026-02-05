export type ReportFormat = "json" | "markdown" | "html" | "pdf" | "docx" | "pptx" | "text";

export interface ReportTemplate {
  id: string;
  label: string;
  description: string;
  recommendedUse: string;
  supportedFormats: ReportFormat[];
}

/**
 * Central registry of report templates a user can choose from.
 * Backend changes will later interpret `templateId` + `format`
 * when generating PDF/HTML/DOCX/PPTX from the canonical JSON report.
 */
export const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: "academic_full_v1",
    label: "Academic report (full)",
    description:
      "Includes abstract, introduction, full literature review, methodology, findings, discussion, conclusion, and references.",
    recommendedUse: "Thesis-style academic deliverables or detailed technical research reports.",
    supportedFormats: ["markdown", "html", "pdf", "docx", "text"],
  },
  {
    id: "executive_summary_v1",
    label: "Executive summary",
    description:
      "Concise 1–3 page overview focusing on key findings, implications, and recommendations.",
    recommendedUse: "Stakeholder briefings and non-technical audiences.",
    supportedFormats: ["markdown", "html", "pdf", "docx", "text"],
  },
  {
    id: "slide_deck_outline_v1",
    label: "Slide deck outline",
    description:
      "Bullet-point outline grouped by sections and themes, suitable for slide decks.",
    recommendedUse: "Conference talks, teaching slides, internal presentations.",
    supportedFormats: ["pptx", "markdown", "pdf"],
  },
];


