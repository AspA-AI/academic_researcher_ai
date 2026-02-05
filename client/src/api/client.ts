import type { PipelineRequestPayload, PipelineResponseEnvelope } from "../types/api";

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  // Default to FastAPI served on the same host, port 8000, with /api/v1 prefix.
  "http://localhost:8000/api/v1";

async function postJson(path: string, body: unknown): Promise<PipelineResponseEnvelope> {
  const url = `${API_BASE}${path}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    const raw = await res.json().catch(() => null);

    if (!res.ok) {
      // Try to surface backend error structure if available
      const errorMessage =
        (raw && (raw.detail || raw.message || raw.error)) ||
        `Request failed with status ${res.status}`;
      return {
        success: false,
        status: String(res.status),
        error: errorMessage,
        raw
      };
    }

    return {
      success: true,
      status: String(res.status),
      pipeline_id: raw?.pipeline_id ?? raw?.data?.pipeline_id,
      raw
    };
  } catch (e: any) {
    return {
      success: false,
      error: e?.message || "Network error while calling API",
      raw: null
    };
  }
}

export async function startFullPipeline(
  payload: PipelineRequestPayload
): Promise<PipelineResponseEnvelope> {
  return postJson("/pipelines", payload);
}

export async function startLitePipeline(
  payload: PipelineRequestPayload
): Promise<PipelineResponseEnvelope> {
  return postJson("/pipelines/lite", payload);
}

/**
 * Transform canonical report JSON into format-specific structure using LLM.
 */
export async function transformReportFormat(
  report: any,
  targetFormat: "pptx" | "html" | "pdf" | "docx"
): Promise<{ success: boolean; data?: any; error?: string }> {
  const url = `${API_BASE}/reports/transform`;
  try {
    console.log("🔄 Calling transformation endpoint...", { targetFormat });
    
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        report,
        targetFormat
      })
    });

    console.log("📡 Response status:", res.status, res.statusText);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      console.error("❌ Transformation failed:", errorData);
      return {
        success: false,
        error: errorData.detail || errorData.error || `Request failed with status ${res.status}`
      };
    }

    const data = await res.json();
    console.log("✅ Transformation successful:", { success: data.success, hasData: !!data.data });

    if (!data.success) {
      return {
        success: false,
        error: data.error || "Transformation returned success=false"
      };
    }

    return {
      success: true,
      data: data.data
    };
  } catch (e: any) {
    console.error("💥 Transformation error:", e);
    return {
      success: false,
      error: e?.message || "Network error while transforming report"
    };
  }
}

