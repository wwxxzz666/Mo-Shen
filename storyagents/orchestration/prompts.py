"""Prompt builders for AgentScope story roles."""

from __future__ import annotations

from typing import Any, Dict, List


def get_language_instruction(config: dict) -> str:
    language = config.get("output_language", "English").strip()
    if language.lower() == "english":
        return ""
    return f" Write your response in {language}."


def format_recent_summaries(summaries: List[str], limit: int = 3) -> str:
    if not summaries:
        return "No prior chapters yet."
    recent = summaries[-limit:]
    return "\n\n".join(
        f"Chapter {idx + 1} summary:\n{summary}"
        for idx, summary in enumerate(
            recent, start=len(summaries) - len(recent) + 1
        )
    )


ROLE_SYSTEM_PROMPTS = {
    "Planner": (
        "You are a developmental editor turning rough fiction ideas into "
        "clean production briefs for a multi-agent novel room."
    ),
    "Worldbuilder": (
        "You are a worldbuilding specialist. Create concise, durable story "
        "bibles that keep later chapters consistent."
    ),
    "Character Designer": (
        "You are a character designer. Build casts whose desires collide and "
        "sustain multi-chapter conflict."
    ),
    "Outline Agent": (
        "You are a story architect. Produce chapter-by-chapter outlines with "
        "clear objectives, conflict, and ending hooks."
    ),
    "Chapter Writer": (
        "You are the chapter writer for a collaborative fiction room. Write "
        "polished, emotionally specific prose aligned with the beat sheet."
    ),
    "Continuity Reviewer": (
        "You are the continuity reviewer and developmental editor. Protect "
        "character motivation, timeline, and chapter purpose."
    ),
    "Showrunner": (
        "You are the showrunner overseeing a multi-agent fiction room. Make "
        "crisp editorial handoff decisions and keep the production on track."
    ),
    "Editor": (
        "You are a senior prose editor. Rewrite, expand, compress, or polish "
        "fiction text while preserving the author's intent."
    ),
}


def planner_prompt(state: Dict[str, Any], config: dict) -> str:
    return f"""Turn the rough fiction idea into a clean production brief.

User request:
{state["user_request"]}

Default target chapters: {state["target_chapters"]}.

Extract the story's premise, audience, point of view, tone, and core conflict. If the user did not specify a chapter count, keep the default target chapter count.{get_language_instruction(config)}"""


def worldbuilder_prompt(state: Dict[str, Any], config: dict) -> str:
    return f"""Create a concise but durable story bible.

Story brief:
{state["story_brief"]}

Focus on the rules, locations, and pressures that will keep the plot moving. Keep it specific enough for future chapters to stay consistent.{get_language_instruction(config)}"""


def character_prompt(state: Dict[str, Any], config: dict) -> str:
    return f"""Build a cast that can sustain the story.

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Create a protagonist, antagonist, and supporting cast whose desires collide in interesting ways.{get_language_instruction(config)}"""


def outline_prompt(state: Dict[str, Any], config: dict) -> str:
    return f"""Create a chapter outline for a fiction draft.

Story brief:
{state["story_brief"]}

World bible:
{state["story_bible"]}

Character sheets:
{state["character_sheets"]}

Produce exactly {state["target_chapters"]} chapter beats, each with a clear objective, conflict, and ending hook.{get_language_instruction(config)}"""


def _chapter_beat(state: Dict[str, Any]) -> str:
    beats = state.get("chapter_beats", [])
    index = state["current_chapter_index"] - 1
    if 0 <= index < len(beats):
        return beats[index]
    return f"Chapter {state['current_chapter_index']}: advance the story decisively."


def writer_prompt(state: Dict[str, Any], config: dict) -> str:
    beat = _chapter_beat(state)
    rewrite_mode = "yes" if state.get("revision_notes") else "no"
    return f"""Write the requested chapter in polished prose.

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


def reviewer_prompt(state: Dict[str, Any], config: dict) -> str:
    return f"""Review the current chapter for continuity and readiness.

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


def showrunner_prompt(state: Dict[str, Any], config: dict) -> str:
    chapter_index = state["current_chapter_index"]
    target_chapters = state["target_chapters"]
    maxed_out = (
        state.get("reviewer_verdict") == "Revise"
        and state.get("revision_count", 0) >= config["max_revision_rounds"]
    )
    return f"""Provide the editorial handoff for the multi-agent fiction room.

Story title: {state["story_title"]}
Current chapter: {chapter_index} of {target_chapters}

Reviewer verdict: {state.get("reviewer_verdict") or "N/A"}
Revision count used: {state.get("revision_count", 0)} / {config["max_revision_rounds"]}
Force accept due to maxed revisions: {"yes" if maxed_out else "no"}

Current chapter summary:
{state.get("current_chapter_summary") or "Summary unavailable."}

Current chapter draft:
{state["current_chapter_draft"]}

Continuity notes:
{state.get("continuity_notes") or "None yet."}

Write a short editorial handoff note for the room. If the story should continue, describe the next focus. If the current chapter should close the run, explain why.{get_language_instruction(config)}"""


EDIT_PROMPTS = {
    "rewrite": """请改写以下文字，保持原意但换一种表达方式。

要求：
- 保持原文的核心意思和情感
- 使用不同的词汇和句式
- 保持相同的长度范围
- 确保改写后的文字流畅自然

原文：
{text}

{context}""",
    "expand": """请扩写以下文字，增加更多细节和描写。

要求：
- 保持原文的核心情节和走向
- 增加环境描写、心理活动、感官细节
- 扩展对话和互动
- 扩写后长度为原文的 1.5-2 倍

原文：
{text}

{context}""",
    "compress": """请精简以下文字，去除冗余但保留精华。

要求：
- 保留核心情节和关键信息
- 删除重复、冗长的描写
- 精简对话，保留关键台词
- 压缩后长度为原文的 60-70%

原文：
{text}

{context}""",
    "polish": """请润色以下文字，提升文采和可读性。

要求：
- 保持原文结构和情节不变
- 优化用词，替换平淡词汇
- 改善句式节奏和韵律
- 增强文学性和感染力

原文：
{text}

{context}""",
}


def editor_prompt(
    text: str,
    action: str = "rewrite",
    context: str = "",
    instruction: str = "",
) -> str:
    prompt_template = EDIT_PROMPTS.get(action, EDIT_PROMPTS["rewrite"])
    context_block = ""
    if context:
        context_block = f"上下文信息：\n{context}"
    if instruction:
        context_block += f"\n\n用户指令：\n{instruction}"
    return prompt_template.format(text=text, context=context_block)
