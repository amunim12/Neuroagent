# Experiment Tracking

This directory logs experiments that improve NeuroAgent's quality, cost, or latency. Each experiment lives in its own subdirectory with a structured log and any supporting artefacts.

---

## Why track experiments?

NeuroAgent's pipeline involves several components that respond to parameter changes: the model router heuristics, the planner prompt, the executor's ReAct prompt, the memory top-k value, and the benchmark scoring thresholds. Without tracking, it's easy to lose the context behind a decision ("why did we change the router to prefer Sonnet for this keyword?") and hard to compare results across changes.

The goal is not heavyweight MLflow infrastructure — it's a lightweight paper trail that lives in git alongside the code.

---

## Directory structure

```
docs/experiments/
├── README.md          ← this file
├── EXP-001-router-keyword-tuning/
│   ├── experiment.md  ← structured log (see template below)
│   └── results.json   ← raw benchmark output
├── EXP-002-planner-prompt-v2/
│   ├── experiment.md
│   └── results.json
└── ...
```

Name experiment directories `EXP-<NNN>-<short-slug>` (zero-padded to 3 digits).

---

## Experiment log template

Copy this template into a new `experiment.md` inside a new `EXP-NNN-<slug>/` directory.

```markdown
# EXP-<NNN>: <Title>

**Status:** Planned | Running | Completed | Abandoned
**Date started:** YYYY-MM-DD
**Date completed:** YYYY-MM-DD (or — if ongoing)
**Author:** <name>

## Hypothesis

One sentence: what do we expect to happen, and why?

_Example: "Adding 'analyse' to the GPT-4o keyword list will reduce routing misclassification
on reasoning-heavy subtasks, improving the `reasoning` benchmark category pass rate by ≥ 5 pp."_

## Motivation

What problem or observation prompted this experiment? Link to a LangSmith run, GitHub issue,
or benchmark report that surfaced the issue.

## Setup

### What changed

Describe the code change precisely. Include file path and the before/after diff (or a link to the PR).

### Evaluation method

How will you measure success? Which benchmark categories? How many runs? What's the success threshold?

_Example: "Run `python -m tests.eval.benchmark --category reasoning` (4 tasks). Compare pass rate
and mean latency against the baseline in `EXP-000-baseline/results.json`."_

### Controlled variables

What did you hold constant to isolate the effect of the change?

_Example: "Same API keys, same Pinecone index, same benchmark dataset version."_

## Results

| Metric | Baseline | This experiment | Delta |
|---|---|---|---|
| Pass rate — reasoning | — % | — % | — pp |
| Pass rate — overall | — % | — % | — pp |
| Mean latency | — s | — s | — s |
| Mean cost / task | $— | $— | $— |
| GPT-4o routing share | — % | — % | — pp |

Raw results: `results.json` in this directory.

## Analysis

What do the numbers mean? Did the hypothesis hold? Were there unexpected effects in other categories?

## Decision

- [ ] **Ship it** — merge to main; update `router.py` / prompt / config as appropriate.
- [ ] **Iterate** — hypothesis partially validated; refine and run EXP-NNN+1.
- [ ] **Abandon** — hypothesis rejected; document why so we don't repeat it.

## Follow-up

Any actions, new experiments, or GitHub Issues created as a result of this experiment.
```

---

## Baseline

Before running any experiment, establish a baseline by running the full benchmark and saving the result:

```bash
cd backend
python -m tests.eval.benchmark
cp tests/eval/reports/latest.json ../docs/experiments/EXP-000-baseline/results.json
```

All subsequent experiments compare their `results.json` to `EXP-000-baseline/results.json`.

---

## Running the benchmark

```bash
cd backend

# Full suite (20 tasks) — use for final experiment evaluation
python -m tests.eval.benchmark

# Single category — use for fast iteration during an experiment
python -m tests.eval.benchmark --category reasoning
python -m tests.eval.benchmark --category coding

# Limit to N tasks — use for smoke-testing a change
python -m tests.eval.benchmark --limit 5

# Dry run (validate dataset, no API calls)
python -m tests.eval.benchmark --dry-run
```

Results land in `backend/tests/eval/reports/latest.json`. Copy this file into the experiment directory before running another benchmark (it is overwritten on each run).

---

## Current experiments

| ID | Title | Status | Pass rate delta | Decision |
|---|---|---|---|---|
| EXP-000 | Baseline — v1.0 release | Completed | — | Baseline |

Add a row here when starting a new experiment. Update the row when it concludes.

---

## Tips

- **One variable at a time.** Changing the router and the planner prompt simultaneously makes it impossible to attribute the result to either.
- **Save the raw `results.json`** before running another benchmark. The file is overwritten and git-ignored (`backend/tests/eval/reports/`).
- **Commit the experiment log even if the result is negative.** A failed experiment that's documented prevents the same idea from being tried again in 6 months.
- **Link LangSmith runs.** Copy the run URL from the LangSmith dashboard into the experiment log for the most representative run. This gives reviewers a live trace to inspect.
