# ADR-0001: LangGraph-based agent architecture

**Status:** Accepted
**Date:** 2026-04-17
**Deciders:** Core maintainers
**Supersedes:** —

---

## Context

NeuroAgent needs to turn a free-form user goal into a concrete, observable, tool-using execution. The core requirements are:

- **Deterministic control flow.** We need explicit nodes (plan, route, execute, synthesize) so every run is reproducible and inspectable, not an opaque chain of LLM calls.
- **Streaming.** The frontend must show planning, tool calls, and synthesis as they happen over WebSocket — a request/response shape is not acceptable.
- **Multi-model routing.** Cost and latency differ by an order of magnitude between GPT-4o, Claude Sonnet, and Groq Llama 3. Each subtask must be dispatchable to the right model without rewriting the orchestration layer.
- **Typed state.** We want a single shared state object that nodes mutate in a structured way, with full LangSmith traces on every transition.
- **Loops with a safe exit.** The executor may iterate over N subtasks; the graph must short-circuit on error or `is_complete` without unbounded recursion.

Candidate orchestrators considered:

1. **Plain LangChain `AgentExecutor` (ReAct).** Mature, but tree-shaped and opaque: we can't cleanly insert memory read/write nodes, per-step model routing, or structured subtask planning without subclassing internals.
2. **CrewAI.** Role-based multi-agent; excellent DX for simulated teams, but overkill for a single-agent pipeline and less granular over streaming events.
3. **Homegrown state machine.** Maximum control but we'd be rebuilding cancellation, checkpointing, and tracing from scratch.
4. **LangGraph.** Explicit `StateGraph` with typed state, first-class conditional edges, native async, built-in LangSmith tracing, and seamless interop with LangChain tools and chat models.

## Decision

We use **LangGraph** as the agent's orchestration substrate. The graph is assembled in [`backend/app/agent/graph.py`](../../backend/app/agent/graph.py) and consists of six nodes over a single `AgentState` TypedDict:

```
 read_memory → plan → route_model → execute ──► (loop back to route_model)
                                       │
                                       ▼
                                  synthesize → write_memory → END
```

- `read_memory` pulls top-k semantic matches from Pinecone so the planner has user-specific prior context.
- `plan` decomposes the goal into 3–7 ordered subtasks via a structured-output LLM call.
- `route_model` selects the cheapest-sufficient model for the current subtask (heuristic now; classifier-based in a later ADR).
- `execute` runs a ReAct agent with the four tools (`web_search`, `code_executor`, `browser`, `api_caller`) bound to the chosen model.
- `should_continue` conditionally loops back to `route_model` while subtasks remain, or proceeds to `synthesize` on completion/error.
- `synthesize` combines all per-subtask outputs into the final answer.
- `write_memory` upserts the goal + final answer back into Pinecone for future recall.

Every node invokes a `stream_callback` (supplied by the WebSocket handler) to emit typed events (`planning`, `tool_call`, `final_answer`, `error`) to the frontend in real time.

## Consequences

### Positive

- **Explicit state and transitions.** Debugging a failed run is reading a linear trace of node transitions, not reverse-engineering an agent scratchpad.
- **Native LangSmith integration.** Every node shows up as a separate span with model/tool metadata — the observability story is free.
- **Cheap extensibility.** Adding a new capability (e.g. a `verify` node) is one function + one edge; the rest of the pipeline is untouched.
- **Cancellation and checkpointing.** LangGraph ships both; we can surface a "stop" button and resumable sessions without bespoke plumbing.
- **Streaming-first.** The per-node callback pattern maps cleanly onto WebSocket events, giving the UI the granularity it needs.

### Negative / trade-offs

- **Lock-in to LangChain conventions.** Tools, messages, and chat models follow LangChain's interfaces. Migrating away would require abstracting these at the node boundary.
- **Pre-1.0 API surface.** LangGraph is evolving quickly; minor-version upgrades have required small refactors. Pinned in `requirements.txt` to mitigate.
- **Heuristic model router is coarse.** Keyword matching misclassifies roughly 1-in-10 subtasks based on internal review. A follow-up ADR will replace it with a tiny classifier.

### Neutral

- The graph assumes subtasks are sequential. Parallel subtask execution (fan-out/fan-in) is possible with LangGraph but deliberately out of scope for v1 — see the open issue for the follow-up ADR.

## References

- [`backend/app/agent/graph.py`](../../backend/app/agent/graph.py) — graph assembly and conditional edge
- [`backend/app/agent/state.py`](../../backend/app/agent/state.py) — shared `AgentState`
- [`backend/app/agent/nodes/`](../../backend/app/agent/nodes/) — one file per node
- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
