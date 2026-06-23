---
name: sync-csdn
description: 检查 CSDN 博客主页最新博文，同步到本地仓库（搬文件 + 记 URL + 前/后处理钩子）
allowed-tools: Read Write Grep Bash Agent Webfetch
argument-hint: ""
---

# Sync CSDN Published Articles

对比 CSDN 博客主页最新文章列表与本地 `published.json`，发现新发表的博文自动同步。

## 流程

### Step 0：抓取 CSDN 主页
- URL: `https://blog.csdn.net/YourUsername`（替换为你的 CSDN 用户名）
- 提取每篇文章的标题 + 链接

### Step 1：对比本地记录
- 加载 `.author/published.json` 中的 `agent_articles` 和 `tech_articles` 列表
- 找出不在本地记录中的文章

### Step 2：搬文件
- 对每篇新文章，在 `博文/` 下各层级的 `草稿/` 中搜索标题匹配的 `.md`
- 匹配规则：忽略特殊符号差异（`:` vs `：`, `→` vs `到` 等），核心子串匹配
- 找到后 `Move-Item` 到对应的 `已发表/`
- 未找到本地草稿的文章，记录到 `published.json` 的 `notes` 字段标记"无本地草稿"

### Step 3：更新 published.json
- 追加到对应的 `agent_articles` / `tech_articles` 数组
- 字段：`{ title, url, published_at, status: "published" }`
- 更新 `updated_at`

### Step 4：输出摘要
- 新同步了几篇、路径、URL
- 无变化的输出"无新发表"
