---
name: csdn-upload
description: 通过 Playwright 浏览器自动化将本地博文上传到 CSDN 草稿箱。三态管理：未上传 → 草稿箱 → 已发布。
allowed-tools: Read Write Grep Bash Agent
argument-hint: "[--login | --dry-run | --sync | --no-confirm]"
---

# CSDN 草稿批量上传

Playwright 浏览器自动化。**只存草稿不发布。** 登录一次，后续全自动。

## 三态管理

| 状态 | 含义 | 判定依据 |
|------|------|----------|
| **未上传** | 本地有草稿，未上传到 CSDN | 不在 `published.json`，不在 `csdn_article_map.json` |
| **草稿箱** | 已上传到 CSDN 草稿箱但未发布 | `csdn_article_map.json` 中 `status: "draft"` |
| **已发布** | 已在 CSDN 公开发布 | `published.json` 中有记录，或在 `已发表/` 目录 |

数据流向：

```
未上传  ──upload──→  草稿箱  ──manual publish──→  已发布
                        │
                        └──sync──→  csdn_article_map.json 标记为 published
```

## 使用

### 1. 首次登录

```bash
python scripts/playwright_uploader.py --login
```

弹出浏览器 → 手动登录 CSDN → 在终端按 Enter → 登录状态自动保存。

### 2. 查看状态

```bash
python scripts/playwright_uploader.py --dry-run
```

列出所有本地草稿的三态分布。

### 3. 上传到草稿箱

```bash
python scripts/playwright_uploader.py
```

逐个打开编辑器 → 填内容 → 点保存草稿 → 记录到 `csdn_article_map.json`。

加 `--no-confirm` 跳过确认。

### 4. 同步发布状态

```bash
python scripts/playwright_uploader.py --sync
```

把 `csdn_article_map.json` 中已发布文章的 `status` 从 `draft` 标记为 `published`。

## 命令参考

| 命令 | 作用 |
|------|------|
| `--login` | 首次登录，保存浏览器状态 |
| `--dry-run` | 预览三态分布，不操作 |
| `--sync` | 同步已发表状态到映射文件 |
| `--no-confirm` | 跳过确认提示直接上传 |

## 目录结构

```
csdn-upload/
├── SKILL.md
├── scripts/
│   └── playwright_uploader.py     # 唯一脚本
├── csdn_playwright_state.json     # 浏览器登录状态（--login 生成）
└── csdn_article_map.json          # 上传记录（自动生成，追踪三态）
```

## 注意事项

- **登录过期**：登录状态数天后失效，重新 `--login`
- **只存草稿**：不会点"发布文章"，只点"保存草稿"
- **限流保护**：每篇间隔 10 秒
- **图片**：不支持自动上传图片
