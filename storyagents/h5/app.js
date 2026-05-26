const AGENTS = [
  { name: "策划编辑", role: "把你的灵感压缩成一份明确、可执行的创作需求。" },
  { name: "剧情架构师", role: "生成章节节拍，确保故事持续前进。" },
  { name: "章节写手", role: "扩写为正文，让人物真正开口与行动。" },
  { name: "总编", role: "最终拍板，决定通过、续章或返工。" },
];

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

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === viewName);
  });
  document.querySelectorAll(".topbar-item").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === viewName);
  });
}

document.querySelectorAll(".nav-item, .topbar-item").forEach((btn) => {
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
    title: data.story_title || "《未命名故事》",
    storyBrief: data.story_brief || "",
    world: data.story_bible || "",
    characters: data.character_sheets || "",
    outline: data.plot_outline || "",
    chapter: chapters[chapters.length - 1] || data.current_chapter_draft || "",
    manuscript: data.final_manuscript || "",
    chapters,
  };
}

async function runApiFlow(payload) {
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
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
    state.title = normalized.title;
    state.artifacts = {
      storyBrief: normalized.storyBrief,
      world: normalized.world,
      characters: normalized.characters,
      outline: normalized.outline,
      chapter: normalized.chapter,
      manuscript: normalized.manuscript,
    };

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

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = readForm();
    if (!payload.prompt) {
      promptInput.focus();
      return;
    }
    await runApiFlow(payload);
  });

  renderAgentCards();
  renderArtifactTabs();
  renderArtifactContent();
  resetLog();
  resetProgress();
  hydrateStoredForm();
  loadHistory();
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

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

const refreshHistoryBtn = document.querySelector("#refresh-history");
if (refreshHistoryBtn) {
  refreshHistoryBtn.addEventListener("click", loadHistory);
}

try {
  bootstrap();
} catch (error) {
  console.error(error);
  document.body.dataset.bootstrap = "failed";
  const banner = document.createElement("div");
  banner.className = "boot-error";
  banner.textContent = `前端启动失败：${error.message}`;
  document.body.prepend(banner);
}
