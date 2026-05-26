from langgraph.graph import END, START, StateGraph

from storyagents.agents import (
    StoryState,
    create_character_designer,
    create_chapter_writer,
    create_continuity_reviewer,
    create_outline_agent,
    create_showrunner,
    create_story_planner,
    create_worldbuilder,
)

from .conditional_logic import StoryConditionalLogic


class StoryGraphSetup:
    def __init__(self, quick_llm, deep_llm, config: dict):
        self.quick_llm = quick_llm
        self.deep_llm = deep_llm
        self.config = config
        self.logic = StoryConditionalLogic(
            max_revision_rounds=config["max_revision_rounds"]
        )

    def setup_graph(self):
        workflow = StateGraph(StoryState)
        fast_mode = self.config.get("fast_mode", True)

        workflow.add_node("Planner", create_story_planner(self.deep_llm, self.config))
        workflow.add_node("Outline Agent", create_outline_agent(self.deep_llm, self.config))
        workflow.add_node("Chapter Writer", create_chapter_writer(self.quick_llm, self.config))
        workflow.add_node("Showrunner", create_showrunner(self.deep_llm, self.config))

        if not fast_mode:
            workflow.add_node("Worldbuilder", create_worldbuilder(self.quick_llm, self.config))
            workflow.add_node(
                "Character Designer",
                create_character_designer(self.quick_llm, self.config),
            )
            workflow.add_node(
                "Continuity Reviewer",
                create_continuity_reviewer(self.quick_llm, self.config),
            )

        workflow.add_edge(START, "Planner")
        if fast_mode:
            workflow.add_edge("Planner", "Outline Agent")
            workflow.add_edge("Outline Agent", "Chapter Writer")
            workflow.add_edge("Chapter Writer", "Showrunner")
        else:
            workflow.add_edge("Planner", "Worldbuilder")
            workflow.add_edge("Worldbuilder", "Character Designer")
            workflow.add_edge("Character Designer", "Outline Agent")
            workflow.add_edge("Outline Agent", "Chapter Writer")
            workflow.add_edge("Chapter Writer", "Continuity Reviewer")
            workflow.add_conditional_edges(
                "Continuity Reviewer",
                self.logic.after_reviewer,
                {"Chapter Writer": "Chapter Writer", "Showrunner": "Showrunner"},
            )
        workflow.add_conditional_edges(
            "Showrunner",
            self.logic.after_showrunner,
            {"Chapter Writer": "Chapter Writer", "__end__": END},
        )

        return workflow
