from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import CharacterBundle, render_character_bundle

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def create_character_designer(llm, config: dict):
    structured_llm = bind_structured(llm, CharacterBundle, "Character Designer")

    def character_node(state) -> dict:
        prompt = f"""You are a character designer building a cast that can sustain the story.

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Create a protagonist, antagonist, and supporting cast whose desires collide in interesting ways.{get_language_instruction(config)}"""

        if structured_llm is not None:
            try:
                bundle = structured_llm.invoke(prompt)
                rendered = render_character_bundle(bundle)
                return {
                    "messages": [AIMessage(content=rendered)],
                    "character_sheets": rendered,
                }
            except Exception:
                pass

        response = llm.invoke(prompt)
        return {
            "messages": [response],
            "character_sheets": response.content,
        }

    return character_node
