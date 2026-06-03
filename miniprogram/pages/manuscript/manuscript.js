/**
 * 成稿预览页面
 * 显示完整故事内容，支持复制和分享
 */

Page({
  data: {
    // 故事信息
    storyTitle: '未命名故事',
    genre: '科幻',
    chapters: 3,
    
    // 成稿内容
    manuscript: '',
    wordCount: 0
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    // 获取传递的参数
    if (options.title) {
      this.setData({ storyTitle: decodeURIComponent(options.title) });
    }
    if (options.genre) {
      this.setData({ genre: decodeURIComponent(options.genre) });
    }
    if (options.chapters) {
      this.setData({ chapters: parseInt(options.chapters) });
    }
    
    // 获取成稿内容
    this.loadManuscript();
  },

  /**
   * 加载成稿内容
   */
  loadManuscript() {
    // 从本地存储或全局数据获取
    const app = getApp();
    let manuscript = '';
    
    // 尝试从本地存储获取
    const savedManuscript = wx.getStorageSync('current_manuscript');
    if (savedManuscript) {
      manuscript = savedManuscript;
    } else {
      // 使用模拟数据（演示用）
      manuscript = this.getDemoManuscript();
    }
    
    // 计算字数
    const wordCount = manuscript.replace(/\s/g, '').length;
    
    this.setData({ manuscript, wordCount });
  },

  /**
   * 获取演示成稿
   */
  getDemoManuscript() {
    return `第一章 黎明号启航

2150年3月15日，地球联合航天中心。

林晓站在指挥塔的落地窗前，望着远处那艘银白色的星际飞船——"黎明号"。这是人类历史上最先进的探索飞船，也是她即将指挥的座舰。

"舰长，所有系统检查完毕，可以登船了。"身后传来副官的声音。

林晓转过身，整了整制服的领口。"通知全体船员，三十分钟后在主舱集合。"

她走向电梯，心跳微微加速。这是她第一次担任星际探索任务的指挥官，虽然已经训练了三年，但真正站在这个位置上时，还是感到一种难以言喻的压力。

电梯门打开，她走进飞船内部。走廊两侧的灯光自动亮起，柔和的蓝光映照在金属墙壁上，给人一种既未来又温馨的感觉。

"欢迎登舰，舰长。"飞船的AI系统"星辰"用温和的声音说道。

"谢谢，星辰。"林晓微笑着回应，"今天的状态如何？"

"所有系统运行正常，能源储备充足，生命维持系统已经调试到最佳状态。"

林晓点点头，继续向主舱走去。沿途，她遇到了几位正在忙碌的船员。他们看到她，纷纷停下手中的工作，向她敬礼致意。

"舰长好！"

"大家好。"林晓一一回应，"十分钟后主舱见。"

当她到达主舱时，大部分船员已经就座。她走上讲台，环视了一圈这些即将与她共同踏上未知旅程的伙伴们。

"各位，"她开口说道，"我们即将执行的是'曙光计划'——人类首次前往半人马座α星系的探索任务。这不仅是一次科学探索，更是人类文明向外延伸的重要一步。"

她停顿了一下，看着每个人的眼睛。

"我知道，前方充满了未知和挑战。但我相信，凭借我们的专业素养和团队精神，我们一定能够完成这次使命。"

掌声响起，林晓感到一股暖流涌上心头。

"现在，各就各位。十分钟后，我们出发。"

随着倒计时的结束，黎明号缓缓升空，穿过大气层，驶向那片浩瀚的星海。

林晓望着舷窗外渐渐变小的地球，心中默默许下承诺：她一定会带着所有人，平安归来。`;
  },

  /**
   * 复制成稿
   */
  copyManuscript() {
    wx.setClipboardData({
      data: this.data.manuscript,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success'
        });
      }
    });
  },

  /**
   * 分享给朋友
   */
  shareManuscript() {
    // 触发分享菜单
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  /**
   * 分享给朋友（右上角菜单）
   */
  onShareAppMessage() {
    return {
      title: `【${this.data.storyTitle}】- AI创作`,
      path: '/pages/manuscript/manuscript?title=' + encodeURIComponent(this.data.storyTitle),
      imageUrl: '' // 可以设置分享图片
    };
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline() {
    return {
      title: `【${this.data.storyTitle}】- 用AI创作的故事`,
      query: 'title=' + encodeURIComponent(this.data.storyTitle)
    };
  }
});
