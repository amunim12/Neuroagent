"use client";

import { Brain } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/stores/auth";

function readTokenFromStorage(): string | null {
  try {
    const raw = localStorage.getItem("neuroagent-auth");
    if (!raw) return null;
    return (JSON.parse(raw) as { state?: { token?: string | null } })?.state?.token ?? null;
  } catch {
    return null;
  }
}

export default function Home() {
  const router = useRouter();
  const token  = useAuthStore((s) => s.token);

  useEffect(() => {
    // Read localStorage directly so the redirect is correct even before
    // Zustand's persist middleware has finished hydrating.
    const stored = readTokenFromStorage();
    router.replace((token || stored) ? "/dashboard" : "/login");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-base bg-dot-grid">
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-purple-600">
          <Brain className="h-6 w-6 animate-pulse text-white" />
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent to-purple-600 opacity-30 blur-xl" />
        </div>
        <p className="text-sm text-fore-subtle/40">Loading…</p>
      </div>
    </main>
  );
}
