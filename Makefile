.PHONY: dev up down down-v build pull prod logs ps \
        test lint lint-fix type-check migrate \
        setup shell-backend shell-frontend

COMPOSE      = docker compose -f infra/docker/docker-compose.yml
COMPOSE_PROD = $(COMPOSE) -f infra/docker/docker-compose.prod.yml

# ── Local dev stack ────────────────────────────────────────────────────────────

dev:          ## Build images and start the full dev stack
	$(COMPOSE) up --build

up:           ## Start the stack (no rebuild)
	$(COMPOSE) up

down:         ## Stop the stack
	$(COMPOSE) down

down-v:       ## Stop the stack and remove volumes
	$(COMPOSE) down -v

build:        ## Build all images without starting
	$(COMPOSE) build

pull:         ## Pull latest pre-built images from Docker Hub
	$(COMPOSE) pull

prod:         ## Start the production stack (multi-worker, optimised images)
	$(COMPOSE_PROD) up -d

logs:         ## Tail logs for all services
	$(COMPOSE) logs -f

ps:           ## Show running containers
	$(COMPOSE) ps

# ── Backend shortcuts ──────────────────────────────────────────────────────────

test:         ## Run the full backend test suite
	cd backend && pytest tests/ -v

lint:         ## Lint backend with ruff
	cd backend && ruff check .

lint-fix:     ## Auto-fix ruff lint issues
	cd backend && ruff check . --fix

type-check:   ## Run mypy on the backend
	cd backend && mypy app/

migrate:      ## Apply pending Alembic migrations
	cd backend && alembic upgrade head

# ── Shells ─────────────────────────────────────────────────────────────────────

shell-backend:   ## Open a shell in the running backend container
	$(COMPOSE) exec backend bash

shell-frontend:  ## Open a shell in the running frontend container
	$(COMPOSE) exec frontend sh

# ── First-run setup ────────────────────────────────────────────────────────────

setup:        ## Copy .env.example → .env and bootstrap the Pinecone index
	cp -n .env.example .env || true
	python scripts/setup_pinecone.py

# ── Help ───────────────────────────────────────────────────────────────────────

help:         ## List all available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
