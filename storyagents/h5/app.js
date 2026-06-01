const AGENTS = [
  { name: "策划编辑", role: "把你的灵感压缩成一份明确、可执行的创作需求。" },
  { name: "剧情架构师", role: "生成章节节拍，确保故事持续前进。" },
  { name: "章节写手", role: "扩写为正文，让人物真正开口与行动。" },
  { name: "总编", role: "最终拍板，决定通过、续章或返工。" },
];

/* ---- Style Presets ---- */
const STYLE_PRESETS = {
  wuxia: {
    genre: "武侠 / 江湖",
    tone: "豪迈、侠义、江湖气",
    audience: "成年向",
    prompt_hint: "写一个武侠故事，主角是一名落魄剑客，被迫卷入江湖纷争。",
  },
  detective: {
    genre: "悬疑 / 推理",
    tone: "冷峻、克制、暗流涌动",
    audience: "成年向",
    prompt_hint: "写一个推理故事，一桩看似简单的命案背后隐藏着惊人真相。",
  },
  murakami: {
    genre: "都市 / 文学",
    tone: "疏离、迷幻、超现实",
    audience: "成年向",
    prompt_hint: "写一个都市故事，主角在东京的酒吧遇到一个神秘女人。",
  },
  healing: {
    genre: "治愈 / 日常",
    tone: "温暖、细腻、感动",
    audience: "全年龄",
    prompt_hint: "写一个治愈故事，主角经营一家深夜食堂，每个客人都有自己的故事。",
  },
  cyberpunk: {
    genre: "科幻 / 赛博朋克",
    tone: "黑暗、高科技、低生活",
    audience: "成年向",
    prompt_hint: "写一个赛博朋克故事，主角是一名黑客，在霓虹灯下的都市中寻找真相。",
  },
  xianxia: {
    genre: "仙侠 / 玄幻",
    tone: "飘逸、大气、仙气",
    audience: "全年龄",
    prompt_hint: "写一个仙侠故事，主角是一名修仙者，踏上寻找天道的旅程。",
  },
};

const ARTIFACT_DEFS = [
  { key: "storyBrief", label: "需求", title: "故事需求" },
  { key: "world", label: "设定", title: "世界设定" },
  { key: "characters", label: "角色", title: "角色关系" },
  { key: "outline", label: "大纲", title: "章节大纲" },
  { key: "chapter", label: "章节", title: "当前章节" },
  { key: "manuscript", label: "成稿", title: "最终稿" },
];

const state = {
  artifacts: {},
  activeArtifact: "storyBrief",
  title: "",
  storyId: null,
  chapters: [],
  chapterSummaries: [],
  continuityNotes: "",
};

const form = document.querySelector("#story-form");
const promptInput = document.querySelector("#prompt");
const chapterSlider = document.querySelector("#chapters");
const chapterCount = document.querySelector("#chapter-count");
const chips = Array.from(document.querySelectorAll(".chip"));
const submitButton = document.querySelector("#submit-button");
const runState = document.querySelector("#run-state");
const agentList = document.querySelector("#agent-list");
const artifactTabs = document.querySelector("#artifact-tabs");
const artifactContent = document.querySelector("#artifact-content");
const activityLog = document.querySelector("#activity-log");
const agentCardTemplate = document.querySelector("#agent-card-template");
const progressPanel = document.querySelector("#progress-panel");
const progressFill = document.querySelector("#progress-fill");
const progressPercent = document.querySelector("#progress-percent");
const progressStage = document.querySelector("#progress-stage");
const progressTitle = document.querySelector("#progress-title");

let progressTimer = null;
let progressValue = 0;

const PROGRESS_PHASES = [
  { label: "正在整理创作需求...", target: 12 },
  { label: "正在规划章节大纲...", target: 36 },
  { label: "正在撰写正文初稿...", target: 72 },
  { label: "正在整理最终成稿...", target: 96 },
];

/* ---- View Switching ---- */
function switchView(viewName) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("is-active"));
  const target = document.querySelector(`#view-${viewName}`);
  if (target) target.classList.add("is-active");

  document.querySelectorAll(".topbar-item").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === viewName);
  });
}

document.querySelectorAll(".topbar-item").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.view) switchView(btn.dataset.view);
  });
});

document.querySelectorAll("[data-goto]").forEach((el) => {
  el.addEventListener("click", () => {
    if (el.dataset.goto) switchView(el.dataset.goto);
  });
});

/* ---- Utilities ---- */
function setProgress(value, label) {
  progressValue = Math.max(0, Math.min(100, value));
  progressPanel.classList.remove("is-hidden");
  progressFill.style.width = `${progressValue}%`;
  progressPercent.textContent = `${Math.round(progressValue)}%`;
  progressStage.textContent = label;
  const progressbar = progressPanel.querySelector(".progress-track");
  progressbar.setAttribute("aria-valuenow", String(Math.round(progressValue)));
}

function startProgress(titleText, phases) {
  clearInterval(progressTimer);
  progressTitle.textContent = titleText;
  let phaseIndex = 0;
  let currentTarget = phases[0]?.target ?? 90;
  let currentLabel = phases[0]?.label ?? "正在处理...";
  setProgress(0, currentLabel);

  progressTimer = window.setInterval(() => {
    if (phaseIndex < phases.length && progressValue >= currentTarget) {
      phaseIndex += 1;
      currentTarget = phases[phaseIndex]?.target ?? 96;
      currentLabel = phases[phaseIndex]?.label ?? currentLabel;
      progressStage.textContent = currentLabel;
    }

    if (progressValue < currentTarget) {
      setProgress(progressValue + 1, currentLabel);
      return;
    }

    if (progressValue < 96) {
      setProgress(progressValue + 0.4, currentLabel);
    }
  }, 260);
}

function finishProgress(label = "已生成完成") {
  clearInterval(progressTimer);
  progressTimer = null;
  setProgress(100, label);
}

function failProgress(label = "生成失败，请稍后重试") {
  clearInterval(progressTimer);
  progressTimer = null;
  setProgress(Math.max(progressValue, 12), label);
}

function resetProgress() {
  clearInterval(progressTimer);
  progressTimer = null;
  progressValue = 0;
  progressPanel.classList.add("is-hidden");
  progressFill.style.width = "0%";
  progressPercent.textContent = "0%";
  progressStage.textContent = "正在准备创作任务...";
}

/* ---- Agent Cards ---- */
function renderAgentCards() {
  agentList.innerHTML = "";
  AGENTS.forEach((agent, index) => {
    const fragment = agentCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".agent-card");
    card.dataset.agent = agent.name;
    fragment.querySelector(".agent-index").textContent = String(index + 1).padStart(2, "0");
    fragment.querySelector(".agent-name").textContent = agent.name;
    fragment.querySelector(".agent-role").textContent = agent.role;
    agentList.appendChild(fragment);
  });
}

function setAgentStatus(index, statusText, className) {
  const cards = Array.from(document.querySelectorAll(".agent-card"));
  cards.forEach((card) => {
    card.classList.remove("is-active");
  });
  const card = cards[index];
  if (!card) {
    return;
  }
  const badge = card.querySelector(".agent-status");
  badge.textContent = statusText;
  if (className === "active") {
    card.classList.add("is-active");
  }
  if (className === "done") {
    card.classList.remove("is-active");
    card.classList.add("is-done");
  }
}

function resetAgentStatuses() {
  Array.from(document.querySelectorAll(".agent-card")).forEach((card) => {
    card.classList.remove("is-active", "is-done");
    card.querySelector(".agent-status").textContent = "待命";
  });
}

/* ---- Activity Log ---- */
function pushLog(title, message) {
  const item = document.createElement("div");
  item.className = "activity-item";
  item.innerHTML = `<strong>${title}</strong><p>${message}</p>`;
  activityLog.prepend(item);
}

function resetLog() {
  activityLog.innerHTML = "";
  pushLog("系统就绪", "当前默认是「生成小说」的极速模式，提交后会直接走四段式写作流程。");
}

/* ---- Artifacts ---- */
function renderArtifactTabs() {
  artifactTabs.innerHTML = "";
  ARTIFACT_DEFS.forEach((artifact) => {
    const button = document.createElement("button");
    button.className = `artifact-tab${artifact.key === state.activeArtifact ? " is-active" : ""}`;
    button.type = "button";
    button.textContent = artifact.label;
    button.dataset.key = artifact.key;
    button.addEventListener("click", () => {
      state.activeArtifact = artifact.key;
      renderArtifactTabs();
      renderArtifactContent();
    });
    artifactTabs.appendChild(button);
  });
}

function renderArtifactContent() {
  const active = ARTIFACT_DEFS.find((item) => item.key === state.activeArtifact) || ARTIFACT_DEFS[0];
  const content = state.artifacts[active.key];
  const wrapper = document.createElement("div");
  wrapper.className = "artifact-card";

  if (!content) {
    wrapper.innerHTML = `
      <h3>${active.title}</h3>
      <p>这里会显示对应阶段生成的内容。先发起一次故事生成吧。</p>
    `;
    artifactContent.innerHTML = "";
    artifactContent.appendChild(wrapper);
    return;
  }

  wrapper.innerHTML = `<h3>${active.title}</h3>`;
  if (Array.isArray(content)) {
    const list = document.createElement("ul");
    content.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    wrapper.appendChild(list);
  } else {
    const pre = document.createElement("pre");
    pre.textContent = content;
    wrapper.appendChild(pre);
  }

  artifactContent.innerHTML = "";
  artifactContent.appendChild(wrapper);

  if (active.key === "manuscript" && content) {
    const bar = document.createElement("div");
    bar.className = "export-bar";
    const txtBtn = document.createElement("button");
    txtBtn.type = "button";
    txtBtn.className = "export-btn";
    txtBtn.textContent = "导出 TXT";
    txtBtn.addEventListener("click", exportTxt);
    const docxBtn = document.createElement("button");
    docxBtn.type = "button";
    docxBtn.className = "export-btn";
    docxBtn.textContent = "导出 DOCX";
    docxBtn.addEventListener("click", exportDocx);
    bar.appendChild(txtBtn);
    bar.appendChild(docxBtn);
    artifactContent.appendChild(bar);
  }
}

/* ---- Export ---- */
function getExportFilename(ext) {
  const raw = state.title || "未命名故事";
  const safe = raw.replace(/[\\/*?:"<>|]/g, "").slice(0, 60);
  return `${safe || "story"}.${ext}`;
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportTxt() {
  const text = state.artifacts.manuscript;
  if (!text) return;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  triggerDownload(blob, getExportFilename("txt"));
}

async function exportDocx() {
  const text = state.artifacts.manuscript;
  if (!text) return;

  const { Document, Paragraph, TextRun, Packer, HeadingLevel, AlignmentType } = docx;

  const lines = text.split("\n");
  const children = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      children.push(new Paragraph({ text: "" }));
      continue;
    }
    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length === 1 ? HeadingLevel.HEADING_1
        : headingMatch[1].length === 2 ? HeadingLevel.HEADING_2
        : HeadingLevel.HEADING_3;
      children.push(new Paragraph({
        heading: level,
        alignment: level === HeadingLevel.HEADING_1 ? AlignmentType.CENTER : AlignmentType.LEFT,
        children: [new TextRun({ text: headingMatch[2], bold: true, font: "Microsoft YaHei" })],
      }));
    } else {
      children.push(new Paragraph({
        children: [new TextRun({ text: trimmed, font: "Microsoft YaHei", size: 24 })],
        spacing: { line: 360 },
      }));
    }
  }

  const doc = new Document({
    sections: [{ children }],
  });
  const blob = await Packer.toBlob(doc);
  triggerDownload(blob, getExportFilename("docx"));
}

/* ---- Run State ---- */
function setRunState(text, className) {
  runState.textContent = text;
  runState.classList.remove("is-running", "is-done");
  if (className) {
    runState.classList.add(className);
  }
}

function scrollToOutput() {
  const el = document.querySelector(".studio-output");
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---- API Flow ---- */
function normalizeApiResponse(data) {
  const chapters = Array.isArray(data.chapters) ? data.chapters : [];
  return {
    storyId: data.story_id || null,
    title: data.story_title || "《未命名故事》",
    storyBrief: data.story_brief || "",
    world: data.story_bible || "",
    characters: data.character_sheets || "",
    outline: data.plot_outline || "",
    chapter: chapters[chapters.length - 1] || data.current_chapter_draft || "",
    manuscript: data.final_manuscript || "",
    chapters,
    chapterSummaries: Array.isArray(data.chapter_summaries) ? data.chapter_summaries : [],
    continuityNotes: data.continuity_notes || "",
  };
}

function applyNormalizedStory(normalized) {
  state.storyId = normalized.storyId || state.storyId;
  state.title = normalized.title;
  state.chapters = Array.isArray(normalized.chapters) ? normalized.chapters : [];
  state.chapterSummaries = Array.isArray(normalized.chapterSummaries)
    ? normalized.chapterSummaries
    : [];
  state.continuityNotes = normalized.continuityNotes || "";
  state.artifacts = {
    storyBrief: normalized.storyBrief,
    world: normalized.world,
    characters: normalized.characters,
    outline: normalized.outline,
    chapter: normalized.chapter,
    manuscript: normalized.manuscript,
  };
}

function replaceFirstOccurrence(source, target, replacement) {
  if (!source || !target) return source;
  const index = source.indexOf(target);
  if (index === -1) return source;
  return `${source.slice(0, index)}${replacement}${source.slice(index + target.length)}`;
}

function buildStoryUpdatePayload() {
  if (!state.storyId) {
    return null;
  }
  return {
    story_title: state.title || "",
    story_brief: state.artifacts.storyBrief || "",
    story_bible: state.artifacts.world || "",
    character_sheets: state.artifacts.characters || "",
    plot_outline: state.artifacts.outline || "",
    current_chapter_draft: state.artifacts.chapter || "",
    chapters: Array.isArray(state.chapters) ? state.chapters : [],
    chapter_summaries: Array.isArray(state.chapterSummaries) ? state.chapterSummaries : [],
    continuity_notes: state.continuityNotes || "",
    final_manuscript: state.artifacts.manuscript || "",
  };
}

async function persistCurrentStory() {
  const payload = buildStoryUpdatePayload();
  if (!payload) {
    return;
  }
  const response = await fetch(`/api/storyagents/stories/${encodeURIComponent(state.storyId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const data = await response.json();
  applyNormalizedStory(normalizeApiResponse(data));
}

async function runApiFlow(payload) {
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
  state.storyId = null;
  state.chapters = [];
  state.chapterSummaries = [];
  state.continuityNotes = "";
  renderArtifactTabs();
  renderArtifactContent();
  resetAgentStatuses();
  resetLog();
  switchView("studio");
  scrollToOutput();
  startProgress("正在生成小说", PROGRESS_PHASES);
  setRunState("请求中", "is-running");
  submitButton.disabled = true;
  submitButton.textContent = "请求后端中...";

  AGENTS.forEach((_, index) => {
    if (index === 0) {
      setAgentStatus(index, "等待响应", "active");
    }
  });

  try {
    const response = await fetch("/api/storyagents/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: payload.prompt,
        genre: payload.genre,
        tone: payload.tone,
        audience: payload.audience,
        chapters: Number(payload.chapters),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const normalized = normalizeApiResponse(data);
    applyNormalizedStory(normalized);

    Array.from(document.querySelectorAll(".agent-card")).forEach((card) => {
      card.classList.remove("is-active");
      card.classList.add("is-done");
      card.querySelector(".agent-status").textContent = "已返回";
    });
    pushLog("接口返回完成", "已经收到后端数据并刷新全部故事产物。");
    renderArtifactTabs();
    renderArtifactContent();
    localStorage.setItem("storyagents-h5-form", JSON.stringify(payload));
    finishProgress("小说生成完成");
    setRunState("已完成", "is-done");
    scrollToOutput();
  } catch (error) {
    pushLog("请求失败", `未能从后端获取结果：${error.message}`);
    failProgress("生成失败，请检查网络或稍后重试");
    setRunState("出错");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "重新提交";
  }
}

/* ---- Streaming API Flow ---- */
const NODE_TO_AGENT = {
  "Planner": 0,
  "Outline Agent": 1,
  "Chapter Writer": 2,
  "Showrunner": 3,
};

let currentAbortController = null;

/* ---- Chat Message Helpers ---- */
const NODE_ICONS = {
  "Planner": "📋",
  "Outline Agent": "📝",
  "Chapter Writer": "✍️",
  "Showrunner": "🎬",
  "Worldbuilder": "🌍",
  "Character Designer": "👥",
  "Continuity Reviewer": "🔍",
};

function addChatMessage(type, name, content, options = {}) {
  const container = document.querySelector("#chat-container");
  if (!container) return;

  // Remove welcome message
  const welcome = container.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const msg = document.createElement("div");
  msg.className = `chat-message ${type}-message`;

  const avatarIcon = type === "agent" ? (NODE_ICONS[name] || "🤖") :
                     type === "chapter" ? "📖" : "💬";
  const time = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });

  const isLong = content.length > 500;
  const displayContent = isLong ? content.slice(0, 500) + "..." : content;

  msg.innerHTML = `
    <div class="chat-message-avatar ${type}">${avatarIcon}</div>
    <div class="chat-message-body">
      <div class="chat-message-header">
        <span class="chat-message-name">${escapeHtml(name)}</span>
        <span class="chat-message-time">${time}</span>
      </div>
      <div class="chat-message-content${isLong ? ' collapsed' : ''}">
        <pre>${escapeHtml(displayContent)}</pre>
      </div>
      ${isLong ? '<button class="chat-message-toggle" type="button">展开全文</button>' : ''}
      ${options.extra || ''}
    </div>
  `;

  // Toggle collapse
  const toggle = msg.querySelector(".chat-message-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const pre = msg.querySelector(".chat-message-content pre");
      const contentDiv = msg.querySelector(".chat-message-content");
      if (contentDiv.classList.contains("collapsed")) {
        pre.textContent = content;
        contentDiv.classList.remove("collapsed");
        toggle.textContent = "收起";
      } else {
        pre.textContent = displayContent;
        contentDiv.classList.add("collapsed");
        toggle.textContent = "展开全文";
      }
    });
  }

  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function addSystemMessage(content) {
  addChatMessage("system", "系统", content);
}

function clearChat() {
  const container = document.querySelector("#chat-container");
  if (!container) return;
  container.innerHTML = `
    <div class="chat-welcome">
      <div class="chat-welcome-icon">✨</div>
      <h3>欢迎使用墨神</h3>
      <p>在左侧填写创意需求，点击「开始生成」后，这里会实时显示创作过程。</p>
    </div>
  `;
}

async function runApiFlowStream(payload) {
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
  state.storyId = null;
  state.chapters = [];
  state.chapterSummaries = [];
  state.continuityNotes = "";
  resetAgentStatuses();
  switchView("studio");
  startProgress("生成中", PROGRESS_PHASES);
  setRunState("生成中", "is-running");
  submitButton.disabled = true;
  submitButton.textContent = "生成中...";

  // Clear chat and show initial message
  clearChat();
  addSystemMessage("开始连接流式接口...");

  // Show stop button
  const stopButton = document.querySelector("#stop-button");
  if (stopButton) {
    stopButton.classList.remove("is-hidden");
  }

  // Create abort controller
  currentAbortController = new AbortController();

  try {
    const response = await fetch("/api/storyagents/draft/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: payload.prompt,
        genre: payload.genre,
        tone: payload.tone,
        audience: payload.audience,
        chapters: Number(payload.chapters),
      }),
      signal: currentAbortController.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let currentChapter = 0;
    let lastNode = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr);

          if (event.event === "node_complete") {
            const { node, data } = event;

            // Update agent status
            const agentIndex = NODE_TO_AGENT[node];
            if (agentIndex !== undefined) {
              setAgentStatus(agentIndex, "已完成", "done");
              const nextIndex = agentIndex + 1;
              if (nextIndex < AGENTS.length) {
                setAgentStatus(nextIndex, "工作中", "active");
              }
            }

            // Update state
            if (data.story_title) {
              state.title = data.story_title;
            }
            if (data.story_id) {
              state.storyId = data.story_id;
            }

            // Add chat message for node completion
            const nodeDesc = getNodeDescription(node);
            addChatMessage("agent", node, nodeDesc);

            // If there's a chapter draft, add it as a chapter message
            if (data.current_chapter_draft && node === "Chapter Writer") {
              const chapterIdx = data.current_chapter_index || currentChapter + 1;
              addChatMessage("chapter", `第 ${chapterIdx} 章`, data.current_chapter_draft);
              currentChapter = chapterIdx;
            }

            // Update artifacts
            if (data.story_brief) {
              state.artifacts.storyBrief = data.story_brief;
            }
            if (data.story_bible) {
              state.artifacts.world = data.story_bible;
            }
            if (data.character_sheets) {
              state.artifacts.characters = data.character_sheets;
            }
            if (data.plot_outline) {
              state.artifacts.outline = data.plot_outline;
            }
            if (data.current_chapter_draft) {
              state.artifacts.chapter = data.current_chapter_draft;
            }
            if (data.chapters && data.chapters.length > 0) {
              state.chapters = data.chapters;
              state.artifacts.manuscript = data.final_manuscript || data.chapters.join("\n\n");
            }
            if (Array.isArray(data.chapter_summaries)) {
              state.chapterSummaries = data.chapter_summaries;
            }
            if (typeof data.continuity_notes === "string" && data.continuity_notes) {
              state.continuityNotes = data.continuity_notes;
            }

            // Update progress
            const chapterIndex = data.current_chapter_index || 0;
            const targetChapters = data.target_chapters || 3;
            if (chapterIndex > 0) {
              const progress = Math.min(95, (chapterIndex / targetChapters) * 80 + 15);
              setProgress(progress, `第 ${chapterIndex}/${targetChapters} 章`);
            }

            lastNode = node;
          }

          if (event.event === "story_saved") {
            if (event.data?.story_id) {
              state.storyId = event.data.story_id;
            }
            loadHistory();
          }

          if (event.event === "story_complete") {
            finishProgress("生成完成");
            setRunState("已完成", "is-done");
            addSystemMessage("🎉 所有章节已生成完毕！");

            // Show final manuscript in chat
            if (state.artifacts.manuscript) {
              addChatMessage("chapter", "最终成稿", state.artifacts.manuscript);
            }

            Array.from(document.querySelectorAll(".agent-card")).forEach((card) => {
              if (!card.classList.contains("is-done")) {
                card.classList.add("is-done");
                card.querySelector(".agent-status").textContent = "已完成";
              }
            });

            localStorage.setItem("storyagents-h5-form", JSON.stringify(payload));
          }

          if (event.error) {
            throw new Error(event.error);
          }
        } catch (parseError) {
          console.warn("SSE parse error:", parseError);
        }
      }
    }
  } catch (error) {
    if (error.name === "AbortError") {
      addSystemMessage("⏹ 已停止生成。");
      failProgress("已停止生成");
      setRunState("已停止");
    } else {
      addSystemMessage(`❌ 生成失败：${error.message}`);
      failProgress("生成失败，请检查网络或稍后重试");
      setRunState("出错");
    }
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "重新提交";
    currentAbortController = null;

    // Hide stop button
    const stopButton = document.querySelector("#stop-button");
    if (stopButton) {
      stopButton.classList.add("is-hidden");
    }
  }
}

function getNodeDescription(node) {
  const descriptions = {
    "Planner": "已完成故事规划，确定了标题和核心设定。",
    "Outline Agent": "已完成章节大纲规划。",
    "Chapter Writer": "已完成当前章节撰写。",
    "Showrunner": "已完成章节审核和整合。",
    "Worldbuilder": "已完成世界观设定。",
    "Character Designer": "已完成角色设计。",
    "Continuity Reviewer": "已完成连续性审核。",
  };
  return descriptions[node] || "已完成处理。";
}

/* ---- Form ---- */
function readForm() {
  const formData = new FormData(form);
  return {
    prompt: String(formData.get("prompt") || "").trim(),
    genre: String(formData.get("genre") || "").trim(),
    tone: String(formData.get("tone") || "").trim(),
    audience: String(formData.get("audience") || "").trim(),
    chapters: String(formData.get("chapters") || "3"),
  };
}

function hydrateStoredForm() {
  const raw = localStorage.getItem("storyagents-h5-form");
  if (!raw) {
    return;
  }
  try {
    const data = JSON.parse(raw);
    ["prompt", "genre", "tone", "audience"].forEach((key) => {
      if (typeof data[key] === "string" && document.querySelector(`#${key}`)) {
        document.querySelector(`#${key}`).value = data[key];
      }
    });
    if (data.chapters) {
      chapterSlider.value = data.chapters;
      chapterCount.textContent = `${data.chapters} 章`;
    }
  } catch (error) {
    console.warn("保存的墨神表单解析失败", error);
  }
}

function bootstrap() {
  chapterSlider.addEventListener("input", (event) => {
    chapterCount.textContent = `${event.target.value} 章`;
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      promptInput.value = chip.dataset.prompt || "";
      promptInput.focus();
    });
  });

  // Style presets
  const presetGrid = document.querySelector("#preset-grid");
  if (presetGrid) {
    presetGrid.querySelectorAll(".preset-card").forEach((card) => {
      card.addEventListener("click", () => {
        const presetKey = card.dataset.preset;
        const preset = STYLE_PRESETS[presetKey];
        if (!preset) return;

        // Fill form fields
        document.querySelector("#genre").value = preset.genre;
        document.querySelector("#tone").value = preset.tone;
        document.querySelector("#audience").value = preset.audience;

        // Fill prompt hint if empty
        if (!promptInput.value.trim()) {
          promptInput.value = preset.prompt_hint;
        }

        // Highlight selected preset
        presetGrid.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("is-selected"));
        card.classList.add("is-selected");

        promptInput.focus();
      });
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = readForm();
    if (!payload.prompt) {
      promptInput.focus();
      return;
    }
    await runApiFlowStream(payload);
  });

  // Stop button
  const stopButton = document.querySelector("#stop-button");
  if (stopButton) {
    stopButton.addEventListener("click", () => {
      if (currentAbortController) {
        currentAbortController.abort();
      }
    });
  }

  // Clear chat button
  const clearChatBtn = document.querySelector("#clear-chat");
  if (clearChatBtn) {
    clearChatBtn.addEventListener("click", clearChat);
  }

  renderAgentCards();
  renderArtifactTabs();
  renderArtifactContent();
  resetLog();
  resetProgress();
  hydrateStoredForm();
  loadHistory();
  initEditToolbar();
  document.body.dataset.bootstrap = "ready";
}

/* ---- History ---- */

async function loadHistory() {
  const list = document.querySelector("#history-list");
  if (!list) return;
  list.innerHTML = "<p style='color:var(--text-tertiary);font-size:0.85rem'>正在加载历史记录...</p>";
  try {
    const res = await fetch("/api/storyagents/stories");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const stories = await res.json();
    renderHistory(stories);
  } catch (e) {
    list.innerHTML = "<p style='color:var(--text-tertiary);font-size:0.85rem'>无法加载历史记录</p>";
  }
}

function renderHistory(stories) {
  const list = document.querySelector("#history-list");
  if (!stories.length) {
    list.innerHTML = "<p style='color:var(--text-tertiary);font-size:0.85rem'>还没有创作记录，快去生成一篇吧。</p>";
    return;
  }
  list.innerHTML = "";
  stories.forEach((s) => {
    const card = document.createElement("div");
    card.className = "history-card";
    card.innerHTML = `
      <div class="history-card-head">
        <h3>${escapeHtml(s.title || "未命名")}</h3>
        <span>${s.created_at || ""}</span>
      </div>
      <p class="history-prompt">${escapeHtml(s.prompt || "").slice(0, 80)}</p>
      <div class="history-card-footer">
        <div class="history-meta">
          <span>${escapeHtml(s.genre || "")}</span>
          <span>${s.chapters || 0} 章</span>
        </div>
        <div class="history-actions">
          <button class="history-act-btn" data-action="view" data-id="${s.id}" type="button">查看</button>
          <button class="history-act-btn" data-action="continue" data-id="${s.id}" type="button">续写</button>
          <button class="history-act-btn" data-action="export" data-id="${s.id}" type="button">导出</button>
          <button class="history-act-btn history-act-delete" data-action="delete" data-id="${s.id}" type="button">删除</button>
        </div>
      </div>
    `;
    list.appendChild(card);
  });

  list.querySelectorAll(".history-act-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const action = btn.dataset.action;
      const id = btn.dataset.id;
      if (action === "view") loadStory(id);
      else if (action === "continue") continueStory(id);
      else if (action === "delete") deleteStory(id);
      else if (action === "export") exportStory(id);
    });
  });
}

async function loadStory(id) {
  try {
    const res = await fetch(`/api/storyagents/stories/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error("Not found");
    const data = await res.json();

    const manuscript = data.final_manuscript || data.current_chapter_draft || "暂无成稿内容。";
    const title = data.story_title || "未命名故事";

    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    const modal = document.createElement("div");
    modal.className = "modal";
    modal.innerHTML = `
      <div class="modal-head">
        <h2>${escapeHtml(title)}</h2>
        <button class="modal-close" type="button">&times;</button>
      </div>
      <div class="modal-body">
        <pre>${escapeHtml(manuscript)}</pre>
      </div>
      <div class="modal-footer">
        <button class="export-btn" type="button" data-action="export-txt">导出 TXT</button>
        <button class="export-btn" type="button" data-action="export-docx">导出 DOCX</button>
      </div>
    `;

    modal.querySelector(".modal-close").addEventListener("click", () => overlay.remove());
    modal.querySelector('[data-action="export-txt"]').addEventListener("click", () => {
      const safeName = title.replace(/[\\/*?:"<>|]/g, "").slice(0, 60) || "story";
      const blob = new Blob([manuscript], { type: "text/plain;charset=utf-8" });
      triggerDownload(blob, `${safeName}.txt`);
    });
    modal.querySelector('[data-action="export-docx"]').addEventListener("click", async () => {
      const { Document, Paragraph, TextRun, Packer, HeadingLevel, AlignmentType } = docx;
      const lines = manuscript.split("\n");
      const children = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) { children.push(new Paragraph({ text: "" })); continue; }
        const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)/);
        if (headingMatch) {
          const level = headingMatch[1].length === 1 ? HeadingLevel.HEADING_1
            : headingMatch[1].length === 2 ? HeadingLevel.HEADING_2
            : HeadingLevel.HEADING_3;
          children.push(new Paragraph({
            heading: level,
            alignment: level === HeadingLevel.HEADING_1 ? AlignmentType.CENTER : AlignmentType.LEFT,
            children: [new TextRun({ text: headingMatch[2], bold: true, font: "Microsoft YaHei" })],
          }));
        } else {
          children.push(new Paragraph({
            children: [new TextRun({ text: trimmed, font: "Microsoft YaHei", size: 24 })],
            spacing: { line: 360 },
          }));
        }
      }
      const doc = new Document({ sections: [{ children }] });
      const blob = await Packer.toBlob(doc);
      const safeName = title.replace(/[\\/*?:"<>|]/g, "").slice(0, 60) || "story";
      triggerDownload(blob, `${safeName}.docx`);
    });

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  } catch (e) {
    alert("加载失败：" + e.message);
  }
}

async function deleteStory(id) {
  if (!confirm("确定要删除这个故事吗？删除后无法恢复。")) return;
  try {
    const res = await fetch(`/api/storyagents/stories/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    loadHistory();
  } catch (e) {
    pushLog("删除失败", "无法删除故事：" + e.message);
  }
}

async function exportStory(id) {
  loadStory(id);
}

async function continueStory(id) {
  const continueChapters = prompt("请输入续写章节数（1-12）：", "3");
  if (!continueChapters) return;

  const chapters = parseInt(continueChapters, 10);
  if (isNaN(chapters) || chapters < 1 || chapters > 12) {
    alert("请输入有效的章节数（1-12）");
    return;
  }

  // Switch to studio view
  switchView("studio");
  state.storyId = id;
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
  state.chapters = [];
  state.chapterSummaries = [];
  state.continuityNotes = "";
  renderArtifactTabs();
  renderArtifactContent();
  resetAgentStatuses();
  resetLog();
  startProgress("正在续写小说", PROGRESS_PHASES);
  setRunState("续写中", "is-running");

  pushLog("开始续写", `正在续写故事，计划生成 ${chapters} 章...`);

  try {
    const response = await fetch("/api/storyagents/continue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        story_id: id,
        continue_chapters: chapters,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // Read SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let currentChapter = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const event = JSON.parse(jsonStr);

          if (event.event === "node_complete") {
            const { node, data } = event;

            // Update agent status
            const agentIndex = NODE_TO_AGENT[node];
            if (agentIndex !== undefined) {
              setAgentStatus(agentIndex, "已完成", "done");
              const nextIndex = agentIndex + 1;
              if (nextIndex < AGENTS.length) {
                setAgentStatus(nextIndex, "工作中", "active");
              }
            }

            // Update artifacts
            if (data.story_title) {
              state.title = data.story_title;
            }
            if (data.story_id) {
              state.storyId = data.story_id;
            }
            if (data.current_chapter_draft) {
              state.artifacts.chapter = data.current_chapter_draft;
            }
            if (data.chapters && data.chapters.length > 0) {
              state.chapters = data.chapters;
              state.artifacts.manuscript = data.final_manuscript || data.chapters.join("\n\n");
            }
            if (Array.isArray(data.chapter_summaries)) {
              state.chapterSummaries = data.chapter_summaries;
            }
            if (typeof data.continuity_notes === "string" && data.continuity_notes) {
              state.continuityNotes = data.continuity_notes;
            }

            // Update progress
            const chapterIndex = data.current_chapter_index || 0;
            const targetChapters = data.target_chapters || chapters;
            if (chapterIndex > currentChapter) {
              currentChapter = chapterIndex;
              const progress = Math.min(95, (currentChapter / targetChapters) * 80 + 15);
              setProgress(progress, `正在续写第 ${currentChapter}/${targetChapters} 章...`);
            }

            pushLog(`${node} 完成`, getNodeDescription(node));
            renderArtifactTabs();
            renderArtifactContent();
          }

          if (event.event === "story_complete") {
            finishProgress("续写完成");
            setRunState("已完成", "is-done");
            pushLog("续写完成", "所有续写章节已生成完毕！");

            Array.from(document.querySelectorAll(".agent-card")).forEach((card) => {
              if (!card.classList.contains("is-done")) {
                card.classList.add("is-done");
                card.querySelector(".agent-status").textContent = "已完成";
              }
            });
          }

          if (event.error) {
            throw new Error(event.error);
          }
        } catch (parseError) {
          console.warn("SSE parse error:", parseError);
        }
      }
    }
  } catch (error) {
    pushLog("续写失败", `续写失败：${error.message}`);
    failProgress("续写失败，请检查网络或稍后重试");
    setRunState("出错");
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ---- Edit Toolbar ---- */
let selectedText = "";
let selectedRange = null;

function initEditToolbar() {
  const toolbar = document.querySelector("#edit-toolbar");
  const editModalOverlay = document.querySelector("#edit-modal-overlay");
  const editModalClose = document.querySelector("#edit-modal-close");
  const editCancelBtn = document.querySelector("#edit-cancel-btn");
  const editApplyBtn = document.querySelector("#edit-apply-btn");

  if (!toolbar) return;

  // Listen for text selection
  document.addEventListener("mouseup", (e) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();

    // Check if selection is within artifact content
    const artifactContent = document.querySelector("#artifact-content");
    if (!artifactContent || !artifactContent.contains(e.target)) {
      if (!toolbar.contains(e.target)) {
        toolbar.classList.add("is-hidden");
      }
      return;
    }

    if (text.length > 10) {
      selectedText = text;
      selectedRange = selection.getRangeAt(0).cloneRange();

      // Position toolbar near selection
      const rect = selectedRange.getBoundingClientRect();
      toolbar.style.top = `${rect.top - 50 + window.scrollY}px`;
      toolbar.style.left = `${rect.left + rect.width / 2 - 150}px`;
      toolbar.classList.remove("is-hidden");
    } else {
      if (!toolbar.contains(e.target)) {
        toolbar.classList.add("is-hidden");
      }
    }
  });

  // Edit button click
  toolbar.querySelectorAll(".edit-btn[data-action]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.action;
      if (!selectedText) return;

      toolbar.classList.add("is-hidden");

      // Show loading state
      pushLog("编辑中", `正在进行${getActionName(action)}...`);

      try {
        const response = await fetch("/api/storyagents/edit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: selectedText,
            action: action,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        // Show edit result modal
        showEditResultModal(selectedText, result, action);
      } catch (error) {
        pushLog("编辑失败", `编辑操作失败：${error.message}`);
      }
    });
  });

  // Close toolbar
  const closeBtn = toolbar.querySelector(".edit-btn-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      toolbar.classList.add("is-hidden");
    });
  }

  // Close edit modal
  if (editModalClose) {
    editModalClose.addEventListener("click", () => {
      editModalOverlay.classList.add("is-hidden");
    });
  }
  if (editCancelBtn) {
    editCancelBtn.addEventListener("click", () => {
      editModalOverlay.classList.add("is-hidden");
    });
  }

  // Apply edit
  if (editApplyBtn) {
    editApplyBtn.addEventListener("click", async () => {
      const ok = await applyEditResult();
      if (ok !== false) {
        editModalOverlay.classList.add("is-hidden");
      }
    });
  }
}

let currentEditResult = null;

function showEditResultModal(original, result, action) {
  const overlay = document.querySelector("#edit-modal-overlay");
  const actionLabel = document.querySelector("#edit-action-label");
  const changesSummary = document.querySelector("#edit-changes-summary");
  const resultText = document.querySelector("#edit-result-text");
  const originalText = document.querySelector("#edit-original-text");

  if (!overlay) return;

  currentEditResult = { original, result, action };

  actionLabel.textContent = getActionName(action);
  changesSummary.textContent = result.changes_summary || "";
  resultText.textContent = result.edited_text || "";
  originalText.textContent = original;

  overlay.classList.remove("is-hidden");
}

function applyEditResult() {
  if (!currentEditResult || !selectedRange) return;

  const { result } = currentEditResult;
  const editedText = result.edited_text;

  if (!editedText) return;

  // Replace selected text with edited text
  selectedRange.deleteContents();
  selectedRange.insertNode(document.createTextNode(editedText));

  // Clear selection
  selectedText = "";
  selectedRange = null;
  currentEditResult = null;

  pushLog("编辑完成", "已应用编辑结果。");
}

async function applyEditResult() {
  if (!currentEditResult) return false;

  const { original, result } = currentEditResult;
  const editedText = result.edited_text;

  if (!editedText) return false;

  const activeKey = state.activeArtifact;
  const currentContent = state.artifacts[activeKey];
  if (typeof currentContent !== "string") {
    return false;
  }

  const updatedContent = replaceFirstOccurrence(currentContent, original, editedText);
  if (updatedContent === currentContent) {
    return false;
  }

  state.artifacts[activeKey] = updatedContent;

  if (activeKey === "chapter") {
    if (Array.isArray(state.chapters) && state.chapters.length > 0) {
      const nextChapters = state.chapters.slice();
      const lastIndex = nextChapters.length - 1;
      nextChapters[lastIndex] = replaceFirstOccurrence(nextChapters[lastIndex], original, editedText);
      state.chapters = nextChapters;
    }
    if (typeof state.artifacts.manuscript === "string") {
      state.artifacts.manuscript = replaceFirstOccurrence(
        state.artifacts.manuscript,
        original,
        editedText,
      );
    }
  }

  if (activeKey === "manuscript" && Array.isArray(state.chapters) && state.chapters.length > 0) {
    const nextChapters = state.chapters.slice();
    const lastIndex = nextChapters.length - 1;
    nextChapters[lastIndex] = replaceFirstOccurrence(nextChapters[lastIndex], original, editedText);
    state.chapters = nextChapters;
  }

  try {
    await persistCurrentStory();
    renderArtifactContent();
    loadHistory();
    pushLog("编辑完成", "修改已经写回当前故事。");
  } catch (error) {
    pushLog("保存失败", `编辑已应用但保存失败：${error.message}`);
    return false;
  } finally {
    selectedText = "";
    selectedRange = null;
    currentEditResult = null;
  }

  return true;
}

function getActionName(action) {
  const names = {
    rewrite: "改写",
    expand: "扩写",
    compress: "缩写",
    polish: "润色",
  };
  return names[action] || action;
}

const refreshHistoryBtn = document.querySelector("#refresh-history");
if (refreshHistoryBtn) {
  refreshHistoryBtn.addEventListener("click", loadHistory);
}

try {
  bootstrap();
  initScrollAnimations();
} catch (error) {
  console.error(error);
  document.body.dataset.bootstrap = "failed";
  const banner = document.createElement("div");
  banner.className = "boot-error";
  banner.textContent = `前端启动失败：${error.message}`;
  document.body.prepend(banner);
}

/* ---- Scroll Animations (Apple-style) ---- */
function initScrollAnimations() {
  // Enable animations only when JS is ready
  document.body.classList.add("anim-ready");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target); // Only animate once
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  function observeElements(container) {
    const selector = ".anim-fade-up, .anim-scale-in, .anim-blur-in, .anim-slide-left, .anim-slide-right";
    const elements = container
      ? container.querySelectorAll(selector)
      : document.querySelectorAll(selector);
    elements.forEach((el) => observer.observe(el));
  }

  // Observe all elements on load
  observeElements();

  // Trigger animations for elements already in viewport (like homepage)
  setTimeout(() => {
    const homeElements = document.querySelectorAll(
      "#view-home .anim-fade-up, #view-home .anim-scale-in, #view-home .anim-blur-in, #view-home .anim-slide-left, #view-home .anim-slide-right"
    );
    homeElements.forEach((el) => el.classList.add("is-visible"));
  }, 100);

  // Re-observe when switching views
  const originalSwitchView = switchView;
  switchView = function (viewName) {
    originalSwitchView(viewName);
    setTimeout(() => {
      // Reset animations for the new view
      const view = document.querySelector(`#view-${viewName}`);
      if (!view) return;

      view.querySelectorAll(
        ".anim-fade-up, .anim-scale-in, .anim-blur-in, .anim-slide-left, .anim-slide-right"
      ).forEach((el) => {
        el.classList.remove("is-visible");
      });

      // Trigger animations after a brief delay
      setTimeout(() => {
        view.querySelectorAll(
          ".anim-fade-up, .anim-scale-in, .anim-blur-in, .anim-slide-left, .anim-slide-right"
        ).forEach((el) => {
          el.classList.add("is-visible");
        });
      }, 50);
    }, 50);
  };
}
