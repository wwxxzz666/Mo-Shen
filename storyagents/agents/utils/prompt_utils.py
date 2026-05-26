def get_language_instruction(config: dict) -> str:
    language = config.get("output_language", "English").strip()
    if language.lower() == "english":
        return ""
    return f" Write your response in {language}."


def format_recent_summaries(summaries: list[str], limit: int = 3) -> str:
    if not summaries:
        return "No prior chapters yet."
    recent = summaries[-limit:]
    return "\n\n".join(
        f"Chapter {idx + 1} summary:\n{summary}"
        for idx, summary in enumerate(
            recent, start=len(summaries) - len(recent) + 1
        )
    )
