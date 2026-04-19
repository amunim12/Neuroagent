"""Deterministic scoring for benchmark runs.

Scoring is intentionally simple and offline — substring matching on the
``final_answer`` plus tool-usage checks. Keeping it lightweight avoids a
circular dependency on an LLM-as-judge: we are evaluating the agent, not the
judge.

Score composition (per task):
    * content score (75%): fraction of required substrings present, subject to
      ``scoring_mode`` ("any" passes with one match; "all" needs every match
      present). A must_not_include hit zeroes this component.
    * tool score (25%): fraction of ``expected_tools`` actually invoked. When
      the task lists no expected tools this component is treated as full
      credit so reasoning/synthesis tasks aren't penalised.

A task is considered *passed* when its aggregate score is >= ``PASS_THRESHOLD``
AND no ``must_not_include`` phrase appeared. The threshold (0.75) keeps the
"any" content rule compatible with a perfect tool match.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tests.eval.dataset import BenchmarkTask

CONTENT_WEIGHT = 0.75
TOOL_WEIGHT = 0.25
PASS_THRESHOLD = 0.75


@dataclass
class TaskScore:
    """Score breakdown for a single task evaluation."""

    task_id: str
    passed: bool
    score: float
    content_score: float
    tool_score: float
    matched_includes: list[str] = field(default_factory=list)
    missing_includes: list[str] = field(default_factory=list)
    disallowed_hits: list[str] = field(default_factory=list)
    matched_tools: list[str] = field(default_factory=list)
    missing_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "passed": self.passed,
            "score": round(self.score, 4),
            "content_score": round(self.content_score, 4),
            "tool_score": round(self.tool_score, 4),
            "matched_includes": self.matched_includes,
            "missing_includes": self.missing_includes,
            "disallowed_hits": self.disallowed_hits,
            "matched_tools": self.matched_tools,
            "missing_tools": self.missing_tools,
        }


def _score_content(task: BenchmarkTask, answer: str) -> tuple[float, list[str], list[str], list[str]]:
    """Return (score, matched, missing, disallowed_hits)."""
    haystack = answer.lower()

    matched = [phrase for phrase in task.must_include if phrase.lower() in haystack]
    missing = [phrase for phrase in task.must_include if phrase.lower() not in haystack]
    disallowed_hits = [phrase for phrase in task.must_not_include if phrase.lower() in haystack]

    if disallowed_hits:
        return 0.0, matched, missing, disallowed_hits

    if not task.must_include:
        return 1.0, matched, missing, disallowed_hits

    if task.scoring_mode == "all":
        score = len(matched) / len(task.must_include)
    else:  # "any"
        score = 1.0 if matched else 0.0

    return score, matched, missing, disallowed_hits


def _score_tools(task: BenchmarkTask, used_tools: set[str]) -> tuple[float, list[str], list[str]]:
    """Return (score, matched, missing)."""
    if not task.expected_tools:
        return 1.0, [], []

    matched = [tool for tool in task.expected_tools if tool in used_tools]
    missing = [tool for tool in task.expected_tools if tool not in used_tools]
    score = len(matched) / len(task.expected_tools)
    return score, matched, missing


def score_task(task: BenchmarkTask, final_answer: str, used_tools: set[str] | None = None) -> TaskScore:
    """Evaluate a task's output and return a structured score."""
    tools = used_tools or set()

    content_score, matched_includes, missing_includes, disallowed_hits = _score_content(task, final_answer)
    tool_score, matched_tools, missing_tools = _score_tools(task, tools)

    aggregate = CONTENT_WEIGHT * content_score + TOOL_WEIGHT * tool_score
    passed = aggregate >= PASS_THRESHOLD and not disallowed_hits

    return TaskScore(
        task_id=task.id,
        passed=passed,
        score=aggregate,
        content_score=content_score,
        tool_score=tool_score,
        matched_includes=matched_includes,
        missing_includes=missing_includes,
        disallowed_hits=disallowed_hits,
        matched_tools=matched_tools,
        missing_tools=missing_tools,
    )
