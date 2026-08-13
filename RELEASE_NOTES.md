# Release Notes

## 2026-08-13 · v2.0.2

### 用户创作流程

- 三种模式重新命名并按使用目的拆分为灵感工坊、故事工坊和长篇工坊
- 增加约 200 字风格试写，确认风格后才开始正式创作
- 故事工坊和长篇工坊增加大纲确认关口
- 正文逐章展示，Agent 节点与日志收进“协作详情”
- 三个工坊均允许自定义章节数，每章最多 5000 字

### 后台任务与恢复

- 新增独立创作任务与 `task_id`
- 支持任务状态查询、事件游标、暂停、恢复和大纲确认
- 页面退出或网络中断后可恢复已有任务，不重复生成已完成内容
- 暂停在当前 Agent 步骤完成后生效，保护章节和共享故事状态

### 微信小程序

- 工作室从定时器模拟数据切换为真实 HTTP API
- 接入试写、正式任务、大纲确认、暂停恢复和成稿读取
- 增加本地草稿和活动任务恢复
- 使用适合触屏和纵向小屏的东方诗意界面

### 工程质量

- 增强小说章节格式规范化和成稿完整性校验
- 增加后台任务、大纲确认、请求边界和前端 SSE 测试
- Python 测试 20 项通过，前端测试 4 项通过；真实模型 smoke 保持为显式启用

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
