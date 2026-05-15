// ====== ozon.js — Ozon 精选卡片 + 详情 ======

export async function loadFeaturedPost() {
  try {
    const r = await fetch('posts/featured_ozon_pick.json?v=' + Date.now());
    if (!r.ok) throw Error('HTTP ' + r.status);
    window.featuredPost = await r.json();
  } catch (e) {
    window.featuredPost = null;
  }
}

export function showFeaturedDetail() {
  if (!window.featuredPost || !window.featuredPost.slug) return;
  window.showArticle(window.featuredPost.slug, 'ozon-pick');
}

// Featured section HTML 生成 (在 render() 中调用)
export function buildFeaturedHTML() {
  const fp = window.featuredPost;
  if (!fp || !fp.products || !fp.products.length) return '';

  const verified = fp.verified;
  const top3 = fp.products.slice(0, 3);
  const score = Math.round(
    fp.products.reduce((s, p) => s + (p.trend_score || 50), 0) /
      Math.max(1, fp.products.length)
  );
  const medals = ['🥇', '🥈', '🥉'];

  return `<div class="featured-section">
    <div class="featured-post-card" onclick="showFeaturedDetail()" tabindex="0" role="button" onkeydown="if(event.key==='Enter')showFeaturedDetail()">
      <div class="fp-inner">
        <div class="fp-meta">
          <span class="fp-tag">🏆 OZON 每日选品</span>
          ${verified ? '<span class="featured-badge verified">✅ 已验证</span>' : '<span class="featured-badge live">● 实时数据</span>'}
          <span class="fp-date" style="margin-left:auto">📅 ${fp.date}</span>
        </div>
        <div class="fp-title-row">
          <h3>🇷🇺 俄罗斯 Wildberries 平台 · 今日精选 ${fp.products.length} 款高潜力商品</h3>
          <div class="fp-score"><span class="sval">${score}</span><span class="slab">趋势分</span></div>
        </div>
        <div class="fp-products-preview">
          ${top3
            .map(
              (p, i) => `<div class="fp-mini">
            <div class="fm-rank">${medals[i]} 推荐 #${i + 1}</div>
            <div class="fm-name" title="${(p.product_name_cn || p.product_name_ru || '').replace(/"/g, '&quot;')}">${p.product_name_cn || p.product_name_ru || '—'}</div>
            <div class="fm-info">
              <span class="fm-price">${p.price_rub ? p.price_rub.toLocaleString() + ' ₽' : '—'}</span>
              ${p.rating > 0 ? `<span class="fm-rating">★ ${p.rating}</span>` : ''}
              ${p.review_count > 0 ? `<span>${p.review_count} 评</span>` : ''}
              ${p.trend_score >= 70 ? '<span style="color:var(--gold);font-size:10px">🔥 热</span>' : ''}
            </div>
          </div>`
            )
            .join('')}
        </div>
        <div class="fp-stats">
          <span><span class="fp-live"></span> <span class="fp-val">${fp.products.length}</span> 款推荐商品</span>
          <span>📰 <span class="fp-val">${fp.data_sources ? fp.data_sources.length : 0}</span> 数据源</span>
          <span>📊 趋势评分 <span class="fp-val">${score}/100</span></span>
          <span style="margin-left:auto">🕐 ${(fp.generated_at || '').substring(11, 16) || fp.date}</span>
        </div>
      </div>
    </div>
  </div>`;
}

// 挂载到 window
window.loadFeaturedPost = loadFeaturedPost;
window.showFeaturedDetail = showFeaturedDetail;
window.buildFeaturedHTML = buildFeaturedHTML;
