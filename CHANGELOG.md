# Changelog

All notable changes to NeuroAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `CODE_OF_CONDUCT.md` with the project's community expectations, reporting channel, and enforcement ladder.
- `docs/adr/0001-langgraph-agent-architecture.md` — the first architecture decision record, covering why the agent is built on LangGraph and the trade-offs taken.
- `.github/pull_request_template.md` — PR template with summary, test plan, and a full definition-of-done checklist.
- `.github/ISSUE_TEMPLATE/` — structured issue forms for bug reports and feature requests plus a `config.yml` that routes questions to Discussions and security reports to email.
- `docs/images/README.md` — instructions for capturing and committing the demo GIF, LangSmith trace screenshot, and architecture render.
- `.github/workflows/docker-publish.yml` — matrix workflow that builds `backend` and `frontend` images on GitHub-hosted runners and pushes them to Docker Hub (`amunim12/neuroagent-backend`, `amunim12/neuroagent-frontend`) with `latest`, semver, branch, and `sha-<short>` tags. Gated by the `DOCKER_PUBLISH_ENABLED` repo variable so maintainers can pause it without deleting the workflow.

### Changed
- README: added the full tech-stack badge row, a hero demo GIF slot, a plain-language "what it does" summary, a live-demo placeholder, a benchmark categories/results table, and an expanded project-layout tree that covers `docs/` and `.github/` subfolders.
- README: split the Docker quickstart into "3a. Pull pre-built images" (the fast path, no local build) and "3b. Build from source" (fallback for contributors), with links to the Docker Hub repositories and the publish workflow.
- `docker-compose.yml`: backend and frontend services now reference `${DOCKER_NAMESPACE:-amunim12}/neuroagent-*:${IMAGE_TAG:-latest}` so `docker compose pull` works without a local build. The `build:` blocks remain as a fallback.
- `.env.example`: added a `# === Docker image source ===` section documenting `DOCKER_NAMESPACE` and `IMAGE_TAG` so forks can point at their own Docker Hub namespace or pin a specific commit SHA.

### Fixed
- `backend/tests/conftest.py`: switched the test database from file-backed `./test.db` to in-memory SQLite with `StaticPool`, dropped the deprecated custom `event_loop` fixture, and added a `sync_client_db_reset` fixture so TestClient-based WebSocket tests get a clean schema (the async autouse fixture doesn't run around sync tests). Previously caused CI failures where `register` returned 409 on a "fresh" DB and registrations bled between test files.
- Test assertions for missing `HTTPBearer` credentials now accept both 401 and 403 — FastAPI ≥ 0.118 returns 401, older versions return 403, and `requirements.txt` pins a range that spans both.
- `frontend/public/.gitkeep`: added so the multi-stage Docker build's `COPY --from=builder /app/public ./public` step resolves. Next.js treats `public/` as optional, but the Dockerfile required it.
- `.gitignore`: now ignores `*.db` / `*.sqlite*` and removed the accidentally-committed `test.db`.

## [1.0.0] - 2026-04-19

### Added
- Initial public release of NeuroAgent.
- Backend: FastAPI app with JWT auth, SlowAPI rate limiting, SQLAlchemy 2 async + Alembic migrations.
- Agent core: LangGraph state machine with planner, model router, executor, synthesizer, and memory read/write nodes.
- Multi-model routing between OpenAI GPT-4o, Anthropic Claude Sonnet, and Groq Llama 3 based on task heuristics.
- Tool integrations: Tavily web search, E2B sandboxed Python execution, Playwright browser automation, httpx API caller.
- Hybrid memory: Redis-backed short-term history and Pinecone vector store for long-term semantic recall.
- Real-time WebSocket streaming of planning, routing, tool calls, and final answers.
- LangSmith tracing wired up via `app.utils.tracing`, with per-run metadata for filtering.
- Frontend: Next.js 14 dashboard with goal input, live event stream, task decomposition view, tool call cards, final result viewer, and session history.
- Auth store powered by Zustand (persisted) and React Query for server state.
- Docker Compose local dev stack and production override (`docker-compose.prod.yml`) with multi-stage builds, non-root users, and Alembic-on-boot.
- GitHub Actions CI (lint, type-check, migration dry-run, pytest, Docker build) and gated deploy workflow for Railway + Vercel.
- One-off bootstrap script `scripts/setup_pinecone.py` (idempotent, supports `--dry-run`).
- Evaluation benchmark: 20-task dataset, deterministic offline scoring, per-task latency + token accounting, JSON reports.

[Unreleased]: https://github.com/amunim12/NeuroAgent/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/amunim12/NeuroAgent/releases/tag/v1.0.0
