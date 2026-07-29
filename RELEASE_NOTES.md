# Release Notes

## 2026-07-29 · v0.2.1（AgentScope 正式版展示）

### 文档与发布面

- README / README_EN 按 **v0.2 AgentScope 版**重写：版本介绍、v0.1→v0.2 对照表、改动清单、架构简图
- GitHub Release / Tag：`v0.2.1`，默认分支 `main` 展示新版说明

### 运行时（相对 v0.1）

- 局部编辑 **Editor** 迁到 AgentScope（`orchestration/editor.py`）
- 清理 `graph/` 中 LangGraph 实现与旧 `agents/` 角色节点
- 移除 `llm_clients/` 与 LangChain 运行时依赖
- 新增真实 API smoke 测试：`tests/test_real_api_smoke.py`（`STORYAGENTS_RUN_SMOKE=1` 启用）

## 2026-07-29 · v0.2.0

### AgentScope Multi-Agent Orchestration

- 多智能体协作编排从 **LangGraph** 切换为 **AgentScope 2.x**
- 新增 `storyagents/orchestration/`：角色 Agent、共享故事状态、条件路由与章节循环
- 仍保留 `quick` / `standard` / `deep` 三档工作流，以及 CLI / HTTP / H5 对外接口
- `StoryAgentsGraph` API 保持兼容（`generate_story` / `generate_story_stream`）
- 要求 Python **3.11+**

## 2026-06-01

### UI Refresh

- H5 工作台升级为黑金液态玻璃风格
- 首页、工作台、历史页和编辑弹窗统一为新的视觉语言
- 新增工作流模式选择区，模式说明与界面状态同步可见

### Story Persistence

- 生成完成后返回并保存 `story_id`
- 局部编辑后的正文可直接回写原故事项目
- 续写结果会自动合并回原故事，不再只停留在流式展示
- 历史记录保留创建时间、更新时间和模式信息

### Workflow Modes

- 新增三档模式：`quick` / `standard` / `deep`
- `quick` 走最短四节点链路，适合快速起稿
- `standard` 增加世界观与角色设计
- `deep` 进一步加入连续性审校，并自动提高修订轮次下限
- 前端会根据模式切换智能体列表与可见产物标签

### Docs

- README 重写为新版首页说明
- README 已补入可线上展示的界面截图
- 增加本文件，便于后续继续累积版本记录
