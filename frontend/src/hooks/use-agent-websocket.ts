"use client";

import { useCallback, useEffect, useRef } from "react";

import type { AgentEvent } from "@/lib/events";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

/**
 * Connects to /api/v1/agent/ws/{sessionId}?token=..., sends the goal,
 * and streams events into the agent store until the socket closes.
 */
export function useAgentWebSocket() {
  const token = useAuthStore((s) => s.token);
  const socketRef = useRef<WebSocket | null>(null);

  const runAgent = useCallback(
    (sessionId: string, goal: string) => {
      if (!token) {
        useAgentStore.getState().setError("Not authenticated");
        return;
      }

      useAgentStore.getState().startRun(sessionId, goal);

      const url = `${WS_URL}/api/v1/agent/ws/${sessionId}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        useAgentStore.getState().setStatus("streaming");
        ws.send(JSON.stringify({ goal }));
      };

      ws.onmessage = (message) => {
        try {
          const parsed = JSON.parse(message.data) as AgentEvent;
          useAgentStore.getState().appendEvent(parsed);
        } catch (err) {
          console.error("Failed to parse event", err);
        }
      };

      ws.onerror = () => {
        useAgentStore.getState().setError("WebSocket connection failed");
      };

      ws.onclose = () => {
        const status = useAgentStore.getState().status;
        if (status === "streaming" || status === "connecting") {
          useAgentStore.getState().setStatus("done");
        }
      };
    },
    [token],
  );

  const cancel = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  return { runAgent, cancel };
}
