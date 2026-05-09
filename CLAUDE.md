# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

猫明之主小站 — 个人学习仪表盘网站，三大栏目：跨境电商（Ozon/Yandex/俄罗斯铺货选品）+ 每日健身（徒手自重/瑜伽垫/男女教程）+ AI新闻。静态站点，GitHub Pages 托管。

- 域名: `20020426.top`，DNS 在 Cloudflare（4条A记录 + www CNAME）
- GitHub: `2328405055-creator/blog`，分支 `master`
- GitHub Pages 自定义域名已配置，**需手动开启 Enforce HTTPS**

## 常用命令

```bash
cd D:\games\blog

# 每日生成10篇文章（5跨境+2健身+3AI）+ 更新sitemap + 推送
python scripts/daily_generator.py --push

# 只生成不推送
python scripts/daily_generator.py

# 手动推送
git add . && git commit -m "更新" && git push
```

## 文件架构

```
D:\games\blog\
├── index.html           # 单页应用（Apple风格，毛玻璃导航，星空背景）
├── 404.html             # 自定义404页面
├── CNAME                # 20020426.top
├── robots.txt           # SEO爬虫规则
├── sitemap.xml          # 自动生成，包含所有文章URL
├── CLAUDE.md
├── posts/
│   ├── posts.json       # 文章索引 [{slug,title,date,excerpt,cat,sub,source?,source_name?}]
│   └── *.md             # 每篇文章一个.md
└── scripts/
    ├── daily_generator.py  # v3 来源驱动生成器 + sitemap生成
    └── tracker.json        # 已发文章追踪
```

**cat 值:** `"cross-border"` | `"fitness"` | `"ai-news"`

## 网站功能

- 首页工具：日期卡片、歇后语（点看答案）、猜字谜（交互输入）
- TODO待办：导航栏📋按钮，密码 `catming`，localStorage存储
- 呼吸放松：右下角🧘按钮
- 卢布汇率：实时显示1 CNY ≈ X RUB（1小时缓存）
- 分页：每页10篇
- SEO：JSON-LD结构化数据 + meta标签 + sitemap + ARIA无障碍
- 复制引言、文章分享

## 内容来源

Google News RSS（跨境电商中文 + 健身英文 + AI中英文），每篇标注来源媒体和链接。tracker.json防止重复推送。

## 用户偏好

- 所有沟通用中文
- 跨境电商：Ozon+Yandex平台，俄罗斯市场，铺货选品上架
- 健身：徒手自重训练+瑜伽垫，男女教程都要
- 内容必须有真实来源可追溯
