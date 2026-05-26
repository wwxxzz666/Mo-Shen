from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import StoryOutline, outline_to_beat_text, render_story_outline

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def _fallback_beats(target_chapters: int) -> list[str]:
    beats = []
    for idx in range(1, target_chapters + 1):
        beats.append(
            "\n".join(
                [
                    f"Chapter {idx}: Working Beat {idx}",
                    "Objective: Advance the central conflict.",
                    "Conflict: Force the protagonist to make a meaningful choice.",
                    "Ending Hook: End with a turn that pulls readers into the next chapter.",
                ]
            )
        )
    return beats


def create_outline_agent(llm, config: dict):
    structured_llm = bind_structured(llm, StoryOutline, "Outline Agent")

    def outline_node(state) -> dict:
        prompt = f"""You are a story architect creating a chapter outline for a fiction draft.

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Character sheets:
{state["character_sheets"]}

Produce exactly {state["target_chapters"]} chapter beats, each with a clear objective, conflict, and ending hook.{get_language_instruction(config)}"""

        if structured_llm is not None:
            try:
                outline = structured_llm.invoke(prompt)
                rendered = render_story_outline(outline)
                beats = outline_to_beat_text(outline)
                if not beats:
                    beats = _fallback_beats(state["target_chapters"])
                return {
                    "messages": [AIMessage(content=rendered)],
                    "plot_outline": rendered,
                    "chapter_beats": beats,
                }
            except Exception:
                pass

        response = llm.invoke(prompt)
        return {
            "messages": [response],
            "plot_outline": response.content,
            "chapter_beats": _fallback_beats(state["target_chapters"]),
        }

    return outline_node
