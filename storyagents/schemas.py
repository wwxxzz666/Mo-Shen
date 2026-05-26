from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class StoryPlan(BaseModel):
    title: str = Field(description="Working title for the novel or novella.")
    premise: str = Field(description="One-paragraph premise for the story.")
    genre: str = Field(description="Primary genre and subgenre if relevant.")
    tone: str = Field(description="Desired emotional tone and reading experience.")
    audience: str = Field(description="Target audience for the story.")
    pov: str = Field(description="Narrative point of view, such as first person or close third.")
    tense: str = Field(description="Narrative tense, such as past tense or present tense.")
    core_conflict: str = Field(description="The central conflict driving the story.")
    must_include: List[str] = Field(
        default_factory=list,
        description="Concrete elements or scenes that must appear in the story.",
    )
    target_chapters: int = Field(
        description="Recommended chapter count for the first draft.",
        ge=1,
        le=12,
    )


def render_story_plan(plan: StoryPlan) -> str:
    must_include = (
        "\n".join(f"- {item}" for item in plan.must_include)
        if plan.must_include
        else "- None specified"
    )
    return "\n".join(
        [
            f"# {plan.title}",
            "",
            f"**Premise**: {plan.premise}",
            "",
            f"**Genre**: {plan.genre}",
            f"**Tone**: {plan.tone}",
            f"**Audience**: {plan.audience}",
            f"**POV**: {plan.pov}",
            f"**Tense**: {plan.tense}",
            f"**Core Conflict**: {plan.core_conflict}",
            f"**Target Chapters**: {plan.target_chapters}",
            "",
            "## Must Include",
            must_include,
        ]
    )


class StoryWorld(BaseModel):
    world_summary: str = Field(description="High-level world summary for the story.")
    rules: List[str] = Field(
        default_factory=list,
        description="Important rules, constraints, or genre promises that should stay consistent.",
    )
    key_locations: List[str] = Field(
        default_factory=list,
        description="Important locations that should shape the plot.",
    )
    conflict_engine: str = Field(
        description="Why this world naturally keeps producing conflict and momentum."
    )


def render_story_world(world: StoryWorld) -> str:
    rules = "\n".join(f"- {item}" for item in world.rules) if world.rules else "- None"
    locations = (
        "\n".join(f"- {item}" for item in world.key_locations)
        if world.key_locations
        else "- None"
    )
    return "\n".join(
        [
            "## World Summary",
            world.world_summary,
            "",
            "## Rules",
            rules,
            "",
            "## Key Locations",
            locations,
            "",
            "## Conflict Engine",
            world.conflict_engine,
        ]
    )


class CharacterBundle(BaseModel):
    protagonist: str = Field(description="Profile of the protagonist with goals and flaws.")
    antagonist: str = Field(description="Profile of the antagonist or primary opposing force.")
    supporting_cast: List[str] = Field(
        default_factory=list,
        description="Important supporting characters and what each contributes.",
    )
    relationship_web: str = Field(
        description="How the main characters relate to and pressure each other."
    )


def render_character_bundle(bundle: CharacterBundle) -> str:
    cast = (
        "\n".join(f"- {item}" for item in bundle.supporting_cast)
        if bundle.supporting_cast
        else "- None"
    )
    return "\n".join(
        [
            "## Protagonist",
            bundle.protagonist,
            "",
            "## Antagonist",
            bundle.antagonist,
            "",
            "## Supporting Cast",
            cast,
            "",
            "## Relationship Web",
            bundle.relationship_web,
        ]
    )


class ChapterBeat(BaseModel):
    chapter_number: int = Field(description="1-based chapter index.")
    title: str = Field(description="Working chapter title.")
    objective: str = Field(description="What the chapter must accomplish.")
    conflict: str = Field(description="The central pressure or conflict in the chapter.")
    ending_hook: str = Field(description="How the chapter should propel the reader forward.")


class StoryOutline(BaseModel):
    logline: str = Field(description="One-sentence story logline.")
    act_structure: str = Field(description="Short explanation of the story arc.")
    chapter_beats: List[ChapterBeat] = Field(
        default_factory=list,
        description="Ordered chapter beats for the draft.",
    )


def render_story_outline(outline: StoryOutline) -> str:
    beat_lines = []
    for beat in outline.chapter_beats:
        beat_lines.extend(
            [
                f"### Chapter {beat.chapter_number}: {beat.title}",
                f"- Objective: {beat.objective}",
                f"- Conflict: {beat.conflict}",
                f"- Ending Hook: {beat.ending_hook}",
                "",
            ]
        )
    if not beat_lines:
        beat_lines = ["- No chapter beats generated"]
    return "\n".join(
        [
            "## Logline",
            outline.logline,
            "",
            "## Act Structure",
            outline.act_structure,
            "",
            "## Chapter Beats",
            *beat_lines,
        ]
    ).rstrip()


def outline_to_beat_text(outline: StoryOutline) -> list[str]:
    beats = []
    for beat in outline.chapter_beats:
        beats.append(
            "\n".join(
                [
                    f"Chapter {beat.chapter_number}: {beat.title}",
                    f"Objective: {beat.objective}",
                    f"Conflict: {beat.conflict}",
                    f"Ending Hook: {beat.ending_hook}",
                ]
            )
        )
    return beats


class ReviewVerdict(str, Enum):
    APPROVE = "Approve"
    REVISE = "Revise"


class ChapterReview(BaseModel):
    verdict: ReviewVerdict = Field(
        description="Approve if the chapter is ready to keep, otherwise Revise."
    )
    continuity_notes: str = Field(
        description="Important canon, timeline, or emotional continuity notes to preserve."
    )
    revision_instructions: str = Field(
        description="Specific changes the writer should make if the chapter needs revision."
    )
    chapter_summary: str = Field(
        description="A concise summary of the current chapter for future context retrieval."
    )


class ShowrunnerStatus(str, Enum):
    CONTINUE = "Continue"
    COMPLETE = "Complete"


class ShowrunnerDecision(BaseModel):
    status: ShowrunnerStatus = Field(
        description="Continue if another chapter should be drafted, otherwise Complete."
    )
    editorial_note: str = Field(
        description="Short editorial note on what is working and what to carry forward."
    )
    next_chapter_focus: str = Field(
        description="Guidance for the next chapter, or a closing note if the story is done."
    )
