from __future__ import annotations

from langchain_core.messages import AIMessage

from ..utils.prompt_utils import format_recent_summaries, get_language_instruction


def _chapter_beat(state) -> str:
    beats = state.get("chapter_beats", [])
    index = state["current_chapter_index"] - 1
    if 0 <= index < len(beats):
        return beats[index]
    return f"Chapter {state['current_chapter_index']}: advance the story decisively."


def create_chapter_writer(llm, config: dict):
    def writer_node(state) -> dict:
        beat = _chapter_beat(state)
        rewrite_mode = "yes" if state.get("revision_notes") else "no"
        prompt = f"""You are the chapter writer for a collaborative fiction room.

Story title: {state["story_title"]}

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Character sheets:
{state["character_sheets"]}

Full outline:
{state["plot_outline"]}

Current beat:
{beat}

Approved chapter summaries:
{format_recent_summaries(state.get("chapter_summaries", []))}

Continuity notes:
{state.get("continuity_notes") or "None yet."}

Rewrite requested: {rewrite_mode}
Revision notes:
{state.get("revision_notes") or "None."}

Write Chapter {state["current_chapter_index"]} in polished prose. Keep it narratively complete, emotionally specific, and aligned with the beat. If revision notes are present, fully rewrite the chapter rather than patching isolated sentences.{get_language_instruction(config)}"""

        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return {
            "messages": [AIMessage(content=content)],
            "current_chapter_draft": content,
        }

    return writer_node
