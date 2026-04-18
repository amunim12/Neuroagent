"use client";

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
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setAuth(result.access_token, email);
      router.push("/dashboard");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const title = mode === "login" ? "Sign in" : "Create account";
  const submitLabel = mode === "login" ? "Sign in" : "Sign up";
  const altHref = mode === "login" ? "/register" : "/login";
  const altLabel = mode === "login" ? "Need an account? Register" : "Already have an account? Sign in";

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-sm rounded-xl border border-border bg-panel p-8 shadow-lg"
    >
      <h1 className="mb-6 text-2xl font-semibold">{title}</h1>

      <label className="mb-4 block">
        <span className="mb-1 block text-sm text-muted">Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:border-accent"
        />
      </label>

      <label className="mb-6 block">
        <span className="mb-1 block text-sm text-muted">Password</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:border-accent"
        />
      </label>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accentMuted disabled:opacity-50"
      >
        {isSubmitting ? "..." : submitLabel}
      </button>

      <a href={altHref} className="mt-4 block text-center text-sm text-muted hover:text-white">
        {altLabel}
      </a>
    </form>
  );
}
