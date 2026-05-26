from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import ChapterReview, ReviewVerdict

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def create_continuity_reviewer(llm, config: dict):
    structured_llm = bind_structured(llm, ChapterReview, "Continuity Reviewer")

    def reviewer_node(state) -> dict:
        prompt = f"""You are the continuity reviewer and developmental editor for a fiction pipeline.

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Character sheets:
{state["character_sheets"]}

Outline:
{state["plot_outline"]}

Current chapter draft:
{state["current_chapter_draft"]}

Existing continuity notes:
{state.get("continuity_notes") or "None yet."}

Decide whether the chapter is ready to keep. Approve only if character motivation, continuity, and chapter purpose are all coherent. If not, provide concrete rewrite instructions.{get_language_instruction(config)}"""

        if structured_llm is not None:
            try:
                review = structured_llm.invoke(prompt)
                revision_count = state["revision_count"]
                if review.verdict == ReviewVerdict.REVISE:
                    revision_count += 1
                return {
                    "messages": [AIMessage(content=f"{review.verdict.value}: {review.revision_instructions}")],
                    "reviewer_verdict": review.verdict.value,
                    "revision_notes": review.revision_instructions,
                    "current_chapter_summary": review.chapter_summary,
                    "continuity_notes": review.continuity_notes,
                    "revision_count": revision_count,
                }
            except Exception:
                pass

        response = llm.invoke(prompt)
        verdict = (
            ReviewVerdict.APPROVE.value
            if "APPROVE" in response.content.upper()
            else ReviewVerdict.REVISE.value
        )
        revision_count = state["revision_count"] + (1 if verdict == ReviewVerdict.REVISE.value else 0)
        return {
            "messages": [response],
            "reviewer_verdict": verdict,
            "revision_notes": response.content,
            "current_chapter_summary": state["current_chapter_draft"][:300],
            "revision_count": revision_count,
        }

    return reviewer_node
