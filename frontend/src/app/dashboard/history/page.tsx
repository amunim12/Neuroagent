"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type SessionSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";

function statusClass(status: string): string {
  const base = "rounded-full border px-2 py-0.5 text-xs font-medium uppercase tracking-wide";
  switch (status) {
    case "completed":
      return `${base} border-emerald-400/40 bg-emerald-400/10 text-emerald-300`;
    case "failed":
      return `${base} border-red-400/40 bg-red-400/10 text-red-300`;
    case "running":
      return `${base} border-accent/40 bg-accent/10 text-accent`;
    case "cancelled":
      return `${base} border-border bg-bg text-muted`;
    default:
      return `${base} border-border bg-bg text-muted`;
  }
}

export default function HistoryPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions", "all"],
    queryFn: () => (token ? api.listSessions(token) : Promise.resolve({ sessions: [], total: 0 })),
    enabled: Boolean(token),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => {
      if (!token) return Promise.reject(new Error("Not authenticated"));
      return api.deleteSession(token, id);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      if (selectedId === id) setSelectedId(null);
    },
  });

  if (!token) return null;

  const sessions = data?.sessions ?? [];
  const selected = sessions.find((session) => session.id === selectedId) ?? null;

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-muted hover:text-white">
            ← Back to agent
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">Session history</h1>
          <p className="text-sm text-muted">
            {data ? `${data.total} total sessions` : "Review past agent runs"}
          </p>
        </div>
      </header>

      {isLoading && <p className="text-sm text-muted">Loading sessions...</p>}
      {error && <p className="text-sm text-red-400">Failed to load sessions</p>}

      {!isLoading && sessions.length === 0 && (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-sm text-muted">
          No sessions yet. Head back to the dashboard and run your first goal.
        </div>
      )}

      {sessions.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
          <SessionGrid
            sessions={sessions}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDelete={(id) => deleteMutation.mutate(id)}
            deletePending={deleteMutation.isPending}
          />

          <div className="min-w-0">
            {selected ? (
              <SessionDetail session={selected} />
            ) : (
              <div className="flex h-full min-h-[16rem] items-center justify-center rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">
                Select a session to see its goal and final result.
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

interface SessionGridProps {
  sessions: SessionSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  deletePending: boolean;
}

function SessionGrid({ sessions, selectedId, onSelect, onDelete, deletePending }: SessionGridProps) {
  return (
    <ul className="flex max-h-[calc(100vh-12rem)] flex-col gap-2 overflow-y-auto pr-1">
      {sessions.map((session) => {
        const isSelected = session.id === selectedId;
        return (
          <li
            key={session.id}
            className={cn(
              "cursor-pointer rounded-lg border bg-panel p-3 text-sm transition",
              isSelected
                ? "border-accent/60 ring-1 ring-accent/40"
                : "border-border hover:border-accent/40",
            )}
            onClick={() => onSelect(session.id)}
          >
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className={statusClass(session.status)}>{session.status}</span>
              <span className="font-mono text-[11px] text-muted">
                {new Date(session.created_at).toLocaleDateString()}
              </span>
            </div>
            <p className="line-clamp-2 text-white/90">{session.goal}</p>
            <div className="mt-2 flex items-center justify-end">
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  if (confirm("Delete this session?")) onDelete(session.id);
                }}
                disabled={deletePending}
                className="text-xs text-muted hover:text-red-400 disabled:opacity-30"
              >
                Delete
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function SessionDetail({ session }: { session: SessionSummary }) {
  const created = new Date(session.created_at);
  const updated = session.updated_at ? new Date(session.updated_at) : null;

  return (
    <article className="flex flex-col gap-5 rounded-xl border border-border bg-panel p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <span className={statusClass(session.status)}>{session.status}</span>
        <div className="text-xs text-muted">
          <p>Started {created.toLocaleString()}</p>
          {updated && <p>Updated {updated.toLocaleString()}</p>}
        </div>
      </header>

      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Goal</h2>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/90">{session.goal}</p>
      </div>

      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Result</h2>
        {session.result ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/90">{session.result}</p>
        ) : (
          <p className="text-sm italic text-muted">
            {session.status === "running"
              ? "Agent is still working on this goal."
              : "No result recorded."}
          </p>
        )}
      </div>

      <footer className="flex items-center gap-2 text-xs text-muted">
        <span>Session ID</span>
        <code className="rounded bg-bg px-2 py-0.5 font-mono text-[11px]">{session.id}</code>
      </footer>
    </article>
  );
}
