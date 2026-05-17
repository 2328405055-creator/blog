# Shopify 后台启用 Google Analytics 4 教程

> 📂 分类: 选品技巧
> 📅 采集日期: 2026-05-17
> 📰 来源: **Shopify**（shopify.com）

---

## 一、GA4 账户创建与媒体资源配置  
登录 [Google Analytics 官网](https://analytics.google.com/analytics/web/provision/#/provision)，使用谷歌邮箱注册账户。进入「管理」→「媒体资源」→「创建媒体资源」，选择「网站」类型，填写店铺域名（如 `yourstore.myshopify.com`）、国家/地区（选俄罗斯或中国均可），勾选「我同意数据共享设置」。系统自动生成 GA4 媒体资源ID（格式为 `G-XXXXXXXXXX`）和全局网站代码（gtag.js）。**关键指标**：确保「数据流」中显示「Web 数据流」状态为「已启用」，且「测量ID」字段可见。

## 二、Shopify 后台代码嵌入实操步骤  
1. 进入 Shopify 后台 →「在线商店」→「主题」→「操作」→「编辑代码」；  
2. 在左侧文件列表中打开 `theme.liquid`，定位到 `<head>` 标签内（通常在第3–5行）；  
3. 将 GA4 的 gtag.js 代码（含 `gtag('config', 'G-XXXXXXXXXX');`）完整粘贴至 `<head>` 内顶部位置；  
4. **强制验证**：在「设置」→「支付」→「添加自定义脚本」中，再次粘贴同一段代码（用于捕获结账页事件，避免漏掉关键转化数据）；  
5. 点击「保存」，立即访问店铺首页、商品页、购物车页各3次，等待10分钟。  

## 三、数据校验与基础监控设置  
登录 GA4 后台 →「实时报告」，查看是否出现「活跃用户」（需显示 ≥1人）；若无数据，检查浏览器是否开启广告拦截插件（如 uBlock Origin），临时关闭后重试。进入「配置」→「事件」，确认已自动捕获 `page_view`、`view_item`、`add_to_cart`、`purchase` 四类核心事件。**新手必设指标**：在「探索」模块新建「漏斗分析」，路径设为「首页→商品页→加购→下单→支付成功」，观察各环节流失率（健康值：加购率＞15%，支付完成率＞65%）。

## 四、新手三大致命错误及规避方案  
**错误1：仅粘贴代码未验证结账页追踪**  
→ 后果：90%以上订单数据丢失。**解法**：必须在「设置→支付→添加自定义脚本」二次部署代码，且在 GA4 中进入「调试视图」（需安装 Google Tag Assistant Chrome 插件）验证 `purchase` 事件触发。  
**错误2：混淆 UA 与 GA4 代码混用**  
→ 后果：数据重复或冲突。**解法**：彻底删除旧版 Universal Analytics 的 `UA-XXXXX-X` 代码，GA4 不兼容 UA 代码段。  
**错误3：未启用增强型衡量**  
→ 后果：视频播放、文件下载、滚动深度等行为数据全量缺失。**解法**：在 GA4「数据流」→「Web 数据流」→「增强型衡量」中，手动开启「滚动」、「视频开始」、「文件下载」、「出站点击」全部开关。

## 今日行动建议  
用5分钟完成三件事：① 打开 Google Analytics 官网注册新账户并创建 GA4 媒体资源；② 登录 Shopify 后台，在 `theme.liquid` 的 `<head>` 内粘贴生成的 gtag.js 代码；③ 访问自己店铺的任意3个页面，随后打开 GA4 实时报告，截图确认「活跃用户数」是否实时更新。完成后，将截图发至团队群内打卡——数据追踪，今天就启动。

## 核心要点

- 一、GA4 账户创建与媒体资源配置  
- 二、Shopify 后台代码嵌入实操步骤  
- 三、数据校验与基础监控设置  
- 四、新手三大致命错误及规避方案  
- 今日行动建议  

---

## 查看原文

📎 **原文链接:** [点击查看原文](https://news.google.com/rss/articles/CBMibkFVX3lxTE8yUUNfcEx2Y0N5Sl9GYmo1dnRXc1V2dWljQkpRd2cxd3NxbE52TlBibnkxVVBxS2w5Y3EyOGd0WkZQaHMzU2V4NVZHc0JtWFlWSzdDSzdwQkt6R2Q3MVdUdndGNC1aY1lYRS1JeFNR?oc=5)
🔍 **站内搜索:** [在 Shopify 站内搜索本文](https://www.google.com/search?q=Shopify%20%E5%90%8E%E5%8F%B0%E5%90%AF%E7%94%A8%20Google%20Analytics%204%20%E6%95%99%E7%A8%8B+site:shopify.com)

> 📚 本文内容来自 **Shopify**，版权归原来源所有。
