from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel

from storyagents.schemas import (
    ChapterReview,
    CharacterBundle,
    ReviewVerdict,
    ShowrunnerDecision,
    ShowrunnerStatus,
    StoryOutline,
    StoryPlan,
    StoryWorld,
    outline_to_beat_text,
    render_character_bundle,
    render_story_outline,
    render_story_plan,
    render_story_world,
)

from .prompts import (
    ROLE_SYSTEM_PROMPTS,
    character_prompt,
    outline_prompt,
    planner_prompt,
    reviewer_prompt,
    showrunner_prompt,
    worldbuilder_prompt,
    writer_prompt,
)


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


def _first_nonempty_title(text: str, default: str = "Untitled Story") -> str:
    for line in (text or "").splitlines():
        cleaned = line.strip().lstrip("#").strip()
        if cleaned:
            return cleaned
    return default


class StoryRoleAgent:
    """One specialized AgentScope agent in the fiction pipeline."""

    def __init__(
        self,
        name: str,
        model: Any,
        config: dict,
        *,
        prompt_builder: Callable[[Dict[str, Any], dict], str],
        structured_schema: Optional[Type[BaseModel]] = None,
        apply_result: Callable[[Dict[str, Any], Any, str, dict], Dict[str, Any]],
    ):
        self.name = name
        self.model = model
        self.config = config
        self.prompt_builder = prompt_builder
        self.structured_schema = structured_schema
        self.apply_result = apply_result

    def _build_agent(self):
        from agentscope.agent import Agent, InjectionConfig, ReActConfig

        return Agent(
            name=self.name,
            system_prompt=ROLE_SYSTEM_PROMPTS[self.name],
            model=self.model,
            react_config=ReActConfig(max_iters=6),
            # Fiction roles receive full task context in each user message;
            # disable runtime state injection to keep prompts stable.
            injection_config=InjectionConfig(inject_runtime_state=False),
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        from agentscope.message import UserMsg

        agent = self._build_agent()
        prompt = self.prompt_builder(state, self.config)
        user_msg = UserMsg(name="user", content=prompt)

        structured_obj: Any = None
        text = ""

        try:
            if self.structured_schema is not None:
                reply = await agent.reply(
                    user_msg,
                    structured_schema=self.structured_schema,
                )
                raw = reply.structured_output
                if raw:
                    structured_obj = self.structured_schema.model_validate(raw)
                text = reply.get_text_content() or ""
            else:
                reply = await agent.reply(user_msg)
                text = reply.get_text_content() or ""
        except Exception:
            # Fall back to a plain free-text reply on a fresh agent if structured
            # output fails (avoids carrying a half-finished ReAct state).
            if self.structured_schema is None:
                raise
            fallback_agent = self._build_agent()
            reply = await fallback_agent.reply(user_msg)
            text = reply.get_text_content() or ""

        return self.apply_result(state, structured_obj, text, self.config)


def _apply_planner(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    if isinstance(structured, StoryPlan):
        rendered = render_story_plan(structured)
        return {
            "messages": [("ai", rendered)],
            "story_title": structured.title,
            "story_brief": rendered,
        }
    title = _first_nonempty_title(text)
    return {
        "messages": [("ai", text)],
        "story_title": title,
        "story_brief": text,
    }


def _apply_worldbuilder(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    if isinstance(structured, StoryWorld):
        rendered = render_story_world(structured)
        return {"messages": [("ai", rendered)], "story_bible": rendered}
    return {"messages": [("ai", text)], "story_bible": text}


def _apply_character(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    if isinstance(structured, CharacterBundle):
        rendered = render_character_bundle(structured)
        return {"messages": [("ai", rendered)], "character_sheets": rendered}
    return {"messages": [("ai", text)], "character_sheets": text}


def _apply_outline(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    if isinstance(structured, StoryOutline):
        rendered = render_story_outline(structured)
        beats = outline_to_beat_text(structured) or _fallback_beats(
            state["target_chapters"]
        )
        return {
            "messages": [("ai", rendered)],
            "plot_outline": rendered,
            "chapter_beats": beats,
        }
    return {
        "messages": [("ai", text)],
        "plot_outline": text,
        "chapter_beats": _fallback_beats(state["target_chapters"]),
    }


def _apply_writer(
    state: Dict[str, Any],
    _structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    return {
        "messages": [("ai", text)],
        "current_chapter_draft": text,
    }


def _apply_reviewer(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    _config: dict,
) -> Dict[str, Any]:
    if isinstance(structured, ChapterReview):
        revision_count = state.get("revision_count", 0)
        if structured.verdict == ReviewVerdict.REVISE:
            revision_count += 1
        return {
            "messages": [
                (
                    "ai",
                    f"{structured.verdict.value}: {structured.revision_instructions}",
                )
            ],
            "reviewer_verdict": structured.verdict.value,
            "revision_notes": structured.revision_instructions,
            "current_chapter_summary": structured.chapter_summary,
            "continuity_notes": structured.continuity_notes,
            "revision_count": revision_count,
        }

    verdict = (
        ReviewVerdict.APPROVE.value
        if "APPROVE" in (text or "").upper()
        else ReviewVerdict.REVISE.value
    )
    revision_count = state.get("revision_count", 0) + (
        1 if verdict == ReviewVerdict.REVISE.value else 0
    )
    return {
        "messages": [("ai", text)],
        "reviewer_verdict": verdict,
        "revision_notes": text,
        "current_chapter_summary": (state.get("current_chapter_draft") or "")[:300],
        "revision_count": revision_count,
    }


def _apply_showrunner(
    state: Dict[str, Any],
    structured: Any,
    text: str,
    config: dict,
) -> Dict[str, Any]:
    chapter_index = state["current_chapter_index"]
    target_chapters = state["target_chapters"]
    default_status = (
        ShowrunnerStatus.COMPLETE
        if chapter_index >= target_chapters
        else ShowrunnerStatus.CONTINUE
    )

    editorial_note = text
    next_focus = ""
    status = default_status

    if isinstance(structured, ShowrunnerDecision):
        editorial_note = structured.editorial_note
        next_focus = structured.next_chapter_focus
        status = structured.status

    if chapter_index >= target_chapters:
        status = ShowrunnerStatus.COMPLETE

    accepted_chapters = list(state.get("chapters", []))
    accepted_summaries = list(state.get("chapter_summaries", []))

    if len(accepted_chapters) < chapter_index:
        accepted_chapters.append(state["current_chapter_draft"])
    if len(accepted_summaries) < chapter_index:
        accepted_summaries.append(state.get("current_chapter_summary") or "")

    final_manuscript = "\n\n".join(
        f"# Chapter {idx}\n\n{chapter}"
        for idx, chapter in enumerate(accepted_chapters, start=1)
    )

    updates: Dict[str, Any] = {
        "messages": [("ai", editorial_note)],
        "chapters": accepted_chapters,
        "chapter_summaries": accepted_summaries,
        "showrunner_note": editorial_note,
        "showrunner_status": status.value,
        "final_manuscript": final_manuscript,
        "revision_notes": "",
        "reviewer_verdict": "",
        "revision_count": 0,
    }

    if status == ShowrunnerStatus.CONTINUE and chapter_index < target_chapters:
        updates["current_chapter_index"] = chapter_index + 1
        if next_focus:
            updates["continuity_notes"] = (
                (state.get("continuity_notes") or "")
                + "\n\nShowrunner handoff:\n"
                + next_focus
            ).strip()

    return updates


def build_role_agents(
    *,
    deep_model: Any,
    quick_model: Any,
    config: dict,
    include_worldbuilding: bool,
    include_continuity_review: bool,
) -> Dict[str, StoryRoleAgent]:
    agents: Dict[str, StoryRoleAgent] = {
        "Planner": StoryRoleAgent(
            "Planner",
            deep_model,
            config,
            prompt_builder=planner_prompt,
            structured_schema=StoryPlan,
            apply_result=_apply_planner,
        ),
        "Outline Agent": StoryRoleAgent(
            "Outline Agent",
            deep_model,
            config,
            prompt_builder=outline_prompt,
            structured_schema=StoryOutline,
            apply_result=_apply_outline,
        ),
        "Chapter Writer": StoryRoleAgent(
            "Chapter Writer",
            quick_model,
            config,
            prompt_builder=writer_prompt,
            structured_schema=None,
            apply_result=_apply_writer,
        ),
        "Showrunner": StoryRoleAgent(
            "Showrunner",
            deep_model,
            config,
            prompt_builder=showrunner_prompt,
            structured_schema=ShowrunnerDecision,
            apply_result=_apply_showrunner,
        ),
    }

    if include_worldbuilding:
        agents["Worldbuilder"] = StoryRoleAgent(
            "Worldbuilder",
            quick_model,
            config,
            prompt_builder=worldbuilder_prompt,
            structured_schema=StoryWorld,
            apply_result=_apply_worldbuilder,
        )
        agents["Character Designer"] = StoryRoleAgent(
            "Character Designer",
            quick_model,
            config,
            prompt_builder=character_prompt,
            structured_schema=CharacterBundle,
            apply_result=_apply_character,
        )

    if include_continuity_review:
        agents["Continuity Reviewer"] = StoryRoleAgent(
            "Continuity Reviewer",
            quick_model,
            config,
            prompt_builder=reviewer_prompt,
            structured_schema=ChapterReview,
            apply_result=_apply_reviewer,
        )

    return agents
