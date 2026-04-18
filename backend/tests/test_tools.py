"""Tests for agent tools -- input validation, error handling, and output formatting.

All tests mock external services (Tavily, E2B, Playwright, httpx) so no API keys are needed.
"""

import json
from unittest.mock import MagicMock, patch

from app.agent.tools.api_caller import api_caller_tool
from app.agent.tools.browser import browser_tool
from app.agent.tools.code_executor import code_executor_tool
from app.agent.tools.web_search import web_search_tool

# === Web Search Tool ===


class TestWebSearchTool:
    def test_empty_query_returns_error(self):
        result = web_search_tool.invoke({"query": ""})
        assert "empty" in result.lower()

    def test_whitespace_query_returns_error(self):
        result = web_search_tool.invoke({"query": "   "})
        assert "empty" in result.lower()

    @patch("tavily.TavilyClient")
    def test_successful_search(self, mock_tavily_cls):
        mock_client = MagicMock()
        mock_tavily_cls.return_value = mock_client
        mock_client.search.return_value = {
            "answer": "Python 3.12 is the latest.",
            "results": [
                {"title": "Python Docs", "url": "https://python.org", "content": "Official documentation."},
                {"title": "Release Notes", "url": "https://python.org/release", "content": "What's new in 3.12."},
            ],
        }

        result = web_search_tool.invoke({"query": "latest Python version"})

        assert "Python 3.12" in result
        assert "Sources:" in result
        assert "Python Docs" in result

    @patch("tavily.TavilyClient")
    def test_no_results(self, mock_tavily_cls):
        mock_client = MagicMock()
        mock_tavily_cls.return_value = mock_client
        mock_client.search.return_value = {"answer": "Unknown", "results": []}

        result = web_search_tool.invoke({"query": "obscure topic xyz"})

        assert "No detailed sources found" in result

    @patch("tavily.TavilyClient")
    def test_api_error_returns_message(self, mock_tavily_cls):
        mock_tavily_cls.side_effect = RuntimeError("API key invalid")

        result = web_search_tool.invoke({"query": "test query"})

        assert "failed" in result.lower()


# === Code Executor Tool ===


class TestCodeExecutorTool:
    def test_empty_code_returns_error(self):
        result = code_executor_tool.invoke({"code": ""})
        assert "empty" in result.lower()

    def test_whitespace_code_returns_error(self):
        result = code_executor_tool.invoke({"code": "  \n  "})
        assert "empty" in result.lower()

    @patch("e2b_code_interpreter.Sandbox")
    def test_successful_execution(self, mock_sandbox_cls):
        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value.__enter__ = MagicMock(return_value=mock_sandbox)
        mock_sandbox_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_execution = MagicMock()
        mock_execution.logs.stdout = ["Hello, World!"]
        mock_execution.logs.stderr = []
        mock_execution.results = []
        mock_sandbox.run_code.return_value = mock_execution

        result = code_executor_tool.invoke({"code": "print('Hello, World!')"})

        assert "Hello, World!" in result

    @patch("e2b_code_interpreter.Sandbox")
    def test_execution_with_stderr(self, mock_sandbox_cls):
        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value.__enter__ = MagicMock(return_value=mock_sandbox)
        mock_sandbox_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_execution = MagicMock()
        mock_execution.logs.stdout = []
        mock_execution.logs.stderr = ["NameError: name 'x' is not defined"]
        mock_execution.results = []
        mock_sandbox.run_code.return_value = mock_execution

        result = code_executor_tool.invoke({"code": "print(x)"})

        assert "NameError" in result
        assert "Errors:" in result

    @patch("e2b_code_interpreter.Sandbox")
    def test_sandbox_crash_returns_error(self, mock_sandbox_cls):
        mock_sandbox_cls.side_effect = RuntimeError("Sandbox unavailable")

        result = code_executor_tool.invoke({"code": "print(1)"})

        assert "failed" in result.lower() or "Sandbox unavailable" in result

    @patch("e2b_code_interpreter.Sandbox")
    def test_output_truncation(self, mock_sandbox_cls):
        mock_sandbox = MagicMock()
        mock_sandbox_cls.return_value.__enter__ = MagicMock(return_value=mock_sandbox)
        mock_sandbox_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_execution = MagicMock()
        mock_execution.logs.stdout = ["x" * 10000]
        mock_execution.logs.stderr = []
        mock_execution.results = []
        mock_sandbox.run_code.return_value = mock_execution

        result = code_executor_tool.invoke({"code": "print('x' * 10000)"})

        assert "truncated" in result


# === Browser Tool ===


class TestBrowserTool:
    def test_invalid_json_returns_error(self):
        result = browser_tool.invoke({"action": "not json"})
        assert "Invalid JSON" in result

    def test_unknown_action_returns_error(self):
        result = browser_tool.invoke({"action": json.dumps({"action": "destroy", "url": "http://example.com"})})
        assert "Unknown action" in result

    def test_missing_url_returns_error(self):
        result = browser_tool.invoke({"action": json.dumps({"action": "navigate"})})
        assert "url" in result.lower()

    def test_click_without_selector_returns_error(self):
        payload = json.dumps({"action": "click", "url": "http://example.com"})
        result = browser_tool.invoke({"action": payload})
        assert "selector" in result.lower()

    def test_fill_without_value_returns_error(self):
        payload = json.dumps({"action": "fill", "url": "http://example.com", "selector": "#name"})
        result = browser_tool.invoke({"action": payload})
        assert "required" in result.lower()

    def test_fill_without_selector_returns_error(self):
        payload = json.dumps({"action": "fill", "url": "http://example.com", "value": "test"})
        result = browser_tool.invoke({"action": payload})
        assert "required" in result.lower()


# === API Caller Tool ===


class TestApiCallerTool:
    def test_invalid_json_returns_error(self):
        result = api_caller_tool.invoke({"request": "not json"})
        assert "Invalid JSON" in result

    def test_invalid_method_returns_error(self):
        result = api_caller_tool.invoke({"request": json.dumps({"method": "YEET", "url": "http://example.com"})})
        assert "Invalid HTTP method" in result

    def test_missing_url_returns_error(self):
        result = api_caller_tool.invoke({"request": json.dumps({"method": "GET"})})
        assert "url" in result.lower()

    @patch("app.agent.tools.api_caller.httpx.Client")
    def test_successful_get_request(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "hello"}'
        mock_client.request.return_value = mock_response

        payload = json.dumps({"method": "GET", "url": "https://api.example.com/data"})
        result = api_caller_tool.invoke({"request": payload})

        assert "200" in result
        assert "hello" in result

    @patch("app.agent.tools.api_caller.httpx.Client")
    def test_post_with_body(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        mock_client.request.return_value = mock_response

        payload = json.dumps({"method": "POST", "url": "https://api.example.com/items", "body": {"name": "test"}})
        result = api_caller_tool.invoke({"request": payload})

        assert "201" in result
        mock_client.request.assert_called_once()
        call_kwargs = mock_client.request.call_args
        assert call_kwargs.kwargs["json"] == {"name": "test"}

    @patch("app.agent.tools.api_caller.httpx.Client")
    def test_timeout_returns_message(self, mock_client_cls):
        import httpx

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.request.side_effect = httpx.TimeoutException("timed out")

        payload = json.dumps({"method": "GET", "url": "https://slow.example.com"})
        result = api_caller_tool.invoke({"request": payload})

        assert "timed out" in result.lower()

    @patch("app.agent.tools.api_caller.httpx.Client")
    def test_response_truncation(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "x" * 5000
        mock_client.request.return_value = mock_response

        payload = json.dumps({"method": "GET", "url": "https://api.example.com/big"})
        result = api_caller_tool.invoke({"request": payload})

        assert "truncated" in result
