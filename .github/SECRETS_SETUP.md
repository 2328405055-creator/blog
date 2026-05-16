# GitHub Secrets 配置指南

在 GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret

---

## 必填 Secrets (3 个)

| Secret 名称 | 说明 | 示例值 |
|-------------|------|--------|
| `BLOG_FIRECRAWL_API_KEY` | Firecrawl 网页抓取 API Key | `fc-xxxxxxxxxxxxxxxx` |
| `BLOG_PRIMARY_API_KEY` | 千问 (DashScope) API Key | `sk-xxxxxxxxxxxxxxxx` |
| `BLOG_PRIMARY_API_BASE` | 千问 API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

## 可选 Secrets (9 个)

| Secret 名称 | 默认值 | 说明 |
|-------------|--------|------|
| `BLOG_PRIMARY_MODEL` | `qwen-plus` | 主 AI 模型名 |
| `BLOG_BACKUP_API_KEY` | (空) | DeepSeek API Key (主模型失败时自动切换) |
| `BLOG_BACKUP_API_BASE` | `https://api.deepseek.com` | DeepSeek API 地址 |
| `BLOG_BACKUP_MODEL` | `deepseek-chat` | 备用 AI 模型名 |
| `BLOG_ENRICH_ENABLED` | `true` | 是否启用内容富化 (Firecrawl + AI总结) |
| `BLOG_TARGET_WORDS` | `700` | AI 总结目标字数 |
| `BLOG_SCRAPE_TIMEOUT` | `30` | Firecrawl 抓取超时 (秒) |
| `BLOG_EMBEDDING_API_BASE` | 同 PRIMARY_API_BASE | RAG Embedding API 地址 |
| `BLOG_EMBEDDING_MODEL` | `text-embedding-v1` | RAG Embedding 模型 |
| `GH_PAT` | (空) | GitHub Personal Access Token (用于 git push，可选) |

## 快速配置命令

在 GitHub 仓库的 Settings 中逐一添加，或使用 `gh` CLI：

```bash
# 必填
gh secret set BLOG_FIRECRAWL_API_KEY -b "fc-xxx"
gh secret set BLOG_PRIMARY_API_KEY -b "sk-xxx"
gh secret set BLOG_PRIMARY_API_BASE -b "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 推荐设置
gh secret set BLOG_BACKUP_API_KEY -b "sk-xxx"
gh secret set BLOG_BACKUP_API_BASE -b "https://api.deepseek.com"
```

## 验证配置

1. 在 Actions 页面手动触发 `Daily Blog Content Generator`
2. 选择 `section: all`，勾选 `skip_push: true` (先测试不推送)
3. 确认日志中无 `secret not found` 错误

## 安全提醒

- 仓库 `.env` 文件已在 `.gitignore` 中
- 这些 Secrets 只存在于 GitHub 加密存储，不会出现在 Actions 日志中
- 如果 API Key 泄露，立即在 DashScope/DeepSeek/Firecrawl 后台轮换
