# Deploying to Railway

NeuroAgent uses a **registry-pull** deployment model: GitHub Actions builds Docker images and pushes them to Docker Hub; Railway automatically redeploys when a new `:latest` digest appears. GitHub never needs Railway credentials.

## Prerequisites

- A [Railway](https://railway.app) account
- Docker Hub credentials (username + access token with Read/Write/Delete)
- All API keys from [`.env.example`](../../.env.example) ready

---

## Step 1 — Configure GitHub secrets and variables

In your GitHub repository settings (`Settings → Secrets and variables → Actions`):

| Kind     | Name                       | Value                                        |
|----------|----------------------------|----------------------------------------------|
| Secret   | `DOCKERHUB_USERNAME`       | Your Docker Hub username (e.g. `amunim12`)   |
| Secret   | `DOCKERHUB_TOKEN`          | Docker Hub access token                      |
| Variable | `DOCKER_PUBLISH_ENABLED`   | `true`                                       |
| Variable | `RAILWAY_BACKEND_URL`      | Railway backend public URL (set after step 2)|
| Variable | `RAILWAY_BACKEND_WS_URL`   | Same URL with `wss://` scheme                |
| Variable | `RAILWAY_BACKEND_WEBHOOK`  | Railway redeploy webhook (optional)          |
| Variable | `RAILWAY_FRONTEND_WEBHOOK` | Railway redeploy webhook (optional)          |

---

## Step 2 — Create Railway services

1. Open the Railway dashboard and create a new **Project**.
2. Add two **services**, selecting **Deploy from Docker image** for each:
   - `backend` → `amunim12/neuroagent-backend:latest`
   - `frontend` → `amunim12/neuroagent-frontend:latest`
3. Add **PostgreSQL** and **Redis** plugins to the project.

### Backend environment variables

Reference the Railway plugin URLs directly:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}    # prefix with postgresql+asyncpg://
REDIS_URL=${{Redis.REDIS_URL}}
```

Then add all remaining keys from [`.env.example`](../../.env.example):
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `E2B_API_KEY`,
`PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_ENVIRONMENT`,
`JWT_SECRET_KEY`, `LANGCHAIN_API_KEY`, etc.

> **Note:** Railway provides `DATABASE_URL` in `postgresql://` format. Prefix it with `postgresql+asyncpg://` so SQLAlchemy's async driver works correctly.

### Frontend environment variables

```
NEXT_PUBLIC_API_URL=https://<your-backend-railway-domain>
NEXT_PUBLIC_WS_URL=wss://<your-backend-railway-domain>
```

---

## Step 3 — Enable automatic redeploys

In each service's settings (`Settings → Source → Deploy`), enable **automatic deployments**. Railway will poll Docker Hub and redeploy whenever the `:latest` digest changes.

Alternatively, the [docker-publish.yml](../../.github/workflows/docker-publish.yml) workflow triggers a Railway webhook after a successful push (set `RAILWAY_BACKEND_WEBHOOK` / `RAILWAY_FRONTEND_WEBHOOK`).

---

## Deploy flow

```
git push → CI (lint + test) → docker-publish (build + push to Docker Hub) → Railway redeploy
```

Every merge to `main` that passes CI automatically ships to production within ~5 minutes.

---

## Rollback

To roll back, override `IMAGE_TAG` in Railway to a previous `sha-<short>` digest, then trigger a redeploy. All image tags are listed in Docker Hub under `amunim12/neuroagent-backend` and `amunim12/neuroagent-frontend`.
