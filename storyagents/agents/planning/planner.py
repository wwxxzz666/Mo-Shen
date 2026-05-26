from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import StoryPlan, render_story_plan

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def create_story_planner(llm, config: dict):
    structured_llm = bind_structured(llm, StoryPlan, "Story Planner")

    def planner_node(state) -> dict:
        prompt = f"""You are a developmental editor turning a rough fiction idea into a clean production brief.

User request:
{state["user_request"]}

Default target chapters: {state["target_chapters"]}.

Extract the story's premise, audience, point of view, tone, and core conflict. If the user did not specify a chapter count, keep the default target chapter count.{get_language_instruction(config)}"""

        if structured_llm is not None:
            try:
                plan = structured_llm.invoke(prompt)
                rendered = render_story_plan(plan)
                return {
                    "messages": [AIMessage(content=rendered)],
                    "story_title": plan.title,
                    "story_brief": rendered,
                    "target_chapters": plan.target_chapters,
                }
            except Exception:
                pass

        response = llm.invoke(prompt)
        title = "Untitled Story"
        for line in response.content.splitlines():
            cleaned = line.strip().lstrip("#").strip()
            if cleaned:
                title = cleaned
                break
        return {
            "messages": [response],
            "story_title": title,
            "story_brief": response.content,
        }

    return planner_node
