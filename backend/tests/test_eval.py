"""Tests for the evaluation benchmark scaffolding.

These tests exercise the dataset + scoring framework itself — not live agent
runs — so they remain deterministic and fast in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.eval import benchmark
from tests.eval.dataset import (
    BENCHMARK_TASKS,
    BenchmarkTask,
    categories,
    get_task,
    tasks_by_category,
)
from tests.eval.scoring import PASS_THRESHOLD, score_task


class TestDatasetIntegrity:
    def test_at_least_twenty_tasks(self):
        assert len(BENCHMARK_TASKS) >= 20

    def test_task_ids_are_unique(self):
        ids = [t.id for t in BENCHMARK_TASKS]
        assert len(ids) == len(set(ids))

    def test_every_task_has_goal_and_criteria(self):
        for task in BENCHMARK_TASKS:
            assert task.goal, f"{task.id} is missing a goal"
            assert task.must_include, f"{task.id} needs at least one must_include phrase"

    def test_categories_are_covered(self):
        expected = {"reasoning", "web_research", "coding", "synthesis", "multi_step"}
        assert expected.issubset(set(categories()))

    def test_get_task_returns_matching_task(self):
        task = get_task("reason-001")
        assert task.category == "reasoning"

    def test_get_task_raises_for_unknown_id(self):
        with pytest.raises(KeyError):
            get_task("does-not-exist")

    def test_tasks_by_category_filters_correctly(self):
        coding = tasks_by_category("coding")
        assert coding and all(t.category == "coding" for t in coding)


class TestScoring:
    def _task(self, **overrides) -> BenchmarkTask:
        defaults = {
            "id": "unit-001",
            "category": "reasoning",
            "goal": "test goal",
            "must_include": ("python",),
            "scoring_mode": "any",
            "must_not_include": (),
            "expected_tools": (),
        }
        defaults.update(overrides)
        return BenchmarkTask(**defaults)

    def test_any_mode_passes_with_one_match(self):
        task = self._task(must_include=("python", "rust"), scoring_mode="any")
        score = score_task(task, "I wrote some python code.")
        assert score.passed is True
        assert score.content_score == 1.0

    def test_all_mode_requires_every_substring(self):
        task = self._task(must_include=("alpha", "beta"), scoring_mode="all")
        score = score_task(task, "only alpha is mentioned")
        assert score.passed is False
        assert score.content_score == 0.5

    def test_missing_substrings_reported(self):
        task = self._task(must_include=("foo", "bar"), scoring_mode="all")
        score = score_task(task, "answer contains foo only")
        assert "bar" in score.missing_includes

    def test_disallowed_phrase_fails_the_task(self):
        task = self._task(must_include=("python",), must_not_include=("I don't know",))
        score = score_task(task, "python is great but I don't know more")
        assert score.passed is False
        assert score.content_score == 0.0
        assert "I don't know" in score.disallowed_hits

    def test_case_insensitive_matching(self):
        task = self._task(must_include=("Python",))
        score = score_task(task, "python is nice")
        assert score.passed is True

    def test_expected_tools_credit(self):
        task = self._task(must_include=("x",), expected_tools=("web_search",))
        full = score_task(task, "x appears", used_tools={"web_search"})
        partial = score_task(task, "x appears", used_tools=set())
        assert full.tool_score == 1.0
        assert partial.tool_score == 0.0
        assert full.score > partial.score

    def test_tool_score_is_full_credit_when_none_required(self):
        task = self._task(must_include=("ok",), expected_tools=())
        score = score_task(task, "ok")
        assert score.tool_score == 1.0

    def test_pass_threshold_constant_matches_design(self):
        # If the threshold moves, tests in this module need re-inspection.
        assert PASS_THRESHOLD == 0.75


class TestBenchmarkRunnerDryRun:
    def test_dry_run_lists_tasks_without_invoking_agent(self, capsys, tmp_path):
        # --dry-run must not import the agent graph or touch the LLM stack.
        exit_code = benchmark.main(["--dry-run", "--limit", "3", "--output", str(tmp_path / "r.json")])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Loaded 3 task(s)" in captured.out
        assert "[reason-001]" in captured.out

    def test_category_filter_selects_subset(self, capsys, tmp_path):
        exit_code = benchmark.main([
            "--dry-run", "--category", "coding", "--output", str(tmp_path / "r.json"),
        ])
        assert exit_code == 0

        captured = capsys.readouterr()
        # All printed ids should belong to the coding slice.
        for line in captured.out.splitlines():
            if line.strip().startswith("[") and "]" in line:
                assert "(coding)" in line

    def test_task_id_filter_runs_exactly_one(self, capsys, tmp_path):
        exit_code = benchmark.main([
            "--dry-run", "--task-id", "reason-001", "--output", str(tmp_path / "r.json"),
        ])
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Loaded 1 task(s)" in captured.out

    def test_no_matching_tasks_returns_error(self, tmp_path):
        exit_code = benchmark.main([
            "--category", "nonexistent", "--output", str(tmp_path / "r.json"),
        ])
        assert exit_code == 2


class TestBenchmarkAggregation:
    def test_aggregate_counts_passes_and_failures(self):
        from tests.eval.benchmark import TaskRunResult, _aggregate
        from tests.eval.scoring import TaskScore

        def make(passed: bool, latency: float, tokens: int, category: str = "reasoning") -> TaskRunResult:
            return TaskRunResult(
                task_id=f"t-{latency}",
                category=category,
                goal="",
                final_answer="",
                used_tools=[],
                latency_seconds=latency,
                input_tokens=0,
                output_tokens=0,
                total_tokens=tokens,
                error=None,
                score=TaskScore(task_id="x", passed=passed, score=1.0 if passed else 0.0,
                                content_score=1.0 if passed else 0.0, tool_score=1.0),
            )

        report = _aggregate([
            make(True, 1.0, 100, "reasoning"),
            make(False, 2.0, 200, "reasoning"),
            make(True, 3.0, 300, "coding"),
        ])

        assert report.total == 3
        assert report.passed == 2
        assert report.failed == 1
        assert report.pass_rate == pytest.approx(2 / 3)
        assert report.total_tokens == 600
        assert set(report.by_category.keys()) == {"reasoning", "coding"}
        assert report.by_category["reasoning"]["total"] == 2
        assert report.by_category["coding"]["passed"] == 1

    def test_percentile_handles_empty_and_single_values(self):
        from tests.eval.benchmark import _percentile

        assert _percentile([], 0.95) == 0.0
        assert _percentile([5.0], 0.95) == 5.0
        assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.95) == 5.0

    def test_report_is_json_serialisable(self, tmp_path):
        import json

        from tests.eval.benchmark import TaskRunResult, _aggregate, _write_report
        from tests.eval.scoring import TaskScore

        result = TaskRunResult(
            task_id="t1",
            category="reasoning",
            goal="g",
            final_answer="a",
            used_tools=["web_search"],
            latency_seconds=1.23,
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            error=None,
            score=TaskScore(task_id="t1", passed=True, score=1.0, content_score=1.0, tool_score=1.0),
        )
        report = _aggregate([result])

        out = tmp_path / "report.json"
        _write_report(out, report)

        loaded = json.loads(out.read_text())
        assert loaded["total"] == 1
        assert loaded["results"][0]["task_id"] == "t1"


class TestBenchmarkScopedPath:
    def test_default_output_lives_under_tests_eval_reports(self):
        assert Path("tests/eval/reports") in benchmark.DEFAULT_OUTPUT.parents
