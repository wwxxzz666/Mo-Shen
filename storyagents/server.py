from __future__ import annotations

import json
import mimetypes
import os
import re
import time
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import unquote, urlparse

from storyagents.default_config import DEFAULT_STORY_CONFIG
from storyagents.graph.story_graph import StoryAgentsGraph


H5_DIR = Path(__file__).resolve().parent / "h5"


def build_runtime_config(
    *,
    provider: Optional[str] = None,
    deep_model: Optional[str] = None,
    quick_model: Optional[str] = None,
    output_language: Optional[str] = None,
    chapter_count: Optional[int] = None,
    results_dir: Optional[str] = None,
    deepseek_reasoning_effort: Optional[str] = None,
    deepseek_thinking_enabled: Optional[bool] = None,
) -> dict[str, Any]:
    config = DEFAULT_STORY_CONFIG.copy()
    if provider:
        config["llm_provider"] = provider
    if deep_model:
        config["deep_think_llm"] = deep_model
    if quick_model:
        config["quick_think_llm"] = quick_model
    if output_language:
        config["output_language"] = output_language
    if chapter_count is not None:
        config["target_chapters"] = chapter_count
    if results_dir:
        config["results_dir"] = results_dir
    if deepseek_reasoning_effort:
        config["deepseek_reasoning_effort"] = deepseek_reasoning_effort
    if deepseek_thinking_enabled is not None:
        config["deepseek_thinking_enabled"] = deepseek_thinking_enabled
    return config


def build_request_overrides(payload: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    field_map = {
        "provider": "llm_provider",
        "deep_model": "deep_think_llm",
        "quick_model": "quick_think_llm",
        "output_language": "output_language",
        "results_dir": "results_dir",
        "deepseek_reasoning_effort": "deepseek_reasoning_effort",
        "deepseek_thinking_enabled": "deepseek_thinking_enabled",
    }
    for incoming, target in field_map.items():
        if incoming in payload and payload[incoming] not in (None, ""):
            overrides[target] = payload[incoming]
    if "chapters" in payload and payload["chapters"] not in (None, ""):
        overrides["target_chapters"] = max(1, min(12, int(payload["chapters"])))
    return overrides


def build_story_response_payload(state: dict[str, Any], manuscript: str) -> dict[str, Any]:
    return {
        "story_title": state.get("story_title", ""),
        "story_brief": state.get("story_brief", ""),
        "story_bible": state.get("story_bible", ""),
        "character_sheets": state.get("character_sheets", ""),
        "plot_outline": state.get("plot_outline", ""),
        "current_chapter_draft": state.get("current_chapter_draft", ""),
        "chapters": state.get("chapters", []),
        "chapter_summaries": state.get("chapter_summaries", []),
        "continuity_notes": state.get("continuity_notes", ""),
        "showrunner_status": state.get("showrunner_status", ""),
        "final_manuscript": manuscript,
    }


def merge_story_payloads(
    existing_story: dict[str, Any],
    generated_story: dict[str, Any],
) -> dict[str, Any]:
    existing_chapters = list(existing_story.get("chapters", []))
    new_chapters = list(generated_story.get("chapters", []))
    merged_chapters = existing_chapters + new_chapters

    existing_summaries = list(existing_story.get("chapter_summaries", []))
    new_summaries = list(generated_story.get("chapter_summaries", []))
    merged_summaries = existing_summaries + new_summaries

    existing_notes = str(existing_story.get("continuity_notes", "") or "").strip()
    new_notes = str(generated_story.get("continuity_notes", "") or "").strip()
    if existing_notes and new_notes and existing_notes != new_notes:
        merged_notes = f"{existing_notes}\n\n{new_notes}"
    else:
        merged_notes = new_notes or existing_notes

    final_manuscript = "\n\n".join(
        f"# Chapter {idx}\n\n{chapter}"
        for idx, chapter in enumerate(merged_chapters, start=1)
    )

    return {
        "story_title": generated_story.get("story_title") or existing_story.get("story_title", ""),
        "story_brief": generated_story.get("story_brief") or existing_story.get("story_brief", ""),
        "story_bible": generated_story.get("story_bible") or existing_story.get("story_bible", ""),
        "character_sheets": generated_story.get("character_sheets") or existing_story.get("character_sheets", ""),
        "plot_outline": generated_story.get("plot_outline") or existing_story.get("plot_outline", ""),
        "current_chapter_draft": generated_story.get("current_chapter_draft") or existing_story.get("current_chapter_draft", ""),
        "chapters": merged_chapters,
        "chapter_summaries": merged_summaries,
        "continuity_notes": merged_notes,
        "showrunner_status": generated_story.get("showrunner_status") or existing_story.get("showrunner_status", ""),
        "final_manuscript": final_manuscript,
    }


class StoryAgentsRequestHandler(BaseHTTPRequestHandler):
    server_version = "StoryAgentsHTTP/0.1"

    def __init__(
        self,
        *args,
        graph_factory: Callable[[dict[str, Any]], StoryAgentsGraph],
        h5_dir: Path,
        results_dir: Path,
        **kwargs,
    ):
        self.graph_factory = graph_factory
        self.h5_dir = h5_dir
        self.results_dir = results_dir
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers(content_type="application/json")
        self.send_header("Access-Control-Request-Method", "GET, POST, PATCH, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return

        if parsed.path == "/api/storyagents/stories":
            self._list_stories()
            return

        if parsed.path.startswith("/api/storyagents/stories/"):
            story_id = parsed.path.split("/")[-1]
            self._serve_story(story_id)
            return

        if parsed.path in ("/", "/h5", "/h5/"):
            self._serve_file(self.h5_dir / "index.html")
            return

        if parsed.path.startswith("/h5/"):
            relative = parsed.path.removeprefix("/h5/").strip("/")
            target = (self.h5_dir / relative).resolve()
            if not str(target).startswith(str(self.h5_dir.resolve())):
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            self._serve_file(target)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        prefix = "/api/storyagents/stories/"
        if parsed.path.startswith(prefix):
            story_id = parsed.path.removeprefix(prefix)
            self._delete_story(story_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_PATCH(self):
        parsed = urlparse(self.path)
        prefix = "/api/storyagents/stories/"
        if parsed.path.startswith(prefix):
            story_id = parsed.path.removeprefix(prefix)
            self._update_story(story_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/storyagents/draft":
            self._handle_draft()
            return

        if parsed.path == "/api/storyagents/draft/stream":
            self._handle_draft_stream()
            return

        if parsed.path == "/api/storyagents/edit":
            self._handle_edit()
            return

        if parsed.path == "/api/storyagents/continue":
            self._handle_continue()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _handle_draft(self):
        try:
            payload = self._read_json_body()
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                self._send_json(
                    {"error": "Field 'prompt' is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            chapter_count = max(
                1,
                min(12, int(payload.get("chapters") or DEFAULT_STORY_CONFIG["target_chapters"])),
            )

            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)
            state, manuscript = graph.generate_story(prompt, target_chapters=chapter_count)
            response = build_story_response_payload(state, manuscript)
            story_id = self._save_story(payload, response)
            response["story_id"] = story_id
            self._send_json(response)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json(
                {"error": str(exc), "type": exc.__class__.__name__},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _handle_draft_stream(self):
        try:
            payload = self._read_json_body()
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                self._send_json(
                    {"error": "Field 'prompt' is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            chapter_count = max(
                1,
                min(12, int(payload.get("chapters") or DEFAULT_STORY_CONFIG["target_chapters"])),
            )

            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)

            # Send SSE headers
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

            # Stream events
            last_state: dict[str, Any] = {}
            for event in graph.generate_story_stream(prompt, target_chapters=chapter_count):
                if not self._write_sse_event(event):
                    break

                # Track state for saving
                if event["event"] == "node_complete":
                    last_state.update(event["data"])

            # Save final story
            if last_state.get("final_manuscript"):
                response = build_story_response_payload(
                    last_state,
                    last_state.get("final_manuscript", ""),
                )
                story_id = self._save_story(payload, response)
                saved_event = {
                    "event": "story_saved",
                    "data": {"story_id": story_id},
                }
                self._write_sse_event(saved_event)

        except ValueError as exc:
            self._write_sse_event({"error": str(exc)})
        except Exception as exc:
            self._write_sse_event(
                {"error": str(exc), "type": exc.__class__.__name__},
            )

    def _handle_edit(self):
        try:
            from storyagents.agents.editing.editor import create_editor
            from storyagents.llm_clients import create_llm_client

            payload = self._read_json_body()
            text = str(payload.get("text", "")).strip()
            action = str(payload.get("action", "rewrite")).strip()
            context = str(payload.get("context", "")).strip()
            instruction = str(payload.get("instruction", "")).strip()

            if not text:
                self._send_json(
                    {"error": "Field 'text' is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            if action not in ("rewrite", "expand", "compress", "polish"):
                self._send_json(
                    {"error": "Invalid action. Must be one of: rewrite, expand, compress, polish"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            # Create LLM client for editing
            provider = payload.get("provider", DEFAULT_STORY_CONFIG["llm_provider"])
            model = payload.get("quick_model", DEFAULT_STORY_CONFIG["quick_think_llm"])

            llm_client = create_llm_client(
                provider=provider,
                model=model,
                base_url=payload.get("backend_url"),
            )
            llm = llm_client.get_llm()

            # Create editor and run edit
            editor = create_editor(llm)
            result = editor(text, action=action, context=context, instruction=instruction)

            self._send_json(result)
        except Exception as exc:
            self._send_json(
                {"error": str(exc), "type": exc.__class__.__name__},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _handle_continue(self):
        try:
            payload = self._read_json_body()
            story_id = str(payload.get("story_id", "")).strip()

            if not story_id:
                self._send_json(
                    {"error": "Field 'story_id' is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            # Load existing story
            safe_id = re.sub(r'[\\/]', '', unquote(story_id))
            path = self.results_dir / f"{safe_id}.json"

            if not path.exists():
                self._send_json(
                    {"error": "Story not found."},
                    status=HTTPStatus.NOT_FOUND,
                )
                return

            existing_story = self._read_story_file(path)

            # Build continuation prompt
            existing_chapters = existing_story.get("chapters", [])
            story_brief = existing_story.get("story_brief", "")
            plot_outline = existing_story.get("plot_outline", "")
            story_title = existing_story.get("story_title", "")

            continue_chapters = max(
                1,
                min(12, int(payload.get("continue_chapters", 3))),
            )

            # Create a prompt that includes context from existing story
            context_prompt = f"""继续创作故事《{story_title}》。

故事简介：
{story_brief}

已有大纲：
{plot_outline}

已完成章节（共 {len(existing_chapters)} 章）：
{chr(10).join(f'--- 第 {i+1} 章 ---{chr(10)}{ch[:500]}...' for i, ch in enumerate(existing_chapters))}

请继续创作后续 {continue_chapters} 章，保持故事的连贯性和风格一致性。"""

            # Use streaming for continuation
            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)

            # Send SSE headers
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

            # Stream events
            last_state: dict[str, Any] = {}
            for event in graph.generate_story_stream(context_prompt, target_chapters=continue_chapters):
                if event["event"] == "node_complete":
                    last_state.update(event["data"])
                    merged_event_data = dict(event["data"])
                    merged_event_data["story_id"] = safe_id
                    merged_event_data["chapters"] = existing_chapters + list(
                        event["data"].get("chapters", [])
                    )
                    if merged_event_data.get("final_manuscript"):
                        merged_event_data["final_manuscript"] = "\n\n".join(
                            f"# Chapter {idx}\n\n{chapter}"
                            for idx, chapter in enumerate(merged_event_data["chapters"], start=1)
                        )
                    event = {"event": "node_complete", "data": merged_event_data}
                if not self._write_sse_event(event):
                    break

            if last_state.get("final_manuscript"):
                generated_story = build_story_response_payload(
                    last_state,
                    last_state.get("final_manuscript", ""),
                )
                merged_story = merge_story_payloads(existing_story, generated_story)
                self._write_story_file(path, self._apply_story_metadata(existing_story, merged_story))
                saved_event = {
                    "event": "story_saved",
                    "data": {"story_id": safe_id},
                }
                self._write_sse_event(saved_event)

        except Exception as exc:
            self._write_sse_event(
                {"error": str(exc), "type": exc.__class__.__name__},
            )

    def _list_stories(self):
        stories = []
        if self.results_dir.exists():
            for f in sorted(self.results_dir.glob("*.json"), reverse=True):
                try:
                    data = self._read_story_file(f)
                    stories.append({
                        "id": f.stem,
                        "title": data.get("story_title", ""),
                        "prompt": data.get("_prompt", ""),
                        "genre": data.get("_genre", ""),
                        "chapters": len(data.get("chapters", [])),
                        "created_at": data.get("_created_at", ""),
                        "updated_at": data.get("_updated_at", ""),
                    })
                except Exception:
                    continue
        self._send_json(stories)

    def _serve_story(self, story_id):
        path = self._story_path(story_id)
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Story not found")
            return
        self._serve_file(path)

    def _delete_story(self, story_id):
        path = self._story_path(story_id)
        if not path.exists():
            self._send_json({"error": "Story not found"}, status=HTTPStatus.NOT_FOUND)
            return
        path.unlink()
        self._send_json({"deleted": path.stem})

    def _update_story(self, story_id):
        path = self._story_path(story_id)
        if not path.exists():
            self._send_json({"error": "Story not found"}, status=HTTPStatus.NOT_FOUND)
            return

        payload = self._read_json_body()
        existing_story = self._read_story_file(path)
        allowed_fields = {
            "story_title",
            "story_brief",
            "story_bible",
            "character_sheets",
            "plot_outline",
            "current_chapter_draft",
            "chapters",
            "chapter_summaries",
            "continuity_notes",
            "showrunner_status",
            "final_manuscript",
        }
        updates = {key: payload[key] for key in allowed_fields if key in payload}
        if not updates:
            self._send_json({"error": "No updatable fields provided."}, status=HTTPStatus.BAD_REQUEST)
            return

        updated_story = existing_story.copy()
        updated_story.update(updates)
        updated_story = self._apply_story_metadata(existing_story, updated_story)
        self._write_story_file(path, updated_story)

        response = updated_story.copy()
        response["story_id"] = path.stem
        self._send_json(response)

    def _save_story(self, payload, story_data):
        os.makedirs(self.results_dir, exist_ok=True)
        title = story_data.get("story_title", "未命名").strip()
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:40]
        ts = int(time.time())
        story_id = f"{ts}_{safe_title}" if safe_title else str(ts)
        story_data = self._apply_story_metadata(
            {},
            story_data,
            payload=payload,
            timestamp=ts,
        )
        self._write_story_file(self.results_dir / f"{story_id}.json", story_data)
        return story_id

    def _story_path(self, story_id: str) -> Path:
        safe_id = re.sub(r'[\\/]', '', unquote(story_id))
        return self.results_dir / f"{safe_id}.json"

    def _read_story_file(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_story_file(self, path: Path, payload: dict[str, Any]):
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _apply_story_metadata(
        self,
        existing_story: dict[str, Any],
        story_data: dict[str, Any],
        *,
        payload: Optional[dict[str, Any]] = None,
        timestamp: Optional[int] = None,
    ) -> dict[str, Any]:
        ts = timestamp or int(time.time())
        result = story_data.copy()
        result["_prompt"] = (
            payload.get("prompt", existing_story.get("_prompt", ""))
            if payload is not None
            else existing_story.get("_prompt", "")
        )
        result["_genre"] = (
            payload.get("genre", existing_story.get("_genre", ""))
            if payload is not None
            else existing_story.get("_genre", "")
        )
        result["_created_at"] = existing_story.get(
            "_created_at",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)),
        )
        result["_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        return result

    def log_message(self, format: str, *args):
        return

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_common_headers(self, *, content_type: str):
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers(content_type="application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_sse_event(self, payload: dict[str, Any]) -> bool:
        try:
            event_data = json.dumps(payload, ensure_ascii=False)
            self.wfile.write(f"data: {event_data}\n\n".encode("utf-8"))
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return False

    def _serve_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File Not Found")
            return
        content = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(str(path))
        self.send_response(HTTPStatus.OK)
        self._send_common_headers(content_type=f"{mime_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    graph_factory: Optional[Callable[[dict[str, Any]], StoryAgentsGraph]] = None,
    h5_dir: Optional[Path] = None,
) -> ThreadingHTTPServer:
    if graph_factory is None:
        graph_factory = lambda overrides: StoryAgentsGraph(
            config=build_runtime_config(
                provider=overrides.get("llm_provider"),
                deep_model=overrides.get("deep_think_llm"),
                quick_model=overrides.get("quick_think_llm"),
                output_language=overrides.get("output_language"),
                chapter_count=overrides.get("target_chapters"),
                results_dir=overrides.get("results_dir"),
                deepseek_reasoning_effort=overrides.get("deepseek_reasoning_effort"),
                deepseek_thinking_enabled=overrides.get("deepseek_thinking_enabled"),
            )
        )
    handler = partial(
        StoryAgentsRequestHandler,
        graph_factory=graph_factory,
        h5_dir=(h5_dir or H5_DIR),
        results_dir=Path(DEFAULT_STORY_CONFIG["results_dir"]),
    )
    return ThreadingHTTPServer((host, port), handler)


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    graph_factory: Optional[Callable[[dict[str, Any]], StoryAgentsGraph]] = None,
):
    server = create_server(host, port, graph_factory=graph_factory)
    print(f"StoryAgents server running at http://{host}:{port}")
    print(f"H5 UI: http://{host}:{port}/h5/")
    print(f"Draft API: http://{host}:{port}/api/storyagents/draft")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    serve()


if __name__ == "__main__":
    main()
