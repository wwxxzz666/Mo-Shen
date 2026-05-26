from __future__ import annotations

from langchain_core.messages import AIMessage

from storyagents.schemas import ShowrunnerDecision, ShowrunnerStatus

from ..utils.prompt_utils import get_language_instruction
from ..utils.structured_utils import bind_structured


def create_showrunner(llm, config: dict):
    structured_llm = bind_structured(llm, ShowrunnerDecision, "Showrunner")

    def showrunner_node(state) -> dict:
        chapter_index = state["current_chapter_index"]
        target_chapters = state["target_chapters"]
        maxed_out = (
            state["reviewer_verdict"] == "Revise"
            and state["revision_count"] >= config["max_revision_rounds"]
        )

        prompt = f"""You are the showrunner overseeing a multi-agent fiction room.

Story title: {state["story_title"]}
Current chapter: {chapter_index} of {target_chapters}

Reviewer verdict: {state["reviewer_verdict"]}
Revision count used: {state["revision_count"]} / {config["max_revision_rounds"]}
Force accept due to maxed revisions: {"yes" if maxed_out else "no"}

Current chapter summary:
{state.get("current_chapter_summary") or "Summary unavailable."}

Current chapter draft:
{state["current_chapter_draft"]}

Continuity notes:
{state.get("continuity_notes") or "None yet."}

Write a short editorial handoff note for the room. If the story should continue, describe the next focus. If the current chapter should close the run, explain why.{get_language_instruction(config)}"""

        default_status = (
            ShowrunnerStatus.COMPLETE
            if chapter_index >= target_chapters
            else ShowrunnerStatus.CONTINUE
        )
        editorial_note = ""
        next_focus = ""

        if structured_llm is not None:
            try:
                decision = structured_llm.invoke(prompt)
                editorial_note = decision.editorial_note
                next_focus = decision.next_chapter_focus
                status = decision.status
            except Exception:
                response = llm.invoke(prompt)
                editorial_note = response.content
                next_focus = ""
                status = default_status
        else:
            response = llm.invoke(prompt)
            editorial_note = response.content
            next_focus = ""
            status = default_status

        # The run should always close cleanly once we have reached the
        # requested chapter budget, even if the model suggests "Continue".
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

        updates = {
            "messages": [AIMessage(content=editorial_note)],
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

    return showrunner_node
