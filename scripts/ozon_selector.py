#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ozon俄罗斯站每日选品推荐 - 数据采集与生成器
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
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

import requests
import feedparser

# 修复 Windows 控制台 GBK 编码问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ====== 路径配置 ======
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
    """生成 URL 安全的 slug,保留中文字符"""
    text = re.sub(r"[^\w\s一-鿿Ѐ-ӿ-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")[:80]


# ====== 俄语→中文 常用电商术语词典 ======
RU_CN_DICT = {
    # 商品类目
    "электроника": "电子产品", "смартфон": "智能手机", "наушники": "耳机",
    "ноутбук": "笔记本电脑", "планшет": "平板电脑", "телевизор": "电视机",
    "умная розетка": "智能插座", "умная лампа": "智能灯", "умный дом": "智能家居",
    "фитнес-браслет": "智能手环", "смарт-часы": "智能手表",
    "камера": "摄像头", "видеонаблюдение": "监控摄像",
    "зарядное устройство": "充电器", "power bank": "充电宝", "аккумулятор": "移动电源",
    "кабель": "数据线", "переходник": "转接头", "адаптер": "适配器",
    "чехол": "手机壳", "стекло защитное": "钢化膜", "пленка": "保护膜",
    "клавиатура": "键盘", "мышь": "鼠标", "монитор": "显示器",
    "колонка": "音箱", "блютуз": "蓝牙", "bluetooth": "蓝牙",
    "наушники беспроводные": "无线耳机", "tws": "真无线耳机",
    # 家居厨房
    "дом": "家居", "кухня": "厨房", "посуда": "餐具",
    "сковорода": "煎锅", "кастрюля": "汤锅", "нож": "刀具",
    "термос": "保温杯", "бутылка": "水杯", "контейнер": "收纳盒",
    "органайзер": "收纳整理", "вешалка": "衣架", "корзина": "收纳篮",
    "подушка": "枕头", "одеяло": "被子", "постельное белье": "床品",
    "полотенце": "毛巾", "коврик": "地垫", "штора": "窗帘",
    "светильник": "灯具", "лампа": "台灯", "гирлянда": "灯串",
    "свеча": "蜡烛", "ароматизатор": "香薰", "диффузор": "扩香器",
    # 服装鞋包
    "одежда": "服装", "обувь": "鞋靴", "сумка": "包袋",
    "футболка": "T恤", "рубашка": "衬衫", "джинсы": "牛仔裤",
    "платье": "连衣裙", "юбка": "半身裙", "куртка": "外套",
    "пуховик": "羽绒服", "свитер": "毛衣", "толстовка": "卫衣",
    "спортивный костюм": "运动套装", "шорты": "短裤",
    "кроссовки": "运动鞋", "ботинки": "靴子", "тапочки": "拖鞋",
    "рюкзак": "双肩包", "кошелек": "钱包", "ремень": "腰带",
    "шапка": "帽子", "шарф": "围巾", "перчатки": "手套",
    "носки": "袜子", "белье": "内衣",
    # 母婴玩具
    "детский": "儿童", "игрушка": "玩具", "конструктор": "积木",
    "кукла": "娃娃", "машинка": "玩具车", "развивающая игрушка": "益智玩具",
    "пазл": "拼图", "настольная игра": "桌游",
    "подгузники": "纸尿裤", "бутылочка для кормления": "奶瓶",
    "коляска": "婴儿车", "автокресло": "安全座椅",
    # 美妆健康
    "косметика": "化妆品", "уход за кожей": "护肤品", "парфюмерия": "香水",
    "крем": "面霜", "сыворотка": "精华液", "маска для лица": "面膜",
    "тушь": "睫毛膏", "помада": "口红", "тональный крем": "粉底液",
    "масло": "精油", "шампунь": "洗发水", "бальзам": "护发素",
    "гель для душа": "沐浴露", "дезодорант": "止汗露",
    "массажер": "按摩器", "эпилятор": "脱毛器", "фен": "吹风机",
    "щетка электрическая": "电动牙刷", "ирригатор": "冲牙器",
    # 运动户外
    "спорт": "运动", "фитнес": "健身", "йога": "瑜伽",
    "гантели": "哑铃", "эспандер": "弹力带", "скакалка": "跳绳",
    "коврик для йоги": "瑜伽垫", "мяч": "球",
    "туристический": "户外", "палатка": "帐篷", "спальный мешок": "睡袋",
    "термос": "保温壶", "фонарь": "手电筒", "рюкзак туристический": "登山包",
    "велосипед": "自行车", "самокат": "滑板车",
    # 品牌/平台
    "xiaomi": "小米", "huawei": "华为", "samsung": "三星", "apple": "苹果",
    "sony": "索尼", "jbl": "JBL", "bosch": "博世", "philips": "飞利浦",
    "wildberries": "Wildberries", "ozon": "Ozon", "яндекс": "Yandex",
    # 通用
    "беспроводной": "无线", "портативный": "便携", "водонепроницаемый": "防水",
    "акция": "促销", "скидка": "折扣", "новинка": "新品",
    "хит продаж": "热销", "рейтинг": "评分", "отзыв": "评价",
    "доставка": "配送", "цена": "价格", "качество": "品质",
    "размер": "尺码", "цвет": "颜色", "черный": "黑色", "белый": "白色",
    "красный": "红色", "синий": "蓝色", "зеленый": "绿色",
}


def translate_ru(text):
    """俄语→中文翻译: 先查词典, 再尝试 Google Translate"""
    text_lower = text.lower().strip()
    # 全词匹配
    if text_lower in RU_CN_DICT:
        return RU_CN_DICT[text_lower]
    # 部分匹配(最长匹配)
    best = ""
    for ru_word, cn_word in sorted(RU_CN_DICT.items(), key=lambda x: -len(x[0])):
        if ru_word in text_lower and len(ru_word) > len(best):
            best = ru_word
            result = text_lower.replace(ru_word, cn_word)
    if best:
        # 对剩余未翻译的俄语词再尝试
        for ru_word, cn_word in sorted(RU_CN_DICT.items(), key=lambda x: -len(x[0])):
            if ru_word not in best and ru_word in result:
                result = result.replace(ru_word, cn_word)
        return result
    # 尝试 Google Translate (无需 API Key 的免费接口)
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


# ====== Wildberries 数据采集 ======

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def fetch_wildberries(category_key, keyword, config, max_pages=2):
    """
    从 Wildberries 非官方搜索 API 获取热门商品.
    返回: list of dict
    """
    wb_config = config.get("scrape_sources", {}).get("wildberries", {})
    base_url = wb_config.get("base_url")
    dest = wb_config.get("dest", "-1257786")
    delay = wb_config.get("request_delay_seconds", 3)
    min_rating = wb_config.get("min_rating", 4.0)
    min_reviews = wb_config.get("min_reviews", 50)

    all_products = []

    for page in range(1, max_pages + 1):
        params = {
            "ab_testing": "false",
            "appType": "1",
            "curr": "rub",
            "dest": dest,
            "lang": "ru",
            "page": str(page),
            "query": keyword,
            "resultset": "catalog",
            "sort": "popular",
            "spp": "30",
            "suppressSpellcheck": "false",
        }
        url = base_url + "?" + urllib.parse.urlencode(params)

        for attempt in range(3):
            try:
                headers = {
                    "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)],
                    "Accept": "application/json",
                    "Accept-Language": "ru-RU,ru;q=0.9",
                }
                resp = requests.get(url, headers=headers, timeout=20)
                if attempt == 0:
                    print(f"    [{resp.status_code}] {url[:90]}...")
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get("data", {}).get("products", [])
                    if not products:
                        break
                    for p in products:
                        name = p.get("name", "")
                        if not name or len(name) < 5:
                            continue
                        rating = float(p.get("reviewRating", 0) or 0)
                        reviews = int(p.get("feedbacks", 0) or 0)
                        if rating < min_rating or reviews < min_reviews:
                            continue
                        price_kop = int(p.get("salePriceU", 0) or 0)
                        price_rub = price_kop // 100 if price_kop else 0
                        if price_rub < 50:
                            continue
                        brand = p.get("brand", "")
                        nm_id = str(p.get("id", ""))
                        all_products.append({
                            "product_name_ru": name,
                            "brand": brand,
                            "price_rub": price_rub,
                            "rating": round(rating, 1),
                            "review_count": reviews,
                            "wb_url": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
                            "nm_id": nm_id,
                            "category_key": category_key,
                        })
                    break
                elif resp.status_code == 429:
                    wait = (2 ** attempt) * delay
                    time.sleep(wait)
                else:
                    time.sleep(1)
            except Exception as e:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 2)
                else:
                    print(f"  [WARN] WB API 请求失败({category_key} p{page}): {e}")
        time.sleep(delay)

    # 去重(按 nm_id)
    seen = set()
    unique = []
    for p in all_products:
        if p["nm_id"] not in seen:
            seen.add(p["nm_id"])
            unique.append(p)
    return unique


# ====== Google News RSS 采集 ======

def fetch_russian_news(config):
    """抓取俄语+英语 Google News RSS,获取俄罗斯电商市场趋势"""
    rss_config = config.get("scrape_sources", {}).get("russian_news_rss", {})
    feeds = rss_config.get("feeds", [])
    articles = []

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
                if len(title) < 10:
                    continue
                source_name = entry.get("source", {}).get("title", "") if hasattr(entry, "source") else ""
                published = entry.get("published", "")
                summary = entry.get("summary", "")
                articles.append({
                    "title": title,
                    "link": link,
                    "source_name": source_name,
                    "published": published,
                    "summary": summary[:300] if summary else "",
                })
        except Exception as e:
            print(f"  [WARN] RSS 请求失败: {e}")

    # 去重(按链接)
    seen = set()
    unique = []
    for a in articles:
        link = a.get("link", "")
        if link not in seen:
            seen.add(link)
            unique.append(a)
    return unique


# ====== 汇率获取 ======

def fetch_rub_cny_rate():
    """获取 1 CNY = ? RUB 汇率"""
    try:
        r = requests.get("https://open.er-api.com/v6/latest/CNY", timeout=10)
        if r.status_code == 200:
            return r.json().get("rates", {}).get("RUB")
    except Exception:
        pass
    # 降级: 使用近似汇率
    return 13.5


# ====== 商品分析与推荐 ======

WB_CATEGORY_CN = {
    "electronics": "电子产品",
    "home": "家居厨房",
    "clothing": "服装鞋包",
    "kids": "母婴玩具",
    "beauty": "美妆健康",
    "sports": "运动户外",
}

CERT_REQUIREMENTS = {
    "electronics": "需 EAC 认证(TR CU 004/2011, TR CU 020/2011), 部分产品需 FSS 通知",
    "home": "食品接触类需 EAC 声明(TR CU 005/2011), 纺织品需 TR CU 017/2011",
    "clothing": "纺织品需 EAC 认证(TR CU 017/2011), 儿童服装需额外 GOST 认证",
    "kids": "儿童用品需 EAC 认证(TR CU 007/2011), 玩具需 TR CU 008/2011, 严格安全标准",
    "beauty": "化妆品需 EAC 声明(TR CU 009/2011), 香水需额外认证",
    "sports": "一般运动装备需 EAC 声明, 防护装备需严格认证",
}

SEASONALITY_MAP = {
    1: {"season": "冬季", "hot": ["electronics", "home", "clothing"], "note": "保暖商品、新年礼品、电子产品需求高"},
    2: {"season": "冬末", "hot": ["electronics", "home", "clothing"], "note": "情人节礼品、冬季清仓"},
    3: {"season": "初春", "hot": ["clothing", "beauty", "home"], "note": "三八节礼品、换季服装、春季家居"},
    4: {"season": "春季", "hot": ["sports", "beauty", "clothing"], "note": "户外装备、运动用品需求上升"},
    5: {"season": "春末", "hot": ["sports", "clothing", "kids"], "note": "五一假期、户外烧烤、夏装上市"},
    6: {"season": "夏季", "hot": ["sports", "clothing", "beauty"], "note": "夏季户外、防晒、旅游用品旺季"},
    7: {"season": "盛夏", "hot": ["sports", "beauty", "electronics"], "note": "暑期消费、泳装、降温设备"},
    8: {"season": "夏末", "hot": ["electronics", "kids", "home"], "note": "开学季电子产品、文具、返校用品"},
    9: {"season": "初秋", "hot": ["clothing", "home", "electronics"], "note": "换季服装、家居用品、双十一备货"},
    10: {"season": "秋季", "hot": ["home", "electronics", "clothing"], "note": "保暖用品、双十一大促备货"},
    11: {"season": "冬初", "hot": ["electronics", "home", "clothing"], "note": "黑五/圣诞礼品、冬季用品采购高峰"},
    12: {"season": "冬季", "hot": ["electronics", "home", "kids"], "note": "圣诞新年礼品、玩具、冬季商品旺销"},
}


def generate_recommendation(product, rank):
    """根据商品数据生成中文推荐理由"""
    name_cn = product.get("product_name_cn", "")
    price_rub = product.get("price_rub", 0)
    price_cny = product.get("price_cny", 0)
    rating = product.get("rating", 0)
    reviews = product.get("review_count", 0)
    cat_cn = product.get("category_cn", "")

    reasons = []

    # 价格吸引力
    if price_cny < 50:
        reasons.append(f"低价位商品(¥{price_cny}),适合新手试水,资金压力小")
    elif price_cny < 150:
        reasons.append(f"中等价位(¥{price_cny}),利润空间充足(预估30-50%),性价比突出")
    elif price_cny < 500:
        reasons.append(f"高客单价(¥{price_cny}),单件利润可观,适合精品运营路线")
    else:
        reasons.append(f"高价值商品(¥{price_cny}),需注意物流保险和售后保障")

    # 评分分析
    if rating >= 4.7:
        reasons.append(f"极高用户评分({rating}分),产品质量和用户满意度有保证")
    elif rating >= 4.3:
        reasons.append(f"良好用户口碑({rating}分),市场接受度较高")
    else:
        reasons.append(f"评分{rating}分,市场反馈尚可,需关注差评原因")

    # 竞争度分析(基于评论数)
    if reviews < 200:
        reasons.append(f"评论数较少({reviews}条),竞争度低,蓝海潜力大")
    elif reviews < 1000:
        reasons.append(f"中等评论量({reviews}条),有一定竞争但仍有进入空间")
    elif reviews < 5000:
        reasons.append(f"评论量较高({reviews}条),市场需求旺盛,需差异化策略")
    else:
        reasons.append(f"头部商品({reviews}条评论),市场需求极强,建议关注供应链优势")

    # 类目分析
    month = datetime.now().month
    season_info = SEASONALITY_MAP.get(month, SEASONALITY_MAP[1])
    if cat_cn in [WB_CATEGORY_CN.get(c, c) for c in season_info["hot"]]:
        reasons.append(f"符合{season_info['season']}消费趋势,当前为{cat_cn}类目旺季")

    return "；".join(reasons)


def assess_risks(product):
    """生成风险提示"""
    risks = []
    cat_key = product.get("category_key", "")

    # 认证风险
    cert = CERT_REQUIREMENTS.get(cat_key, "需确认具体认证要求")
    risks.append(f"认证要求: {cert}")

    # 竞争风险(基于评论数)
    reviews = product.get("review_count", 0)
    if reviews > 5000:
        risks.append("高竞争类目,头部商品护城河深,新入场者需差异化定位")
    elif reviews > 1000:
        risks.append("中等竞争,建议分析TOP10竞品的定价和卖点后再入场")

    # 价格风险
    price_cny = product.get("price_cny", 0)
    if price_cny > 300:
        risks.append("高客单价商品退货/售后成本较高,建议购买物流保险")
    if price_cny < 30:
        risks.append("低价商品利润薄,需通过走量实现盈利,注意物流成本占比")

    # 季节性风险
    month = datetime.now().month
    cat_cn = product.get("category_cn", "")
    season_info = SEASONALITY_MAP.get(month, SEASONALITY_MAP[1])
    hot_cats_cn = [WB_CATEGORY_CN.get(c, c) for c in season_info["hot"]]
    if cat_cn not in hot_cats_cn:
        risks.append(f"当前{season_info['season']}非{cat_cn}传统旺季,需评估库存周转风险")

    return risks


# ====== 市场概览生成 ======

def generate_market_summary(products, news_articles, rate):
    """基于采集数据生成当日市场概览"""
    now = datetime.now()
    month = now.month
    season_info = SEASONALITY_MAP.get(month, SEASONALITY_MAP[1])

    parts = []

    # 商品数据统计
    if products:
        is_news_mode = products[0].get("is_news_insight", False) if products else False
        cats = defaultdict(int)
        total_products = len(products)
        for p in products:
            cats[p.get("category_cn", "其他")] += 1

        if is_news_mode:
            parts.append(f"今日基于俄罗斯电商新闻分析,识别 {total_products} 个潜力类目")
        else:
            avg_rating = sum(p["rating"] for p in products if p.get("rating", 0) > 0) / max(1, sum(1 for p in products if p.get("rating", 0) > 0))
            avg_price = sum(p["price_rub"] for p in products if p.get("price_rub", 0) > 0) / max(1, sum(1 for p in products if p.get("price_rub", 0) > 0))
            parts.append(f"今日采集 {total_products} 款高评分商品(均分 {avg_rating:.1f}/5.0), 均价 {avg_price:.0f} ₽ (约 {avg_price/rate:.0f} CNY)")
        top_cats = sorted(cats.items(), key=lambda x: -x[1])[:3]
        parts.append(f"热门类目: {'、'.join(f'{c}({n}款)' for c, n in top_cats)}")

    # 季节信息
    parts.append(f"当前季节: {season_info['season']} — {season_info['note']}")

    # 新闻摘要
    if news_articles:
        parts.append(f"今日采集俄罗斯电商相关资讯 {len(news_articles)} 条")
        if len(news_articles) >= 3:
            top_news = news_articles[:3]
            for n in top_news:
                title = n.get("title", "")[:80]
                if title:
                    parts.append(f"  · {title}")

    # 汇率
    parts.append(f"参考汇率: 1 CNY ≈ {rate:.2f} RUB (数据来源: open.er-api.com)")

    # 免责声明
    parts.append("> ⚠️ 以上分析基于公开数据自动生成,仅供选品参考,不构成投资建议。实际采购前请核实平台最新数据和认证要求。")

    return "\n\n".join(parts)


# ====== Markdown 生成 ======

# ====== 新闻趋势分析 (WB数据不可用时的降级模式) ======

NEWS_CATEGORY_KEYWORDS = {
    "electronics": ["смартфон", "наушники", "ноутбук", "телефон", "гаджет", "электроника",
                     "smartphone", "headphone", "laptop", "gadget", "electronics",
                     "手机", "耳机", "笔记本", "电子产品", "智能"],
    "home": ["дом", "кухня", "посуда", "мебель", "интерьер", "товары для дома",
             "home", "kitchen", "furniture", "household",
             "家居", "厨房", "家具", "日用"],
    "clothing": ["одежда", "обувь", "мода", "аксессуар", "сумка",
                 "clothing", "shoes", "fashion", "apparel",
                 "服装", "鞋", "时尚", "配饰"],
    "beauty": ["косметика", "уход", "парфюм", "красота", "макияж",
               "cosmetic", "beauty", "skincare", "perfume",
               "美妆", "护肤", "化妆品", "香水"],
    "sports": ["спорт", "фитнес", "тренировка", "йога", "outdoor", "туризм",
               "sport", "fitness", "training", "yoga", "camping",
               "运动", "健身", "户外", "瑜伽"],
    "kids": ["детский", "игрушка", "ребенок", "школа", "канцелярия",
             "kids", "toys", "children", "baby",
             "儿童", "玩具", "母婴", "婴儿"],
}


def generate_news_based_insights(news_articles, rate):
    """当 WB 数据不可用时,基于新闻标题分析生成选品趋势建议"""
    insights = []
    cat_hits = defaultdict(list)
    now = datetime.now()

    # 分类新闻到不同类目
    for article in news_articles:
        title = article.get("title", "")
        title_lower = title.lower()
        for cat_key, keywords in NEWS_CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in title_lower:
                    cat_hits[cat_key].append(article)
                    break

    # 每个类目生成一条趋势建议
    rank = 0
    for cat_key in ["electronics", "home", "clothing", "beauty", "sports", "kids"]:
        articles = cat_hits.get(cat_key, [])
        cat_cn = WB_CATEGORY_CN.get(cat_key, cat_key)
        if not articles:
            continue
        rank += 1
        if rank > 10:
            break

        # 汇总该类目的新闻标题
        titles = [a.get("title", "")[:100] for a in articles[:3]]
        sources = [a.get("source_name", "") or a.get("link", "")[:60] for a in articles[:3]]

        # 生成参考价格(基于类目经验值)
        ref_prices = {
            "electronics": (1500, 8000),
            "home": (500, 3000),
            "clothing": (800, 4000),
            "beauty": (300, 2000),
            "sports": (600, 3500),
            "kids": (400, 2500),
        }
        min_p, max_p = ref_prices.get(cat_key, (500, 3000))
        ref_price = (min_p + max_p) // 2
        ref_cny = round(ref_price / rate, 1) if rate else 0

        reason_parts = [
            f"基于 {len(articles)} 条相关新闻的趋势分析",
            f"俄罗斯电商资讯中{cat_cn}类目近期讨论活跃",
        ]
        if articles:
            top_title = titles[0][:80] if titles else ""
            if top_title:
                reason_parts.append(f"相关动态: {top_title}")

        # 季节性提示
        month = now.month
        season_info = SEASONALITY_MAP.get(month, SEASONALITY_MAP[1])
        hot_cats_cn = [WB_CATEGORY_CN.get(c, c) for c in season_info["hot"]]
        if cat_cn in hot_cats_cn:
            reason_parts.append(f"当前{season_info['season']}为此类目传统旺季,需求上升中")

        risks = [
            f"此为新闻趋势分析,非实时商品数据,仅供参考方向",
            f"建议打开 Wildberries/Ozon 搜索 '{cat_cn}' 确认具体商品数据",
            f"价格区间基于类目经验估算({min_p:,}-{max_p:,} RUB),实际价格以平台为准",
        ]

        source_urls = [a.get("link", "") for a in articles[:3] if a.get("link")]

        insights.append({
            "rank": rank,
            "product_name_ru": f"{cat_cn}类目趋势",
            "product_name_cn": f"📊 {cat_cn}类目选品机会",
            "brand": "",
            "category_key": cat_key,
            "category_cn": cat_cn,
            "price_rub": ref_price,
            "price_cny": ref_cny,
            "rating": 0,
            "review_count": len(articles),
            "wb_url": "",
            "source_urls": source_urls,
            "recommendation_reason_cn": "；".join(reason_parts),
            "risk_warnings_cn": risks,
            "news_titles": titles,
            "is_news_insight": True,
        })

    return insights


def build_featured_md(featured_data):
    """生成置顶选品文章的 Markdown 内容"""
    date_str = featured_data["date"]
    products = featured_data["products"]
    market_summary = featured_data.get("market_summary_cn", "")
    verified = featured_data.get("verified", False)
    data_sources = featured_data.get("data_sources", [])
    generated_at = featured_data.get("generated_at", "")

    md = f"""# 🏆 Ozon俄罗斯站每日选品推荐 — {date_str}

> 📊 数据采集时间：{generated_at or date_str}
> 🔍 数据来源：{' + '.join(s['name'] for s in data_sources) if data_sources else 'Wildberries实时数据 + Google News俄罗斯电商资讯'}
> ✅ 验证状态：{'已验证' if verified else '待验证 — 运行 `python scripts/ozon_verifier.py --check` 进行核查'}
> 💱 参考汇率：数据中已提供 CNY 估算价格

---

## 📈 今日市场概览

{market_summary}

---

"""

    medals = ["🥇", "🥈", "🥉"] + ["📦"] * 7
    for i, product in enumerate(products):
        rank = i + 1
        medal = medals[i] if i < len(medals) else "📦"
        name_ru = product.get("product_name_ru", "")
        name_cn = product.get("product_name_cn", name_ru)
        brand = product.get("brand", "")
        price_rub = product.get("price_rub", 0)
        price_cny = product.get("price_cny", 0)
        rating = product.get("rating", 0)
        reviews = product.get("review_count", 0)
        cat_cn = product.get("category_cn", "")
        reason = product.get("recommendation_reason_cn", "")
        risks = product.get("risk_warnings_cn", [])
        source_urls = product.get("source_urls", [])
        wb_url = product.get("wb_url", "")

        is_news_insight = product.get("is_news_insight", False)

        md += f"""## {medal} 推荐 #{rank}: {name_cn}

> {name_ru}{' / ' + brand if brand and brand not in name_ru else ''}

| 属性 | 详情 |
|------|------|
| 📂 类目 | {cat_cn or '综合'} |
| 💰 参考价格区间 | {price_rub:,} ₽ (≈ {price_cny} CNY) 起 |
"""
        if not is_news_insight and rating > 0:
            md += f"""| ⭐ 评分 | {rating} / 5.0 |
| 💬 评论数 | {reviews:,} |
| 🏪 平台 | Wildberries |
"""
        else:
            md += f"""| 📰 数据来源 | 俄罗斯电商新闻趋势分析 ({reviews} 条相关新闻) |
| 🔍 数据模式 | 新闻趋势挖掘 (非实时商品数据) |
"""

        md += f"""
### 💡 推荐理由

{reason}

### ⚠️ 风险提示

"""
        for risk in risks:
            md += f"- {risk}\n"

        md += "\n### 📎 数据溯源\n\n"
        if wb_url:
            md += f"- [Wildberries 商品页]({wb_url})\n"
        for src_url in source_urls[:5]:
            if src_url != wb_url:
                md += f"- [数据来源]({src_url})\n"

        md += "\n---\n\n"

    # 免责声明
    md += """## 📋 免责声明

> 本推荐基于 Wildberries 平台公开可获取的商品数据及 Google News 俄罗斯电商资讯自动生成,仅供选品参考,不构成投资建议。
>
> - 数据可能存在延迟,实际售价和库存以平台实时显示为准
> - 评分和评论数为采集时刻的快照数据
> - 认证要求请以俄罗斯官方最新法规为准
> - 物流成本需根据具体线路和货代报价核算
>
> 📝 数据验证: 运行 `python scripts/ozon_verifier.py --check` 进行内容核查

---

*本文章由 Ozon选品机器人自动生成 · 猫明之主小站 · {date_str}*
"""

    return md


# ====== 保存与索引更新 ======

def save_featured_post(featured_data, md_content):
    """保存置顶文章: markdown文件 + featured JSON + 更新 posts.json"""
    slug = featured_data["slug"]
    date_str = featured_data["date"]

    # 1. 写入 Markdown
    md_path = os.path.join(POSTS_DIR, f"{slug}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 2. 写入 featured JSON
    save_json(FEATURED_JSON_PATH, featured_data)

    # 3. 更新 posts.json (添加或更新置顶文章条目)
    posts = load_json(JSON_PATH, [])
    entry = {
        "slug": slug,
        "title": f"🏆 Ozon每日选品推荐 — {date_str}",
        "date": date_str,
        "excerpt": featured_data.get("market_summary_cn", "")[:150] or f"今日推荐{len(featured_data.get('products',[]))}款俄罗斯热销商品",
        "cat": "ozon-pick",
        "sub": "daily-select",
        "featured": True,
        "verified": featured_data.get("verified", False),
        "source": "Wildberries API + Google News RSS",
        "source_name": "Ozon选品机器人",
    }

    # 移除旧的 featured 标记 和 同日 slug
    new_posts = []
    for p in posts:
        p.pop("featured", None)
        if p.get("slug") == slug:
            continue
        new_posts.append(p)
    new_posts.insert(0, entry)
    # 保持日期降序
    new_posts.sort(key=lambda x: x.get("date", ""), reverse=True)
    save_json(JSON_PATH, new_posts)

    print(f"[OK] 置顶文章已保存: {slug}")
    print(f"    Markdown: posts/{slug}.md")
    print(f"    Featured JSON: posts/featured_ozon_pick.json")
    print(f"    总文章数: {len(new_posts)}")


# ====== 主编排 ======

def run_selector(config, dry_run=False):
    """主编排器: 采集数据 → 分析推荐 → 生成文章 → 保存"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    generated_at = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    slug = f"ozon-daily-pick-{date_str}"

    print(f"\n{'='*60}")
    print(f"  Ozon 俄罗斯站每日选品 — {date_str}")
    print(f"{'='*60}\n")

    # 1. 获取汇率
    print("[1/5] 获取汇率...")
    rate = fetch_rub_cny_rate()
    print(f"  1 CNY ≈ {rate:.2f} RUB")

    # 2. 采集 Wildberries 数据
    print("[2/5] 采集 Wildberries 热门商品...")
    all_wb_products = []
    wb_config = config.get("scrape_sources", {}).get("wildberries", {})
    if wb_config.get("enabled", True):
        categories = wb_config.get("categories", ["electronics", "home", "clothing", "kids", "beauty", "sports"])
        keywords_map = wb_config.get("search_keywords", {})
        max_pages = wb_config.get("max_pages_per_category", 2)

        for cat_key in categories:
            keyword = keywords_map.get(cat_key, cat_key)
            print(f"  → 采集 {cat_key} ({keyword})...")
            try:
                products = fetch_wildberries(cat_key, keyword, config, max_pages)
                print(f"    获取 {len(products)} 款商品")
                all_wb_products.extend(products)
            except Exception as e:
                print(f"    [ERROR] {e}")
    else:
        print("  [SKIP] Wildberries 采集已禁用")

    # 3. 采集俄罗斯电商新闻
    print("[3/5] 采集俄罗斯电商新闻...")
    news_articles = []
    rss_config = config.get("scrape_sources", {}).get("russian_news_rss", {})
    if rss_config.get("enabled", True):
        news_articles = fetch_russian_news(config)
        print(f"  获取 {len(news_articles)} 条新闻")
    else:
        print("  [SKIP] 新闻 RSS 已禁用")

    # 4. 分析、翻译、推荐
    print("[4/5] 分析商品数据,生成选品推荐...")
    # 按评分×评论数的加权排序
    for p in all_wb_products:
        p["score"] = p["rating"] * min(p["review_count"], 10000) / 100
    all_wb_products.sort(key=lambda x: x["score"], reverse=True)

    max_products = config.get("output", {}).get("max_products", 10)
    top_products = all_wb_products[:max_products]

    # 翻译 + 推荐理由 + 风险
    featured_products = []
    for rank, p in enumerate(top_products):
        name_cn = translate_ru(p["product_name_ru"])
        cat_cn = WB_CATEGORY_CN.get(p.get("category_key", ""), "综合")
        price_cny = round(p["price_rub"] / rate, 1) if rate else 0

        product_data = {
            "rank": rank + 1,
            "product_name_ru": p["product_name_ru"],
            "product_name_cn": name_cn,
            "brand": p.get("brand", ""),
            "category_key": p.get("category_key", ""),
            "category_cn": cat_cn,
            "price_rub": p["price_rub"],
            "price_cny": price_cny,
            "rating": p["rating"],
            "review_count": p["review_count"],
            "wb_url": p.get("wb_url", ""),
            "source_urls": [p.get("wb_url", "")] if p.get("wb_url") else [],
            "recommendation_reason_cn": generate_recommendation(
                {"product_name_cn": name_cn, "price_rub": p["price_rub"], "price_cny": price_cny,
                 "rating": p["rating"], "review_count": p["review_count"], "category_cn": cat_cn,
                 "category_key": p.get("category_key", "")}, rank + 1
            ),
            "risk_warnings_cn": assess_risks(
                {"category_key": p.get("category_key", ""), "review_count": p["review_count"],
                 "price_cny": price_cny, "category_cn": cat_cn}
            ),
        }
        featured_products.append(product_data)

    print(f"  最终推荐 {len(featured_products)} 款商品")

    # 如果 WB 数据不足,基于新闻生成选品趋势分析
    if len(featured_products) < 3:
        print("  [INFO] 商品数据不足,基于新闻生成选品趋势分析...")
        news_products = generate_news_based_insights(news_articles, rate)
        featured_products = news_products
        print(f"  基于新闻生成 {len(featured_products)} 条选品趋势")

    # 5. 生成内容
    print("[5/5] 生成市场概览和 Markdown...")
    market_summary = generate_market_summary(featured_products, news_articles, rate)

    # 构建数据源列表
    data_sources = []
    if wb_config.get("enabled", True) and all_wb_products:
        data_sources.append({"name": "Wildberries Search API", "url": "https://search.wb.ru/", "reliability": "medium"})
    if rss_config.get("enabled", True) and news_articles:
        data_sources.append({"name": "Google News RSS (RU+EN)", "url": "https://news.google.com/", "reliability": "medium"})

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

    # 保存
    save_featured_post(featured_data, md_content)

    # 保存原始数据到 data/ozon_raw/
    raw_dir = os.path.join(BASE_DIR, config.get("output", {}).get("data_dump_dir", "data/ozon_raw"))
    ensure_dir(raw_dir)
    raw_dump = {
        "date": date_str,
        "generated_at": generated_at,
        "rate_cny_rub": rate,
        "wb_products_all": all_wb_products[:50],
        "news_articles": news_articles[:20],
    }
    raw_path = os.path.join(raw_dir, f"raw_{date_str}.json")
    save_json(raw_path, raw_dump)
    print(f"[OK] 原始数据已存档: {raw_path}")

    # 清理 7 天前的原始数据
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
                    print(f"[CLEAN] 删除过期数据: {fname}")
            except Exception:
                pass

    print(f"\n{'='*60}")
    print(f"  ✅ 完成! 今日推荐 {len(featured_products)} 款商品")
    print(f"{'='*60}\n")

    return featured_data


# ====== 主入口 ======

def main():
    do_push = "--push" in sys.argv
    dry_run = "--dry-run" in sys.argv

    config = load_json(CONFIG_PATH, {})
    if not config:
        print("[ERROR] 无法加载配置文件: scripts/ozon_config.json")
        sys.exit(1)

    if not config.get("enabled", True):
        print("[SKIP] Ozon selector 已在配置中禁用 (enabled: false)")
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
