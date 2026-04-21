"use client";

import { Brain, Eye, EyeOff, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const result = mode === "login"
        ? await api.login(email, password)
        : await api.register(email, password);
      setAuth(result.access_token, email);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setIsSubmitting(false);
    }
  }

  const isLogin = mode === "login";

  return (
    <div className="w-full max-w-sm animate-slide-up">
      {/* Brand */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-purple-600">
          <Brain className="h-7 w-7 text-white" />
          <div className="absolute inset-0 rounded-2xl opacity-50 blur-xl bg-gradient-to-br from-accent to-purple-600" />
        </div>
        <div className="text-center">
          <h1 className="gradient-text text-2xl font-bold tracking-tight">NeuroAgent</h1>
          <p className="mt-1 text-sm text-fore-subtle">
            {isLogin ? "Welcome back" : "Start building with AI"}
          </p>
        </div>
      </div>

      {/* Card */}
      <div
        className="rounded-2xl border border-border bg-panel p-7"
        style={{ boxShadow: "0 8px 64px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.05)" }}
      >
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* Email */}
          <div className="flex flex-col gap-2">
            <label htmlFor="email" className="text-xs font-semibold uppercase tracking-widest text-fore-subtle">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
              className="w-full rounded-xl border border-border bg-elevated px-4 py-3 text-sm text-fore placeholder:text-fore-subtle/40 outline-none transition-all focus:border-accent/50 focus:bg-base focus:shadow-glow-sm"
            />
          </div>

          {/* Password */}
          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-xs font-semibold uppercase tracking-widest text-fore-subtle">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete={isLogin ? "current-password" : "new-password"}
                placeholder="Min. 8 characters"
                className="w-full rounded-xl border border-border bg-elevated px-4 py-3 pr-11 text-sm text-fore placeholder:text-fore-subtle/40 outline-none transition-all focus:border-accent/50 focus:bg-base focus:shadow-glow-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-fore-subtle/60 hover:text-fore-muted transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting || !email || !password}
            className="btn-gradient mt-1 flex h-12 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white"
          >
            {isSubmitting
              ? <><Loader2 className="h-4 w-4 animate-spin" />{isLogin ? "Signing in…" : "Creating account…"}</>
              : isLogin ? "Sign in" : "Create account"
            }
          </button>
        </form>

        <div className="mt-5 text-center">
          <a
            href={isLogin ? "/register" : "/login"}
            className="text-sm text-fore-subtle hover:text-fore-muted transition-colors"
          >
            {isLogin ? "No account yet? " : "Already have an account? "}
            <span className="font-medium text-accent-light hover:text-accent">{isLogin ? "Register" : "Sign in"}</span>
          </a>
        </div>
      </div>

      <p className="mt-5 text-center text-xs text-fore-subtle/50">
        Autonomous AI powered by LangGraph + Groq
      </p>
    </div>
  );
}
