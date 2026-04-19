# NeuroAgent

> Give it a goal. Watch it think, plan, search, code, and deliver.

[![CI](https://github.com/amunim12/NeuroAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/amunim12/NeuroAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)

NeuroAgent is a full-stack autonomous AI agent. It accepts a natural-language goal, decomposes it into subtasks, routes each step to the most cost-effective model, uses real tools (web search, sandboxed code execution, browser automation, HTTP calls), remembers what it has learned via short-term (Redis) and long-term (Pinecone) memory, and streams every step of its reasoning to the browser in real time.

---

## ✨ Features

- **Goal → plan → execute → synthesise** pipeline built on LangGraph, with conditional looping until subtasks are complete.
- **Multi-model routing:** simple retrieval → Groq Llama 3, coding/structured reasoning → Claude Sonnet, complex/ambiguous → GPT-4o.
- **Real tool use:** Tavily web search, E2B sandboxed Python execution, Playwright browser automation, generic HTTP.
- **Hybrid memory:** Redis-backed short-term message history and Pinecone vector store for long-term semantic recall (`text-embedding-3-small`, 1536 dims).
- **Real-time streaming UI:** WebSocket pipe surfaces planning, model routing, tool calls, and the final answer as the agent runs.
- **LangSmith-native observability:** every run is traced with user/session metadata so failures are filterable in the dashboard.
- **Evaluation benchmark:** 20-task offline suite with deterministic scoring, latency, and token accounting.
- **Production-grade infra:** multi-stage Docker builds, non-root containers, Alembic migrations, GitHub Actions CI/CD, Railway + Vercel deploy workflows.

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
| Infra             | Docker Compose, Railway (backend), Vercel (frontend), GitHub Actions      |

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

### 3. Run with Docker Compose (recommended)

```bash
docker compose up --build
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

All runtime configuration is loaded from environment variables — never hard-code anything. The full list lives in [.env.example](.env.example). The most important groups:

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

---

## 🚢 Deployment

The repo ships with two GitHub Actions workflows:

- [`ci.yml`](.github/workflows/ci.yml) — lint, type-check, migration dry-run, pytest, Docker build on every push / PR.
- [`deploy.yml`](.github/workflows/deploy.yml) — deploys backend to Railway and frontend to Vercel on merges to `main`. Both jobs gate on repository variables (`vars.DEPLOY_BACKEND_ENABLED`, `vars.DEPLOY_FRONTEND_ENABLED`) so the workflow is a no-op until you're ready.

Required secrets: `RAILWAY_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.

For production docker-compose (multi-worker Uvicorn, non-dev Next build) use:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
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
├── docs/adr/                # Architecture Decision Records
├── scripts/                 # One-off operational scripts (Pinecone bootstrap, ...)
├── .github/                 # CI, deploy workflows, issue + PR templates
├── docker-compose.yml       # Local dev stack
└── docker-compose.prod.yml  # Production overrides
```

---

## 🤝 Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the local setup, coding standards, commit conventions, and PR checklist, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community expectations.

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## 📄 License

Released under the [MIT License](LICENSE).
