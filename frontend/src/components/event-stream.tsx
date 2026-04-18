"use client";

import { useEffect, useRef } from "react";

import { FinalResult } from "@/components/final-result";
import { ToolCallCard } from "@/components/tool-call-card";
import type { AgentEvent } from "@/lib/events";
import { useAgentStore } from "@/stores/agent";

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

function StatusRow({ label, children, tone }: { label: string; children: React.ReactNode; tone: string }) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-border bg-bg/60 px-3 py-2 text-sm">
      <span className={`w-20 shrink-0 text-xs font-semibold uppercase tracking-wide ${tone}`}>{label}</span>
      <div className="flex-1 text-white/80">{children}</div>
    </div>
  );
}

function RenderEvent({ event }: { event: AgentEvent }) {
  switch (event.type) {
    case "tool_call":
      return <ToolCallCard event={event} />;

    case "routing": {
      const model = typeof event.model === "string" ? event.model : "unknown";
      const subtask = typeof event.subtask === "string" ? event.subtask : null;
      return (
        <StatusRow label="Routing" tone="text-purple-300">
          Routed to <span className="font-medium text-white">{model}</span>
          {subtask && <span className="text-muted"> · {subtask}</span>}
        </StatusRow>
      );
    }

    case "thinking": {
      const content =
        typeof event.content === "string"
          ? event.content
          : typeof event.message === "string"
            ? event.message
            : "";
      return (
        <StatusRow label="Thinking" tone="text-yellow-200">
          <span className="italic">{content || "…"}</span>
        </StatusRow>
      );
    }

    case "status": {
      const message = typeof event.message === "string" ? event.message : "";
      return (
        <StatusRow label="Status" tone="text-muted">
          {message}
        </StatusRow>
      );
    }

    case "error": {
      const message = typeof event.message === "string" ? event.message : "Unknown error";
      return (
        <StatusRow label="Error" tone="text-red-400">
          {message}
        </StatusRow>
      );
    }

    case "complete": {
      const message = typeof event.status === "string" ? `Run ${event.status}` : "Run complete";
      return (
        <StatusRow label="Complete" tone="text-emerald-300">
          {message}
        </StatusRow>
      );
    }

    // planning and final_answer are rendered by dedicated components outside the stream
    case "planning":
    case "final_answer":
      return null;

    default:
      return null;
  }
}

export function EventStream() {
  const events = useAgentStore((s) => s.events);
  const status = useAgentStore((s) => s.status);
  const finalAnswer = useAgentStore((s) => s.finalAnswer);
  const errorMessage = useAgentStore((s) => s.errorMessage);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  const visibleEvents = events.filter(
    (event) => event.type !== "planning" && event.type !== "final_answer",
  );

  if (status === "idle" && events.length === 0) {
    return (
      <div className="flex min-h-[12rem] items-center justify-center rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted">
        Enter a goal above to start streaming agent events.
      </div>
    );
  }

  const isStreaming = status === "connecting" || status === "streaming";

  return (
    <div className="flex flex-col gap-4">
      <div
        ref={containerRef}
        className="max-h-[32rem] overflow-y-auto rounded-xl border border-border bg-panel p-4"
      >
        <ul className="flex flex-col gap-3">
          {visibleEvents.map((event, index) => (
            <li key={index} className="flex flex-col gap-1">
              <RenderEvent event={event} />
              <span className="pl-1 font-mono text-[10px] text-muted">{formatTime(event.timestamp)}</span>
            </li>
          ))}
          {isStreaming && (
            <li className="flex items-center gap-2 text-xs text-muted">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
              Agent is working…
            </li>
          )}
        </ul>
      </div>

      {finalAnswer && <FinalResult answer={finalAnswer} />}

      {errorMessage && (
        <div className="rounded-xl border border-red-500/40 bg-panel p-5 text-sm text-red-300">
          {errorMessage}
        </div>
      )}
    </div>
  );
}
