# NeuroAgent

> Give it a goal. Watch it think, plan, search, code, and deliver.

[![CI](https://github.com/amunim12/NeuroAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/amunim12/NeuroAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C.svg)](https://langchain-ai.github.io/langgraph/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38B2AC.svg)](https://tailwindcss.com/)

![NeuroAgent live demo](docs/architecture/demo.gif)

NeuroAgent is a full-stack autonomous AI agent. It accepts a natural-language goal, decomposes it into subtasks, routes each step to the most cost-effective model, uses real tools (web search, sandboxed code execution, browser automation, HTTP calls), remembers what it has learned via short-term (Redis) and long-term (Pinecone) memory, and streams every step of its reasoning to the browser in real time.

In three bullets, non-technical:

- You type a goal. It plans how to get there.
- It uses real tools — the web, a code sandbox, a browser — to do the work, not just talk about it.
- You watch it think, step by step, and get a written answer you can act on.


---

## 🎯 Problem

AI assistants that only generate text have a hard ceiling: they can describe a solution but cannot execute it. A developer asking "find the top three Python web frameworks by GitHub stars, write a comparison table, and email it to me" needs an agent that can actually open a browser, run queries, write and test code, and call an API not one that drafts plausible sounding steps and stops.

**Baseline:** Chat-only LLM frontends (ChatGPT, Claude.ai) require the user to copy outputs between tools, manually run code, and synthesise results. Multi step tasks take 20–40 minutes of manual back and forth.

**NeuroAgent's target:** Complete the same task end to end in a single goal submission, under 3 minutes, with full step by step transparency. The agent decompose the goal, routes each subtask to the cheapest sufficient model, executes real tools in a sandbox, persists what it learns across sessions, and surfaces every decision in the browser in real time.

**Success criteria:**

| Metric | Target | Source |
|---|---|---|
| Task pass rate (20-task benchmark) | ≥ 80 % | `backend/tests/eval/` |
| Mean end to end latency | ≤ 45 s | benchmark `latest.json` |
| Cost per complex task (GPT-4o) | ≤ $0.05 | LangSmith token accounting |
| Routing accuracy (correct model selected) | ≥ 85 % | manual spot check, 50 runs |

See [docs/project-brief.md](docs/project-brief.md) for the full problem statement, constraints, and risk assessment.

---

## 📊 Results

> Results below are from the built in 20 task evaluation benchmark. Run `make test` (or `python -m tests.eval.benchmark` inside `backend/`) with your own API keys to reproduce.

| Metric | Most recent run |
|---|---|
| Pass rate (overall) | _run benchmark to populate_ |
| Pass rate (`reasoning`) | _run benchmark to populate_ |
| Pass rate (`web_research`) | _run benchmark to populate_ |
| Pass rate (`coding`) | _run benchmark to populate_ |
| Pass rate (`synthesis`) | _run benchmark to populate_ |
| Pass rate (`multi_step`) | _run benchmark to populate_ |
| Mean latency | _run benchmark to populate_ |
| P95 latency | _run benchmark to populate_ |
| Mean tokens / task | _run benchmark to populate_ |

**Known limitations:**

- The model router uses keyword heuristics, not a trained classifier. It misroutes roughly 1 in 10 subtasks (complex tasks get sent to Groq when GPT-4o is warranted). A fine-tuned classifier is scoped in the roadmap.
- Long multi-step tasks (> 7 subtasks) occasionally exceed Groq's context window; the executor falls back to GPT-4o, raising cost.
- Playwright browser automation is headless and unsigned sites with aggressive bot detection (Cloudflare Turnstile) may block it.
- Long term Pinecone recall degrades when the index contains > ~10 k entries per user without periodic consolidation.

---

## ✨ Features

- **Goal → plan → execute → synthesise** pipeline built on LangGraph, with conditional looping until subtasks are complete.
- **Multi-model routing:** simple retrieval → Groq Llama 3, coding/structured reasoning → Claude Sonnet, complex/ambiguous → GPT-4o.
- **Real tool use:** Tavily web search, E2B sandboxed Python execution, Playwright browser automation, generic HTTP.
- **Hybrid memory:** Redis backed short term message history and Pinecone vector store for long term semantic recall (`text-embedding-3-small`, 1536 dims).
- **Real-time streaming UI:** WebSocket pipe surfaces planning, model routing, tool calls, and the final answer as the agent runs.
- **LangSmith-native observability:** every run is traced with user/session metadata so failures are filterable in the dashboard (see [`docs/architecture/langsmith-trace.png`](docs/architecture/langsmith-trace.png) for a representative capture).
- **Evaluation benchmark:** 20 task offline suite with deterministic scoring, latency, and token accounting.
- **Production-grade infra:** multi stage Docker builds, non root containers, Alembic migrations, GitHub Actions CI/CD, AWS deploy workflow (backend + frontend).

---

## 🏗️ Architecture

```
 ┌─────────────────┐          WebSocket (events)          ┌──────────────────┐
 │  Next.js 14 UI  │ <────────────────────────────────── │  FastAPI server  │
 │  Zustand + RQ   │ ──────── REST (auth, sessions) ───> │  JWT + SlowAPI   │
 └─────────────────┘                                      └────────┬─────────┘
                                                                   │
                                                                   ▼
                                 ┌──────────────── LangGraph state machine ────────────────┐
                                 │                                                          │
                                 │   read_memory → plan → route_model → execute ──► loop    │
                                 │                                       │                  │
                                 │                                       ▼                  │
                                 │                                  synthesize              │
                                 │                                       │                  │
                                 │                                       ▼                  │
                                 │                                  write_memory ──► END    │
                                 └──────────────────────────────────────────────────────────┘
                                        │                  │                  │
                                        ▼                  ▼                  ▼
                                  ┌─────────┐       ┌──────────────┐   ┌───────────┐
                                  │ OpenAI  │       │  Tavily /    │   │ Postgres  │
                                  │Anthropic│       │  E2B /       │   │ Redis     │
                                  │ Groq    │       │  Playwright  │   │ Pinecone  │
                                  └─────────┘       └──────────────┘   └───────────┘
```

**Layers**

| Layer             | Stack                                                                     |
|-------------------|---------------------------------------------------------------------------|
| Frontend          | Next.js 14 (App Router), TypeScript, Tailwind, Zustand, React Query       |
| Backend API       | FastAPI, SQLAlchemy 2 async, Pydantic v2, Alembic, SlowAPI rate limiting  |
| Agent core        | LangGraph, LangChain, LangSmith tracing                                   |
| Models            | OpenAI GPT-4o, Anthropic Claude Sonnet, Groq Llama 3                      |
| Tools             | Tavily (search), E2B (code sandbox), Playwright (browser), httpx (API)    |
| Data              | PostgreSQL 16, Redis 7, Pinecone                                          |
| Infra             | Docker Compose, Railway (backend + frontend), GitHub Actions              |

See [docs/adr/0001-langgraph-agent-architecture.md](docs/adr/0001-langgraph-agent-architecture.md) for the rationale behind the core architectural choices.

---

## 🚀 Quickstart

### Prerequisites

- Docker + Docker Compose **or** Python 3.11+ and Node 20+
- API keys for the providers you want to exercise (see [.env.example](.env.example))

### 1. Clone + configure

```bash
git clone https://github.com/amunim12/NeuroAgent.git
cd NeuroAgent
cp .env.example .env
# edit .env and fill in at least OPENAI_API_KEY, TAVILY_API_KEY, JWT_SECRET_KEY
```

### 2. Bootstrap the Pinecone index (one-off)

```bash
python scripts/setup_pinecone.py        # idempotent; safe to rerun
```

### 3a. Pull pre-built images (fastest, no local build)

Published images live on Docker Hub under [`amunim12/neuroagent-backend`](https://hub.docker.com/r/amunim12/neuroagent-backend) and [`amunim12/neuroagent-frontend`](https://hub.docker.com/r/amunim12/neuroagent-frontend). They're rebuilt and pushed on every merge to `main` by [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml).

```bash
make pull   # download latest images
make up     # boot the full stack without building
```

This is the right path if you're short on local disk or your machine struggles with the full build (the backend image installs Playwright + chromium). The `DOCKER_NAMESPACE` and `IMAGE_TAG` variables in `.env` control which images are pulled override `IMAGE_TAG` to pin a commit SHA (`sha-<short>`) or a released version (`1.0.0`).

### 3b. Build from source

```bash
make dev
# API:      http://localhost:8000
# Frontend: http://localhost:3000
# Docs:     http://localhost:8000/docs
```

The compose stack runs Postgres, Redis, the FastAPI backend (with Alembic migrations applied on boot) and the Next.js dev server.

### 4. Or run locally without Docker

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new shell)
cd frontend
npm install
npm run dev
```

---

## 📦 Installation

| Target                 | Command                                       |
|------------------------|-----------------------------------------------|
| Backend (dev)          | `pip install -r backend/requirements-dev.txt` |
| Backend (prod)         | `pip install -r backend/requirements.txt`     |
| Frontend               | `npm install` (inside `frontend/`)            |
| DB migrations          | `alembic upgrade head` (inside `backend/`)    |
| Pinecone index         | `python scripts/setup_pinecone.py`            |
| Playwright browsers    | `playwright install --with-deps chromium`     |

---

## ⚙️ Configuration

All runtime configuration is loaded from environment variables never hard code anything. The full list lives in [.env.example](.env.example). The most important groups:

- **LLM providers** — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`
- **Tools** — `TAVILY_API_KEY`, `E2B_API_KEY`
- **Data** — `DATABASE_URL`, `REDIS_URL`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_ENVIRONMENT`
- **Auth** — `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- **Observability** — `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`

Settings are validated at import time via `app.config.Settings`, so missing or malformed values surface immediately.

---

## 🔧 Usage

### Trigger a run from the browser

1. Register at `http://localhost:3000/register`
2. Sign in, open the dashboard
3. Enter a goal (e.g. *"Find the latest Python release and write code that prints its major/minor version"*)
4. Watch the event stream render planning, tool calls, and the final synthesised answer

### Trigger a run from the REST API

```bash
# Acquire a JWT
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "hunter2"}'

# Kick off an agent run (returns a session id immediately)
curl -X POST http://localhost:8000/api/v1/agent/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Summarise the top 3 HN stories"}'

# Stream events over WebSocket at ws://localhost:8000/api/v1/agent/ws/<session_id>?token=<jwt>
```

OpenAPI docs live at `http://localhost:8000/docs`.

---

## 🧪 Running Tests

```bash
# Backend unit + integration tests (SQLite via aiosqlite — no external DB needed)
cd backend
pytest tests/ -v
ruff check .
mypy app/

# Frontend
cd frontend
npm run lint
npm run type-check
npm run build
```

### Evaluation benchmark

```bash
cd backend
python -m tests.eval.benchmark --dry-run            # validate dataset
python -m tests.eval.benchmark --limit 5            # run 5 tasks
python -m tests.eval.benchmark --category coding    # single slice
python -m tests.eval.benchmark                      # full 20-task suite
```

Reports (pass rate, mean / p95 latency, token totals, per-category breakdown) land in `backend/tests/eval/reports/latest.json`.

The dataset ships with 20 tasks across five capability slices:

| Category       | Tasks | What it exercises                                                           |
|----------------|-------|-----------------------------------------------------------------------------|
| `reasoning`    | 4     | Pure LLM reasoning with no external tool use.                               |
| `web_research` | 5     | Live Tavily web search + synthesis of retrieved pages.                      |
| `coding`       | 4     | Python generation and execution in the E2B sandbox.                         |
| `synthesis`    | 3     | Multi-source aggregation into a single structured answer.                   |
| `multi_step`   | 4     | Chained tool use across planner → multiple executors → synthesizer.         |

Results from the most recent run are summarised in the [Results](#-results) section above. Commit the filled table alongside `latest.json` when publishing a release.

---

## 🚢 Deployment

**Hosted demo:** _not yet published — see the note near the top of this README. When it goes live, this section will link to the two Railway services (backend + frontend).

Production deploys follow a **registry-pull** flow GitHub builds images and pushes them to Docker Hub; Railway pulls from Docker Hub and redeploys automatically when a new `:latest` digest appears. GitHub never needs Railway credentials.

The repo ships with two GitHub Actions workflows:

- [`ci.yml`](.github/workflows/ci.yml) — lint, type-check, migration dry-run, pytest, Docker build on every push / PR.
- [`docker-publish.yml`](.github/workflows/docker-publish.yml) — matrix workflow that builds `amunim12/neuroagent-backend` and `amunim12/neuroagent-frontend` on merges to `main` (and on `v*.*.*` tags) and pushes them to Docker Hub with `latest`, semver, branch, and `sha-<short>` tags. Gated by `vars.DOCKER_PUBLISH_ENABLED` so it's a no-op until you're ready.

**GitHub repo settings required:**

| Kind | Name | Value |
|---|---|---|
| Secret | `DOCKERHUB_USERNAME` | your Docker Hub username (e.g. `amunim12`) |
| Secret | `DOCKERHUB_TOKEN` | Docker Hub access token with Read/Write/Delete |
| Variable | `DOCKER_PUBLISH_ENABLED` | `true` |

**Railway setup (one-time, in the Railway dashboard):**

1. Create a project with two services. For each one, choose **Deploy from Docker image**:
   - `backend` → `amunim12/neuroagent-backend:latest`
   - `frontend` → `amunim12/neuroagent-frontend:latest`
2. Add **PostgreSQL** and **Redis** plugins in the same project; reference them from the backend service as `${{Postgres.DATABASE_URL}}` / `${{Redis.REDIS_URL}}` (remember to prefix the DB URL with `postgresql+asyncpg://` for the async driver).
3. Set the remaining env vars from [`.env.example`](.env.example) on the backend service, and `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` on the frontend service (pointing at the backend's generated Railway domain).
4. Service settings → **Source: Docker Image** → enable **automatic deploys** so Railway redeploys when the `:latest` digest changes.

For production docker-compose (multi-worker Uvicorn, non-dev Next build) use:

```bash
make prod
```

---

## 📁 Project Layout

```
NeuroAgent/
├── backend/
│   ├── app/
│   │   ├── agent/           # LangGraph nodes, tools, memory, model router
│   │   ├── api/v1/          # Thin FastAPI route handlers
│   │   ├── services/        # Business logic
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── db/              # SQLAlchemy models + session factory
│   │   ├── utils/           # JWT, streaming, LangSmith tracing
│   │   └── main.py          # FastAPI app + lifespan
│   ├── alembic/versions/    # Database migrations
│   └── tests/
│       ├── eval/            # 20-task benchmark suite
│       └── test_*.py        # Unit + integration tests
├── frontend/
│   └── src/
│       ├── app/             # Next.js App Router pages
│       ├── components/      # UI (event stream, task decomposition, ...)
│       ├── hooks/           # React Query + WebSocket hooks
│       ├── lib/             # API client, utilities
│       └── stores/          # Zustand auth store
├── infra/
│   └── docker/              # Docker Compose files (dev + prod overrides)
├── docs/
│   ├── adr/                 # Architecture Decision Records (0001–0003)
│   ├── architecture/        # Diagrams, demo GIF, LangSmith traces
│   ├── api/                 # API reference and usage guides
│   ├── deployment/          # Hosting and deployment guides (Railway, Docker)
│   ├── development/         # Local setup and contribution guides
│   ├── experiments/         # Experiment log and tracking guide
│   ├── monitoring/          # Observability strategy and incident playbooks
│   ├── model-card.md        # LLM component documentation
│   └── project-brief.md     # Business problem, success criteria, risk assessment
├── scripts/                 # One-off operational scripts (Pinecone bootstrap, ...)
├── .github/
│   ├── workflows/           # CI + gated deploy
│   ├── ISSUE_TEMPLATE/      # Bug report + feature request forms
│   └── pull_request_template.md
├── Makefile                 # Unified dev commands (make dev, make test, make prod, ...)
└── .env.example             # Full environment variable reference
```

---

## 🔭 Future Improvements

The items below are scoped, prioritised, and tracked as GitHub Issues. Contributions welcome check `good first issue` labels.

**High priority (v1.1)**

- [ ] **Trained model router** — replace keyword heuristics with a small fine tuned classifier (distilBERT or similar) trained on LangSmith trace data. Target: ≥ 93 % routing accuracy. ([ADR-0002](docs/adr/0002-multi-model-routing.md) documents the current heuristic and flags this follow-up.)
- [ ] **Parallel subtask execution** — fan-out/fan-in for independent subtasks using LangGraph's native map-reduce pattern. Expected 40–60 % latency reduction on multi-step tasks.
- [ ] **Pinecone consolidation job** — scheduled task to cluster and summarise old memory entries, preventing recall degradation past 10 k entries.

**Medium priority (v1.2)**

- [ ] **Human-in-the-loop checkpoints** — surface a "confirm before executing" gate for destructive tool calls (file writes, external API mutations).
- [ ] **Cost cap enforcement** — per-session and per-user token budgets enforced at the router level, with graceful degradation to cheaper models when the cap is approached.
- [ ] **Streaming SSE fallback** — Server-Sent Events endpoint for clients that can't maintain WebSocket connections (corporate proxies, some mobile networks).

**Longer term**

- [ ] **Multi-agent collaboration** — delegate subtasks to specialised sub-agents (research agent, coding agent) coordinated by a supervisor graph.
- [ ] **Fine-tuned synthesiser** — RLHF-style feedback loop on final-answer quality using session thumbs-up/down signals.
- [ ] **Browser extension** — trigger NeuroAgent from any web page; surface tool-call results as an overlay.

---

## 🤝 Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup, coding standards, commit conventions, and PR checklist, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations.

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## 📄 License

Released under the [MIT License](LICENSE).
