// ====== article.js — 文章详情 + 目录生成 + 分享 ======

export function buildTOC(md) {
  const hs = [...md.matchAll(/^(#{2,3})\s+(.+)$/gm)];
  if (hs.length < 2) return '';
  let h =
    '<nav class="toc" aria-label="文章目录"><div class="toc-title">📑 目录</div>';
  hs.forEach((m) => {
    const lv = m[1].length,
      t = m[2],
      id = t.replace(/[^\w一-鿿]/g, '-').toLowerCase();
    h += `<a class="${lv === 3 ? 'toc-h3' : ''}" href="javascript:document.getElementById('${id}').scrollIntoView({behavior:'smooth'})">${lv === 2 ? '●' : '◦'} ${t}</a>`;
  });
  h += '</nav>';
  return h;
}

// marked.js 自定义 heading 渲染
if (typeof marked !== 'undefined') {
  marked.use({
    renderer: {
      heading(t) {
        const id = t.text.replace(/[^\w一-鿿]/g, '-').toLowerCase();
        return `<h${t.depth} id="${id}">${t.text}</h${t.depth}>`;
      },
    },
  });
}

export async function showArticle(slug, cat) {
  const wrap = document.getElementById('pageWrap');
  wrap.innerHTML = `<div class="article-full"><div class="skeleton" style="grid-template-columns:1fr">${Array(4)
    .fill(
      '<div class="skel-card"><div class="s-line"></div><div class="s-line"></div><div class="s-line"></div></div>'
    )
    .join('')}</div></div>`;
  window.scrollTo(0, 0);
  try {
    const r = await fetch('posts/' + slug + '.md');
    if (!r.ok) throw Error('404');
    const md = await r.text(),
      post = window.posts.find((p) => p.slug === slug);
    const colors = {
      'cross-border': 'var(--cyan)',
      fitness: 'var(--green)',
      'ai-news': 'var(--purple)',
    };
    const c = colors[cat] || 'var(--cyan)';
    const toc = buildTOC(md);
    const shareURL = encodeURIComponent(
      `https://20020426.top/#post/${slug}/${cat}`
    );
    const shareTitle = encodeURIComponent(post?.title || '');
    wrap.innerHTML = `<div class="article-full"><article class="article" aria-label="文章详情"><button class="back-btn" onclick="switchTab('${cat}')">← 返回${window.catName(cat)}</button><h1>${post?.title || ''}</h1><div class="art-meta"><span style="color:${c}">${window.SUB_NAMES[post?.sub] || window.catName(cat)}</span><span aria-hidden="true">·</span><span>${post?.date || ''}</span><span aria-hidden="true">·</span><span>${window.readTime(md)}</span>${post?.source_name ? `<span aria-hidden="true">·</span><span class="art-source">📰 ${post.source_name}</span>` : ''}</div>${toc}<div class="content">${marked.parse(md)}</div><div class="share-row"><span style="font-size:12px;color:var(--muted);line-height:2">分享：</span><button onclick="navigator.clipboard.writeText('https://20020426.top/#post/${slug}/${cat}');this.textContent='✓ 已复制';setTimeout(()=>this.textContent='📋 复制链接',1500)">📋 复制链接</button><a href="https://twitter.com/intent/tweet?url=${shareURL}&text=${shareTitle}" target="_blank" rel="noopener" style="padding:6px 16px;border-radius:14px;border:1px solid var(--border);font-size:12px;color:var(--muted)">𝕏 分享</a></div></article></div>`;
    document.querySelectorAll('.content h2,.content h3').forEach((h) => {
      if (!h.id)
        h.id = h.textContent.replace(/[^\w一-鿿]/g, '-').toLowerCase();
    });
  } catch (e) {
    wrap.innerHTML = `<div class="article-full"><div class="error-box"><p>文章加载失败</p><button onclick="switchTab('${cat}')">← 返回</button><button onclick="showArticle('${slug}','${cat}')">🔄 重试</button></div></div>`;
  }
}

// 挂载到 window
window.showArticle = showArticle;
window.buildTOC = buildTOC;
