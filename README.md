# 猫明之主 · 个人学习仪表盘

> 跨境电商实战 + 徒手健身 + AI 学习 — 安静学习，温柔生长。

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-20020426.top-blue)](https://20020426.top)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

## 内容方向

| 栏目 | 内容 | 来源 |
|------|------|------|
| 跨境教程 | Ozon / Yandex / Wildberries 俄罗斯铺货选品实战 | Google News RSS + Firecrawl + AI 总结 |
| 每日健身 | 徒手自重训练、瑜伽垫动作、男女教程 | Google News RSS + YouTube 频道 |
| AI 学习 | AI 工具教程、行业动态、AI 与电商交汇 | Google News RSS (中英文) |
| Ozon 选品 | Wildberries 真实销量排序 + 每日推荐 | WB v18 API + Google News |

## 技术栈

- **前端**: 纯 HTML/CSS/JS 单页应用 — 毛玻璃导航、星空粒子背景、蓝白金色调
- **后端**: Python 脚本 — RSS 抓取 + Firecrawl 网页采集 + AI 总结 (千问/DeepSeek)
- **托管**: GitHub Pages (域名 `20020426.top`，DNS Cloudflare)
- **CI/CD**: GitHub Actions 每日自动生成内容
- **依赖**: `firecrawl-py`, `openai`, `feedparser`, `requests`, `tenacity`, `pydantic`

## 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/2328405055-creator/blog.git
cd blog

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 4. 生成每日内容（不推送）
python scripts/daily_generator.py

# 5. 生成每日内容并推送
python scripts/daily_generator.py --push

# 6. 本地预览
# 用浏览器直接打开 index.html，或用 Python 启动本地服务器:
python -m http.server 8080
```

### GitHub Actions 自动部署

项目已配置 `.github/workflows/daily-generate.yml`，每天 UTC 4:00 自动运行。

**配置步骤**:

1. 进入 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 添加以下 Repository secrets:

| Secret 名称 | 说明 |
|-------------|------|
| `BLOG_FIRECRAWL_API_KEY` | Firecrawl API Key |
| `BLOG_PRIMARY_API_KEY` | 千问 API Key |
| `BLOG_PRIMARY_API_BASE` | 千问 API Base URL |
| `BLOG_PRIMARY_MODEL` | 主模型名称 (如 `qwen-plus`) |
| `BLOG_BACKUP_API_KEY` | DeepSeek API Key |
| `BLOG_BACKUP_API_BASE` | DeepSeek API Base URL |
| `BLOG_BACKUP_MODEL` | 备用模型名称 (如 `deepseek-chat`) |
| `BLOG_ENRICH_ENABLED` | 是否启��内容富化 (`true`/`false`) |
| `BLOG_TARGET_WORDS` | 目标字数 |
| `BLOG_SCRAPE_TIMEOUT` | 抓取超时秒数 |

## 环境变量

所有配置通过 `.env` 文件或系统环境变量注入。详见 [.env.example](./.env.example)。

| 变量 | 必填 | 说明 |
|------|------|------|
| `BLOG_FIRECRAWL_API_KEY` | 是 | Firecrawl 网页抓取 API Key |
| `BLOG_PRIMARY_API_KEY` | 是 | 主 AI 模型 API Key (千问) |
| `BLOG_PRIMARY_API_BASE` | 是 | 主 AI API 地址 |
| `BLOG_PRIMARY_MODEL` | 是 | 主模型名称 |
| `BLOG_BACKUP_API_KEY` | 否 | 备用 AI 模型 API Key (DeepSeek) |
| `BLOG_BACKUP_API_BASE` | 否 | 备用 AI API 地址 |
| `BLOG_BACKUP_MODEL` | 否 | 备用模型名称 |
| `BLOG_ENRICH_ENABLED` | 否 | 启用内容富化 (默认 false) |
| `BLOG_TARGET_WORDS` | 否 | AI 总结目标字数 (默认 700) |
| `BLOG_SCRAPE_TIMEOUT` | 否 | 抓取超时秒数 (默认 30) |

## 项目结构

```
blog/
├── index.html               # 单页应用主入口
├── 404.html                 # 自定义 404 页面
├── CNAME                    # 自定义域名 (20020426.top)
├── robots.txt               # SEO 爬虫规则
├── sitemap.xml              # 自动生成的站点地图
├── README.md                # 本文件
├── LICENSE                  # 开源协议
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
├── CLAUDE.md                # AI 辅助开发指导
│
├── assets/                  # 前端静态资源
│   ├── css/main.css         # 全局样式 (蓝白金色调)
│   └── js/                  # JS 模块
│       ├── app.js           # 主入口 + 数据加载 + 渲染
│       ├── article.js       # 文章详情 + 目录 + 分享
│       ├── search.js        # 搜索 + Tab 切换 + 分页
│       ├── games.js         # 数独 + 呼吸放松 + 音乐
│       ├── theme.js         # 主题切换 + 粒子星空
│       └── ozon.js          # Ozon 精选卡片 + 详情
│
├── posts/                   # 文章内容
│   ├── posts.json           # 文章索引
│   ├── featured_ozon_pick.json  # Ozon 每日推荐
│   └── *.md                 # 单篇文章
│
├── scripts/                 # Python 脚本入口
│   ├── daily_generator.py   # 每日内容生成器入口
│   ├── ozon_selector.py     # Ozon 选品推荐入口
│   └── ozon_verifier.py     # 内容验证插件
│
├── textscripts/             # Python 核心模块
│   ├── config.py            # 配置管理
│   ├── cli.py               # CLI 入口
│   ├── generators/          # 内容生成
│   ├── scrapers/            # 数据采集
│   └── utils/               # 工具函数
│
├── data/ozon_raw/           # Ozon 原始采集数据
├── .github/workflows/       # GitHub Actions
└── log/                     # 运行日志
```

## 常用命令

```bash
# 每日生成文章 + 更新 sitemap + Git 推送
python scripts/daily_generator.py --push

# 只生成不推送
python scripts/daily_generator.py

# Ozon 每日选品推荐
python scripts/ozon_selector.py --push

# Ozon 选品预览 (不写入文件)
python scripts/ozon_selector.py --dry-run

# 手动 Git 推送
git add . && git commit -m "手动更新" && git push
```

## 网站功能

- 首页：搜索、引言、歇后语、字谜、卢布汇率
- 文章：列表 + 详情页、目录导航、社交分享
- 游戏：数独 (简单/普通/困难 + 排行榜)、呼吸放松引导
- 主题：暗色/亮色一键切换
- SEO：JSON-LD 结构化数据 + meta 标签 + sitemap + robots.txt
- a11y：ARIA 属性 + 键盘导航 + prefers-reduced-motion

## License

MIT
