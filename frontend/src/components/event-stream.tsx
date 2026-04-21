"use client";

import {
  Brain,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  Globe,
  Loader2,
  Monitor,
  Network,
  Sparkles,
  Terminal,
  Zap,
  AlertTriangle,
  ListTodo,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { AgentEvent } from "@/lib/events";
import { cn } from "@/lib/utils";
import { useAgentStore } from "@/stores/agent";

/* ─── Avatar ───────────────────────────────────────────────────────────── */
function AgentAvatar({ size = "md" }: { size?: "sm" | "md" }) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-purple-600",
        size === "sm" ? "h-6 w-6" : "h-8 w-8",
      )}
    >
      <Brain className={cn("text-white", size === "sm" ? "h-3 w-3" : "h-4 w-4")} />
    </div>
  );
}

/* ─── Welcome / empty state ─────────────────────────────────────────────── */
const EXAMPLE_PROMPTS = [
  "Research the latest breakthroughs in AI safety",
  "Write a Python script to scrape Hacker News",
  "Summarize the top papers in quantum computing",
  "Compare LangChain vs LlamaIndex for RAG",
];

function WelcomeScreen({ onPrompt }: { onPrompt: (p: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-8 px-6 py-20 text-center">
      {/* Brand mark */}
      <div className="relative">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-purple-600">
          <Brain className="h-8 w-8 text-white" />
        </div>
        <div
          className="absolute inset-0 rounded-2xl bg-gradient-to-br from-accent to-purple-600 opacity-25 blur-xl"
          aria-hidden
        />
      </div>

      <div>
        <h2 className="gradient-text text-3xl font-bold tracking-tight">NeuroAgent</h2>
        <p className="mt-2 text-base text-fore-subtle/60">
          Give it a goal — it plans, searches, codes, and delivers.
        </p>
      </div>

      {/* Example prompts */}
      <div className="grid w-full max-w-xl grid-cols-2 gap-2.5">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onPrompt(prompt)}
            className="card-hover rounded-xl border border-border bg-panel px-4 py-3.5 text-left text-xs text-fore-muted transition hover:text-fore"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─── User message ──────────────────────────────────────────────────────── */
function UserMessage({ text }: { text: string }) {
  return (
    <div className="flex justify-end px-4 animate-slide-up">
      <div
        className="max-w-[78%] rounded-2xl rounded-br-sm border border-accent/20 bg-accent/10 px-5 py-3.5"
        style={{ boxShadow: "0 2px 12px rgba(99,102,241,0.12)" }}
      >
        <p className="text-sm leading-relaxed text-fore">{text}</p>
      </div>
    </div>
  );
}

/* ─── Agent bubble wrapper ──────────────────────────────────────────────── */
function AgentBubble({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className="flex items-start gap-3 px-4 animate-slide-up">
      <AgentAvatar />
      <div className={cn("flex-1 min-w-0", className)}>
        {children}
      </div>
    </div>
  );
}

/* ─── Planning message ─────────────────────────────────────────────────── */
function PlanningMessage({ events, finalAnswer }: { events: AgentEvent[]; finalAnswer: string | null }) {
  const planningEvent = events.find((e) => e.type === "planning");
  if (!planningEvent) return null;

  const subtasks = Array.isArray(planningEvent.subtasks)
    ? (planningEvent.subtasks as unknown[]).filter((t): t is string => typeof t === "string")
    : [];
  const reasoning = typeof planningEvent.reasoning === "string" ? planningEvent.reasoning : null;
  if (subtasks.length === 0) return null;

  const lastRouting = [...events].reverse().find((e) => e.type === "routing");
  const activeSubtask = typeof lastRouting?.subtask === "string" ? lastRouting.subtask : null;
  const activeIndex = activeSubtask ? subtasks.indexOf(activeSubtask) : -1;
  const completedCount = finalAnswer !== null ? subtasks.length : activeIndex >= 0 ? activeIndex : 0;

  return (
    <AgentBubble>
      <div
        className="rounded-2xl rounded-tl-sm border border-border bg-panel p-5"
        style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03)" }}
      >
        <div className="mb-4 flex items-center gap-2">
          <ListTodo className="h-4 w-4 text-violet-400" />
          <span className="text-xs font-semibold uppercase tracking-widest text-fore-subtle/70">
            Task Plan
          </span>
          <span className="ml-auto text-xs text-fore-subtle/40">
            {completedCount}/{subtasks.length}
          </span>
        </div>

        {reasoning && (
          <p className="mb-4 border-l-2 border-accent/25 pl-3 text-sm italic leading-relaxed text-fore-muted">
            {reasoning}
          </p>
        )}

        {/* Progress */}
        <div className="mb-4 h-0.5 overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent to-purple-500 transition-all duration-700"
            style={{ width: `${(completedCount / subtasks.length) * 100}%` }}
          />
        </div>

        <ol className="flex flex-col gap-2.5">
          {subtasks.map((task, i) => {
            const isComplete = finalAnswer !== null || (activeIndex >= 0 && i < activeIndex);
            const isActive = !finalAnswer && i === activeIndex;
            return (
              <li key={i} className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">
                  {isComplete ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/12">
                      <Check className="h-2.5 w-2.5 text-emerald-400" strokeWidth={3} />
                    </div>
                  ) : isActive ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full border border-accent/40 bg-accent/12">
                      <Loader2 className="h-2.5 w-2.5 animate-spin text-accent" />
                    </div>
                  ) : (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full border border-border">
                      <span className="font-mono text-[9px] text-fore-subtle/50">{i + 1}</span>
                    </div>
                  )}
                </div>
                <span
                  className={cn(
                    "text-sm leading-relaxed",
                    isComplete && "text-fore-subtle/50 line-through decoration-fore-subtle/20",
                    isActive && "font-medium text-fore",
                    !isComplete && !isActive && "text-fore-subtle/70",
                  )}
                >
                  {task}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </AgentBubble>
  );
}

/* ─── Tool call message ─────────────────────────────────────────────────── */
const TOOL_CONFIG: Record<string, { icon: React.ReactNode; label: string; color: string; border: string; bg: string }> = {
  web_search_tool:   { icon: <Globe className="h-3.5 w-3.5" />,    label: "Web Search",  color: "text-sky-300",     border: "border-sky-500/20",    bg: "bg-sky-500/8"    },
  code_executor_tool:{ icon: <Terminal className="h-3.5 w-3.5" />, label: "Code",        color: "text-emerald-300", border: "border-emerald-500/20",bg: "bg-emerald-500/8"},
  browser_tool:      { icon: <Monitor className="h-3.5 w-3.5" />,  label: "Browser",     color: "text-violet-300",  border: "border-violet-500/20", bg: "bg-violet-500/8" },
  api_caller_tool:   { icon: <Zap className="h-3.5 w-3.5" />,      label: "API Call",    color: "text-amber-300",   border: "border-amber-500/20",  bg: "bg-amber-500/8"  },
};

function ToolCallMessage({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);
  const toolKey = typeof event.tool === "string" ? event.tool : "unknown";
  const cfg = TOOL_CONFIG[toolKey] ?? { icon: <Zap className="h-3.5 w-3.5" />, label: toolKey, color: "text-fore-muted", border: "border-border", bg: "bg-elevated" };
  const input  = typeof event.input  === "string" ? event.input  : "";
  const output = typeof event.output === "string" ? event.output : "";
  const truncate = (s: string, n: number) => s.length > n ? s.slice(0, n) + "…" : s;
  const needsExpand = input.length > 180 || output.length > 280;

  return (
    <AgentBubble>
      <div
        className={cn("rounded-2xl rounded-tl-sm border overflow-hidden", cfg.border)}
        style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.25)" }}
      >
        {/* Tool header */}
        <div className={cn("flex items-center gap-2 px-4 py-2.5 border-b", cfg.bg, cfg.border)}>
          <span className={cn("flex items-center gap-1.5 text-xs font-semibold", cfg.color)}>
            {cfg.icon} {cfg.label}
          </span>
          {typeof event.model === "string" && (
            <span className="ml-auto rounded-md bg-border/60 px-2 py-0.5 font-mono text-[10px] text-fore-subtle/50">
              {event.model}
            </span>
          )}
        </div>

        {/* Body */}
        <div className="bg-elevated px-4 py-3.5 flex flex-col gap-3">
          {input && (
            <div>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/35">Input</p>
              <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-fore-subtle">
                {expanded ? input : truncate(input, 180)}
              </pre>
            </div>
          )}
          {output && (
            <div>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-fore-subtle/35">Output</p>
              <pre className="whitespace-pre-wrap break-all font-mono text-[11px] leading-relaxed text-fore-muted">
                {expanded ? output : truncate(output, 280)}
              </pre>
            </div>
          )}
          {needsExpand && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="flex items-center gap-1 self-start text-[11px] font-medium text-accent-light hover:text-accent transition-colors"
            >
              {expanded ? <><ChevronUp className="h-3 w-3" />Show less</> : <><ChevronDown className="h-3 w-3" />Show more</>}
            </button>
          )}
        </div>
      </div>
    </AgentBubble>
  );
}

/* ─── Routing row ───────────────────────────────────────────────────────── */
function RoutingRow({ event }: { event: AgentEvent }) {
  const model = typeof event.model === "string" ? event.model : "unknown";
  return (
    <div className="flex items-center gap-3 px-4 py-1 animate-fade-in">
      <div className="h-px flex-1 bg-border/50" />
      <span className="flex items-center gap-1.5 text-[11px] text-fore-subtle/35">
        <Network className="h-3 w-3" />
        {model}
      </span>
      <div className="h-px flex-1 bg-border/50" />
    </div>
  );
}

/* ─── Thinking row ──────────────────────────────────────────────────────── */
function ThinkingRow({ event }: { event: AgentEvent }) {
  const content = typeof event.content === "string" ? event.content
    : typeof event.message === "string" ? event.message : "…";
  return (
    <AgentBubble>
      <p className="border-l-2 border-fore-subtle/15 pl-3 text-xs italic leading-relaxed text-fore-subtle/50">
        {content}
      </p>
    </AgentBubble>
  );
}

/* ─── Final answer ──────────────────────────────────────────────────────── */
function FinalAnswerMessage({ answer }: { answer: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(answer).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <AgentBubble className="animate-slide-up">
      <div
        className="rounded-2xl rounded-tl-sm border border-accent/20 bg-panel overflow-hidden"
        style={{ boxShadow: "0 0 32px rgba(99,102,241,0.1), 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-accent/12 bg-accent/5 px-5 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-accent-light" />
            <span className="text-xs font-semibold uppercase tracking-widest text-accent-light/80">Result</span>
          </div>
          <button
            type="button"
            onClick={copy}
            className="flex items-center gap-1.5 rounded-xl border border-border/50 bg-elevated px-3 py-1.5 text-[11px] font-medium text-fore-subtle transition hover:border-border-bright hover:text-fore"
          >
            {copied ? <><Check className="h-3 w-3 text-emerald-400" />Copied</> : <><Copy className="h-3 w-3" />Copy</>}
          </button>
        </div>
        {/* Content */}
        <div className="px-5 py-5">
          <p className="whitespace-pre-wrap break-words text-sm leading-[1.85] text-fore/90">{answer}</p>
        </div>
      </div>
    </AgentBubble>
  );
}

/* ─── Error message ─────────────────────────────────────────────────────── */
function ErrorMessage({ message }: { message: string }) {
  return (
    <AgentBubble>
      <div className="flex items-start gap-3 rounded-2xl rounded-tl-sm border border-red-500/20 bg-red-500/6 px-5 py-4">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
        <p className="text-sm text-red-300">{message}</p>
      </div>
    </AgentBubble>
  );
}

/* ─── Working indicator ─────────────────────────────────────────────────── */
function WorkingIndicator() {
  return (
    <div className="flex items-center gap-3 px-4 animate-fade-in">
      <AgentAvatar size="sm" />
      <div className="flex items-center gap-1">
        <span className="working-dot h-2 w-2 rounded-full bg-accent/70" />
        <span className="working-dot h-2 w-2 rounded-full bg-accent/70" />
        <span className="working-dot h-2 w-2 rounded-full bg-accent/70" />
      </div>
    </div>
  );
}

/* ─── Completion pill ───────────────────────────────────────────────────── */
function CompletionPill() {
  return (
    <div className="flex justify-center px-4 animate-fade-in">
      <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/6 px-3 py-1 text-[11px] font-medium text-emerald-400">
        <CheckCircle2 className="h-3 w-3" /> Completed
      </span>
    </div>
  );
}

/* ─── Main EventStream ──────────────────────────────────────────────────── */
export function EventStream({ onExampleClick }: { onExampleClick?: (p: string) => void }) {
  const events    = useAgentStore((s) => s.events);
  const status    = useAgentStore((s) => s.status);
  const goal      = useAgentStore((s) => s.goal);
  const finalAnswer  = useAgentStore((s) => s.finalAnswer);
  const errorMessage = useAgentStore((s) => s.errorMessage);
  const containerRef = useRef<HTMLDivElement>(null);

  const isStreaming = status === "connecting" || status === "streaming";
  const isIdle      = status === "idle" && events.length === 0;

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length, finalAnswer]);

  if (isIdle) {
    return (
      <div ref={containerRef} className="h-full overflow-y-auto">
        <WelcomeScreen onPrompt={onExampleClick ?? (() => {})} />
      </div>
    );
  }

  // Separate events into categories
  const hasPlanning   = events.some((e) => e.type === "planning");
  const streamEvents  = events.filter(
    (e) => e.type !== "planning" && e.type !== "final_answer" && e.type !== "complete",
  );
  const isComplete    = events.some((e) => e.type === "complete");

  return (
    <div ref={containerRef} className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-5 px-2 py-8 pb-4">

        {/* User goal */}
        {goal && <UserMessage text={goal} />}

        {/* Planning / task decomposition */}
        {hasPlanning && <PlanningMessage events={events} finalAnswer={finalAnswer} />}

        {/* Streaming events */}
        {streamEvents.map((event, i) => {
          switch (event.type) {
            case "tool_call": return <ToolCallMessage key={i} event={event} />;
            case "routing":   return <RoutingRow      key={i} event={event} />;
            case "thinking":  return <ThinkingRow     key={i} event={event} />;
            case "error":
              return (
                <ErrorMessage
                  key={i}
                  message={typeof event.message === "string" ? event.message : "Unknown error"}
                />
              );
            default: return null;
          }
        })}

        {/* Working dots */}
        {isStreaming && <WorkingIndicator />}

        {/* Final answer */}
        {finalAnswer && <FinalAnswerMessage answer={finalAnswer} />}

        {/* Error outside stream */}
        {errorMessage && !finalAnswer && <ErrorMessage message={errorMessage} />}

        {/* Completion */}
        {isComplete && !isStreaming && <CompletionPill />}

        {/* Scroll anchor */}
        <div className="h-2" />
      </div>
    </div>
  );
}
