"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, BarChart3, BookOpen, Check, Copy, Download, RefreshCw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { createSSEClient } from "@/lib/sse-client";
import { useSettingsStore } from "@/stores/settings-store";
import { API_BASE_URL, apiClient } from "@/lib/api-client";
import { Loading } from "@/components/ui/loading";
import type { ResearchStep, SearchResult, ResearchStrategy } from "@/types";

const STEP_LABELS: Record<string, string> = {
  planning: "意图理解与拆解",
  refining: "搜索策略优化",
  searching: "全网深度检索",
  evaluating: "质量评估与决策",
  filtering: "内容阅读与筛选",
  synthesizing: "交叉验证与综合",
  drafting: "报告撰写中",
  done: "完成",
};

const STEP_ORDER = ["planning", "refining", "searching", "evaluating", "filtering", "synthesizing", "drafting"];

const STRATEGY_LABELS: Record<string, string> = {
  factual: "快速事实",
  analytical: "深度分析",
  exploratory: "探索发现",
  comparative: "对比分析",
};

function ResearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const taskId = searchParams.get("taskId") || "";
  const queryStr = searchParams.get("query") || "";
  const strategyParam = (searchParams.get("strategy") || "analytical") as ResearchStrategy;
  const { deviceId, apiKey, provider, model } = useSettingsStore();

  const [step, setStep] = useState<ResearchStep["step"]>("planning");
  const [message, setMessage] = useState("正在连接...");
  const [report, setReport] = useState("");
  const [sources, setSources] = useState<SearchResult[]>([]);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [classifiedCategory, setClassifiedCategory] = useState<string | null>(null);
  const [iteration, setIteration] = useState(0);
  const [qualityScore, setQualityScore] = useState<number | null>(null);
  const [coverageScore, setCoverageScore] = useState<number | null>(null);
  const [reportQuality, setReportQuality] = useState<number | null>(null);

  useEffect(() => {
    if (!taskId || !apiKey) return;

    const params = new URLSearchParams({
      deviceId,
      apiKey,
      provider,
      model,
    });
    const sse = createSSEClient(`${API_BASE_URL}/api/research/${taskId}/stream?${params.toString()}`);

    sse.connect(
      (event) => {
        switch (event.type) {
          case "step": {
            setStep(event.step as ResearchStep["step"]);
            setMessage(event.message || "");
            const idx = STEP_ORDER.indexOf(event.step || "");
            if (idx >= 0) setCurrentStepIdx(idx);
            break;
          }
          case "classified":
            if (event.category) setClassifiedCategory(event.category);
            break;
          case "quality_update":
            if (event.qualityScore !== undefined) setQualityScore(event.qualityScore);
            if (event.coverageScore !== undefined) setCoverageScore(event.coverageScore);
            if (event.reportQuality !== undefined) setReportQuality(event.reportQuality);
            if (event.iteration !== undefined) setIteration(event.iteration);
            break;
          case "report":
            setReport((prev) => prev + (event.content || ""));
            break;
          case "sources":
            if (event.sources) setSources(event.sources as SearchResult[]);
            break;
          case "done":
            setStep("done");
            break;
          case "error":
            setError(event.error || "未知错误");
            break;
        }
      },
      (err) => setError(err.message)
    );

    return () => sse.disconnect();
  }, [taskId, deviceId, apiKey, provider, model]);

  async function handleSave() {
    if (!report || saved) return;
    try {
      await apiClient.post("/api/library", {
        title: extractTitle(report) || "未命名报告",
        content: report,
        sources: sources.map((s) => s.url),
        query: queryStr,
        deviceId,
      });
      setSaved(true);
    } catch {
      setError("保存失败");
    }
  }

  function extractTitle(md: string): string {
    const match = md.match(/^#\s+(.+)/m);
    return match?.[1] || "";
  }

  function handleCopy() {
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${extractTitle(report) || "研究报告"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex shrink-0 items-center gap-4 border-b bg-card/50 px-6 py-3">
        <button onClick={() => router.push("/")} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          返回
        </button>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-medium">研究任务</span>
        {taskId && <span className="font-mono text-xs text-muted-foreground">{taskId.slice(0, 12)}...</span>}
        {strategyParam && (
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
            {STRATEGY_LABELS[strategyParam] || strategyParam}
          </span>
        )}
        {classifiedCategory && classifiedCategory !== strategyParam && (
          <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-600">
            自动识别: {STRATEGY_LABELS[classifiedCategory] || classifiedCategory}
          </span>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden w-64 shrink-0 overflow-auto border-r bg-card/30 p-6 md:block">
          <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">研究进度</h3>
          <ol className="space-y-3">
            {STEP_ORDER.map((s, i) => (
              <li key={s} className="flex items-center gap-3 text-sm">
                <div
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    i < currentStepIdx
                      ? "bg-primary text-primary-foreground"
                      : i === currentStepIdx
                        ? "border border-primary bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i < currentStepIdx ? "✓" : i + 1}
                </div>
                <span className={i <= currentStepIdx ? "text-foreground" : "text-muted-foreground"}>
                  {STEP_LABELS[s]}
                </span>
              </li>
            ))}
          </ol>

          {iteration > 0 && (
            <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-3">
              <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-primary">
                <RefreshCw className="h-3 w-3" />
                迭代轮次: {iteration}
              </div>
            </div>
          )}

          {(qualityScore !== null || coverageScore !== null || reportQuality !== null) && (
            <div className="mt-4 rounded-lg bg-muted/50 p-3">
              <div className="mb-2 flex items-center gap-1.5 text-xs font-medium">
                <BarChart3 className="h-3 w-3" />
                质量评分
              </div>
              {qualityScore !== null && (
                <div className="mb-1 text-xs text-muted-foreground">搜索质量: {qualityScore.toFixed(1)}/10</div>
              )}
              {coverageScore !== null && (
                <div className="mb-1 text-xs text-muted-foreground">覆盖度: {coverageScore.toFixed(1)}/10</div>
              )}
              {reportQuality !== null && (
                <div className="text-xs text-muted-foreground">报告质量: {reportQuality.toFixed(1)}/10</div>
              )}
            </div>
          )}

          {message && step !== "done" && (
            <p className="mt-6 text-xs leading-relaxed text-muted-foreground">{message}</p>
          )}
          {step === "done" && (
            <p className="mt-6 text-xs font-medium text-green-600">所有步骤已完成</p>
          )}
        </aside>

        <main className="flex-1 overflow-auto">
          {error ? (
            <div className="p-8 text-center">
              <p className="mb-4 text-destructive">{error}</p>
              <button onClick={() => router.push("/")} className="text-sm text-primary hover:underline">返回首页重试</button>
            </div>
          ) : !report && step !== "done" ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <p className="text-sm text-muted-foreground">{message}</p>
                {classifiedCategory && (
                  <p className="mt-2 text-xs text-primary">
                    策略: {STRATEGY_LABELS[classifiedCategory] || classifiedCategory}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-4xl p-8">
              {report && (
                <article className="prose prose-neutral max-w-none prose-headings:font-bold prose-headings:tracking-tight prose-a:text-primary prose-li:my-1 prose-pre:bg-muted prose-pre:text-sm">
                  <ReactMarkdown>{report}</ReactMarkdown>
                </article>
              )}

              {sources.length > 0 && (
                <section className="mt-12 border-t pt-8">
                  <h2 className="mb-4 text-lg font-bold">参考来源</h2>
                  <ul className="space-y-2">
                    {sources.map((s, i) => (
                      <li key={i} className="flex gap-2 text-sm">
                        <span className="shrink-0 text-muted-foreground">{i + 1}.</span>
                        <a href={s.url} target="_blank" rel="noopener noreferrer" className="break-all text-primary hover:underline">
                          {s.title || s.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </main>
      </div>

      {step === "done" && report && (
        <footer className="flex shrink-0 items-center justify-between border-t bg-card/50 px-6 py-3">
          <span className="text-sm text-muted-foreground">
            报告生成完毕 · {report.length} 字
            {reportQuality !== null && ` · 质量 ${reportQuality.toFixed(1)}/10`}
          </span>
          <div className="flex items-center gap-2">
            <button onClick={handleCopy} className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm transition-colors hover:bg-muted">
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              {copied ? "已复制" : "复制全文"}
            </button>
            <button onClick={handleDownload} className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm transition-colors hover:bg-muted">
              <Download className="h-4 w-4" />
              下载 Markdown
            </button>
            <button onClick={handleSave} disabled={saved} className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50">
              <BookOpen className="h-4 w-4" />
              {saved ? "已保存" : "保存到知识库"}
            </button>
          </div>
        </footer>
      )}
    </div>
  );
}

export default function ResearchPage() {
  return (
    <Suspense fallback={<Loading fullScreen message="加载中..." />}>
      <ResearchContent />
    </Suspense>
  );
}
