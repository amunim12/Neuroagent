"""Tests for the agent graph structure and individual node logic."""

from unittest.mock import MagicMock

from app.agent.models.clients import MODEL_CLAUDE_SONNET, MODEL_GPT4O, MODEL_GROQ_LLAMA3
from app.agent.models.router import route_model_for_task
from app.agent.nodes.router import model_router_node
from app.agent.state import AgentState

# --- Model routing tests ---


class TestModelRouting:
    def test_simple_query_routes_to_groq(self):
        assert route_model_for_task("summarize the latest Python release notes") == MODEL_GROQ_LLAMA3

    def test_search_query_routes_to_groq(self):
        assert route_model_for_task("search for best REST API practices") == MODEL_GROQ_LLAMA3

    def test_what_is_routes_to_groq(self):
        assert route_model_for_task("what is dependency injection") == MODEL_GROQ_LLAMA3

    def test_coding_task_routes_to_claude(self):
        assert route_model_for_task("write a Python function to parse CSV") == MODEL_CLAUDE_SONNET

    def test_debug_task_routes_to_claude(self):
        assert route_model_for_task("debug the authentication middleware") == MODEL_CLAUDE_SONNET

    def test_analyze_task_routes_to_claude(self):
        assert route_model_for_task("analyze the performance of this query") == MODEL_CLAUDE_SONNET

    def test_complex_task_routes_to_gpt4o(self):
        assert route_model_for_task("create a comprehensive business strategy") == MODEL_GPT4O

    def test_ambiguous_task_routes_to_gpt4o(self):
        assert route_model_for_task("help me plan my project roadmap") == MODEL_GPT4O


# --- Router node tests ---


class TestRouterNode:
    def _make_state(self, **overrides) -> AgentState:
        defaults: AgentState = {
            "goal": "test goal",
            "session_id": "test-session",
            "user_id": "test-user",
            "messages": [],
            "subtasks": ["search for Python docs", "write a parser"],
            "current_task_index": 0,
            "tool_outputs": [],
            "retrieved_memory": [],
            "selected_model": MODEL_GPT4O,
            "final_answer": "",
            "is_complete": False,
            "error": None,
            "stream_callback": None,
        }
        defaults.update(overrides)
        return defaults

    def test_routes_first_subtask(self):
        state = self._make_state(subtasks=["search for Python tutorials", "write code"])
        result = model_router_node(state)
        assert result["selected_model"] == MODEL_GROQ_LLAMA3

    def test_routes_second_subtask(self):
        state = self._make_state(subtasks=["search for docs", "write a unit test"], current_task_index=1)
        result = model_router_node(state)
        assert result["selected_model"] == MODEL_CLAUDE_SONNET

    def test_falls_back_to_goal_when_no_subtasks(self):
        state = self._make_state(subtasks=[], goal="summarize this article")
        result = model_router_node(state)
        assert result["selected_model"] == MODEL_GROQ_LLAMA3

    def test_emits_stream_event(self):
        callback = MagicMock()
        state = self._make_state(stream_callback=callback, subtasks=["find latest news"])
        model_router_node(state)
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event["type"] == "routing"
        assert "model" in event


# --- Graph structure tests ---


class TestGraphStructure:
    def test_graph_compiles(self):
        """Verify the graph compiles without errors."""
        from app.agent.graph import build_agent_graph

        graph = build_agent_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        from app.agent.graph import build_agent_graph

        graph = build_agent_graph()
        node_names = set(graph.nodes.keys())
        expected = {"read_memory", "plan", "route_model", "execute", "synthesize", "write_memory", "__start__"}
        assert expected.issubset(node_names), f"Missing nodes: {expected - node_names}"


# --- Conditional edge tests ---


class TestShouldContinue:
    def _make_state(self, **overrides) -> AgentState:
        defaults: AgentState = {
            "goal": "test",
            "session_id": "s",
            "user_id": "u",
            "messages": [],
            "subtasks": ["a", "b", "c"],
            "current_task_index": 0,
            "tool_outputs": [],
            "retrieved_memory": [],
            "selected_model": MODEL_GPT4O,
            "final_answer": "",
            "is_complete": False,
            "error": None,
            "stream_callback": None,
        }
        defaults.update(overrides)
        return defaults

    def test_continues_when_subtasks_remain(self):
        from app.agent.graph import should_continue

        state = self._make_state(current_task_index=1, subtasks=["a", "b", "c"])
        assert should_continue(state) == "route_model"

    def test_synthesizes_when_all_subtasks_done(self):
        from app.agent.graph import should_continue

        state = self._make_state(current_task_index=3, subtasks=["a", "b", "c"])
        assert should_continue(state) == "synthesize"

    def test_synthesizes_on_error(self):
        from app.agent.graph import should_continue

        state = self._make_state(error="something broke")
        assert should_continue(state) == "synthesize"

    def test_ends_when_complete(self):
        from app.agent.graph import should_continue

        state = self._make_state(is_complete=True)
        assert should_continue(state) == "__end__"
