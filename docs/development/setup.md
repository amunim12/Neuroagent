# Local Development Setup

This guide walks through setting up a full NeuroAgent development environment from scratch.

## Prerequisites

| Tool            | Version   | Notes                                           |
|-----------------|-----------|-------------------------------------------------|
| Python          | 3.11+     | Use `pyenv` or the official installer           |
| Node.js         | 20+       | Use `nvm` or the official installer             |
| Docker Desktop  | Latest    | Required for the full stack via `make dev`      |
| Git             | 2.40+     |                                                 |

---

## Quick path (Docker)

```bash
git clone https://github.com/amunim12/NeuroAgent.git
cd NeuroAgent
cp .env.example .env
# edit .env — at minimum fill in: OPENAI_API_KEY, TAVILY_API_KEY, JWT_SECRET_KEY
make dev
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- API docs (ReDoc): http://localhost:8000/redoc

---

## Manual path (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
playwright install --with-deps chromium
alembic upgrade head
uvicorn app.main:app --reload
# Windows: python run.py   (sets WindowsSelectorEventLoopPolicy for psycopg v3)
```

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## Environment variables

All configuration is loaded from `.env` at the project root (backend reads it via `app.config.Settings`; the compose file injects it into containers). Copy `.env.example` and fill in the values:

```bash
cp .env.example .env
```

**Minimum required keys to start the agent:**

| Variable           | Description                             |
|--------------------|-----------------------------------------|
| `OPENAI_API_KEY`   | Powers GPT-4o for complex tasks         |
| `TAVILY_API_KEY`   | Web search tool                         |
| `JWT_SECRET_KEY`   | Any strong random string                |

Everything else can be left as the placeholder values for local development — features that depend on missing keys (Pinecone, E2B, Anthropic, Groq) will degrade gracefully or raise clear startup errors.

---

## Database migrations

Migrations are managed with Alembic. The Docker stack applies them automatically on boot (`alembic upgrade head` in the container entrypoint). For local development:

```bash
make migrate                              # apply pending migrations
cd backend && alembic revision --autogenerate -m "description"  # generate a new migration
```

---

## Running tests

```bash
make test         # pytest (uses SQLite + mocks — no external services needed)
make lint         # ruff
make type-check   # mypy
```

For the frontend:

```bash
cd frontend
npm run lint
npm run type-check
npm run build
```

---

## Useful Makefile targets

Run `make help` to see all available targets with descriptions.

```
  dev                Start full dev stack (build + up)
  up                 Start without rebuilding
  down               Stop all services
  test               Run backend test suite
  lint               Lint with ruff
  migrate            Apply database migrations
  shell-backend      Shell into the backend container
  shell-frontend     Shell into the frontend container
```

---

## LangSmith tracing (optional)

Set `LANGCHAIN_TRACING_V2=true` and provide a `LANGCHAIN_API_KEY` in `.env`. Every agent run will appear in your LangSmith project under the name set by `LANGCHAIN_PROJECT`. This is the fastest way to debug unexpected agent behaviour.
