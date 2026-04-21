"use client";

import { ChevronDown, ChevronUp, Globe, Terminal, Monitor, Zap } from "lucide-react";
import { useState } from "react";

import type { AgentEvent } from "@/lib/events";
import { cn } from "@/lib/utils";

const TOOL_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string; border: string }> = {
  web_search_tool: {
    label: "Web Search",
    icon: <Globe className="h-3.5 w-3.5" />,
    color: "text-sky-300",
    bg: "bg-sky-500/10",
    border: "border-sky-500/25",
  },
  code_executor_tool: {
    label: "Code",
    icon: <Terminal className="h-3.5 w-3.5" />,
    color: "text-emerald-300",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/25",
  },
  browser_tool: {
    label: "Browser",
    icon: <Monitor className="h-3.5 w-3.5" />,
    color: "text-violet-300",
    bg: "bg-violet-500/10",
    border: "border-violet-500/25",
  },
  api_caller_tool: {
    label: "API Call",
    icon: <Zap className="h-3.5 w-3.5" />,
    color: "text-amber-300",
    bg: "bg-amber-500/10",
    border: "border-amber-500/25",
  },
};

const FALLBACK_TOOL = {
  label: "Tool",
  icon: <Zap className="h-3.5 w-3.5" />,
  color: "text-fore-muted",
  bg: "bg-border",
  border: "border-border",
};

function truncate(v: string, max: number) {
  return v.length <= max ? v : v.slice(0, max) + "…";
}

export function ToolCallCard({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);

  const toolKey = typeof event.tool === "string" ? event.tool : "unknown";
  const config = TOOL_CONFIG[toolKey] ?? FALLBACK_TOOL;
  const model = typeof event.model === "string" ? event.model : null;
  const input = typeof event.input === "string" ? event.input : "";
  const output = typeof event.output === "string" ? event.output : "";
  const subtask = typeof event.subtask === "string" ? event.subtask : null;

  const needsExpand = input.length > 160 || output.length > 240;

  return (
    <div className="animate-flow-in rounded-xl border border-border bg-elevated overflow-hidden">
      {/* Header */}
      <div className={cn("flex items-center gap-2.5 border-b border-border px-4 py-2.5", config.bg)}>
        <div className={cn("flex items-center gap-1.5 rounded-lg px-2 py-1 border text-xs font-semibold", config.color, config.bg, config.border)}>
          {config.icon}
          {config.label}
        </div>
        {model && (
          <span className="rounded-md bg-border/60 px-2 py-0.5 text-[11px] text-fore-subtle font-mono">
            {model}
          </span>
        )}
        {subtask && (
          <span className="ml-auto truncate text-[11px] text-fore-subtle/60 max-w-[200px]" title={subtask}>
            {truncate(subtask, 50)}
          </span>
        )}
      </div>

      {/* Body */}
      <div className="px-4 py-3 flex flex-col gap-3">
        {/* Input */}
        {input && (
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/50">Input</p>
            <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-fore-muted overflow-hidden">
              {expanded ? input : truncate(input, 160)}
            </pre>
          </div>
        )}

        {/* Output */}
        {output && (
          <div>
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/50">Output</p>
            <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-fore overflow-hidden">
              {expanded ? output : truncate(output, 240)}
            </pre>
          </div>
        )}

        {/* Expand toggle */}
        {needsExpand && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 self-start text-[11px] font-medium text-accent-light hover:text-accent transition-colors"
          >
            {expanded ? <><ChevronUp className="h-3 w-3" /> Show less</> : <><ChevronDown className="h-3 w-3" /> Show more</>}
          </button>
        )}
      </div>
    </div>
  );
}
