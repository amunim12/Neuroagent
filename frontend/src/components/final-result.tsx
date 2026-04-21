"use client";

import { Check, Copy, Sparkles } from "lucide-react";
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
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard not available
    }
  }

  return (
    <section
      className="animate-slide-up rounded-2xl border border-accent/25 bg-panel overflow-hidden"
      style={{ boxShadow: "0 0 40px rgba(99,102,241,0.12), inset 0 1px 0 rgba(255,255,255,0.05)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-accent/15 bg-accent/5 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent/20">
            <Sparkles className="h-3.5 w-3.5 text-accent-light" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-widest text-accent-light">
            Result
          </span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-xl border border-border/60 bg-elevated px-3 py-1.5 text-xs font-medium text-fore-muted transition hover:border-accent/30 hover:text-fore"
        >
          {copied
            ? <><Check className="h-3 w-3 text-emerald-400" />Copied</>
            : <><Copy className="h-3 w-3" />Copy</>
          }
        </button>
      </div>

      {/* Content */}
      <div className="px-5 py-5">
        <p className="whitespace-pre-wrap break-words text-sm leading-[1.8] text-fore/90">
          {answer}
        </p>
      </div>
    </section>
  );
}
