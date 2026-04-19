"""Benchmark runner for NeuroAgent.

Executes the curated dataset (``tests.eval.dataset``) against the live agent
graph and reports aggregate success rate, latency, and token usage. The runner
is intentionally simple so the results stay reproducible:

* one agent invocation per task, no retries
* deterministic offline scoring (see ``tests.eval.scoring``)
* JSON report written to disk for diffing against previous runs

Typical usage (from the ``backend/`` directory):

    python -m tests.eval.benchmark                      # full suite
    python -m tests.eval.benchmark --limit 5            # first 5 tasks
    python -m tests.eval.benchmark --category coding    # one slice
    python -m tests.eval.benchmark --dry-run            # validate dataset only
    python -m tests.eval.benchmark --output report.json # custom output path

The runner requires the same environment variables as the application
(OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, TAVILY_API_KEY, ...).
Missing keys surface as per-task failures rather than aborting the whole run.
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tests.eval.dataset import BENCHMARK_TASKS, BenchmarkTask, categories
from tests.eval.scoring import TaskScore, score_task

logger = logging.getLogger("neuroagent.eval")

DEFAULT_OUTPUT = Path("tests/eval/reports/latest.json")


@dataclass
class TaskRunResult:
    """Outcome of a single benchmark task execution."""

    task_id: str
    category: str
    goal: str
    final_answer: str
    used_tools: list[str]
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error: str | None
    score: TaskScore

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "category": self.category,
            "goal": self.goal,
            "final_answer": self.final_answer,
            "used_tools": self.used_tools,
            "latency_seconds": round(self.latency_seconds, 3),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "error": self.error,
            "score": self.score.to_dict(),
        }


@dataclass
class BenchmarkReport:
    """Aggregate benchmark results across every task in a run."""

    total: int
    passed: int
    failed: int
    pass_rate: float
    mean_latency_seconds: float
    p95_latency_seconds: float
    total_tokens: int
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)
    results: list[TaskRunResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 4),
            "mean_latency_seconds": round(self.mean_latency_seconds, 3),
            "p95_latency_seconds": round(self.p95_latency_seconds, 3),
            "total_tokens": self.total_tokens,
            "by_category": self.by_category,
            "results": [r.to_dict() for r in self.results],
        }


def _build_token_counter() -> tuple[Any, dict[str, int]]:
    """Return a LangChain callback + mutable tally of token usage.

    The tally is populated during each LLM call; reading it after the graph
    returns gives per-task usage. Importing ``BaseCallbackHandler`` lazily
    keeps ``--dry-run`` working without LangChain installed.
    """
    from langchain_core.callbacks import BaseCallbackHandler

    tally = {"input": 0, "output": 0, "total": 0}

    class TokenCounter(BaseCallbackHandler):
        def on_llm_end(self, response, **_kwargs):  # type: ignore[override]
            for gen_list in getattr(response, "generations", []) or []:
                for gen in gen_list:
                    message = getattr(gen, "message", None)
                    usage = getattr(message, "usage_metadata", None) if message else None
                    if not usage:
                        continue
                    tally["input"] += int(usage.get("input_tokens", 0) or 0)
                    tally["output"] += int(usage.get("output_tokens", 0) or 0)
                    tally["total"] += int(usage.get("total_tokens", 0) or 0)

    return TokenCounter(), tally


def _run_single_task(task: BenchmarkTask) -> TaskRunResult:
    """Invoke the agent on one task and collect metrics."""
    # Import lazily so --dry-run can run without the full agent dependency tree.
    from app.agent.graph import agent_graph
    from app.agent.state import AgentState
    from app.utils.tracing import run_config

    session_id = f"eval-{task.id}-{uuid.uuid4().hex[:8]}"
    used_tools: set[str] = set()

    def capture(event: dict[str, Any]) -> None:
        if event.get("type") == "tool_call":
            tool = event.get("tool")
            if isinstance(tool, str):
                used_tools.add(tool)

    initial_state: AgentState = {
        "goal": task.goal,
        "session_id": session_id,
        "user_id": "eval-harness",
        "messages": [],
        "subtasks": [],
        "current_task_index": 0,
        "tool_outputs": [],
        "retrieved_memory": [],
        "selected_model": "gpt-4o",
        "final_answer": "",
        "is_complete": False,
        "error": None,
        "stream_callback": capture,
    }

    callback, tally = _build_token_counter()
    config = run_config(session_id=session_id, user_id="eval-harness", goal=task.goal)
    config["callbacks"] = [callback]

    final_answer = ""
    error: str | None = None
    started = time.perf_counter()
    try:
        final_state = agent_graph.invoke(initial_state, config=config)
        final_answer = final_state.get("final_answer") or ""
        if final_state.get("error"):
            error = str(final_state["error"])
    except Exception as exc:  # noqa: BLE001 - surface any failure per-task
        error = f"{type(exc).__name__}: {exc}"
        logger.exception("Task %s raised during agent invocation", task.id)
    latency = time.perf_counter() - started

    score = score_task(task, final_answer, used_tools=used_tools)

    return TaskRunResult(
        task_id=task.id,
        category=task.category,
        goal=task.goal,
        final_answer=final_answer,
        used_tools=sorted(used_tools),
        latency_seconds=latency,
        input_tokens=tally["input"],
        output_tokens=tally["output"],
        total_tokens=tally["total"],
        error=error,
        score=score,
    )


def _aggregate(results: list[TaskRunResult]) -> BenchmarkReport:
    """Fold per-task results into a single benchmark report."""
    total = len(results)
    passed = sum(1 for r in results if r.score.passed)
    latencies = [r.latency_seconds for r in results] or [0.0]
    mean_latency = statistics.fmean(latencies)
    p95_latency = _percentile(latencies, 0.95)
    total_tokens = sum(r.total_tokens for r in results)

    by_category: dict[str, dict[str, float]] = {}
    for result in results:
        bucket = by_category.setdefault(
            result.category,
            {"total": 0, "passed": 0, "mean_latency_seconds": 0.0, "total_tokens": 0},
        )
        bucket["total"] += 1
        bucket["passed"] += 1 if result.score.passed else 0
        bucket["mean_latency_seconds"] += result.latency_seconds
        bucket["total_tokens"] += result.total_tokens

    for bucket in by_category.values():
        count = bucket["total"] or 1
        bucket["mean_latency_seconds"] = round(bucket["mean_latency_seconds"] / count, 3)
        bucket["pass_rate"] = round(bucket["passed"] / count, 4)

    return BenchmarkReport(
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=(passed / total) if total else 0.0,
        mean_latency_seconds=mean_latency,
        p95_latency_seconds=p95_latency,
        total_tokens=total_tokens,
        by_category=by_category,
        results=results,
    )


def _percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile — avoids a numpy dependency for one calc."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(pct * (len(ordered) - 1)))))
    return ordered[index]


def _select_tasks(args: argparse.Namespace) -> list[BenchmarkTask]:
    tasks: list[BenchmarkTask] = list(BENCHMARK_TASKS)
    if args.category:
        tasks = [t for t in tasks if t.category == args.category]
    if args.task_id:
        tasks = [t for t in tasks if t.id == args.task_id]
    if args.limit:
        tasks = tasks[: args.limit]
    return tasks


def _print_summary(report: BenchmarkReport) -> None:
    print()
    print("=" * 72)
    print(f"Benchmark results: {report.passed}/{report.total} passed "
          f"({report.pass_rate:.1%})")
    print(f"Mean latency: {report.mean_latency_seconds:.2f}s  "
          f"p95: {report.p95_latency_seconds:.2f}s  "
          f"Total tokens: {report.total_tokens:,}")
    print("-" * 72)
    print(f"{'task':<14}{'cat':<14}{'pass':<6}{'score':<8}{'lat(s)':<9}{'tokens':<8}")
    print("-" * 72)
    for result in report.results:
        mark = "PASS" if result.score.passed else "FAIL"
        print(
            f"{result.task_id:<14}{result.category:<14}{mark:<6}"
            f"{result.score.score:<8.2f}{result.latency_seconds:<9.2f}"
            f"{result.total_tokens:<8}"
        )
    print("-" * 72)
    print("By category:")
    for cat, stats in sorted(report.by_category.items()):
        print(
            f"  {cat:<14} {int(stats['passed'])}/{int(stats['total'])} "
            f"({stats.get('pass_rate', 0):.1%})  "
            f"mean {stats['mean_latency_seconds']:.2f}s  "
            f"tokens {int(stats['total_tokens']):,}"
        )
    print("=" * 72)


def _write_report(path: Path, report: BenchmarkReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


def _dry_run(tasks: list[BenchmarkTask]) -> int:
    print(f"Loaded {len(tasks)} task(s) across categories: {', '.join(categories())}")
    for task in tasks:
        print(f"  [{task.id}] ({task.category}) {task.goal[:80]}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the NeuroAgent evaluation benchmark.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N tasks after filtering.")
    parser.add_argument("--category", default=None, help="Run only tasks in this category.")
    parser.add_argument("--task-id", default=None, help="Run only the task with this id.")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"Report output path (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List selected tasks and exit without invoking the agent.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable DEBUG-level logging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    tasks = _select_tasks(args)
    if not tasks:
        print("No tasks match the given filters.", file=sys.stderr)
        return 2

    if args.dry_run:
        return _dry_run(tasks)

    results: list[TaskRunResult] = []
    for idx, task in enumerate(tasks, 1):
        print(f"[{idx}/{len(tasks)}] Running {task.id} ({task.category})...")
        result = _run_single_task(task)
        mark = "PASS" if result.score.passed else "FAIL"
        print(
            f"  -> {mark}  score={result.score.score:.2f}  "
            f"lat={result.latency_seconds:.2f}s  tokens={result.total_tokens}"
            + (f"  error={result.error}" if result.error else "")
        )
        results.append(result)

    report = _aggregate(results)
    _print_summary(report)
    _write_report(args.output, report)
    print(f"\nReport written to {args.output}")

    return 0 if report.pass_rate >= 0.5 else 1


__all__ = [
    "BenchmarkReport",
    "TaskRunResult",
    "main",
    "parse_args",
]


if __name__ == "__main__":
    raise SystemExit(main())
