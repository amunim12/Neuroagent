"use client";

import { Check, Circle, Loader2, ListTodo } from "lucide-react";

import { useAgentStore } from "@/stores/agent";

export function TaskDecomposition() {
  const events = useAgentStore((s) => s.events);
  const finalAnswer = useAgentStore((s) => s.finalAnswer);
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

  const completedCount = finalAnswer !== null
    ? subtasks.length
    : activeIndex >= 0 ? activeIndex : 0;

  return (
    <div
      className="animate-slide-up rounded-2xl border border-border bg-panel"
      style={{ boxShadow: "0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-violet-500/15">
            <ListTodo className="h-3.5 w-3.5 text-violet-400" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-widest text-fore-subtle">Task Plan</span>
        </div>
        <span className="text-xs text-fore-subtle">
          <span className="text-fore-muted font-medium">{completedCount}</span>
          <span className="mx-1">/</span>
          {subtasks.length}
        </span>
      </div>

      <div className="p-5">
        {/* Reasoning */}
        {reasoning && (
          <p className="mb-4 text-sm leading-relaxed text-fore-muted border-l-2 border-accent/30 pl-3 italic">
            {reasoning}
          </p>
        )}

        {/* Progress bar */}
        <div className="mb-5 h-1 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent to-purple-500 transition-all duration-700"
            style={{ width: `${(completedCount / subtasks.length) * 100}%` }}
          />
        </div>

        {/* Steps */}
        <ol className="flex flex-col gap-1">
          {subtasks.map((task, index) => {
            const isComplete = finalAnswer !== null || (activeIndex >= 0 && index < activeIndex);
            const isActive = !finalAnswer && index === activeIndex;
            const isPending = !isComplete && !isActive;

            return (
              <li key={index} className="flex items-start gap-3.5 py-2">
                {/* Step indicator */}
                <div className="mt-0.5 shrink-0">
                  {isComplete ? (
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/15 border border-emerald-500/30">
                      <Check className="h-3 w-3 text-emerald-400" strokeWidth={2.5} />
                    </div>
                  ) : isActive ? (
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/15 border border-accent/40">
                      <Loader2 className="h-3 w-3 text-accent animate-spin" />
                    </div>
                  ) : (
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border border-border">
                      <span className="text-[10px] font-mono font-medium text-fore-subtle">{index + 1}</span>
                    </div>
                  )}
                </div>

                {/* Task text */}
                <span
                  className={`text-sm leading-relaxed pt-0.5 ${
                    isComplete
                      ? "text-fore-subtle line-through decoration-fore-subtle/30"
                      : isActive
                        ? "text-fore font-medium"
                        : isPending
                          ? "text-fore-subtle"
                          : "text-fore-muted"
                  }`}
                >
                  {task}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
