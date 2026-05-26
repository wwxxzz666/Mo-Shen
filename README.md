# 墨神 (Mo-Shen)

多智能体协作小说生成框架，四个专职 AI 智能体接力完成从创意到成稿的全流程。

## 架构

墨神基于 [LangGraph](https://github.com/langchain-ai/langgraph) 构建，通过 4 个专职智能体的流水线协作生成小说：

```
策划编辑 → 剧情架构师 → 章节写手 → 总编
```

| 智能体 | 职责 |
|--------|------|
| **策划编辑** | 将创意灵感压缩为明确、可执行的创作需求 |
| **剧情架构师** | 生成章节节拍，确保故事持续前进 |
| **章节写手** | 扩写为正文，让人物真正开口与行动 |
| **总编** | 最终拍板，决定通过、续章或返工 |

## 功能

- 多智能体流水线协作生成小说
- 支持 DeepSeek、OpenAI、Anthropic、Google 等多种 LLM 后端
- 极速模式（fast_mode）四段式快速出稿
- 内置 Web 控制台，实时追踪智能体协作进度
- 成稿支持导出 TXT / DOCX
- 历史记录管理（查看、导出、删除）

## 快速开始

### 安装

```bash
git clone https://github.com/wwxxzz666/Mo-Shen.git
cd Mo-Shen
pip install -e .
```

### 配置

创建 `.env` 文件，填入你的 LLM API Key：

```
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

默认使用 DeepSeek，也可切换为 OpenAI、Anthropic 等其他提供商。

### 启动 Web 服务

```bash
python -m storyagents.cli serve --port 8000
```

浏览器打开 `http://localhost:8000` 即可使用。

### 命令行生成

```bash
python -m storyagents.cli generate "写一个发生在海上记忆之城的悬疑小说"
```

### 运行测试

```bash
pip install pytest
python -m pytest tests/ -v
```

## 技术栈

- **Python 3.10+**
- **LangChain / LangGraph** — 多智能体编排框架
- **Pydantic** — 数据校验
- **Typer** — CLI 框架
- **Vanilla HTML/CSS/JS** — 前端控制台
- **docx.js** — 浏览器端 DOCX 生成

## 项目结构

```
storyagents/
├── agents/            # 各专职智能体实现
│   ├── planning/      # 策划编辑
│   ├── outlining/     # 剧情架构师
│   ├── writing/       # 章节写手
│   ├── management/    # 总编
│   ├── worldbuilding/ # 世界观构建（标准模式）
│   ├── characters/    # 角色设计（标准模式）
│   └── review/        # 审稿（标准模式）
├── graph/             # LangGraph 图定义与编排
├── llm_clients/       # 多 LLM 后端适配层
├── h5/                # Web 控制台前端
├── cli.py             # 命令行入口
├── server.py          # HTTP 服务器
├── schemas.py         # 数据模型
└── default_config.py  # 默认配置
```

## License

MIT
