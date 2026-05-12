# Model Card — NeuroAgent LLM Components

**Version:** 1.0
**Date:** 2026-04-19
**Contact:** abdulmunim.personal@gmail.com

This document follows the [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) framework (Mitchell et al., 2019) adapted for a system that orchestrates multiple third-party LLMs rather than owning a single trained model.

---

## 1. Model Details

NeuroAgent does not train or fine-tune its own language models. It orchestrates three third-party foundation models via a **heuristic model router** that selects the cheapest-sufficient model per subtask.

### 1.1 Models in use

| Model | Provider | Role | Context window |
|---|---|---|---|
| `llama3-70b-8192` | Groq | Fast retrieval, summarisation, simple Q&A | 8 192 tokens |
| `claude-sonnet-4-6` | Anthropic | Structured reasoning, code generation, JSON extraction | 200 k tokens |
| `gpt-4o` | OpenAI | Complex multi-step reasoning, ambiguous goals, fallback | 128 k tokens |

### 1.2 Embedding model

| Model | Provider | Usage |
|---|---|---|
| `text-embedding-3-small` | OpenAI | Encoding goals and answers for Pinecone long-term memory (1 536 dims) |

### 1.3 Router logic (v1 — heuristic)

The `route_model` node in `backend/app/agent/nodes/router.py` selects a model based on keyword signals in the current subtask description:

- **Groq Llama 3** — subtasks containing retrieval, summarise, list, describe, explain keywords and no code generation signals.
- **Claude Sonnet** — subtasks containing write code, generate, implement, debug, parse JSON, extract structured.
- **GPT-4o** — subtasks that are ambiguous, exceed Groq's context window estimate, or explicitly require complex multi-step reasoning.

**Known limitation:** This is a keyword heuristic, not a trained classifier. It misroutes approximately 1-in-10 subtasks based on internal spot-checks (50 runs). A fine-tuned classifier is scoped for v1.1. See [ADR-0002](adr/0002-multi-model-routing.md).

---

## 2. Intended Use

### Primary intended use

Autonomous execution of multi-step natural-language goals by software engineers and technical users in a local or self-hosted environment.

### Out-of-scope uses

- **Medical, legal, or financial advice.** NeuroAgent's outputs are not reviewed by domain experts and must not be relied upon for high-stakes decisions.
- **Unattended production automation.** The agent has access to real tools (web search, code execution, HTTP calls). Running it unattended on production systems without human-in-the-loop review is explicitly out of scope until v1.2 checkpoints are implemented.
- **High-volume batch processing.** The system is designed for interactive use. Sending thousands of automated goals will exhaust API rate limits and incur significant cost.
- **Processing sensitive PII at scale.** User-submitted goals may contain personal data. This data is passed to third-party LLM providers (OpenAI, Anthropic, Groq) under their respective data-handling terms.

---

## 3. Training Data

NeuroAgent does not train its own models. The foundation models used (GPT-4o, Claude Sonnet, Groq Llama 3) were trained by their respective providers. Refer to their model cards and data governance documentation:

- [OpenAI GPT-4o model card](https://openai.com/index/gpt-4o-system-card/)
- [Anthropic Claude model card](https://www.anthropic.com/model-card)
- [Meta LLaMA 3 model card](https://llama.meta.com/llama3/model-cards/)

The evaluation benchmark (`backend/tests/eval/dataset.json`) contains 20 tasks hand-authored by the NeuroAgent maintainer. It is not used to train any model.

---

## 4. Performance

All numbers come from the built-in 20-task evaluation benchmark. Run `python -m tests.eval.benchmark` inside `backend/` to reproduce.

### 4.1 Benchmark summary

| Metric | Target | Baseline (run benchmark to populate) |
|---|---|---|
| Pass rate — overall | ≥ 80 % | — |
| Pass rate — `reasoning` | ≥ 80 % | — |
| Pass rate — `web_research` | ≥ 80 % | — |
| Pass rate — `coding` | ≥ 80 % | — |
| Pass rate — `synthesis` | ≥ 80 % | — |
| Pass rate — `multi_step` | ≥ 80 % | — |
| Mean end-to-end latency | ≤ 45 s | — |
| P95 latency | ≤ 90 s | — |
| Mean cost / task | ≤ $0.05 | — |

Commit populated numbers to this file when publishing a release.

### 4.2 Known failure modes

- **Groq context overflow:** subtasks that produce > 8 k tokens of context cause the executor to fall back to GPT-4o. The fallback works but increases cost and adds ~5 s of latency.
- **Playwright bot detection:** browser tool calls fail silently on sites with Cloudflare Turnstile or similar protection. The planner does not retry with a different tool.
- **Long sequential plans:** plans with > 7 subtasks occasionally exceed the planner's structured-output schema validation, producing a malformed subtask list. The executor catches this and returns a partial result.
- **Hallucinated tool arguments:** rare (< 2 % of tool calls) but the executor does not validate tool input schemas before calling E2B or httpx.

---

## 5. Ethical Considerations

### 5.1 Data privacy

User goals and agent outputs are stored in PostgreSQL (per session) and Pinecone (long-term memory). Both are tied to the authenticated user's account. No data is shared between users. Deployers who run NeuroAgent as a hosted service must:

- Disclose to users that goal text is sent to OpenAI, Anthropic, and Groq.
- Comply with applicable data protection regulations (GDPR, CCPA) before processing goals that may contain PII.
- Implement a data retention and deletion policy for session data and Pinecone vectors.

### 5.2 Misuse potential

The agent can execute arbitrary Python code (via E2B sandbox), make HTTP requests to any URL, and automate a real browser. These capabilities could be misused to:

- Scrape websites at high volume.
- Send automated requests to third-party APIs on behalf of users.
- Execute malicious code if a prompt injection attack manipulates the planner.

**Mitigations in place:**

- Code execution is fully sandboxed inside E2B; it has no access to the host filesystem or network beyond E2B's own sandbox egress.
- Input validation at the API boundary (`/api/v1/agent/run`) enforces maximum goal length and basic sanitisation.
- Rate limiting via SlowAPI limits burst submissions per user.

**Mitigations not yet implemented (v1.2 roadmap):**

- Human-in-the-loop confirmation gate for tool calls flagged as potentially destructive.
- Per-session and per-user token/cost budgets enforced at the router.

### 5.3 Bias and fairness

The underlying foundation models (GPT-4o, Claude, Llama 3) carry the biases present in their training data. NeuroAgent does not apply additional debiasing. Goals that ask the agent to make judgments about people, groups, or sensitive topics will reflect the biases of whichever model is routed to handle the subtask.

---

## 6. Caveats and Recommendations

- **Always review agent outputs before acting on them.** The agent may produce plausible-sounding but incorrect code, factually wrong research summaries, or hallucinated tool results.
- **Pin model versions in production.** Provider models are updated without notice; new versions may change output format or quality. The `requirements.txt` pins SDK versions; pin model IDs in `app/config.py` for reproducibility.
- **Monitor cost continuously.** The router can misclassify subtasks and route expensive tasks to GPT-4o unexpectedly. LangSmith dashboards provide per-run token accounting; set budget alerts.
- **Do not use for real-money transactions or irreversible actions** without explicit human confirmation at each step.

---

## 7. References

- [docs/adr/0002-multi-model-routing.md](adr/0002-multi-model-routing.md) — routing decision rationale
- [docs/adr/0003-hybrid-memory-architecture.md](adr/0003-hybrid-memory-architecture.md) — memory architecture rationale
- [docs/monitoring/strategy.md](monitoring/strategy.md) — how model behaviour is monitored in production
- [backend/app/agent/nodes/router.py](../backend/app/agent/nodes/router.py) — router implementation
- [backend/tests/eval/](../backend/tests/eval/) — evaluation benchmark
