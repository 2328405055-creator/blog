# CLAUDE.md

Project guide for Claude Code. Keep context small and avoid reading unrelated generated content.

## Project

- Site: `20020426.top`
- Repo: `2328405055-creator/blog`
- Hosting: GitHub Pages static site
- Stack: plain HTML/CSS/JS plus Python generation scripts
- Topics: cross-border ecommerce, Ozon/Yandex/Wildberries, home fitness, AI learning

## Key Files

- `index.html`: main page
- `assets/css/main.css`: global styles
- `assets/js/*.js`: frontend modules
- `posts/posts.json`: article index and list data source
- `posts/*.md`: article bodies
- `scripts/daily_generator.py`: daily article generator
- `scripts/ozon_selector.py`: Ozon product selection generator
- `sitemap.xml`: generated sitemap
- `.env.example`: env template; never read or commit `.env`

## Commands

```bash
python scripts/daily_generator.py
python scripts/daily_generator.py --push
python scripts/ozon_selector.py --dry-run
python scripts/ozon_selector.py --push
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

## Development Rules

- Keep the static-site structure. Do not add a build tool unless requested.
- Reuse existing CSS variables and component patterns.
- Preserve article index fields: `slug`, `title`, `date`, `excerpt`, `cat`, `sub`, `source`, `source_name`, `lastmod`.
- Generated content must keep real source links and media names.
- Never expose real API keys, tokens, cookies, or account data.

## Verify

- Frontend: open `index.html` or run `python -m http.server 8080`.
- Scripts: run without `--push` first.
- Before release: check `git status --short` and `git diff --stat`.
