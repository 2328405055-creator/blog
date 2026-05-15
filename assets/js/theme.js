// ====== theme.js — 主题切换 + 粒子星空背景 ======

// 粒子颜色 (全局可变)
window.starColor = 'rgba(140,170,210,';

// 星空粒子背景
(function () {
  const c = document.getElementById('particles'),
    ctx = c.getContext('2d');
  let stars = [], w, h;

  function R() {
    w = c.width = window.innerWidth;
    h = c.height = window.innerHeight;
  }
  R();
  window.addEventListener('resize', R);

  for (let i = 0; i < 100; i++)
    stars.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.5 + 0.4,
      o: Math.random(),
      s: Math.random() * 0.004 + 0.0015,
    });

  (function D() {
    ctx.clearRect(0, 0, w, h);
    stars.forEach((s) => {
      s.o += s.s;
      if (s.o > 1 || s.o < 0) s.s *= -1;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `${window.starColor}${s.o * 0.55})`;
      ctx.fill();
    });
    requestAnimationFrame(D);
  })();
})();

// 主题管理
export function getTheme() {
  return document.documentElement.getAttribute('data-theme') || 'dark';
}

export function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
  updateThemeBtn();
}

export function toggleTheme() {
  setTheme(getTheme() === 'dark' ? 'light' : 'dark');
  updateParticlesForTheme();
}

export function updateThemeBtn() {
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = getTheme() === 'dark' ? '☀️' : '🌙';
}

export function updateParticlesForTheme() {
  window.starColor =
    getTheme() === 'dark' ? 'rgba(140,170,210,' : 'rgba(90,120,170,';
}

// 初始化主题
(function () {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') {
    setTheme('light');
    updateParticlesForTheme();
  } else {
    updateThemeBtn();
  }
})();

// 挂载到 window 供 HTML onclick 使用
window.getTheme = getTheme;
window.setTheme = setTheme;
window.toggleTheme = toggleTheme;
window.updateThemeBtn = updateThemeBtn;
window.updateParticlesForTheme = updateParticlesForTheme;
