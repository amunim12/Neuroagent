const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface SessionSummary {
  id: string;
  goal: string;
  status: string;
  result: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
  total: number;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_URL}/api/v1${path}`, { ...init, headers });

  if (!response.ok) {
    const text = await response.text();
    let message = text;
    try {
      const parsed = JSON.parse(text);
      message = parsed.detail ?? text;
    } catch {
      // keep the raw text
    }
    throw new ApiError(response.status, message || response.statusText);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<{ id: string; email: string }>("/auth/me", {}, token),

  runAgent: (token: string, goal: string) =>
    request<{ session_id: string; status: string }>(
      "/agent/run",
      { method: "POST", body: JSON.stringify({ goal }) },
      token,
    ),

  listSessions: (token: string) => request<SessionListResponse>("/sessions", {}, token),

  getSession: (token: string, id: string) => request<SessionSummary>(`/sessions/${id}`, {}, token),

  deleteSession: (token: string, id: string) =>
    request<void>(`/sessions/${id}`, { method: "DELETE" }, token),
};
