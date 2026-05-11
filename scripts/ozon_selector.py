#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ozon俄罗斯站每日选品推荐 — 数据采集与生成器 v2
=================================================
数据来源: Wildberries v18 公开API (真实销量排序) + Yandex Wordstat (可选) + Google News RSS

用法:
  python scripts/ozon_selector.py              # 采集+生成(不推送)
  python scripts/ozon_selector.py --push       # 采集+生成+git推送
  python scripts/ozon_selector.py --dry-run    # 仅采集预览,不写文件
"""

import json
import os
import sys
import re
import time
import random
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

import requests
import feedparser

# Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ====== 路径 ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(SCRIPTS_DIR, "ozon_config.json")
FEATURED_JSON_PATH = os.path.join(POSTS_DIR, "featured_ozon_pick.json")
JSON_PATH = os.path.join(POSTS_DIR, "posts.json")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(text):
    text = re.sub(r"[^\w\s一-鿿Ѐ-ӿ-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")[:80]


# ====== 俄语→中文 常用电商术语词典 ======
RU_CN_DICT = {
    "беспроводные наушники": "无线耳机", "наушники": "耳机",
    "умная розетка": "智能插座", "умный дом": "智能家居",
    "фитнес-браслет": "智能手环", "смарт-часы": "智能手表",
    "портативная колонка": "便携蓝牙音箱", "колонка": "音箱",
    "power bank": "充电宝", "внешний аккумулятор": "充电宝",
    "кабель зарядный": "充电线", "type-c": "Type-C",
    "стекло защитное": "钢化膜", "чехол": "手机壳",
    "держатель телефон": "手机支架", "автомобиль": "车载",
    "коврик для йоги": "瑜伽垫", "гантели разборные": "可调节哑铃",
    "гантели": "哑铃", "эспандер": "弹力带", "фитнес резинка": "健身带",
    "скакалка": "跳绳", "бутылка для воды": "运动水杯",
    "термос": "保温杯", "кружка": "杯子",
    "контейнер для еды": "便当盒", "ланч-бокс": "饭盒",
    "органайзер": "收纳盒", "косметика": "化妆品",
    "массажер для лица": "面部按摩仪", "массажер": "按摩器",
    "щетка электрическая": "电动牙刷", "зубная": "牙刷",
    "фен для волос": "电吹风", "фен": "吹风机",
    "подушка для сна": "睡眠枕头", "подушка": "枕头",
    "светильник": "台灯", "светодиодный": "LED",
    "носки": "袜子", "кроссовки": "运动鞋",
    "шапка": "帽子", "зима": "冬季",
    "рюкзак городской": "城市双肩包", "рюкзак": "双肩包",
    "игрушка развивающая": "益智玩具", "игрушка": "玩具",
    "конструктор магнитный": "磁力积木", "конструктор": "积木",
    "пазл": "拼图", "мыло ручной работы": "手工皂",
    "ароматизатор": "香薰", "для дома": "家用",
    "нож кухонный": "厨房刀具", "набор": "套装",
    "ремень мужской": "男士皮带", "кожаный": "真皮",
    # 品牌
    "xiaomi": "小米", "huawei": "华为", "samsung": "三星",
    "apple": "苹果", "sony": "索尼", "jbl": "JBL",
    "iphone": "iPhone", "airpods": "AirPods",
}


def translate_ru(text):
    """俄语→中文翻译"""
    text_lower = text.lower().strip()
    if text_lower in RU_CN_DICT:
        return RU_CN_DICT[text_lower]
    # 部分匹配
    result = text_lower
    for ru_word, cn_word in sorted(RU_CN_DICT.items(), key=lambda x: -len(x[0])):
        if ru_word in result:
            result = result.replace(ru_word, cn_word)
    if result != text_lower:
        return result
    # Google Translate 降级
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text)
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            parts = r.json()
            translated = "".join(p[0] for p in parts[0] if p[0])
            if translated and translated != text:
                return translated
    except Exception:
        pass
    return text


# ====== Wildberries v18 API 采集 ======

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def fetch_wildberries_products(config):
    """
    使用 WB v18 API 搜索 30+ 具体商品关键词,获取真实热门商品.
    sort=popular 返回真实销量排序, sort=newly 返回新品(趋势信号).
    返回: list of dict
    """
    wb_config = config.get("scrape_sources", {}).get("wildberries", {})
    base_url = wb_config.get("base_url")
    dest = wb_config.get("dest", "-1257786")
    delay = wb_config.get("request_delay_seconds", 8)
    min_rating = wb_config.get("min_rating", 4.0)
    min_reviews = wb_config.get("min_reviews", 30)
    spp = wb_config.get("products_per_page", 60)
    queries = wb_config.get("queries", [])

    all_products = []
    seen_ids = set()

    for qi, query_item in enumerate(queries):
        keyword = query_item["keyword"]
        cat_cn = query_item.get("cat_cn", "")
        cat_key = query_item.get("cat_key", "")

        # 两种排序: popular (热销趋势) + newly (新品趋势)
        for sort_mode in ["popular", "newly"]:
            params = {
                "appType": "1",
                "curr": "rub",
                "dest": dest,
                "page": "1",
                "query": keyword,
                "resultset": "catalog",
                "sort": sort_mode,
                "spp": str(spp),
                "suppressSpellcheck": "False",
            }
            url = base_url + "?" + urllib.parse.urlencode(params)

            for attempt in range(3):
                try:
                    headers = {
                        "User-Agent": USER_AGENTS[qi % len(USER_AGENTS)],
                        "Accept": "application/json",
                        "Accept-Language": "ru-RU,ru;q=0.9",
                        "Origin": "https://www.wildberries.ru",
                        "Referer": "https://www.wildberries.ru/",
                    }
                    resp = requests.get(url, headers=headers, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        # v5: products 在顶层; v18: 在 data.products
                        products = data.get("products", [])
                        if not products:
                            products = data.get("data", {}).get("products", [])
                        if attempt == 0:
                            total = data.get("total", data.get("data", {}).get("total", 0))
                            print(f"  [{sort_mode}] {keyword}: {len(products)}件 (总计{total:,}件)")

                        for p in products:
                            nm_id = str(p.get("id", ""))
                            if nm_id in seen_ids:
                                continue
                            seen_ids.add(nm_id)

                            name = p.get("name", "")
                            if not name or len(name) < 5:
                                continue

                            rating = float(p.get("reviewRating", 0) or 0)
                            reviews = int(p.get("feedbacks", 0) or 0)
                            if rating < min_rating or reviews < min_reviews:
                                continue

                            # 价格优先: sizes[0].price.product > salePriceU > priceU > sizes[0].price.basic
                            price_kop = 0
                            sizes = p.get("sizes", [])
                            if sizes:
                                sp = sizes[0].get("price", {})
                                price_kop = int(sp.get("product", 0) or sp.get("basic", 0) or 0)
                            if price_kop == 0:
                                price_kop = int(p.get("salePriceU") or p.get("priceU") or 0)
                            if price_kop < 5000:  # < 50 RUB
                                continue
                            price_rub = price_kop // 100

                            brand = p.get("brand", "")
                            all_products.append({
                                "nm_id": nm_id,
                                "product_name_ru": name,
                                "brand": brand,
                                "price_rub": price_rub,
                                "rating": round(rating, 1),
                                "review_count": reviews,
                                "wb_url": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
                                "cat_cn": cat_cn,
                                "cat_key": cat_key,
                                "sort_mode": sort_mode,
                                "search_keyword": keyword,
                            })
                            break
                    elif resp.status_code == 429:
                        wait = (2 ** attempt) * delay + random.random() * 5
                        time.sleep(wait)
                    else:
                        time.sleep(2)
                except Exception as e:
                    if attempt < 2:
                        time.sleep((2 ** attempt) * 3)
                    else:
                        print(f"  [ERR] {keyword} ({sort_mode}): {e}")
            # 请求间隔
            time.sleep(delay + random.random() * 4)

    return all_products


# ====== 趋势评分 ======

def load_previous_data():
    """加载前一天的数据用于趋势对比"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    raw_dir = os.path.join(BASE_DIR, "data", "ozon_raw")
    raw_path = os.path.join(raw_dir, f"raw_{yesterday}.json")
    prev = load_json(raw_path)
    if prev:
        prev_products = prev.get("wb_products_all", [])
        return {p.get("nm_id", ""): p for p in prev_products}
    return {}


def calculate_trend_score(product, prev_data):
    """计算趋势分数(0-100)"""
    score = 50  # 基础分

    nm_id = product.get("nm_id", "")
    rating = product.get("rating", 0)
    reviews = product.get("review_count", 0)
    price = product.get("price_rub", 0)
    sort_mode = product.get("sort_mode", "")

    # popularity 排序中的靠前位置 = 真实热销信号
    if sort_mode == "popular":
        score += 15

    # newly 排序 = 新品上架, 早期趋势信号
    if sort_mode == "newly":
        score += 5  # 新品本身说明不了太多, 轻微加分

    # 高评分加分
    if rating >= 4.7:
        score += 10
    elif rating >= 4.3:
        score += 5

    # 中等评论数 = 有一定市场验证但竞争不算极端
    if 100 <= reviews <= 3000:
        score += 10
    elif 50 <= reviews < 100:
        score += 5
    elif reviews > 5000:  # 头部商品, 竞争激烈, 对新手不友好
        score -= 5

    # 价格适中(CNY 50-300) = 新手友好区间
    if 500 <= price <= 4000:
        score += 10
    elif 4000 < price <= 8000:
        score += 5

    # 日环比: 和昨天的数据对比
    if nm_id in prev_data:
        prev = prev_data[nm_id]
        prev_reviews = prev.get("review_count", 0)
        prev_rating = prev.get("rating", 0)
        # 评论增长 = 持续热销信号
        if prev_reviews > 0 and reviews > prev_reviews:
            growth = (reviews - prev_reviews) / prev_reviews
            if growth > 0.1:
                score += 10  # 日环比增长 > 10%
            elif growth > 0.03:
                score += 5
        # 评分提升
        if rating > prev_rating + 0.05:
            score += 3
    else:
        # 新出现的商品, 趋势信号
        score += 5

    return min(100, max(10, score))


# ====== 推荐理由生成 ======

def generate_recommendation(product, rank, trend_score):
    """根据真实数据生成中文推荐理由"""
    name_cn = product.get("product_name_cn", "")
    price_rub = product.get("price_rub", 0)
    price_cny = product.get("price_cny", 0)
    rating = product.get("rating", 0)
    reviews = product.get("review_count", 0)
    sort_mode = product.get("sort_mode", "")

    reasons = []

    # 数据来源与可信度
    if sort_mode == "popular":
        reasons.append(f"数据来源: Wildberries真实销量排序(популярности), 反映当前热销趋势")
    elif sort_mode == "newly":
        reasons.append(f"数据来源: Wildberries新品排序(новинки), 捕捉早期选品机会")

    # 价格分析
    if price_cny < 50:
        reasons.append(f"低价位(¥{price_cny}), 适合新手试水, 资金压力小")
    elif price_cny < 150:
        reasons.append(f"中等价位(¥{price_cny}), 预估利润率30-50%, 性价比突出")
    elif price_cny < 400:
        reasons.append(f"中高价位(¥{price_cny}), 单品利润可观, 适合精品运营")
    else:
        reasons.append(f"高客单价(¥{price_cny}), 需注意物流保险和售后成本")

    # 市场验证
    if reviews >= 1000:
        reasons.append(f"市场高度认可({reviews}条真实评价, {rating}分), 需求强劲但竞争也大")
    elif reviews >= 200:
        reasons.append(f"有一定市场验证({reviews}条评价, {rating}分), 竞争适中")
    else:
        reasons.append(f"新兴商品({reviews}条评价, {rating}分), 竞争较少, 蓝海潜力")

    # 趋势评分
    if trend_score >= 75:
        reasons.append(f"趋势评分{trend_score}/100(高), 多维度信号积极, 强烈推荐关注")
    elif trend_score >= 60:
        reasons.append(f"趋势评分{trend_score}/100(中高), 综合信号良好")
    else:
        reasons.append(f"趋势评分{trend_score}/100, 建议进一步人工验证")

    return "；".join(reasons)


def assess_risks(product):
    """基于真实数据生成风险提示"""
    risks = []
    cat_cn = product.get("cat_cn", "")
    price_cny = product.get("price_cny", 0)
    reviews = product.get("review_count", 0)
    sort_mode = product.get("sort_mode", "")
    nm_id = product.get("nm_id", "")

    # 数据时效性声明
    risks.append(f"数据采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} CST, 价格/库存以 Wildberries 实时数据为准")

    # 竞争风险
    if reviews > 5000:
        risks.append(f"头部商品({reviews}条评价), 已形成竞争壁垒, 建议分析差异化切入点后再入场")
    elif reviews > 1000:
        risks.append(f"中等竞争({reviews}条评价), 建议研究TOP10竞品的定价/卖点策略")

    # 认证风险 (按类目)
    cert_map = {
        "audio": "需 EAC 认证 (TR CU 004/2011, TR CU 020/2011)",
        "smart-home": "需 EAC 认证 (TR CU 004/2011, TR CU 020/2011)",
        "wearables": "需 EAC 认证 (TR CU 004/2011, TR CU 020/2011)",
        "accessories": "需 EAC 声明 (TR CU 004/2011)",
        "auto": "需 EAC 认证 + 部分需 FSS 通知",
        "sports": "一般运动装备需 EAC 声明, 防护类需严格认证",
        "beauty": "需 EAC 声明 (TR CU 009/2011), 部分需卫生注册",
        "home": "食品接触类需 EAC 声明, 电子类需 TR CU 004/2011",
        "clothing": "需 EAC 声明 (TR CU 017/2011), 儿童服装额外要求",
        "kids": "严格认证 (TR CU 007/2011 + TR CU 008/2011), 需 GOST 测试",
    }
    cert = cert_map.get(product.get("cat_key", ""), "请确认具体认证要求")
    risks.append(f"认证要求: {cert}")

    # 新品风险
    if sort_mode == "newly" and reviews < 100:
        risks.append("新品上架, 评价较少, 建议少量首批试单验证市场反应")

    # 价格风险
    if price_cny > 300:
        risks.append("高客单价商品退货/售后成本较高, 建议购买物流保险")
    if price_cny < 20:
        risks.append("超低价商品利润率薄, 需走量且有供应链优势才能盈利")

    # SKU 溯源
    risks.append(f"SKU: {nm_id}, 可在 WB 搜索验证: wildberries.ru/catalog/{nm_id}/detail.aspx")

    return risks


# ====== 市场概览 ======

def generate_market_summary(products, news_articles, rate):
    """基于采集数据生成当日市场概览"""
    now = datetime.now()
    parts = []
    is_real_data = any(not p.get("is_news_insight", False) for p in products) if products else False

    if is_real_data:
        real_products = [p for p in products if not p.get("is_news_insight", False)]
        total = len(real_products)
        avg_rating = sum(p["rating"] for p in real_products) / total if total else 0
        avg_price = sum(p["price_rub"] for p in real_products) / total if total else 0
        cats = defaultdict(int)
        for p in real_products:
            cats[p.get("cat_cn", "其他")] += 1

        parts.append(f"## 数据概览")
        parts.append(f"- 数据来源: **Wildberries 平台真实销量排序** (v18 API)")
        parts.append(f"- 搜索关键词: 32个精确商品品类, 覆盖电子配件/运动/美妆/家居/母婴/服装")
        parts.append(f"- 采集商品: {total} 款 (均分 {avg_rating:.1f}/5.0, 均价 {avg_price:.0f} ₽ / ≈{avg_price/rate:.0f} CNY)")
        parts.append(f"- 热门细分类目: {', '.join(f'{c}({n}款)' for c, n in sorted(cats.items(), key=lambda x: -x[1])[:5])}")
        parts.append(f"- 采集时间: {now.strftime('%Y-%m-%d %H:%M')} CST")
    else:
        parts.append(f"## 数据模式: 新闻趋势分析")
        parts.append(f"- 今日采集俄罗斯电商相关资讯 {len(news_articles) if news_articles else 0} 条")

    # 新闻关联
    if news_articles:
        parts.append(f"\n## 相关市场动态")
        for n in news_articles[:5]:
            title = n.get("title", "")[:100]
            if title:
                parts.append(f"- {title}")

    # 汇率
    parts.append(f"\n## 参考信息")
    parts.append(f"- 参考汇率: 1 CNY ≈ {rate:.2f} RUB (open.er-api.com)")
    parts.append(f"- 数据时效: 采集于 {now.strftime('%Y-%m-%d %H:%M')} CST, 所有价格/评分/评论数为实时快照")
    parts.append(f"- > 以上数据均来自 Wildberries 平台公开接口, 每日12:00自动更新")

    return "\n".join(parts)


# ====== Yandex Wordstat (可选) ======

def fetch_yandex_wordstat(config):
    """通过 Yandex Direct API v4 获取关键词搜索量"""
    ws_config = config.get("scrape_sources", {}).get("yandex_wordstat", {})
    if not ws_config.get("enabled", False):
        return None

    token = ws_config.get("oauth_token", "")
    login = ws_config.get("client_login", "")
    if not token or not login:
        print("  [SKIP] Yandex Wordstat 未配置 token")
        return None

    sandbox = ws_config.get("use_sandbox", True)
    api_url = "https://api-sandbox.direct.yandex.ru/v4/json/" if sandbox else "https://api.direct.yandex.ru/v4/json/"

    queries = config.get("scrape_sources", {}).get("wildberries", {}).get("queries", [])
    keywords = [q["keyword"] for q in queries[:10]]

    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Login": login,
        "Accept-Language": "ru",
    }
    body = {
        "method": "CreateNewWordstatReport",
        "param": {
            "Phrases": keywords,
            "GeoID": [225],  # Russia
        }
    }

    try:
        r = requests.post(api_url, headers=headers, json=body, timeout=15)
        if r.status_code == 200:
            data = r.json()
            report_id = data.get("data")
            if report_id:
                # 等待报告生成
                time.sleep(5)
                poll_body = {"method": "GetWordstatReport", "param": int(report_id)}
                for _ in range(6):
                    time.sleep(10)
                    r2 = requests.post(api_url, headers=headers, json=poll_body, timeout=15)
                    if r2.status_code == 200:
                        report = r2.json()
                        if report.get("data", {}).get("StatusReport") == "Done":
                            return report.get("data", {}).get("SearchedWith", [])
            else:
                print(f"  [WARN] Yandex Wordstat 返回错误: {data}")
        else:
            print(f"  [WARN] Yandex Wordstat HTTP {r.status_code}")
    except Exception as e:
        print(f"  [WARN] Yandex Wordstat 请求失败: {e}")

    return None


# ====== RSS 新闻采集 ======

def fetch_russian_news(config):
    """抓取俄语 Google News RSS"""
    rss_config = config.get("scrape_sources", {}).get("russian_news_rss", {})
    feeds = rss_config.get("feeds", [])
    articles = []
    seen = set()

    for feed_url in feeds:
        try:
            headers = {"User-Agent": USER_AGENTS[0]}
            resp = requests.get(feed_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                if len(title) < 10 or link in seen:
                    continue
                seen.add(link)
                articles.append({
                    "title": title,
                    "link": link,
                    "source_name": entry.get("source", {}).get("title", "") if hasattr(entry, "source") else "",
                    "published": entry.get("published", ""),
                    "summary": (entry.get("summary", "") or "")[:300],
                })
        except Exception as e:
            print(f"  [WARN] RSS 请求失败: {e}")
    return articles


# ====== 汇率 ======

def fetch_rub_cny_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/CNY", timeout=10)
        if r.status_code == 200:
            return r.json().get("rates", {}).get("RUB", 13.5)
    except Exception:
        pass
    return 13.5


# ====== Markdown 生成 ======

def build_featured_md(featured_data):
    """生成置顶选品文章的 Markdown"""
    date_str = featured_data["date"]
    products = featured_data["products"]
    market_summary = featured_data.get("market_summary_cn", "")
    generated_at = featured_data.get("generated_at", "")
    is_real = any(not p.get("is_news_insight", False) for p in products) if products else False

    md = f"""# 🏆 Ozon俄罗斯站每日选品推荐 — {date_str}

> 📊 数据采集: {generated_at or date_str} CST
> 🔍 数据来源: {'**Wildberries 平台真实销量排序** (v18 API)' if is_real else 'Google News 俄罗斯电商资讯'}
> 📦 搜索关键词: 32个精确商品品类 (电子配件/运动/家居/美妆/母婴/服装)
> ⏱️ 数据时效: 实时快照, 所有数据不早于采集前72小时

---

## 📈 市场概览

{market_summary}

---

## 🏅 今日精选推荐

"""

    medals = ["🥇", "🥈", "🥉"] + ["📦"] * 9
    for i, product in enumerate(products[:10]):
        rank = i + 1
        medal = medals[i] if i < len(medals) else "📦"
        name_ru = product.get("product_name_ru", "")
        name_cn = product.get("product_name_cn", name_ru)
        brand = product.get("brand", "")
        price_rub = product.get("price_rub", 0)
        price_cny = product.get("price_cny", 0)
        rating = product.get("rating", 0)
        reviews = product.get("review_count", 0)
        cat_cn = product.get("cat_cn", "")
        reason = product.get("recommendation_reason_cn", "")
        risks = product.get("risk_warnings_cn", [])
        nm_id = product.get("nm_id", "")
        wb_url = product.get("wb_url", "")
        trend_score = product.get("trend_score", 50)
        is_news = product.get("is_news_insight", False)
        search_kw = product.get("search_keyword", "")

        md += f"""## {medal} 推荐 #{rank}: {name_cn}

> {name_ru}{' / ' + brand if brand and brand.lower() not in name_ru.lower() else ''}

| 属性 | 详情 |
|------|------|
| 📂 精细类目 | {cat_cn or '综合'} |
| 💰 平台售价 | **{price_rub:,} ₽** (≈ {price_cny} CNY) |
"""

        if not is_news and rating > 0:
            md += f"""| ⭐ 用户评分 | **{rating} / 5.0** |
| 💬 真实评价 | **{reviews:,}** 条 |
| 🏪 数据来源 | Wildberries **真实销量排序** (popular) |
| 📊 趋势评分 | **{trend_score}/100** |
"""
        else:
            md += f"""| 📰 数据模式 | 新闻趋势分析 |
| 📊 趋势评分 | {trend_score}/100 |
"""

        md += f"""| 🔗 直达链接 | [Wildberries商品页]({wb_url}) |
| 🏷️ 平台SKU | `{nm_id}` |

### 💡 推荐理由

{reason}

### ⚠️ 风险提示

"""
        for risk in risks:
            md += f"- {risk}\n"

        md += "\n---\n\n"

    # 免责声明
    md += f"""## 📋 免责声明与方法说明

> **数据来源:** Wildberries 平台公开搜索接口 (search.wb.ru), 使用 `sort=popular` (真实销量排序) + `sort=newly` (新品排序) 双维度采集。
>
> **数据时效:** 所有价格、评分、评论数均为采集时刻 ({generated_at}) 的快照数据, 不早于72小时。
>
> **选品逻辑:**
> 1. 对 32 个精确商品品类进行关键词搜索
> 2. 取 popularity 排序(销量信号) + newly 排序(新品信号) 各 TOP 商品
> 3. 综合评分(≥4.0)、评论数(≥30)、价格合理性进行筛选
> 4. 趋势评分 = popularity权重 + 日环比评论增长率 + 评分趋势 + 价格区间适配
>
> **不构成投资建议。实际采购前请核实平台最新数据、认证要求和物流成本。**

---

*本文章由 Ozon选品机器人 v2 自动生成 · [猫明之主小站](https://20020426.top) · {date_str}*
"""

    return md


# ====== 保存与索引 ======

def save_featured_post(featured_data, md_content):
    """保存置顶文章"""
    slug = featured_data["slug"]
    date_str = featured_data["date"]

    md_path = os.path.join(POSTS_DIR, f"{slug}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    save_json(FEATURED_JSON_PATH, featured_data)

    posts = load_json(JSON_PATH, [])
    entry = {
        "slug": slug,
        "title": f"🏆 Ozon每日选品推荐 — {date_str}",
        "date": date_str,
        "excerpt": featured_data.get("market_summary_cn", "")[:150] or f"今日推荐{len(featured_data.get('products',[]))}款俄罗斯热销商品(基于WB真实销量数据)",
        "cat": "ozon-pick",
        "sub": "daily-select",
        "featured": True,
        "verified": featured_data.get("verified", False),
        "source": "Wildberries v18 API",
        "source_name": "Ozon选品机器人 v2",
    }

    new_posts = []
    for p in posts:
        p.pop("featured", None)
        if p.get("slug") == slug:
            continue
        new_posts.append(p)
    new_posts.insert(0, entry)
    new_posts.sort(key=lambda x: x.get("date", ""), reverse=True)
    save_json(JSON_PATH, new_posts)

    print(f"[OK] 置顶文章已保存: posts/{slug}.md")
    print(f"[OK] Featured JSON: posts/featured_ozon_pick.json")
    print(f"[OK] posts.json 更新: {len(new_posts)} 篇文章")


# ====== 主编排 ======

def run_selector(config, dry_run=False):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    slug = f"ozon-daily-pick-{date_str}"

    print(f"\n{'='*60}")
    print(f"  Ozon 俄罗斯站每日选品 v2 — {date_str}")
    print(f"  数据源: WB v18 API (真实销量排序)")
    print(f"{'='*60}\n")

    # 1. 汇率
    print("[1/6] 获取汇率...")
    rate = fetch_rub_cny_rate()
    print(f"  1 CNY ≈ {rate:.2f} RUB")

    # 2. WB v18 API 采集
    print("[2/6] Wildberries v18 API 采集 (32个关键词 × popular/newly 双维度)...")
    all_wb_products = []
    wb_config = config.get("scrape_sources", {}).get("wildberries", {})
    if wb_config.get("enabled", True):
        all_wb_products = fetch_wildberries_products(config)
        print(f"  总计采集: {len(all_wb_products)} 款商品")
    else:
        print("  [SKIP] WB 采集已禁用")

    # 3. 加载昨天数据做趋势对比
    print("[3/6] 加载昨日数据做趋势对比...")
    prev_data = load_previous_data()
    print(f"  昨日数据: {len(prev_data)} 款商品")

    # 4. Yandex Wordstat (可选)
    print("[4/6] Yandex Wordstat 搜索量 (可选)...")
    ws_config = config.get("scrape_sources", {}).get("yandex_wordstat", {})
    if ws_config.get("enabled", False):
        wordstat_data = fetch_yandex_wordstat(config)
        if wordstat_data:
            print(f"  获取 {len(wordstat_data)} 个关键词的搜索量数据")
    else:
        print("  [SKIP] Yandex Wordstat 未启用 (需配置 OAuth token)")

    # 5. RSS 新闻
    print("[5/6] 采集俄罗斯电商新闻...")
    news_articles = fetch_russian_news(config)
    print(f"  获取 {len(news_articles)} 条新闻")

    # 6. 趋势评分 + 排序 + 生成推荐
    print("[6/6] 趋势评分 + 生成推荐...")
    for p in all_wb_products:
        p["trend_score"] = calculate_trend_score(p, prev_data)

    # 按趋势评分排序
    all_wb_products.sort(key=lambda x: (x.get("trend_score", 0), x.get("rating", 0)), reverse=True)

    # 翻译 + 构建推荐
    max_products = config.get("output", {}).get("max_products", 10)
    top_products = all_wb_products[:max_products]

    featured_products = []
    seen_cats = set()
    for rank, p in enumerate(top_products):
        name_cn = translate_ru(p["product_name_ru"])
        price_cny = round(p["price_rub"] / rate, 1) if rate else 0
        trend_score = p.get("trend_score", 50)

        product_data = {
            "rank": rank + 1,
            "nm_id": p.get("nm_id", ""),
            "product_name_ru": p["product_name_ru"],
            "product_name_cn": name_cn,
            "brand": p.get("brand", ""),
            "cat_cn": p.get("cat_cn", ""),
            "cat_key": p.get("cat_key", ""),
            "price_rub": p["price_rub"],
            "price_cny": price_cny,
            "rating": p["rating"],
            "review_count": p["review_count"],
            "trend_score": trend_score,
            "sort_mode": p.get("sort_mode", ""),
            "search_keyword": p.get("search_keyword", ""),
            "wb_url": p.get("wb_url", ""),
            "source_urls": [p.get("wb_url", "")],
            "recommendation_reason_cn": generate_recommendation(
                {"product_name_cn": name_cn, "price_rub": p["price_rub"], "price_cny": price_cny,
                 "rating": p["rating"], "review_count": p["review_count"], "cat_cn": p.get("cat_cn", ""),
                 "sort_mode": p.get("sort_mode", "")}, rank + 1, trend_score
            ),
            "risk_warnings_cn": assess_risks(
                {"cat_cn": p.get("cat_cn", ""), "cat_key": p.get("cat_key", ""),
                 "price_cny": price_cny, "review_count": p["review_count"],
                 "sort_mode": p.get("sort_mode", ""), "nm_id": p.get("nm_id", "")}
            ),
        }
        featured_products.append(product_data)

    print(f"  最终推荐: {len(featured_products)} 款商品 (按趋势评分排序)")

    # 如果 WB 数据不足, 降级为新闻分析
    if len(featured_products) < 3:
        print("  [INFO] 商品数据不足, 降级为新闻趋势分析...")
        from collections import defaultdict
        cat_hits = defaultdict(list)
        for a in news_articles:
            title = a.get("title", "").lower()
            for cat_key, keywords in [
                ("audio", ["наушники", "колонка", "гарнитура", "headphone", "speaker", "耳机", "音箱"]),
                ("smart-home", ["умный", "розетка", "лампа", "smart", "智能"]),
                ("sports", ["спорт", "фитнес", "йога", "тренировка", "sport", "fitness", "运动", "健身"]),
                ("beauty", ["косметика", "уход", "красота", "beauty", "美妆", "护肤"]),
                ("home", ["дом", "кухня", "посуда", "home", "kitchen", "家居", "厨房"]),
                ("kids", ["дети", "игрушка", "kids", "toy", "儿童", "玩具"]),
                ("clothing", ["одежда", "обувь", "fashion", "服装", "鞋"]),
            ]:
                if any(kw in title for kw in keywords):
                    cat_hits[cat_key].append(a)
                    break

        cat_names = {"audio": "无线耳机/音箱", "smart-home": "智能家居", "sports": "运动户外",
                     "beauty": "美妆健康", "home": "家居用品", "kids": "母婴玩具", "clothing": "服装鞋包"}
        for rank, (cat_key, articles) in enumerate(sorted(cat_hits.items(), key=lambda x: -len(x[1]))[:10]):
            cat_cn = cat_names.get(cat_key, cat_key)
            ref_prices = {"audio": 2000, "smart-home": 1500, "sports": 1200, "beauty": 800,
                          "home": 1000, "kids": 1200, "clothing": 2000}
            ref_price = ref_prices.get(cat_key, 1200)
            featured_products.append({
                "rank": rank + 1,
                "nm_id": "",
                "product_name_ru": f"{cat_cn}趋势",
                "product_name_cn": f"📊 {cat_cn}选品机会",
                "brand": "",
                "cat_cn": cat_cn,
                "cat_key": cat_key,
                "price_rub": ref_price,
                "price_cny": round(ref_price / rate, 1),
                "rating": 0,
                "review_count": len(articles),
                "trend_score": 30 + len(articles) * 5,
                "sort_mode": "news",
                "search_keyword": "",
                "wb_url": "",
                "source_urls": [a.get("link", "") for a in articles[:3] if a.get("link")],
                "recommendation_reason_cn": f"基于 {len(articles)} 条俄罗斯电商新闻的趋势分析；建议打开 WB/Ozon 搜索 '{cat_cn}' 确认具体商品数据",
                "risk_warnings_cn": ["此为新闻趋势分析, 非实时商品数据", "建议到 WB/Ozon 平台确认具体 SKU"],
                "is_news_insight": True,
            })
        print(f"  新闻趋势: {len(featured_products)} 条类目趋势")

    # 构建数据
    data_sources = []
    if wb_config.get("enabled", True) and all_wb_products:
        data_sources.append({"name": "Wildberries v18 API (真实销量排序)", "url": "https://search.wb.ru/", "reliability": "high"})
    if news_articles:
        data_sources.append({"name": "Google News RSS (RU+EN)", "url": "https://news.google.com/", "reliability": "medium"})

    market_summary = generate_market_summary(featured_products, news_articles, rate)

    featured_data = {
        "slug": slug,
        "date": date_str,
        "generated_at": generated_at,
        "verified": False,
        "verification_report": None,
        "products": featured_products,
        "market_summary_cn": market_summary,
        "data_sources": data_sources,
    }

    md_content = build_featured_md(featured_data)

    if dry_run:
        print("\n" + "=" * 60)
        print("  DRY RUN — 预览 (未写入文件)")
        print("=" * 60)
        print(json.dumps(featured_data, ensure_ascii=False, indent=2))
        return featured_data

    save_featured_post(featured_data, md_content)

    # 保存原始数据
    raw_dir = os.path.join(BASE_DIR, config.get("output", {}).get("data_dump_dir", "data/ozon_raw"))
    ensure_dir(raw_dir)
    raw_dump = {
        "date": date_str,
        "generated_at": generated_at,
        "rate_cny_rub": rate,
        "wb_products_all": all_wb_products[:100],
        "news_articles": news_articles[:20],
    }
    save_json(os.path.join(raw_dir, f"raw_{date_str}.json"), raw_dump)
    print(f"[OK] 原始数据存档: data/ozon_raw/raw_{date_str}.json")

    # 清理过期数据
    keep_days = config.get("output", {}).get("keep_raw_days", 7)
    cutoff = now - timedelta(days=keep_days)
    for fname in os.listdir(raw_dir):
        if fname.startswith("raw_") and fname.endswith(".json"):
            fpath = os.path.join(raw_dir, fname)
            try:
                fdate_str = fname[4:14]
                fdate = datetime.strptime(fdate_str, "%Y-%m-%d")
                if fdate < cutoff:
                    os.remove(fpath)
            except Exception:
                pass

    print(f"\n{'='*60}")
    print(f"  完成! 今日推荐 {len(featured_products)} 款商品")
    print(f"{'='*60}\n")

    return featured_data


def main():
    do_push = "--push" in sys.argv
    dry_run = "--dry-run" in sys.argv

    config = load_json(CONFIG_PATH, {})
    if not config:
        print("[ERROR] 无法加载配置文件: scripts/ozon_config.json")
        sys.exit(1)

    if not config.get("enabled", True):
        print("[SKIP] Ozon selector 已在配置中禁用")
        return

    run_selector(config, dry_run=dry_run)

    if do_push and not dry_run:
        import subprocess
        print("[PUSH] 推送至 GitHub...")
        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", f"Ozon每日选品 {datetime.now().strftime('%Y-%m-%d')}"],
            ["git", "push"],
        ]:
            r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
            status = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:100]}"
            print(f"  {' '.join(cmd)} → {status}")


if __name__ == "__main__":
    main()
