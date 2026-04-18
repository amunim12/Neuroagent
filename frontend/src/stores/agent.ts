import { create } from "zustand";

import type { AgentEvent } from "@/lib/events";

export type ConnectionStatus = "idle" | "connecting" | "streaming" | "done" | "error";

interface AgentState {
  sessionId: string | null;
  goal: string;
  status: ConnectionStatus;
  events: AgentEvent[];
  finalAnswer: string | null;
  errorMessage: string | null;

  startRun: (sessionId: string, goal: string) => void;
  appendEvent: (event: AgentEvent) => void;
  setStatus: (status: ConnectionStatus) => void;
  setFinalAnswer: (answer: string) => void;
  setError: (message: string) => void;
  reset: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  sessionId: null,
  goal: "",
  status: "idle",
  events: [],
  finalAnswer: null,
  errorMessage: null,

  startRun: (sessionId, goal) =>
    set({
      sessionId,
      goal,
      status: "connecting",
      events: [],
      finalAnswer: null,
      errorMessage: null,
    }),

  appendEvent: (event) =>
    set((state) => {
      const next: Partial<AgentState> = { events: [...state.events, event] };
      if (event.type === "final_answer" && typeof event.content === "string") {
        next.finalAnswer = event.content;
      }
      if (event.type === "complete") {
        next.status = "done";
        if (typeof event.result === "string") next.finalAnswer = event.result;
      }
      if (event.type === "error") {
        next.status = "error";
        if (typeof event.message === "string") next.errorMessage = event.message;
      }
      return next;
    }),

  setStatus: (status) => set({ status }),
  setFinalAnswer: (answer) => set({ finalAnswer: answer }),
  setError: (message) => set({ status: "error", errorMessage: message }),
  reset: () =>
    set({
      sessionId: null,
      goal: "",
      status: "idle",
      events: [],
      finalAnswer: null,
      errorMessage: null,
    }),
}));
