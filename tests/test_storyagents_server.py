import json
import threading
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pytest

import storyagents.server as server_module
from storyagents.server import (
    H5_DIR,
    build_request_overrides,
    build_runtime_config,
    build_story_response_payload,
    create_server,
    enrich_generation_prompt,
    validate_continuation_request,
    validate_workshop_request,
)


class _FakeGraph:
    def __init__(self, config):
        self.config = config

    def generate_story(self, prompt, target_chapters=1):
        manuscript = "# Chapter 1\n\nA storm letter arrives."
        state = {
            "story_title": "A Letter from Tomorrow",
            "story_brief": f"Brief for: {prompt}",
            "story_bible": "World bible",
            "character_sheets": "Character sheets",
            "plot_outline": "Outline",
            "current_chapter_draft": "A storm letter arrives.",
            "chapters": ["A storm letter arrives."],
            "chapter_summaries": ["The letter appears and changes everything."],
            "continuity_notes": "Remember the wet envelope.",
            "showrunner_status": "Complete",
            "target_chapter_length": self.config.get("target_chapter_length", 1500),
        }
        return state, manuscript

    def generate_story_stream(self, prompt, target_chapters=1):
        chapters = [
            f"Continuation chapter {idx}"
            for idx in range(1, target_chapters + 1)
        ]
        final_manuscript = "\n\n".join(
            f"# Chapter {idx}\n\n{chapter}"
            for idx, chapter in enumerate(chapters, start=1)
        )
        yield {
            "event": "node_complete",
            "data": {
                "node": "Chapter Writer",
                "story_title": "A Letter from Tomorrow",
                "story_brief": "Brief for continuation",
                "story_bible": "World bible",
                "character_sheets": "Character sheets",
                "plot_outline": "Outline",
                "current_chapter_index": target_chapters,
                "current_chapter_draft": chapters[-1],
                "chapters": chapters,
                "chapter_summaries": [f"Summary {idx}" for idx in range(1, target_chapters + 1)],
                "continuity_notes": "Keep the wet envelope in play.",
                "showrunner_status": "Complete",
                "final_manuscript": final_manuscript,
                "target_chapters": target_chapters,
                "target_chapter_length": self.config.get("target_chapter_length", 1500),
            },
        }
        yield {
            "event": "story_complete",
            "data": {"target_chapters": target_chapters},
        }


class _OutlineGraph(_FakeGraph):
    def generate_story_stream(self, prompt, target_chapters=1):
        yield {
            "event": "node_complete",
            "data": {
                "node": "Outline Agent",
                "plot_outline": "Chapter 1: The letter arrives.",
                "target_chapters": target_chapters,
            },
        }
        yield from super().generate_story_stream(prompt, target_chapters)


def test_build_story_response_payload():
    payload = build_story_response_payload(
        {
            "story_title": "T",
            "story_brief": "B",
            "story_bible": "W",
            "character_sheets": "C",
            "plot_outline": "O",
            "current_chapter_draft": "D",
            "chapters": ["x"],
            "chapter_summaries": ["s"],
            "continuity_notes": "n",
            "showrunner_status": "Complete",
            "target_chapter_length": 1500,
        },
        "M",
    )

    assert payload["story_title"] == "T"
    assert payload["final_manuscript"] == "M"
    assert payload["chapters"] == ["x"]
    assert payload["target_chapter_length"] == 1500


def test_mode_helpers():
    overrides = build_request_overrides(
        {"mode": "standard", "chapters": 5, "chapter_length": 2200}
    )
    assert overrides["workflow_mode"] == "standard"
    assert overrides["target_chapters"] == 5
    assert overrides["target_chapter_length"] == 2200
    assert (
        build_request_overrides(
            {"mode": "deep", "chapter_length": 99999}
        )["target_chapter_length"]
        == 5000
    )
    assert build_request_overrides(
        {"mode": "quick", "chapter_length": 5000}
    )["target_chapter_length"] == 5000
    assert overrides["fast_mode"] is False

    config = build_runtime_config(workflow_mode="deep", target_chapter_length=2400)
    assert config["workflow_mode"] == "deep"
    assert config["fast_mode"] is False
    assert config["max_revision_rounds"] >= 3
    assert config["target_chapter_length"] == 2400


def test_author_style_is_validated_and_reaches_agent_config():
    overrides = build_request_overrides({"author_style": "yu_hua"})
    config = build_runtime_config(author_style=overrides["author_style"])
    prompt = enrich_generation_prompt(
        "Write a short story.",
        {"author_style": "yu_hua", "genre": "现实文学"},
    )

    assert overrides["author_style"] == "yu_hua"
    assert config["author_style_label"] == "余华"
    assert "plainspoken narration" in config["author_style_guidance"]
    assert "Reference author: 余华" in prompt
    assert build_request_overrides({"author_style": "unknown"})["author_style"] == ""


def test_workshop_limits_allow_unbounded_deep_chapters_but_enforce_other_modes():
    assert validate_workshop_request(
        {"mode": "quick", "chapters": 25, "chapter_length": 5000}
    ) == ("quick", 25, 5000)
    assert validate_workshop_request(
        {"mode": "standard", "chapters": 30, "chapter_length": 5000}
    ) == ("standard", 30, 5000)
    assert validate_workshop_request(
        {"mode": "deep", "chapters": 27, "chapter_length": 5000}
    ) == ("deep", 27, 5000)

    assert validate_workshop_request(
        {"mode": "standard", "chapters": 1, "chapter_length": 5100}
    ) == ("standard", 1, 5000)


def test_background_task_can_pause_resume_and_complete(tmp_path, monkeypatch):
    monkeypatch.setitem(server_module.DEFAULT_STORY_CONFIG, "results_dir", str(tmp_path))
    server = create_server(
        "127.0.0.1",
        0,
        graph_factory=lambda config: _FakeGraph(config),
        h5_dir=H5_DIR,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    try:
        create_request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/tasks",
            data=json.dumps(
                {
                    "prompt": "Write a suspense story.",
                    "chapters": 2,
                    "chapter_length": 1500,
                    "mode": "standard",
                    "confirm_outline": False,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(create_request, timeout=5) as response:
            created = json.loads(response.read().decode("utf-8"))
        task_id = created["task_id"]

        deadline = time.time() + 5
        snapshot = created
        while time.time() < deadline and snapshot["status"] not in {"completed", "failed"}:
            with urlopen(
                f"http://127.0.0.1:{port}/api/storyagents/tasks/{task_id}?after=0",
                timeout=5,
            ) as response:
                snapshot = json.loads(response.read().decode("utf-8"))
            time.sleep(0.05)

        assert snapshot["status"] == "completed"
        assert snapshot["story_id"]
        assert any(event.get("event") == "node_complete" for event in snapshot["events"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_background_task_waits_for_outline_approval(tmp_path, monkeypatch):
    monkeypatch.setitem(server_module.DEFAULT_STORY_CONFIG, "results_dir", str(tmp_path))
    server = create_server(
        "127.0.0.1",
        0,
        graph_factory=lambda config: _OutlineGraph(config),
        h5_dir=H5_DIR,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/tasks",
            data=json.dumps({
                "prompt": "Write a suspense story.",
                "chapters": 1,
                "mode": "standard",
                "confirm_outline": True,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            task_id = json.loads(response.read().decode("utf-8"))["task_id"]

        deadline = time.time() + 3
        snapshot = {}
        while time.time() < deadline:
            with urlopen(f"http://127.0.0.1:{port}/api/storyagents/tasks/{task_id}", timeout=5) as response:
                snapshot = json.loads(response.read().decode("utf-8"))
            if snapshot["status"] == "awaiting_outline":
                break
            time.sleep(0.03)
        assert snapshot["status"] == "awaiting_outline"

        approve = Request(
            f"http://127.0.0.1:{port}/api/storyagents/tasks/{task_id}/approve-outline",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(approve, timeout=5) as response:
            approved = json.loads(response.read().decode("utf-8"))
        assert approved["status"] == "running"

        deadline = time.time() + 3
        while time.time() < deadline:
            with urlopen(f"http://127.0.0.1:{port}/api/storyagents/tasks/{task_id}", timeout=5) as response:
                snapshot = json.loads(response.read().decode("utf-8"))
            if snapshot["status"] == "completed":
                break
            time.sleep(0.03)
        assert snapshot["status"] == "completed"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_continuation_limits_are_mode_specific():
    assert validate_continuation_request(
        {"mode": "quick", "continue_chapters": 3}, used_continuations=1
    ) == ("quick", 3)
    assert validate_continuation_request(
        {"mode": "deep", "continue_chapters": 29}, used_continuations=99
    ) == ("deep", 29)

    with pytest.raises(ValueError, match="故事工坊最多续写 2 次"):
        validate_continuation_request(
            {"mode": "standard", "continue_chapters": 1}, used_continuations=2
        )
    with pytest.raises(ValueError, match="灵感工坊每次续写最多 3 章"):
        validate_continuation_request(
            {"mode": "quick", "continue_chapters": 4}, used_continuations=0
        )


def test_storyagents_server_health_and_draft_endpoint():
    server = create_server(
        "127.0.0.1",
        0,
        graph_factory=lambda config: _FakeGraph(config),
        h5_dir=H5_DIR,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        with urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        assert health["status"] == "ok"

        request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/draft",
            data=json.dumps(
                {
                    "prompt": "Write a suspense story.",
                    "chapters": 1,
                    "mode": "standard",
                    "output_language": "English",
                    "chapter_length": 1800,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            cors = response.headers.get("Access-Control-Allow-Origin")

        assert payload["story_title"] == "A Letter from Tomorrow"
        assert payload["showrunner_status"] == "Complete"
        assert payload["chapters"] == ["A storm letter arrives."]
        assert payload["workflow_mode"] == "standard"
        assert payload["target_chapter_length"] == 1800
        assert cors == "*"

        with urlopen(f"http://127.0.0.1:{port}/h5/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "墨神" in html
        assert html.index("/h5/sse.js") < html.index("/h5/app.js")
        assert "/h5/app.js" in html
        assert 'name="chapter_length"' in html
        assert 'id="confirm-preview-button"' in html
        assert 'id="outline-gate"' in html
        assert 'id="workflow-map-panel"' in html

        with urlopen(f"http://127.0.0.1:{port}/h5/sse.js", timeout=5) as response:
            sse_helper = response.read().decode("utf-8")
        assert "parseEventLine" in sse_helper
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_story_updates_and_continuation_persist(tmp_path, monkeypatch):
    monkeypatch.setitem(server_module.DEFAULT_STORY_CONFIG, "results_dir", str(tmp_path))
    server = create_server(
        "127.0.0.1",
        0,
        graph_factory=lambda config: _FakeGraph(config),
        h5_dir=H5_DIR,
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    try:
        draft_request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/draft",
            data=json.dumps(
                {
                    "prompt": "Write a suspense story.",
                    "chapters": 1,
                    "chapter_length": 2100,
                    "mode": "deep",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(draft_request, timeout=5) as response:
            draft_payload = json.loads(response.read().decode("utf-8"))

        story_id = draft_payload["story_id"]
        encoded_story_id = quote(story_id, safe="")
        update_request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/stories/{encoded_story_id}",
            data=json.dumps(
                {
                    "current_chapter_draft": "An edited storm letter arrives.",
                    "chapters": ["An edited storm letter arrives."],
                    "final_manuscript": "# Chapter 1\n\nAn edited storm letter arrives.",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        with urlopen(update_request, timeout=5) as response:
            updated_payload = json.loads(response.read().decode("utf-8"))

        assert updated_payload["story_id"] == story_id
        assert updated_payload["current_chapter_draft"] == "An edited storm letter arrives."

        continue_request = Request(
            f"http://127.0.0.1:{port}/api/storyagents/continue",
            data=json.dumps({"story_id": story_id, "continue_chapters": 1}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        stream_lines = []
        with urlopen(continue_request, timeout=5) as response:
            while True:
                line = response.readline().decode("utf-8")
                if not line:
                    break
                stream_lines.append(line)
                if '"event": "story_saved"' in line:
                    break
        stream_text = "".join(stream_lines)

        assert '"event": "node_complete"' in stream_text
        assert '"event": "story_saved"' in stream_text

        with urlopen(
            f"http://127.0.0.1:{port}/api/storyagents/stories/{encoded_story_id}",
            timeout=5,
        ) as response:
            final_payload = json.loads(response.read().decode("utf-8"))

        assert final_payload["chapters"] == [
            "An edited storm letter arrives.",
            "Continuation chapter 1",
        ]
        assert "An edited storm letter arrives." in final_payload["final_manuscript"]
        assert "Continuation chapter 1" in final_payload["final_manuscript"]
        assert final_payload["_updated_at"]
        assert final_payload["_workflow_mode"] == "deep"
        assert final_payload["target_chapter_length"] == 2100
        assert final_payload["_target_chapter_length"] == 2100

        with urlopen(f"http://127.0.0.1:{port}/api/storyagents/stories", timeout=5) as response:
            stories = json.loads(response.read().decode("utf-8"))

        assert stories[0]["mode"] == "deep"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
