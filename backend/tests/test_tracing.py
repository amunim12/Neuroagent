"""Tests for LangSmith tracing configuration."""

import os

import pytest

from app.config import settings
from app.utils.tracing import configure_tracing, run_config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove tracing env vars so each test starts clean."""
    for key in ("LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"):
        monkeypatch.delenv(key, raising=False)
    yield


async def test_configure_tracing_disabled_without_key(monkeypatch):
    monkeypatch.setattr(settings, "LANGCHAIN_API_KEY", "")
    monkeypatch.setattr(settings, "LANGCHAIN_TRACING_V2", True)

    activated = configure_tracing()

    assert activated is False
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    assert "LANGCHAIN_API_KEY" not in os.environ


async def test_configure_tracing_enabled_with_key(monkeypatch):
    monkeypatch.setattr(settings, "LANGCHAIN_API_KEY", "ls-test-key")
    monkeypatch.setattr(settings, "LANGCHAIN_TRACING_V2", True)
    monkeypatch.setattr(settings, "LANGCHAIN_PROJECT", "neuroagent-test")

    activated = configure_tracing()

    assert activated is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "ls-test-key"
    assert os.environ["LANGCHAIN_PROJECT"] == "neuroagent-test"


async def test_configure_tracing_key_present_but_flag_off(monkeypatch):
    monkeypatch.setattr(settings, "LANGCHAIN_API_KEY", "ls-test-key")
    monkeypatch.setattr(settings, "LANGCHAIN_TRACING_V2", False)

    activated = configure_tracing()

    assert activated is False
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    # API key still exported so manual client.trace() works if ever used.
    assert os.environ["LANGCHAIN_API_KEY"] == "ls-test-key"


async def test_configure_tracing_ignores_whitespace_key(monkeypatch):
    monkeypatch.setattr(settings, "LANGCHAIN_API_KEY", "   ")
    monkeypatch.setattr(settings, "LANGCHAIN_TRACING_V2", True)

    assert configure_tracing() is False


async def test_run_config_includes_metadata_and_tags(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    config = run_config(session_id="sess-1", user_id="user-1", goal="test goal")

    assert config["run_name"] == "agent-run:sess-1"
    assert "neuroagent" in config["tags"]
    assert "production" in config["tags"]
    assert config["metadata"]["session_id"] == "sess-1"
    assert config["metadata"]["user_id"] == "user-1"
    assert config["metadata"]["goal"] == "test goal"
    assert config["metadata"]["environment"] == "production"
