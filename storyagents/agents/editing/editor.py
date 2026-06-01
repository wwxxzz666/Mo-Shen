"""Editor agent for rewriting, expanding, compressing, and polishing text."""

from __future__ import annotations

from typing import Any, Dict

from storyagents.agents.utils.structured_utils import bind_structured

from storyagents.schemas import EditResult


EDIT_PROMPTS = {
    "rewrite": """你是一位资深文字编辑。请改写以下文字，保持原意但换一种表达方式。

要求：
- 保持原文的核心意思和情感
- 使用不同的词汇和句式
- 保持相同的长度范围
- 确保改写后的文字流畅自然

原文：
{text}

{context}""",

    "expand": """你是一位资深文字编辑。请扩写以下文字，增加更多细节和描写。

要求：
- 保持原文的核心情节和走向
- 增加环境描写、心理活动、感官细节
- 扩展对话和互动
- 扩写后长度为原文的 1.5-2 倍

原文：
{text}

{context}""",

    "compress": """你是一位资深文字编辑。请精简以下文字，去除冗余但保留精华。

要求：
- 保留核心情节和关键信息
- 删除重复、冗长的描写
- 精简对话，保留关键台词
- 压缩后长度为原文的 60-70%

原文：
{text}

{context}""",

    "polish": """你是一位资深文字编辑。请润色以下文字，提升文采和可读性。

要求：
- 保持原文结构和情节不变
- 优化用词，替换平淡词汇
- 改善句式节奏和韵律
- 增强文学性和感染力

原文：
{text}

{context}""",
}


def create_editor(llm):
    """Create an editor agent for text manipulation."""

    structured_llm = bind_structured(llm, EditResult, "Editor")

    def edit_text(
        text: str,
        action: str = "rewrite",
        context: str = "",
        instruction: str = "",
    ) -> Dict[str, Any]:
        prompt_template = EDIT_PROMPTS.get(action, EDIT_PROMPTS["rewrite"])

        context_block = ""
        if context:
            context_block = f"上下文信息：\n{context}"
        if instruction:
            context_block += f"\n\n用户指令：\n{instruction}"

        prompt = prompt_template.format(text=text, context=context_block)

        if structured_llm:
            result = structured_llm.invoke(prompt)
            return {
                "edited_text": result.edited_text,
                "changes_summary": result.changes_summary,
            }
        else:
            # Fallback: free text generation
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return {
                "edited_text": content,
                "changes_summary": f"已完成{action}操作。",
            }

    return edit_text
