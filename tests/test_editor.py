from storyagents.orchestration.editor import VALID_EDIT_ACTIONS, create_editor
from storyagents.orchestration.prompts import editor_prompt
from storyagents.schemas import EditResult


class _FakeEditorModel:
    """Stand-in model object; the real Agent is patched in unit tests."""


def test_editor_prompt_includes_text_and_instruction():
    prompt = editor_prompt(
        "窗外下着雨。",
        action="polish",
        context="第一章开头",
        instruction="更文学一点",
    )
    assert "窗外下着雨。" in prompt
    assert "第一章开头" in prompt
    assert "更文学一点" in prompt
    assert "润色" in prompt


def test_valid_edit_actions():
    assert set(VALID_EDIT_ACTIONS) == {"rewrite", "expand", "compress", "polish"}


def test_create_editor_callable_shape(monkeypatch):
    """create_editor returns a sync callable matching the historical API."""
    calls = {}

    async def fake_edit_async(self, text, action="rewrite", context="", instruction=""):
        calls["args"] = {
            "text": text,
            "action": action,
            "context": context,
            "instruction": instruction,
        }
        return {
            "edited_text": f"EDITED:{text}",
            "changes_summary": f"did {action}",
        }

    monkeypatch.setattr(
        "storyagents.orchestration.editor.StoryEditor.edit_async",
        fake_edit_async,
    )

    editor = create_editor(_FakeEditorModel())
    result = editor(
        "原文",
        action="compress",
        context="ctx",
        instruction="keep plot",
    )

    assert result["edited_text"] == "EDITED:原文"
    assert result["changes_summary"] == "did compress"
    assert calls["args"]["action"] == "compress"
    assert EditResult(
        edited_text=result["edited_text"],
        changes_summary=result["changes_summary"],
    )
