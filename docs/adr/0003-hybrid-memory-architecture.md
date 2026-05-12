# ADR-0003: Hybrid memory architecture (Redis + Pinecone)

**Status:** Accepted
**Date:** 2026-04-19
**Deciders:** Core maintainers
**Supersedes:** —

---

## Context

NeuroAgent must support two distinct memory horizons:

1. **Short-term / within-session memory:** The planner and executor need access to the conversation history and intermediate results from earlier steps in the current run. This context must be available in milliseconds and is only relevant for the duration of the session.

2. **Long-term / cross-session memory:** When a returning user submits a new goal, the planner should be able to recall semantically related goals and outcomes from previous sessions. This enables personalisation ("last time you researched Python frameworks, you preferred async ones") and avoids duplicated work. This context must survive process restarts and support semantic (not exact) search.

### Requirements

| Requirement | Short-term | Long-term |
|---|---|---|
| Latency | < 5 ms | < 100 ms |
| Persistence across restarts | Not required | Required |
| Search type | Key-based (session ID) | Semantic (vector similarity) |
| Scale | Current session (< 50 messages) | Per-user history (potentially 1 000s of entries) |
| Eviction | TTL-based (session ends) | Manual or scheduled consolidation |

### Candidate approaches

**Short-term options considered:**

1. **PostgreSQL session table.** Reliable, persistent, but query latency for small payloads is 5–20 ms — too slow for the hot path between nodes in the LangGraph state machine.
2. **In-memory Python dict / LangGraph checkpointer.** Zero latency but lost on process restart. Acceptable for demos but not suitable for Railway deploys that restart on redeploy.
3. **Redis.** Sub-millisecond reads/writes, optional TTL, serialise message lists as JSON. Lives outside the app process so survives restarts (within the Docker Compose stack). Standard for this use case.

**Long-term options considered:**

1. **PostgreSQL with `pgvector`.** Single database, no extra service. `pgvector` supports cosine similarity on 1 536-dim vectors. Performance degrades noticeably past ~100 k rows without IVFFlat tuning; requires self-managing embeddings and index maintenance.
2. **Pinecone (managed vector store).** Fully managed, built for semantic search, Starter tier is free for up to 100 k vectors, SDK is well-documented. No infrastructure to run. Latency: 20–80 ms for top-k queries.
3. **Weaviate / Qdrant (self-hosted).** More control over infrastructure and data residency. Adds a Docker service to the stack, operational overhead. Not worth it at v1 scale.

---

## Decision

We use a **two-tier hybrid architecture**:

- **Redis 7** for short-term session memory.
- **Pinecone** (managed, Starter tier) for long-term vector memory.

### Short-term memory (Redis)

Implementation: [`backend/app/agent/memory/short_term.py`](../../backend/app/agent/memory/short_term.py)

- Each session's message history is stored as a JSON-serialised list under key `session:{session_id}:messages`.
- TTL: 24 hours after last write. Sessions that expire from Redis are still queryable from PostgreSQL (sessions table) but without the fast message context.
- The `read_memory` node prepends the last N messages (configurable, default 20) from Redis into the planner's context.

### Long-term memory (Pinecone)

Implementation: [`backend/app/agent/memory/long_term.py`](../../backend/app/agent/memory/long_term.py)

- On `write_memory`, the goal + final synthesised answer is embedded with `text-embedding-3-small` (1 536 dims) and upserted into Pinecone under a namespace keyed by `user_id`.
- On `read_memory`, the current goal is embedded and a top-5 cosine similarity query is run against the user's namespace. The top-k results are prepended to the planner's context as prior-session context.
- Metadata stored per vector: `session_id`, `goal_preview` (first 200 chars), `created_at`, `category` (reserved for future filtering).

---

## Consequences

### Positive

- **Clean separation of concerns.** Redis handles transient, high-frequency reads with sub-millisecond latency. Pinecone handles semantic search which is inherently slower and called only twice per run (read and write).
- **No self-hosted vector infrastructure in v1.** Pinecone Starter tier is free and zero-maintenance at demo scale. This is the right trade-off until the project has proven demand.
- **Redis TTL prevents unbounded memory growth.** Old session message lists expire automatically without a cleanup job.
- **User-namespaced Pinecone index.** Namespace isolation ensures that semantic search is always scoped to the authenticated user; no cross-user recall leakage.

### Negative / trade-offs

- **Two external services required.** Contributors need Redis running locally. Docker Compose handles this automatically (`make dev`), but bare-metal setup requires an extra step.
- **Pinecone Starter tier limits.** 100 k vectors free. A production deployment with many active users will require a paid plan (or migration to `pgvector`).
- **No consolidation in v1.** As a user accumulates sessions, old, low-quality memories are not pruned. Recall quality degrades past ≈ 10 k entries per user as relevant results are diluted. A consolidation job is scoped for v1.1.
- **Short-term memory is not durable across restarts.** If Redis is restarted mid-session, the in-progress message history is lost and the run will fail. Docker Compose persists the Redis data volume, but cold container restarts during an active run will cause session loss.

### Alternative not taken: PostgreSQL-only

A single `pgvector`-backed table would simplify the stack (one fewer service). We decided against it for v1 because:

1. The Redis sub-millisecond message retrieval is on the hot path between LangGraph nodes. Adding 10–20 ms per node invocation would push mean latency above the 45 s target for complex tasks.
2. `pgvector` operational concerns (IVFFlat index tuning, VACUUM on high-write workloads) are non-trivial and out of scope for a demo project.

This decision should be revisited if Pinecone costs or operational concerns outweigh the complexity savings from consolidation.

---

## References

- [`backend/app/agent/memory/short_term.py`](../../backend/app/agent/memory/short_term.py) — Redis memory implementation
- [`backend/app/agent/memory/long_term.py`](../../backend/app/agent/memory/long_term.py) — Pinecone memory implementation
- [`backend/app/agent/nodes/`](../../backend/app/agent/nodes/) — `read_memory` and `write_memory` nodes
- [`scripts/setup_pinecone.py`](../../scripts/setup_pinecone.py) — one-off index bootstrap script
- [ADR-0001](0001-langgraph-agent-architecture.md) — overall agent architecture
