/**
 * 墨神AI创作 - 小程序入口文件
 * 这是整个小程序的启动文件，会最先被执行
 */

App({
  // 全局数据（所有页面都能访问）
  globalData: {
    // API服务器地址（暂时留空，后面部署后端再填）
    baseUrl: '',
    
    // 用户信息
    userInfo: null,
    
    // 故事列表（模拟数据，后面会从服务器获取）
    stories: [
      {
        id: '1',
        title: '星际迷途',
        genre: '科幻',
        status: '已完成',
        chapters: 12,
        createdAt: '2024-01-15'
      },
      {
        id: '2',
        title: '古镇幽灵',
        genre: '悬疑',
        status: '创作中',
        chapters: 5,
        createdAt: '2024-02-20'
      }
    ]
  },

  /**
   * 小程序启动时执行（只执行一次）
   */
  onLaunch() {
    console.log('墨神AI创作启动成功！');
    
    // 检查本地是否有保存的故事
    const savedStories = wx.getStorageSync('stories');
    if (savedStories) {
      this.globalData.stories = savedStories;
    }
  }
});
