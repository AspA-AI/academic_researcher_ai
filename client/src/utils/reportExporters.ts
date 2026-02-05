import type { CanonicalReport } from "./report";
import type { ReportFormat } from "../config/reportTemplates";
import { jsPDF } from "jspdf";
import { Document, Packer, Paragraph, HeadingLevel, AlignmentType } from "docx";
// pptxgenjs uses default export
import PptxGenJS from "pptxgenjs";
import { getThemeById, type PPTXTheme } from "../config/pptxThemes";
import { transformReportFormat } from "../api/client";

/**
 * Format-specific exporters that generate downloadable files
 * from a canonical report object.
 */

// PDF Generator (using jsPDF)
export async function generatePDF(
  report: CanonicalReport,
  templateId: string
): Promise<Blob> {
  const doc = new jsPDF();

  let yPos = 20;
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 20;
  const maxWidth = pageWidth - 2 * margin;

  // Title
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  const titleLines = doc.splitTextToSize(report.title, maxWidth);
  doc.text(titleLines, margin, yPos);
  yPos += titleLines.length * 8 + 10;

  // Metadata
  if (report.research_domain || report.generated_at) {
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    const meta: string[] = [];
    if (report.research_domain) meta.push(`Domain: ${report.research_domain}`);
    if (report.generated_at) {
      meta.push(`Generated: ${new Date(report.generated_at).toLocaleDateString()}`);
    }
    doc.text(meta.join(" | "), margin, yPos);
    yPos += 10;
  }

  // Sections
  doc.setFontSize(12);
  const sections = report.sections;

  if (sections.abstract) {
    yPos = addSection(doc, "Abstract", sections.abstract, margin, yPos, maxWidth);
  }
  if (sections.introduction) {
    yPos = addSection(doc, "Introduction", sections.introduction, margin, yPos, maxWidth);
  }
  if (sections.literature_review) {
    yPos = addSection(
      doc,
      "Literature Review",
      sections.literature_review,
      margin,
      yPos,
      maxWidth
    );
  }
  if (sections.methodology) {
    yPos = addSection(doc, "Methodology", sections.methodology, margin, yPos, maxWidth);
  }
  if (Array.isArray(sections.findings) && sections.findings.length > 0) {
    yPos = addFindingsSection(doc, sections.findings, margin, yPos, maxWidth);
  }
  if (sections.discussion) {
    yPos = addSection(doc, "Discussion", sections.discussion, margin, yPos, maxWidth);
  }
  if (sections.conclusion) {
    yPos = addSection(doc, "Conclusion", sections.conclusion, margin, yPos, maxWidth);
  }

  return doc.output("blob");
}

function addSection(
  doc: any,
  heading: string,
  content: string,
  margin: number,
  yPos: number,
  maxWidth: number
): number {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (yPos > pageHeight - 30) {
    doc.addPage();
    yPos = 20;
  }

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(heading, margin, yPos);
  yPos += 10;

  doc.setFontSize(11);
  doc.setFont("helvetica", "normal");
  const lines = doc.splitTextToSize(content, maxWidth);
  doc.text(lines, margin, yPos);
  yPos += lines.length * 6 + 10;

  return yPos;
}

function addFindingsSection(
  doc: any,
  findings: any[],
  margin: number,
  yPos: number,
  maxWidth: number
): number {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (yPos > pageHeight - 30) {
    doc.addPage();
    yPos = 20;
  }

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Findings", margin, yPos);
  yPos += 10;

  doc.setFontSize(11);
  doc.setFont("helvetica", "normal");
  findings.forEach((theme: any, idx: number) => {
    if (yPos > pageHeight - 30) {
      doc.addPage();
      yPos = 20;
    }
    const themeName = theme.theme_name || `Theme ${idx + 1}`;
    doc.setFont("helvetica", "bold");
    doc.text(`• ${themeName}`, margin + 5, yPos);
    yPos += 6;
    if (theme.precise_definition) {
      doc.setFont("helvetica", "normal");
      const defLines = doc.splitTextToSize(theme.precise_definition, maxWidth - 10);
      doc.text(defLines, margin + 10, yPos);
      yPos += defLines.length * 6;
    }
    yPos += 5;
  });

  return yPos;
}

// DOCX Generator (using docx)
export async function generateDOCX(
  report: CanonicalReport,
  templateId: string
): Promise<Blob> {

  const children: any[] = [];

  // Title
  children.push(
    new Paragraph({
      text: report.title,
      heading: HeadingLevel.TITLE,
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
    })
  );

  // Metadata
  const meta: string[] = [];
  if (report.research_domain) meta.push(`Domain: ${report.research_domain}`);
  if (report.generated_at) {
    meta.push(`Generated: ${new Date(report.generated_at).toLocaleDateString()}`);
  }
  if (meta.length > 0) {
    children.push(
      new Paragraph({
        text: meta.join(" | "),
        alignment: AlignmentType.CENTER,
        spacing: { after: 300 },
      })
    );
  }

  // Sections
  const sections = report.sections;

  if (sections.abstract) {
    children.push(
      new Paragraph({
        text: "Abstract",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.abstract, spacing: { after: 300 } }));
  }

  if (sections.introduction) {
    children.push(
      new Paragraph({
        text: "Introduction",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.introduction, spacing: { after: 300 } }));
  }

  if (sections.literature_review) {
    children.push(
      new Paragraph({
        text: "Literature Review",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.literature_review, spacing: { after: 300 } }));
  }

  if (sections.methodology) {
    children.push(
      new Paragraph({
        text: "Methodology",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.methodology, spacing: { after: 300 } }));
  }

  if (Array.isArray(sections.findings) && sections.findings.length > 0) {
    children.push(
      new Paragraph({
        text: "Findings",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    sections.findings.forEach((theme: any, idx: number) => {
      const themeName = theme.theme_name || `Theme ${idx + 1}`;
      children.push(
        new Paragraph({
          text: themeName,
          bullet: { level: 0 },
          spacing: { after: 100 },
        })
      );
      if (theme.precise_definition) {
        children.push(
          new Paragraph({
            text: theme.precise_definition,
            indent: { left: 400 },
            spacing: { after: 100 },
          })
        );
      }
    });
  }

  if (sections.discussion) {
    children.push(
      new Paragraph({
        text: "Discussion",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.discussion, spacing: { after: 300 } }));
  }

  if (sections.conclusion) {
    children.push(
      new Paragraph({
        text: "Conclusion",
        heading: HeadingLevel.HEADING_1,
        spacing: { before: 200, after: 200 },
      })
    );
    children.push(new Paragraph({ text: sections.conclusion, spacing: { after: 300 } }));
  }

  const doc = new Document({
    sections: [
      {
        properties: {},
        children,
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  return blob;
}

// PPTX Generator (using pptxgenjs with beautiful themes and LLM transformation)
export async function generatePPTX(
  report: CanonicalReport,
  templateId: string,
  themeId?: string
): Promise<Blob> {
  // First, transform canonical report to PPTX structure using LLM
  const transformResult = await transformReportFormat(report, "pptx");
  
  if (!transformResult.success || !transformResult.data) {
    throw new Error(`Failed to transform report for PPTX: ${transformResult.error || "Unknown error"}`);
  }
  
  const pptxStructure = transformResult.data;
  const pptx = new PptxGenJS();
  const theme = getThemeById(themeId || "ocean_sunset");

  // Set master slide layout
  pptx.layout = "LAYOUT_WIDE";
  pptx.defineLayout({ name: "CUSTOM", width: 10, height: 7.5 });

  // Helper to create gradient background (simulated with shapes)
  const addGradientBackground = (slide: any, fromColor: string, toColor: string) => {
    slide.background = { color: `#${toColor}` };
    // Add gradient effect with overlapping shapes
    if (theme.layout?.useGradients) {
      slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 10,
        h: 7.5,
        fill: { color: `#${fromColor}`, transparency: 30 },
        line: { color: "transparent" },
      });
    }
  };

  // Title slide with creative design
  const titleSlide = pptx.addSlide();
  
  // Background
  if (theme.colors.backgroundGradient && theme.layout?.useGradients) {
    addGradientBackground(titleSlide, theme.colors.backgroundGradient.from, theme.colors.backgroundGradient.to);
  } else {
    titleSlide.background = { color: `#${theme.colors.background}` };
  }

  // Add decorative shapes based on theme style
  if (theme.layout?.useShapes) {
    if (theme.style === "gradient" || theme.style === "elegant") {
      // Add large decorative circle
      titleSlide.addShape(pptx.ShapeType.ellipse, {
        x: 8,
        y: 0,
        w: 3,
        h: 3,
        fill: { color: `#${theme.colors.primary}`, transparency: 15 },
        line: { color: "transparent" },
      });
      // Add smaller accent circle
      titleSlide.addShape(pptx.ShapeType.ellipse, {
        x: -1,
        y: 5,
        w: 2.5,
        h: 2.5,
        fill: { color: `#${theme.colors.accent}`, transparency: 20 },
        line: { color: "transparent" },
      });
    }
    
    if (theme.style === "tech" || theme.style === "bold") {
      // Add geometric shapes
      titleSlide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 10,
        h: 0.3,
        fill: { color: `#${theme.colors.primary}` },
        line: { color: "transparent" },
      });
      titleSlide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 7.2,
        w: 10,
        h: 0.3,
        fill: { color: `#${theme.colors.secondary}` },
        line: { color: "transparent" },
      });
    }
  }

  // Title with beautiful styling
  const titleColor = theme.style === "tech" || theme.style === "bold" ? `#${theme.colors.text}` : `#${theme.colors.primary}`;
  titleSlide.addText(report.title, {
    x: 0.5,
    y: 2.8,
    w: 9,
    h: 1.8,
    fontSize: theme.fonts.title.size,
    fontFace: theme.fonts.title.name,
    bold: theme.fonts.title.weight === "bold",
    align: "center",
    color: titleColor,
  });

  // Metadata slide with elegant design
  const meta: string[] = [];
  if (report.research_domain) meta.push(`Domain: ${report.research_domain}`);
  if (report.generated_at) {
    meta.push(`Generated: ${new Date(report.generated_at).toLocaleDateString()}`);
  }
  if (meta.length > 0) {
    const metaSlide = pptx.addSlide();
    
    // Background
    if (theme.colors.backgroundGradient && theme.layout?.useGradients) {
      addGradientBackground(metaSlide, theme.colors.backgroundGradient.from, theme.colors.backgroundGradient.to);
    } else {
      metaSlide.background = { color: `#${theme.colors.background}` };
    }
    
    // Add subtle decorative element
    if (theme.layout?.useShapes) {
      metaSlide.addShape(pptx.ShapeType.rect, {
        x: 2,
        y: 3.2,
        w: 6,
        h: 0.1,
        fill: { color: `#${theme.colors.primary}`, transparency: 40 },
        line: { color: "transparent" },
      });
    }
    
    metaSlide.addText(meta.join(" • "), {
      x: 0.5,
      y: 3.5,
      w: 9,
      h: 0.8,
      fontSize: theme.fonts.body.size - 1,
      fontFace: theme.fonts.body.name,
      align: "center",
      color: `#${theme.colors.textLight}`,
      italic: true,
    });
  }

  // Use LLM-transformed slide structure
  const slides = pptxStructure.slides || [];
  
  // Helper function to create slide header (reusable)
  const addSlideHeader = (slide: any, title: string, isContinuation: boolean = false) => {
    const headerHeight = theme.layout?.headerStyle === "minimal" ? 0.6 : 0.9;
    const headerColor = theme.colors.headerBg || theme.colors.primary;
    
    if (theme.layout?.headerStyle === "full") {
      slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 10,
        h: headerHeight,
        fill: { color: `#${headerColor}` },
        line: { color: "transparent" },
      });
      
      if (theme.layout?.useShapes) {
        slide.addShape(pptx.ShapeType.rect, {
          x: 0,
          y: headerHeight - 0.15,
          w: 10,
          h: 0.15,
          fill: { color: `#${theme.colors.accent}` },
          line: { color: "transparent" },
        });
      }
    } else if (theme.layout?.headerStyle === "left") {
      slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 0.3,
        h: headerHeight,
        fill: { color: `#${headerColor}` },
        line: { color: "transparent" },
      });
    } else if (theme.layout?.headerStyle === "centered") {
      slide.addShape(pptx.ShapeType.rect, {
        x: 2,
        y: 0,
        w: 6,
        h: headerHeight,
        fill: { color: `#${headerColor}` },
        line: { color: "transparent" },
      });
    } else if (theme.layout?.headerStyle === "minimal") {
      slide.addShape(pptx.ShapeType.rect, {
        x: 0.5,
        y: 0.4,
        w: 9,
        h: 0.1,
        fill: { color: `#${headerColor}` },
        line: { color: "transparent" },
      });
    }

    const titleX = theme.layout?.headerStyle === "left" ? 0.8 : 0.5;
    const titleY = theme.layout?.headerStyle === "minimal" ? 0.5 : 0.15;
    const titleColor = theme.layout?.headerStyle === "minimal" ? `#${theme.colors.primary}` : `#${theme.colors.background}`;
    const displayTitle = isContinuation ? `${title} (continued)` : title;
    
    slide.addText(displayTitle, {
      x: titleX,
      y: titleY,
      w: theme.layout?.headerStyle === "left" ? 8.5 : 9,
      h: 0.6,
      fontSize: theme.fonts.subtitle?.size || theme.fonts.title.size - 6,
      fontFace: theme.fonts.title.name,
      bold: true,
      color: titleColor,
      align: "left",
    });
  };

  // Generate slides from LLM-transformed structure
  if (slides.length > 0) {
    slides.forEach((slideData: any, index: number) => {
      // Handle title slide specially (use our custom title slide)
      if (slideData.slideType === "title" && index === 0) {
        // Title slide already created above, skip
        return;
      }
      
      const slide = pptx.addSlide();
      
      // Background
      if (theme.colors.backgroundGradient && theme.layout?.useGradients) {
        addGradientBackground(slide, theme.colors.backgroundGradient.from, theme.colors.backgroundGradient.to);
      } else {
        slide.background = { color: `#${theme.colors.background}` };
      }
      
      // Add header based on slide type
      const isContinuation = slideData.title.toLowerCase().includes("continued");
      addSlideHeader(slide, slideData.title, isContinuation);
      
      // Add decorative shapes for visual interest
      if (theme.layout?.useShapes && (theme.style === "gradient" || theme.style === "elegant")) {
        slide.addShape(pptx.ShapeType.ellipse, {
          x: 8.5,
          y: 6,
          w: 1.2,
          h: 1.2,
          fill: { color: `#${theme.colors.accent}`, transparency: 25 },
          line: { color: "transparent" },
        });
      }
      
      // Add content (bullet points from LLM transformation)
      const contentY = theme.layout?.headerStyle === "minimal" ? 0.9 : 1.05;
      const contentItems = Array.isArray(slideData.content) ? slideData.content : [slideData.content || ""];
      
      // Calculate dynamic height based on content
      const maxItemsPerSlide = 6;
      const itemHeight = 0.75;
      const totalHeight = Math.min(contentItems.length, maxItemsPerSlide) * itemHeight;
      
      contentItems.slice(0, maxItemsPerSlide).forEach((item: string, itemIdx: number) => {
        if (!item || item.trim().length === 0) return;
        
        slide.addText(`• ${item}`, {
          x: 0.7,
          y: contentY + (itemIdx * itemHeight),
          w: 8.6,
          h: itemHeight,
          fontSize: theme.fonts.body.size,
          fontFace: theme.fonts.body.name,
          color: `#${theme.colors.text}`,
          align: "left",
          valign: "top",
          bullet: false, // We're adding bullet manually
          lineSpacing: 22,
          wrap: true,
        });
      });
      
      // If there are more items, create continuation slides
      if (contentItems.length > maxItemsPerSlide) {
        const remainingItems = contentItems.slice(maxItemsPerSlide);
        remainingItems.forEach((item: string, itemIdx: number) => {
          if (itemIdx % maxItemsPerSlide === 0) {
            const continuationSlide = pptx.addSlide();
            
            if (theme.colors.backgroundGradient && theme.layout?.useGradients) {
              addGradientBackground(continuationSlide, theme.colors.backgroundGradient.from, theme.colors.backgroundGradient.to);
            } else {
              continuationSlide.background = { color: `#${theme.colors.background}` };
            }
            
            addSlideHeader(continuationSlide, slideData.title, true);
            
            const continuationContentY = theme.layout?.headerStyle === "minimal" ? 0.9 : 1.05;
            const continuationBatch = remainingItems.slice(itemIdx, itemIdx + maxItemsPerSlide);
            
            continuationBatch.forEach((continuationItem: string, batchIdx: number) => {
              if (!continuationItem || continuationItem.trim().length === 0) return;
              
              continuationSlide.addText(`• ${continuationItem}`, {
                x: 0.7,
                y: continuationContentY + (batchIdx * itemHeight),
                w: 8.6,
                h: itemHeight,
                fontSize: theme.fonts.body.size,
                fontFace: theme.fonts.body.name,
                color: `#${theme.colors.text}`,
                align: "left",
                valign: "top",
                bullet: false,
                lineSpacing: 22,
                wrap: true,
              });
            });
          }
        });
      }
    });
  } else {
    // Fallback: use old method if transformation failed
    throw new Error("LLM transformation failed to generate slides. Please try again.");
  }


  const result = await pptx.write({ outputType: "blob" });
  return result as Blob;
}

// Markdown Generator
export function generateMarkdown(report: CanonicalReport, templateId: string): Blob {
  let md = `# ${report.title}\n\n`;

  if (report.research_domain || report.generated_at) {
    md += "---\n\n";
    if (report.research_domain) md += `**Domain:** ${report.research_domain}\n\n`;
    if (report.generated_at) {
      md += `**Generated:** ${new Date(report.generated_at).toLocaleDateString()}\n\n`;
    }
    md += "---\n\n";
  }

  const sections = report.sections;

  if (sections.abstract) {
    md += `## Abstract\n\n${sections.abstract}\n\n`;
  }
  if (sections.introduction) {
    md += `## Introduction\n\n${sections.introduction}\n\n`;
  }
  if (sections.literature_review) {
    md += `## Literature Review\n\n${sections.literature_review}\n\n`;
  }
  if (sections.methodology) {
    md += `## Methodology\n\n${sections.methodology}\n\n`;
  }
  if (Array.isArray(sections.findings) && sections.findings.length > 0) {
    md += `## Findings\n\n`;
    sections.findings.forEach((theme: any, idx: number) => {
      const themeName = theme.theme_name || `Theme ${idx + 1}`;
      md += `### ${themeName}\n\n`;
      if (theme.precise_definition) {
        md += `${theme.precise_definition}\n\n`;
      }
    });
  }
  if (sections.discussion) {
    md += `## Discussion\n\n${sections.discussion}\n\n`;
  }
  if (sections.conclusion) {
    md += `## Conclusion\n\n${sections.conclusion}\n\n`;
  }

  return new Blob([md], { type: "text/markdown" });
}

// HTML Generator
export function generateHTML(report: CanonicalReport, templateId: string): Blob {
  const sections = report.sections;
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(report.title)}</title>
  <style>
    body {
      font-family: 'Georgia', 'Times New Roman', serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      color: #333;
    }
    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; margin-top: 30px; }
    h3 { color: #555; }
    .meta { color: #7f8c8d; font-style: italic; margin-bottom: 30px; }
    p { text-align: justify; }
    ul { margin-left: 20px; }
  </style>
</head>
<body>
  <h1>${escapeHtml(report.title)}</h1>
  <div class="meta">
    ${report.research_domain ? `<strong>Domain:</strong> ${escapeHtml(report.research_domain)}<br>` : ""}
    ${report.generated_at ? `<strong>Generated:</strong> ${new Date(report.generated_at).toLocaleDateString()}` : ""}
  </div>
  ${sections.abstract ? `<h2>Abstract</h2><p>${escapeHtml(sections.abstract)}</p>` : ""}
  ${sections.introduction ? `<h2>Introduction</h2><p>${escapeHtml(sections.introduction)}</p>` : ""}
  ${sections.literature_review ? `<h2>Literature Review</h2><p>${escapeHtml(sections.literature_review)}</p>` : ""}
  ${sections.methodology ? `<h2>Methodology</h2><p>${escapeHtml(sections.methodology)}</p>` : ""}
  ${Array.isArray(sections.findings) && sections.findings.length > 0 ? `<h2>Findings</h2><ul>${sections.findings.map((t: any) => `<li><strong>${escapeHtml(t.theme_name || "Theme")}</strong>: ${escapeHtml(t.precise_definition || "")}</li>`).join("")}</ul>` : ""}
  ${sections.discussion ? `<h2>Discussion</h2><p>${escapeHtml(sections.discussion)}</p>` : ""}
  ${sections.conclusion ? `<h2>Conclusion</h2><p>${escapeHtml(sections.conclusion)}</p>` : ""}
</body>
</html>`;

  return new Blob([html], { type: "text/html" });
}

// Text Generator
export function generateText(report: CanonicalReport, templateId: string): Blob {
  let text = `${report.title}\n`;
  text += "=".repeat(report.title.length) + "\n\n";

  if (report.research_domain || report.generated_at) {
    if (report.research_domain) text += `Domain: ${report.research_domain}\n`;
    if (report.generated_at) {
      text += `Generated: ${new Date(report.generated_at).toLocaleDateString()}\n`;
    }
    text += "\n";
  }

  const sections = report.sections;

  if (sections.abstract) {
    text += `ABSTRACT\n${"-".repeat(50)}\n${sections.abstract}\n\n`;
  }
  if (sections.introduction) {
    text += `INTRODUCTION\n${"-".repeat(50)}\n${sections.introduction}\n\n`;
  }
  if (sections.literature_review) {
    text += `LITERATURE REVIEW\n${"-".repeat(50)}\n${sections.literature_review}\n\n`;
  }
  if (sections.methodology) {
    text += `METHODOLOGY\n${"-".repeat(50)}\n${sections.methodology}\n\n`;
  }
  if (Array.isArray(sections.findings) && sections.findings.length > 0) {
    text += `FINDINGS\n${"-".repeat(50)}\n`;
    sections.findings.forEach((theme: any, idx: number) => {
      const themeName = theme.theme_name || `Theme ${idx + 1}`;
      text += `\n${themeName}\n`;
      if (theme.precise_definition) {
        text += `${theme.precise_definition}\n`;
      }
    });
    text += "\n";
  }
  if (sections.discussion) {
    text += `DISCUSSION\n${"-".repeat(50)}\n${sections.discussion}\n\n`;
  }
  if (sections.conclusion) {
    text += `CONCLUSION\n${"-".repeat(50)}\n${sections.conclusion}\n\n`;
  }

  return new Blob([text], { type: "text/plain" });
}

// JSON Generator
export function generateJSON(report: CanonicalReport, templateId: string): Blob {
  const json = JSON.stringify(report, null, 2);
  return new Blob([json], { type: "application/json" });
}

// Helper to escape HTML
function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Main export function
export async function generateReportFile(
  report: CanonicalReport,
  format: ReportFormat,
  templateId: string,
  pptxThemeId?: string
): Promise<Blob> {
  switch (format) {
    case "pdf":
      return await generatePDF(report, templateId);
    case "docx":
      return await generateDOCX(report, templateId);
    case "pptx":
      return await generatePPTX(report, templateId, pptxThemeId);
    case "markdown":
      return generateMarkdown(report, templateId);
    case "html":
      return generateHTML(report, templateId);
    case "text":
      return generateText(report, templateId);
    case "json":
      return generateJSON(report, templateId);
    default:
      throw new Error(`Unsupported format: ${format}`);
  }
}

// Helper to download a blob
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

