from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import re
import threading
import time
import uuid
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import unquote, urlparse

from storyagents.default_config import (
    DEFAULT_STORY_CONFIG,
    normalize_target_chapter_length,
    normalize_workflow_mode,
)
from storyagents.orchestration.story_graph import StoryAgentsGraph
from storyagents.orchestration.formatting import render_manuscript, normalize_chapter_text


H5_DIR = Path(__file__).resolve().parent / "h5"


WORKSHOP_LIMITS = {
    "quick": {
        "label": "灵感工坊",
        "max_chapters": None,
        "max_chapter_length": 5000,
        "max_continue_chapters": 3,
        "max_continuations": 2,
    },
    "standard": {
        "label": "故事工坊",
        "max_chapters": None,
        "max_chapter_length": 5000,
        "max_continue_chapters": 5,
        "max_continuations": 2,
    },
    "deep": {
        "label": "长篇工坊",
        "max_chapters": None,
        "max_chapter_length": 5000,
        "max_continue_chapters": None,
        "max_continuations": None,
    },
}


class StoryTask:
    """In-process generation task that survives client disconnects."""

    def __init__(self, task_id: str, payload: dict[str, Any]):
        self.task_id = task_id
        self.payload = payload
        self.status = "queued"
        self.events: list[dict[str, Any]] = []
        self.last_state: dict[str, Any] = {}
        self.story_id: Optional[str] = None
        self.error = ""
        self.pause_requested = False
        self.awaiting_outline = False
        self.created_at = time.time()
        self.updated_at = self.created_at
        self._condition = threading.Condition()

    def append_event(self, event: dict[str, Any]):
        with self._condition:
            self.events.append(event)
            if event.get("event") == "node_complete":
                self.last_state.update(event.get("data") or {})
            self.updated_at = time.time()

    def wait_if_paused(self):
        with self._condition:
            while self.pause_requested or self.awaiting_outline:
                self._condition.wait(timeout=1)

    def pause(self):
        with self._condition:
            if self.status in {"queued", "running"}:
                self.pause_requested = True
                self.status = "paused"
                self.updated_at = time.time()

    def resume(self):
        with self._condition:
            if self.status in {"paused", "awaiting_outline"}:
                self.pause_requested = False
                self.awaiting_outline = False
                self.status = "running"
                self.updated_at = time.time()
                self._condition.notify_all()

    def snapshot(self, after: int = 0) -> dict[str, Any]:
        with self._condition:
            safe_after = max(0, min(int(after), len(self.events)))
            return {
                "task_id": self.task_id,
                "status": self.status,
                "events": self.events[safe_after:],
                "next_cursor": len(self.events),
                "story_id": self.story_id,
                "error": self.error,
                "workflow_mode": normalize_workflow_mode(self.payload.get("mode")),
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }


class StoryTaskRegistry:
    """Thread-safe registry shared by all request handlers in one server."""

    def __init__(self):
        self._tasks: dict[str, StoryTask] = {}
        self._lock = threading.Lock()

    def create(self, payload: dict[str, Any]) -> StoryTask:
        task = StoryTask(uuid.uuid4().hex, payload)
        with self._lock:
            self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> Optional[StoryTask]:
        with self._lock:
            return self._tasks.get(task_id)


AUTHOR_STYLE_PROFILES = {
    "jia_pingwa": {
        "label": "贾平凹",
        "guidance": "favor grounded local detail, layered human relationships, and a patient, quietly pressurized narrative pace",
    },
    "wang_xiaobo": {
        "label": "王小波",
        "guidance": "favor lucid wit, restrained irony, intellectual play, and a clear-eyed response to absurd situations",
    },
    "wang_shuo": {
        "label": "王朔",
        "guidance": "favor lively urban dialogue, sharp social observation, irreverent humor, and characters who reveal themselves through verbal sparring",
    },
    "lv_xin": {
        "label": "吕新",
        "guidance": "favor restraint, distance, suggestive fragments, and emotional weight carried by what remains unsaid",
    },
    "tian_er": {
        "label": "田耳",
        "guidance": "favor everyday texture, a quietly uncanny undercurrent, vivid secondary characters, and tension emerging from ordinary life",
    },
    "su_tong": {
        "label": "苏童",
        "guidance": "favor sensory imagery, family and social undercurrents, elegant darkness, and a durable sense of fate",
    },
    "yu_hua": {
        "label": "余华",
        "guidance": "favor plainspoken narration, concrete events, emotional restraint, and humane attention to absurd or difficult circumstances",
    },
}


def normalize_author_style(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in AUTHOR_STYLE_PROFILES else ""


def get_author_style_label(value: Any) -> str:
    key = normalize_author_style(value)
    return AUTHOR_STYLE_PROFILES.get(key, {}).get("label", "")


def get_author_style_guidance(value: Any) -> str:
    key = normalize_author_style(value)
    return AUTHOR_STYLE_PROFILES.get(key, {}).get("guidance", "")


def enrich_generation_prompt(prompt: str, payload: dict[str, Any]) -> str:
    """Carry form choices into every Agent without changing the public API shape."""
    constraints = []
    for label, key in (("Genre", "genre"), ("Tone", "tone"), ("Audience", "audience")):
        value = str(payload.get(key, "") or "").strip()
        if value:
            constraints.append(f"{label}: {value}")

    style_key = normalize_author_style(payload.get("author_style"))
    if style_key:
        profile = AUTHOR_STYLE_PROFILES[style_key]
        constraints.append(
            "Reference author: "
            f"{profile['label']}. Use only these high-level narrative qualities: {profile['guidance']}. "
            "Create original plot, characters, scenes, and wording; do not imitate signature phrasing or reproduce existing passages."
        )

    if not constraints:
        return prompt
    return f"{prompt}\n\nCreative constraints:\n" + "\n".join(
        f"- {item}" for item in constraints
    )


def get_workshop_limits(mode: Any) -> dict[str, Any]:
    return WORKSHOP_LIMITS[normalize_workflow_mode(mode)]


def _positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Field '{field_name}' must be a positive integer.") from exc
    if parsed < 1:
        raise ValueError(f"Field '{field_name}' must be at least 1.")
    return parsed


def validate_workshop_request(payload: dict[str, Any]) -> tuple[str, int, int]:
    """Validate initial-generation limits for the selected workshop."""
    mode = normalize_workflow_mode(payload.get("mode") or payload.get("workflow_mode"))
    limits = get_workshop_limits(mode)
    chapters = _positive_int(
        payload.get("chapters") or DEFAULT_STORY_CONFIG["target_chapters"],
        "chapters",
    )
    chapter_length = normalize_target_chapter_length(
        payload.get("chapter_length", payload.get("target_chapter_length"))
    )
    max_chapters = limits["max_chapters"]
    if max_chapters is not None and chapters > max_chapters:
        raise ValueError(f"{limits['label']}单次最多生成 {max_chapters} 章。")
    if chapter_length > limits["max_chapter_length"]:
        raise ValueError(
            f"{limits['label']}每章最多 {limits['max_chapter_length']} 字。"
        )
    return mode, chapters, chapter_length


def validate_continuation_request(
    payload: dict[str, Any],
    *,
    used_continuations: int,
) -> tuple[str, int]:
    """Validate a continuation without applying a hidden cap to long-form mode."""
    mode = normalize_workflow_mode(payload.get("mode") or payload.get("workflow_mode"))
    limits = get_workshop_limits(mode)
    max_runs = limits["max_continuations"]
    if max_runs is not None and used_continuations >= max_runs:
        raise ValueError(f"{limits['label']}最多续写 {max_runs} 次。")
    chapters = _positive_int(payload.get("continue_chapters", 3), "continue_chapters")
    max_chapters = limits["max_continue_chapters"]
    if max_chapters is not None and chapters > max_chapters:
        raise ValueError(f"{limits['label']}每次续写最多 {max_chapters} 章。")
    return mode, chapters


def build_runtime_config(
    *,
    provider: Optional[str] = None,
    deep_model: Optional[str] = None,
    quick_model: Optional[str] = None,
    workflow_mode: Optional[str] = None,
    output_language: Optional[str] = None,
    chapter_count: Optional[int] = None,
    target_chapter_length: Optional[int] = None,
    author_style: Optional[str] = None,
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
    if workflow_mode:
        config["workflow_mode"] = normalize_workflow_mode(workflow_mode)
        config["fast_mode"] = config["workflow_mode"] == "quick"
        if config["workflow_mode"] == "deep":
            config["max_revision_rounds"] = max(int(config["max_revision_rounds"]), 3)
    if output_language:
        config["output_language"] = output_language
    if chapter_count is not None:
        config["target_chapters"] = chapter_count
    if target_chapter_length is not None:
        config["target_chapter_length"] = normalize_target_chapter_length(
            target_chapter_length
        )
    if author_style is not None:
        style_key = normalize_author_style(author_style)
        config["author_style"] = style_key
        config["author_style_label"] = get_author_style_label(style_key)
        config["author_style_guidance"] = get_author_style_guidance(style_key)
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
        "mode": "workflow_mode",
        "output_language": "output_language",
        "results_dir": "results_dir",
        "deepseek_reasoning_effort": "deepseek_reasoning_effort",
        "deepseek_thinking_enabled": "deepseek_thinking_enabled",
        "author_style": "author_style",
    }
    for incoming, target in field_map.items():
        if incoming in payload and payload[incoming] not in (None, ""):
            overrides[target] = (
                normalize_workflow_mode(payload[incoming])
                if incoming == "mode"
                else normalize_author_style(payload[incoming])
                if incoming == "author_style"
                else payload[incoming]
            )
    if "workflow_mode" in payload and payload["workflow_mode"] not in (None, ""):
        overrides["workflow_mode"] = normalize_workflow_mode(payload["workflow_mode"])
    if "chapters" in payload and payload["chapters"] not in (None, ""):
        _, chapters, _ = validate_workshop_request(payload)
        overrides["target_chapters"] = chapters
    chapter_length = payload.get(
        "chapter_length",
        payload.get("target_chapter_length"),
    )
    if chapter_length not in (None, ""):
        _, _, normalized_length = validate_workshop_request(payload)
        overrides["target_chapter_length"] = normalized_length
    if "workflow_mode" in overrides:
        overrides["fast_mode"] = overrides["workflow_mode"] == "quick"
        if overrides["workflow_mode"] == "deep":
            overrides["max_revision_rounds"] = max(
                int(DEFAULT_STORY_CONFIG["max_revision_rounds"]),
                3,
            )
    return overrides


def build_story_response_payload(state: dict[str, Any], manuscript: str) -> dict[str, Any]:
    chapters = [normalize_chapter_text(item) for item in (state.get("chapters", []) or [])]
    canonical_manuscript = str(manuscript or "").replace("\r\n", "\n").strip()
    if not canonical_manuscript and chapters:
        canonical_manuscript = render_manuscript(chapters)
    return {
        "story_title": state.get("story_title", ""),
        "story_brief": state.get("story_brief", ""),
        "story_bible": state.get("story_bible", ""),
        "character_sheets": state.get("character_sheets", ""),
        "plot_outline": state.get("plot_outline", ""),
        "current_chapter_draft": state.get("current_chapter_draft", ""),
        "chapters": chapters,
        "chapter_summaries": state.get("chapter_summaries", []),
        "continuity_notes": state.get("continuity_notes", ""),
        "showrunner_status": state.get("showrunner_status", ""),
        "final_manuscript": canonical_manuscript,
        "target_chapter_length": normalize_target_chapter_length(
            state.get("target_chapter_length")
            or DEFAULT_STORY_CONFIG["target_chapter_length"]
        ),
        "workflow_mode": normalize_workflow_mode(
            state.get("workflow_mode") or state.get("_workflow_mode")
        ),
        "author_style": normalize_author_style(
            state.get("author_style") or state.get("_author_style")
        ),
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

    final_manuscript = render_manuscript(merged_chapters)

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
        "target_chapter_length": normalize_target_chapter_length(
            generated_story.get("target_chapter_length")
            or existing_story.get("target_chapter_length")
            or DEFAULT_STORY_CONFIG["target_chapter_length"]
        ),
    }


class StoryAgentsRequestHandler(BaseHTTPRequestHandler):
    server_version = "StoryAgentsHTTP/0.1"

    def __init__(
        self,
        *args,
        graph_factory: Callable[[dict[str, Any]], StoryAgentsGraph],
        h5_dir: Path,
        results_dir: Path,
        task_registry: StoryTaskRegistry,
        **kwargs,
    ):
        self.graph_factory = graph_factory
        self.h5_dir = h5_dir
        self.results_dir = results_dir
        self.task_registry = task_registry
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

        if parsed.path.startswith("/api/storyagents/tasks/"):
            task_id = parsed.path.removeprefix("/api/storyagents/tasks/").strip("/")
            self._serve_task(task_id, parsed.query)
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

        if parsed.path == "/api/storyagents/preview":
            self._handle_preview()
            return

        if parsed.path == "/api/storyagents/tasks":
            self._create_task()
            return

        if parsed.path.startswith("/api/storyagents/tasks/"):
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 4 and parts[:3] == ["api", "storyagents", "tasks"]:
                self._control_task(parts[3], "resume")
                return
            if len(parts) == 5 and parts[:3] == ["api", "storyagents", "tasks"]:
                self._control_task(parts[3], parts[4])
                return

        if parsed.path == "/api/storyagents/edit":
            self._handle_edit()
            return

        if parsed.path == "/api/storyagents/continue":
            self._handle_continue()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _create_task(self):
        try:
            payload = self._read_json_body()
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                raise ValueError("Field 'prompt' is required.")
            _, chapter_count, _ = validate_workshop_request(payload)
            payload = dict(payload)
            payload["chapters"] = chapter_count
            task = self.task_registry.create(payload)
            worker = threading.Thread(
                target=self._run_task,
                args=(task,),
                daemon=True,
                name=f"story-task-{task.task_id[:8]}",
            )
            worker.start()
            self._send_json(task.snapshot(), status=HTTPStatus.ACCEPTED)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _run_task(self, task: StoryTask):
        try:
            payload = task.payload
            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)
            prompt = enrich_generation_prompt(str(payload["prompt"]).strip(), payload)
            task.status = "running"
            require_outline = bool(payload.get("confirm_outline"))
            for event in graph.generate_story_stream(
                prompt,
                target_chapters=int(payload["chapters"]),
            ):
                task.append_event(event)
                node = (event.get("data") or {}).get("node")
                if require_outline and node == "Outline Agent":
                    with task._condition:
                        task.awaiting_outline = True
                        task.status = "awaiting_outline"
                        task.updated_at = time.time()
                task.wait_if_paused()

            if task.last_state.get("final_manuscript"):
                response = build_story_response_payload(
                    task.last_state,
                    task.last_state.get("final_manuscript", ""),
                )
                response["workflow_mode"] = overrides.get(
                    "workflow_mode", DEFAULT_STORY_CONFIG["workflow_mode"]
                )
                task.story_id = self._save_story(payload, response)
                task.append_event(
                    {
                        "event": "story_saved",
                        "data": {
                            "story_id": task.story_id,
                            "workflow_mode": response["workflow_mode"],
                        },
                    }
                )
            task.status = "completed"
            task.updated_at = time.time()
        except Exception as exc:
            task.error = str(exc)
            task.status = "failed"
            task.updated_at = time.time()
            task.append_event({"error": str(exc), "type": exc.__class__.__name__})

    def _serve_task(self, task_id: str, query: str):
        task = self.task_registry.get(unquote(task_id))
        if task is None:
            self._send_json({"error": "Task not found."}, status=HTTPStatus.NOT_FOUND)
            return
        after = 0
        for pair in query.split("&"):
            if pair.startswith("after="):
                try:
                    after = int(pair.split("=", 1)[1])
                except ValueError:
                    after = 0
        self._send_json(task.snapshot(after))

    def _control_task(self, task_id: str, action: str):
        task = self.task_registry.get(unquote(task_id))
        if task is None:
            self._send_json({"error": "Task not found."}, status=HTTPStatus.NOT_FOUND)
            return
        if action == "pause":
            task.pause()
        elif action in {"resume", "approve-outline"}:
            task.resume()
        else:
            self._send_json({"error": "Unsupported task action."}, status=HTTPStatus.BAD_REQUEST)
            return
        self._send_json(task.snapshot())

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

            _, chapter_count, _ = validate_workshop_request(payload)

            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)
            generation_prompt = enrich_generation_prompt(prompt, payload)
            state, manuscript = graph.generate_story(
                generation_prompt,
                target_chapters=chapter_count,
            )
            response = build_story_response_payload(state, manuscript)
            response["workflow_mode"] = overrides.get(
                "workflow_mode",
                DEFAULT_STORY_CONFIG["workflow_mode"],
            )
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

            _, chapter_count, _ = validate_workshop_request(payload)

            overrides = build_request_overrides(payload)
            graph = self.graph_factory(overrides)
            generation_prompt = enrich_generation_prompt(prompt, payload)

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
            for event in graph.generate_story_stream(
                generation_prompt,
                target_chapters=chapter_count,
            ):
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
                response["workflow_mode"] = overrides.get(
                    "workflow_mode",
                    DEFAULT_STORY_CONFIG["workflow_mode"],
                )
                story_id = self._save_story(payload, response)
                saved_event = {
                    "event": "story_saved",
                    "data": {
                        "story_id": story_id,
                        "workflow_mode": response["workflow_mode"],
                    },
                }
                self._write_sse_event(saved_event)

        except ValueError as exc:
            self._write_sse_event({"error": str(exc)})
        except Exception as exc:
            self._write_sse_event(
                {"error": str(exc), "type": exc.__class__.__name__},
            )

    def _handle_preview(self):
        """Generate a short, unsaved sample using the current workshop settings."""
        try:
            payload = self._read_json_body()
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                self._send_json(
                    {"error": "Field 'prompt' is required."},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            from agentscope.agent import Agent, InjectionConfig, ReActConfig
            from agentscope.message import UserMsg
            from storyagents.orchestration.models import create_chat_model

            mode, _, _ = validate_workshop_request(payload)
            overrides = build_request_overrides(payload)
            config = build_runtime_config(
                provider=overrides.get("llm_provider"),
                quick_model=overrides.get("quick_think_llm"),
                workflow_mode=mode,
                output_language=overrides.get("output_language"),
                author_style=overrides.get("author_style"),
                target_chapter_length=overrides.get("target_chapter_length"),
            )
            model = create_chat_model(
                provider=config["llm_provider"],
                model=config["quick_think_llm"],
                base_url=config.get("backend_url"),
                stream=False,
                thinking_enabled=bool(config.get("deepseek_thinking_enabled", False)),
            )
            agent = Agent(
                name="Style Preview",
                system_prompt=(
                    "You write compact original fiction previews. Follow the supplied constraints, "
                    "but never explain them or mention the reference author."
                ),
                model=model,
                react_config=ReActConfig(max_iters=3),
                injection_config=InjectionConfig(inject_runtime_state=False),
            )
            preview_prompt = enrich_generation_prompt(prompt, payload)
            preview_prompt += (
                "\n\nWrite one self-contained Chinese fiction preview of about 200 Chinese characters. "
                "Begin directly with prose. Do not add a title, outline, commentary, or Markdown."
            )

            async def generate_preview():
                reply = await agent.reply(UserMsg(name="user", content=preview_prompt))
                return (reply.get_text_content() or "").strip()

            preview = asyncio.run(generate_preview())
            if not preview:
                raise RuntimeError("Preview generation returned no text.")
            self._send_json({"preview": preview[:260], "mode": mode})
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json(
                {"error": str(exc), "type": exc.__class__.__name__},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _handle_edit(self):
        try:
            from storyagents.orchestration.editor import VALID_EDIT_ACTIONS, create_editor
            from storyagents.orchestration.models import create_chat_model

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

            if action not in VALID_EDIT_ACTIONS:
                self._send_json(
                    {
                        "error": (
                            "Invalid action. Must be one of: "
                            + ", ".join(VALID_EDIT_ACTIONS)
                        )
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            provider = payload.get("provider", DEFAULT_STORY_CONFIG["llm_provider"])
            model_name = payload.get(
                "quick_model",
                DEFAULT_STORY_CONFIG["quick_think_llm"],
            )
            chat_model = create_chat_model(
                provider=provider,
                model=model_name,
                base_url=payload.get("backend_url"),
                stream=False,
            )
            editor = create_editor(chat_model)
            result = editor(
                text,
                action=action,
                context=context,
                instruction=instruction,
            )

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
            payload = payload.copy()
            payload.setdefault(
                "mode",
                existing_story.get("_workflow_mode", DEFAULT_STORY_CONFIG["workflow_mode"]),
            )
            payload.setdefault(
                "chapter_length",
                existing_story.get(
                    "_target_chapter_length",
                    existing_story.get("target_chapter_length"),
                ),
            )
            payload.setdefault("author_style", existing_story.get("_author_style", ""))

            # Build continuation prompt
            existing_chapters = existing_story.get("chapters", [])
            story_brief = existing_story.get("story_brief", "")
            plot_outline = existing_story.get("plot_outline", "")
            story_title = existing_story.get("story_title", "")

            used_continuations = max(
                0,
                int(existing_story.get("_continuation_count", 0) or 0),
            )
            try:
                continuation_mode, continue_chapters = validate_continuation_request(
                    payload,
                    used_continuations=used_continuations,
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            payload["mode"] = continuation_mode

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
            generation_prompt = enrich_generation_prompt(context_prompt, payload)

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
            for event in graph.generate_story_stream(
                generation_prompt,
                target_chapters=continue_chapters,
            ):
                if event["event"] == "node_complete":
                    last_state.update(event["data"])
                    merged_event_data = dict(event["data"])
                    merged_event_data["story_id"] = safe_id
                    merged_event_data["chapters"] = existing_chapters + list(
                        event["data"].get("chapters", [])
                    )
                    if merged_event_data.get("final_manuscript"):
                        merged_event_data["final_manuscript"] = render_manuscript(
                            merged_event_data["chapters"]
                        )
                    event = {"event": "node_complete", "data": merged_event_data}
                if not self._write_sse_event(event):
                    break

            if last_state.get("final_manuscript"):
                generated_story = build_story_response_payload(
                    last_state,
                    last_state.get("final_manuscript", ""),
                )
                generated_story["workflow_mode"] = normalize_workflow_mode(
                    payload.get("mode", DEFAULT_STORY_CONFIG["workflow_mode"])
                )
                merged_story = merge_story_payloads(existing_story, generated_story)
                updated_story = self._apply_story_metadata(
                    existing_story,
                    merged_story,
                    payload=payload,
                )
                updated_story["_continuation_count"] = used_continuations + 1
                self._write_story_file(
                    path,
                    updated_story,
                )
                saved_event = {
                    "event": "story_saved",
                    "data": {
                        "story_id": safe_id,
                        "workflow_mode": generated_story["workflow_mode"],
                    },
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
                        "mode": data.get("_workflow_mode", DEFAULT_STORY_CONFIG["workflow_mode"]),
                        "author_style": get_author_style_label(data.get("_author_style", "")),
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
            "target_chapter_length",
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
        result["_author_style"] = normalize_author_style(
            (
                payload.get("author_style", existing_story.get("_author_style", ""))
                if payload is not None
                else existing_story.get("_author_style", "")
            )
        )
        result["_continuation_count"] = max(
            0,
            int(existing_story.get("_continuation_count", 0) or 0),
        )
        result["_workflow_mode"] = normalize_workflow_mode(
            (
                payload.get("mode", existing_story.get("_workflow_mode", DEFAULT_STORY_CONFIG["workflow_mode"]))
                if payload is not None
                else existing_story.get("_workflow_mode", DEFAULT_STORY_CONFIG["workflow_mode"])
            )
        )
        chapter_length_source = (
            payload.get(
                "chapter_length",
                payload.get(
                    "target_chapter_length",
                    existing_story.get("_target_chapter_length"),
                ),
            )
            if payload is not None
            else existing_story.get(
                "_target_chapter_length",
                existing_story.get("target_chapter_length"),
            )
        )
        normalized_chapter_length = normalize_target_chapter_length(
            chapter_length_source
        )
        result["target_chapter_length"] = normalized_chapter_length
        result["_target_chapter_length"] = normalized_chapter_length
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
                workflow_mode=overrides.get("workflow_mode"),
                output_language=overrides.get("output_language"),
                chapter_count=overrides.get("target_chapters"),
                target_chapter_length=overrides.get("target_chapter_length"),
                author_style=overrides.get("author_style"),
                results_dir=overrides.get("results_dir"),
                deepseek_reasoning_effort=overrides.get("deepseek_reasoning_effort"),
                deepseek_thinking_enabled=overrides.get("deepseek_thinking_enabled"),
            )
        )
    task_registry = StoryTaskRegistry()
    handler = partial(
        StoryAgentsRequestHandler,
        graph_factory=graph_factory,
        h5_dir=(h5_dir or H5_DIR),
        results_dir=Path(DEFAULT_STORY_CONFIG["results_dir"]),
        task_registry=task_registry,
    )
    server = ThreadingHTTPServer((host, port), handler)
    server.task_registry = task_registry
    return server


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
