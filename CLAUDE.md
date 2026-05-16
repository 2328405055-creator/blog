# CLAUDE.md

Project guide for Claude Code. Keep context small and avoid reading unrelated generated content.

## Project

- Site: `20020426.top`
- Repo: `2328405055-creator/blog`
- Hosting: GitHub Pages static site
- Stack: plain HTML/CSS/JS plus Python generation scripts
- Topics: cross-border ecommerce, Ozon/Yandex/Wildberries, home fitness, AI learning

## Key Files

### Pipeline 4 层架构

```
textscripts/
├── cli.py                     # 统一 CLI: generate / publish / rag
├── config.py                  # 配置加载 (.env > config.json > 环境变量)
├── models.py                  # Pydantic 数据模型 (ArticleEntry, GateResult...)
│
├── scrapers/                  # 第1层: 数据采集
│   ├── base.py                # BaseScraper 抽象类
│   ├── news_scraper.py        # Google News RSS
│   ├── firecrawl_scraper.py   # Firecrawl 深度抓取 + 交叉合成
│   ├── wildberries_scraper.py # WB API 商品采集
│   └── web_search.py          # [预留] 通用搜索兜底
│
├── rag/                       # 第2层: 轻量 RAG (零新依赖)
│   ├── embedder.py            # Embedding (API 优先, 关键词向量降级)
│   ├── vector_store.py        # JSON 文件向量存储
│   ├── deduplicator.py        # 余弦相似度去重 (默认阈值 0.85)
│   ├── retriever.py           # 相关推荐 + 语义搜索
│   └── indexer.py             # 全量/增量索引构建
│
├── generators/                # 第3层: 内容生成
│   ├── base.py                # BaseGenerator 抽象类
│   ├── daily_generator.py     # 三板块生成 (跨境/健身/AI)
│   ├── ozon_generator.py      # Ozon 选品生成器 (从 scripts/ 迁移)
│   ├── unified_generator.py   # 统一调度 4 板块
│   ├── prompts.py             # LLM Prompt 模板库
│   └── markdown_builder.py    # [预留] Markdown 构建
│
├── publishers/                # 第4层: 发布分发
│   ├── git_publisher.py       # Git add/commit/push
│   ├── site_publisher.py      # 统一发布入口 (sitemap + git)
│   └── quality_gate.py        # 质量门禁 (字数/来源/去重/结构)
│
└── utils/                     # 横切工具
    ├── file_ops.py            # JSON/MD 读写 / slugify / hash
    ├── llm.py                 # AI 客户端 (千问主 + DeepSeek备)
    ├── ru_utils.py            # 俄语翻译 / 推荐理由 / 风险评估
    ├── sitemap_generator.py   # Sitemap 生成
    └── markdown_utils.py      # Markdown 构建 (跨境/健身/AI)
```

### 数据文件
- `index.html`: 主页面 (SPA)
- `assets/css/main.css`: 全局样式
- `assets/js/*.js`: 前端模块 (含 MiniSearch 语义搜索)
- `assets/js/vendor/minisearch.js`: MiniSearch 库 (vendor, ~18KB)
- `posts/posts.json`: 文章索引
- `posts/*.md`: 文章正文
- `data/embeddings.json`: RAG 向量存储
- `data/ozon_raw/`: Ozon 原始数据存档
- `scripts/ozon_config.json`: Ozon 选品配置
- `sitemap.xml`: 生成 sitemap
- `.env.example`: 环境变量模板

## Commands

```bash
# 生成
python -m textscripts generate                    # 全板块
python -m textscripts generate --section cb       # 仅跨境
python -m textscripts generate --section ozon     # 仅Ozon选品
python -m textscripts generate --section ozon --dry-run

# 发布 (dry-run 默认不写文件)
python -m textscripts publish --push              # 质量门禁 + git push
python -m textscripts publish --push --force      # 跳过质量门禁

# RAG
python -m textscripts rag rebuild                 # 重建向量索引

# 开发
python -m http.server 8080
git status --short
git diff --stat
```

## Token Rules

- Search first with `rg`; read only the files needed for the task.
- For frontend issues, inspect `index.html`, `assets/css/main.css`, and relevant `assets/js/` files.
- For content generation issues, inspect only relevant files in `scripts/`.
- Do not bulk-read `posts/*.md`. Use `posts/posts.json` unless the task names a specific article.
- Do not read `.env`, logs, caches, or generated history unless the user explicitly asks.
- For changes touching 3 or more files, give a short 3-5 step plan before editing.
- Suggest `/compact` after exploration, after a milestone, and before switching topics.

## Current Handoff

- Keep the current optimization direction; do not roll back the frontend or Python split unless the user asks.
- Frontend modules in `assets/js/` passed `node --check`.
- Python validation is blocked until real Python is installed or enabled; Windows Store stubs are currently first on PATH.
- `auto_daily.log` is tracked but now ignored for future changes; avoid committing log churn.
- Before any `--push`, run Python dry-runs first once Python works.

## RAG 模块

- 向量存储: `data/embeddings.json` (纯 JSON, 零新依赖)
- Embedding: DashScope `text-embedding-v1` API, 失败自动降级到 256d 关键词向量
- 去重阈值: 余弦相似度 ≥ 0.85 判为重复
- 索引: `build_index()` 增量, `rebuild_index()` 全量重建
- 前端搜索: MiniSearch (fuzzy=0.2, 标题 boost=3x)

## Development Rules

- Keep the static-site structure. Do not add a build tool unless requested.
- Reuse existing CSS variables and component patterns.
- Preserve article index fields: `slug`, `title`, `date`, `excerpt`, `cat`, `sub`, `source`, `source_name`, `lastmod`.
- Generated content must keep real source links and media names.
- Never expose real API keys, tokens, cookies, or account data.
- All new generators inherit from `BaseGenerator` (collect → enrich → compose → validate).
- Quality gate (`quality_gate.py`) runs before publishing. `--force` to bypass.
- RAG dedup checks run before generating if embedding API is available.

## Verify

- Frontend: open `index.html` or run `python -m http.server 8080`.
- Scripts: run without `--push` first.
- Before release: check `git status --short` and `git diff --stat`.
