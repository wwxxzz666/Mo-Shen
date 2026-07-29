from __future__ import annotations

from typing import Any, Dict


class StoryConditionalLogic:
    """Routing rules previously expressed as LangGraph conditional edges."""

    def __init__(self, max_revision_rounds: int = 2):
        self.max_revision_rounds = max_revision_rounds

    def after_reviewer(self, state: Dict[str, Any]) -> str:
        if (
            state.get("reviewer_verdict") == "Revise"
            and state.get("revision_count", 0) < self.max_revision_rounds
        ):
            return "Chapter Writer"
        return "Showrunner"

    def after_showrunner(self, state: Dict[str, Any]) -> str:
        if (
            state.get("showrunner_status") == "Continue"
            and len(state.get("chapters", [])) < state.get("target_chapters", 0)
        ):
            return "Chapter Writer"
        return "__end__"
