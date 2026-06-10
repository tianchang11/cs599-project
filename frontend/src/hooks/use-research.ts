"use client";

import { useState, useCallback } from "react";
import { API_BASE_URL } from "@/lib/api-client";
import type { ResearchStep, SearchResult } from "@/types";
import { createSSEClient } from "@/lib/sse-client";

const STEP_ORDER = ["planning", "searching", "filtering", "synthesizing", "drafting"];

export interface ResearchState {
  step: ResearchStep["step"];
  message: string;
  report: string;
  sources: SearchResult[];
  currentStepIdx: number;
  error: string;
  isDone: boolean;
}

export function useResearch(taskId: string, params: {
  deviceId: string;
  apiKey: string;
  provider: string;
  model: string;
}) {
  const [state, setState] = useState<ResearchState>({
    step: "planning",
    message: "正在连接...",
    report: "",
    sources: [],
    currentStepIdx: 0,
    error: "",
    isDone: false,
  });
  const connect = useCallback(() => {
    const url = `${API_BASE_URL}/api/research/${taskId}/stream?deviceId=${params.deviceId}&apiKey=${encodeURIComponent(params.apiKey)}&provider=${params.provider}&model=${params.model}`;
    const sse = createSSEClient(url);

    sse.connect(
      (event) => {
        switch (event.type) {
          case "step":
            setState((s) => ({
              ...s,
              step: event.step as ResearchStep["step"],
              message: event.message || s.message,
              currentStepIdx: STEP_ORDER.indexOf(event.step || ""),
            }));
            break;
          case "report":
            setState((s) => ({ ...s, report: s.report + (event.content || "") }));
            break;
          case "sources":
            if (event.sources) {
              setState((s) => ({ ...s, sources: event.sources! }));
            }
            break;
          case "done":
            setState((s) => ({ ...s, isDone: true }));
            break;
          case "error":
            setState((s) => ({ ...s, error: event.error || "未知错误" }));
            break;
        }
      },
      (err) => setState((s) => ({ ...s, error: err.message }))
    );

    return sse;
  }, [taskId, params.deviceId, params.apiKey, params.provider, params.model]);

  return { state, connect };
}
