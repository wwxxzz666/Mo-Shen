from storyagents.orchestration.prompts import get_chapter_length_instruction
from storyagents.orchestration.roles import (
    _apply_outline,
    _apply_planner,
    _apply_reviewer,
    _apply_showrunner,
    _apply_writer,
)
from storyagents.orchestration.routing import StoryConditionalLogic
from storyagents.orchestration.state import create_initial_state
from storyagents.orchestration.story_graph import StoryAgentsGraph
from storyagents.orchestration.workflow import StoryWorkflow
from storyagents.schemas import (
    ChapterBeat,
    ChapterReview,
    CharacterBundle,
    ReviewVerdict,
    ShowrunnerDecision,
    ShowrunnerStatus,
    StoryOutline,
    StoryPlan,
    StoryWorld,
)


class _FakeRoleAgent:
    """Deterministic stand-in for AgentScope role agents in unit tests."""

    def __init__(self, name: str):
        self.name = name

    async def run(self, state):
        if self.name == "Planner":
            plan = StoryPlan(
                title="The Salt Tower",
                premise="A courier discovers a drowned city's memory archive can rewrite grief.",
                genre="Speculative mystery",
                tone="Lyrical and tense",
                audience="Adult crossover readers",
                pov="Close third person",
                tense="Past tense",
                core_conflict="The protagonist must decide whether truth is worth reopening collective trauma.",
                must_include=["A submerged library", "A choice that costs a friendship"],
                target_chapters=state["target_chapters"],
            )
            return _apply_planner(state, plan, "", {})

        if self.name == "Worldbuilder":
            world = StoryWorld(
                world_summary="A coastal city survives by harvesting memories from flooded ruins.",
                rules=["Memories decay when exposed to direct sunlight."],
                key_locations=["The salt tower archive"],
                conflict_engine="Recovered memories destabilize political myths.",
            )
            from storyagents.orchestration.roles import _apply_worldbuilder

            return _apply_worldbuilder(state, world, "", {})

        if self.name == "Character Designer":
            bundle = CharacterBundle(
                protagonist="Mira, a disciplined courier.",
                antagonist="Archivist Vey.",
                supporting_cast=["Jun, Mira's engineer friend."],
                relationship_web="Trust frays under public pressure.",
            )
            from storyagents.orchestration.roles import _apply_character

            return _apply_character(state, bundle, "", {})

        if self.name == "Outline Agent":
            outline = StoryOutline(
                logline="A courier risks the city's fragile peace by uncovering a drowned memory.",
                act_structure="Chapter one opens the mystery; chapter two forces the public choice.",
                chapter_beats=[
                    ChapterBeat(
                        chapter_number=idx,
                        title=f"Beat {idx}",
                        objective=f"Objective {idx}",
                        conflict=f"Conflict {idx}",
                        ending_hook=f"Hook {idx}",
                    )
                    for idx in range(1, state["target_chapters"] + 1)
                ],
            )
            return _apply_outline(state, outline, "", {})

        if self.name == "Chapter Writer":
            chapter_number = state["current_chapter_index"]
            text = (
                f"Chapter {chapter_number}\n\n"
                f"Mira enters the scene for chapter {chapter_number} and makes a costly choice."
            )
            return _apply_writer(state, None, text, {})

        if self.name == "Continuity Reviewer":
            chapter_number = state["current_chapter_index"]
            review = ChapterReview(
                verdict=ReviewVerdict.APPROVE,
                continuity_notes=f"Chapter {chapter_number} locks in Mira's distrust.",
                revision_instructions="Ready to keep.",
                chapter_summary=f"Approved summary for chapter {chapter_number}.",
            )
            return _apply_reviewer(state, review, "", {})

        if self.name == "Showrunner":
            current = state["current_chapter_index"]
            total = state["target_chapters"]
            status = (
                ShowrunnerStatus.CONTINUE
                if current < total
                else ShowrunnerStatus.COMPLETE
            )
            decision = ShowrunnerDecision(
                status=status,
                editorial_note=f"Chapter {current} lands the intended turn cleanly.",
                next_chapter_focus=(
                    "Escalate the emotional cost of telling the truth."
                    if status == ShowrunnerStatus.CONTINUE
                    else "Close the run with the consequences now in motion."
                ),
            )
            return _apply_showrunner(
                state,
                decision,
                decision.editorial_note,
                {"max_revision_rounds": 2},
            )

        raise AssertionError(f"Unexpected role: {self.name}")


def _fake_agents(include_worldbuilding: bool = False, include_review: bool = False):
    names = ["Planner", "Outline Agent", "Chapter Writer", "Showrunner"]
    if include_worldbuilding:
        names = [
            "Planner",
            "Worldbuilder",
            "Character Designer",
            "Outline Agent",
            "Chapter Writer",
            "Showrunner",
        ]
    if include_review:
        names = [
            "Planner",
            "Worldbuilder",
            "Character Designer",
            "Outline Agent",
            "Chapter Writer",
            "Continuity Reviewer",
            "Showrunner",
        ]
    return {name: _FakeRoleAgent(name) for name in names}


def test_story_propagator_initial_state():
    state = create_initial_state("Write me a flooded-city mystery.", 2)

    assert state["target_chapters"] == 2
    assert state["target_chapter_length"] == 1500
    assert state["current_chapter_index"] == 1
    assert state["chapters"] == []
    assert state["revision_count"] == 0


def test_chapter_length_instruction_uses_language_appropriate_units():
    state = create_initial_state("Write a mystery.", 1, target_chapter_length=2000)

    english = get_chapter_length_instruction(state, {"output_language": "English"})
    chinese = get_chapter_length_instruction(state, {"output_language": "Chinese"})

    assert "between 1700 and 2300 words" in english
    assert "between 1700 and 2300 non-whitespace characters" in chinese


def test_planner_cannot_override_requested_chapter_count():
    state = create_initial_state("Write exactly two chapters.", 2)
    plan = StoryPlan(
        title="The Salt Tower",
        premise="A courier discovers a drowned memory archive.",
        genre="Speculative mystery",
        tone="Tense",
        audience="Adult readers",
        pov="Close third person",
        tense="Past tense",
        core_conflict="Truth threatens the city's fragile peace.",
        must_include=[],
        target_chapters=12,
    )

    updates = _apply_planner(state, plan, "", {})
    state.update(updates)

    assert state["target_chapters"] == 2
    assert "target_chapters" not in updates


def test_story_conditional_logic_routes_revision_loop():
    logic = StoryConditionalLogic(max_revision_rounds=2)

    assert logic.after_reviewer({"reviewer_verdict": "Revise", "revision_count": 1}) == "Chapter Writer"
    assert logic.after_reviewer({"reviewer_verdict": "Revise", "revision_count": 2}) == "Showrunner"
    assert logic.after_showrunner(
        {"showrunner_status": "Continue", "chapters": ["c1"], "target_chapters": 2}
    ) == "Chapter Writer"
    assert logic.after_showrunner(
        {"showrunner_status": "Continue", "chapters": ["c1", "c2"], "target_chapters": 2}
    ) == "__end__"


def test_story_graph_runs_two_chapters_end_to_end():
    workflow = StoryWorkflow(
        deep_model=None,
        quick_model=None,
        config={"max_revision_rounds": 2, "output_language": "English", "workflow_mode": "quick"},
        role_agents=_fake_agents(),
    )
    graph = StoryAgentsGraph(
        config={
            "max_revision_rounds": 2,
            "output_language": "English",
            "workflow_mode": "quick",
            "target_chapters": 2,
            "results_dir": ".",
            "llm_provider": "deepseek",
            "deep_think_llm": "deepseek-chat",
            "quick_think_llm": "deepseek-chat",
        },
        workflow=workflow,
    )

    result, manuscript = graph.generate_story(
        "Write a two-chapter speculative mystery about archived memories.",
        target_chapters=2,
    )

    assert result["story_title"] == "The Salt Tower"
    assert len(result["chapters"]) == 2
    assert "Chapter 1" in manuscript
    assert "Chapter 2" in manuscript
    assert result["showrunner_status"] == "Complete"


def test_story_graph_stream_emits_node_events():
    workflow = StoryWorkflow(
        deep_model=None,
        quick_model=None,
        config={"max_revision_rounds": 2, "output_language": "English", "workflow_mode": "quick"},
        role_agents=_fake_agents(),
    )
    graph = StoryAgentsGraph(
        config={
            "max_revision_rounds": 2,
            "output_language": "English",
            "workflow_mode": "quick",
            "target_chapters": 1,
            "results_dir": ".",
            "llm_provider": "deepseek",
            "deep_think_llm": "deepseek-chat",
            "quick_think_llm": "deepseek-chat",
        },
        workflow=workflow,
    )

    events = list(
        graph.generate_story_stream(
            "Write a one-chapter story.",
            target_chapters=1,
        )
    )
    node_names = [
        event["data"]["node"]
        for event in events
        if event["event"] == "node_complete"
    ]
    assert node_names == ["Planner", "Outline Agent", "Chapter Writer", "Showrunner"]
    assert events[-1]["event"] == "story_complete"
