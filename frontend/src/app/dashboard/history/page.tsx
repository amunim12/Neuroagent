"use client";

import {
  ArrowLeft,
  Brain,
  CheckCircle2,
  Clock,
  History,
  LayoutDashboard,
  Loader2,
  LogOut,
  Trash2,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type SessionSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { AuthGuard } from "@/components/auth-guard";
import { useAuthStore } from "@/stores/auth";

function StatusBadge({ status }: { status: string }) {
  const configs: Record<string, { icon: React.ReactNode; cls: string }> = {
    completed: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      cls: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
    },
    failed: {
      icon: <XCircle className="h-3 w-3" />,
      cls: "border-red-500/25 bg-red-500/10 text-red-300",
    },
    running: {
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      cls: "border-accent/25 bg-accent/10 text-accent-light",
    },
  };
  const cfg = configs[status] ?? {
    icon: <Clock className="h-3 w-3" />,
    cls: "border-border bg-elevated text-fore-subtle",
  };
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium", cfg.cls)}>
      {cfg.icon}
      {status}
    </span>
  );
}

interface NavItemProps { href: string; icon: React.ReactNode; label: string; active: boolean }
function NavItem({ href, icon, label, active }: NavItemProps) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
        active
          ? "bg-accent/10 text-fore font-medium border border-accent/20"
          : "text-fore-subtle hover:bg-elevated hover:text-fore-muted border border-transparent"
      }`}
    >
      <span className={active ? "text-accent-light" : ""}>{icon}</span>
      {label}
    </Link>
  );
}

export default function HistoryPage() {
  const router      = useRouter();
  const pathname    = usePathname();
  const token       = useAuthStore((s) => s.token);
  const email       = useAuthStore((s) => s.email);
  const clearAuth   = useAuthStore((s) => s.clearAuth);
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions", "all"],
    queryFn: () => token ? api.listSessions(token) : Promise.resolve({ sessions: [], total: 0 }),
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

  const sessions = data?.sessions ?? [];
  const selected = sessions.find((s) => s.id === selectedId) ?? null;

  function handleLogout() {
    clearAuth();
    router.replace("/login");
  }

  return (
    <AuthGuard>
    <div className="flex h-screen overflow-hidden bg-base">
      {/* Sidebar */}
      <aside
        className="flex w-64 shrink-0 flex-col border-r border-border bg-panel"
        style={{ boxShadow: "inset -1px 0 0 rgba(255,255,255,0.03)" }}
      >
        <div className="flex items-center gap-3 border-b border-border px-5 py-5">
          <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-purple-600">
            <Brain className="h-4 w-4 text-white" />
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-accent to-purple-600 opacity-30 blur-md" />
          </div>
          <div>
            <p className="gradient-text text-sm font-bold leading-tight">NeuroAgent</p>
            <p className="text-[10px] text-fore-subtle/50 leading-tight">AI Agent Platform</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 px-3 py-4">
          <NavItem href="/dashboard" icon={<LayoutDashboard className="h-4 w-4" />} label="Agent" active={false} />
          <NavItem href="/dashboard/history" icon={<History className="h-4 w-4" />} label="History" active={pathname === "/dashboard/history"} />
        </nav>

        <div className="mx-4 h-px bg-border" />

        <div className="flex-1" />

        <div className="border-t border-border p-4">
          <div className="flex items-center gap-3 rounded-xl border border-border bg-elevated px-3 py-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-xs font-bold text-accent-light uppercase">
              {email?.[0] ?? "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-fore-muted">{email}</p>
            </div>
            <button type="button" onClick={handleLogout} title="Sign out" className="shrink-0 text-fore-subtle/40 hover:text-red-400 transition-colors">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden bg-dot-grid">
        <div
          className="pointer-events-none fixed inset-0 left-64"
          style={{ background: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.06) 0%, transparent 70%)" }}
        />

        <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
          {/* Page header */}
          <div className="border-b border-border bg-panel/50 px-8 py-5">
            <Link href="/dashboard" className="mb-3 flex items-center gap-1.5 text-xs text-fore-subtle/60 hover:text-fore-muted transition-colors">
              <ArrowLeft className="h-3 w-3" />
              Back to agent
            </Link>
            <div className="flex items-end justify-between">
              <div>
                <h1 className="text-xl font-bold text-fore">Session History</h1>
                <p className="mt-0.5 text-sm text-fore-subtle/60">
                  {data ? `${data.total} total runs` : "Browse past agent runs"}
                </p>
              </div>
            </div>
          </div>

          {isLoading && (
            <div className="flex flex-1 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-fore-subtle/40" />
            </div>
          )}

          {error && (
            <div className="m-6 rounded-xl border border-red-500/20 bg-red-500/6 px-5 py-4 text-sm text-red-400">
              Failed to load sessions
            </div>
          )}

          {!isLoading && sessions.length === 0 && (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-elevated">
                <History className="h-7 w-7 text-fore-subtle/30" />
              </div>
              <div>
                <p className="text-sm font-medium text-fore-subtle/60">No sessions yet</p>
                <p className="mt-1 text-xs text-fore-subtle/35">Run your first goal to see it here</p>
              </div>
              <Link
                href="/dashboard"
                className="btn-gradient rounded-xl px-4 py-2 text-xs font-semibold text-white"
              >
                Start a session
              </Link>
            </div>
          )}

          {sessions.length > 0 && (
            <div className="flex min-h-0 flex-1 overflow-hidden">
              {/* Session list */}
              <div className="w-80 shrink-0 overflow-y-auto border-r border-border p-4">
                <div className="flex flex-col gap-1.5">
                  {sessions.map((session) => (
                    <button
                      key={session.id}
                      type="button"
                      onClick={() => setSelectedId(session.id)}
                      className={cn(
                        "card-hover group w-full rounded-xl border p-3.5 text-left transition-all",
                        session.id === selectedId
                          ? "border-accent/30 bg-accent/6"
                          : "border-border bg-elevated hover:border-border-bright",
                      )}
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <StatusBadge status={session.status} />
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-fore-subtle/40">
                            {new Date(session.created_at).toLocaleDateString()}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm("Delete this session?")) deleteMutation.mutate(session.id);
                            }}
                            disabled={deleteMutation.isPending}
                            className="opacity-0 group-hover:opacity-100 text-fore-subtle/30 hover:text-red-400 transition-all"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                      <p className="line-clamp-2 text-xs leading-relaxed text-fore-muted">{session.goal}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Session detail */}
              <div className="flex min-w-0 flex-1 overflow-y-auto p-6">
                {selected ? (
                  <SessionDetail session={selected} />
                ) : (
                  <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border text-center">
                    <p className="text-sm text-fore-subtle/40">Select a session to view details</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
    </AuthGuard>
  );
}

function SessionDetail({ session }: { session: SessionSummary }) {
  const created = new Date(session.created_at);
  const updated = session.updated_at ? new Date(session.updated_at) : null;

  return (
    <article className="w-full animate-slide-up">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <StatusBadge status={session.status} />
        <div className="text-xs text-fore-subtle/40">
          <p>Started {created.toLocaleString()}</p>
          {updated && <p>Updated {updated.toLocaleString()}</p>}
        </div>
      </div>

      <div className="mb-6 rounded-2xl border border-border bg-panel p-5" style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.3)" }}>
        <h2 className="mb-2.5 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/50">Goal</h2>
        <p className="text-sm leading-relaxed text-fore/90 whitespace-pre-wrap">{session.goal}</p>
      </div>

      <div className="rounded-2xl border border-border bg-panel p-5" style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.3)" }}>
        <h2 className="mb-2.5 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/50">Result</h2>
        {session.result ? (
          <p className="text-sm leading-[1.8] text-fore/90 whitespace-pre-wrap">{session.result}</p>
        ) : (
          <p className="text-sm italic text-fore-subtle/50">
            {session.status === "running" ? "Agent is still working…" : "No result recorded."}
          </p>
        )}
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-fore-subtle/30">
        <span>Session ID</span>
        <code className="rounded-lg border border-border bg-elevated px-2 py-0.5 font-mono text-[10px] text-fore-subtle/50">
          {session.id}
        </code>
      </div>
    </article>
  );
}
