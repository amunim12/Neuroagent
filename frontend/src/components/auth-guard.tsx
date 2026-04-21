"use client";

import { Brain } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

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

function Spinner() {
  return (
    <div className="flex h-screen items-center justify-center bg-base">
      <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-purple-600">
        <Brain className="h-6 w-6 animate-pulse text-white" />
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent to-purple-600 opacity-30 blur-xl" />
      </div>
    </div>
  );
}

/**
 * Guards pages that require authentication.
 *
 * Always renders a spinner on the first pass (avoids SSR/hydration mismatch),
 * then reads localStorage directly in useEffect so the auth decision is always
 * based on real client-side state — not the null Zustand starts with before
 * its persist middleware has finished hydrating.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const token  = useAuthStore((s) => s.token);

  // `ready` stays false until useEffect confirms we've read client-side state.
  const [ready,         setReady        ] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  // Runs once on the client after first paint — reads localStorage directly.
  useEffect(() => {
    const stored = readTokenFromStorage();
    setAuthenticated(Boolean(stored));
    setReady(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If Zustand hydrates later and surfaces a token, accept it.
  useEffect(() => {
    if (token) setAuthenticated(true);
  }, [token]);

  // Redirect only after we've confirmed client state and found no token.
  useEffect(() => {
    if (ready && !authenticated) router.replace("/login");
  }, [ready, authenticated, router]);

  if (!ready || !authenticated) return <Spinner />;

  return <>{children}</>;
}
