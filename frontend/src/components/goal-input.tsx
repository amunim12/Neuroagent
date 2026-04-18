"use client";

import { useState, type FormEvent } from "react";

import { useAgentWebSocket } from "@/hooks/use-agent-websocket";
import { useAgentStore } from "@/stores/agent";

export function GoalInput() {
  const [goal, setGoal] = useState("");
  const { runAgent, cancel } = useAgentWebSocket();
  const status = useAgentStore((s) => s.status);
  const isRunning = status === "connecting" || status === "streaming";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = goal.trim();
    if (!trimmed || isRunning) return;
    const sessionId = crypto.randomUUID();
    runAgent(sessionId, trimmed);
    setGoal("");
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-border bg-panel p-4">
      <label htmlFor="goal" className="mb-2 block text-sm text-muted">
        What should the agent do?
      </label>
      <textarea
        id="goal"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        rows={3}
        placeholder="e.g. Research the latest developments in quantum error correction and summarize the top 3 papers"
        className="w-full resize-y rounded-md border border-border bg-bg px-3 py-2 text-sm outline-none focus:border-accent"
        disabled={isRunning}
      />
      <div className="mt-3 flex items-center justify-end gap-2">
        {isRunning ? (
          <button
            type="button"
            onClick={cancel}
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-bg"
          >
            Cancel
          </button>
        ) : null}
        <button
          type="submit"
          disabled={isRunning || !goal.trim()}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accentMuted disabled:opacity-50"
        >
          {isRunning ? "Running..." : "Run agent"}
        </button>
      </div>
    </form>
  );
}
