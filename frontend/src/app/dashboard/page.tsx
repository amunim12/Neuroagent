"use client";

import { Brain, History, LayoutDashboard, LogOut, ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useRef } from "react";

import { AuthGuard } from "@/components/auth-guard";
import { EventStream } from "@/components/event-stream";
import { GoalInput } from "@/components/goal-input";
import { SessionList } from "@/components/session-list";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";

function NavItem({
  href,
  icon,
  label,
  active,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
}) {
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
      {active && <ChevronRight className="ml-auto h-3.5 w-3.5 text-accent/60" />}
    </Link>
  );
}

export default function DashboardPage() {
  const router     = useRouter();
  const pathname   = usePathname();
  const email      = useAuthStore((s) => s.email);
  const clearAuth  = useAuthStore((s) => s.clearAuth);
  const resetAgent = useAgentStore((s) => s.reset);
  const setGoalRef = useRef<((text: string) => void) | null>(null);

  function handleLogout() {
    clearAuth();
    resetAgent();
    router.replace("/login");
  }

  const handleExampleClick = useCallback((prompt: string) => {
    setGoalRef.current?.(prompt);
  }, []);

  return (
    <AuthGuard>
    <div className="flex h-screen overflow-hidden bg-base">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside
        className="flex w-64 shrink-0 flex-col border-r border-border bg-panel"
        style={{ boxShadow: "inset -1px 0 0 rgba(255,255,255,0.03)" }}
      >
        {/* Logo */}
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

        {/* New chat button */}
        <div className="px-3 py-3">
          <button
            type="button"
            onClick={() => resetAgent()}
            className="w-full rounded-xl border border-border/60 bg-elevated px-3 py-2.5 text-xs font-medium text-fore-muted transition hover:border-border-bright hover:text-fore"
          >
            + New session
          </button>
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 px-3 pb-3">
          <NavItem href="/dashboard" icon={<LayoutDashboard className="h-4 w-4" />} label="Agent" active={pathname === "/dashboard"} />
          <NavItem href="/dashboard/history" icon={<History className="h-4 w-4" />} label="History" active={false} />
        </nav>

        {/* Divider */}
        <div className="mx-4 h-px bg-border" />

        {/* Recent sessions */}
        <div className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-hidden px-3 py-4">
          <p className="px-1 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/40">
            Recent Sessions
          </p>
          <div className="min-h-0 flex-1 overflow-y-auto">
            <SessionList />
          </div>
        </div>

        {/* User footer */}
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2.5 rounded-xl border border-border bg-elevated px-3 py-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-xs font-bold uppercase text-accent-light">
              {email?.[0] ?? "U"}
            </div>
            <p className="min-w-0 flex-1 truncate text-xs font-medium text-fore-subtle">{email}</p>
            <button
              type="button"
              onClick={handleLogout}
              title="Sign out"
              className="shrink-0 text-fore-subtle/30 transition hover:text-red-400"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Chat area ────────────────────────────────────────────────────── */}
      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden bg-dot-grid">
        {/* Radial top glow */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-64 z-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 100% at 50% 0%, rgba(99,102,241,0.07) 0%, transparent 70%)",
          }}
        />

        {/* Scrollable messages */}
        <div className="relative z-10 flex-1 overflow-hidden">
          <EventStream onExampleClick={handleExampleClick} />
        </div>

        {/* Fixed bottom input */}
        <div className="relative z-10 shrink-0">
          <GoalInputWithRef setGoalRef={setGoalRef} />
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}

/* ─── Thin wrapper so example-prompt clicks can pre-fill the textarea ─── */
function GoalInputWithRef({
  setGoalRef,
}: {
  setGoalRef: React.MutableRefObject<((text: string) => void) | null>;
}) {
  return <GoalInput externalSetGoal={setGoalRef} />;
}
