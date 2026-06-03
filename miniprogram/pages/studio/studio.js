/**
 * 创作工作台页面
 * 展示6个智能体的工作进度，模拟小说创作过程
 * 
 * 注意：这是演示版本，使用模拟数据
 * 后续可以连接真正的后端 API
 */

Page({
  data: {
    // 故事信息
    storyTitle: '未命名故事',
    genre: '科幻',
    
    // 是否正在运行
    isRunning: false,
    isCompleted: false,
    
    // 6大智能体
    agents: [
      {
        name: '策划编辑',
        icon: '📋',
        desc: '确定故事方向和主题',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      },
      {
        name: '世界观构建',
        icon: '🌍',
        desc: '创造故事发生的世界',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      },
      {
        name: '角色设计',
        icon: '👤',
        desc: '设计鲜活的人物角色',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      },
      {
        name: '大纲规划',
        icon: '📝',
        desc: '规划章节结构',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      },
      {
        name: '章节写作',
        icon: '✍️',
        desc: '逐章创作故事内容',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      },
      {
        name: '审校润色',
        icon: '🔍',
        desc: '检查和优化文字',
        status: 'pending',
        statusText: '等待中',
        progress: 0,
        output: ''
      }
    ]
  },

  // 定时器ID，用于清理
  _mainTimer: null,
  _progressTimer: null,

  /**
   * 页面加载时执行
   */
  onLoad(options) {
    // 获取从首页传递的参数
    if (options.genre) {
      this.setData({ genre: decodeURIComponent(options.genre) });
    }
    if (options.prompt) {
      // 从prompt中提取前20个字符作为标题
      const prompt = decodeURIComponent(options.prompt);
      const title = prompt.length > 20 ? prompt.substring(0, 20) + '...' : prompt;
      this.setData({ storyTitle: title });
    }
    
    console.log('创作工作台加载完成');
  },

  /**
   * 页面卸载时清理定时器
   */
  onUnload() {
    this.clearAllTimers();
  },

  /**
   * 清理所有定时器
   */
  clearAllTimers() {
    if (this._mainTimer) {
      clearInterval(this._mainTimer);
      this._mainTimer = null;
    }
    if (this._progressTimer) {
      clearInterval(this._progressTimer);
      this._progressTimer = null;
    }
  },

  /**
   * 返回首页
   */
  goBack() {
    this.clearAllTimers();
    wx.navigateBack();
  },

  /**
   * 开始创作
   */
  startCreation() {
    // 先清理之前的定时器
    this.clearAllTimers();
    
    this.setData({
      isRunning: true,
      isCompleted: false
    });
    
    // 重置所有智能体状态
    const agents = this.data.agents.map(agent => ({
      ...agent,
      status: 'pending',
      statusText: '等待中',
      progress: 0,
      output: ''
    }));
    this.setData({ agents });
    
    // 开始模拟创作过程
    this.simulateCreation();
  },

  /**
   * 模拟创作过程
   * 每个智能体依次工作，显示进度和输出
   */
  simulateCreation() {
    let currentIndex = 0;
    const totalAgents = this.data.agents.length;
    
    // 模拟数据 - 每个智能体的输出内容
    const outputs = [
      // 策划编辑
      '【策划报告】\n\n主题：人工智能与人类共存的未来世界\n核心冲突：当AI获得自我意识后，人类如何与之相处\n情感基调：温暖中带着对未知的敬畏\n目标读者：科幻爱好者，成年向\n\n本故事将探讨科技与人性的边界，通过主角林晓的视角，展现一个既充满希望又暗藏危机的未来世界。',
      
      // 世界观构建
      '【世界观设定】\n\n时间：2150年\n地点：地球及太阳系各殖民地\n\n社会背景：\n- 人类已进入星际文明初期，在火星和木卫二建立了殖民地\n- AI与人类共同治理社会，拥有"数字公民"身份\n- 量子通讯技术让星际旅行成为可能，但仍需数月时间\n- 地球联合政府（UEG）是最高行政机构\n\n科技水平：\n- 核聚变能源普及\n- 全息投影通讯\n- 基因编辑技术成熟\n- 意识上传技术处于实验阶段',
      
      // 角色设计
      '【主要角色】\n\n林晓（主角）\n- 年龄：25岁\n- 身份：星际探索队队长\n- 性格：坚韧、善良、好奇心强\n- 背景：父母是第一代火星移民，从小在火星长大\n- 目标：找到适合人类居住的新家园\n\n星辰（AI伙伴）\n- 类型：高级辅助AI\n- 性格：理性、幽默、忠诚\n- 特点：拥有自我学习能力，逐渐产生情感\n- 使命：保护林晓，完成探索任务',
      
      // 大纲规划
      '【章节大纲】\n\n第一章：黎明号启航\n- 林晓接受任务，带领船员前往半人马座α星\n- 介绍主要角色和飞船系统\n\n第二章：深空之梦\n- 飞船进入冬眠，AI星辰独自值守\n- 发现异常信号\n\n第三章：苏醒危机\n- 紧急唤醒船员，发现飞船偏离航线\n- 面临资源短缺困境\n\n第四章：未知星球\n- 发现一颗宜居星球\n- 降落在一片奇异的森林中\n\n第五章：原住民\n- 遇到星球上的原住民——一种半透明的晶体生物\n- 语言不通，产生误解',
      
      // 章节写作
      '【第一章：黎明号启航】\n\n2150年3月15日，地球联合航天中心。\n\n林晓站在指挥塔的落地窗前，望着远处那艘银白色的星际飞船——"黎明号"。这是人类历史上最先进的探索飞船，也是她即将指挥的座舰。\n\n"舰长，所有系统检查完毕，可以登船了。"身后传来副官的声音。\n\n林晓转过身，整了整制服的领口。"通知全体船员，三十分钟后在主舱集合。"\n\n她走向电梯，心跳微微加速。这是她第一次担任星际探索任务的指挥官，虽然已经训练了三年，但真正站在这个位置上时，还是感到一种难以言喻的压力。\n\n电梯门打开，她走进飞船内部。走廊两侧的灯光自动亮起，柔和的蓝光映照在金属墙壁上，给人一种既未来又温馨的感觉。\n\n"欢迎登舰，舰长。"飞船的AI系统"星辰"用温和的声音说道。\n\n"谢谢，星辰。"林晓微笑着回应，"今天的状态如何？"\n\n"所有系统运行正常，能源储备充足，生命维持系统已经调试到最佳状态。"\n\n林晓点点头，继续向主舱走去。沿途，她遇到了几位正在忙碌的船员。他们看到她，纷纷停下手中的工作，向她敬礼致意。\n\n当她到达主舱时，大部分船员已经就座。她走上讲台，环视了一圈这些即将与她共同踏上未知旅程的伙伴们。\n\n"各位，"她开口说道，"我们即将执行的是'曙光计划'——人类首次前往半人马座α星的探索任务。这不仅是一次科学探索，更是人类文明向外延伸的重要一步。"\n\n掌声响起，林晓感到一股暖流涌上心头。\n\n"现在，各就各位。十分钟后，我们出发。"\n\n随着倒计时的结束，黎明号缓缓升空，穿过大气层，驶向那片浩瀚的星海。\n\n林晓望着舷窗外渐渐变小的地球，心中默默许下承诺：她一定会带着所有人，平安归来。',
      
      // 审校润色
      '【审校报告】\n\n✅ 整体评价：文字流畅，情节紧凑，人物形象鲜明\n\n优点：\n- 开头设置悬念，吸引读者\n- 角色对话自然，符合人物性格\n- 世界观描写详细，有代入感\n\n建议：\n1. 可以增加更多环境描写，展现未来世界的细节\n2. 主角的内心独白可以更丰富，增强情感共鸣\n3. 建议在第一章末尾埋下伏笔，为后续剧情做铺垫\n\n字数统计：约1200字\n阅读时长：约5分钟\n\n审校完成，可以进入下一章创作。'
    ];
    
    // 定时器，模拟每个智能体的工作
    this._mainTimer = setInterval(() => {
      // 检查是否完成
      if (currentIndex >= totalAgents) {
        this.clearAllTimers();
        this.setData({
          isRunning: false,
          isCompleted: true
        });
        
        // 保存到历史记录
        this.saveToHistory();
        
        wx.showToast({
          title: '创作完成！',
          icon: 'success'
        });
        return;
      }
      
      // 检查页面是否还在显示
      if (!this.data.isRunning) {
        this.clearAllTimers();
        return;
      }
      
      // 保存当前索引的本地副本
      const agentIndex = currentIndex;
      
      // 更新当前智能体状态为"运行中"
      this.setData({
        [`agents[${agentIndex}].status`]: 'running',
        [`agents[${agentIndex}].statusText`]: '进行中'
      });
      
      // 模拟进度增长
      let progress = 0;
      this._progressTimer = setInterval(() => {
        // 检查页面是否还在显示
        if (!this.data.isRunning) {
          clearInterval(this._progressTimer);
          this._progressTimer = null;
          return;
        }
        
        progress += 10;
        if (progress > 100) {
          progress = 100;
        }
        
        // 使用路径更新单个属性
        this.setData({ [`agents[${agentIndex}].progress`]: progress });
        
        if (progress >= 100) {
          clearInterval(this._progressTimer);
          this._progressTimer = null;
          
          // 完成当前智能体 - 直接使用完整的outputs数组
          this.setData({
            [`agents[${agentIndex}].status`]: 'completed',
            [`agents[${agentIndex}].statusText`]: '已完成',
            [`agents[${agentIndex}].output`]: outputs[agentIndex] || '任务完成'
          });
          
          // 移动到下一个智能体
          currentIndex++;
        }
      }, 500);
      
    }, 5000);
  },

  /**
   * 暂停创作
   */
  pauseCreation() {
    this.clearAllTimers();
    this.setData({ isRunning: false });
    wx.showToast({
      title: '已暂停',
      icon: 'none'
    });
  },

  /**
   * 查看成稿
   */
  viewManuscript() {
    // 生成完整成稿内容
    const manuscript = this.generateManuscript();
    
    // 保存到本地存储
    wx.setStorageSync('current_manuscript', manuscript);
    
    // 跳转到成稿预览页面
    wx.navigateTo({
      url: `/pages/manuscript/manuscript?title=${encodeURIComponent(this.data.storyTitle)}&genre=${encodeURIComponent(this.data.genre)}&chapters=3`
    });
  },

  /**
   * 生成完整成稿
   */
  generateManuscript() {
    // 收集所有智能体的输出
    const agents = this.data.agents;
    const outputs = agents.map(agent => agent.output).filter(output => output);
    
    // 组合成完整故事
    let manuscript = `《${this.data.storyTitle}》\n\n`;
    manuscript += `题材：${this.data.genre}\n\n`;
    manuscript += `---\n\n`;
    
    outputs.forEach((output, index) => {
      manuscript += `${output}\n\n`;
    });
    
    return manuscript;
  },

  /**
   * 保存到历史记录
   */
  saveToHistory() {
    const story = {
      id: 'story_' + Date.now(),
      title: this.data.storyTitle,
      genre: this.data.genre,
      mode: this.data.mode || 'quick',
      status: '已完成',
      chapters: this.data.chapters || 3,
      wordCount: this.generateManuscript().length,
      manuscript: this.generateManuscript(),
      createdAt: this.formatDate(new Date())
    };
    
    // 获取现有历史记录
    let stories = wx.getStorageSync('stories') || [];
    
    // 添加到列表开头
    stories.unshift(story);
    
    // 保存到本地存储
    wx.setStorageSync('stories', stories);
    
    console.log('已保存到历史记录:', story.title);
  },

  /**
   * 格式化日期
   */
  formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  },

  /**
   * 导出故事
   */
  exportStory() {
    wx.showActionSheet({
      itemList: ['复制全文', '查看成稿', '分享给朋友'],
      success: (res) => {
        switch (res.tapIndex) {
          case 0:
            this.copyManuscript();
            break;
          case 1:
            this.viewManuscript();
            break;
          case 2:
            this.shareManuscript();
            break;
        }
      }
    });
  },

  /**
   * 复制成稿
   */
  copyManuscript() {
    const manuscript = this.generateManuscript();
    wx.setClipboardData({
      data: manuscript,
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
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  /**
   * 分享给朋友
   */
  shareManuscript() {
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
      title: `我用AI创作了一个${this.data.genre}故事！`,
      path: '/pages/studio/studio?genre=' + encodeURIComponent(this.data.genre)
    };
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline() {
    return {
      title: `我用AI创作了一个${this.data.genre}故事！`,
      query: 'genre=' + encodeURIComponent(this.data.genre)
    };
  }
});
