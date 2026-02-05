import React from "react";
import { PPTX_THEMES, type PPTXTheme } from "../config/pptxThemes";

interface Props {
  value: string;
  onChange: (themeId: string) => void;
}

/**
 * Component for selecting PPTX design theme (like Gamma's template picker)
 */
export const PPTXThemeSelector: React.FC<Props> = ({ value, onChange }) => {
  return (
    <div className="form-section">
      <label className="form-label">
        <strong>Design Theme</strong>
        <span className="form-label-caption">
          Choose a visual style for your presentation slides
        </span>
      </label>
      <div className="theme-grid">
        {PPTX_THEMES.map((theme: PPTXTheme) => (
          <div
            key={theme.id}
            className={`theme-card ${value === theme.id ? "theme-card-selected" : ""}`}
            onClick={() => onChange(theme.id)}
            style={{
              borderColor: value === theme.id ? `#${theme.colors.primary}` : "#e5e7eb",
              borderWidth: value === theme.id ? "2px" : "1px",
            }}
          >
            <div className="theme-preview">
              <div
                className="theme-preview-header"
                style={{ backgroundColor: `#${theme.colors.primary}` }}
              >
                <div
                  className="theme-preview-title"
                  style={{ color: `#${theme.colors.background}` }}
                >
                  Sample Title
                </div>
              </div>
              <div
                className="theme-preview-body"
                style={{ backgroundColor: `#${theme.colors.background}` }}
              >
                <div
                  className="theme-preview-text"
                  style={{ color: `#${theme.colors.text}` }}
                >
                  Content preview
                </div>
              </div>
            </div>
            <div className="theme-info">
              <div className="theme-name">{theme.name}</div>
              <div className="theme-description">{theme.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

