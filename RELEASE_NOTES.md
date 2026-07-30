# Release Notes

## 2026-07-29 · v2.0（分支 agentscope-mo-shen）

### 版本分轨

- 默认分支 `main` → 经典 LangGraph 版，标签 **`v1`**
- 分支 `agentscope-mo-shen` → AgentScope 版，标签 **`v2.0`**
- README 按双版本结构展示：对照表、架构说明、克隆方式

### 运行时（相对 v1）

- 多智能体协作编排从 **LangGraph** 切换为 **AgentScope 2.x**
- 新增 `storyagents/orchestration/`：角色 Agent、共享故事状态、条件路由与章节循环
- 局部编辑 **Editor** 迁到 AgentScope
- 清理旧 `agents/` / LangGraph `graph/` 实现与 `llm_clients/`
- 移除 LangChain 运行时依赖
- 仍保留 `quick` / `standard` / `deep` 与 CLI / HTTP / H5 接口
- `StoryAgentsGraph` API 兼容
- Python **3.11+**
- 真实 API smoke：`tests/test_real_api_smoke.py`（`STORYAGENTS_RUN_SMOKE=1`）

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
