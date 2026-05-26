from typing import Any, Dict


class StoryPropagator:
    def __init__(self, max_recur_limit: int = 80):
        self.max_recur_limit = max_recur_limit

    def create_initial_state(self, user_request: str, target_chapters: int) -> Dict[str, Any]:
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

    def graph_args(self) -> Dict[str, Any]:
        return {"config": {"recursion_limit": self.max_recur_limit}}
