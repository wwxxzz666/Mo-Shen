const app = getApp();

const AGENTS_BY_MODE = {
  quick: ['策划编辑', '剧情架构师', '章节写手', '总编'],
  standard: ['策划编辑', '世界观设计师', '角色设计师', '剧情架构师', '章节写手', '总编'],
  deep: ['策划编辑', '世界观设计师', '角色设计师', '剧情架构师', '章节写手', '连续性审校', '总编']
};

const NODE_LABELS = {
  Planner: '策划编辑',
  Worldbuilder: '世界观设计师',
  'Character Designer': '角色设计师',
  'Outline Agent': '剧情架构师',
  'Chapter Writer': '章节写手',
  'Continuity Reviewer': '连续性审校',
  Showrunner: '总编'
};

Page({
  data: {
    prompt: '',
    mode: 'quick',
    genre: '',
    tone: '',
    audience: '',
    authorStyle: '',
    chapters: 3,
    chapterLength: 1500,
    phase: 'preview',
    previewText: '',
    previewConfirmed: false,
    taskId: '',
    taskCursor: 0,
    taskStatus: 'idle',
    storyId: '',
    storyTitle: '未命名故事',
    outline: '',
    currentChapter: 0,
    currentChapterDraft: '',
    manuscript: '',
    progress: 0,
    statusText: '先试写约 200 字，确认语言感觉',
    showCollaboration: false,
    agents: []
  },

  onLoad(options) {
    const mode = ['quick', 'standard', 'deep'].includes(options.mode) ? options.mode : 'quick';
    this.setData({
      prompt: decodeURIComponent(options.prompt || ''),
      mode,
      genre: decodeURIComponent(options.genre || ''),
      tone: decodeURIComponent(options.tone || ''),
      audience: decodeURIComponent(options.audience || ''),
      authorStyle: options.author_style || '',
      chapters: Math.max(1, Number(options.chapters || 3)),
      chapterLength: Math.min(5000, Math.max(300, Number(options.chapter_length || 1500))),
      agents: AGENTS_BY_MODE[mode].map(name => ({ name, status: '等待中' }))
    });
    this.restoreTask();
  },

  onUnload() {
    this.stopPolling();
  },

  api(path, options = {}) {
    const baseUrl = app.globalData.baseUrl || 'http://127.0.0.1:8000';
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${baseUrl}${path}`,
        method: options.method || 'GET',
        data: options.data,
        header: { 'content-type': 'application/json' },
        timeout: 60000,
        success: res => {
          if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data);
          else reject(new Error((res.data && res.data.error) || `请求失败 ${res.statusCode}`));
        },
        fail: reject
      });
    });
  },

  getPayload() {
    return {
      prompt: this.data.prompt,
      mode: this.data.mode,
      genre: this.data.genre,
      tone: this.data.tone,
      audience: this.data.audience,
      author_style: this.data.authorStyle,
      chapters: Number(this.data.chapters),
      chapter_length: Number(this.data.chapterLength)
    };
  },

  async generatePreview() {
    this.setData({ phase: 'previewing', previewConfirmed: false, statusText: '正在生成约 200 字试写…' });
    try {
      const result = await this.api('/api/storyagents/preview', { method: 'POST', data: this.getPayload() });
      this.setData({ phase: 'preview', previewText: result.preview || '', statusText: '读一读，确认这是不是你想要的感觉' });
    } catch (error) {
      this.setData({ phase: 'error', statusText: error.message });
    }
  },

  confirmPreview() {
    this.setData({ previewConfirmed: true, statusText: '风格已确认，可以开始正式创作' });
  },

  async startCreation() {
    if (!this.data.previewConfirmed) {
      wx.showToast({ title: '请先确认试写风格', icon: 'none' });
      return;
    }
    this.setData({ phase: 'running', taskStatus: 'queued', statusText: '正在创建创作任务…' });
    try {
      const result = await this.api('/api/storyagents/tasks', {
        method: 'POST',
        data: { ...this.getPayload(), confirm_outline: this.data.mode !== 'quick' }
      });
      this.setData({ taskId: result.task_id, taskCursor: 0, taskStatus: result.status });
      this.saveTask();
      this.pollTask();
    } catch (error) {
      this.setData({ phase: 'error', statusText: error.message });
    }
  },

  async pollTask() {
    this.stopPolling();
    if (!this.data.taskId) return;
    try {
      const snapshot = await this.api(`/api/storyagents/tasks/${this.data.taskId}?after=${this.data.taskCursor}`);
      (snapshot.events || []).forEach(event => this.applyEvent(event));
      const next = {
        taskCursor: snapshot.next_cursor || this.data.taskCursor,
        taskStatus: snapshot.status,
        storyId: snapshot.story_id || this.data.storyId
      };
      if (snapshot.status === 'awaiting_outline') {
        Object.assign(next, { phase: 'outline', statusText: '大纲已完成，等你确认后再写正文' });
      } else if (snapshot.status === 'paused') {
        Object.assign(next, { phase: 'paused', statusText: '已在安全节点暂停，可随时恢复' });
      } else if (snapshot.status === 'completed') {
        Object.assign(next, { phase: 'completed', progress: 100, statusText: '创作完成' });
      } else if (snapshot.status === 'failed') {
        Object.assign(next, { phase: 'error', statusText: snapshot.error || '生成失败' });
      } else {
        Object.assign(next, { phase: 'running', statusText: '正在逐章创作，可以离开页面' });
      }
      this.setData(next);
      this.saveTask();
      if (!['completed', 'failed'].includes(snapshot.status)) {
        this._pollTimer = setTimeout(() => this.pollTask(), 900);
      } else {
        wx.removeStorageSync('mo-shen-active-task');
      }
    } catch (error) {
      this.setData({ statusText: '网络已断开，正在等待恢复…' });
      this._pollTimer = setTimeout(() => this.pollTask(), 1800);
    }
  },

  applyEvent(event) {
    if (event.error) {
      this.setData({ phase: 'error', statusText: event.error });
      return;
    }
    if (event.event !== 'node_complete') return;
    const data = event.data || {};
    const node = data.node;
    const label = NODE_LABELS[node] || node;
    const agents = this.data.agents.map(agent => agent.name === label ? { ...agent, status: '已完成' } : agent);
    const target = Number(data.target_chapters || this.data.chapters || 1);
    const current = Number(data.current_chapter_index || this.data.currentChapter || 0);
    this.setData({
      agents,
      storyTitle: data.story_title || this.data.storyTitle,
      outline: data.plot_outline || this.data.outline,
      currentChapter: current,
      currentChapterDraft: data.current_chapter_draft || this.data.currentChapterDraft,
      manuscript: data.final_manuscript || this.data.manuscript,
      progress: Math.min(96, current ? Math.round(15 + current / target * 80) : 10)
    });
  },

  async approveOutline() {
    await this.api(`/api/storyagents/tasks/${this.data.taskId}/approve-outline`, { method: 'POST' });
    this.setData({ phase: 'running', taskStatus: 'running', statusText: '大纲已确认，开始写正文' });
    this.pollTask();
  },

  async togglePause() {
    const action = this.data.taskStatus === 'paused' ? 'resume' : 'pause';
    const snapshot = await this.api(`/api/storyagents/tasks/${this.data.taskId}/${action}`, { method: 'POST' });
    this.setData({
      taskStatus: snapshot.status,
      phase: snapshot.status === 'paused' ? 'paused' : 'running',
      statusText: snapshot.status === 'paused' ? '将在当前步骤结束后暂停' : '已恢复创作'
    });
    this.pollTask();
  },

  toggleCollaboration() {
    this.setData({ showCollaboration: !this.data.showCollaboration });
  },

  async viewManuscript() {
    if (!this.data.storyId) return;
    try {
      const story = await this.api(`/api/storyagents/stories/${encodeURIComponent(this.data.storyId)}`);
      wx.setStorageSync('current_manuscript', story.final_manuscript || this.data.manuscript);
      wx.navigateTo({ url: `/pages/manuscript/manuscript?title=${encodeURIComponent(story.story_title || this.data.storyTitle)}` });
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' });
    }
  },

  saveTask() {
    if (!this.data.taskId) return;
    wx.setStorageSync('mo-shen-active-task', {
      taskId: this.data.taskId,
      taskCursor: this.data.taskCursor,
      payload: this.getPayload()
    });
  },

  restoreTask() {
    const active = wx.getStorageSync('mo-shen-active-task');
    if (!active || !active.taskId) return;
    this.setData({
      ...active.payload,
      taskId: active.taskId,
      taskCursor: Number(active.taskCursor || 0),
      phase: 'running',
      statusText: '正在恢复上次创作…'
    });
    this.pollTask();
  },

  stopPolling() {
    if (this._pollTimer) clearTimeout(this._pollTimer);
    this._pollTimer = null;
  }
});
