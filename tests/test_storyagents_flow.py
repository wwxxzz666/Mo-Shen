import re

from langchain_core.messages import AIMessage

from storyagents.graph.conditional_logic import StoryConditionalLogic
from storyagents.graph.propagation import StoryPropagator
from storyagents.graph.setup import StoryGraphSetup
from storyagents.schemas import (
    ChapterReview,
    CharacterBundle,
    ReviewVerdict,
    ShowrunnerDecision,
    ShowrunnerStatus,
    StoryOutline,
    StoryPlan,
    StoryWorld,
    ChapterBeat,
)


class _StructuredResponder:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, prompt):
        if self.schema is StoryPlan:
            return StoryPlan(
                title="The Salt Tower",
                premise="A courier discovers a drowned city's memory archive can rewrite grief.",
                genre="Speculative mystery",
                tone="Lyrical and tense",
                audience="Adult crossover readers",
                pov="Close third person",
                tense="Past tense",
                core_conflict="The protagonist must decide whether truth is worth reopening collective trauma.",
                must_include=["A submerged library", "A choice that costs a friendship"],
                target_chapters=2,
            )
        if self.schema is StoryWorld:
            return StoryWorld(
                world_summary="A coastal city survives by harvesting memories from flooded ruins.",
                rules=["Memories decay when exposed to direct sunlight.", "Divers can carry only one memory shard at a time."],
                key_locations=["The salt tower archive", "The drowned tram tunnels"],
                conflict_engine="Every recovered memory can destabilize the political myths holding the city together.",
            )
        if self.schema is CharacterBundle:
            return CharacterBundle(
                protagonist="Mira, a disciplined courier who distrusts nostalgia yet secretly hoards forbidden memories.",
                antagonist="Archivist Vey, who weaponizes selective truth to keep the city orderly.",
                supporting_cast=["Jun, Mira's engineer friend who wants the city to remember honestly."],
                relationship_web="Mira and Jun share deep trust that frays when Jun pushes her toward public disclosure.",
            )
        if self.schema is StoryOutline:
            return StoryOutline(
                logline="A courier risks the city's fragile peace by uncovering a memory everyone agreed to drown.",
                act_structure="Chapter one opens the mystery; chapter two forces the public choice.",
                chapter_beats=[
                    ChapterBeat(
                        chapter_number=1,
                        title="The First Retrieval",
                        objective="Introduce Mira and the forbidden memory shard.",
                        conflict="Mira must hide the shard from the archive while Jun pressures her to decode it.",
                        ending_hook="The shard reveals someone erased Jun's sister from the city's official history.",
                    ),
                    ChapterBeat(
                        chapter_number=2,
                        title="The Public Unsealing",
                        objective="Force Mira to decide whether to expose the archive's lie.",
                        conflict="Vey offers Mira safety if she buries the truth again.",
                        ending_hook="Mira releases the memory and accepts the city's anger.",
                    ),
                ],
            )
        if self.schema is ChapterReview:
            chapter_match = re.search(r"Current chapter draft:\n(.+)", prompt, re.DOTALL)
            draft = chapter_match.group(1).strip() if chapter_match else "Draft unavailable."
            chapter_number_match = re.search(r"Chapter (\d+)", draft)
            chapter_number = chapter_number_match.group(1) if chapter_number_match else "?"
            return ChapterReview(
                verdict=ReviewVerdict.APPROVE,
                continuity_notes=f"Chapter {chapter_number} locks in Mira's escalating distrust of the archive.",
                revision_instructions="Ready to keep.",
                chapter_summary=f"Approved summary for chapter {chapter_number}.",
            )
        if self.schema is ShowrunnerDecision:
            match = re.search(r"Current chapter: (\d+) of (\d+)", prompt)
            current = int(match.group(1))
            total = int(match.group(2))
            status = (
                ShowrunnerStatus.CONTINUE
                if current < total
                else ShowrunnerStatus.COMPLETE
            )
            return ShowrunnerDecision(
                status=status,
                editorial_note=f"Chapter {current} lands the intended turn cleanly.",
                next_chapter_focus=(
                    "Escalate the emotional cost of telling the truth."
                    if status == ShowrunnerStatus.CONTINUE
                    else "Close the run with the consequences now in motion."
                ),
            )
        raise AssertionError(f"Unexpected schema: {self.schema}")


class _FakeLLM:
    def with_structured_output(self, schema):
        return _StructuredResponder(schema)

    def invoke(self, prompt):
        match = re.search(r"Write Chapter (\d+)", str(prompt))
        chapter_number = match.group(1) if match else "?"
        return AIMessage(
            content=(
                f"Chapter {chapter_number}\n\n"
                f"Mira enters the scene for chapter {chapter_number} and makes a costly choice."
            )
        )


def test_story_propagator_initial_state():
    state = StoryPropagator().create_initial_state("Write me a flooded-city mystery.", 2)

    assert state["target_chapters"] == 2
    assert state["current_chapter_index"] == 1
    assert state["chapters"] == []
    assert state["revision_count"] == 0


def test_story_conditional_logic_routes_revision_loop():
    logic = StoryConditionalLogic(max_revision_rounds=2)

    assert logic.after_reviewer({"reviewer_verdict": "Revise", "revision_count": 1}) == "Chapter Writer"
    assert logic.after_reviewer({"reviewer_verdict": "Revise", "revision_count": 2}) == "Showrunner"
    assert logic.after_showrunner({"showrunner_status": "Continue", "chapters": ["c1"], "target_chapters": 2}) == "Chapter Writer"
    assert logic.after_showrunner({"showrunner_status": "Continue", "chapters": ["c1", "c2"], "target_chapters": 2}) == "__end__"


def test_story_graph_runs_two_chapters_end_to_end():
    fake_llm = _FakeLLM()
    workflow = StoryGraphSetup(fake_llm, fake_llm, {"max_revision_rounds": 2, "output_language": "English"}).setup_graph()
    graph = workflow.compile()
    initial_state = StoryPropagator().create_initial_state(
        "Write a two-chapter speculative mystery about archived memories.",
        2,
    )

    result = graph.invoke(initial_state, config={"recursion_limit": 40})

    assert result["story_title"] == "The Salt Tower"
    assert len(result["chapters"]) == 2
    assert "Chapter 1" in result["final_manuscript"]
    assert "Chapter 2" in result["final_manuscript"]
    assert result["showrunner_status"] == "Complete"
