# API Overview

NeuroAgent exposes a versioned REST API under `/api/v1/` and a WebSocket endpoint for real-time agent event streaming. Interactive documentation is available at runtime:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

All endpoints (except `/api/v1/health`, `/api/v1/auth/login`, and `/api/v1/auth/register`) require a valid JWT in the `Authorization: Bearer <token>` header.

---

## Authentication

### Register

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "hunter2"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "hunter2"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Use `access_token` as the Bearer token for all subsequent requests.

---

## Agent

### Start a run

```http
POST /api/v1/agent/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "goal": "Find the latest stable Python release and print its version"
}
```

Response:

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

### Stream events (WebSocket)

```
ws://localhost:8000/api/v1/agent/ws/{session_id}?token=<jwt>
```

Events are newline-delimited JSON objects. Each event has a `type` field:

| Type             | Description                                            |
|------------------|--------------------------------------------------------|
| `planning`       | Planner is decomposing the goal into subtasks          |
| `routing`        | Router selected a model for the next subtask           |
| `tool_call`      | Agent is invoking a tool (web search, code exec, etc.) |
| `tool_result`    | Tool returned a result                                 |
| `synthesizing`   | Synthesizer is assembling the final answer             |
| `final_answer`   | Run complete — contains the final synthesised response |
| `error`          | Agent encountered an unrecoverable error               |

Example `tool_call` event:

```json
{
  "type": "tool_call",
  "tool": "web_search",
  "input": {"query": "Python latest stable release"},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Sessions

### List sessions

```http
GET /api/v1/sessions
Authorization: Bearer <token>
```

Returns a paginated list of the authenticated user's past agent runs.

### Get session

```http
GET /api/v1/sessions/{session_id}
Authorization: Bearer <token>
```

Returns the session record including goal, status, and all stored events.

---

## Health

```http
GET /api/v1/health
```

Returns `200 OK` when the server is up. Used by Docker health checks and monitoring.

---

## Response envelope

All responses follow a consistent structure:

```json
{
  "data": { },
  "error": null,
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "abc123"
  }
}
```

Error responses use standard HTTP status codes (`400`, `401`, `403`, `404`, `422`, `500`) with a descriptive `error` field and `null` `data`.

---

## Rate limiting

The API is rate-limited via [SlowAPI](https://github.com/laurentS/slowapi). Default limits are configured in `app/main.py`. Exceeding the limit returns `429 Too Many Requests`.
