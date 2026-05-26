from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from storyagents.llm_clients import create_llm_client

from storyagents.default_config import DEFAULT_STORY_CONFIG

from .propagation import StoryPropagator
from .setup import StoryGraphSetup


class StoryAgentsGraph:
    def __init__(
        self,
        debug: bool = False,
        config: Optional[Dict[str, Any]] = None,
        callbacks: Optional[list] = None,
    ):
        self.debug = debug
        self.config = config or DEFAULT_STORY_CONFIG.copy()
        self.callbacks = callbacks or []

        os.makedirs(self.config["results_dir"], exist_ok=True)

        llm_kwargs = self._get_provider_kwargs()
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        self.deep_llm = deep_client.get_llm()
        self.quick_llm = quick_client.get_llm()

        self.propagator = StoryPropagator(
            max_recur_limit=self.config.get("max_recur_limit", 80)
        )
        self.workflow = StoryGraphSetup(
            self.quick_llm,
            self.deep_llm,
            self.config,
        ).setup_graph()
        self.graph = self.workflow.compile()

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        provider = self.config.get("llm_provider", "").lower()

        if provider == "deepseek":
            reasoning_effort = self.config.get("deepseek_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            # Keep DeepSeek thinking mode explicitly disabled for StoryAgents
            # API calls so generation stays faster and operationally
            # predictable, regardless of request-side toggles.
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        return kwargs

    def generate_story(
        self,
        user_request: str,
        target_chapters: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], str]:
        chapter_count = target_chapters or self.config["target_chapters"]
        initial_state = self.propagator.create_initial_state(
            user_request,
            chapter_count,
        )
        final_state = self.graph.invoke(initial_state, **self.propagator.graph_args())
        return final_state, final_state.get("final_manuscript", "")
