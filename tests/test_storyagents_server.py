import json
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

from storyagents.server import (
    H5_DIR,
    build_story_response_payload,
    create_server,
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
        }
        return state, manuscript


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
        },
        "M",
    )

    assert payload["story_title"] == "T"
    assert payload["final_manuscript"] == "M"
    assert payload["chapters"] == ["x"]


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
                    "output_language": "English",
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
        assert cors == "*"

        with urlopen(f"http://127.0.0.1:{port}/h5/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "墨神" in html
        assert "/h5/app.js" in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
