#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日内容生成器 v4 - Firecrawl抓取 + AI总结
Google News RSS -> Firecrawl 抓取原文 -> 千问/DeepSeek 总结
用法: python daily_generator.py [--push]
"""

import json, os, sys, re, hashlib, urllib.parse, time
from datetime import datetime, timedelta
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
import requests
from firecrawl import V1FirecrawlApp
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
JSON_PATH = os.path.join(POSTS_DIR, "posts.json")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(SCRIPTS_DIR, "config.json")

def load_config():
    config = {
        "firecrawl_api_key": "", "primary_api_key": "", "primary_api_base": "",
        "primary_model": "qwen-plus", "backup_api_key": "", "backup_api_base": "",
        "backup_model": "deepseek-chat", "enrich_enabled": False,
        "target_words": 700, "scrape_timeout": 30,
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    for key in config:
        env_val = os.environ.get(f"BLOG_{key.upper()}")
        if env_val is not None:
            if key in ("target_words", "scrape_timeout"):
                config[key] = int(env_val)
            elif key == "enrich_enabled":
                config[key] = env_val.lower() in ("1", "true", "yes")
            else:
                config[key] = env_val
    return config

CONFIG = load_config()
FC_KEY = CONFIG["firecrawl_api_key"]
ENRICH = bool(CONFIG["enrich_enabled"] and FC_KEY and CONFIG["primary_api_key"])

# ============================================================
# 信息源配置
# ============================================================

RSS_SOURCES = {
    "cross-border": [
        # 跨境电商 Ozon 教程 入门 实操
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86+Ozon+%E6%95%99%E7%A8%8B+%E5%85%A5%E9%97%A8+%E5%AE%9E%E6%93%8D&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # Ozon 运营技巧 指南
        "https://news.google.com/rss/search?q=Ozon+%E8%BF%90%E8%90%A5+%E6%8A%80%E5%B7%A7+%E6%8C%87%E5%8D%97+%E9%80%89%E5%93%81+%E6%95%99%E7%A8%8B&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # 跨境电商 俄罗斯 选品 教程 经验
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83%E7%94%B5%E5%95%86+%E4%BF%84%E7%BD%97%E6%96%AF+%E9%80%89%E5%93%81+%E6%95%99%E7%A8%8B+%E7%BB%8F%E9%AA%8C&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # 跨境物流 俄罗斯 实操 方法
        "https://news.google.com/rss/search?q=%E8%B7%A8%E5%A2%83+%E7%89%A9%E6%B5%81+%E4%BF%84%E7%BD%97%E6%96%AF+%E5%AE%9E%E6%93%8D+%E6%96%B9%E6%B3%95&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # 电商 铺货 教程 技巧
        "https://news.google.com/rss/search?q=%E7%94%B5%E5%95%86+%E9%93%BA%E8%B4%A7+Ozon+%E6%95%99%E7%A8%8B+%E6%8A%80%E5%B7%A7&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ],
    "ai-news": [
        # AI 教程 入门 学习
        "https://news.google.com/rss/search?q=AI+%E6%95%99%E7%A8%8B+%E5%85%A5%E9%97%A8+%E5%AD%A6%E4%B9%A0+%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # AI工具 使用教程 教学 实操
        "https://news.google.com/rss/search?q=AI%E5%B7%A5%E5%85%B7+%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B+%E6%95%99%E5%AD%A6+%E5%AE%9E%E6%93%8D&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # AI 电商 应用 教程 方法
        "https://news.google.com/rss/search?q=AI+%E7%94%B5%E5%95%86+%E5%BA%94%E7%94%A8+%E6%95%99%E7%A8%8B+%E6%96%B9%E6%B3%95&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        # AI tutorial guide how-to
        "https://news.google.com/rss/search?q=AI+tutorial+guide+how-to+artificial+intelligence+learning&hl=en&gl=US&ceid=US:en",
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


# Firecrawl 抓取 + AI 总结 模块

def scrape_article_content(url):
    """用 Firecrawl 抓取完整文章，返回 clean markdown。失败返回 None"""
    if not FC_KEY:
        return None
    try:
        app = V1FirecrawlApp(api_key=FC_KEY)
        result = app.scrape_url(url, formats=["markdown"],
                                timeout=CONFIG["scrape_timeout"] * 1000)
        md = getattr(result, "markdown", "") or ""
        if not md or len(md) < 100:
            return None
        max_chars = CONFIG["target_words"] * 8
        if len(md) > max_chars:
            md = md[:max_chars] + "\n\n...(内容已截断)"
        return md
    except Exception as e:
        print(f"  [SCRAPE FAIL] {url[:60]}: {e}")
        return None


def _get_ai_client(use_backup=False):
    """获取 AI 客户端（主: 千问, 备: DeepSeek）"""
    if use_backup:
        return OpenAI(
            api_key=CONFIG["backup_api_key"],
            base_url=CONFIG["backup_api_base"],
        ), CONFIG["backup_model"]
    return OpenAI(
        api_key=CONFIG["primary_api_key"],
        base_url=CONFIG["primary_api_base"],
    ), CONFIG["primary_model"]


def summarize_article(title, source_name, content_md, section):
    """用 AI 总结文章为高质量学习内容"""
    if not content_md or len(content_md) < 100:
        return None

    prompts = {
        "cross-border": (
            "你是一位跨境电商实战教练，帮助中国卖家在Ozon/Yandex平台卖货到俄罗斯。"
            "把下面的文章总结为一篇600-900字的纯中文教程。要求：\n"
            "1. 用 ## 分节，每节有实质性内容\n"
            "2. 包含具体操作步骤、工具名称、数据指标\n"
            "3. 指出新手常见的3个错误及如何避免\n"
            "4. 结尾给一个「今日行动建议」\n"
            "只输出教程正文，不要写「根据原文」之类的元描述。"
        ),
        "fitness": (
            "你是一位徒手健身教练，帮助读者在家用瑜伽垫训练。"
            "把下面的文章总结为一篇600-900字的纯中文健身教程。要求：\n"
            "1. 用 ## 分节，每节有实质性内容\n"
            "2. 包含具体动作名称、组数次数、动作要领\n"
            "3. 指出常见的动作错误及纠正方法\n"
            "4. 结尾给一个「今日训练计划」\n"
            "只输出教程正文，不要写「根据原文」之类的元描述。"
        ),
        "ai-news": (
            "你是一位AI学习教练，帮助读者掌握AI工具和技能。"
            "把下面的文章总结为一篇600-900字的纯中文学习教程。要求：\n"
            "1. 用 ## 分节，每节有实质性内容\n"
            "2. 包含具体工具名称、使用步骤、参数设置\n"
            "3. 指出实际应用场景和效率提升点\n"
            "4. 结尾给一个「今日动手实践」任务\n"
            "只输出教程正文，不要写「根据原文」之类的元描述。"
        ),
    }

    system_prompt = prompts.get(section, prompts["cross-border"])
    user_msg = f"标题：{title}\n来源：{source_name}\n\n原文内容：\n{content_md[:6000]}"

    # 先试主 API，失败试备用
    for attempt, use_backup in enumerate([False, True]):
        try:
            client, model = _get_ai_client(use_backup)
            label = "DeepSeek" if use_backup else "Qianwen"
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            body = resp.choices[0].message.content.strip()
            # 提取 key points（取 ## 标题作为要点）
            key_points = re.findall(r'^##\s+(.+)', body, re.MULTILINE)[:5]
            if not key_points:
                key_points = re.findall(r'^\d+\.\s+(.+)', body, re.MULTILINE)[:5]
            return {
                "content": body,
                "key_points": key_points if key_points else ["详见正文"],
                "word_count": len(body),
                "model": label,
            }
        except Exception as e:
            print(f"  [AI FAIL {label}] {e}")
            if not use_backup and CONFIG["backup_api_key"]:
                print(f"  [AI FALLBACK] 切换到 DeepSeek...")
                time.sleep(1)
                continue
    return None


def translate_title(title):
    """如果标题主要是英文，翻译为中文"""
    import unicodedata
    en_chars = len(re.findall(r'[a-zA-Z]', title))
    cn_chars = len(re.findall(r'[一-鿿]', title))
    if en_chars <= cn_chars or en_chars < 15:
        return title  # 中文或短英文标题不用翻译
    try:
        client, model = _get_ai_client(False)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"把这句话翻译成简洁的中文标题（不要加任何前缀或编号）: {title}"}],
            max_tokens=80, temperature=0.3,
        )
        cn = resp.choices[0].message.content.strip()
        if cn and len(cn) >= 3 and not cn.startswith("1."):
            return cn
    except Exception:
        pass
    return title


def enrich_batch(entries):
    """批量抓取+总结。3 线程并行抓取，串行总结"""
    if not ENRICH:
        return entries

    total = len(entries)
    print(f"[INFO] 内容富化: {total} 篇（Firecrawl + 千问）...")

    # Phase 1: 并发抓取
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        for i, entry in enumerate(entries):
            f = pool.submit(scrape_article_content, entry["link"])
            futures[f] = i
            time.sleep(0.5)

        for f in as_completed(futures):
            i = futures[f]
            try:
                md = f.result()
            except Exception:
                md = None
            results[i] = md
            status = "OK" if md else "FAIL"
            try: print(f"  [SCRAPE {status}] ({i+1}/{total}) {entries[i]['title'][:40]}...")
            except UnicodeEncodeError: print(f"  [SCRAPE {status}] ({i+1}/{total})")

    # Phase 2: 串行总结 + 附加到 entry
    for i, entry in enumerate(entries):
        content_md = results.get(i)
        if content_md:
            enriched = summarize_article(
                entry["title"], entry["source_name"], content_md, entry["section"]
            )
            entry["enriched"] = enriched
            if enriched:
                try:
                    print(f"  [SUMMARIZE OK] ({i+1}/{total}) {enriched.get('word_count',0)}字 via {enriched.get('model','?')}")
                except UnicodeEncodeError:
                    print(f"  [SUMMARIZE OK] ({i+1}/{total})")
            else:
                print(f"  [SUMMARIZE FAIL] ({i+1}/{total})")
            time.sleep(1)
        else:
            entry["enriched"] = None

    ok = sum(1 for e in entries if e.get("enriched"))
    print(f"[INFO] 富化完成: {ok}/{total} 篇成功")
    return entries


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
AI_CAT_NAMES = {
    "ai-tools": "AI工具", "ai-industry": "行业动态",
    "ai-ecommerce": "AI与电商", "ai-tutorial": "AI教程",
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
    enriched = entry.get("enriched")

    body = ""
    if enriched and enriched.get("content"):
        body = enriched["content"]
        kp = enriched.get("key_points", [])
        if kp:
            body += "\n\n## 核心要点\n\n" + "\n".join(f"- {p}" for p in kp)
    else:
        body = """## 学习要点

阅读这篇教程后，你将会学到：

1. **实操方法:** 具体的操作步骤和落地技巧
2. **避坑指南:** 新手常见错误及如何避免
3. **进阶思路:** 从入门到精通的学习路径
"""

    return f"""# {title}

> 📂 分类: {cat_name}
> 📅 采集日期: {datetime.now().strftime('%Y-%m-%d')}
> 📰 来源: **{source_name}**（{domain}）

---

{body}

---

## 查看原文

📎 **原文链接:** [点击查看原文]({link})
🔍 **站内搜索:** [在 {source_name} 站内搜索本文]({search_url})

> 📚 本文内容来自 **{source_name}**，版权归原来源所有。
""", cat
def build_fitness_post(entry):
    title = entry["title"]
    source_name = entry["source_name"]
    domain = entry["domain"]
    link = entry["link"]
    cat = classify_fitness(title)
    cat_name = CAT_NAMES_FIT.get(cat, "健身")
    search_url = build_search_link(title, domain)
    enriched = entry.get("enriched")
    yt_query = urllib.parse.quote(title[:50])
    yt_link = f"https://www.youtube.com/results?search_query={yt_query}"

    body = ""
    if enriched and enriched.get("content"):
        body = enriched["content"]
    else:
        body = """## 训练建议

无论文章中提到哪种训练方法，请牢记:

- 🔹 **动作标准优先:** 宁可少做几个，也不牺牲动作质量
- 🔹 **循序渐进:** 每周比上周多做1-2个就是进步
- 🔹 **充分休息:** 肌肉在休息时生长，每周至少休息1天
- 🔹 **配合饮食:** 徒手训练配合合理饮食才能看到线条变化
- 🔹 **只需瑜伽垫:** 本文推荐的所有训练只需一张瑜伽垫即可
"""

    return f"""# {title}

> 💪 分类: {cat_name}
> 📅 采集日期: {datetime.now().strftime('%Y-%m-%d')}
> 📰 来源: **{source_name}**

---

{body}

---

## 查看原文与视频教程

📎 **原文链接:** [点击查看原文]({link})
🔍 **搜索原文:** [在 {source_name} 站内搜索]({search_url})
🎬 **YouTube 视频教程:** [搜索相关训练视频]({yt_link})

> ⚠️ 训练前请评估自身状况，量力而行。
""", cat
def build_ai_post(entry):
    title = entry["title"]
    source_name = entry["source_name"]
    domain = entry["domain"]
    link = entry["link"]
    cat = classify_ai(title)
    cat_name = AI_CAT_NAMES.get(cat, "AI新闻")
    search_url = build_search_link(title, domain)
    enriched = entry.get("enriched")

    body = ""
    if enriched and enriched.get("content"):
        body = enriched["content"]
    else:
        body = """## AI 与跨境电商的交汇

无论这则 AI 新闻的具体内容是什么，对跨境电商卖家来说，AI 正在改变:

- 🔹 **选品智能化:** AI 工具正在帮助卖家分析市场趋势和消费者偏好
- 🔹 **内容生成:** 产品描述、广告文案的 AI 自动化处理
- 🔹 **客服优化:** AI 翻译和智能客服降低跨境沟通成本
- 🔹 **数据驱动:** 从经验决策转向 AI 辅助的数据决策
"""

    return f"""# {title}

> 🤖 分类: {cat_name}
> 📅 采集日期: {datetime.now().strftime('%Y-%m-%d')}
> 📰 来源: **{source_name}**

---

{body}

---

## 查看原文

📎 **原文链接:** [点击查看原文]({link})
🔍 **站内搜索:** [在 {source_name} 站内搜索]({search_url})

> 📚 本文内容来自 **{source_name}**，版权归原来源所有。
""", cat
def generate_posts(limit_cb=8, limit_fit=5, limit_ai=7):
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
    cb_fresh = [e for e in cb_entries if str_hash(e["title"]) not in posted_titles][:limit_cb]
    print(f"  获取 {len(cb_entries)} 条，{len(cb_fresh)} 条可用")

    # ---- 健身 ----
    print("[INFO] 抓取健身内容...")
    fit_entries = fetch_all_feeds("fitness", limit_per_feed=4)
    fit_fresh = [e for e in fit_entries if str_hash(e["title"]) not in posted_titles][:limit_fit]
    print(f"  获取 {len(fit_entries)} 条，{len(fit_fresh)} 条可用")

    # ---- AI新闻 ----
    print("[INFO] 抓取 AI 新闻...")
    ai_entries = fetch_all_feeds("ai-news", limit_per_feed=5)
    ai_fresh = [e for e in ai_entries if str_hash(e["title"]) not in posted_titles][:limit_ai]
    print(f"  获取 {len(ai_entries)} 条，{len(ai_fresh)} 条可用")

    # ---- 内容富化（Firecrawl + AI总结） ----
    all_fresh = cb_fresh + fit_fresh + ai_fresh
    if all_fresh:
        enrich_batch(all_fresh)

    # ---- 生成文章 ----
    for entry in cb_fresh:
        new_posts.append(build_and_save(entry, "cross-border", date_str, existing_slugs))
    for entry in fit_fresh:
        new_posts.append(build_and_save(entry, "fitness", date_str, existing_slugs))
    for entry in ai_fresh:
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

    current_total = len(load_json(JSON_PATH))

    cb_count = sum(1 for p in new_posts if p["cat"] == "cross-border")
    fit_count = sum(1 for p in new_posts if p["cat"] == "fitness")
    ai_count = sum(1 for p in new_posts if p["cat"] == "ai-news")
    print(f"\n[DONE] {date_str} — 跨境电商 {cb_count} + 健身 {fit_count} + AI新闻 {ai_count} = {len(new_posts)} 篇")
    print(f"  线上共 {current_total} 篇文章 → http://20020426.top")

    return new_posts


def build_and_save(entry, section, date_str, existing_slugs):
    title = entry["title"]
    # 自动翻译英文标题
    title = translate_title(title)
    if title != entry["title"]:
        print(f"  [TL] {entry['title'][:30]}... -> {title[:30]}...")
        entry["title"] = title
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
    enriched = entry.get("enriched") or {}
    all_posts = load_json(JSON_PATH)
    all_posts.insert(0, {
        "slug": slug, "title": title, "date": date_str, "excerpt": excerpt,
        "cat": section, "sub": cat,
        "source": entry["link"],
        "source_name": f"{entry['source_name']} ({entry['domain']})",
        "has_content": bool(enriched and enriched.get("content")),
        "word_count": enriched.get("word_count", 0),
    })
    save_json(JSON_PATH, all_posts)

    label = "CB" if section == "cross-border" else "Fit"
    try:
        print(f"  [{label}/{cat}] {title[:50]}... <- {entry['source_name']}")
    except (UnicodeEncodeError, UnicodeDecodeError):
        print(f"  [{label}/{cat}] (article saved)")

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
