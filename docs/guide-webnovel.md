# Web Novel Writing Guide 📚

Complete walkthrough of the 12 web novel skills in DaisyWriter.

---

## Overview

```
Reference Novel          New Novel
     │                       │
     ▼                       ▼
deconstruct ───┐         init
               │           │
               └──► ideas  │
                           ▼
                         plan
                           │
                           ▼
                    ┌── write ──┐
                    │           │
                    ▼           ▼
                  batch      review
                    │           │
                    └──► review ◄┘
                           │
                           ▼
                        publish
```

---

## Skill 1: Deconstruct (`webnovel-deconstruct`)

Analyze a reference novel to extract patterns.

```
/webnovel-deconstruct 盗墓笔记
```

**Output:**
```
参考书/盗墓笔记/
├── 盗墓笔记.txt                  # Original text
├── 盗墓笔记-拆书报告.md          # Analysis report
├── 盗墓笔记-拆书数据.json        # Structured data
├── 盗墓笔记-情绪曲线.md          # Emotion curve
└── 盗墓笔记-节奏统计.md          # Pacing statistics
```

**Use the report to:**
- Identify hook placement patterns
- Understand chapter-level pacing
- Extract payoff structures you can borrow

---

## Skill 2: Init (`webnovel-init`)

Create a new novel project with structured worldbuilding.

```
/webnovel-init "诡异熔炉"
```

The skill runs a phased interview:

| Phase | Collects | Gate |
|-------|----------|------|
| Inspiration | Idea bank, reference novels | At least 1 idea |
| Story core | Genre, title, hook, target length | Book title + genre |
| Character | Protagonist, supporting cast | Protagonist with desire & flaw |
| Golden finger | Power system type, limitations | Type determined |
| World rules | Setting, factions, history | World scale |
| Constraints | Creative boundaries, anti-tropes | Naming rules |

**Sufficiency gates** prevent generation until essential info is collected — no half-baked projects.

---

## Skill 3: Plan (`webnovel-plan`)

Generate volume outlines and chapter plans.

```
/webnovel-plan 1
```

**10-step pipeline:**
1. Load project state
2. Backfill settings from existing files
3. Select target volume
4. Generate beat sheet (volume-level pacing)
5. Generate timeline (in-story chronology)
6. Build volume skeleton
7. Batch chapter outlines (8-12 per batch)
8. Write back new settings to files
9. Verify completeness
10. Refresh story system contracts

**Per-chapter outline includes:**
- CBN (Critical Beat Nodes — must-haves)
- CPN (optional nodes)
- CEN (Chapter End State)
- Time anchor
- Hook to next chapter
- Forbidden content

---

## Skill 4: Write (`webnovel-write`)

Single chapter production with quality gates.

```
/webnovel-write 5
```

**Three modes:**

| Mode | Pipeline | When to use |
|------|----------|-------------|
| Default | Full 6-step: preflight → context → draft → scan → review → polish | Normal chapters |
| `--fast` | Lightweight review (skip full blind review) | Filler/transition chapters |
| `--minimal` | No review, minimal polish | First draft / brainstorming |

**Prose quality gates (enforced by prose_scanner.py):**

| Metric | Standard | Blocking |
|--------|----------|----------|
| Avg sentence length | 30-55 chars | <25 or >55 |
| Very short sentences | ≤15% | >15% |
| Long sentences | ≥30% | — |
| Emotion label words | 0 | >0 |

---

## Skill 5: Batch (`webnovel-batch`)

Batch-write chapters with checkpoint resume.

```
/webnovel-batch 5 50
```

**Architecture:**
```
Main dialog
  │
  ├── Writer agent (chapter N) → reviews itself → passes
  ├── Reviewer agent (chapter N, blind) → passes
  ├── Save checkpoint
  ├── Writer agent (chapter N+1) → ...
  └── ...
```

- Progress persisted in `stream_progress.json`
- Resume after crash: `/webnovel-batch 18 50`
- Each chapter gets a fresh writer agent (no context bleed)

---

## Skill 6: Craft (`webnovel-craft`)

Quantitative prose quality constraints.

This is a **supporting skill** — loaded automatically by `webnovel-write` and `webnovel-review`. You rarely invoke it directly:

```
python skills/webnovel/craft/scripts/prose_scanner.py "正文/第0005章-觉醒.md"
```

Returns JSON with blocking/non-blocking issues.

---

## Skill 7: Review (`webnovel-review`)

Blind chapter quality review.

```
/webnovel-review 5
```

**Reviewer receives:**
- Chapter outline (CBN/CEN)
- Previous chapter summary
- Full chapter text
- Craft constraints reference

**Reviews three questions:**
1. Are all CBNs present? Are all CENs achieved?
2. Does the chapter have at least one emotional beat?
3. Are there prose quality issues?

**Outcomes:**
- All pass → chapter is marked passed
- Blocking issues → user decides: fix now, save report, or abort

---

## Skill 8: Review Settings (`webnovel-review-settings`)

Audit worldview consistency.

```
/webnovel-review-settings
/webnovel-review-settings --quick      # Blocking + high only
/webnovel-review-settings --scope power # Single dimension
```

**Severity levels:**
- 🔴 **Blocking** — logic contradiction that kills writing
- 🟠 **High** — obvious loophole
- 🟡 **Medium** — potential edge-case隐患
- 🟢 **Low** — polish suggestion

---

## Skill 9: Query (`webnovel-query`)

Retrieve information from project state.

```
/webnovel-query 主角
/webnovel-query 伏笔
/webnovel-query 力量体系
```

Reads from:
- `.webnovel/state.json`
- `.story-system/MASTER_SETTING.json`
- Setting files in `设定集/`
- RAG (WordPress-based knowledge base, if configured)

---

## Skill 10: Learn (`webnovel-learn`)

Extract successful writing patterns to project memory.

```
/webnovel-learn 本章的悬念设计很有层次感
```

Appends to `.webnovel/project_memory.json` with pattern type classification:
- hook, pacing, dialogue, payoff, emotion, format, other

**Skips duplicates automatically.**

---

## Skill 11: Doctor (`webnovel-doctor`)

Read-only health check for novel projects.

```
/webnovel-doctor
/webnovel-doctor --chapter 5
/webnovel-doctor --deep
```

Checks:
- Directory structure integrity
- File existence and completeness
- JSON/SQLite state validity
- RAG configuration
- Dashboard build artifacts

---

## Skill 12: Dashboard (`webnovel-dashboard`)

Launch a read-only web UI for project visualization.

```
/webnovel-dashboard
/webnovel-dashboard --port 8080
```

Features:
- Project overview (word counts, chapter status)
- Entity graph (characters, factions, locations)
- Chapter content viewer
- Reading power data