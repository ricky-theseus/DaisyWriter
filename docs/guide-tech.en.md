# Technical Blogging Guide 💻

Write, batch, and auto-publish technical articles.

---

## Overview

```
tech-deconstruct (参考) → tech-write (起草) → tech-batch (批量) → CSDN
                                                                    │
                                                            sync-csdn / csdn-upload
```

---

## Skill 1: Write (`tech-write`)

Structured technical blog writing.

```
/tech-write "用 FastAPI 构建 REST API"
```

**Standard structure:**
1. **Problem** — What issue does this solve?
2. **Solution** — Step-by-step implementation
3. **Code** — Copy-paste-runnable snippets
4. **Verification** — How to test it works
5. **Summary** — Key takeaways

**Review checklist:**
- All code snippets are copy-paste-runnable
- Version numbers and API refs are explicit
- Logic chain is complete (no skipped steps)
- No blank placeholders
- Word count matches target audience

**Output:** `博文/{一级}/{二级}/{三级}/{文章}.md`

---

## Skill 2: Deconstruct (`tech-deconstruct`)

Analyze reference articles for structure patterns.

```
/tech-deconstruct "参考文章路径"
```

**Analysis dimensions:**
- Structure skeleton
- Opening hook technique
- Code quality and examples
- Information density
- Logic chain completeness
- Reader match assessment
- Borrowable patterns

---

## Skill 3: Batch (`tech-batch`)

Batch-produce multiple articles under a topic.

```
/tech-batch 项目目录
```

**Two-loop architecture:**
- **Outer loop**: Schedule items from project plan
- **Inner loop**: Produce → Review → Revise → Re-review (until zero issues)

**Rules:**
- Producer and reviewer are always separate agents
- Reviewer is always blind (no conversation history)
- No retry limit — iterate until zero blocking

---

## Skill 4: Sync CSDN (`sync-csdn`)

Sync published CSDN articles to local repo.

```
/sync-csdn
```

**Pipeline:**
1. Fetch CSDN homepage
2. Compare with local `published.json`
3. Move matched drafts to `已发表/`
4. Update record

---

## Skill 5: Upload CSDN (`csdn-upload`)

Browser-automated upload drafts to CSDN.

```
/csdn-upload --dry-run      # Preview three-state distribution
/csdn-upload                # Upload all unpublished drafts
/csdn-upload --login        # First-time login (save browser state)
/csdn-upload --sync         # Sync publish status
```

**Three-state management:**

| State | Meaning |
|-------|---------|
| 📝 **Unpublished** | Local draft, not uploaded |
| 📤 **Draft box** | Uploaded to CSDN drafts, not published |
| ✅ **Published** | Public on CSDN |

**Safety:** Only saves drafts — never auto-publishes.