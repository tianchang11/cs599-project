import type { SSEEvent } from "@/types";

export function createSSEClient(url: string) {
  let controller: AbortController | null = null;
  let eventSource: EventSource | null = null;

  function parseEvent(data: string): SSEEvent {
    try {
      return JSON.parse(data) as SSEEvent;
    } catch {
      return { type: "error", error: "Failed to parse SSE data" };
    }
  }

  function connect(
    onEvent: (event: SSEEvent) => void,
    onError?: (err: Error) => void
  ) {
    controller = new AbortController();

    eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      if (e.data === "[DONE]") {
        onEvent({ type: "done" });
        return;
      }
      onEvent(parseEvent(e.data));
    };

    eventSource.onerror = (e) => {
      onError?.(new Error("SSE connection error"));
      eventSource?.close();
    };
  }

  function disconnect() {
    controller?.abort();
    eventSource?.close();
  }

  return { connect, disconnect };
}
