export type AgentEventType =
  | "status"
  | "planning"
  | "routing"
  | "tool_call"
  | "thinking"
  | "final_answer"
  | "complete"
  | "error";

export interface AgentEvent {
  type: AgentEventType;
  timestamp: string;
  [key: string]: unknown;
}
