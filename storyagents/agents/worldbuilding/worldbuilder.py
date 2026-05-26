from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import StoryWorld, render_story_world

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def create_worldbuilder(llm, config: dict):
    structured_llm = bind_structured(llm, StoryWorld, "Worldbuilder")

    def worldbuilder_node(state) -> dict:
        prompt = f"""You are a worldbuilding specialist creating a concise but durable story bible.

Story brief:
{state["story_brief"]}

Focus on the rules, locations, and pressures that will keep the plot moving. Keep it specific enough for future chapters to stay consistent.{get_language_instruction(config)}"""

        if structured_llm is not None:
            try:
                world = structured_llm.invoke(prompt)
                rendered = render_story_world(world)
                return {
                    "messages": [AIMessage(content=rendered)],
                    "story_bible": rendered,
                }
            except Exception:
                pass

        response = llm.invoke(prompt)
        return {
            "messages": [response],
            "story_bible": response.content,
        }

    return worldbuilder_node
