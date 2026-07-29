"""Real LLM API smoke tests.

These tests call a live model provider. They are **opt-in** so default unit
runs stay free of network / secret requirements:

    # Windows PowerShell
    $env:STORYAGENTS_RUN_SMOKE = "1"
    $env:DEEPSEEK_API_KEY = "sk-..."
    uv run pytest tests/test_real_api_smoke.py -m smoke -q

    # bash
    STORYAGENTS_RUN_SMOKE=1 DEEPSEEK_API_KEY=sk-... \\
      uv run pytest tests/test_real_api_smoke.py -m smoke -q
"""

from __future__ import annotations

import os

import pytest

from storyagents.api_key_env import PROVIDER_API_KEY_ENV
from storyagents.default_config import DEFAULT_STORY_CONFIG
from storyagents.orchestration.editor import StoryEditor
from storyagents.orchestration.models import create_chat_model
from storyagents.orchestration.story_graph import StoryAgentsGraph


def _smoke_enabled() -> bool:
    return os.environ.get("STORYAGENTS_RUN_SMOKE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _configured_provider() -> str | None:
    """Pick the first provider that has an API key available."""
    preferred = (
        os.environ.get("STORYAGENTS_LLM_PROVIDER"),
        DEFAULT_STORY_CONFIG.get("llm_provider", "deepseek"),
        "deepseek",
        "openai",
        "qwen",
        "qwen-cn",
        "anthropic",
        "google",
        "openrouter",
        "xai",
        "glm",
        "glm-cn",
        "minimax",
        "minimax-cn",
    )
    seen: set[str] = set()
    for provider in preferred:
        if not provider or provider in seen:
            continue
        provider = provider.strip().lower()
        seen.add(provider)
        env_name = PROVIDER_API_KEY_ENV.get(provider)
        if env_name is None:
            continue
        if os.environ.get(env_name, "").strip():
            return provider
    return None


def _smoke_config(provider: str) -> dict:
    config = DEFAULT_STORY_CONFIG.copy()
    config.update(
        {
            "llm_provider": provider,
            "workflow_mode": "quick",
            "fast_mode": True,
            "target_chapters": 1,
            "max_revision_rounds": 1,
            "output_language": "Chinese",
            "results_dir": os.path.join(os.path.dirname(__file__), "..", ".tmp_smoke"),
        }
    )
    # Prefer compact/cheap defaults when provider is deepseek/openai.
    if provider == "deepseek":
        config["deep_think_llm"] = os.environ.get(
            "STORYAGENTS_DEEP_THINK_LLM",
            "deepseek-chat",
        )
        config["quick_think_llm"] = os.environ.get(
            "STORYAGENTS_QUICK_THINK_LLM",
            "deepseek-chat",
        )
    elif provider == "openai":
        config["deep_think_llm"] = os.environ.get(
            "STORYAGENTS_DEEP_THINK_LLM",
            "gpt-4o-mini",
        )
        config["quick_think_llm"] = os.environ.get(
            "STORYAGENTS_QUICK_THINK_LLM",
            "gpt-4o-mini",
        )
    return config


@pytest.fixture(scope="module")
def live_provider():
    if not _smoke_enabled():
        pytest.skip(
            "Real API smoke tests are opt-in. Set STORYAGENTS_RUN_SMOKE=1 "
            "and a provider API key (e.g. DEEPSEEK_API_KEY) to enable."
        )
    provider = _configured_provider()
    if provider is None:
        pytest.skip(
            "No LLM API key found. Set e.g. DEEPSEEK_API_KEY or OPENAI_API_KEY "
            "to run real API smoke tests."
        )
    return provider


@pytest.mark.smoke
@pytest.mark.integration
def test_real_api_quick_draft_smoke(live_provider):
    config = _smoke_config(live_provider)
    os.makedirs(config["results_dir"], exist_ok=True)

    graph = StoryAgentsGraph(config=config)
    state, manuscript = graph.generate_story(
        "写一个只有一章的极短童话：一只会说话的灯笼在雨夜迷路。",
        target_chapters=1,
    )

    assert state.get("story_title"), "expected a non-empty story title"
    assert state.get("chapters"), "expected at least one chapter"
    assert len(state["chapters"]) == 1
    assert manuscript.strip(), "expected non-empty manuscript"
    assert "Chapter" in manuscript or "章" in manuscript or state["chapters"][0].strip()
    assert state.get("showrunner_status") in {"Complete", "Continue", ""}


@pytest.mark.smoke
@pytest.mark.integration
def test_real_api_editor_smoke(live_provider):
    config = _smoke_config(live_provider)
    model = create_chat_model(
        provider=config["llm_provider"],
        model=config["quick_think_llm"],
        base_url=config.get("backend_url"),
        stream=False,
    )
    editor = StoryEditor(model)
    result = editor.edit(
        "雨点敲打窗台，灯笼轻轻摇晃。",
        action="polish",
        instruction="保持简短",
    )

    assert result.get("edited_text", "").strip(), "expected edited text"
    assert result.get("changes_summary", "").strip(), "expected change summary"
