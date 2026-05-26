from typing import Annotated, List

from langgraph.graph import MessagesState


class StoryState(MessagesState):
    user_request: Annotated[str, "Original user story prompt"]
    story_title: Annotated[str, "Working title for the draft"]
    story_brief: Annotated[str, "Normalized creative brief"]
    target_chapters: Annotated[int, "Number of chapters to draft in this run"]
    story_bible: Annotated[str, "World-building reference document"]
    character_sheets: Annotated[str, "Character profiles and relationships"]
    plot_outline: Annotated[str, "Chapter-by-chapter outline"]
    chapter_beats: Annotated[List[str], "Ordered beat sheet, one string per chapter"]
    current_chapter_index: Annotated[int, "1-based current chapter index"]
    current_chapter_draft: Annotated[str, "Most recent chapter draft"]
    current_chapter_summary: Annotated[str, "Summary of the current chapter"]
    chapters: Annotated[List[str], "Approved chapter drafts"]
    chapter_summaries: Annotated[List[str], "Approved chapter summaries"]
    revision_notes: Annotated[str, "Latest reviewer change requests"]
    continuity_notes: Annotated[str, "Accumulated canon notes for future chapters"]
    reviewer_verdict: Annotated[str, "Approve or Revise"]
    revision_count: Annotated[int, "How many rewrites were requested for current chapter"]
    showrunner_note: Annotated[str, "Editorial handoff note"]
    showrunner_status: Annotated[str, "Continue or Complete"]
    final_manuscript: Annotated[str, "Combined story draft"]
