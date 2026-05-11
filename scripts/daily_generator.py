#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日内容生成器 v3 — 真实来源驱动
- 从 Google News RSS 抓取跨境电商业内新闻
- 每篇文章标注来源、日期、可用搜索直连
- 健身内容优先嵌入 YouTube 教程视频
- 所有内容有据可查，来源可追溯
用法：python daily_generator.py [--push]
"""

import json, os, sys, re, hashlib, urllib.parse
from datetime import datetime, timedelta
from html import unescape

import feedparser
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
JSON_PATH = os.path.join(POSTS_DIR, "posts.json")
TRACKER_PATH = os.path.join(BASE_DIR, "scripts", "tracker.json")

# ============================================================
# 信息源配置
# ============================================================

RSS_SOURCES = {
    "cross-border": [
        # Google News — 跨境电商 + Ozon
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86+Ozon+%E4%BF%84%E7%BD%97%E6%96%AF+%E9%80%89%E5%93%81&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — Ozon 卖家 运营
        "https://news.google.com/rss/search?q=Ozon+%E5%8D%96%E5%AE%B6+%E8%BF%90%E8%90%A5+%E4%BF%84%E7%BD%97%E6%96%AF+%E7%94%B5%E5%95%86&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — 跨境电商 俄罗斯 市场
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86+%E4%BF%84%E7%BD%97%E6%96%AF+%E5%B8%82%E5%9C%BA+%E6%94%BF%E7%AD%96&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — 跨境物流 俄罗斯
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%89%A9%E6%B5%81+%E4%BF%84%E7%BD%97%E6%96%AF+Ozon+FBO&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — Yandex Market 电商
        "https://news.google.com/rss/search?q=Yandex+Market+%E4%BF%84%E7%BD%97%E6%96%AF+%E7%94%B5%E5%95%86+%E5%8D%96%E5%AE%B6&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ],
    "ai-news": [
        # Google News — AI人工智能 最新
        "https://news.google.com/rss/search?q=AI+%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD+%E6%9C%80%E6%96%B0&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — AI工具 应用
        "https://news.google.com/rss/search?q=AI%E5%B7%A5%E5%85%B7+%E5%BA%94%E7%94%A8+%E6%95%99%E7%A8%8B&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — AI电商 跨境
        "https://news.google.com/rss/search?q=AI+%E7%94%B5%E5%95%86+%E8%B7%A8%E5%A2%83+%E5%BA%94%E7%94%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — artificial intelligence news
        "https://news.google.com/rss/search?q=artificial+intelligence+AI+tools+news&hl=en&gl=US&ceid=US:en",
    ],
    "fitness": [
        # Google News — 徒手健身 自重训练 教程
        "https://news.google.com/rss/search?q=%E5%BE%92%E6%89%8B%E5%81%A5%E8%BA%AB+%E8%87%AA%E9%87%8D%E8%AE%AD%E7%BB%83+%E6%95%99%E7%A8%8B+%E4%BF%AF%E5%8D%A7%E6%92%91+%E6%B7%B1%E8%B9%B2&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — 核心训练 瑜伽 腹部
        "https://news.google.com/rss/search?q=%E6%A0%B8%E5%BF%83%E8%AE%AD%E7%BB%83+%E7%91%9C%E4%BC%BD%E5%9E%AB+%E8%85%B9%E8%82%8C+%E5%81%A5%E8%BA%AB&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Google News — bodyweight workout plan home
        "https://news.google.com/rss/search?q=bodyweight+workout+home+routine+beginner+no+equipment&hl=en&gl=US&ceid=US:en",
        # Google News — calisthenics tutorial exercises
        "https://news.google.com/rss/search?q=calisthenics+bodyweight+exercise+tutorial+plan&hl=en&gl=US&ceid=US:en",
    ],
}

# 健身 YouTube 频道（用于嵌入视频）
FITNESS_YOUTUBE = [
    "Chris Heria", "FitnessFAQs", "Calisthenicmovement",
    "Thenx", "Tom Merrick", "Sid Paulson",
    "SaturnoMovement", "Minus The Gym",
]

# ============================================================
# 工具函数
# ============================================================

def clean_html(text):
    return re.sub(r'<[^>]+>', '', unescape(text or '')).strip()


def slugify(title):
    s = re.sub(r'[^\w\s-]', '', title.lower())
    s = re.sub(r'[-\s]+', '-', s)
    return s[:80]


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def str_hash(s):
    return hashlib.md5(s.encode()).hexdigest()[:8]


def source_domain(href):
    """从 URL 提取域名"""
    m = re.search(r'https?://(?:www\.)?([^/]+)', href)
    return m.group(1) if m else ""


def build_search_link(title, domain):
    """构建在源站搜索文章的直连"""
    q = urllib.parse.quote(title[:60])
    domain_clean = domain.replace("www.", "")
    # 针对常见来源使用站内搜索
    search_templates = {
        "ebrun.com": f"https://www.ebrun.com/search?keyword={q}",
        "cifnews.com": f"https://www.cifnews.com/search?keyword={q}",
        "jiemian.com": f"https://www.jiemian.com/search/?keyword={q}",
        "sina.com.cn": f"https://search.sina.com.cn/?q={q}",
        "sohu.com": f"https://search.sohu.com/?keyword={q}",
        "163.com": f"https://search.163.com/search?keyword={q}",
    }
    for key, url in search_templates.items():
        if key in domain_clean:
            return url
    return f"https://www.google.com/search?q={q}+site:{domain_clean}"


# ============================================================
# RSS 抓取
# ============================================================

BLACKLIST_FITNESS = [
    "明星", "演员", "刘亦菲", "死亡", "减肥药", "保险",
    "金融", "股票", "理财", "信用卡", "贷款", "基金", "投资",
    "celeb", "hollywood", "surgery", "weight loss drug",
    "insurance", "stock", "finance", "bankrupt",
]


def fetch_all_feeds(section, limit_per_feed=8):
    """抓取 RSS 源，返回去重文章列表"""
    entries = []
    seen_links = set()

    for url in RSS_SOURCES.get(section, []):
        try:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=15)
            if resp.status_code != 200:
                continue

            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                link = entry.get("link", "")
                if not link or link in seen_links:
                    continue
                seen_links.add(link)

                title = clean_html(entry.get("title", ""))
                if not title or len(title) < 10:
                    continue

                # 过滤无关内容
                title_lower = title.lower()
                if section == "fitness":
                    if any(w in title_lower for w in BLACKLIST_FITNESS):
                        continue
                if any(w in title_lower for w in ["广告", "sponsored", "advertisement"]):
                    continue

                source = entry.get("source", {})
                source_href = source.get("href", "") if isinstance(source, dict) else ""
                source_name = source.get("title", "") if isinstance(source, dict) else ""
                if not source_name:
                    source_name = source_domain(link)

                # 提取摘要（Google News 摘要通常只有标题+来源，这是正常的）
                summary_html = entry.get("summary", entry.get("description", ""))
                summary_text = clean_html(summary_html)[:300]

                entries.append({
                    "title": title,
                    "link": link,
                    "source_name": source_name,
                    "source_href": source_href,
                    "domain": source_domain(source_href) or source_domain(link),
                    "summary": summary_text,
                    "published": entry.get("published", ""),
                    "section": section,
                })
        except Exception as e:
            print(f"  [WARN] {url[:60]}...: {e}")
            continue

    # 按来源去重（同一来源同一天不要太多条）
    unique = []
    domain_counts = {}
    for e in sorted(entries, key=lambda x: x.get("published", ""), reverse=True):
        domain = e["domain"]
        if domain_counts.get(domain, 0) >= 3:
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        unique.append(e)

    return unique


# ============================================================
# 内容分类
# ============================================================

def classify_cross_border(title):
    t = title.lower()
    if any(w in t for w in ["选品", "热销", "蓝海", "爆款", "品类", "趋势报告"]):
        return "selection"
    if any(w in t for w in ["yandex", "yandex market"]):
        return "yandex"
    if any(w in t for w in ["物流", "仓储", "fbo", "fbs", "发货", "头程", "海外仓"]):
        return "logistics"
    if any(w in t for w in ["收款", "回款", "卢布", "支付", "汇率", "收款"]):
        return "logistics"
    if any(w in t for w in ["政策", "法规", "关税", "认证", "合规", "eac"]):
        return "tools"
    if any(w in t for w in ["工具", "软件", "erp", "翻译", "数据"]):
        return "tools"
    if any(w in t for w in ["市场", "俄罗斯", "经济", "消费", "趋势"]):
        return "russia-market"
    if any(w in t for w in ["ozon", "ozon", "оzon"]):
        return "ozon"
    return "selection"


def classify_fitness(title):
    t = title.lower()
    if any(w in t for w in ["男性", "男人", "男生", "male", "men", "man"]):
        return "male"
    if any(w in t for w in ["女性", "女人", "女生", "female", "women", "woman"]):
        return "female"
    if any(w in t for w in ["瑜伽垫", "yoga mat", "yoga"]):
        return "yoga-mat"
    if any(w in t for w in ["饮食", "营养", "吃", "食物", "蛋白质", "减脂", "diet", "nutrition"]):
        return "diet"
    if any(w in t for w in ["计划", "安排", "每周", "每日", "routine", "plan", "schedule", "program"]):
        return "plan"
    return "yoga-mat"


# ============================================================
def classify_ai(title):
    t = title.lower()
    if any(w in t for w in ["工具", "tool", "应用", "platform"]):
        return "ai-tools"
    if any(w in t for w in ["电商", "跨境", "ecommerce", "零售", "卖家"]):
        return "ai-ecommerce"
    if any(w in t for w in ["教程", "指南", "tutorial", "guide", "how"]):
        return "ai-tutorial"
    return "ai-industry"


# Markdown 构建
# ============================================================

CAT_NAMES_CB = {
    "selection": "选品技巧", "ozon": "Ozon运营", "yandex": "Yandex运营",
    "russia-market": "俄罗斯市场", "logistics": "物流收款", "tools": "工具教程",
}
CAT_NAMES_FIT = {
    "male": "男性训练", "female": "女性训练", "yoga-mat": "瑜伽垫动作",
    "plan": "每日计划", "diet": "饮食建议",
}


def build_cross_border_post(entry):
    title = entry["title"]
    source_name = entry["source_name"]
    source_href = entry["source_href"]
    domain = entry["domain"]
    link = entry["link"]
    cat = classify_cross_border(title)
    cat_name = CAT_NAMES_CB.get(cat, "跨境电商")
    search_url = build_search_link(title, domain)

    return f"""# {title}

> 📂 分类：{cat_name}
> 📅 采集日期：{datetime.now().strftime('%Y-%m-%d')}
> 📰 来源：**{source_name}**（{domain}）

---

## 来源信息

本文信息来自 **{source_name}** 的真实报道。

{source_href if source_href else domain}

---

## 对跨境卖家的启示

基于这则行业动态，建议关注以下方向：

1. **市场趋势：** 密切跟踪俄罗斯电商市场变化，及时调整选品策略
2. **平台政策：** Ozon/Yandex 的政策调整直接影响运营成本和利润
3. **竞争格局：** 关注行业头部动态和竞争变化，找到差异化空间

---

## 查看原文

📎 **Google News 入口：** [点击查看原文]({link})
🔍 **站内搜索：** [在 {source_name} 站内搜索本文]({search_url})

> ⚠️ 本文为行业新闻采集，内容版权归原来源所有。点击上方链接跳转原文阅读完整内容。
""", cat


def build_fitness_post(entry):
    title = entry["title"]
    source_name = entry["source_name"]
    domain = entry["domain"]
    link = entry["link"]
    cat = classify_fitness(title)
    cat_name = CAT_NAMES_FIT.get(cat, "健身")
    search_url = build_search_link(title, domain)

    # 尝试构建 YouTube 搜索链接
    yt_query = urllib.parse.quote(title[:50])
    yt_link = f"https://www.youtube.com/results?search_query={yt_query}"

    return f"""# {title}

> 💪 分类：{cat_name}
> 📅 采集日期：{datetime.now().strftime('%Y-%m-%d')}
> 📰 来源：**{source_name}**

---

## 来源信息

本文信息来自 **{source_name}** 的真实健身内容。

---

## 训练建议

无论文章中提到哪种训练方法，请牢记：

- 🔹 **动作标准优先：** 宁可少做几个，也不牺牲动作质量
- 🔹 **循序渐进：** 每周比上周多做1-2个就是进步
- 🔹 **充分休息：** 肌肉在休息时生长，每周至少休息1天
- 🔹 **配合饮食：** 徒手训练配合合理饮食才能看到线条变化
- 🔹 **只需瑜伽垫：** 本文推荐的所有训练只需一张瑜伽垫即可

---

## 查看原文与视频教程

📎 **原文链接：** [点击查看原文]({link})
🔍 **搜索原文：** [在 {source_name} 站内搜索]({search_url})
🎬 **YouTube 视频教程：** [搜索相关训练视频]({yt_link})

> ⚠️ 本文为健身内容采集，版权归原来源所有。训练前请评估自身状况，量力而行。
""", cat


AI_CAT_NAMES = {
    "ai-tools": "AI工具", "ai-industry": "行业动态",
    "ai-ecommerce": "AI与电商", "ai-tutorial": "AI教程",
}


def build_ai_post(entry):
    title = entry["title"]
    source_name = entry["source_name"]
    domain = entry["domain"]
    link = entry["link"]
    cat = classify_ai(title)
    cat_name = AI_CAT_NAMES.get(cat, "AI新闻")
    search_url = build_search_link(title, domain)

    return f"""# {title}

> 🤖 分类：{cat_name}
> 📅 采集日期：{datetime.now().strftime('%Y-%m-%d')}
> 📰 来源：**{source_name}**

---

## 来源信息

本文信息来自 **{source_name}** 的真实 AI 行业报道。

---

## AI 与跨境电商的交汇

无论这则 AI 新闻的具体内容是什么，对跨境电商卖家来说，AI 正在改变：

- 🔹 **选品智能化：** AI 工具正在帮助卖家分析市场趋势和消费者偏好
- 🔹 **内容生成：** 产品描述、广告文案的 AI 自动化处理
- 🔹 **客服优化：** AI 翻译和智能客服降低跨境沟通成本
- 🔹 **数据驱动：** 从经验决策转向 AI 辅助的数据决策

---

## 查看原文

📎 **原文链接：** [点击查看原文]({link})
🔍 **站内搜索：** [在 {source_name} 站内搜索]({search_url})

> ⚠️ 本文为 AI 行业新闻采集，版权归原来源所有。完整内容请点击原文链接阅读。
""", cat


# ============================================================
# 主逻辑
# ============================================================

def generate_posts(limit_cb=8, limit_fit=5, limit_ai=7):
    tracker = load_json(TRACKER_PATH)
    all_posts = load_json(JSON_PATH)
    existing_slugs = set(p["slug"] for p in all_posts)
    posted_titles = set()
    for p in all_posts:
        if "source_name" in p:
            posted_titles.add(str_hash(p["title"]))

    new_posts = []
    date_str = datetime.now().strftime("%Y-%m-%d")

    # ---- 跨境电商 ----
    print("[INFO] 抓取跨境电商新闻...")
    cb_entries = fetch_all_feeds("cross-border", limit_per_feed=6)
    cb_fresh = [e for e in cb_entries if str_hash(e["title"]) not in posted_titles]
    print(f"  获取 {len(cb_entries)} 条，{len(cb_fresh)} 条可用")
    for entry in cb_fresh[:limit_cb]:
        new_posts.append(build_and_save(entry, "cross-border", date_str, existing_slugs))

    # ---- 健身 ----
    print("[INFO] 抓取健身内容...")
    fit_entries = fetch_all_feeds("fitness", limit_per_feed=4)
    fit_fresh = [e for e in fit_entries if str_hash(e["title"]) not in posted_titles]
    print(f"  获取 {len(fit_entries)} 条，{len(fit_fresh)} 条可用")
    for entry in fit_fresh[:limit_fit]:
        new_posts.append(build_and_save(entry, "fitness", date_str, existing_slugs))

    # ---- AI新闻 ----
    print("[INFO] 抓取 AI 新闻...")
    ai_entries = fetch_all_feeds("ai-news", limit_per_feed=5)
    ai_fresh = [e for e in ai_entries if str_hash(e["title"]) not in posted_titles]
    print(f"  获取 {len(ai_entries)} 条，{len(ai_fresh)} 条可用")
    for entry in ai_fresh[:limit_ai]:
        new_posts.append(build_and_save(entry, "ai-news", date_str, existing_slugs))

    # ---- 补充 ----
    cb_total = sum(1 for p in new_posts if p["cat"] == "cross-border")
    fit_total = sum(1 for p in new_posts if p["cat"] == "fitness")
    ai_total = sum(1 for p in new_posts if p["cat"] == "ai-news")

    if cb_total < limit_cb or fit_total < limit_fit or ai_total < limit_ai:
        print(f"[INFO] 补充搜索 (缺CB:{limit_cb-cb_total} Fit:{limit_fit-fit_total} AI:{limit_ai-ai_total})...")
        fill_all = fetch_fill(max(0,limit_cb-cb_total+limit_fit-fit_total+limit_ai-ai_total), posted_titles)
        for entry in fill_all:
            sec = entry["section"]
            if sec == "cross-border" and cb_total < limit_cb:
                new_posts.append(build_and_save(entry, "cross-border", date_str, existing_slugs))
                cb_total += 1
            elif sec == "fitness" and fit_total < limit_fit:
                new_posts.append(build_and_save(entry, "fitness", date_str, existing_slugs))
                fit_total += 1
            elif sec == "ai-news" and ai_total < limit_ai:
                new_posts.append(build_and_save(entry, "ai-news", date_str, existing_slugs))
                ai_total += 1

    save_json(TRACKER_PATH, tracker)
    current_total = len(load_json(JSON_PATH))

    cb_count = sum(1 for p in new_posts if p["cat"] == "cross-border")
    fit_count = sum(1 for p in new_posts if p["cat"] == "fitness")
    ai_count = sum(1 for p in new_posts if p["cat"] == "ai-news")
    print(f"\n[DONE] {date_str} — 跨境电商 {cb_count} + 健身 {fit_count} + AI新闻 {ai_count} = {len(new_posts)} 篇")
    print(f"  线上共 {current_total} 篇文章 → http://20020426.top")

    return new_posts


def build_and_save(entry, section, date_str, existing_slugs):
    title = entry["title"]
    if section == "cross-border":
        md_content, cat = build_cross_border_post(entry)
    elif section == "fitness":
        md_content, cat = build_fitness_post(entry)
    else:
        md_content, cat = build_ai_post(entry)

    slug_base = slugify(title) + "-" + date_str
    slug = slug_base
    i = 1
    while slug in existing_slugs:
        slug = slug_base + "-" + str(i)
        i += 1
    existing_slugs.add(slug)

    md_path = os.path.join(POSTS_DIR, slug + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    excerpt = title[:150]
    all_posts = load_json(JSON_PATH)
    all_posts.insert(0, {
        "slug": slug, "title": title, "date": date_str, "excerpt": excerpt,
        "cat": section, "sub": cat,
        "source": entry["link"],
        "source_name": f"{entry['source_name']} ({entry['domain']})",
    })
    save_json(JSON_PATH, all_posts)

    label = "CB" if section == "cross-border" else "Fit"
    print(f"  [{label}/{cat}] {title[:50]}... ← {entry['source_name']}")

    return {"title": title, "cat": section}


def fetch_fill(needed, exclude_hashes):
    """补充搜索"""
    fill_urls = [
        ("cross-border", "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86+%E4%BF%84%E7%BD%97%E6%96%AF+%E9%80%89%E5%93%81+%E8%BF%90%E8%90%A5+%E7%89%A9%E6%B5%81&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
        ("fitness", "https://news.google.com/rss/search?q=%E5%BE%92%E6%89%8B+%E8%87%AA%E9%87%8D+%E8%AE%AD%E7%BB%83+%E6%95%99%E7%A8%8B+%E4%BF%AF%E5%8D%A7%E6%92%91+%E6%B7%B1%E8%B9%B2+%E7%91%9C%E4%BC%BD+%E5%81%A5%E8%BA%AB&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
        ("ai-news", "https://news.google.com/rss/search?q=AI+%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD+%E5%B7%A5%E5%85%B7+%E6%95%99%E7%A8%8B+%E5%BA%94%E7%94%A8&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ]

    results = []
    for section, url in fill_urls:
        try:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0"
            }, timeout=15)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.content)
            for entry in feed.entries:
                link = entry.get("link", "")
                title = clean_html(entry.get("title", ""))
                if not title or len(title) < 10:
                    continue
                if str_hash(title) in exclude_hashes:
                    continue
                exclude_hashes.add(str_hash(title))
                source = entry.get("source", {})
                source_href = source.get("href", "") if isinstance(source, dict) else ""
                source_name = source.get("title", "") if isinstance(source, dict) else ""

                results.append({
                    "title": title, "link": link,
                    "source_name": source_name or source_domain(link),
                    "source_href": source_href,
                    "domain": source_domain(source_href) or source_domain(link),
                    "summary": clean_html(entry.get("summary", ""))[:300],
                    "section": section,
                })
                if len(results) >= needed:
                    break
        except Exception as e:
            print(f"  [WARN] 补充抓取失败: {e}")
    return results


def generate_sitemap():
    """从 posts.json 生成 sitemap.xml"""
    posts = load_json(JSON_PATH)
    base = "https://20020426.top"
    now = datetime.now().strftime("%Y-%m-%d")

    urls = [
        f"  <url><loc>{base}</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{base}/#section/cross-border</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{base}/#section/fitness</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{base}/#section/ai-news</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>",
    ]
    for p in posts:
        d = p.get("date", now)
        urls.append(f"  <url><loc>{base}/#post/{p['slug']}/{p['cat']}</loc><lastmod>{d}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"
    path = os.path.join(BASE_DIR, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[INFO] sitemap.xml 已更新 ({len(posts)} 篇文章)")


# ============================================================
# 入口
# ============================================================

def main():
    do_push = "--push" in sys.argv

    print("=" * 56)
    print("  每日内容生成器 v3 — 真实来源 · 有据可查")
    print("=" * 56)

    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)

    generate_posts()
    generate_sitemap()

    if do_push:
        print("\n[INFO] 推送至 GitHub...")
        import subprocess
        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", f"每日更新 {datetime.now().strftime('%Y-%m-%d')} — 来源采集"],
            ["git", "push"],
        ]:
            r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
            tag = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:60]}"
            print(f"  {' '.join(cmd)} → {tag}")
        print("  推送完成")

    total = len(load_json(JSON_PATH))
    print(f"\n当前线上 {total} 篇文章 → http://20020426.top")


if __name__ == "__main__":
    main()
