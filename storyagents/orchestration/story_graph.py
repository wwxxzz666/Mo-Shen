from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Generator, Optional, Tuple

from storyagents.default_config import DEFAULT_STORY_CONFIG

from .models import create_chat_model
from .state import create_initial_state
from .workflow import StoryWorkflow


class StoryAgentsGraph:
    """Public story generation facade backed by AgentScope multi-agent roles.

    Keeps the historical class name and method surface so CLI / server /
    tests can switch from LangGraph to AgentScope without API churn.
    """

    def __init__(
        self,
        debug: bool = False,
        config: Optional[Dict[str, Any]] = None,
        callbacks: Optional[list] = None,
        *,
        deep_model: Any = None,
        quick_model: Any = None,
        workflow: Optional[StoryWorkflow] = None,
    ):
        self.debug = debug
        self.config = config or DEFAULT_STORY_CONFIG.copy()
        self.callbacks = callbacks or []

        os.makedirs(self.config["results_dir"], exist_ok=True)

        if workflow is not None:
            self.workflow = workflow
            self.deep_model = deep_model
            self.quick_model = quick_model
        else:
            model_kwargs = self._get_model_kwargs()
            self.deep_model = deep_model or create_chat_model(
                provider=self.config["llm_provider"],
                model=self.config["deep_think_llm"],
                base_url=self.config.get("backend_url"),
                **model_kwargs,
            )
            self.quick_model = quick_model or create_chat_model(
                provider=self.config["llm_provider"],
                model=self.config["quick_think_llm"],
                base_url=self.config.get("backend_url"),
                **model_kwargs,
            )
            self.workflow = StoryWorkflow(
                deep_model=self.deep_model,
                quick_model=self.quick_model,
                config=self.config,
            )

    def _get_model_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"stream": False}
        provider = self.config.get("llm_provider", "").lower()
        if provider == "deepseek":
            kwargs["thinking_enabled"] = bool(
                self.config.get("deepseek_thinking_enabled", False)
            )
            reasoning_effort = self.config.get("deepseek_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
        return kwargs

    def _run_async(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        # Already inside an event loop (e.g. notebook): use a private loop
        # in the current thread via a new loop to avoid nested-run errors.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def generate_story(
        self,
        user_request: str,
        target_chapters: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], str]:
        chapter_count = target_chapters or self.config["target_chapters"]
        final_state: Dict[str, Any] = {}

        async def _collect() -> Dict[str, Any]:
            state: Dict[str, Any] = create_initial_state(
                user_request,
                chapter_count,
                int(self.config.get("target_chapter_length", 1500)),
            )
            async for event in self.workflow.stream(user_request, chapter_count):
                if event["event"] == "node_complete":
                    data = dict(event["data"])
                    data.pop("node", None)
                    state.update(data)
                elif event["event"] == "story_complete":
                    state.update(
                        {
                            k: v
                            for k, v in (event.get("data") or {}).items()
                            if k != "target_chapters" or not state.get("target_chapters")
                        }
                    )
            # Prefer the workflow's retained full state when available.
            retained = getattr(self.workflow, "_last_state", None)
            if isinstance(retained, dict) and retained:
                return retained
            return state

        final_state = self._run_async(_collect())
        return final_state, final_state.get("final_manuscript", "")

    def generate_story_stream(
        self,
        user_request: str,
        target_chapters: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream story generation events (sync generator for HTTP SSE)."""
        chapter_count = target_chapters or self.config["target_chapters"]

        async def _aiter():
            async for event in self.workflow.stream(user_request, chapter_count):
                yield event

        agen = _aiter()
        loop = asyncio.new_event_loop()
        try:
            while True:
                try:
                    event = loop.run_until_complete(agen.__anext__())
                except StopAsyncIteration:
                    break
                yield event
        finally:
            loop.close()
