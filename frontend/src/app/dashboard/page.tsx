"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { EventStream } from "@/components/event-stream";
import { GoalInput } from "@/components/goal-input";
import { SessionList } from "@/components/session-list";
import { TaskDecomposition } from "@/components/task-decomposition";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";

export default function DashboardPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const email = useAuthStore((s) => s.email);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const resetAgent = useAgentStore((s) => s.reset);

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  function handleLogout() {
    clearAuth();
    resetAgent();
    router.replace("/login");
  }

  if (!token) return null;

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">NeuroAgent</h1>
          <p className="text-sm text-muted">Give it a goal. Watch it think, plan, search, code, and deliver.</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link
            href="/dashboard/history"
            className="rounded-md border border-border px-3 py-1.5 hover:bg-panel"
          >
            History
          </Link>
          <span className="text-muted">{email}</span>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-md border border-border px-3 py-1.5 hover:bg-panel"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <section className="flex flex-col gap-6">
          <GoalInput />
          <TaskDecomposition />
          <EventStream />
        </section>

        <aside className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Recent sessions</h2>
          <SessionList />
        </aside>
      </div>
    </main>
  );
}
