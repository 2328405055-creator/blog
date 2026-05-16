// ====== search.js — Tab 切换 + 搜索 + 分页 + 歇后语/字谜 ======

// MiniSearch 实例 (延迟初始化)
let _miniSearch = null;

export function getMiniSearch() {
  return _miniSearch;
}

export function buildSearchIndex(posts) {
  if (typeof MiniSearch === 'undefined') {
    console.warn('MiniSearch 未加载，降级到基础搜索');
    return;
  }
  _miniSearch = new MiniSearch({
    fields: ['title', 'excerpt', 'catName'],
    storeFields: ['slug', 'title', 'date', 'cat', 'sub', 'excerpt'],
    searchOptions: {
      prefix: true,
      fuzzy: 0.2,
      boost: { title: 3, excerpt: 1.5, catName: 1 },
    },
  });

  const docs = posts.map((p, i) => ({
    id: i,
    slug: p.slug,
    title: p.title,
    excerpt: (p.excerpt || '').replace(/<[^>]+>/g, '').replace(/#/g, ''),
    catName: catName(p.cat),
    cat: p.cat,
    sub: p.sub,
    date: p.date,
  }));
  _miniSearch.addAll(docs);
  console.log(`MiniSearch 索引: ${docs.length} 篇文章`);
}

export function searchPosts(query) {
  if (!_miniSearch || !query.trim()) {
    return null; // 返回 null 表示用原始过滤
  }
  const results = _miniSearch.search(query, { prefix: true, fuzzy: 0.2 });
  const matchIds = new Set(results.map((r) => r.id));
  const matched = window.posts.filter((_, i) => matchIds.has(i));
  const unmatched = window.posts.filter((_, i) => !matchIds.has(i));
  return [...matched, ...unmatched]; // 匹配的在前，其余在后
}

export function catName(c) {
  const m = {
    'cross-border': '跨境教程',
    fitness: '每日健身',
    'ai-news': 'AI学习',
    'ozon-pick': 'Ozon选品',
  };
  return m[c] || c;
}

export function readTime(t) {
  return Math.max(1, Math.ceil((t || '').length / 8)) + ' 分钟阅读';
}

export function copyQuote() {
  navigator.clipboard.writeText(window.QUOTE).then(() => {
    const b = document.querySelector('.q-act button');
    if (!b) return;
    b.textContent = '✓ 已复制';
    b.classList.add('done');
    setTimeout(() => {
      b.textContent = '📋 复制';
      b.classList.remove('done');
    }, 2000);
  }).catch(() => {});
}

export function revealXHY() {
  if (window.todayXHY.show) {
    window.pickXHY();
    window.render();
  } else {
    window.todayXHY.show = true;
    window.render();
  }
}

export function checkRiddle() {
  const i = document.getElementById('riddleInput'),
    f = document.getElementById('riddleFeedback');
  if (!i || !f) return;
  const v = i.value.trim();
  if (!v) return;
  if (v === window.riddleAnswer) {
    f.textContent = '✅ 答对了！';
    f.className = 'sc-fb ok';
    setTimeout(() => {
      window.pickZM();
      window.render();
    }, 1500);
  } else {
    f.textContent = '❌ 不对，再试试';
    f.className = 'sc-fb no';
  }
}

export function switchTab(t) {
  window.currentTab = t;
  window.currentSub = 'all';
  window.currentSearch = '';
  window.currentPage = 1;
  window.render();
  window.scrollTo(0, 0);
  closeMenu();
}

export function switchSub(s) {
  window.currentSub = s;
  window.currentPage = 1;
  window.render();
}

export function onSearch(v) {
  window.currentSearch = v;
  window.currentPage = 1;
  window.render();
}

export function goPage(n) {
  window.currentPage = Math.max(1, n);
  window.render();
  document.getElementById('articleList').scrollIntoView({ behavior: 'smooth' });
}

export function goHome() {
  switchTab('all');
}

export function toggleMenu() {
  const m = document.getElementById('navMenu');
  m.classList.toggle('open');
  document
    .getElementById('hamBtn')
    .setAttribute('aria-expanded', m.classList.contains('open'));
}

export function closeMenu() {
  document.getElementById('navMenu').classList.remove('open');
  document.getElementById('hamBtn').setAttribute('aria-expanded', 'false');
}

// 挂载到 window
window.catName = catName;
window.readTime = readTime;
window.copyQuote = copyQuote;
window.revealXHY = revealXHY;
window.checkRiddle = checkRiddle;
window.switchTab = switchTab;
window.switchSub = switchSub;
window.onSearch = onSearch;
window.goPage = goPage;
window.goHome = goHome;
window.toggleMenu = toggleMenu;
window.closeMenu = closeMenu;
window.buildSearchIndex = buildSearchIndex;
window.searchPosts = searchPosts;
