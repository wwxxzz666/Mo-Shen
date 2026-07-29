"""Local text editor powered by an AgentScope Agent."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from storyagents.schemas import EditResult

from .prompts import ROLE_SYSTEM_PROMPTS, editor_prompt


VALID_EDIT_ACTIONS = ("rewrite", "expand", "compress", "polish")


class StoryEditor:
    """AgentScope-based editor for rewrite / expand / compress / polish."""

    def __init__(self, model: Any):
        self.model = model

    def _build_agent(self):
        from agentscope.agent import Agent, InjectionConfig, ReActConfig

        return Agent(
            name="Editor",
            system_prompt=ROLE_SYSTEM_PROMPTS["Editor"],
            model=self.model,
            react_config=ReActConfig(max_iters=4),
            injection_config=InjectionConfig(inject_runtime_state=False),
        )

    async def edit_async(
        self,
        text: str,
        action: str = "rewrite",
        context: str = "",
        instruction: str = "",
    ) -> Dict[str, Any]:
        if action not in VALID_EDIT_ACTIONS:
            raise ValueError(
                "Invalid action. Must be one of: "
                + ", ".join(VALID_EDIT_ACTIONS)
            )

        from agentscope.message import UserMsg

        agent = self._build_agent()
        prompt = editor_prompt(
            text,
            action=action,
            context=context,
            instruction=instruction,
        )
        user_msg = UserMsg(name="user", content=prompt)

        try:
            reply = await agent.reply(user_msg, structured_schema=EditResult)
            raw = reply.structured_output
            if raw:
                result = EditResult.model_validate(raw)
                return {
                    "edited_text": result.edited_text,
                    "changes_summary": result.changes_summary,
                }
            content = reply.get_text_content() or ""
            return {
                "edited_text": content,
                "changes_summary": f"已完成{action}操作。",
            }
        except Exception:
            fallback = self._build_agent()
            reply = await fallback.reply(user_msg)
            content = reply.get_text_content() or ""
            return {
                "edited_text": content,
                "changes_summary": f"已完成{action}操作。",
            }

    def edit(
        self,
        text: str,
        action: str = "rewrite",
        context: str = "",
        instruction: str = "",
    ) -> Dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.edit_async(
                    text,
                    action=action,
                    context=context,
                    instruction=instruction,
                )
            )

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.edit_async(
                    text,
                    action=action,
                    context=context,
                    instruction=instruction,
                )
            )
        finally:
            loop.close()


def create_editor(model: Any):
    """Factory matching the historical create_editor(llm) call shape."""
    editor = StoryEditor(model)

    def edit_text(
        text: str,
        action: str = "rewrite",
        context: str = "",
        instruction: str = "",
    ) -> Dict[str, Any]:
        return editor.edit(
            text,
            action=action,
            context=context,
            instruction=instruction,
        )

    return edit_text
