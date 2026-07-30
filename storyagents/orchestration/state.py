from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class StoryState(TypedDict, total=False):
    """Shared story workspace passed between AgentScope role agents."""

    messages: List[Any]
    user_request: str
    story_title: str
    story_brief: str
    target_chapters: int
    story_bible: str
    character_sheets: str
    plot_outline: str
    chapter_beats: List[str]
    current_chapter_index: int
    current_chapter_draft: str
    current_chapter_summary: str
    chapters: List[str]
    chapter_summaries: List[str]
    revision_notes: str
    continuity_notes: str
    reviewer_verdict: str
    revision_count: int
    showrunner_note: str
    showrunner_status: str
    final_manuscript: str


def create_initial_state(user_request: str, target_chapters: int) -> Dict[str, Any]:
    return {
        "messages": [("human", user_request)],
        "user_request": user_request,
        "story_title": "",
        "story_brief": "",
        "target_chapters": target_chapters,
        "story_bible": "",
        "character_sheets": "",
        "plot_outline": "",
        "chapter_beats": [],
        "current_chapter_index": 1,
        "current_chapter_draft": "",
        "current_chapter_summary": "",
        "chapters": [],
        "chapter_summaries": [],
        "revision_notes": "",
        "continuity_notes": "",
        "reviewer_verdict": "",
        "revision_count": 0,
        "showrunner_note": "",
        "showrunner_status": "",
        "final_manuscript": "",
    }
