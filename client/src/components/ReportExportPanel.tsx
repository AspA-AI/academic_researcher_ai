import React, { useState } from "react";
import { ReportTemplateSelector } from "./ReportTemplateSelector";
import { ReportFormatSelector } from "./ReportFormatSelector";
import { ReportPreview } from "./ReportPreview";
import { PPTXThemeSelector } from "./PPTXThemeSelector";
import { REPORT_TEMPLATES, type ReportFormat } from "../config/reportTemplates";
import type { CanonicalReport } from "../utils/report";
import { generateReportFile, downloadBlob } from "../utils/reportExporters";

interface Props {
  pipelineId?: string;
  report: CanonicalReport | null;
}

/**
 * Panel for choosing template + format, previewing, and exporting
 * reports in various formats (PDF, DOCX, PPTX, Markdown, HTML, Text, JSON).
 */
export const ReportExportPanel: React.FC<Props> = ({ pipelineId, report }) => {
  const [templateId, setTemplateId] = useState<string>("academic_full_v1");
  const [format, setFormat] = useState<ReportFormat>("pdf");
  const [pptxThemeId, setPptxThemeId] = useState<string>("ocean_sunset");
  const [isExporting, setIsExporting] = useState(false);

  const selectedTemplate =
    REPORT_TEMPLATES.find((t) => t.id === templateId) ?? REPORT_TEMPLATES[0];

  const handleExport = async () => {
    if (!report) {
      alert("No report data available to export.");
      return;
    }

    setIsExporting(true);
    try {
      const blob = await generateReportFile(report, format, templateId, format === "pptx" ? pptxThemeId : undefined);
      const extension = format === "markdown" ? "md" : format;
      const filename = `${report.title.replace(/[^a-z0-9]/gi, "_")}_${templateId}.${extension}`;
      downloadBlob(blob, filename);
    } catch (error) {
      console.error("Export error:", error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      let userMessage = `Failed to generate ${format.toUpperCase()} file.\n\n`;
      
      // Format-specific error messages
      if (format === "html" || format === "markdown" || format === "text" || format === "json") {
        userMessage += `Error: ${errorMessage}`;
      } else if (format === "pdf") {
        userMessage += `Make sure jspdf is installed.\nError: ${errorMessage}`;
      } else if (format === "docx") {
        userMessage += `Make sure docx is installed.\nError: ${errorMessage}`;
      } else if (format === "pptx") {
        userMessage += `Make sure pptxgenjs is installed.\nError: ${errorMessage}`;
      } else {
        userMessage += `Error: ${errorMessage}`;
      }
      
      alert(userMessage);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="export-panel">
      <div className="export-header">
        <h4>Report Export & Preview</h4>
        <p className="card-subtitle">
          Choose a template style and output format, preview the layout, then export your report as a
          downloadable file.
        </p>
      </div>

      <div className="export-controls">
        <div className="control-group">
          <ReportTemplateSelector value={templateId} onChange={setTemplateId} />
        </div>

        <div className="control-group">
          <ReportFormatSelector
            value={format}
            onChange={setFormat}
            allowedFormats={selectedTemplate.supportedFormats}
          />
        </div>

        {format === "pptx" && (
          <div className="control-group pptx-theme-group">
            <div className="control-group-header">
              <h5>PowerPoint Theme</h5>
              <p className="control-hint">Choose a visual theme for your presentation slides</p>
            </div>
            <PPTXThemeSelector value={pptxThemeId} onChange={setPptxThemeId} />
          </div>
        )}
      </div>

      <div className="preview-section">
        <ReportPreview report={report} templateId={templateId} format={format} />
      </div>

      <div className="export-footer">
        <button
          type="button"
          className="primary-btn export-btn"
          disabled={!report || isExporting}
          onClick={handleExport}
        >
          {isExporting ? (
            <>
              <span className="spinner-small"></span>
              <span>Generating...</span>
            </>
          ) : (
            <>
              <span>⬇️</span>
              <span>Export as {format.toUpperCase()}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

