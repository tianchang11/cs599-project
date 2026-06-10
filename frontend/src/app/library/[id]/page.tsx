"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Check, Copy, Download, Edit2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { apiClient } from "@/lib/api-client";

interface NoteDetail {
  id: string;
  title: string;
  content: string;
  sources: string[];
  query: string;
  createdAt: string;
  updatedAt: string;
}

export default function NoteDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");

  const { data: note, isLoading } = useQuery({
    queryKey: ["note", id],
    queryFn: () => apiClient.get<NoteDetail>(`/api/library/${id}`),
  });

  useEffect(() => {
    if (note) setTitle(note.title);
  }, [note]);

  async function handleDelete() {
    if (!confirm("确定删除这篇笔记吗？")) return;
    await apiClient.delete(`/api/library/${id}`);
    router.push("/library");
  }

  function handleCopy() {
    navigator.clipboard.writeText(note?.content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    if (!note) return;
    const blob = new Blob([note.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${note.title}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleSaveTitle() {
    await apiClient.put(`/api/library/${id}`, { title });
    setEditing(false);
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!note) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">笔记不存在</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between border-b bg-card/50 px-6 py-3">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/library")} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            返回知识库
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleCopy} className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm transition-colors hover:bg-muted">
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            {copied ? "已复制" : "复制"}
          </button>
          <button onClick={handleDownload} className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm transition-colors hover:bg-muted">
            <Download className="h-4 w-4" />
            下载
          </button>
          <button onClick={handleDelete} className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm text-destructive transition-colors hover:bg-muted">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          {editing ? (
            <div className="flex flex-1 gap-2">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="flex-1 border-b-2 border-primary bg-transparent text-2xl font-bold focus:outline-none"
                autoFocus
              />
              <button onClick={handleSaveTitle} className="rounded-lg bg-primary px-3 py-1 text-sm text-primary-foreground">保存</button>
              <button onClick={() => setEditing(false)} className="rounded-lg border px-3 py-1 text-sm">取消</button>
            </div>
          ) : (
            <div className="flex flex-1 items-center gap-2">
              <h1 className="text-2xl font-bold">{note.title}</h1>
              <button onClick={() => setEditing(true)} className="rounded p-1.5 transition-colors hover:bg-muted">
                <Edit2 className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          )}
          <div className="shrink-0 text-xs text-muted-foreground">
            {format(new Date(note.createdAt), "yyyy年M月d日 HH:mm", { locale: zhCN })}
          </div>
        </div>

        <article className="prose prose-neutral max-w-none prose-headings:font-bold prose-pre:bg-muted prose-pre:text-sm">
          <ReactMarkdown>{note.content}</ReactMarkdown>
        </article>

        {note.sources.length > 0 && (
          <section className="mt-12 border-t pt-8">
            <h2 className="mb-4 text-lg font-bold">参考来源</h2>
            <ul className="space-y-2">
              {note.sources.map((url, i) => (
                <li key={i}>
                  <a href={url} target="_blank" rel="noopener noreferrer" className="break-all text-sm text-primary hover:underline">
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
