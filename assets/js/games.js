// ====== games.js — 数独 + 呼吸放松 + 音乐播放器 ======

// ====== 数独常量 ======
const SUDO_BASE = [
  [5, 3, 4, 6, 7, 8, 9, 1, 2],
  [6, 7, 2, 1, 9, 5, 3, 4, 8],
  [1, 9, 8, 3, 4, 2, 5, 6, 7],
  [8, 5, 9, 7, 6, 1, 4, 2, 3],
  [4, 2, 6, 8, 5, 3, 7, 9, 1],
  [7, 1, 3, 9, 2, 4, 8, 5, 6],
  [9, 6, 1, 5, 3, 7, 2, 8, 4],
  [2, 8, 7, 4, 1, 9, 6, 3, 5],
  [3, 4, 5, 2, 8, 6, 1, 7, 9],
];
const SUDO_DIFFS = { easy: 45, normal: 35, hard: 27 };

let sudoSolution = [],
  sudoBoard = [],
  sudoGiven = [],
  sudoSelected = null,
  sudoMode = 'easy',
  sudoTimer = 0,
  sudoTimerId = null,
  sudoStarted = false,
  sudoDone = false;

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

function genSudo() {
  let grid = SUDO_BASE.map((r) => [...r]);
  const bands = [
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
    ],
    stacks = [
      [0, 1, 2],
      [3, 4, 5],
      [6, 7, 8],
    ];
  for (let b of bands) {
    shuffle(b);
    const [r1, r2, r3] = b;
    const t1 = grid[r1],
      t2 = grid[r2],
      t3 = grid[r3];
    grid[r1] = t1;
    grid[r2] = t2;
    grid[r3] = t3;
  }
  for (let s of stacks) {
    shuffle(s);
    for (let r = 0; r < 9; r++) {
      const vals = s.map((c) => grid[r][c]);
      s.forEach((c, i) => {
        grid[r][c] = vals[i];
      });
    }
  }
  const labels = [1, 2, 3, 4, 5, 6, 7, 8, 9];
  shuffle(labels);
  labels.unshift(0);
  for (let r = 0; r < 9; r++)
    for (let c = 0; c < 9; c++) grid[r][c] = labels[grid[r][c]];
  if (Math.random() > 0.5) {
    const t = [];
    for (let r = 0; r < 9; r++) {
      t[r] = [];
      for (let c = 0; c < 9; c++) t[r][c] = grid[c][r];
    }
    grid = t;
  }
  sudoSolution = grid;
  const count = SUDO_DIFFS[sudoMode];
  sudoGiven = Array(9)
    .fill()
    .map(() => Array(9).fill(false));
  sudoBoard = grid.map((r) => [...r]);
  const cells = [];
  for (let r = 0; r < 9; r++)
    for (let c = 0; c < 9; c++) cells.push([r, c]);
  shuffle(cells);
  for (let i = 0; i < 81 - count; i++) {
    const [r, c] = cells[i];
    sudoBoard[r][c] = 0;
  }
  for (let r = 0; r < 9; r++)
    for (let c = 0; c < 9; c++) sudoGiven[r][c] = sudoBoard[r][c] !== 0;
}

let _lastFocus = null;

export function startSudoku() {
  _lastFocus = document.activeElement;
  genSudo();
  sudoSelected = null;
  sudoTimer = 0;
  sudoStarted = false;
  sudoDone = false;
  if (sudoTimerId) clearInterval(sudoTimerId);
  sudoTimerId = null;
  document.getElementById('sudoOverlay').classList.add('on');
  renderSudo();
}

export function closeSudoku() {
  if (sudoTimerId) clearInterval(sudoTimerId);
  document.getElementById('sudoOverlay').classList.remove('on');
  if (_lastFocus && _lastFocus.focus) _lastFocus.focus();
}

function startTimer() {
  if (sudoStarted) return;
  sudoStarted = true;
  sudoTimerId = setInterval(() => {
    sudoTimer++;
    updateTimer();
  }, 1000);
}

function updateTimer() {
  const el = document.getElementById('sudoTime');
  if (el) el.textContent = fmtTime(sudoTimer);
}

function fmtTime(s) {
  const m = Math.floor(s / 60),
    sec = s % 60;
  return m + ':' + (sec < 10 ? '0' : '') + sec;
}

function selectCell(r, c) {
  if (sudoDone || sudoGiven[r][c]) return;
  startTimer();
  if (
    sudoSelected &&
    sudoSelected[0] === r &&
    sudoSelected[1] === c
  ) {
    sudoSelected = null;
    renderSudo();
    return;
  }
  sudoSelected = [r, c];
  renderSudo();
}

function inputNum(n) {
  if (!sudoSelected || sudoDone) return;
  const [r, c] = sudoSelected;
  if (sudoGiven[r][c]) return;
  startTimer();
  sudoBoard[r][c] = n;
  renderSudo();
  if (checkWin()) {
    sudoDone = true;
    if (sudoTimerId) clearInterval(sudoTimerId);
    saveScore();
    renderSudo();
  }
}

function eraseCell() {
  if (!sudoSelected || sudoDone) return;
  const [r, c] = sudoSelected;
  if (sudoGiven[r][c]) return;
  sudoBoard[r][c] = 0;
  renderSudo();
}

function hasConflict(r, c) {
  const v = sudoBoard[r][c];
  if (v === 0) return false;
  for (let i = 0; i < 9; i++) {
    if (i !== c && sudoBoard[r][i] === v) return true;
    if (i !== r && sudoBoard[i][c] === v) return true;
  }
  const br = Math.floor(r / 3) * 3,
    bc = Math.floor(c / 3) * 3;
  for (let i = br; i < br + 3; i++)
    for (let j = bc; j < bc + 3; j++)
      if ((i !== r || j !== c) && sudoBoard[i][j] === v) return true;
  return false;
}

function checkWin() {
  for (let r = 0; r < 9; r++)
    for (let c = 0; c < 9; c++)
      if (sudoBoard[r][c] !== sudoSolution[r][c]) return false;
  return true;
}

export function renderSudo(view = 'game') {
  const panel = document.getElementById('sudoPanel');
  let h = '';
  if (view === 'lb') {
    h = renderLB();
    panel.innerHTML = h;
    return;
  }
  h += `<h2>🧮 数独</h2><div class="g-sub">${sudoDone ? '🎉 恭喜通关！' : '填入1-9使每行/列/宫不重复'}</div>`;
  h += `<div class="sudo-modes">`;
  ['easy', 'normal', 'hard'].forEach((m) => {
    h += `<button class="${sudoMode === m ? 'on' : ''}" onclick="changeMode('${m}')">${m === 'easy' ? '😊 简单' : m === 'normal' ? '🤔 普通' : '🔥 困难'}</button>`;
  });
  h += `</div>`;
  h += `<div class="sudo-info"><span>⏱ <span id="sudoTime">${fmtTime(sudoTimer)}</span></span><span>💡 ${SUDO_DIFFS[sudoMode]}</span><span><a href="javascript:renderSudo('lb')" style="color:var(--muted);font-size:12px">🏆 排行榜</a></span></div>`;
  h += `<div class="sudo-board">`;
  for (let r = 0; r < 9; r++)
    for (let c = 0; c < 9; c++) {
      const v = sudoBoard[r][c];
      let cls = 'sudo-cell';
      if (sudoGiven[r][c]) cls += ' given';
      if (
        sudoSelected &&
        sudoSelected[0] === r &&
        sudoSelected[1] === c
      )
        cls += ' selected';
      if (
        sudoSelected &&
        v > 0 &&
        v === sudoBoard[sudoSelected[0]][sudoSelected[1]] &&
        !(sudoSelected[0] === r && sudoSelected[1] === c) &&
        sudoBoard[sudoSelected[0]][sudoSelected[1]] > 0
      )
        cls += ' same-num';
      if (!sudoGiven[r][c] && v > 0 && hasConflict(r, c))
        cls += ' conflict';
      h += `<div class="${cls}" onclick="selectCell(${r},${c})">${v > 0 ? v : ''}</div>`;
    }
  h += `</div>`;
  if (!sudoDone) {
    h += `<div class="sudo-numpad">`;
    for (let n = 1; n <= 9; n++)
      h += `<button onclick="inputNum(${n})">${n}</button>`;
    h += `<button class="erase" onclick="eraseCell()">⌫ 清除</button>`;
    h += `</div>`;
  } else {
    h += `<div style="text-align:center;font-size:24px;margin:12px 0">🎉</div>`;
    h += `<div style="text-align:center;color:var(--gold);font-size:14px">完成时间：${fmtTime(sudoTimer)}</div>`;
  }
  h += `<button class="sc-btn" style="width:100%;margin-top:4px" onclick="startSudoku()">🔄 新游戏</button>`;
  h += `<button class="game-close" onclick="closeSudoku()">关闭</button>`;
  panel.innerHTML = h;
}

export function changeMode(m) {
  sudoMode = m;
  startSudoku();
}

// 排行榜
function loadLB() {
  try {
    return JSON.parse(localStorage.getItem('sudoku_lb') || '[]');
  } catch (e) {
    return [];
  }
}

function saveScore() {
  const name = prompt('恭喜！请输入你的昵称：', '玩家');
  if (!name) return;
  const lb = loadLB();
  lb.push({
    name: name.substring(0, 10),
    mode: sudoMode,
    time: sudoTimer,
    date: new Date().toISOString().slice(0, 10),
  });
  lb.sort((a, b) => {
    const o = { easy: 0, normal: 1, hard: 2 };
    return o[b.mode] - o[a.mode] || a.time - b.time;
  });
  if (lb.length > 50) lb.length = 50;
  localStorage.setItem('sudoku_lb', JSON.stringify(lb));
}

export function renderLB(lbMode = sudoMode) {
  const lb = loadLB();
  const modes = ['easy', 'normal', 'hard'];
  const names = { easy: '简单', normal: '普通', hard: '困难' };
  let h = `<h2>🏆 排行榜</h2>`;
  h += `<div class="lb-tabs">`;
  modes.forEach((m) => {
    h += `<button class="${lbMode === m ? 'on' : ''}" onclick="renderLB('${m}')">${names[m]}</button>`;
  });
  h += `</div>`;
  const filtered = lb.filter((e) => e.mode === lbMode);
  if (!filtered.length) {
    h += `<div class="lb-empty">暂无记录，通关后上榜 🏅</div>`;
  } else {
    h += `<table class="lb-table"><tr><th>#</th><th>玩家</th><th>时间</th><th>日期</th></tr>`;
    filtered.slice(0, 10).forEach((e, i) => {
      h += `<tr><td>${i + 1}</td><td>${e.name}</td><td>${fmtTime(e.time)}</td><td>${e.date}</td></tr>`;
    });
    h += `</table>`;
  }
  h += `<button class="sc-btn" style="width:100%;margin-top:8px" onclick="renderSudo('game')">← 返回游戏</button>`;
  h += `<button class="game-close" onclick="closeSudoku()">关闭</button>`;
  return h;
}

// 数独键盘操作
document.addEventListener('keydown', (e) => {
  if (
    !document.getElementById('sudoOverlay').classList.contains('on') ||
    sudoDone
  )
    return;
  if (e.key >= '1' && e.key <= '9') inputNum(parseInt(e.key));
  else if (e.key === 'Backspace' || e.key === 'Delete') eraseCell();
  else if (e.key === 'ArrowUp' && sudoSelected)
    selectCell(Math.max(0, sudoSelected[0] - 1), sudoSelected[1]);
  else if (e.key === 'ArrowDown' && sudoSelected)
    selectCell(Math.min(8, sudoSelected[0] + 1), sudoSelected[1]);
  else if (e.key === 'ArrowLeft' && sudoSelected)
    selectCell(sudoSelected[0], Math.max(0, sudoSelected[1] - 1));
  else if (e.key === 'ArrowRight' && sudoSelected)
    selectCell(sudoSelected[0], Math.min(8, sudoSelected[1] + 1));
  else return;
  e.preventDefault();
});

// 数独面板关闭 (点击遮罩)
document.getElementById('sudoOverlay').onclick = function (e) {
  if (e.target === this) closeSudoku();
};

// ====== 呼吸放松 ======
let breathTimer = null;

export function startBreath() {
  _lastFocus = document.activeElement;
  document.getElementById('breathOverlay').classList.add('on');
  runBreath();
}

export function stopBreath() {
  document.getElementById('breathOverlay').classList.remove('on');
  clearTimeout(breathTimer);
  const c = document.getElementById('breathCircle');
  c.textContent = '准备';
  c.className = 'breath-circle';
  if (_lastFocus && _lastFocus.focus) _lastFocus.focus();
}

function runBreath() {
  const c = document.getElementById('breathCircle');
  let p = 0;
  const ph = [
    { t: '吸气', cl: 'breath-circle inhale', d: 4000 },
    { t: '屏息', cl: 'breath-circle hold', d: 2000 },
    { t: '呼气', cl: 'breath-circle exhale', d: 4000 },
    { t: '静息', cl: 'breath-circle', d: 2000 },
  ];
  (function t() {
    const x = ph[p % 4];
    c.textContent = x.t;
    c.className = x.cl;
    p++;
    breathTimer = setTimeout(t, x.d);
  })();
}

document.getElementById('breathOverlay').onclick = function (e) {
  if (e.target === this) stopBreath();
};
document.getElementById('breathBtn').onclick = startBreath;

// ====== 音乐播放器 ======
export function toggleMusic() {
  const p = document.getElementById('musicPanel'),
    t = document.getElementById('musicToggle');
  if (p.style.display === 'none') {
    p.style.display = '';
    t.textContent = '收起 ▾';
  } else {
    p.style.display = 'none';
    t.textContent = '展开 ▸';
  }
}

// 挂载到 window
window.startSudoku = startSudoku;
window.closeSudoku = closeSudoku;
window.renderSudo = renderSudo;
window.changeMode = changeMode;
window.renderLB = renderLB;
window.selectCell = selectCell;
window.inputNum = inputNum;
window.eraseCell = eraseCell;
window.startBreath = startBreath;
window.stopBreath = stopBreath;
window.toggleMusic = toggleMusic;
