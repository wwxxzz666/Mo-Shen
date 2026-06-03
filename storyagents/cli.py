from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from storyagents.default_config import DEFAULT_STORY_CONFIG, normalize_workflow_mode
from storyagents.graph.story_graph import StoryAgentsGraph
from storyagents.server import serve as serve_storyagents

app = typer.Typer(
    name="StoryAgents",
    help="StoryAgents CLI: multi-agent fiction drafting assistant",
    add_completion=True,
)


def _base_config(
    *,
    chapters: int,
    provider: Optional[str],
    deep_model: Optional[str],
    quick_model: Optional[str],
    workflow_mode: Optional[str] = None,
    output_language: Optional[str] = None,
    deepseek_reasoning_effort: Optional[str] = None,
    deepseek_thinking_enabled: Optional[bool] = None,
) -> dict:
    config = DEFAULT_STORY_CONFIG.copy()
    config["target_chapters"] = chapters
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
            config["max_revision_rounds"] = max(config["max_revision_rounds"], 3)
    if output_language:
        config["output_language"] = output_language
    if deepseek_reasoning_effort:
        config["deepseek_reasoning_effort"] = deepseek_reasoning_effort
    if deepseek_thinking_enabled is not None:
        config["deepseek_thinking_enabled"] = deepseek_thinking_enabled
    return config


@app.command()
def draft(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Story request or concept."),
    chapters: int = typer.Option(
        DEFAULT_STORY_CONFIG["target_chapters"],
        "--chapters",
        "-c",
        min=1,
        max=12,
        help="Target chapter count for this run.",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Override the configured LLM provider.",
    ),
    deep_model: Optional[str] = typer.Option(
        None,
        "--deep-model",
        help="Override the planning/showrunner model.",
    ),
    quick_model: Optional[str] = typer.Option(
        None,
        "--quick-model",
        help="Override the drafting/review model.",
    ),
    workflow_mode: str = typer.Option(
        DEFAULT_STORY_CONFIG["workflow_mode"],
        "--mode",
        help="Workflow mode: quick, standard, or deep.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional file path to save the generated manuscript.",
    ),
):
    config = _base_config(
        chapters=chapters,
        provider=provider,
        deep_model=deep_model,
        quick_model=quick_model,
        workflow_mode=workflow_mode,
    )

    graph = StoryAgentsGraph(config=config)
    state, manuscript = graph.generate_story(prompt, target_chapters=chapters)

    header = f"# {state.get('story_title') or 'Untitled Story'}\n\n"
    output_text = header + manuscript
    typer.echo(output_text)

    if output:
        output.write_text(output_text, encoding="utf-8")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address."),
    port: int = typer.Option(8000, "--port", help="Bind port."),
    chapters: int = typer.Option(
        DEFAULT_STORY_CONFIG["target_chapters"],
        "--chapters",
        min=1,
        max=12,
        help="Default chapter count for API requests that omit chapters.",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Override the configured LLM provider for the server.",
    ),
    deep_model: Optional[str] = typer.Option(
        None,
        "--deep-model",
        help="Override the planning/showrunner model for the server.",
    ),
    quick_model: Optional[str] = typer.Option(
        None,
        "--quick-model",
        help="Override the drafting/review model for the server.",
    ),
    workflow_mode: str = typer.Option(
        DEFAULT_STORY_CONFIG["workflow_mode"],
        "--mode",
        help="Default workflow mode for the server: quick, standard, or deep.",
    ),
    output_language: Optional[str] = typer.Option(
        None,
        "--output-language",
        help="Default output language for generated stories.",
    ),
    deepseek_reasoning_effort: Optional[str] = typer.Option(
        None,
        "--deepseek-reasoning-effort",
        help="Optional DeepSeek reasoning_effort value, for example high.",
    ),
    deepseek_thinking_enabled: bool = typer.Option(
        False,
        "--deepseek-thinking-enabled",
        help="Enable DeepSeek thinking mode via extra_body.",
    ),
):
    config = _base_config(
        chapters=chapters,
        provider=provider,
        deep_model=deep_model,
        quick_model=quick_model,
        workflow_mode=workflow_mode,
        output_language=output_language,
        deepseek_reasoning_effort=deepseek_reasoning_effort,
        deepseek_thinking_enabled=deepseek_thinking_enabled,
    )

    def graph_factory(request_config: dict) -> StoryAgentsGraph:
        merged = config.copy()
        merged.update(request_config)
        return StoryAgentsGraph(config=merged)

    serve_storyagents(host, port, graph_factory=graph_factory)


if __name__ == "__main__":
    app()
