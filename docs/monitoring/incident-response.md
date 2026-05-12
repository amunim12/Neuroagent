# Incident Response Plan

**Version:** 1.0
**Date:** 2026-04-19
**Contact:** abdulmunim.personal@gmail.com

---

## Severity Definitions

| Severity | Description | Response time |
|---|---|---|
| **P1 — Critical** | Service is completely down or producing incorrect results for all users | Immediate (within 30 min) |
| **P2 — High** | Significant feature degradation; most agent runs fail; cost spike | Within 2 hours |
| **P3 — Medium** | Partial degradation; some task categories fail; elevated latency | Within 24 hours |
| **P4 — Low** | Minor issue; workaround exists; single user impact | Next scheduled review |

---

## General Response Process

1. **Detect** — alert fires (LangSmith, Railway), or user reports via GitHub Issues.
2. **Triage** — identify severity and affected component from the playbooks below.
3. **Communicate** — update GitHub Discussions (`neuroagent` → Incidents category) with initial diagnosis within 30 min (P1/P2).
4. **Mitigate** — apply the fastest available mitigation (restart, config change, rollback).
5. **Resolve** — confirm the fix with a health check and a benchmark run subset.
6. **Post-mortem** — within 72 hours of P1/P2 resolution, open a GitHub Issue labelled `post-mortem` documenting timeline, root cause, mitigation, and follow-up actions.

---

## Playbook 1: API is down (P1)

**Symptoms:** `/api/v1/health` returns non-200; Railway shows service crashed or restarting.

**Diagnosis steps:**

```bash
# Check Railway logs (Railway dashboard → Deployments → latest → Logs)
# Or locally:
make logs           # tails all container logs
make logs s=backend # backend only
```

Look for:
- `uvicorn` startup error (usually a missing env var or failed DB connection).
- `alembic upgrade head` failed during container startup.
- Out-of-memory kill (Railway shows `OOMKilled`).

**Mitigations:**

| Cause | Mitigation |
|---|---|
| Missing env var | Add the var in Railway dashboard → Variables; trigger redeploy |
| DB migration failed | SSH into container or run `alembic upgrade head` manually; check migration SQL |
| OOMKilled | Scale up Railway service RAM (512 MB → 1 GB); check for memory leak |
| Bad deploy (new commit broke startup) | Railway → Deployments → roll back to previous deployment |

**Recovery confirmation:**

```bash
curl https://<your-railway-domain>/api/v1/health   # expect 200
```

---

## Playbook 2: All agent runs fail with 500 (P1/P2)

**Symptoms:** `POST /api/v1/agent/run` returns 500 or all WebSocket connections immediately emit `{"type": "error"}`.

**Diagnosis steps:**

1. Check LangSmith project for recent runs — are all runs ending at the `plan` node with an exception?
2. Check Railway logs for the last error traceback.
3. Manually trigger a test run:

```bash
# Get a JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"hunter2"}' | jq -r .access_token)

# Fire a minimal goal
curl -s -X POST http://localhost:8000/api/v1/agent/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Say hello"}'
```

**Common causes and mitigations:**

| Cause | Mitigation |
|---|---|
| OpenAI / Anthropic / Groq API key expired or rate-limited | Rotate key in Railway → Variables; check provider dashboard for rate limit reset |
| LangSmith key invalid (tracing fails, run never starts) | Set `LANGCHAIN_TRACING_V2=false` in env vars to disable tracing as a temporary mitigation |
| Pinecone index not found | Re-run `python scripts/setup_pinecone.py` with correct `PINECONE_INDEX_NAME` |
| Redis unavailable (session memory fails) | Check `REDIS_URL`; restart Redis service; verify `docker compose ps` |
| DB schema mismatch after migration | Run `alembic upgrade head` inside the backend container |

---

## Playbook 3: LLM provider outage (P2)

**Symptoms:** Runs succeed but a specific model tier always fails. LangSmith shows `execute` node errors with `openai.APIConnectionError`, `anthropic.APIStatusError`, or `groq.APIConnectionError`.

**Diagnosis:**

Check provider status pages:
- OpenAI: https://status.openai.com
- Anthropic: https://status.anthropic.com
- Groq: https://status.groq.com

**Mitigations:**

```python
# In backend/app/config.py, temporarily force all routing to the working provider:
# Set FORCE_MODEL=gpt-4o (or claude-sonnet-4-6, or groq/llama3-70b-8192) via env var
# The router.py should check this override before applying heuristics.
```

If `FORCE_MODEL` override is not yet implemented (v1 — it isn't), set the affected provider's API key to an invalid value to force the fallback chain: Groq → Claude Sonnet → GPT-4o.

---

## Playbook 4: Cost spike (P2)

**Symptoms:** LangSmith daily spend alert fires; GPT-4o token usage is 3–5× normal.

**Diagnosis:**

1. Open LangSmith → filter by `router.model = gpt-4o` for today's runs.
2. Check if a small number of runs are consuming most tokens (one user sending very long goals).
3. Check if `router.rule` shows most subtasks routing to GPT-4o unexpectedly.

**Mitigations:**

| Cause | Mitigation |
|---|---|
| One user flooding long goals | Temporarily revoke their JWT; investigate; consider tighter rate limiting |
| Router misclassification (all subtasks to GPT-4o) | Identify the triggering keyword pattern; add it to the Groq or Sonnet rule in `router.py`; deploy |
| Provider sent an inflated token count | Compare LangSmith numbers to provider dashboard; contact support if discrepancy |

**Immediate stop-gap:** Set `OPENAI_API_KEY=invalid` in Railway env vars to disable GPT-4o routing. Runs will fall back to Claude Sonnet, reducing cost at the expense of quality on complex tasks. Restore once root cause is identified.

---

## Playbook 5: Benchmark pass rate drops > 5 pp (P3)

**Symptoms:** Weekly benchmark run shows a statistically significant regression vs. the previous baseline.

**Diagnosis steps:**

```bash
cd backend
python -m tests.eval.benchmark
python -m tests.eval.compare_reports   # diff latest.json vs previous
```

Identify which category regressed and look at the specific failing tasks.

**Common causes:**

| Cause | Mitigation |
|---|---|
| Provider updated model behind the same ID | Pin the model ID in `app/config.py`; compare outputs with the previous model version |
| LangGraph minor-version upgrade changed node API | Check `requirements.txt` diff; pin previous LangGraph version; open upstream issue |
| Pinecone recall degradation (old entries diluting results) | Delete low-quality vectors; run consolidation script (when available) |
| Benchmark dataset expanded with harder tasks | Re-baseline; update target metrics in `docs/project-brief.md` and `docs/model-card.md` |

---

## Playbook 6: Database migration failure on deploy (P2)

**Symptoms:** Backend container repeatedly restarts; logs show `alembic upgrade head` failing.

**Diagnosis:**

```bash
# Locally
cd backend
alembic upgrade head --sql   # preview the SQL without running it
```

**Mitigations:**

| Cause | Mitigation |
|---|---|
| Migration SQL errors on the target DB state | Inspect the migration file; fix the SQL; create a corrective migration |
| Migration applied partially (interrupted) | Connect to DB; manually check `alembic_version` table; resolve the partial state |
| Rollback required | `alembic downgrade -1`; fix the migration; redeploy |

**Prevention:** Never squash or edit merged migrations. Every schema change gets a new Alembic revision.

---

## Post-Mortem Template

```markdown
# Incident Post-Mortem — <title>

**Date:** YYYY-MM-DD
**Severity:** P1 / P2
**Duration:** HH:MM (detected at X, resolved at Y)
**Author:** <name>

## Summary
One paragraph describing what happened, what was affected, and how it was resolved.

## Timeline
- HH:MM — Alert detected / user report received
- HH:MM — Diagnosis started
- HH:MM — Root cause identified
- HH:MM — Mitigation applied
- HH:MM — Service restored
- HH:MM — Post-mortem started

## Root Cause
What actually went wrong.

## Impact
How many users were affected; what features were unavailable; any data loss.

## What Went Well
Things that helped us detect and respond quickly.

## What Went Wrong
Things that slowed us down or made the impact worse.

## Action Items
| Action | Owner | Due date |
|---|---|---|
| ... | ... | ... |
```
