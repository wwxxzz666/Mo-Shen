from __future__ import annotations

import os
from typing import Any, Dict, Generator, Optional, Tuple

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

    def generate_story_stream(
        self,
        user_request: str,
        target_chapters: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream story generation events.

        Yields dicts with keys:
        - event: "node_start" | "node_complete" | "story_complete"
        - data: node name, output fields, progress info
        """
        chapter_count = target_chapters or self.config["target_chapters"]
        initial_state = self.propagator.create_initial_state(
            user_request,
            chapter_count,
        )

        for chunk in self.graph.stream(initial_state, **self.propagator.graph_args()):
            # chunk is {node_name: state_update}
            for node_name, state_update in chunk.items():
                yield {
                    "event": "node_complete",
                    "data": {
                        "node": node_name,
                        "story_title": state_update.get("story_title", ""),
                        "story_brief": state_update.get("story_brief", ""),
                        "story_bible": state_update.get("story_bible", ""),
                        "character_sheets": state_update.get("character_sheets", ""),
                        "plot_outline": state_update.get("plot_outline", ""),
                        "current_chapter_index": state_update.get("current_chapter_index", 0),
                        "current_chapter_draft": state_update.get("current_chapter_draft", ""),
                        "chapters": state_update.get("chapters", []),
                        "chapter_summaries": state_update.get("chapter_summaries", []),
                        "continuity_notes": state_update.get("continuity_notes", ""),
                        "showrunner_status": state_update.get("showrunner_status", ""),
                        "final_manuscript": state_update.get("final_manuscript", ""),
                        "target_chapters": chapter_count,
                    },
                }

        # Final event
        yield {
            "event": "story_complete",
            "data": {
                "target_chapters": chapter_count,
            },
        }
