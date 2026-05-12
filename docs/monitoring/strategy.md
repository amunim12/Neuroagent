# Monitoring Strategy

**Version:** 1.0
**Date:** 2026-04-19

This document defines what NeuroAgent monitors in production, how signals are collected, what constitutes an alert, and how the system handles model/data drift.

---

## 1. Observability Stack

| Layer | Tool | Purpose |
|---|---|---|
| LLM traces | LangSmith | Per-run traces with model selection, token counts, latency per node, tool inputs/outputs |
| Application metrics | FastAPI + Prometheus (planned v1.2) | Request rate, error rate, endpoint latency |
| Infrastructure | Railway built-in | CPU, memory, network, restart events |
| Structured logs | Python `logging` (JSON format) | Application events, errors, agent state transitions |
| Uptime | Railway health check → `/api/v1/health` | Service availability |

---

## 2. What to Monitor

### 2.1 System health

| Signal | Normal range | Alert threshold |
|---|---|---|
| API availability (`/api/v1/health`) | 99.5 % | < 99 % over 5 min |
| HTTP 5xx error rate | < 1 % | > 5 % over 5 min |
| HTTP 4xx error rate | < 10 % | > 25 % over 5 min |
| Backend cold-start time | < 5 s | > 15 s |
| Database connection pool saturation | < 70 % | > 90 % |
| Redis memory usage | < 256 MB | > 400 MB |

### 2.2 Agent pipeline health

Monitor these signals in LangSmith (filter by project name `LANGCHAIN_PROJECT`):

| Signal | Normal range | Alert threshold |
|---|---|---|
| Run success rate (no error node reached) | ≥ 80 % | < 65 % over 1 hour |
| Mean end-to-end latency | ≤ 45 s | > 90 s (2× target) |
| P95 latency | ≤ 90 s | > 180 s |
| `plan` node failure rate | < 2 % | > 10 % |
| `execute` node tool error rate | < 5 % | > 20 % |
| `synthesize` node failure rate | < 2 % | > 10 % |

### 2.3 Cost monitoring

LangSmith tracks token usage per run. Export weekly summaries and alert on:

| Signal | Alert threshold |
|---|---|
| Daily GPT-4o token spend | > $5 / day (expected: < $2) |
| Mean tokens / task | > 2× the rolling 7-day average |
| Groq context overflow rate | > 15 % of Groq-routed subtasks |

Set up LangSmith usage alerts at the project level. Anomalous cost is the primary signal for router misclassification (too many subtasks sent to GPT-4o) or prompt injection that inflates context.

### 2.4 Memory health

| Signal | Normal range | Alert threshold |
|---|---|---|
| Pinecone upsert success rate | > 99 % | < 95 % |
| Pinecone query latency | < 100 ms | > 300 ms |
| Redis hit rate (session memory) | > 90 % | < 70 % |
| Vectors per user namespace | < 5 000 | > 8 000 (approaching consolidation need) |

---

## 3. Logging Standards

All application logs are emitted as JSON to stdout, captured by Railway, and queryable in the Railway log explorer.

### Log levels

| Level | When to use |
|---|---|
| `DEBUG` | Node entry/exit, state snapshots (development only; disable in prod via `LOG_LEVEL=INFO`) |
| `INFO` | Agent run started/completed, tool called, model selected, session created |
| `WARNING` | Fallback model used, Redis miss on expected session, Pinecone retry |
| `ERROR` | Node raised unhandled exception, tool returned error, DB write failed |

### Required fields on every log entry

```json
{
  "timestamp": "ISO-8601",
  "level": "INFO",
  "logger": "app.agent.nodes.executor",
  "session_id": "uuid",
  "user_id": "uuid",
  "message": "human-readable event description",
  "extra": { }
}
```

**Never log:** passwords, JWT tokens, raw API keys, full Pinecone vectors, or any PII beyond user ID.

---

## 4. Model and Data Drift Detection

NeuroAgent does not own trained models, so classical dataset drift (covariate shift in training data) does not apply directly. However, two proxies for drift are meaningful:

### 4.1 Output quality drift

**Definition:** A sustained drop in the benchmark pass rate compared to the baseline established at release.

**Detection:**

1. Run the 20-task benchmark weekly (or on every release) using the same dataset and scoring logic.
2. Persist results to `backend/tests/eval/reports/` with a timestamped filename.
3. Alert if pass rate drops > 5 percentage points from the v1.0 baseline in any category.

Common causes:
- Foundation model provider silently updated the model behind the same model ID.
- A new model version has different tool-calling or structured-output format behavior.
- Pinecone long-term memory degraded (too many low-quality entries diluting recall).

**Response:** Pin the model ID in `app/config.py` to the last known-good version. Open an issue. Run the benchmark against the new model version in isolation before updating the pin.

### 4.2 Routing distribution drift

**Definition:** The fraction of subtasks routed to each model shifts significantly from the established baseline.

**Detection:** Export the `router.model` field from LangSmith weekly. Baseline routing mix (from informal testing):

| Model | Expected share |
|---|---|
| Groq Llama 3 | 65–75 % |
| Claude Sonnet | 15–25 % |
| GPT-4o | 5–15 % |

Alert if GPT-4o share exceeds 25 % over a 7-day window — this suggests the router is over-routing or that users are submitting significantly more complex goals than the baseline.

### 4.3 Goal topic drift

**Definition:** User goals shift into topic domains that are outside the benchmark's coverage, potentially exposing blind spots in quality measurement.

**Detection:** Monthly — review a random sample of 20 LangSmith traces. Categorise goals manually. If > 30 % fall into a category not covered by the benchmark (e.g. "financial analysis"), add new benchmark tasks for that category.

---

## 5. Alerting and Escalation

Until a dedicated alerting stack (Prometheus + Alertmanager, or Grafana) is configured, alerts are handled manually:

1. **LangSmith:** Configure usage alerts on the project for daily token spend thresholds. Email notification to abdulmunim.personal@gmail.com.
2. **Railway:** Enable restart notifications and out-of-memory alerts on the backend service.
3. **Weekly review:** Maintainer reviews LangSmith dashboard and benchmark results every Monday. Any metric outside the alert threshold in section 2 triggers an incident.

For the incident response process, see [incident-response.md](incident-response.md).

---

## 6. Runbooks

### Check current system health

```bash
# API availability
curl http://localhost:8000/api/v1/health

# Redis
docker exec -it neuroagent-redis-1 redis-cli ping
docker exec -it neuroagent-redis-1 redis-cli info memory | grep used_memory_human

# Database
docker exec -it neuroagent-db-1 psql -U postgres -c "SELECT count(*) FROM sessions;"
```

### Export LangSmith run statistics (last 7 days)

```python
from langsmith import Client
from datetime import datetime, timedelta

client = Client()
runs = client.list_runs(
    project_name="neuroagent",
    start_time=datetime.utcnow() - timedelta(days=7),
    run_type="chain",
)
# analyse runs for latency, token usage, error rate
```

### Run benchmark and compare to baseline

```bash
cd backend
python -m tests.eval.benchmark        # writes latest.json
python -m tests.eval.compare_reports  # diff latest vs previous
```
