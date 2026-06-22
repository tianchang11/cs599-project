"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Upload, Settings, BookOpen, ChevronRight, Sparkles } from "lucide-react";
import { useSettingsStore } from "@/stores/settings-store";
import { API_BASE_URL, apiClient } from "@/lib/api-client";
import type { ResearchStrategy } from "@/types";

const STRATEGIES: { value: ResearchStrategy; label: string; desc: string }[] = [
  { value: "analytical", label: "深度分析", desc: "多源检索、迭代优化，适合复杂研究" },
  { value: "factual", label: "快速事实", desc: "单轮检索直接回答，适合简单查询" },
  { value: "exploratory", label: "探索发现", desc: "广泛检索发现主题，适合开放式研究" },
  { value: "comparative", label: "对比分析", desc: "对比检索与表格生成，适合比较类查询" },
];

export default function HomePage() {
  const router = useRouter();
  const { apiKey, deviceId } = useSettingsStore();
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [strategy, setStrategy] = useState<ResearchStrategy>("analytical");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    if (!apiKey) {
      setError("请先在设置页面配置 API Key");
      return;
    }
    setLoading(true);
    setError("");
    try {
      let fileId: string | undefined;

      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        const uploadRes = await fetch(`${API_BASE_URL}/api/upload/media`, {
          method: "POST",
          body: formData,
        });
        if (!uploadRes.ok) {
          const errorData = await uploadRes.json().catch(() => null);
          throw new Error(errorData?.detail || "附件上传失败");
        }
        const uploadData = await uploadRes.json();
        fileId = uploadData.fileId;
      }

      const res = await apiClient.post<{ taskId: string }>("/api/research/start", {
        query: query.trim(),
        deviceId,
        fileId,
        strategy,
      });
      router.push(`/research?taskId=${res.taskId}&query=${encodeURIComponent(query.trim())}&strategy=${strategy}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "启动研究失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/60">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Search className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold">DeepResearch</span>
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">v2.0</span>
          </div>
          <nav className="flex items-center gap-4">
            <button
              onClick={() => router.push("/library")}
              className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <BookOpen className="h-4 w-4" />
              我的知识库
            </button>
            <button
              onClick={() => router.push("/settings")}
              className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
              设置
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 pb-16 pt-24">
        <div className="mb-10 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight">
            深度研究，从这里开始
          </h1>
          <p className="text-lg text-muted-foreground">
            输入主题或上传 PDF、图片、音频，让 AI Agent 为你进行全网检索、信息筛选与深度分析
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入你想深入研究的主题，例如：量子计算在金融领域的应用现状与前景..."
              rows={4}
              className="w-full resize-none rounded-xl border border-input bg-background py-3 pl-12 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
            />
          </div>

          <div className="flex items-center gap-3">
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-muted-foreground/50 px-4 py-2 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-primary">
              <Upload className="h-4 w-4" />
              {file ? file.name : "上传 PDF / 图片 / 音频（可选）"}
              <input
                type="file"
                accept=".pdf,image/*,audio/*"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
            {file && (
              <button
                type="button"
                onClick={() => setFile(null)}
                className="text-xs text-muted-foreground hover:text-destructive"
              >
                移除
              </button>
            )}
          </div>

          <div>
            <label className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              研究策略
            </label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {STRATEGIES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setStrategy(s.value)}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    strategy === s.value
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-muted hover:border-muted-foreground/50"
                  }`}
                >
                  <p className="text-sm font-medium">{s.label}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{s.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              "正在启动..."
            ) : (
              <>
                开始深度研究
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            { title: "智能拆解", desc: "将复杂主题分解为多个子查询" },
            { title: "多模态理解", desc: "解析 PDF、图片和音频附件上下文" },
            { title: "质量评估", desc: "自动评估搜索质量并迭代优化" },
          ].map((f) => (
            <div key={f.title} className="rounded-xl bg-muted/50 p-4 text-center">
              <p className="mb-1 text-sm font-medium">{f.title}</p>
              <p className="text-xs text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
