# Midjourney提示词编写指南

> 🤖 分类: AI教程
> 📅 采集日期: 2026-05-14
> 📰 来源: **Shopify**

---

## 什么是Midjourney？核心运行机制与入门准备  
Midjourney是一款基于Discord平台运行的AI图像生成工具，采用扩散模型技术，通过文本提示（Prompt）生成高质量数字图像。使用前需完成三步：① 注册免费Discord账号；② 访问[midjourney.com](https://www.midjourney.com/home)并订阅（基础版$10/月）；③ 在Discord中加入Midjourney官方服务器或私聊@Midjourney Bot。所有指令必须以`/imagine`开头，且单次输入上限约60个单词。关键注意：Midjourney不支持中文提示词解析，**所有描述必须使用英文**（如“ultra-realistic”“cinematic lighting”），但参数（如`--ar 16:9`）可直接使用。

## 提示词四段式结构：命令+参考+描述+参数  
标准提示词严格遵循四部分逻辑：  
1. **命令**：固定以`/imagine`起始；  
2. **参考图像（可选）**：粘贴公开可访问的图片URL（如Imgur链接），用于风格/色调锚定；  
3. **图像描述**：用英文短语组合，按「主体→动作→环境→氛围→细节」顺序展开，例：`a cyberpunk guitarist playing underwater, neon-lit bubbles, zero-gravity hair, frost on guitar body, cinematic depth of field`；  
4. **参数**：置于末尾，用空格分隔，常用参数包括：  
　　• `--ar 4:3`（宽高比，电商主图推荐4:3或1:1）  
　　• `--s 750`（风格化强度，0-1000，默认100，值越高越艺术化）  
　　• `--v 6.0`（指定模型版本，当前主流为v6）  
　　• `--style raw`（关闭默认美化，适合产品写实渲染）  

## 权重控制与高级技巧：让关键元素精准呈现  
当图像偏离预期时，用双冒号`::`实现元素权重分配。语法为`关键词::权重值`，默认权重为1。例如生成“水下电吉他”时若吉他尺寸过小，可写：  
`underwater electric guitar::3 floating ice crystals::1 bioluminescent fish::2 --ar 16:9 --s 600`  
→ 此处吉他权重设为3，显著提升其在构图中的占比。另一技巧是**拆分歧义词**：输入`sandbox`易被理解为儿童游乐场，改写为`sand::box::`后，模型将分别解析“沙子”和“盒子”，生成沙滩上散落多个纸盒的场景，大幅提升可控性。

## 电商实战参数配置与效率提升点  
针对不同场景优化参数组合：  
- **广告主图**：用`--style raw --s 200 --ar 1:1`获得高精度产品细节，省去修图师精修时间；  
- **社交媒体竖版图**：`--ar 9:16 --chaos 30`（`--c 30`）增强构图多样性，批量生成10张供A/B测试；  
- **样机展示**：添加`photorealistic product mockup, studio lighting, white background`描述，并启用`--v 6.0`确保材质反射真实；  
- **品牌情绪板**：用`--weird 500`激发创意联想，快速产出色彩系统、图形纹理等设计灵感源。  
实测显示，熟练运用参数可将单图迭代次数从平均8次降至2次内，节省75%视觉生产时间。

## 今日动手实践  
请在Discord中向Midjourney Bot发送以下完整指令（复制粘贴即可）：  
`/imagine a portable electric guitar submerged in Arctic ocean, glowing blue circuitry, ice crystals on strings, dramatic underwater light rays, ultra-detailed product shot, studio lighting, white background --ar 4:3 --s 300 --style raw --v 6.0`  
生成后观察：① 吉他是否占据画面中心？② 冰晶与电路发光效果是否清晰？③ 背景是否纯净无干扰？记录结果，下次尝试将`guitar::3`调整权重验证控制效果。

---

## 查看原文

📎 **原文链接:** [点击查看原文](https://news.google.com/rss/articles/CBMiZEFVX3lxTFBBUlRxYU9GQlIyQUF3aUhtczNqSmVsZWhvRHNRemMxWHFuQU9POWF1QkpvOUpBYnk3NTlETmVaVUY3WmNmTDdaREVCYTIzSzczQTZHOXFEczc0NnhNS29ScHgwdTA?oc=5)
🔍 **站内搜索:** [在 Shopify 站内搜索](https://www.google.com/search?q=Midjourney%E6%8F%90%E7%A4%BA%E8%AF%8D%E7%BC%96%E5%86%99%E6%8C%87%E5%8D%97+site:shopify.com)

> 📚 本文内容来自 **Shopify**，版权归原来源所有。
