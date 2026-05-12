# ADR-0002: Multi-model routing strategy

**Status:** Accepted
**Date:** 2026-04-19
**Deciders:** Core maintainers
**Supersedes:** —
**Superseded by:** — _(will be superseded when classifier-based routing is implemented)_

---

## Context

NeuroAgent's executor dispatches subtasks to one of three LLMs: Groq Llama 3 (fastest, cheapest), Anthropic Claude Sonnet (strong at code and structured output), and OpenAI GPT-4o (highest capability, highest cost). The cost and latency spread between the cheapest and most expensive option is roughly 30× per token. Without a routing layer, using GPT-4o for every subtask would make even a simple 3-step task cost $0.10–0.30 — an order of magnitude more than necessary.

### Routing requirements

1. **Accuracy:** The wrong model must not cause task failure. Sending a complex reasoning task to Groq Llama 3 is a correctness risk; sending a simple summarisation to GPT-4o is a pure cost waste.
2. **Latency:** The routing decision itself must add < 10 ms of overhead. A secondary LLM call to classify subtasks defeats the purpose.
3. **Explainability:** The routing decision must be inspectable in LangSmith traces so failures are debuggable.
4. **Graceful fallback:** If the selected model returns an error (rate limit, context overflow, provider outage), the executor must fall back to the next tier without user-visible failure.

### Candidate approaches

1. **Keyword heuristics (rule-based).** A function in the router node scans subtask descriptions for signal keywords and maps them to a model tier. Zero latency overhead, fully deterministic, easily debuggable. Imprecise: misses nuance in natural language.
2. **Small embedding-based classifier.** A fine-tuned `distilBERT` or `text-embedding-3-small + logistic regression` classifier trained on LangSmith traces labelled with the correct model tier. High accuracy potential, ~5 ms inference, requires a labelled training set.
3. **Routing via a cheap LLM call.** Send the subtask description to Groq Llama 3 with a prompt like "which model is best suited for this: [A, B, C]?". Adds ~500 ms and a secondary API call per subtask — the cost/latency overhead is too high.
4. **Fixed routing by position.** Plan node → Claude Sonnet (structured output), Executor → GPT-4o (always). Simple but wastes cost on all non-complex subtasks.

---

## Decision

We implement **keyword heuristics (approach 1) for v1**, with a clear migration path to approach 2.

The router in [`backend/app/agent/nodes/router.py`](../../backend/app/agent/nodes/router.py) applies the following rules in order:

1. If subtask description matches **code signals** (`write code`, `implement`, `debug`, `generate`, `parse json`, `extract structured`, `script`, `function`) → **Claude Sonnet**
2. If subtask description matches **complexity signals** (`analyse`, `compare trade-offs`, `design`, `architect`, `evaluate multiple`, `complex`) → **GPT-4o**
3. If estimated token count of the subtask context exceeds **6 000 tokens** (Groq's safe limit below the 8 192 ceiling) → **GPT-4o**
4. Default → **Groq Llama 3**

Fallback chain on API error or context overflow: Groq → Claude Sonnet → GPT-4o.

The selected model ID and the matched rule are logged as LangSmith span metadata (`router.model`, `router.rule`) for every subtask.

---

## Consequences

### Positive

- **Zero latency overhead.** The routing decision is a pure function on a string; < 1 ms.
- **Fully inspectable.** LangSmith traces show exactly which rule fired and which model was selected.
- **Cost-effective at current load.** In informal testing across 50 runs, ≈ 70 % of subtasks route to Groq (cost ≈ $0.001), ≈ 20 % to Claude Sonnet (cost ≈ $0.005), and ≈ 10 % to GPT-4o (cost ≈ $0.02). Average cost per 5-subtask run: $0.02–0.04.

### Negative / trade-offs

- **Misclassification rate ≈ 10 %.** Keyword matching is sensitive to phrasing. "Describe the algorithm and write a brief implementation note" should go to Claude Sonnet but may route to Groq if `write` is treated as a code signal. This can cause incorrect or lower-quality outputs on those subtasks.
- **Brittle to novel subtask phrasing.** Adding new tool types (e.g. a database query tool) will require manually extending the keyword list.
- **No learning signal.** Misclassifications are only discovered by reviewing LangSmith traces — the system cannot self-correct.

### Migration path to classifier-based routing

When the LangSmith trace history contains ≥ 500 labelled subtask–model pairs (exportable via the LangSmith SDK), replace the keyword function with:

1. Embed subtask descriptions with `text-embedding-3-small`.
2. Train a 3-class logistic regression or shallow MLP on the embeddings.
3. Serve the classifier as a 5 ms in-process call in the router node.
4. Keep the keyword heuristic as a fallback for low-confidence predictions (probability < 0.6).

Target accuracy: ≥ 93 %. This will supersede the current ADR with ADR-0002 rev 2.

---

## References

- [`backend/app/agent/nodes/router.py`](../../backend/app/agent/nodes/router.py) — router implementation
- [ADR-0001](0001-langgraph-agent-architecture.md) — overall agent architecture
- [docs/model-card.md](../model-card.md) — model documentation including known failure modes
- [LangSmith filtering docs](https://docs.smith.langchain.com/tracing/faq/filter) — how to export labelled traces for classifier training
