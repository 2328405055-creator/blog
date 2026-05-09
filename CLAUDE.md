# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人学习仪表盘网站，两大栏目：跨境电商（Ozon/Yandex/俄罗斯铺货选品）+ 每日健身（徒手自重/瑜伽垫/男女教程）。静态站点，GitHub Pages 托管，自定义域名。

- 域名: `20020426.top`，DNS 在 Cloudflare 管理
- GitHub 仓库: `2328405055-creator/blog`，分支 `master`
- GitHub Pages 已开启，自定义域名已配置

## 常用命令

```bash
# 每日生成10篇文章并自动推送上线
cd D:\games\blog
python scripts/daily_generator.py --push

# 只生成不推送（测试用）
python scripts/daily_generator.py

# 手动推送
git add . && git commit -m "更新" && git push
```

## 架构

```
D:\games\blog\
├── index.html          # 单页应用，全部/跨境电商/健身三标签切换
├── CNAME               # 20020426.top（GitHub Pages 自定义域名）
├── posts/
│   ├── posts.json      # 文章索引，所有文章元数据
│   └── *.md            # 每篇文章一个 .md 文件
└── scripts/
    ├── daily_generator.py  # 每日内容生成器 v3
    └── tracker.json        # 追踪已发文章，防止重复
```

**数据流:** `daily_generator.py` → 抓取 Google News RSS → 生成 .md + 更新 posts.json → git push → GitHub Pages 自动部署 → `20020426.top`

**posts.json 结构:** 每篇文章 `{slug, title, date, excerpt, cat, sub, source?, source_name?}`
- `cat`: `"cross-border"` | `"fitness"`
- `sub`: 子分类标识（如 `"ozon"`, `"selection"`, `"male"`, `"yoga-mat"` 等）

**内容来源:** Google News RSS（跨境电商中文新闻 + 健身英文教程），每篇标注来源媒体和原文链接，去重逻辑防止重复推送。

## 用户偏好

- 所有通信和输出使用中文
- 跨境电商方向聚焦：Ozon + Yandex 平台，俄罗斯市场，铺货模式选品上架
- 健身仅需徒手自重训练 + 瑜伽垫，男女教程都要
- 内容必须有真实来源、可追溯、非 AI 凭空生成
