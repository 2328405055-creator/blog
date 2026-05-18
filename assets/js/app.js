// ====== app.js — 主入口：数据加载 + 渲染 + 初始化 ======

// 导入所有模块 (副作用: 挂载函数到 window + 初始化主题/粒子)
import './theme.js';
import './games.js';
import './ozon.js';
import './article.js';
import './search.js';

// ====== 全局状态 ======
window.posts = [];
window.currentTab = 'all';
window.currentSub = 'all';
window.currentSearch = '';
window.currentPage = 1;
window.rubRate = null;
window.rateCacheTime = 0;
window.featuredPost = null;

// 常量
window.SITE_START = new Date('2025-09-05');
window.PER_PAGE = 10;

window.SUBS = {
  'cross-border': [
    { key: 'all', name: '全部' },
    { key: 'selection', name: '📦 选品技巧' },
    { key: 'ozon', name: '🔵 Ozon运营' },
    { key: 'yandex', name: '🟡 Yandex运营' },
    { key: 'russia-market', name: '🇷🇺 俄罗斯市场' },
    { key: 'logistics', name: '🚚 物流收款' },
    { key: 'tools', name: '🛠 工具教程' },
  ],
  fitness: [
    { key: 'all', name: '全部' },
    { key: 'male', name: '👨 男性训练' },
    { key: 'female', name: '👩 女性训练' },
    { key: 'yoga-mat', name: '🧘 瑜伽垫' },
    { key: 'plan', name: '📅 每日计划' },
    { key: 'diet', name: '🥗 饮食建议' },
  ],
  'ai-news': [
    { key: 'all', name: '全部' },
    { key: 'ai-tools', name: '🤖 AI工具' },
    { key: 'ai-industry', name: '📡 行业动态' },
    { key: 'ai-ecommerce', name: '🛒 AI与电商' },
    { key: 'ai-tutorial', name: '📖 AI教程' },
  ],
  'ozon-pick': [
    { key: 'all', name: '全部' },
    { key: 'daily-select', name: '🏆 今日推荐' },
    { key: 'electronics', name: '🔌 电子产品' },
    { key: 'home-kitchen', name: '🏠 家居厨房' },
    { key: 'clothing', name: '👕 服装鞋包' },
    { key: 'sports-outdoor', name: '🏃 运动户外' },
    { key: 'beauty-health', name: '💄 美妆健康' },
    { key: 'kids-toys', name: '👶 母婴玩具' },
  ],
};

// SUB_NAMES 扁平化
window.SUB_NAMES = {};
Object.values(window.SUBS).forEach((a) =>
  a.forEach((s) => (window.SUB_NAMES[s.key] = s.name))
);

window.QUOTE = `你来了，愿你在人海茫茫中，仍能像一朵小小的白云，自由地飘过蓝天，不惊扰任何人，却把自己的洁白与柔软留给这世界。愿你的心永远清澈如山间清泉，无论世事如何喧嚣，都能映照出星光与月色。愿你遇见的每一次风雨，都能化作滋养生命的甘露；愿你走过的每一条路，都开满安静而温柔的花。愿你带着孩子般的纯真与对美好的相信，一路平安，一路向光。`;

const XIEHOUYU = [
  ['外甥打灯笼', '照旧（舅）'],
  ['孔夫子搬家', '尽是输（书）'],
  ['小葱拌豆腐', '一清二白'],
  ['哑巴吃黄连', '有苦说不出'],
  ['竹篮打水', '一场空'],
  ['泥菩萨过江', '自身难保'],
  ['飞蛾扑火', '自取灭亡'],
  ['狗咬吕洞宾', '不识好人心'],
  ['姜太公钓鱼', '愿者上钩'],
  ['画蛇添足', '多此一举'],
  ['掩耳盗铃', '自欺欺人'],
  ['对牛弹琴', '白费劲'],
  ['海底捞针', '无处寻'],
  ['铁公鸡', '一毛不拔'],
  ['千里送鹅毛', '礼轻情意重'],
  ['兔子尾巴', '长不了'],
  ['热锅上的蚂蚁', '团团转'],
  ['茶壶里煮饺子', '有口倒不出'],
  ['擀面杖吹火', '一窍不通'],
  ['猪八戒照镜子', '里外不是人'],
  ['瞎子点灯', '白费蜡'],
  ['肉包子打狗', '有去无回'],
  ['隔着门缝看人', '把人看扁了'],
  ['和尚打伞', '无法无天'],
  ['猴子捞月', '一场空'],
  ['鸡蛋里挑骨头', '找茬'],
  ['老虎屁股', '摸不得'],
  ['秋后的蚂蚱', '蹦跶不了几天'],
  ['司马昭之心', '路人皆知'],
  ['周瑜打黄盖', '一个愿打一个愿挨'],
  ['刘备借荆州', '有借无还'],
  ['王婆卖瓜', '自卖自夸'],
  ['黄鼠狼给鸡拜年', '没安好心'],
  ['打破砂锅', '问到底'],
  ['芝麻开花', '节节高'],
  ['八仙过海', '各显神通'],
];

const ZIMI = [
  ['一口吃掉牛尾巴', '告'],
  ['皇帝的新衣', '袭'],
  ['一千零一夜', '歼'],
  ['秀才进门', '闭'],
  ['半青半紫', '素'],
  ['争先恐后', '急'],
  ['半导体', '付'],
  ['吹灯', '黑'],
  ['独眼龙', '省'],
  ['二月平', '朋'],
  ['格外大方', '回'],
  ['黄昏', '晒'],
  ['九十九', '白'],
  ['文武双全', '斌'],
  ['一大二小', '奈'],
  ['十八子', '李'],
  ['三人行', '众'],
  ['三日', '晶'],
  ['十五天', '胖'],
  ['六十天', '朋'],
  ['一加一', '王'],
  ['一百减一', '白'],
  ['七人头上长了草', '花'],
  ['一箭穿心', '必'],
  ['一人一张口', '合'],
  ['山上还有山', '出'],
  ['十张口', '古'],
  ['一斗米', '料'],
  ['一只黑狗不叫不吼', '默'],
  ['差一点六斤', '兵'],
  ['需要一半留下一半', '雷'],
  ['推开又来', '摊'],
  ['多一半', '夕'],
  ['四方来合作', '器'],
  ['守门员', '闪'],
  ['没有人', '门'],
  ['刀出鞘', '力'],
  ['打断念头', '心'],
  ['手提包', '抱'],
];

window.todayXHY = null;
window.todayZM = null;
window.riddleAnswer = '';

window.pickXHY = function () {
  const x = XIEHOUYU[Math.floor(Math.random() * XIEHOUYU.length)];
  window.todayXHY = { q: x[0], a: x[1], show: false };
};

window.pickZM = function () {
  const z = ZIMI[Math.floor(Math.random() * ZIMI.length)];
  window.todayZM = { q: z[0], a: z[1] };
  window.riddleAnswer = z[1];
};

// ====== 数据加载 ======
async function fetchRate() {
  const now = Date.now();
  if (window.rubRate && now - window.rateCacheTime < 3600000) return;
  try {
    const r = await fetch('https://open.er-api.com/v6/latest/CNY');
    window.rubRate = (await r.json()).rates?.RUB || null;
    window.rateCacheTime = now;
  } catch (e) {
    /* ignore */
  }
}
window.fetchRate = fetchRate;

async function loadData(retry = true) {
  try {
    const r = await fetch('posts/posts.json?v=' + Date.now());
    if (!r.ok) throw Error('HTTP ' + r.status);
    window.posts = await r.json();
    window.posts.sort((a, b) => b.date.localeCompare(a.date));
    // 构建 MiniSearch 索引
    if (window.buildSearchIndex) window.buildSearchIndex(window.posts);
    return true;
  } catch (e) {
    console.error(e);
    if (retry) {
      await new Promise((r) => setTimeout(r, 2000));
      return loadData(false);
    }
    return false;
  }
}
window.loadData = loadData;

// ====== 渲染 ======
window.render = function () {
  let filtered = window.posts;
  if (window.currentTab !== 'all')
    filtered = filtered.filter((p) => p.cat === window.currentTab);
  if (window.currentSub !== 'all')
    filtered = filtered.filter((p) => p.sub === window.currentSub);
  if (window.currentSearch) {
    const result = window.searchPosts ? window.searchPosts(window.currentSearch) : null;
    if (result) {
      filtered = result;
    } else {
      const q = window.currentSearch.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.excerpt.toLowerCase().includes(q)
      );
    }
  }

  const totalPages = Math.max(1, Math.ceil(filtered.length / window.PER_PAGE));
  if (window.currentPage > totalPages) window.currentPage = totalPages;
  const start = (window.currentPage - 1) * window.PER_PAGE,
    pageItems = filtered.slice(start, start + window.PER_PAGE);

  const isHome =
    window.currentTab === 'all' &&
    window.currentSub === 'all' &&
    !window.currentSearch;
  const days = Math.ceil(
    (Date.now() - window.SITE_START) / 86400000
  );
  if (!window.todayXHY) window.pickXHY();
  if (!window.todayZM) window.pickZM();
  const now = new Date(),
    weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 星期${weekDays[now.getDay()]}`;
  const counts = {};
  for (let t of ['cross-border', 'fitness', 'ai-news', 'ozon-pick'])
    counts[t] = window.posts.filter((p) => p.cat === t).length;

  const wrap = document.getElementById('pageWrap');
  let html = '';

  // Hero
  html += `<section class="hero" aria-label="网站标题" style="grid-column:1/-1"><h1 class="site-name">猫明之主</h1><p class="site-desc">跨境教程 & 健身 & AI学习 · 每天进步一点点</p></section>`;

  // MAIN COLUMN
  html += `<div class="main-col">`;

  // Search
  html += `<div class="search-wrap"><input id="searchInput" placeholder="🔍 搜索文章..." value="${window.currentSearch.replace(/"/g, '&quot;')}" oninput="onSearch(this.value)" autocomplete="off" aria-label="搜索文章"></div>`;

  // Quote (home only)
  if (isHome) {
    html += `<div class="quote-card"><span class="qm" aria-hidden="true">"</span><p>${window.QUOTE}</p><div class="q-act"><button onclick="copyQuote()" aria-label="复制引言">📋 复制</button></div></div>`;
    html += `<div style="margin-bottom:20px"></div>`;
  }

  // Featured Ozon Pick
  if (isHome && window.featuredPost && window.featuredPost.products && window.featuredPost.products.length > 0) {
    html += window.buildFeaturedHTML();
  }

  // Sub filters
  if (window.currentTab !== 'all') {
    const subs = window.SUBS[window.currentTab] || [];
    html += `<div class="sub-row" role="group" aria-label="子分类">`;
    subs.forEach(
      (s) =>
        (html += `<button class="sub-btn${window.currentSub === s.key ? ' on' : ''}" onclick="switchSub('${s.key}')" aria-pressed="${window.currentSub === s.key}">${s.name}</button>`)
    );
    html += `</div>`;
  }

  // Posts
  html += `<div id="articleList">`;
  if (!pageItems.length) {
    html += `<div class="msg">✨ 暂无文章，等待更新</div>`;
  } else {
    html += `<div class="post-grid" role="list" aria-label="文章列表">`;
    pageItems.forEach((p) => {
      const colors = {
        'cross-border': 'var(--cyan)',
        fitness: 'var(--green)',
        'ai-news': 'var(--purple)',
        'ozon-pick': 'var(--gold)',
      };
      const c = colors[p.cat] || 'var(--cyan)';
      const isOzon = p.cat === 'ozon-pick';
      if (isOzon) {
        html += `<article class="post-card ozon-card" style="border-left:3px solid var(--gold)" tabindex="0" role="listitem" aria-label="阅读：${p.title}" onclick="showArticle('${p.slug}','${p.cat}')" onkeydown="if(event.key==='Enter')showArticle('${p.slug}','${p.cat}')">
          <div class="p-meta">
            <span class="p-tag" style="background:${c}22;color:${c}">🏆 ${window.SUB_NAMES[p.sub] || window.catName(p.cat)}</span>
            <span class="p-date">📅 ${p.date}</span>
            ${p.verified ? '<span style="font-size:10px;color:var(--green)">✅ 已验证</span>' : '<span style="font-size:10px;color:var(--gold)">● 实时</span>'}
          </div>
          <h3>${p.title}</h3>
          <p class="p-excerpt">${p.excerpt || ''}</p>
          <div class="p-meta" style="margin-top:6px">
            <span style="font-size:10px;color:var(--muted)">📰 ${p.source || 'Wildberries'}</span>
            <span style="font-size:10px;color:var(--muted);margin-left:auto">${p.date}</span>
          </div>
        </article>`;
      } else {
        html += `<article class="post-card" tabindex="0" role="listitem" aria-label="阅读：${p.title}" onclick="showArticle('${p.slug}','${p.cat}')" onkeydown="if(event.key==='Enter')showArticle('${p.slug}','${p.cat}')"><div class="p-meta"><span class="p-tag" style="background:${c}22;color:${c}">${window.SUB_NAMES[p.sub] || window.catName(p.cat)}</span><span class="p-date">${p.date}</span><span class="p-read">${window.readTime(p.title)}</span></div><h3>${p.title}</h3><p class="p-excerpt">${p.excerpt || ''}</p></article>`;
      }
    });
    html += `</div>`;
  }
  html += `</div>`;

  // Pagination
  if (totalPages > 1) {
    html += `<nav class="pager" aria-label="分页导航"><button onclick="goPage(${window.currentPage - 1})" ${window.currentPage <= 1 ? 'disabled' : ''}>←</button><span class="pg-info">${window.currentPage} / ${totalPages}</span>`;
    for (
      let i = Math.max(1, window.currentPage - 2);
      i <= Math.min(totalPages, window.currentPage + 2);
      i++
    )
      html += `<button onclick="goPage(${i})" class="${i === window.currentPage ? 'pg-on' : ''}" aria-current="${i === window.currentPage ? 'page' : 'false'}">${i}</button>`;
    html += `<button onclick="goPage(${window.currentPage + 1})" ${window.currentPage >= totalPages ? 'disabled' : ''}>→</button></nav>`;
  }
  html += `</div>`; // end main-col

  // SIDEBAR
  html += `<aside class="side-col" aria-label="侧边栏">`;

  // Music player
  html += `<div class="side-card" style="padding:0;overflow:hidden;border:0;background:transparent">
    <div style="padding:14px 16px 8px;display:flex;align-items:center;justify-content:space-between;cursor:pointer" onclick="toggleMusic()">
      <span class="sc-title" style="margin:0">🎵 猫明歌单</span>
      <span style="font-size:11px;color:var(--muted)" id="musicToggle">展开 ▸</span>
    </div>
    <div id="musicPanel" style="display:none">
      <iframe style="border-radius:0" src="https://open.spotify.com/embed/playlist/6Xr9Xc1vYQmgrYyqC4mY18?utm_source=generator" width="100%" height="380" frameBorder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
    </div>
  </div>`;

  // Date
  html += `<div class="side-card date-card"><div class="sc-title">📅 今日</div><div class="sc-main">${dateStr}</div><div class="sc-sub">已运行 <span style="color:var(--cyan)">${days}</span> 天</div></div>`;

  // Stats
  html += `<div class="side-card"><div class="sc-title">📊 文章统计</div><div class="side-stats"><div class="ss"><div class="n">${window.posts.length}</div><div class="l">全部</div></div><div class="ss"><div class="n">${counts['cross-border']}</div><div class="l">跨境</div></div><div class="ss"><div class="n">${counts['fitness']}</div><div class="l">健身</div></div><div class="ss"><div class="n">${counts['ai-news']}</div><div class="l">AI</div></div><div class="ss"><div class="n">${counts['ozon-pick']}</div><div class="l">选品</div></div></div></div>`;

  // Rate
  html += `<div class="side-card"><div class="side-rate">💱 1 CNY ≈ <span class="rv">${window.rubRate ? window.rubRate.toFixed(2) : '--'}</span> RUB</div></div>`;

  // Game Center
  html += `<div class="side-card"><div class="sc-title">🎮 小游戏</div><div style="display:flex;flex-direction:column;gap:6px">
    <button class="sc-btn" style="width:100%;text-align:left;font-size:13px;padding:8px 12px" onclick="startSudoku()">🧮 数独挑战</button>
    <button class="sc-btn" style="width:100%;text-align:left;font-size:13px;padding:8px 12px" onclick="startBreath()">🧘 呼吸放松</button>
  </div></div>`;

  // Quick links
  html += `<div class="side-card"><div class="sc-title">🔗 快捷入口</div><div class="side-links"><a href="javascript:switchTab('cross-border')">🚀 跨境教程</a><a href="javascript:switchTab('fitness')">💪 每日健身</a><a href="javascript:switchTab('ai-news')">🤖 AI学习</a><a href="javascript:switchTab('ozon-pick')">🏆 Ozon选品</a><a href="eat.html">🍳 今晚吃什么</a><a href="javascript:startBreath()">🧘 呼吸放松</a></div></div>`;

  html += `</aside>`; // end side-col

  // Save focus before rebuilding DOM
  const ae = document.activeElement;
  const aid = ae ? ae.id : null;
  const apos = ae && ae.selectionStart != null ? ae.selectionStart : null;
  wrap.innerHTML = html;
  wrap.style.animation = 'fadeIn 0.4s ease-out';

  // Restore focus
  if (aid) {
    const el = document.getElementById(aid);
    if (el) {
      el.focus();
      if (apos != null && el.setSelectionRange)
        el.setSelectionRange(apos, apos);
    }
  }

  document.getElementById('footer').innerHTML = `© 2026 猫明之主 · 已安静运行 <span class="days">${days}</span> 天 · <a href="javascript:startBreath()" style="color:var(--muted);text-decoration:none">🧘 呼吸放松</a>`;

  // Update nav tabs
  document.querySelectorAll('.nav-tabs button').forEach((b) => {
    b.setAttribute('aria-selected', b.dataset.tab === window.currentTab);
    b.classList.toggle('on', b.dataset.tab === window.currentTab);
  });
};

// ====== 滚动事件 ======
window.addEventListener('scroll', () => {
  const h =
    document.documentElement.scrollHeight - window.innerHeight;
  const pct = h > 0 ? Math.min(100, Math.round((window.scrollY / h) * 100)) : 0;
  const bar = document.getElementById('progress-bar');
  bar.style.width = pct + '%';
  bar.setAttribute('aria-valuenow', pct);
  document.getElementById('toTop').classList.toggle('show', window.scrollY > 400);
});

// ====== 回到顶部 ======
document.getElementById('toTop').onclick = function () {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// ====== 菜单按钮 ======
document.getElementById('hamBtn').onclick = window.toggleMenu;

// ====== 初始化 ======
(async function () {
  window.pickXHY();
  window.pickZM();
  document.getElementById('pageWrap').innerHTML = `<div class="main-col"><div class="skeleton">${Array(6)
    .fill(
      '<div class="skel-card"><div class="s-line"></div><div class="s-line"></div><div class="s-line"></div></div>'
    )
    .join('')}</div></div><aside class="side-col"><div class="side-card"><div class="sc-title">加载中...</div></div></aside>`;

  const [ok] = await Promise.all([
    window.loadData(),
    fetchRate(),
    window.loadFeaturedPost(),
  ]);
  if (!ok) {
    document.getElementById('pageWrap').innerHTML = `<div class="article-full"><div class="error-box"><p>⚠️ 文章加载失败</p><button onclick="location.reload()">🔄 重新加载</button></div></div>`;
    return;
  }
  window.render();
})();
