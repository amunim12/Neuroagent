# Contributing to NeuroAgent

Thanks for your interest in contributing! This document captures the local-setup and day-to-day workflow that every contributor (including the maintainers) follows.

Please also read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 1. Set up your environment

See the [Quickstart in the README](README.md#-quickstart) for the full path. A minimal dev loop:

```bash
git clone https://github.com/amunim12/NeuroAgent.git
cd NeuroAgent
cp .env.example .env     # fill in at least OPENAI_API_KEY, TAVILY_API_KEY, JWT_SECRET_KEY
docker compose up --build
```

If you don't use Docker:

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new shell)
cd frontend
npm install
npm run dev
```

---

## 2. Pick up work

- Browse [open issues](https://github.com/amunim12/NeuroAgent/issues). Issues labelled `good first issue` are scoped for new contributors.
- Open a new issue **before** starting on anything non-trivial so we can align on scope.
- Comment on the issue to claim it.

---

## 3. Branch, commit, and push

We follow **GitHub Flow** — `main` is always deployable, all work happens on short-lived branches.

```bash
git checkout -b feat/short-descriptive-slug
# ... code ...
git push -u origin feat/short-descriptive-slug
```

**Branch prefixes:** `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `perf/`, `ci/`.

**Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary, imperative mood, no trailing period>

[optional body explaining the *why*, wrapped at 72 chars]

[optional footer: BREAKING CHANGE, Closes #123]
```

Examples:

```
feat(agent): add Groq Llama 3 to the model router
fix(auth): reject expired JWTs with 401 instead of 500
docs(readme): document the evaluation benchmark CLI
```

Every commit must build and pass the relevant checks — no broken commits. Rebase locally if you need to clean up history before opening a PR.

---

## 4. Code style and standards

The full standards live in [CLAUDE.md](CLAUDE.md); the highlights that the automation enforces:

**Backend (Python 3.11+)**

```bash
cd backend
ruff check .           # lint (must pass)
ruff check . --fix     # auto-fix what's fixable
mypy app/              # type check (informational in CI, aim for clean locally)
pytest tests/ -v       # full suite
```

**Frontend (Next.js 14 / TypeScript)**

```bash
cd frontend
npm run lint
npm run type-check
npm run build          # production build must succeed
```

**Conventions**

- Layer separation: route handlers stay thin; put business logic in `app/services/`.
- Pydantic v2 schemas for every request/response.
- Tests live under `backend/tests/` (Python) and mirror the source tree.
- File naming: `snake_case` in Python, `kebab-case` for frontend files.
- Functions target ≤ 30 lines; nesting ≤ 3 levels — refactor if you exceed either.
- Never commit secrets. All configuration flows through `app.config.Settings` / `.env`.

---

## 5. Tests are required

- Every new feature ships with tests.
- Bug fixes ship with a regression test that fails before the fix and passes after.
- Business-logic coverage target: **≥ 80%**. Critical paths (auth, agent graph, tools) aim for 100%.
- The benchmark suite (`python -m tests.eval.benchmark`) is not required for every change but please run the relevant slice if you touch agent behaviour.

---

## 6. Open a Pull Request

- Target `main`.
- Fill in every section of the [PR template](.github/pull_request_template.md). Link the issue with `Closes #N`.
- CI must be green before review.
- Keep PRs focused — one concern per PR is easier to review and revert.
- Respond to review comments with either a fix or a justification; resolve threads only when addressed.

---

## 7. Releases

- Versioning follows [SemVer](https://semver.org): `MAJOR.MINOR.PATCH`.
- Add an entry under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md) with every user-visible change.
- Maintainers cut releases by moving `[Unreleased]` notes under a new version and tagging `vX.Y.Z`.

---

## 8. Architecture Decision Records

For non-trivial technical decisions (adding a new LLM provider, changing the memory store, swapping the graph orchestration layer, etc.) add an ADR under [docs/adr/](docs/adr/). Use the existing records as templates — Context → Decision → Consequences.

---

## 9. Questions

Open a [GitHub Discussion](https://github.com/amunim12/NeuroAgent/discussions) or an issue. We try to respond within a few days.
