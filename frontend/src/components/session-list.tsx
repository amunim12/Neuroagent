"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";

export function SessionList() {
  const token = useAuthStore((s) => s.token);
  const currentSessionId = useAgentStore((s) => s.sessionId);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions", "recent", currentSessionId],
    queryFn: () => (token ? api.listSessions(token) : Promise.resolve({ sessions: [], total: 0 })),
    enabled: Boolean(token),
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => {
      if (!token) return Promise.reject(new Error("Not authenticated"));
      return api.deleteSession(token, id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });

  if (isLoading) return <p className="text-sm text-muted">Loading sessions...</p>;
  if (error) return <p className="text-sm text-red-400">Failed to load sessions</p>;
  if (!data || data.sessions.length === 0) {
    return <p className="text-sm text-muted">No sessions yet.</p>;
  }

  const recent = data.sessions.slice(0, 6);

  return (
    <ul className="flex flex-col gap-2">
      {recent.map((session) => (
        <li key={session.id} className="group rounded-md border border-border bg-panel p-3 text-sm">
          <div className="mb-1 flex items-center justify-between">
            <span className={statusClass(session.status)}>{session.status}</span>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted">
                {new Date(session.created_at).toLocaleDateString()}
              </span>
              <button
                type="button"
                onClick={() => {
                  if (confirm("Delete this session?")) deleteMutation.mutate(session.id);
                }}
                disabled={deleteMutation.isPending}
                aria-label="Delete session"
                className="text-xs text-muted opacity-0 transition group-hover:opacity-100 hover:text-red-400 disabled:opacity-30"
              >
                ✕
              </button>
            </div>
          </div>
          <p className="line-clamp-2 text-white/90">{session.goal}</p>
        </li>
      ))}
    </ul>
  );
}

function statusClass(status: string): string {
  const base = "text-xs font-semibold uppercase tracking-wide";
  switch (status) {
    case "completed":
      return `${base} text-emerald-300`;
    case "failed":
      return `${base} text-red-400`;
    case "running":
      return `${base} text-accent`;
    case "cancelled":
      return `${base} text-muted`;
    default:
      return `${base} text-muted`;
  }
}
