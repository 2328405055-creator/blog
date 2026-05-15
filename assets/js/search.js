// ====== search.js — Tab 切换 + 搜索 + 分页 + 歇后语/字谜 ======

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
