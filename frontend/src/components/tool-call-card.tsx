"use client";

import { useState } from "react";

import type { AgentEvent } from "@/lib/events";

const MODEL_STYLES: Record<string, string> = {
  "gpt-4o": "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  "claude-sonnet": "bg-purple-500/15 text-purple-300 border-purple-500/30",
  "groq-llama3": "bg-orange-500/15 text-orange-300 border-orange-500/30",
};

const TOOL_LABELS: Record<string, string> = {
  web_search_tool: "Web search",
  code_executor_tool: "Code exec",
  browser_tool: "Browser",
  api_caller_tool: "API call",
};

function truncate(value: string, max: number): string {
  if (value.length <= max) return value;
  return value.slice(0, max) + "…";
}

export function ToolCallCard({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);

  const tool = typeof event.tool === "string" ? event.tool : "unknown";
  const toolLabel = TOOL_LABELS[tool] ?? tool;
  const model = typeof event.model === "string" ? event.model : null;
  const input = typeof event.input === "string" ? event.input : "";
  const output = typeof event.output === "string" ? event.output : "";
  const subtask = typeof event.subtask === "string" ? event.subtask : null;

  const modelClass = model ? MODEL_STYLES[model] ?? "bg-white/5 text-white/80 border-white/20" : "";

  return (
    <div className="rounded-lg border border-border bg-bg p-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="rounded-md border border-accent/40 bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
          {toolLabel}
        </span>
        {model && (
          <span className={`rounded-md border px-2 py-0.5 text-xs font-medium ${modelClass}`}>
            {model}
          </span>
        )}
        {subtask && (
          <span className="truncate text-xs text-muted" title={subtask}>
            {truncate(subtask, 60)}
          </span>
        )}
      </div>

      <div className="mb-1">
        <p className="text-xs uppercase tracking-wide text-muted">Input</p>
        <pre className="mt-1 max-h-16 overflow-hidden whitespace-pre-wrap break-words font-mono text-xs text-white/70">
          {expanded ? input : truncate(input, 140)}
        </pre>
      </div>

      {output && (
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Output</p>
          <pre className="mt-1 whitespace-pre-wrap break-words font-mono text-xs text-white/80">
            {expanded ? output : truncate(output, 200)}
          </pre>
        </div>
      )}

      {(input.length > 140 || output.length > 200) && (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="mt-2 text-xs text-accent hover:underline"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}
