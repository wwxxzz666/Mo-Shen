from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Optional

from .roles import StoryRoleAgent, build_role_agents
from .routing import StoryConditionalLogic
from .state import create_initial_state


class StoryWorkflow:
    """Sequential multi-agent fiction pipeline powered by AgentScope Agents."""

    def __init__(
        self,
        *,
        deep_model: Any,
        quick_model: Any,
        config: dict,
        role_agents: Optional[Dict[str, StoryRoleAgent]] = None,
    ):
        self.config = config
        self.workflow_mode = config.get("workflow_mode", "quick")
        self.include_worldbuilding = self.workflow_mode in {"standard", "deep"}
        self.include_continuity_review = self.workflow_mode == "deep"
        self.logic = StoryConditionalLogic(
            max_revision_rounds=config.get("max_revision_rounds", 2)
        )
        self.agents = role_agents or build_role_agents(
            deep_model=deep_model,
            quick_model=quick_model,
            config=config,
            include_worldbuilding=self.include_worldbuilding,
            include_continuity_review=self.include_continuity_review,
        )
        self.max_steps = int(config.get("max_recur_limit", 80))

    async def _run_role(
        self,
        name: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        agent = self.agents[name]
        updates = await agent.run(state)
        state.update(updates)
        return state

    def _snapshot(self, state: Dict[str, Any], chapter_count: int) -> Dict[str, Any]:
        return {
            "node": "",
            "story_title": state.get("story_title", ""),
            "story_brief": state.get("story_brief", ""),
            "story_bible": state.get("story_bible", ""),
            "character_sheets": state.get("character_sheets", ""),
            "plot_outline": state.get("plot_outline", ""),
            "current_chapter_index": state.get("current_chapter_index", 0),
            "current_chapter_draft": state.get("current_chapter_draft", ""),
            "chapters": state.get("chapters", []),
            "chapter_summaries": state.get("chapter_summaries", []),
            "continuity_notes": state.get("continuity_notes", ""),
            "showrunner_status": state.get("showrunner_status", ""),
            "final_manuscript": state.get("final_manuscript", ""),
            "target_chapters": chapter_count,
        }

    async def run(
        self,
        user_request: str,
        target_chapters: int,
    ) -> Dict[str, Any]:
        final_state: Dict[str, Any] = {}
        async for event in self.stream(user_request, target_chapters):
            if event["event"] == "node_complete":
                final_state = dict(event["data"])
                final_state.pop("node", None)
            elif event["event"] == "story_complete" and not final_state:
                final_state = dict(event.get("data") or {})
        # Reconstruct a full state for callers that need manuscript fields.
        # The stream already carries the full snapshot after showrunner.
        return final_state

    async def stream(
        self,
        user_request: str,
        target_chapters: int,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        state = create_initial_state(user_request, target_chapters)
        steps = 0

        async def emit(node_name: str) -> AsyncGenerator[Dict[str, Any], None]:
            nonlocal steps, state
            steps += 1
            if steps > self.max_steps:
                raise RuntimeError(
                    f"Story workflow exceeded max steps ({self.max_steps})."
                )
            state = await self._run_role(node_name, state)
            payload = self._snapshot(state, target_chapters)
            payload["node"] = node_name
            yield {"event": "node_complete", "data": payload}

        # Planning phase
        async for event in emit("Planner"):
            yield event

        if self.include_worldbuilding:
            async for event in emit("Worldbuilder"):
                yield event
            async for event in emit("Character Designer"):
                yield event

        async for event in emit("Outline Agent"):
            yield event

        # Chapter loop with optional continuity revision
        while True:
            async for event in emit("Chapter Writer"):
                yield event

            if self.include_continuity_review:
                async for event in emit("Continuity Reviewer"):
                    yield event
                if self.logic.after_reviewer(state) == "Chapter Writer":
                    continue

            async for event in emit("Showrunner"):
                yield event

            if self.logic.after_showrunner(state) == "Chapter Writer":
                continue
            break

        yield {
            "event": "story_complete",
            "data": {
                "target_chapters": target_chapters,
                "story_title": state.get("story_title", ""),
                "final_manuscript": state.get("final_manuscript", ""),
                "chapters": state.get("chapters", []),
                "showrunner_status": state.get("showrunner_status", ""),
            },
        }

        # Keep final fields available after stream ends via last full state.
        self._last_state = state
