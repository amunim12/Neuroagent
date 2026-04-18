"use client";

import { useState } from "react";

interface FinalResultProps {
  answer: string;
}

export function FinalResult({ answer }: FinalResultProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error("Failed to copy", err);
    }
  }

  return (
    <section className="rounded-xl border border-accent/40 bg-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-accent">Final answer</h3>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-md border border-border px-2 py-1 text-xs text-muted hover:text-white"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-white/90">{answer}</p>
    </section>
  );
}
