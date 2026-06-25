---
name: daisywriter
description: "DaisyWriter — AI-powered writing toolkit / AI 驱动写作工具包"
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion
argument-hint: "[skill-name | setup]"
---

# DaisyWriter for OpenCode

OpenCode 原生支持 SKILL.md 格式，DaisyWriter 的所有技能可直接使用。

## 安装

在 `opencode.json` 中添加：

```json
{
  "skills": ["path/to/DaisyWriter"]
}
```

## 使用

```python
# 加载单个技能
skill("skills/webnovel/write")

# 或使用命令
# /webnovel-write 1
```

## 技能索引

所有技能位于 `../../skills/` 目录，按领域分组：

| 命令 | 技能路径 | 说明 |
|------|----------|------|
| `/webnovel-init` | `../../skills/webnovel/init/` | 网文立项 |
| `/webnovel-write` | `../../skills/webnovel/write/` | 网文写章 |
| `/shortstory-write` | `../../skills/shortstory/write/` | 短篇写章 |
| `/tech-write` | `../../skills/tech/write/` | 技术博文 |
| `/fanqie-publish` | `../../skills/fanqie/` | 番茄发布 |
| `/cover-maker` | `../../skills/cover-maker/` | 封面生成 |

## 平台配置

DaisyWriter 需要以下工具执行脚本：

```bash
# Python（工艺扫描等）
python --version  # ≥ 3.8

# Node.js（番茄发布、封面生成）
node --version    # ≥ 18
```