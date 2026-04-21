"use client";

import { ArrowUp, Square, Paperclip } from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type MutableRefObject,
} from "react";

import { useAgentWebSocket } from "@/hooks/use-agent-websocket";
import { useAgentStore } from "@/stores/agent";

interface GoalInputProps {
  /** Optionally expose a setter so parent can pre-fill the textarea. */
  externalSetGoal?: MutableRefObject<((text: string) => void) | null>;
}

export function GoalInput({ externalSetGoal }: GoalInputProps) {
  const [goal, setGoal] = useState("");
  const { runAgent, cancel } = useAgentWebSocket();
  const status    = useAgentStore((s) => s.status);
  const isRunning = status === "connecting" || status === "streaming";
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Expose setter to parent
  useEffect(() => {
    if (externalSetGoal) {
      externalSetGoal.current = (text: string) => {
        setGoal(text);
        textareaRef.current?.focus();
        // Trigger resize after state update
        requestAnimationFrame(() => autoResize());
      };
    }
    return () => {
      if (externalSetGoal) externalSetGoal.current = null;
    };
  });

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submit();
  }

  function submit() {
    const trimmed = goal.trim();
    if (!trimmed || isRunning) return;
    runAgent(crypto.randomUUID(), trimmed);
    setGoal("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  // Auto-focus when not running
  useEffect(() => {
    if (!isRunning) {
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [isRunning]);

  return (
    <div className="border-t border-border/50 bg-base/85 px-4 pb-5 pt-3 backdrop-blur-xl">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-3xl flex-col rounded-2xl border border-border bg-panel transition-all focus-within:border-border-bright focus-within:shadow-glow-sm"
        style={{ boxShadow: "0 8px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)" }}
      >
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={goal}
          onChange={(e) => { setGoal(e.target.value); autoResize(); }}
          onKeyDown={handleKeyDown}
          placeholder="Message NeuroAgent…"
          disabled={isRunning}
          rows={1}
          className="w-full resize-none bg-transparent px-5 pb-2 pt-4 text-sm leading-relaxed text-fore placeholder:text-fore-subtle/30 outline-none disabled:opacity-50"
          style={{ minHeight: "54px", maxHeight: "180px" }}
        />

        {/* Actions row */}
        <div className="flex items-center justify-between px-3 pb-3 pt-1">
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              className="flex h-7 w-7 items-center justify-center rounded-xl text-fore-subtle/30 hover:bg-elevated hover:text-fore-muted transition-all"
              title="Attach file (coming soon)"
              tabIndex={-1}
            >
              <Paperclip className="h-3.5 w-3.5" />
            </button>
            <span className="text-[10px] text-fore-subtle/20 select-none">
              {isRunning ? "Working…" : "Enter ↵ to send · Shift+Enter for newline"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isRunning && (
              <button
                type="button"
                onClick={cancel}
                className="flex items-center gap-1.5 rounded-xl border border-red-500/20 bg-red-500/8 px-3 py-1.5 text-xs font-medium text-red-400 transition hover:border-red-500/35 hover:bg-red-500/12"
              >
                <Square className="h-3 w-3 fill-current" />
                Stop
              </button>
            )}
            <button
              type="submit"
              disabled={isRunning || !goal.trim()}
              className="btn-gradient flex h-9 w-9 items-center justify-center rounded-xl"
              aria-label="Send"
            >
              <ArrowUp className="h-4 w-4 text-white" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </form>

      <p className="mt-2 text-center text-[10px] text-fore-subtle/18">
        NeuroAgent can make mistakes. Always verify important information.
      </p>
    </div>
  );
}
