from __future__ import annotations

import os
from typing import Any, Optional

from pydantic import SecretStr

from storyagents.api_key_env import get_api_key_env


# OpenAI-compatible provider base URLs.
_PROVIDER_BASE_URL = {
    "xai": "https://api.x.ai/v1",
    "deepseek": "https://api.deepseek.com",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "qwen-cn": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "glm": "https://api.z.ai/api/paas/v4/",
    "glm-cn": "https://open.bigmodel.cn/api/paas/v4/",
    "minimax": "https://api.minimax.io/v1",
    "minimax-cn": "https://api.minimaxi.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}

_OPENAI_COMPATIBLE = {
    "openai",
    "xai",
    "deepseek",
    "qwen",
    "qwen-cn",
    "glm",
    "glm-cn",
    "minimax",
    "minimax-cn",
    "ollama",
    "openrouter",
}


def _require_api_key(provider: str) -> str:
    env_name = get_api_key_env(provider)
    if env_name is None:
        return "ollama"
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise ValueError(
            f"API key for provider '{provider}' is not set. "
            f"Please set the {env_name} environment variable."
        )
    return api_key


def _resolve_base_url(provider: str, base_url: Optional[str]) -> Optional[str]:
    if base_url:
        return base_url
    if provider == "ollama":
        return os.environ.get("OLLAMA_BASE_URL") or _PROVIDER_BASE_URL["ollama"]
    return _PROVIDER_BASE_URL.get(provider)


def create_chat_model(
    provider: str,
    model: str,
    base_url: Optional[str] = None,
    *,
    stream: bool = False,
    thinking_enabled: bool = False,
    reasoning_effort: Optional[str] = None,
    **_: Any,
):
    """Build an AgentScope ChatModel for the configured provider."""
    from agentscope.model import (
        AnthropicChatModel,
        DeepSeekChatModel,
        GeminiChatModel,
        OpenAIChatModel,
    )
    from agentscope.credential import (
        AnthropicCredential,
        DeepSeekCredential,
        GeminiCredential,
        OpenAICredential,
    )

    provider_lower = (provider or "deepseek").lower()
    resolved_base = _resolve_base_url(provider_lower, base_url)

    if provider_lower == "deepseek":
        api_key = _require_api_key("deepseek")
        credential = DeepSeekCredential(
            api_key=SecretStr(api_key),
            base_url=resolved_base or "https://api.deepseek.com",
        )
        params_kwargs: dict[str, Any] = {
            "thinking_enable": bool(thinking_enabled),
        }
        if reasoning_effort:
            # DeepSeek accepts high/max; map common aliases.
            effort = reasoning_effort.lower()
            if effort in {"xhigh", "max"}:
                params_kwargs["reasoning_effort"] = "max"
            else:
                params_kwargs["reasoning_effort"] = "high"
        return DeepSeekChatModel(
            credential=credential,
            model=model,
            parameters=DeepSeekChatModel.Parameters(**params_kwargs),
            stream=stream,
        )

    if provider_lower == "anthropic":
        api_key = _require_api_key("anthropic")
        credential = AnthropicCredential(api_key=SecretStr(api_key))
        return AnthropicChatModel(
            credential=credential,
            model=model,
            stream=stream,
        )

    if provider_lower == "google":
        api_key = _require_api_key("google")
        credential = GeminiCredential(api_key=SecretStr(api_key))
        return GeminiChatModel(
            credential=credential,
            model=model,
            stream=stream,
        )

    if provider_lower in _OPENAI_COMPATIBLE:
        if provider_lower == "ollama":
            api_key = os.environ.get("OPENAI_API_KEY") or "ollama"
        else:
            api_key = _require_api_key(provider_lower)
        credential = OpenAICredential(
            api_key=SecretStr(api_key),
            base_url=resolved_base,
        )
        return OpenAIChatModel(
            credential=credential,
            model=model,
            stream=stream,
        )

    raise ValueError(f"Unsupported LLM provider for AgentScope: {provider}")
