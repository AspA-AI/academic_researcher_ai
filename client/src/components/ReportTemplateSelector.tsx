import React from "react";
import { REPORT_TEMPLATES, type ReportTemplate } from "../config/reportTemplates";

interface Props {
  value: string;
  onChange: (templateId: string) => void;
}

export const ReportTemplateSelector: React.FC<Props> = ({ value, onChange }) => {
  const selected = REPORT_TEMPLATES.find((t) => t.id === value) ?? REPORT_TEMPLATES[0];

  return (
    <div className="form-section">
      <h4>Report template</h4>
      <div className="field-grid">
        <label className="field">
          <span className="field-label">Template style</span>
          <select
            className="field-input"
            value={selected.id}
            onChange={(e) => onChange(e.target.value)}
          >
            {REPORT_TEMPLATES.map((tpl: ReportTemplate) => (
              <option key={tpl.id} value={tpl.id}>
                {tpl.label}
              </option>
            ))}
          </select>
          <span className="field-hint">{selected.description}</span>
        </label>

        <div className="field">
          <span className="field-label">Recommended use</span>
          <p className="field-hint">{selected.recommendedUse}</p>
        </div>
      </div>
    </div>
  );
};


