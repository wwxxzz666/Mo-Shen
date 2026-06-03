/**
 * 导航首页
 * 展示品牌、功能入口、智能体介绍
 */

Page({
  data: {
    // 6大智能体
    agents: [
      { name: '策划编辑', icon: '📋' },
      { name: '世界观构建', icon: '🌍' },
      { name: '角色设计', icon: '👤' },
      { name: '大纲规划', icon: '📝' },
      { name: '章节写作', icon: '✍️' },
      { name: '审校润色', icon: '🔍' }
    ]
  },

  /**
   * 跳转到创作页面
   */
  goToCreate() {
    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  /**
   * 跳转到历史页面
   */
  goToHistory() {
    wx.switchTab({
      url: '/pages/history/history'
    });
  },

  /**
   * 跳转到智能体介绍页面
   */
  goToAgents() {
    wx.showModal({
      title: 'AI 智能体团队',
      content: '策划编辑：确定故事方向和主题\n\n世界观构建：创造故事发生的世界\n\n角色设计：设计鲜活的人物角色\n\n大纲规划：规划章节结构\n\n章节写作：逐章创作故事内容\n\n审校润色：检查和优化文字',
      showCancel: false,
      confirmText: '知道了'
    });
  },

  onShow() {
    console.log('导航首页显示');
  }
});
