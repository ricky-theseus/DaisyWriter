---
name: csdn-upload
description: 通过 Playwright + 直连 API（X-Ca HMAC-SHA256 签名）将本地博文批量上传到 CSDN 草稿箱。三态管理：未上传 → 草稿箱 → 已发布。
allowed-tools: Read Write Grep Bash Agent
argument-hint: "[--login | --dry-run | --sync | --retry-failed | --no-confirm]"
---

# CSDN 草稿批量上传

## 三态管理

| 状态 | 含义 | 判定依据 |
|------|------|----------|
| **未上传** | 本地有草稿，未上传到 CSDN | 不在 `csdn_article_map.json`，不在已发表集合 |
| **草稿箱** | 已上传到 CSDN 但未发布 | `csdn_article_map.json` 中 `status: "draft"` |
| **已发布** | 已在 CSDN 公开发布 | `published.json` 中有记录，或在 `已发表/` 目录 |

数据流向：

```
未上传 ──upload──→ 草稿箱 ──manual publish──→ 已发布
                       │
                       └──sync──→ csdn_article_map.json (status→published)
```

## 使用

### 首次登录

```bash
python scripts/playwright_uploader.py --login
```

弹出浏览器 → 手动登录 CSDN → 在编辑器页面出现后关闭浏览器 → 登录态保存到 `chrome_profile/`。

### 查看状态

```bash
python scripts/playwright_uploader.py --dry-run
```

列出所有草稿的三态分布，不下发任何请求。

### 上传到草稿箱

```bash
python scripts/playwright_uploader.py
python scripts/playwright_uploader.py --no-confirm   # 跳过确认
python scripts/playwright_uploader.py --retry-failed  # 只重试上次失败的
```

使用直连 API（非 UI 操作），自动重试频率限制。

### 同步已发布状态

```bash
python scripts/playwright_uploader.py --sync
```

对比 `published.json` / `已发表/` 目录，将 `csdn_article_map.json` 中对应文章从 `draft` 标记为 `published`。

## 命令参考

| 命令 | 作用 |
|------|------|
| `--login` | 首次登录，保存浏览器状态 |
| `--dry-run` | 预览三态分布，不操作 |
| `--sync` | 同步已发表状态到映射文件 |
| `--retry-failed` | 只重试上次失败的未上传文章 |
| `--no-confirm` | 跳过确认提示直接上传 |

## 工作原理

### 架构

```
Python 脚本 ──Playwright──→ 浏览器（提供 Cookie 环境）
                │
                ├── page.evaluate(JS) 注入 HMAC 签名计算
                └── fetch() → POST bizapi.csdn.net/saveArticle
```

不使用 UI 操作（CSDN 的 Vue 3 contenteditable 编辑器不稳定且不触发 saveArticle API）。

### X-Ca 签名算法

CSDN 的 bizapi 使用阿里云 API 网关风格的四层签名：

| 参数 | 值 |
|------|-----|
| `X-Ca-Key` | `203803574` |
| `X-Ca-Secret` | `9znpamsyl2c7cdrr9sas0le9vbc3r6ba` |
| `X-Ca-Nonce` | 每次请求新生成的 UUID v4 |
| `X-Ca-Signature-Headers` | `x-ca-key,x-ca-nonce` |

签名字符串格式（HMAC-SHA256 → Base64）：

```
POST\n
*/*\n
\n
application/json\n
\n
x-ca-key:{key}\n
x-ca-nonce:{nonce}\n
/path
```

签名在浏览器内用 `crypto.subtle.sign('HMAC', ...)` 计算，避免 Python 端逆向兼容问题。

### 频率限制

- 每次 POST 后至少等待 **10 秒**
- 触发频率限制后重试，退避策略：10s → 20s → 失败（最多 3 次）
- 连续多发容易触发 CSDN 的"请求太过频繁"防护

## 输入源

- 递归搜索 `博文/**/草稿/*.md`
- 每篇博文要求（技术博文规范）：
  - 最低 800 中文字符（不含代码块/Mermaid）
  - 含 Mermaid 图
  - 标题、分类、标签等元信息上传时由脚本构造

## 状态存储

三态不依赖数据库，由两个 JSON 文件协同完成：

### `csdn_article_map.json` — 上传台账（本 skill 维护）

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `int` | 结构版本号，当前 `1` |
| `articles` | `object` | key = 相对路径（`博文/.../草稿/xxx.md`），value = 文章记录 |
| `updated_at` | `string` | ISO 时间戳，最近一次写入时间 |

每篇文章记录：

```json
{
  "id": 162305841,
  "url": "https://blog.csdn.net/.../162305841",
  "title": "文章标题",
  "uploaded_at": "2026-06-25T14:24:40.180430",
  "status": "draft",
  "published_at": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` | CSDN 分配的 article id |
| `url` | `string` | CSDN 文章链接 |
| `title` | `string` | 上传时的标题 |
| `uploaded_at` | `string` | ISO 时间戳，上传时间 |
| `status` | `enum` | `"draft"` \| `"published"` |
| `published_at` | `string?` | 标记为已发布的时间（`--sync` 写入） |

**谁写**：`upload_articles()` 在成功 POST 后写入，`sync_published()` 在 `--sync` 时更新 status。

**谁读**：`classify()` 读取来判断"草稿箱"，`sync_published()` 读取来比对已发表。

**生命周期**：首次上传时创建，随每次上传/同步自动更新。不移除记录（保留审计线索）。

### `published.json` — 已发表台账（外部系统维护，本 skill 只读）

路径：`D:/Writer/.author/published.json`

由项目级发布流程维护，本 skill 只读不写。结构示例：

| 字段 | 类型 | 说明 |
|------|------|------|
| `works` | `array` | 长篇作品（小说等）的已发表章节 |
| `tech_articles` | `array` | 技术博文已发表记录 |
| `agent_articles` | `array` | AI Agent 专题已发表记录 |

每篇记录包含 `title` 字段，本 skill 提取 `title` 的 lowercase 值做字符串匹配，判断文章是否已发布。

**谁写**：外部发布流程（非本 skill）。

**谁读**：`get_published_titles()` 读取，供 `classify()` 判断"已发布"。

### 状态判定逻辑

```
classify(draft):
    1. title.lower() in published.json.titles  → "已发布"
    2. rel_path in csdn_article_map.json       → "草稿箱"
    3. 否则                                      → "未上传"
```

`sync_published()` 额外步骤：扫描 `博文/**/已发表/*.md` 文件头提取 title，与 `published.json` 互补覆盖。

### `.upload_failed.json` — 失败重试缓存（临时）

只在 `--retry-failed` 场景使用。每次上传批次结束后，将失败文章的相对路径写入此文件，供下次 `--retry-failed` 读取。

| 字段 | 类型 | 说明 |
|------|------|------|
| `failed` | `array[string]` | 失败文章的相对路径列表 |
| `updated_at` | `string` | ISO 时间戳 |

不长期保留，成功重试后自然不再使用。

## 文件

```
csdn-upload/
├── SKILL.md                            # 本文件
├── scripts/
│   └── playwright_uploader.py          # 唯一脚本：登录 + 上传 + 同步
├── chrome_profile/                      # Chromium 持久化用户数据（登录态）
├── csdn_article_map.json               # 上传台账（自动生成，追踪三态）
└── .upload_failed.json                 # 失败重试缓存（自动生成，--retry-failed 使用）
```

## 注意事项

- **登录过期**：CSDN 登录态数天后失效，重新 `--login`
- **只存草稿不发布**：`pubStatus: "draft"`，不会触发发布
- **图片暂不支持**：不会自动上传博文中的图片
- **API key/secret**：硬编码在脚本中。如果 CSDN 更换密钥需要重新分析 app 入口 chunk
