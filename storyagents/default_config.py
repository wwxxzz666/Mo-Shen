import os

_STORYAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".storyagents")
_PROJECT_STORIES_DIR = os.path.join(os.path.dirname(__file__), "..", "stories")

_ENV_OVERRIDES = {
    "STORYAGENTS_LLM_PROVIDER": "llm_provider",
    "STORYAGENTS_DEEP_THINK_LLM": "deep_think_llm",
    "STORYAGENTS_QUICK_THINK_LLM": "quick_think_llm",
    "STORYAGENTS_LLM_BACKEND_URL": "backend_url",
    "STORYAGENTS_OUTPUT_LANGUAGE": "output_language",
    "STORYAGENTS_TARGET_CHAPTERS": "target_chapters",
    "STORYAGENTS_MAX_REVISION_ROUNDS": "max_revision_rounds",
    "STORYAGENTS_WORKFLOW_MODE": "workflow_mode",
    "STORYAGENTS_FAST_MODE": "fast_mode",
}

VALID_WORKFLOW_MODES = ("quick", "standard", "deep")


def normalize_workflow_mode(mode) -> str:
    if isinstance(mode, str):
        candidate = mode.strip().lower()
        if candidate in VALID_WORKFLOW_MODES:
            return candidate
    return "quick"


def _coerce(value: str, reference):
    if isinstance(reference, bool):
        return value.strip().lower() in ("true", "1", "yes", "on")
    if isinstance(reference, int) and not isinstance(reference, bool):
        return int(value)
    if isinstance(reference, float):
        return float(value)
    return value


def _apply_env_overrides(config: dict) -> dict:
    for env_var, key in _ENV_OVERRIDES.items():
        raw = os.environ.get(env_var)
        if raw is None or raw == "":
            continue
        config[key] = _coerce(raw, config.get(key))
    workflow_mode = config.get("workflow_mode")
    if workflow_mode in (None, "") and "STORYAGENTS_FAST_MODE" in os.environ:
        config["workflow_mode"] = "quick" if config.get("fast_mode", True) else "deep"
    config["workflow_mode"] = normalize_workflow_mode(config.get("workflow_mode"))
    config["fast_mode"] = config["workflow_mode"] == "quick"
    if config["workflow_mode"] == "deep":
        config["max_revision_rounds"] = max(
            int(config.get("max_revision_rounds", 2)),
            3,
        )
    return config


DEFAULT_STORY_CONFIG = _apply_env_overrides(
    {
        "results_dir": os.getenv(
            "STORYAGENTS_RESULTS_DIR",
            os.path.normpath(_PROJECT_STORIES_DIR),
        ),
        "llm_provider": "deepseek",
        "deep_think_llm": "deepseek-chat",
        "quick_think_llm": "deepseek-chat",
        "backend_url": None,
        "deepseek_reasoning_effort": None,
        "deepseek_thinking_enabled": False,
        "output_language": "Chinese",
        "target_chapters": 3,
        "max_revision_rounds": 2,
        "max_recur_limit": 80,
        "workflow_mode": "quick",
        "fast_mode": True,
    }
)
