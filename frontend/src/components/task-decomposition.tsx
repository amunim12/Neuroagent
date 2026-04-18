"use client";

import { useAgentStore } from "@/stores/agent";

export function TaskDecomposition() {
  const events = useAgentStore((s) => s.events);
  const finalAnswer = useAgentStore((s) => s.finalAnswer);
  const planningEvent = events.find((event) => event.type === "planning");

  if (!planningEvent) return null;

  const subtasks = Array.isArray(planningEvent.subtasks)
    ? (planningEvent.subtasks as unknown[]).filter((item): item is string => typeof item === "string")
    : [];
  const reasoning = typeof planningEvent.reasoning === "string" ? planningEvent.reasoning : null;

  if (subtasks.length === 0) return null;

  // The most recent routing event identifies the in-progress subtask.
  // All prior subtasks are considered completed (graph executes sequentially).
  const lastRouting = [...events].reverse().find((event) => event.type === "routing");
  const activeSubtask = typeof lastRouting?.subtask === "string" ? lastRouting.subtask : null;
  const activeIndex = activeSubtask ? subtasks.indexOf(activeSubtask) : -1;

  return (
    <section className="rounded-xl border border-border bg-panel p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">Task plan</h3>
      {reasoning && <p className="mb-3 text-sm text-white/80">{reasoning}</p>}
      <ol className="flex flex-col gap-2">
        {subtasks.map((task, index) => {
          const isComplete = finalAnswer !== null || (activeIndex >= 0 && index < activeIndex);
          const isActive = !finalAnswer && index === activeIndex;
          return (
            <li
              key={index}
              className="flex items-start gap-3 rounded-md border border-border bg-bg px-3 py-2 text-sm"
            >
              <span
                className={
                  "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border font-mono text-xs " +
                  (isComplete
                    ? "border-emerald-400 bg-emerald-400/20 text-emerald-300"
                    : isActive
                      ? "border-accent bg-accent/20 text-accent"
                      : "border-border text-muted")
                }
              >
                {isComplete ? "✓" : index + 1}
              </span>
              <span className={isActive ? "text-accent" : "text-white/90"}>{task}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
