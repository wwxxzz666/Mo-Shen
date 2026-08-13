"""Canonical manuscript formatting and completion checks."""

from __future__ import annotations

import re
from typing import Any, Iterable


_CHAPTER_HEADING = re.compile(
    r"^\s{0,3}#{0,3}\s*(?:chapter\s+\d+|第\s*[0-9一二三四五六七八九十百千]+\s*章)\b.*$",
    re.IGNORECASE,
)


def normalize_chapter_text(text: Any) -> str:
    """Remove wrapper noise while keeping the chapter's internal Markdown."""
    value = str(text or "").replace("\r\n", "\n").strip()
    if not value:
        return ""
    lines = value.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and _CHAPTER_HEADING.match(lines[0].strip()):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines).strip()


def render_manuscript(chapters: Iterable[Any]) -> str:
    """Render every chapter once with stable Markdown headings."""
    rendered = []
    for index, chapter in enumerate(chapters, start=1):
        body = normalize_chapter_text(chapter)
        if body:
            rendered.append(f"# Chapter {index}\n\n{body}")
    return "\n\n".join(rendered)


def ensure_chapter_summaries(chapters: list[str], summaries: Iterable[Any]) -> list[str]:
    """Keep the archive useful even when a fast workflow has no reviewer."""
    existing = [str(item or "").strip() for item in summaries]
    result = []
    for index, chapter in enumerate(chapters):
        summary = existing[index] if index < len(existing) else ""
        result.append(summary or normalize_chapter_text(chapter)[:320])
    return result


def validate_completed_story(state: dict[str, Any], expected_chapters: int) -> None:
    """Fail closed so incomplete runs are never reported or saved as complete."""
    chapters = state.get("chapters") or []
    if len(chapters) != expected_chapters:
        raise RuntimeError(
            f"Story completed with {len(chapters)} of {expected_chapters} chapters."
        )
    if any(not normalize_chapter_text(chapter) for chapter in chapters):
        raise RuntimeError("Story completed with an empty chapter.")
    if state.get("showrunner_status") != "Complete":
        raise RuntimeError("Story workflow did not reach a complete editorial decision.")
