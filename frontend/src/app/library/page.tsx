"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, BookOpen, Download, LayoutGrid, List, Search, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { apiClient } from "@/lib/api-client";
import { useSettingsStore } from "@/stores/settings-store";
import type { Note } from "@/types";

export default function LibraryPage() {
  const router = useRouter();
  const { deviceId } = useSettingsStore();
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const queryClient = useQueryClient();

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ["library", deviceId],
    queryFn: () => apiClient.get<Note[]>(`/api/library?deviceId=${deviceId}`),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/library/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library"] }),
  });

  const filtered = notes.filter((n) =>
    !search ||
    n.title.toLowerCase().includes(search.toLowerCase()) ||
    n.content.toLowerCase().includes(search.toLowerCase())
  );

  function handleExport(note: Note) {
    const blob = new Blob([note.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${note.title}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function extractSummary(content: string): string {
    const cleaned = content
      .replace(/^#.*$/gm, "")
      .replace(/```[\s\S]*?```/g, "")
      .replace(/\[.*?\]\(.*?\)/g, "")
      .trim();
    return cleaned.slice(0, 200) + (cleaned.length > 200 ? "..." : "");
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => router.push("/")} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" />
              返回
            </button>
            <div className="h-4 w-px bg-border" />
            <h1 className="font-semibold">我的知识库</h1>
          </div>
          <span className="text-sm text-muted-foreground">{filtered.length} 篇笔记</span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="relative max-w-sm flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索笔记标题或内容..."
              className="w-full rounded-lg border border-input bg-background py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
            />
          </div>
          <div className="flex items-center gap-1 rounded-lg border p-1">
            <button onClick={() => setView("grid")} className={`rounded p-1.5 ${view === "grid" ? "bg-muted" : ""}`}>
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button onClick={() => setView("list")} className={`rounded p-1.5 ${view === "list" ? "bg-muted" : ""}`}>
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center">
            <BookOpen className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-muted-foreground">
              {search ? "没有找到匹配的笔记" : "知识库为空，开始研究生成你的第一篇报告吧"}
            </p>
            <button onClick={() => router.push("/")} className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90">
              开始研究
            </button>
          </div>
        ) : view === "grid" ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((note) => (
              <div
                key={note.id}
                className="group relative cursor-pointer rounded-xl border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-sm"
                onClick={() => router.push(`/library/${note.id}`)}
              >
                <h3 className="mb-2 line-clamp-2 text-sm font-semibold">{note.title}</h3>
                <p className="mb-3 line-clamp-3 text-xs text-muted-foreground">
                  {extractSummary(note.content)}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(note.createdAt), "yyyy年M月d日", { locale: zhCN })}
                  </span>
                  <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button onClick={(e) => { e.stopPropagation(); handleExport(note); }} className="rounded p-1.5 hover:bg-muted" title="导出">
                      <Download className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(note.id); }} className="rounded p-1.5 hover:bg-muted" title="删除">
                      <Trash2 className="h-3.5 w-3.5 text-destructive" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((note) => (
              <div
                key={note.id}
                className="flex cursor-pointer items-center gap-4 rounded-xl border bg-card p-4 transition-colors hover:border-primary/50"
                onClick={() => router.push(`/library/${note.id}`)}
              >
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-sm font-medium">{note.title}</h3>
                  <p className="truncate text-xs text-muted-foreground">{note.query}</p>
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {format(new Date(note.createdAt), "yyyy/MM/dd", { locale: zhCN })}
                </span>
                <div className="flex shrink-0 items-center gap-1">
                  <button onClick={(e) => { e.stopPropagation(); handleExport(note); }} className="rounded p-1.5 hover:bg-muted">
                    <Download className="h-4 w-4 text-muted-foreground" />
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(note.id); }} className="rounded p-1.5 hover:bg-muted">
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
