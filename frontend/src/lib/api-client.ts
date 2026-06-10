import { useSettingsStore } from "@/stores/settings-store";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(
      typeof body === "object" && body !== null && "detail" in body
        ? String((body as { detail: string }).detail)
        : `API error ${status}`
    );
  }
}

function getDeviceId(): string {
  if (typeof window === "undefined") return "";
  const store = useSettingsStore.getState();
  return store.deviceId;
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const deviceId = getDeviceId();
  const headers = new Headers(options.headers);

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (deviceId && !headers.has("X-Device-Id")) {
    headers.set("X-Device-Id", deviceId);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiClient = {
  get: <T>(path: string) => api<T>(path),
  post: <T>(path: string, data: unknown) =>
    api<T>(path, { method: "POST", body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) =>
    api<T>(path, { method: "PUT", body: JSON.stringify(data) }),
  delete: <T>(path: string) => api<T>(path, { method: "DELETE" }),
};

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return "请先配置 API Key";
      case 403:
        return "没有权限执行此操作";
      case 404:
        return "资源不存在";
      case 422:
        return "请求参数无效，请检查输入";
      case 429:
        return "请求过于频繁，请稍后再试";
      default:
        return error.message || "发生错误，请重试";
    }
  }
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return "无法连接服务器，请检查网络";
  }
  return error instanceof Error ? error.message : "发生未知错误";
}
