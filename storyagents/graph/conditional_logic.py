from storyagents.agents.utils.story_states import StoryState


class StoryConditionalLogic:
    def __init__(self, max_revision_rounds: int = 2):
        self.max_revision_rounds = max_revision_rounds

    def after_reviewer(self, state: StoryState) -> str:
        if (
            state["reviewer_verdict"] == "Revise"
            and state["revision_count"] < self.max_revision_rounds
        ):
            return "Chapter Writer"
        return "Showrunner"

    def after_showrunner(self, state: StoryState) -> str:
        if (
            state["showrunner_status"] == "Continue"
            and len(state.get("chapters", [])) < state["target_chapters"]
        ):
            return "Chapter Writer"
        return "__end__"
