"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, Eye, EyeOff } from "lucide-react";
import { useSettingsStore } from "@/stores/settings-store";
import { apiClient } from "@/lib/api-client";
import type { LLMProvider } from "@/types";

const PROVIDERS: { value: LLMProvider; label: string; models: string[] }[] = [
  {
    value: "openai",
    label: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
  },
  {
    value: "anthropic",
    label: "Anthropic",
    models: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
  },
  {
    value: "deepseek",
    label: "DeepSeek",
    models: ["deepseek-chat", "deepseek-coder"],
  },
];

export default function SettingsPage() {
  const router = useRouter();
  const { provider, apiKey, model, setProvider, setApiKey, setModel, deviceId } = useSettingsStore();
  const [localKey, setLocalKey] = useState(apiKey);
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const currentProvider = PROVIDERS.find((p) => p.value === provider) || PROVIDERS[0];
  const models = currentProvider.models;

  async function handleSave() {
    if (!localKey.trim()) {
      setError("请输入 API Key");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await apiClient.post("/api/settings", {
        apiKey: localKey,
        provider,
        model,
      });
      setApiKey(localKey);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  function handleProviderChange(val: LLMProvider) {
    setProvider(val);
    const p = PROVIDERS.find((x) => x.value === val);
    if (p && !p.models.includes(model)) {
      setModel(p.models[0]);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 px-6 py-4">
        <div className="mx-auto flex max-w-xl items-center gap-4">
          <button onClick={() => router.push("/")} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            返回
          </button>
          <div className="h-4 w-px bg-border" />
          <h1 className="font-semibold">设置</h1>
        </div>
      </header>

      <main className="mx-auto max-w-xl space-y-8 px-6 py-8">
        <div className="space-y-2">
          <label className="text-sm font-medium">设备 ID</label>
          <p className="rounded-lg bg-muted px-3 py-2 font-mono text-xs text-muted-foreground">
            {deviceId}
          </p>
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium">LLM 提供商</label>
          <div className="grid grid-cols-3 gap-2">
            {PROVIDERS.map((p) => (
              <button
                key={p.value}
                onClick={() => handleProviderChange(p.value)}
                className={`rounded-lg border py-2.5 text-sm font-medium transition-all ${
                  provider === p.value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-input hover:border-primary/50"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium">模型</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
          >
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium">API Key</label>
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              value={localKey}
              onChange={(e) => setLocalKey(e.target.value)}
              placeholder="sk-..."
              className="w-full rounded-lg border border-input bg-background py-2 pl-3 pr-10 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            API Key 将使用 AES-256 加密存储，不会以明文形式保存。
          </p>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {saving ? (
            "保存中..."
          ) : saved ? (
            <>
              <Check className="h-4 w-4" />
              已保存
            </>
          ) : (
            "保存设置"
          )}
        </button>
      </main>
    </div>
  );
}
