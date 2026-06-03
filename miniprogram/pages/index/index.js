/**
 * 首页 - 创作入口页面
 * 包含：故事需求输入、创作模式选择、参数设置、快速灵感
 */

const app = getApp();

Page({
  data: {
    // 故事需求
    prompt: '',
    
    // 创作模式
    selectedMode: 'quick',
    modeSummary: '快速出稿 · 直接从 brief 到章节出稿，适合试题材、试节奏和快速起篇。',
    
    // 参数设置
    genre: '悬疑 / 科幻',
    tone: '冷静、抒情、带压迫感',
    audience: '成年向',
    chapters: 3
  },

  /**
   * 故事需求输入
   */
  onPromptInput(e) {
    this.setData({ prompt: e.detail.value });
  },

  /**
   * 选择创作模式
   */
  selectMode(e) {
    const mode = e.currentTarget.dataset.mode;
    const summaries = {
      quick: '快速出稿 · 直接从 brief 到章节出稿，适合试题材、试节奏和快速起篇。',
      standard: '标准创作 · 补齐世界观与角色层，再进入章节写作，更适合稳定创作。',
      deep: '深度打磨 · 加入连续性审校，适合长篇、人设复杂和伏笔密集的项目。'
    };
    
    this.setData({
      selectedMode: mode,
      modeSummary: summaries[mode]
    });
  },

  /**
   * 参数输入
   */
  onGenreInput(e) {
    this.setData({ genre: e.detail.value });
  },

  onToneInput(e) {
    this.setData({ tone: e.detail.value });
  },

  onAudienceInput(e) {
    this.setData({ audience: e.detail.value });
  },

  onChaptersChange(e) {
    this.setData({ chapters: e.detail.value });
  },

  /**
   * 使用快速灵感
   */
  useChip(e) {
    const prompt = e.currentTarget.dataset.prompt;
    this.setData({ prompt });
    
    wx.showToast({
      title: '已填入灵感',
      icon: 'success'
    });
  },

  /**
   * 开始创作
   */
  startCreate() {
    if (!this.data.prompt) {
      wx.showToast({
        title: '请先描述你的故事需求',
        icon: 'none'
      });
      return;
    }

    // 跳转到创作工作台，传递所有参数
    const params = [
      `prompt=${encodeURIComponent(this.data.prompt)}`,
      `mode=${this.data.selectedMode}`,
      `genre=${encodeURIComponent(this.data.genre)}`,
      `tone=${encodeURIComponent(this.data.tone)}`,
      `audience=${encodeURIComponent(this.data.audience)}`,
      `chapters=${this.data.chapters}`
    ].join('&');

    wx.navigateTo({
      url: `/pages/studio/studio?${params}`
    });
  },

  onShow() {
    console.log('首页显示');
  }
});
