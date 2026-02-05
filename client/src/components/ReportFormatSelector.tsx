import React from "react";
import type { ReportFormat } from "../config/reportTemplates";

interface Props {
  value: ReportFormat;
  onChange: (value: ReportFormat) => void;
  allowedFormats?: ReportFormat[];
}

const ALL_FORMAT_OPTIONS: { value: ReportFormat; label: string }[] = [
  { value: "pdf", label: "PDF (.pdf)" },
  { value: "markdown", label: "Markdown (.md)" },
  { value: "html", label: "HTML (.html)" },
  { value: "docx", label: "Word (.docx)" },
  { value: "pptx", label: "PowerPoint (.pptx)" },
  { value: "text", label: "Plain text (.txt)" },
  { value: "json", label: "Raw JSON (.json)" },
];

export const ReportFormatSelector: React.FC<Props> = ({
  value,
  onChange,
  allowedFormats,
}) => {
  const options = allowedFormats
    ? ALL_FORMAT_OPTIONS.filter((opt) => allowedFormats.includes(opt.value))
    : ALL_FORMAT_OPTIONS;

  return (
    <label className="field">
      <span className="field-label">Output format</span>
      <select
        className="field-input"
        value={value}
        onChange={(e) => onChange(e.target.value as ReportFormat)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <span className="field-hint">
        This only changes how the report is rendered for download. The canonical JSON
        report stays the same under the hood.
      </span>
    </label>
  );
};


