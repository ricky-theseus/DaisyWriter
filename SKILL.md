---
name: skill-writer
description: "AI-powered writing toolkit — Web novel, Short story, Technical blog, Publishing automation / AI 驱动写作工具包 — 网文、短篇、技术博文、发布自动化"
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion
argument-hint: "[skill-name] [args]"
---

# DaisyWriter — Skill Collection

Root entry point for the DaisyWriter skill collection.

## Loading Skills

```python
# Load any skill by path
skill("skills/webnovel/write")
```

Or via command:

```
/webnovel-write 1
/shortstory-write "My Story"
/fanqie-publish --preview
```

## Available Skills

### Web Novel Creation (网文创作 — `skills/webnovel/`)
- [`deconstruct`](skills/webnovel/deconstruct/) — Reference novel analysis / 拆书
- [`init`](skills/webnovel/init/) — Project initialization / 立项
- [`plan`](skills/webnovel/plan/) — Volume & chapter outlining / 规划
- [`write`](skills/webnovel/write/) — Single chapter writing / 写章
- [`batch`](skills/webnovel/batch/) — Batch chapter production / 批量写章
- [`craft`](skills/webnovel/craft/) — Prose quality constraints / 工艺约束
- [`review`](skills/webnovel/review/) — Chapter quality review / 章节审查
- [`review-settings`](skills/webnovel/review-settings/) — Setting consistency audit / 设定审查
- [`query`](skills/webnovel/query/) — Information retrieval / 信息查询
- [`learn`](skills/webnovel/learn/) — Pattern extraction / 模式学习
- [`doctor`](skills/webnovel/doctor/) — Health diagnostic / 健康检查
- [`dashboard`](skills/webnovel/dashboard/) — Web UI dashboard / 仪表盘

### Short Story (短篇创作 — `skills/shortstory/`)
- [`deconstruct`](skills/shortstory/deconstruct/) — Reference analysis / 拆书
- [`init`](skills/shortstory/init/) — Project initialization / 立项
- [`craft`](skills/shortstory/craft/) — Craft constraints / 工艺约束
- [`write`](skills/shortstory/write/) — Full writing pipeline / 写作

### Technical Blog (技术博文 — `skills/tech/`)
- [`deconstruct`](skills/tech/deconstruct/) — Article analysis / 拆解
- [`write`](skills/tech/write/) — Write blog posts / 写作
- [`batch`](skills/tech/batch/) — Batch production / 批量生产
- [`sync-csdn`](skills/tech/sync-csdn/) — Sync CSDN articles / 同步

### Publishing (发布自动化 — `skills/fanqie/`)
- [`fanqie-publish`](skills/fanqie/) — Publish to Fanqie Novel / 发布到番茄小说

## Adapters

Other AI coding assistants can load this collection via:

- **Claude Code**: [adapters/claude-code/](adapters/claude-code/)
- **Codex CLI**: [adapters/codex/](adapters/codex/)
