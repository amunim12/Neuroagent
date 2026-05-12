# Project Brief — NeuroAgent

**Status:** Active
**Version:** 1.0
**Date:** 2026-04-19
**Owner:** Abdul Munim (abdulmunim.personal@gmail.com)

---

## 1. Problem Statement

### Background

AI language models can generate sophisticated text, but they cannot independently execute multi-step tasks that require real-world tool use. A developer who asks "research the three fastest Python web frameworks, run a latency benchmark against each, and produce a comparison report" must manually copy outputs between a chat interface, a terminal, and a browser — often taking 20–40 minutes and requiring constant context-switching.

Existing solutions fall into two camps:

- **Chat-only assistants** (ChatGPT, Claude.ai) — high quality text generation but no real tool execution; the user is the executor.
- **Narrow automation tools** (n8n, Zapier, custom scripts) — excellent at pre-scripted workflows but brittle under natural language input and unable to adapt their plan mid-execution.

### The Gap

There is no widely accessible, open-source, end-to-end system that:

1. Accepts a free-form goal in natural language.
2. Autonomously decomposes it into subtasks.
3. Selects the cheapest model that can handle each subtask.
4. Executes real tools (web search, code sandbox, browser, HTTP calls) in a secure environment.
5. Maintains memory across sessions so repeated users do not re-explain context.
6. Streams its entire reasoning process to the user in real time.

### Target User

Software engineers and technical users who regularly perform multi-step research, analysis, or automation tasks that currently require manual tool-switching.

---

## 2. Proposed Solution

NeuroAgent is a full-stack autonomous AI agent. The core is a **LangGraph state machine** that executes a deterministic pipeline:

```
read_memory → plan → route_model → execute ──► (loop)
                                       │
                                       ▼
                                  synthesize → write_memory → END
```

**Key design choices:**

| Choice | Rationale |
|---|---|
| LangGraph over plain LangChain | Explicit typed state, conditional edges, native LangSmith tracing |
| Multi-model routing | 10–30× cost difference between Groq Llama 3 and GPT-4o; routing by subtask complexity dramatically cuts per-run cost |
| Hybrid memory (Redis + Pinecone) | Redis for fast short-term session context; Pinecone for cross-session semantic recall |
| WebSocket streaming | Users need real-time visibility into agent reasoning to trust and debug it |
| E2B sandboxed code execution | Security boundary for arbitrary LLM-generated Python; no host filesystem access |

Full architectural rationale in [docs/adr/0001-langgraph-agent-architecture.md](adr/0001-langgraph-agent-architecture.md).

---

## 3. Success Definition

### Primary Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Task pass rate (20-task benchmark) | ≥ 80 % | `backend/tests/eval/benchmark.py` |
| Mean end-to-end latency | ≤ 45 s | benchmark `latest.json` |
| P95 latency | ≤ 90 s | benchmark `latest.json` |
| Mean cost per complex task | ≤ $0.05 | LangSmith token accounting |
| Model routing accuracy | ≥ 85 % | Manual spot-check, 50 runs |

### Secondary Metrics

| Metric | Target |
|---|---|
| Auth + session API availability | ≥ 99.5 % (Railway uptime) |
| Backend cold-start time | ≤ 5 s |
| CI pipeline duration | ≤ 8 min |
| Test coverage (business logic) | ≥ 80 % |

### Non-Goals (v1)

- Voice input or multi-modal (image) goals.
- Parallel subtask execution (fan-out/fan-in). Scoped for v1.1.
- Production SLAs below 99.5 % — NeuroAgent is a developer tool, not a consumer product with strict uptime requirements.

---

## 4. Constraints

### Technical

- All LLM API calls go through provider SDKs (OpenAI, Anthropic, Groq); no self-hosted inference in v1.
- Code execution is sandboxed via E2B. No host filesystem writes. Sandbox timeout: 30 s.
- Database: PostgreSQL 16 (users, sessions, messages) + Redis 7 (session memory) + Pinecone Starter tier (long-term memory).
- Python 3.11+, Node 20+. Both required for local dev without Docker.

### Security

- No PII stored beyond email address and user-submitted goals (which may contain PII at user discretion).
- JWT tokens expire in 60 minutes. No refresh token rotation in v1.
- Secrets strictly in environment variables; never logged.
- See [SECURITY.md](../SECURITY.md) for the full policy and disclosure contact.

### Cost

- Pinecone Starter tier: 100 k vectors free. Production users may need a paid index.
- E2B sandbox: pay-per-execution (≈ $0.001 / execution). Budgeted under $10/month at expected demo load.
- LLM costs: expected $15–30 / month at sustained demo traffic (100 runs/day, mix of Groq and GPT-4o).

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM provider outage (OpenAI / Anthropic / Groq) | Medium | High | Multi-provider routing; fallback logic in executor |
| Prompt injection via user goal | Medium | High | Input sanitisation at API boundary; E2B isolation prevents host access |
| Router misclassification raises cost | High | Medium | Cap per-session token budget; alert on cost anomalies via LangSmith |
| Pinecone rate limits at scale | Low | Medium | Redis caching layer for recent queries; exponential back-off |
| LangGraph minor-version API breaks | High | Low | Pinned in `requirements.txt`; automated `pip-audit` in CI |
| Bot detection blocks Playwright | Medium | Low | Affects only `browser` tool; other tools remain functional |

---

## 6. Milestones

| Milestone | Target Date | Status |
|---|---|---|
| v1.0 — initial public release | 2026-04-19 | ✅ Done |
| Trained model router (v1.1) | TBD | Planned |
| Parallel subtask execution (v1.1) | TBD | Planned |
| Human-in-the-loop checkpoints (v1.2) | TBD | Planned |
| Cost cap enforcement (v1.2) | TBD | Planned |

---

## 7. References

- [README.md](../README.md) — project overview and quickstart
- [docs/adr/](adr/) — all architecture decision records
- [docs/model-card.md](model-card.md) — LLM component documentation
- [docs/monitoring/strategy.md](monitoring/strategy.md) — observability and drift detection
- [SECURITY.md](../SECURITY.md) — vulnerability disclosure policy
