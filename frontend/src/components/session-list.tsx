"use client";

import { CheckCircle2, XCircle, Clock, Loader2, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

function StatusDot({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />;
    case "failed":
      return <XCircle className="h-3.5 w-3.5 text-red-400 shrink-0" />;
    case "running":
      return <Loader2 className="h-3.5 w-3.5 text-accent animate-spin shrink-0" />;
    default:
      return <Clock className="h-3.5 w-3.5 text-fore-subtle/40 shrink-0" />;
  }
}

export function SessionList() {
  const token = useAuthStore((s) => s.token);
  const currentSessionId = useAgentStore((s) => s.sessionId);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions", "recent", currentSessionId],
    queryFn: () => token ? api.listSessions(token) : Promise.resolve({ sessions: [], total: 0 }),
    enabled: Boolean(token),
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => {
      if (!token) return Promise.reject(new Error("Not authenticated"));
      return api.deleteSession(token, id);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sessions"] }),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 animate-shimmer rounded-xl border border-border bg-elevated" />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-xs text-red-400/80">Failed to load sessions</p>;
  }

  if (!data || data.sessions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border px-4 py-6 text-center">
        <p className="text-xs text-fore-subtle/50">No sessions yet</p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-1.5">
      {data.sessions.slice(0, 8).map((session) => {
        const isCurrent = session.id === currentSessionId;
        return (
          <li
            key={session.id}
            className={cn(
              "group card-hover rounded-xl border bg-elevated p-3 text-sm",
              isCurrent ? "border-accent/30 bg-accent/5" : "border-border",
            )}
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <StatusDot status={session.status} />
              <div className="flex items-center gap-2 ml-auto">
                <span className="font-mono text-[10px] text-fore-subtle/40">
                  {new Date(session.created_at).toLocaleDateString()}
                </span>
                <button
                  type="button"
                  onClick={() => { if (confirm("Delete this session?")) deleteMutation.mutate(session.id); }}
                  disabled={deleteMutation.isPending}
                  aria-label="Delete session"
                  className="opacity-0 group-hover:opacity-100 text-fore-subtle/40 hover:text-red-400 transition-all disabled:opacity-20"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
            <p className="line-clamp-2 text-xs leading-relaxed text-fore-muted">{session.goal}</p>
          </li>
        );
      })}
    </ul>
  );
}
