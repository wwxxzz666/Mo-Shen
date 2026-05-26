# StoryAgents H5

这是一个独立的移动端友好前端，用来展示 `StoryAgents` 的多智能体小说创作流程。

## 文件

- `index.html`: 页面结构
- `styles.css`: 视觉样式
- `app.js`: 交互逻辑、Mock 演示、API 请求适配

## 使用方式

直接打开：

```text
storyagents/h5/index.html
```

如果你希望 `API Live` 模式直接连上真实小说生成后端，推荐直接启动内置服务：

```bash
storyagents serve --host 127.0.0.1 --port 8000
```

然后打开：

```text
http://127.0.0.1:8000/h5/
```

这时页面里的默认接口 `/api/storyagents/draft` 会自动走同源请求，不需要手动改 endpoint。

如果你只是想单独预览静态界面，也可以通过本地静态服务器访问。

例如：

```bash
python -m http.server 18990
```

然后打开：

```text
http://127.0.0.1:18990/storyagents/h5/
```

## 页面能力

- `Mock Demo`:
  - 不依赖后端
  - 本地演示 7 个智能体的协作顺序
  - 自动生成 brief / world / cast / outline / chapter / manuscript 示例内容

- `API Live`:
  - 请求真实小说生成后端
  - 如果通过 `storyagents serve` 启动，默认 endpoint 已可直接使用
  - 如果你有别的后端地址，也可以手动改 endpoint

## API 返回格式

前端会优先读取下面这些字段：

```json
{
  "story_title": "《潮汐档案》",
  "story_brief": "整理后的故事 brief",
  "story_bible": "世界观设定",
  "character_sheets": "角色卡与关系网",
  "plot_outline": "章节大纲",
  "current_chapter_draft": "当前章节正文",
  "chapters": [
    "第一章正文",
    "第二章正文"
  ],
  "final_manuscript": "合并后的完整稿件"
}
```

其中：

- `chapters` 可选
- `current_chapter_draft` 可选
- `final_manuscript` 最好提供

如果 `chapters` 存在，前端会优先展示最后一章作为 `Current Chapter`。

## 设计方向

这版界面走的是“夜色编辑部 / 纸上调度台”的视觉路线：

- 深墨色背景
- 铜金与珊瑚橙高亮
- `Prata` + `IBM Plex Sans` 字体搭配
- 移动端优先布局
- 强调流程感、阶段感和产物切换感
