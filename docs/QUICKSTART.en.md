# DaisyWriter Quick Start 🚀

Get your first web novel written in 5 minutes.

---

## 1. Install

```bash
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter
```

Configure OpenCode to find the skills:

```json
// opencode.json
{
  "skills": ["path/to/DaisyWriter"]
}
```

## 2. Initialize a Novel

In your AI coding assistant:

```
/webnovel-init "我的修仙之旅"
```

The skill will guide you through an interactive interview:
- Genre, scale, target audience
- Protagonist (desire, flaw, arc)
- World rules and power system
- Golden finger type

> **Don't worry about getting everything perfect** — the sufficiency gate ensures you provide enough info before generation.

**Expected output:**
```
❖ 项目初始化完成 ❖
📁 我的修仙之旅/
├── 设定集/           # World bible
├── 大纲/总纲.md      # Master outline
├── .webnovel/state.json
└── .story-system/    # Story contracts
```

## 3. Plan the First Volume

```
/webnovel-plan 1
```

This generates:
- Volume beat sheet (chapter-level pacing)
- Volume timeline (in-story time)
- Per-chapter outlines (CBN, CPN, CEN)

## 4. Write Chapter 1

```
/webnovel-write 1
```

The pipeline runs:
1. **Preflight** — check project state
2. **Context agent** — build writing brief (current chapter goal, previous events, unresolved threads)
3. **Draft** — write 2500-3500 words
4. **Craft scan** — run `prose_scanner.py` for quality metrics
5. **Review** — blind review agent checks for issues
6. **Polish & commit** — fix issues, save to file, record metrics

## 5. Review and Iterate

```
/webnovel-review 1
```

Blind review checks:
- CBN/CEN coverage
- Continuity with previous chapters
- Character voice consistency
- Pacing and information density

**Blocking issues** halt the workflow until you decide how to resolve them.

## 6. Write More Chapters

```
/webnovel-batch 2 30
```

Batch-write chapters 2 through 30 with:
- Serial loop: write → review → pass → next
- Checkpoint resume (crashes restart from last passed chapter)
- Progress persisted in `stream_progress.json`

---

## Next Steps

- 📖 [Web Novel Tutorial](guide-webnovel.md) — Deep dive into all 12 novel skills
- 📝 [Short Story Guide](guide-shortstory.md) — Write Zhihu Yanxuan stories
- 💻 [Tech Blog Guide](guide-tech.md) — Publish technical articles
- 🐛 [Report an issue](https://github.com/ricky-theseus/DaisyWriter/issues)