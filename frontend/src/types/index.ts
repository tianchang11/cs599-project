export interface Note {
  id: string;
  title: string;
  content: string;
  sources: string[];
  query: string;
  createdAt: string;
  updatedAt: string;
}

export interface SearchResult {
  url: string;
  title: string;
  content: string;
  score?: number;
}

export interface ResearchStep {
  step:
    | "planning"
    | "refining"
    | "searching"
    | "evaluating"
    | "filtering"
    | "synthesizing"
    | "drafting"
    | "done";
  message: string;
  percent?: number;
}

export type SSEEventType =
  | "step"
  | "progress"
  | "report"
  | "sources"
  | "classified"
  | "quality_update"
  | "done"
  | "error";

export interface SSEEvent {
  type: SSEEventType;
  step?: string;
  message?: string;
  percent?: number;
  content?: string;
  sources?: SearchResult[];
  category?: string;
  confidence?: number;
  qualityScore?: number;
  coverageScore?: number;
  reportQuality?: number;
  iteration?: number;
  draftIteration?: number;
  error?: string;
}

export type LLMProvider = "openai" | "anthropic" | "deepseek";

export type ResearchStrategy = "factual" | "analytical" | "exploratory" | "comparative";

export interface AppSettings {
  provider: LLMProvider;
  apiKey: string;
  model: string;
}

export interface StrategyInfo {
  name: string;
  description: string;
}

export interface ResearchStatus {
  taskId: string;
  status: string;
  progress: number;
  currentStep?: string;
  strategy: string;
  qualityScore?: number;
  coverageScore?: number;
  reportQuality?: number;
  iteration: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  device_id: string;
}
