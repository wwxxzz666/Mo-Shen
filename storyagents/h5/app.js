const AGENTS = [
  { name: "策划编辑", role: "把你的灵感压缩成一份明确、可执行的创作需求。" },
  { name: "剧情架构师", role: "生成章节节拍，确保故事持续前进。" },
  { name: "章节写手", role: "扩写为正文，让人物真正开口与行动。" },
  { name: "总编", role: "最终拍板，决定通过、续章或返工。" },
];

const AGENT_LIBRARY = {
  "Planner": { name: "策划编辑", role: "把你的灵感压缩成一份明确、可执行的创作需求。" },
  "Worldbuilder": { name: "世界观设计师", role: "补齐世界规则、氛围母题和叙事约束，让故事更稳。" },
  "Character Designer": { name: "角色设计师", role: "整理主角弧线、关系张力和人物说话方式。" },
  "Outline Agent": { name: "剧情架构师", role: "生成章节节拍，确保故事持续向前推进。" },
  "Chapter Writer": { name: "章节写手", role: "扩写为正文，让人物真正开口与行动。" },
  "Continuity Reviewer": { name: "连续性审校", role: "检查设定、人设和伏笔是否前后一致。" },
  "Showrunner": { name: "总编", role: "最后拍板，决定通过、返工或继续打磨。" },
};

const WORKFLOW_MODES = {
  quick: {
    label: "灵感工坊",
    chip: "4 节点",
    summary: "直接从 brief 到章节出稿，适合试题材、试节奏和快速起篇。",
    logIntro: "当前是「快速出稿」模式，会走四段式创作流程，优先把故事尽快成形。",
    agents: ["Planner", "Outline Agent", "Chapter Writer", "Showrunner"],
    artifacts: ["storyBrief", "outline", "chapter", "manuscript"],
    limits: { maxChapters: null, maxChapterLength: 5000, maxContinuationChapters: 3, maxContinuations: 2 },
    phases: [
      { label: "正在整理创作需求...", target: 16 },
      { label: "正在规划章节大纲...", target: 42 },
      { label: "正在撰写正文初稿...", target: 78 },
      { label: "正在收束并生成成稿...", target: 96 },
    ],
  },
  standard: {
    label: "故事工坊",
    chip: "6 节点",
    summary: "补齐世界观和角色层，再进入大纲与正文，更适合中篇和稳定连载。",
    logIntro: "当前是「标准创作」模式，会先补设定和角色，再推进大纲与正文。",
    agents: ["Planner", "Worldbuilder", "Character Designer", "Outline Agent", "Chapter Writer", "Showrunner"],
    artifacts: ["storyBrief", "world", "characters", "outline", "chapter", "manuscript"],
    limits: { maxChapters: null, maxChapterLength: 5000, maxContinuationChapters: 5, maxContinuations: 2 },
    phases: [
      { label: "正在整理创作需求...", target: 12 },
      { label: "正在扩展世界观与角色设定...", target: 38 },
      { label: "正在规划章节大纲...", target: 62 },
      { label: "正在撰写正文初稿...", target: 86 },
      { label: "正在汇总并整理成稿...", target: 96 },
    ],
  },
  deep: {
    label: "长篇工坊",
    chip: "7 节点",
    summary: "在标准模式上加入连续性审校，更适合长篇、伏笔密集和一致性要求高的项目。",
    logIntro: "当前是「深度打磨」模式，会额外加入连续性审校，优先保证人设与设定稳定。",
    agents: ["Planner", "Worldbuilder", "Character Designer", "Outline Agent", "Chapter Writer", "Continuity Reviewer", "Showrunner"],
    artifacts: ["storyBrief", "world", "characters", "outline", "chapter", "manuscript"],
    limits: { maxChapters: null, maxChapterLength: 5000, maxContinuationChapters: null, maxContinuations: null },
    phases: [
      { label: "正在整理创作需求...", target: 10 },
      { label: "正在扩展世界观与角色设定...", target: 34 },
      { label: "正在规划章节大纲...", target: 58 },
      { label: "正在撰写正文初稿...", target: 80 },
      { label: "正在进行连续性审校...", target: 92 },
      { label: "正在整理最终成稿...", target: 96 },
    ],
  },
};

const MODE_PRESETS = {
  quick: [
    { label: "灵感速写", tag: "15 MIN", genre: "都市 / 短篇", tone: "轻快、直接、有画面感", audience: "全年龄", prompt: "写一个三幕结构的短篇故事，用一个强烈场景快速建立人物、冲突和结尾反转。" },
    { label: "悬念开场", tag: "HOOK FIRST", genre: "悬疑 / 推理", tone: "冷静、紧张、节奏明快", audience: "成年向", prompt: "写一个以神秘事件开场的短篇悬疑故事，第一段就抛出问题，并在结尾留下钩子。" },
    { label: "一章试读", tag: "PILOT", genre: "科幻 / 近未来", tone: "克制、锋利、带科技感", audience: "成年向", prompt: "写一章适合作为长篇试读的科幻故事，突出主角、世界规则和一个必须立刻解决的危机。" },
  ],
  standard: [
    { label: "连载起稿", tag: "SERIES", genre: "都市 / 成长", tone: "细腻、稳定、带情绪推进", audience: "全年龄", prompt: "规划一部适合连载的成长故事，先建立人物关系和日常世界，再逐步引出主线冲突。" },
    { label: "世界观搭建", tag: "WORLD BUILD", genre: "奇幻 / 冒险", tone: "宏大、清晰、富有探索感", audience: "全年龄", prompt: "构建一个规则明确的奇幻世界，设计势力、资源、禁忌和主角必须承担的使命。" },
    { label: "人物群像", tag: "ENSEMBLE", genre: "现实 / 群像", tone: "真实、克制、关系复杂", audience: "成年向", prompt: "创作一组彼此牵动的角色，让每个人都有独立目标，并通过共同事件推动关系变化。" },
  ],
  deep: [
    { label: "长篇工程", tag: "LONG FORM", genre: "史诗 / 奇幻", tone: "厚重、沉浸、伏笔密集", audience: "成年向", prompt: "设计一部多线并进的长篇故事，建立历史、阵营、人物弧光与可回收的长期伏笔。" },
    { label: "连续性审校", tag: "CANON CHECK", genre: "悬疑 / 长篇", tone: "严谨、压迫、逻辑导向", audience: "成年向", prompt: "创作一个线索密集的长篇悬疑项目，明确时间线、证据链、人物动机和真相揭示节奏。" },
    { label: "多线叙事", tag: "MULTI-THREAD", genre: "科幻 / 社会寓言", tone: "冷峻、复杂、具有思辨性", audience: "成年向", prompt: "构建一个多视角科幻故事，让不同角色面对同一系统危机，并在最终章节汇合各条叙事线。" },
  ],
};

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
  mode: "quick",
  chapters: [],
  chapterSummaries: [],
  continuityNotes: "",
  targetChapterLength: 1500,
  taskId: null,
  taskCursor: 0,
  taskStatus: "idle",
  previewConfirmed: false,
};

const form = document.querySelector("#story-form");
const promptInput = document.querySelector("#prompt");
const chapterSlider = document.querySelector("#chapters");
const chapterCount = document.querySelector("#chapter-count");
const chapterLengthSlider = document.querySelector("#chapter-length");
const chapterLengthCount = document.querySelector("#chapter-length-count");
const modeGrid = document.querySelector("#mode-grid");
const modeSummary = document.querySelector("#mode-summary");
const modePresets = document.querySelector("#mode-presets");
const modePresetsHint = document.querySelector("#mode-presets-hint");
const chips = Array.from(document.querySelectorAll(".chip"));
const submitButton = document.querySelector("#submit-button");
const previewButton = document.querySelector("#preview-button");
const stylePreview = document.querySelector("#style-preview");
const stylePreviewText = document.querySelector("#style-preview-text");
const retryPreviewButton = document.querySelector("#retry-preview-button");
const confirmPreviewButton = document.querySelector("#confirm-preview-button");
const outlineGate = document.querySelector("#outline-gate");
const outlineGateContent = document.querySelector("#outline-gate-content");
const approveOutlineButton = document.querySelector("#approve-outline-button");
const runState = document.querySelector("#run-state");
const agentList = document.querySelector("#agent-list");
const artifactTabs = document.querySelector("#artifact-tabs");
const artifactContent = document.querySelector("#artifact-content");
const activityLog = document.querySelector("#activity-log");
const workflowGraph = document.querySelector("#workflow-graph");
const topbarStreamText = document.querySelector("#topbar-stream-text");
const mapStatusText = document.querySelector("#map-status-text");
const agentCardTemplate = document.querySelector("#agent-card-template");
const progressPanel = document.querySelector("#progress-panel");
const progressFill = document.querySelector("#progress-fill");
const progressPercent = document.querySelector("#progress-percent");
const progressStage = document.querySelector("#progress-stage");
const progressTitle = document.querySelector("#progress-title");

let progressTimer = null;
let progressValue = 0;

function normalizeWorkflowMode(mode) {
  return Object.prototype.hasOwnProperty.call(WORKFLOW_MODES, mode) ? mode : "quick";
}

function getWorkflowConfig(mode = state.mode) {
  return WORKFLOW_MODES[normalizeWorkflowMode(mode)];
}

function getActiveAgents(mode = state.mode) {
  return getWorkflowConfig(mode).agents.map((node) => ({ node, ...AGENT_LIBRARY[node] }));
}

function getNodeToAgentMap(mode = state.mode) {
  return getWorkflowConfig(mode).agents.reduce((acc, node, index) => {
    acc[node] = index;
    return acc;
  }, {});
}

function getVisibleArtifactDefs(mode = state.mode) {
  const visibleKeys = new Set(getWorkflowConfig(mode).artifacts);
  return ARTIFACT_DEFS.filter((artifact) => visibleKeys.has(artifact.key));
}

const STUDIO_COPY = {
  quick: {
    kicker: "灵感工坊 / QUICK",
    title: "把一个想法，快速变成故事",
    description: "适合试题材、试风格和快速起稿。只要写下你的核心想法，智能体会直接推进到可读初稿。",
    promptTitle: "故事需求 / 大纲",
    promptHint: "写下人物、场景、冲突、结局方向，或任何还没成形的想法。",
    placeholder: "例如：一个失去记忆的剑客，在暴雨夜收到一封来自未来的信……",
  },
  standard: {
    kicker: "故事工坊 / STANDARD",
    title: "先搭好故事，再开始写",
    description: "适合中篇和稳定连载。智能体会先补齐世界、角色与大纲，再进入章节创作。",
    promptTitle: "故事需求 / 大纲",
    promptHint: "描述你想讲的故事，以及你希望读者记住的核心冲突。",
    placeholder: "例如：一座只在午夜出现的城市，收留所有不愿醒来的人……",
  },
  deep: {
    kicker: "长篇工坊 / DEEP",
    title: "让复杂的长篇，保持清晰",
    description: "适合长篇、群像和伏笔密集的项目。智能体会增加连续性审校，持续维护设定和人物弧线。",
    promptTitle: "故事需求 / 大纲",
    promptHint: "尽量写清楚世界规则、人物关系、主线冲突和你想埋下的长期伏笔。",
    placeholder: "例如：在被海水淹没的记忆城，七个阵营争夺最后一枚真实的记忆……",
  },
};

function updateStudioCopy() {
  const copy = STUDIO_COPY[normalizeWorkflowMode(state.mode)];
  if (!copy) return;
  const header = document.querySelector(".studio-left-panel .panel-header");
  header?.querySelector(".panel-kicker")?.replaceChildren(copy.kicker);
  header?.querySelector(".panel-title")?.replaceChildren(copy.title);
  const description = document.querySelector("#studio-description");
  if (description) description.textContent = copy.description;
  const promptSection = promptInput?.closest(".panel-section");
  promptSection?.querySelector(".section-title")?.replaceChildren(copy.promptTitle);
  promptInput?.setAttribute("placeholder", copy.placeholder);
  const oldSummary = document.querySelector("#mode-summary");
  if (oldSummary) oldSummary.textContent = copy.description;
  const hint = promptSection?.querySelector(".section-caption");
  if (hint) hint.textContent = copy.promptHint;
}

function showStudioRunView(isRunning) {
  document.body.classList.toggle("is-running", isRunning);
  document.querySelector(".studio-layout")?.classList.toggle("is-run-view", isRunning);
  document.querySelector("#studio-setup-view")?.classList.toggle("is-hidden", isRunning);
  document.querySelector("#studio-run-view")?.classList.toggle("is-hidden", !isRunning);
  document.querySelector("#workflow-map-panel")?.classList.toggle("is-hidden", !isRunning);
  document.querySelector("#studio-chat-shell")?.classList.toggle("is-hidden", !isRunning);
  document.querySelector("#studio-output")?.classList.toggle("is-hidden", !isRunning);
  if (!isRunning) document.querySelector("#artifact-panel")?.classList.add("is-collapsed");
}

function openStudio(mode, { updateHash = true } = {}) {
  setWorkflowMode(mode, { rerenderAgents: true, rerenderArtifacts: true, resetActivityHint: true });
  showStudioRunView(false);
  switchView("studio");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (updateHash) window.history.replaceState(null, "", `#studio/${normalizeWorkflowMode(mode)}`);
}

function updateWorkflowModeUi() {
  const mode = normalizeWorkflowMode(state.mode);
  const config = getWorkflowConfig(mode);
  updateStudioCopy();
  applyWorkshopLimits(config);
  if (modeSummary) {
    modeSummary.textContent = `${config.label} · ${config.summary}`;
  }
  if (modeGrid) {
    modeGrid.querySelectorAll(".mode-card").forEach((card) => {
      const isActive = card.dataset.mode === mode;
      card.classList.toggle("is-selected", isActive);
      const input = card.querySelector('input[type="radio"]');
      if (input) {
        input.checked = isActive;
      }
    });
  }
}

function applyWorkshopLimits(config) {
  const limits = config.limits;
  if (chapterSlider && chapterCount) {
    const requested = Math.max(1, Number(chapterSlider.value) || 1);
    const chapters = limits.maxChapters ? Math.min(requested, limits.maxChapters) : requested;
    chapterSlider.value = String(chapters);
    if (limits.maxChapters) {
      chapterSlider.max = String(limits.maxChapters);
      chapterSlider.title = `最多 ${limits.maxChapters} 章`;
      chapterCount.textContent = `${chapters} 章 · 最多 ${limits.maxChapters} 章`;
    } else {
      chapterSlider.removeAttribute("max");
      chapterSlider.title = "章节数不设上限";
      chapterCount.textContent = `${chapters} 章 · 不设上限`;
    }
  }

  if (chapterLengthSlider && chapterLengthCount) {
    const requested = Math.max(300, Number(chapterLengthSlider.value) || 1500);
    const length = Math.min(requested, limits.maxChapterLength);
    chapterLengthSlider.max = String(limits.maxChapterLength);
    chapterLengthSlider.value = String(length);
    chapterLengthSlider.title = `每章最多 ${limits.maxChapterLength} 字`;
    chapterLengthCount.textContent = `${length} 字 · 最多 ${limits.maxChapterLength} 字`;
  }
}

function renderModePresets() {
  if (!modePresets) return;
  const mode = normalizeWorkflowMode(state.mode);
  const presets = MODE_PRESETS[mode] || [];
  modePresets.innerHTML = "";
  if (modePresetsHint) {
    modePresetsHint.textContent = `${getWorkflowConfig(mode).label} · 选择一个固定方案快速开始`;
  }
  presets.forEach((preset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mode-preset-card";
    button.innerHTML = `<span class="mode-preset-tag">${preset.tag}</span><strong>${preset.label}</strong><small>${preset.genre} · ${preset.tone}</small>`;
    button.addEventListener("click", () => {
      const genre = document.querySelector("#genre");
      const tone = document.querySelector("#tone");
      const audience = document.querySelector("#audience");
      if (genre) genre.value = preset.genre;
      if (tone) tone.value = preset.tone;
      if (audience) audience.value = preset.audience;
      if (promptInput) {
        promptInput.value = preset.prompt;
        promptInput.focus();
      }
      modePresets.querySelectorAll(".mode-preset-card").forEach((card) => card.classList.remove("is-selected"));
      button.classList.add("is-selected");
    });
    modePresets.appendChild(button);
  });
}

function setWorkflowMode(mode, options = {}) {
  const {
    rerenderAgents = false,
    rerenderArtifacts = false,
    resetActivityHint = false,
  } = options;
  state.mode = normalizeWorkflowMode(mode);
  updateWorkflowModeUi();
  renderModePresets();
  if (rerenderAgents) {
    renderAgentCards();
    resetAgentStatuses();
  }
  if (rerenderArtifacts) {
    renderArtifactTabs();
    renderArtifactContent();
  }
  if (resetActivityHint) {
    resetLog();
  }
}

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
  if (viewName !== "studio") document.body.classList.remove("is-running");

  document.querySelectorAll(".topbar-item").forEach((btn) => {
    const isStudio = viewName === "studio" && btn.dataset.studioMode === normalizeWorkflowMode(state.mode);
    const isLegacyStudio = btn.dataset.view === "studio" && !btn.dataset.studioMode;
    btn.classList.toggle("is-active", isStudio || (!isLegacyStudio && !btn.dataset.studioMode && btn.dataset.view === viewName));
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

document.querySelectorAll("[data-studio-mode]").forEach((el) => {
  el.addEventListener("click", () => openStudio(el.dataset.studioMode));
});

function openStudioFromHash() {
  const match = window.location.hash.match(/^#studio\/(quick|standard|deep)$/);
  if (match) openStudio(match[1], { updateHash: false });
}

window.addEventListener("hashchange", openStudioFromHash);

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
  if (workflowGraph) workflowGraph.innerHTML = "";
  getActiveAgents().forEach((agent, index) => {
    const fragment = agentCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".agent-card");
    card.dataset.agent = agent.node;
    fragment.querySelector(".agent-index").textContent = String(index + 1).padStart(2, "0");
    fragment.querySelector(".agent-name").textContent = agent.name;
    fragment.querySelector(".agent-role").textContent = agent.role;
    agentList.appendChild(fragment);

    if (workflowGraph) {
      if (index > 0) {
        const link = document.createElement("span");
        link.className = "workflow-link";
        workflowGraph.appendChild(link);
      }
      const node = document.createElement("div");
      node.className = "workflow-node";
      node.dataset.agent = agent.node;
      node.innerHTML = `<span class="workflow-node-index">${String(index + 1).padStart(2, "0")}</span><strong>${agent.name}</strong><small>${agent.node}</small>`;
      workflowGraph.appendChild(node);
    }
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
  const agent = getActiveAgents()[index];
  const graphNode = agent && workflowGraph?.querySelector(`[data-agent="${CSS.escape(agent.node)}"]`);
  if (graphNode) {
    graphNode.classList.toggle("is-active", className === "active");
    graphNode.classList.toggle("is-done", className === "done");
  }
  if (mapStatusText && className === "active") mapStatusText.textContent = "RUNNING";
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
  if (topbarStreamText) topbarStreamText.textContent = `${title} // ${message}`;
}

function resetLog() {
  activityLog.innerHTML = "";
  pushLog("系统就绪", getWorkflowConfig().logIntro);
}

/* ---- Artifacts ---- */
function renderArtifactTabs() {
  const visibleArtifacts = getVisibleArtifactDefs();
  if (state.artifacts.manuscript) {
    state.activeArtifact = "manuscript";
  }
  if (!visibleArtifacts.some((artifact) => artifact.key === state.activeArtifact)) {
    state.activeArtifact = visibleArtifacts[0]?.key || "storyBrief";
  }
  artifactTabs.innerHTML = "";
  visibleArtifacts.forEach((artifact) => {
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
  const visibleArtifacts = getVisibleArtifactDefs();
  const active = visibleArtifacts.find((item) => item.key === state.activeArtifact) || visibleArtifacts[0];
  if (!active) {
    artifactContent.innerHTML = "";
    return;
  }
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
  if (mapStatusText) {
    mapStatusText.textContent = className === "is-running" ? "RUNNING" : className === "is-done" ? "COMPLETE" : "STANDBY";
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
    workflowMode: normalizeWorkflowMode(data.workflow_mode || data._workflow_mode),
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
    targetChapterLength: Number(data.target_chapter_length || 1500),
  };
}

function applyNormalizedStory(normalized) {
  state.storyId = normalized.storyId || state.storyId;
  state.mode = normalizeWorkflowMode(normalized.workflowMode || state.mode);
  state.title = normalized.title;
  state.chapters = Array.isArray(normalized.chapters) ? normalized.chapters : [];
  state.chapterSummaries = Array.isArray(normalized.chapterSummaries)
    ? normalized.chapterSummaries
    : [];
  state.continuityNotes = normalized.continuityNotes || "";
  state.targetChapterLength = normalized.targetChapterLength || 1500;
  if (chapterLengthSlider && chapterLengthCount) {
    chapterLengthSlider.value = String(state.targetChapterLength);
    chapterLengthCount.textContent = `${state.targetChapterLength} 字`;
  }
  state.artifacts = {
    storyBrief: normalized.storyBrief,
    world: normalized.world,
    characters: normalized.characters,
    outline: normalized.outline,
    chapter: normalized.chapter,
    manuscript: normalized.manuscript,
  };
  updateWorkflowModeUi();
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
    target_chapter_length: state.targetChapterLength || 1500,
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
  setWorkflowMode(payload.mode, { rerenderAgents: true, rerenderArtifacts: true, resetActivityHint: true });
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
  state.storyId = null;
  state.chapters = [];
  state.chapterSummaries = [];
  state.continuityNotes = "";
  switchView("studio");
  showStudioRunView(true);
  scrollToOutput();
  startProgress("正在生成小说", getWorkflowConfig().phases);
  setRunState("请求中", "is-running");
  submitButton.disabled = true;
  submitButton.textContent = "请求后端中...";

  getActiveAgents().forEach((_, index) => {
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
        author_style: payload.authorStyle,
        chapters: Number(payload.chapters),
        chapter_length: Number(payload.chapterLength),
        mode: payload.mode,
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
let taskPollCancelled = false;

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

function persistActiveTask(payload) {
  if (!state.taskId) return;
  localStorage.setItem("storyagents-active-task", JSON.stringify({
    taskId: state.taskId,
    cursor: state.taskCursor,
    payload,
  }));
}

function clearActiveTask() {
  localStorage.removeItem("storyagents-active-task");
  state.taskId = null;
  state.taskCursor = 0;
  state.taskStatus = "idle";
}

function processGenerationEvent(event) {
  if (!event) return;
  StoryAgentsSSE.assertSuccessfulEvent(event);

  if (event.event === "node_complete") {
    const { data, node } = StoryAgentsSSE.getNodeEventContext(event);
    const agentIndex = getNodeToAgentMap()[node];
    if (agentIndex !== undefined) {
      setAgentStatus(agentIndex, "已完成", "done");
      const nextIndex = agentIndex + 1;
      if (nextIndex < getActiveAgents().length) {
        setAgentStatus(nextIndex, "工作中", "active");
      }
    }

    if (data.story_title) state.title = data.story_title;
    if (data.story_id) state.storyId = data.story_id;
    addChatMessage("agent", AGENT_LIBRARY[node]?.name || node, getNodeDescription(node));

    if (data.current_chapter_draft && node === "Chapter Writer") {
      const chapterIdx = data.current_chapter_index || state.chapters.length + 1;
      addChatMessage("chapter", `第 ${chapterIdx} 章`, data.current_chapter_draft);
    }

    if (data.story_brief) state.artifacts.storyBrief = data.story_brief;
    if (data.story_bible) state.artifacts.world = data.story_bible;
    if (data.character_sheets) state.artifacts.characters = data.character_sheets;
    if (data.plot_outline) state.artifacts.outline = data.plot_outline;
    if (data.current_chapter_draft) state.artifacts.chapter = data.current_chapter_draft;
    if (Array.isArray(data.chapters) && data.chapters.length > 0) {
      state.chapters = data.chapters;
      state.artifacts.manuscript = data.final_manuscript || data.chapters.join("\n\n");
    }
    if (Array.isArray(data.chapter_summaries)) state.chapterSummaries = data.chapter_summaries;
    if (typeof data.continuity_notes === "string" && data.continuity_notes) {
      state.continuityNotes = data.continuity_notes;
    }

    const chapterIndex = data.current_chapter_index || 0;
    const targetChapters = data.target_chapters || 1;
    if (chapterIndex > 0) {
      const progress = Math.min(95, (chapterIndex / targetChapters) * 80 + 15);
      setProgress(progress, `第 ${chapterIndex}/${targetChapters} 章`);
    }
    renderArtifactContent();
  }

  if (event.event === "story_saved") {
    if (event.data?.story_id) state.storyId = event.data.story_id;
    if (event.data?.workflow_mode) setWorkflowMode(event.data.workflow_mode);
    loadHistory();
  }

  if (event.event === "story_complete") {
    finishProgress("生成完成");
    setRunState("已完成", "is-done");
    addSystemMessage("所有章节已生成完毕。");
  }
}

async function pollTask(payload) {
  const stopButton = document.querySelector("#stop-button");
  while (state.taskId && !taskPollCancelled) {
    const response = await fetch(`/api/storyagents/tasks/${encodeURIComponent(state.taskId)}?after=${state.taskCursor}`);
    const snapshot = await response.json();
    if (!response.ok) throw new Error(snapshot.error || `HTTP ${response.status}`);

    (snapshot.events || []).forEach(processGenerationEvent);
    state.taskCursor = snapshot.next_cursor || state.taskCursor;
    state.taskStatus = snapshot.status;
    persistActiveTask(payload);

    if (snapshot.status === "awaiting_outline") {
      outlineGate?.classList.remove("is-hidden");
      if (outlineGateContent) outlineGateContent.textContent = state.artifacts.outline || "大纲正在整理，请稍候……";
      setRunState("等待确认大纲");
      if (stopButton) stopButton.classList.add("is-hidden");
    } else {
      outlineGate?.classList.add("is-hidden");
      if (stopButton && !["completed", "failed"].includes(snapshot.status)) {
        stopButton.classList.remove("is-hidden");
        stopButton.textContent = snapshot.status === "paused" ? "继续创作" : "完成本步骤后暂停";
      }
    }

    if (snapshot.status === "completed") {
      finishProgress("生成完成");
      setRunState("已完成", "is-done");
      localStorage.setItem("storyagents-h5-form", JSON.stringify(payload));
      clearActiveTask();
      break;
    }
    if (snapshot.status === "failed") {
      throw new Error(snapshot.error || "生成任务失败");
    }
    await new Promise((resolve) => window.setTimeout(resolve, 800));
  }
}

async function runApiFlowStream(payload, existingTask = null) {
  setWorkflowMode(payload.mode, { rerenderAgents: true, rerenderArtifacts: true, resetActivityHint: true });
  if (!existingTask) {
    state.artifacts = {};
    state.activeArtifact = "storyBrief";
    state.storyId = null;
    state.chapters = [];
    state.chapterSummaries = [];
    state.continuityNotes = "";
    state.taskCursor = 0;
  }
  switchView("studio");
  showStudioRunView(true);
  startProgress("生成中", getWorkflowConfig().phases);
  setRunState("生成中", "is-running");
  submitButton.disabled = true;
  submitButton.textContent = "生成中...";

  if (!existingTask) clearChat();
  addSystemMessage(existingTask ? "已恢复上次创作任务。" : "创作任务已提交，可以安全离开当前页面。" );

  // Show stop button
  const stopButton = document.querySelector("#stop-button");
  if (stopButton) {
    stopButton.classList.remove("is-hidden");
  }

  try {
    taskPollCancelled = false;
    if (existingTask) {
      state.taskId = existingTask.taskId;
      state.taskCursor = Number(existingTask.cursor || 0);
    } else {
      const response = await fetch("/api/storyagents/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: payload.prompt,
          genre: payload.genre,
          tone: payload.tone,
          audience: payload.audience,
          author_style: payload.authorStyle,
          chapters: Number(payload.chapters),
          chapter_length: Number(payload.chapterLength),
          mode: payload.mode,
          confirm_outline: payload.mode !== "quick",
        }),
      });
      const created = await response.json();
      if (!response.ok) throw new Error(created.error || `HTTP ${response.status}`);
      state.taskId = created.task_id;
      state.taskCursor = 0;
      persistActiveTask(payload);
    }
    await pollTask(payload);
  } catch (error) {
    addSystemMessage(`生成失败：${error.message}`);
    failProgress("生成失败，请检查网络或稍后重试");
    setRunState("出错");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "重新提交";
    if (stopButton && !state.taskId) {
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
    authorStyle: String(formData.get("author_style") || "").trim(),
    mode: normalizeWorkflowMode(formData.get("workflow_mode") || state.mode),
    chapters: String(formData.get("chapters") || "3"),
    chapterLength: String(formData.get("chapter_length") || "1500"),
  };
}

async function runStylePreview() {
  const payload = readForm();
  if (!payload.prompt) {
    promptInput.focus();
    return;
  }
  if (!previewButton || !stylePreview || !stylePreviewText) return;

  previewButton.disabled = true;
  state.previewConfirmed = false;
  submitButton.disabled = true;
  submitButton.textContent = "确认风格后开始";
  previewButton.textContent = "正在生成预览...";
  stylePreview.classList.remove("is-hidden");
  stylePreviewText.textContent = "正在以当前工坊、题材、语气和参考作家生成约 200 字试读……";

  try {
    const response = await fetch("/api/storyagents/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: payload.prompt,
        genre: payload.genre,
        tone: payload.tone,
        audience: payload.audience,
        author_style: payload.authorStyle,
        chapters: Number(payload.chapters),
        chapter_length: Number(payload.chapterLength),
        mode: payload.mode,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    stylePreviewText.textContent = data.preview || "预览没有返回内容，请再试一次。";
    confirmPreviewButton?.removeAttribute("disabled");
  } catch (error) {
    stylePreviewText.textContent = `预览失败：${error.message}`;
  } finally {
    previewButton.disabled = false;
    previewButton.textContent = "预览风格（约 200 字）";
  }
}

function invalidatePreviewConfirmation() {
  if (!state.previewConfirmed) return;
  state.previewConfirmed = false;
  submitButton.disabled = true;
  submitButton.textContent = "内容已改变，请重新预览";
}

async function restoreActiveTask() {
  const raw = localStorage.getItem("storyagents-active-task");
  if (!raw) return;
  try {
    const active = JSON.parse(raw);
    if (!active.taskId || !active.payload) return;
    await runApiFlowStream(active.payload, active);
  } catch (error) {
    console.warn("恢复创作任务失败", error);
    localStorage.removeItem("storyagents-active-task");
  }
}

function hydrateStoredForm() {
  const raw = localStorage.getItem("storyagents-h5-form");
  if (!raw) {
    return;
  }
  try {
    const data = JSON.parse(raw);
    ["prompt", "genre", "tone", "audience", "authorStyle"].forEach((key) => {
      const fieldId = key === "authorStyle" ? "author-style" : key;
      const field = document.querySelector(`#${fieldId}`);
      if (typeof data[key] === "string" && field) {
        field.value = data[key];
      }
    });
    if (data.chapters) {
      chapterSlider.value = data.chapters;
      chapterCount.textContent = `${data.chapters} 章`;
    }
    if (data.chapterLength && chapterLengthSlider && chapterLengthCount) {
      chapterLengthSlider.value = data.chapterLength;
      chapterLengthCount.textContent = `${data.chapterLength} 字`;
    }
    if (data.mode) {
      setWorkflowMode(data.mode, { rerenderAgents: true, rerenderArtifacts: true, resetActivityHint: true });
    } else {
      updateWorkflowModeUi();
    }
  } catch (error) {
    console.warn("保存的墨神表单解析失败", error);
  }
}

function bootstrap() {
  chapterSlider.addEventListener("input", (event) => {
    applyWorkshopLimits(getWorkflowConfig());
  });

  if (chapterLengthSlider && chapterLengthCount) {
    chapterLengthSlider.addEventListener("input", (event) => {
      applyWorkshopLimits(getWorkflowConfig());
    });
  }

  if (modeGrid) {
    modeGrid.querySelectorAll(".mode-card").forEach((card) => {
      card.addEventListener("click", () => {
        setWorkflowMode(card.dataset.mode, {
          rerenderAgents: true,
          rerenderArtifacts: true,
          resetActivityHint: true,
        });
      });
    });
  }

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      promptInput.value = chip.dataset.prompt || "";
      invalidatePreviewConfirmation();
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
        invalidatePreviewConfirmation();

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
    if (!state.previewConfirmed) {
      stylePreview?.classList.remove("is-hidden");
      if (stylePreviewText && !stylePreviewText.textContent.trim()) {
        stylePreviewText.textContent = "请先生成约 200 字试写并确认风格，再开始正式创作。";
      }
      return;
    }
    await runApiFlowStream(payload);
  });

  if (previewButton) {
    previewButton.addEventListener("click", runStylePreview);
  }
  retryPreviewButton?.addEventListener("click", runStylePreview);
  confirmPreviewButton?.addEventListener("click", () => {
    state.previewConfirmed = true;
    submitButton.disabled = false;
    submitButton.textContent = "确认风格，开始生成";
    stylePreview?.classList.add("is-confirmed");
  });

  form.addEventListener("input", (event) => {
    if (event.target?.id !== "preview-button") invalidatePreviewConfirmation();
  });
  form.addEventListener("change", invalidatePreviewConfirmation);

  const stopButton = document.querySelector("#stop-button");
  if (stopButton) {
    stopButton.addEventListener("click", async () => {
      if (!state.taskId) return;
      const action = state.taskStatus === "paused" ? "resume" : "pause";
      const response = await fetch(`/api/storyagents/tasks/${encodeURIComponent(state.taskId)}/${action}`, {
        method: "POST",
      });
      const snapshot = await response.json();
      if (!response.ok) {
        addSystemMessage(`操作失败：${snapshot.error || response.status}`);
        return;
      }
      state.taskStatus = snapshot.status;
      stopButton.textContent = snapshot.status === "paused" ? "继续创作" : "完成本步骤后暂停";
      setRunState(snapshot.status === "paused" ? "已暂停" : "生成中", snapshot.status === "paused" ? "" : "is-running");
    });
  }

  approveOutlineButton?.addEventListener("click", async () => {
    if (!state.taskId) return;
    approveOutlineButton.disabled = true;
    const response = await fetch(`/api/storyagents/tasks/${encodeURIComponent(state.taskId)}/approve-outline`, {
      method: "POST",
    });
    const snapshot = await response.json();
    approveOutlineButton.disabled = false;
    if (!response.ok) {
      addSystemMessage(`确认大纲失败：${snapshot.error || response.status}`);
      return;
    }
    outlineGate?.classList.add("is-hidden");
    state.taskStatus = snapshot.status;
    setRunState("生成中", "is-running");
    stopButton?.classList.remove("is-hidden");
  });

  // Clear chat button
  const clearChatBtn = document.querySelector("#clear-chat");
  if (clearChatBtn) {
    clearChatBtn.addEventListener("click", clearChat);
  }
  const showArtifactsBtn = document.querySelector("#show-artifacts");
  if (showArtifactsBtn) {
    showArtifactsBtn.addEventListener("click", () => {
      const panel = document.querySelector("#artifact-panel");
      if (!panel) return;
      const isCollapsed = panel.classList.toggle("is-collapsed");
      showArtifactsBtn.textContent = isCollapsed ? "创作档案" : "收起档案";
    });
  }

  renderAgentCards();
  renderArtifactTabs();
  renderArtifactContent();
  resetLog();
  resetProgress();
  updateWorkflowModeUi();
  renderModePresets();
  hydrateStoredForm();
  loadHistory();
  initEditToolbar();
  document.body.dataset.bootstrap = "ready";
  openStudioFromHash();
  restoreActiveTask();
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
          ${s.author_style ? `<span>${escapeHtml(s.author_style)}</span>` : ""}
          <span>${escapeHtml(getWorkflowConfig(s.mode || "quick").label)}</span>
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
  let continuationMode = state.mode;
  let usedContinuations = 0;
  try {
    const storyResponse = await fetch(`/api/storyagents/stories/${encodeURIComponent(id)}`);
    if (storyResponse.ok) {
      const storyData = await storyResponse.json();
      continuationMode = normalizeWorkflowMode(
        storyData.workflow_mode || storyData._workflow_mode || continuationMode,
      );
      usedContinuations = Number(storyData._continuation_count || 0);
    }
  } catch (error) {
    console.warn("读取故事模式失败，继续沿用当前模式。", error);
  }

  const limits = getWorkflowConfig(continuationMode).limits;
  if (limits.maxContinuations !== null && usedContinuations >= limits.maxContinuations) {
    alert(`${getWorkflowConfig(continuationMode).label}最多续写 ${limits.maxContinuations} 次。`);
    return;
  }
  const rangeHint = limits.maxContinuationChapters
    ? `1-${limits.maxContinuationChapters}`
    : "任意正整数";
  const suggested = Math.min(limits.maxContinuationChapters || 3, 3);
  const continueChapters = prompt(`请输入续写章节数（${rangeHint}）：`, String(suggested));
  if (!continueChapters) return;

  const chapters = parseInt(continueChapters, 10);
  if (
    isNaN(chapters) ||
    chapters < 1 ||
    (limits.maxContinuationChapters !== null && chapters > limits.maxContinuationChapters)
  ) {
    alert(limits.maxContinuationChapters
      ? `请输入有效的章节数（1-${limits.maxContinuationChapters}）`
      : "请输入大于 0 的章节数");
    return;
  }

  // Switch to studio view
  setWorkflowMode(continuationMode, { rerenderAgents: true, rerenderArtifacts: true, resetActivityHint: true });
  switchView("studio");
  showStudioRunView(true);
  state.storyId = id;
  state.artifacts = {};
  state.activeArtifact = "storyBrief";
  state.chapters = [];
  state.chapterSummaries = [];
  state.continuityNotes = "";
  startProgress("正在续写小说", getWorkflowConfig().phases);
  setRunState("续写中", "is-running");

  pushLog("开始续写", `正在续写故事，计划生成 ${chapters} 章...`);

  try {
    const response = await fetch("/api/storyagents/continue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        story_id: id,
        continue_chapters: chapters,
        mode: continuationMode,
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

        let event;
        try {
          event = StoryAgentsSSE.parseEventLine(line);
        } catch (parseError) {
          console.warn("SSE parse error:", parseError);
          continue;
        }
        if (!event) continue;
        StoryAgentsSSE.assertSuccessfulEvent(event);

          if (event.event === "node_complete") {
            const { data, node } = StoryAgentsSSE.getNodeEventContext(event);

            // Update agent status
            const agentIndex = getNodeToAgentMap()[node];
            if (agentIndex !== undefined) {
              setAgentStatus(agentIndex, "已完成", "done");
              const nextIndex = agentIndex + 1;
              if (nextIndex < getActiveAgents().length) {
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

            pushLog(`${AGENT_LIBRARY[node]?.name || node} 完成`, getNodeDescription(node));
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

          if (event.event === "story_saved") {
            if (event.data?.workflow_mode) {
              setWorkflowMode(event.data.workflow_mode);
            }
            loadHistory();
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
  initInkTrail();
} catch (error) {
  console.error(error);
  document.body.dataset.bootstrap = "failed";
  const banner = document.createElement("div");
  banner.className = "boot-error";
  banner.textContent = `前端启动失败：${error.message}`;
  document.body.prepend(banner);
}

/* A restrained ink-wash trail for pointer users; touch devices stay untouched. */
function initInkTrail() {
  if (window.matchMedia("(pointer: coarse), (prefers-reduced-motion: reduce)").matches) return;

  const layer = document.createElement("div");
  layer.className = "ink-cursor-layer";
  layer.setAttribute("aria-hidden", "true");
  document.body.appendChild(layer);

  let lastX = 0;
  let lastY = 0;
  let lastStamp = 0;
  let sample = 0;

  document.addEventListener("pointermove", (event) => {
    if (event.pointerType && event.pointerType !== "mouse") return;
    const now = performance.now();
    if (now - lastStamp < 34) return;
    const distance = Math.hypot(event.clientX - lastX, event.clientY - lastY);
    if (distance < 7) return;
    lastX = event.clientX;
    lastY = event.clientY;
    lastStamp = now;

    const blot = document.createElement("i");
    blot.className = `ink-cursor-blot${sample++ % 5 === 0 ? " is-deep" : ""}`;
    blot.style.left = `${event.clientX}px`;
    blot.style.top = `${event.clientY}px`;
    blot.style.setProperty("--ink-scale", (0.7 + Math.random() * 0.75).toFixed(2));
    blot.style.setProperty("--ink-rotate", `${Math.round(Math.random() * 160 - 80)}deg`);
    layer.appendChild(blot);
    window.setTimeout(() => blot.remove(), 800);

    while (layer.childElementCount > 24) layer.firstElementChild.remove();
  }, { passive: true });
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
/* GSAP enhances the interface when it is available; core flows remain dependency-free. */
(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const enabled = () => window.gsap && !reduced;

  const playHomeIntro = () => {
    if (!enabled()) return;
    const tl = window.gsap.timeline({ defaults: { ease: "power3.out" } });
    tl.fromTo(".topbar", { y: -20, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.55 })
      .fromTo("#view-home .home-copy > *", { y: 28, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.7, stagger: 0.09 }, "<0.1")
      .fromTo("#view-home .showcase-pane-main", { y: 32, rotation: 1.5, autoAlpha: 0 }, { y: 0, rotation: 0, autoAlpha: 1, duration: 0.85 }, "<0.12")
      .fromTo("#view-home .showcase-pane-float", { y: 22, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.55, stagger: 0.12 }, "<0.35")
      .to(".ambient-orb", { x: (i) => (i - 1) * 14, y: (i) => (i - 1) * -8, duration: 1.5, stagger: 0.08, ease: "sine.inOut" }, "<");
  };

  const enterView = (viewName) => {
    if (!enabled()) return;
    const view = document.querySelector(`#view-${viewName}`);
    if (!view) return;
    window.gsap.killTweensOf(view.querySelectorAll(".glass-panel, .view-header, .history-card"));
    window.gsap.fromTo(view.querySelectorAll(".glass-panel, .view-header, .history-card"), { y: 18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.48, stagger: 0.055, ease: "power2.out" });
  };

  const init = () => {
    if (!enabled()) return;
    playHomeIntro();
    document.querySelectorAll(".primary-button").forEach((button) => {
      button.addEventListener("pointermove", (event) => {
        const rect = button.getBoundingClientRect();
        window.gsap.to(button, { x: (event.clientX - rect.left - rect.width / 2) * 0.08, y: (event.clientY - rect.top - rect.height / 2) * 0.08, duration: 0.24, ease: "power2.out", overwrite: "auto" });
      });
      button.addEventListener("pointerleave", () => window.gsap.to(button, { x: 0, y: 0, duration: 0.42, ease: "elastic.out(1, 0.45)", overwrite: "auto" }));
    });
  };

  const originalSwitchView = switchView;
  switchView = function motionAwareSwitchView(viewName) {
    originalSwitchView(viewName);
    enterView(viewName);
  };
  window.MoShenMotion = { enterView };
  init();
})();
