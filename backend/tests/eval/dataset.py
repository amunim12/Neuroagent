"""Benchmark task dataset for NeuroAgent evaluation.

Each entry pairs a natural-language goal with lightweight, deterministic success
criteria so scoring can run offline without an LLM-as-judge. The criteria use
case-insensitive substring checks on the agent's ``final_answer`` plus an
optional expectation about which tools the agent invoked.

Keep tasks focused — a single goal should exercise one capability so failures
are diagnosable. Diversity across categories matters more than count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Tool names used in ``executor_node`` callbacks — kept as constants to avoid
# typos slipping into the dataset.
TOOL_WEB_SEARCH = "web_search"
TOOL_CODE_EXECUTOR = "code_executor"
TOOL_API_CALLER = "api_caller"
TOOL_BROWSER = "browser"

Category = Literal["reasoning", "web_research", "coding", "synthesis", "multi_step"]
ScoringMode = Literal["any", "all"]


@dataclass(frozen=True)
class BenchmarkTask:
    """A single benchmark entry.

    Attributes:
        id: Stable identifier (``<category-prefix>-<NNN>``) used in reports.
        category: Capability area this task exercises.
        goal: Prompt sent to the agent.
        must_include: Substrings expected in the final answer.
        scoring_mode: ``"any"`` — at least one substring present;
            ``"all"`` — every substring must be present.
        must_not_include: Substrings whose presence invalidates the answer.
        expected_tools: Tool names the agent is expected to invoke. Missing
            tools reduce the score but do not automatically fail the task.
    """

    id: str
    category: Category
    goal: str
    must_include: tuple[str, ...]
    scoring_mode: ScoringMode = "any"
    must_not_include: tuple[str, ...] = ()
    expected_tools: tuple[str, ...] = ()


BENCHMARK_TASKS: tuple[BenchmarkTask, ...] = (
    # --- Reasoning ---------------------------------------------------------
    BenchmarkTask(
        id="reason-001",
        category="reasoning",
        goal=(
            "A train leaves station A at 3pm traveling 60 mph. Another leaves station B "
            "(180 miles away) at 4pm traveling 40 mph toward A. At what time do they meet?"
        ),
        must_include=("6", "pm"),
        scoring_mode="all",
    ),
    BenchmarkTask(
        id="reason-002",
        category="reasoning",
        goal="Explain the difference between supervised and unsupervised learning in two sentences.",
        must_include=("labeled", "unlabeled", "labels"),
        scoring_mode="any",
    ),
    BenchmarkTask(
        id="reason-003",
        category="reasoning",
        goal="What is the time complexity of binary search, and why?",
        must_include=("O(log n)", "log"),
        scoring_mode="any",
    ),
    BenchmarkTask(
        id="reason-004",
        category="reasoning",
        goal="If a fair coin is flipped 3 times, what is the probability of getting at least one heads?",
        must_include=("7/8", "0.875", "87.5"),
        scoring_mode="any",
    ),
    # --- Web research ------------------------------------------------------
    BenchmarkTask(
        id="web-001",
        category="web_research",
        goal="Search for the current stable version of Python and summarize its key features.",
        must_include=("Python", "3."),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH,),
    ),
    BenchmarkTask(
        id="web-002",
        category="web_research",
        goal="Find the founders of Anthropic and the year the company was founded.",
        must_include=("Amodei", "2021"),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH,),
    ),
    BenchmarkTask(
        id="web-003",
        category="web_research",
        goal="What is LangGraph and how does it relate to LangChain? Provide a short overview.",
        must_include=("LangGraph", "LangChain"),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH,),
    ),
    BenchmarkTask(
        id="web-004",
        category="web_research",
        goal="Look up the HTTP status code for 'Too Many Requests' and describe when servers return it.",
        must_include=("429", "rate"),
        scoring_mode="all",
    ),
    BenchmarkTask(
        id="web-005",
        category="web_research",
        goal="Search for a comparison between PostgreSQL and MySQL and list two differences.",
        must_include=("PostgreSQL", "MySQL"),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH,),
    ),
    # --- Coding ------------------------------------------------------------
    BenchmarkTask(
        id="code-001",
        category="coding",
        goal="Write and execute Python code that computes the 10th Fibonacci number and prints the result.",
        must_include=("55",),
        scoring_mode="all",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
    BenchmarkTask(
        id="code-002",
        category="coding",
        goal="Write Python code that reverses the string 'neuroagent' and prints it.",
        must_include=("tnegaoruen",),
        scoring_mode="all",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
    BenchmarkTask(
        id="code-003",
        category="coding",
        goal="Write a Python function that returns True if a number is prime, then test it with 29.",
        must_include=("True", "prime"),
        scoring_mode="any",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
    BenchmarkTask(
        id="code-004",
        category="coding",
        goal="Execute Python code that counts the vowels in the word 'autonomous' and reports the total.",
        must_include=("5",),
        scoring_mode="all",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
    # --- Synthesis ---------------------------------------------------------
    BenchmarkTask(
        id="synth-001",
        category="synthesis",
        goal=(
            "Summarize the REST architectural style in under 150 words, covering "
            "statelessness and resource-oriented URLs."
        ),
        must_include=("stateless", "resource"),
        scoring_mode="all",
        must_not_include=("SOAP is better",),
    ),
    BenchmarkTask(
        id="synth-002",
        category="synthesis",
        goal="Explain the CAP theorem using a real-world example.",
        must_include=("consistency", "availability", "partition"),
        scoring_mode="all",
    ),
    BenchmarkTask(
        id="synth-003",
        category="synthesis",
        goal="Compare monolithic and microservices architectures and recommend when to use each.",
        must_include=("monolith", "microservice"),
        scoring_mode="all",
    ),
    # --- Multi-step --------------------------------------------------------
    BenchmarkTask(
        id="multi-001",
        category="multi_step",
        goal="Find the latest Node.js LTS version, then write and execute Python code that prints that version string.",
        must_include=("Node", "LTS"),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH, TOOL_CODE_EXECUTOR),
    ),
    BenchmarkTask(
        id="multi-002",
        category="multi_step",
        goal=(
            "Research what a JWT is, then write Python code that encodes a minimal "
            "JWT payload {'sub': '1'} using HS256 with secret 'dev'."
        ),
        must_include=("JWT", "HS256"),
        scoring_mode="all",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
    BenchmarkTask(
        id="multi-003",
        category="multi_step",
        goal="Look up the capital of Australia, then compute the number of letters in its name using Python code.",
        must_include=("Canberra", "8"),
        scoring_mode="all",
        expected_tools=(TOOL_WEB_SEARCH, TOOL_CODE_EXECUTOR),
    ),
    BenchmarkTask(
        id="multi-004",
        category="multi_step",
        goal="Find the current year, then write Python code that prints the number of years since 1969 (moon landing).",
        must_include=("1969",),
        scoring_mode="all",
        expected_tools=(TOOL_CODE_EXECUTOR,),
    ),
)


def tasks_by_category(category: Category) -> list[BenchmarkTask]:
    """Return all benchmark tasks matching the given category."""
    return [task for task in BENCHMARK_TASKS if task.category == category]


def get_task(task_id: str) -> BenchmarkTask:
    """Return the task with the given id, or raise KeyError."""
    for task in BENCHMARK_TASKS:
        if task.id == task_id:
            return task
    raise KeyError(f"No benchmark task with id {task_id!r}")


def categories() -> list[Category]:
    """Return the list of distinct categories present in the dataset."""
    seen: list[Category] = []
    for task in BENCHMARK_TASKS:
        if task.category not in seen:
            seen.append(task.category)
    return seen
