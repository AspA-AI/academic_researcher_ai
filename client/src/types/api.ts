export type PipelineMode = "auto" | "manual";

export interface PipelineConfig {
  auto_retry_failed_steps: boolean;
  enable_supervisor: boolean;
  max_retries: number;
  save_intermediate_results: boolean;
}

export interface PipelineRequestPayload {
  query: string;
  research_domain: string;
  max_results: number;
  limit: number;
  quality_threshold: number;
  mode: PipelineMode;
  sources: string[];
  enrich: "standard" | "deep" | "none";
  year_from?: number | null;
  year_to?: number | null;
  store: boolean;
  pipeline_config: PipelineConfig;
}

export interface PipelineResponseEnvelope {
  success: boolean;
  error?: string;
  status?: string;
  pipeline_id?: string;
  // When hitting FastAPI, we get a structured PipelineResponse.
  // We keep this loose to remain forward-compatible with backend changes.
  raw?: any;
}


