# Short Story Writing Guide 📝

Write Zhihu Yanxuan-style short stories with blind review quality gates.

---

## Overview

```
选题 → init (设定+盲审) → write (滚动写) → review → 定稿
                                  ↑
                            validate_chapter.py
                              字数门禁
```

---

## Skill 1: Init (`shortstory-init`)

Initialize a short story project with state-machine-driven quality.

```
/shortstory-init 3 悬疑
```

Creates 3 suspense story projects with:

| File | Purpose |
|------|---------|
| `作品信息.md` | Title, tagline, tags, summary |
| `设定.md` | World, rules, timeline (≥200 chars) |
| `角色.md` | Character profiles + ASCII relationship map |
| `章节规划.md` | Chapters with hooks, payoffs, foreshadowing table |
| `工艺约束.md` | Craft constraints specific to this piece |
| `正文.md` | Empty placeholder |

**State machine:**

```
drafting ──file check──→ in_review ──zero blocking──→ passed
    ↑                       │
    └── fix issues ←── blocking
```

After init passes, the project is ready for `shortstory-write`.

---

## Skill 2: Write (`shortstory-write`)

Rolling write with word-count gate.

```bash
python skills/shortstory/write/start.py 短篇/悬疑/白骨墙/
```

**Process:**
1. Write a chapter in `正文.md` (separated by `## 第N章：标题`)
2. Run word-count validation:
   ```bash
   python skills/shortstory/write/validate_chapter.py 短篇/悬疑/白骨墙/
   ```
3. If word count passes → submit for blind review
4. If blocking → fix and rerun
5. All chapters done → full story blind review → finalize

**Word-count gate:**
- Actual < Target → **blocked**, must add content
- Actual ≥ Target → **passed**, proceed to review

---

## Skill 3: Review (`shortstory-review`)

Stage-aware blind review for short stories.

```
/shortstory-review 短篇/悬疑/白骨墙/
/shortstory-review 短篇/悬疑/白骨墙/ --final
```

**Two modes:**

| Mode | Scope | Checks |
|------|-------|--------|
| Single-chapter | Current chapter only | CBN coverage, pacing, prose quality |
| Full-story (`--final`) | Entire piece | Structure, arc completion, twist quality |

**Review dimensions:**
1. Logical consistency
2. Character arc
3. Pacing control
4. Foreshadowing design
5. Tool-man loopholes
6. Yanxuan suitability (opening hook)

---

## Skill 4: Craft (`shortstory-craft`)

Quality constraints for short prose.

**Short story metrics:**

| Metric | Standard | Blocking |
|--------|----------|----------|
| Hook position | Within first 500 chars | >500 |
| Word count | 8,000-30,000 | Outside range |
| Avg sentence length | 25-50 chars | <20 or >55 |
| Consecutive same-subject openings | ≤2 | >2 |
| Emotion label words | 0 | >0 |

---

## Skill 5: Deconstruct (`shortstory-deconstruct`)

Extract patterns from reference stories.

```
/shortstory-deconstruct 沉默的真相
```

**Output:** `短篇/参考书/{type}/{title}/`
- `原文.md` — Original text
- `拆解报告.md` — Analysis report
- `拆解数据.json` — Structured data

**Analysis covers:** opening hook, structure skeleton, suspense design, pacing, info density, emotion curve, character building, ending quality.