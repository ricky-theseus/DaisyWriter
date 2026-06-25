---
name: fanqie-publish
description: Publish novel chapters from local Markdown files to the Fanqie Novel writer backend via browser automation. Supports single/batch/scheduled publish with login state persistence.
allowed-tools: Read Write Grep Bash Agent
argument-hint: "[--preview | --login | --publish [--file ...|--dir ...|--range X-Y] [--mode scheduled] [--confirm-publish]]"
---

# Fanqie Publisher (OpenCode Edition)

Use this skill to publish **chapter title + body** from local Markdown files to the Fanqie writer backend via Playwright browser automation.

**Original project**: [amm10090/fanqie-publisher-skill](https://github.com/amm10090/fanqie-publisher-skill) — MIT license.
**This fork**: adapted from OpenClaw Skill to OpenCode project-level skill.

## Scope

This skill is for:
- uploading one chapter from a `.md` file
- batch publishing chapters from a directory
- immediate publish and scheduled publish
- saving and reusing browser login state

This skill is **not** for guessing selectors blindly. If the page changes, inspect first, then update `references/selectors.md` and `{baseDir}/scripts/publish_fanqie.js`.

## Source content

Expected source content shape:
- one `.md` file = one chapter
- filename example: `第001章_标题.md`
- first line: chapter title (e.g. `第001章 标题`)
- body starts after the heading

## Files

- `scripts/prepare_chapters.py` — parse `.md` files into normalized chapter data
- `scripts/browser_page_picker.js` — pick an existing Fanqie writer tab or open a safe fallback page
- `scripts/fanqie_login_flow.js` — shared login helpers
- `scripts/login_fanqie.js` — open browser, detect login page, capture QR code, and save login state
- `scripts/publish_fanqie.js` — publish one or more chapters with Playwright
- `scripts/state.py` — persist publish history and prevent duplicates
- `references/workflow.md` — current known backend workflow
- `references/selectors.md` — selectors and page reconnaissance notes

## Prerequisites

1. **Node.js** (18+) and **Python** (3.8+)
2. Install npm dependencies:

```bash
cd "{baseDir}"
npm install
npx playwright install chromium
```

3. **Chrome** started with remote debugging:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

4. First-time login: `node "{baseDir}/scripts/login_fanqie.js" --cdp http://127.0.0.1:9222`

## Quick Start

### Preview chapters

```bash
python "{baseDir}/scripts/prepare_chapters.py" --dir "/path/to/chapters" --preview
```

### Upload a single chapter as draft

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --book-id "7654770364014136344" \
  --file "/path/to/第001章-标题.md"
```

### Upload a range of chapters as drafts

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --book-id "7654770364014136344" \
  --dir "/path/to/chapters" \
  --range "第0005章-第0010章"
```

Or use chapter numbers:

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --book-id "7654770364014136344" \
  --book-name "书名" \
  --dir "/path/to/chapters" \
  --range "5-10"
```

### Upload all chapters as drafts

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --book-id "7654770364014136344" \
  --book-name "书名" \
  --dir "/path/to/chapters"
```

### Actually publish (default is draft-only)

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --book-id "7654770364014136344" \
  --book-name "书名" \
  --dir "/path/to/chapters" \
  --range "第001章-第003章" \
  --confirm-publish
```

## All Commands

### Preview

```bash
python "{baseDir}/scripts/prepare_chapters.py" --dir "/path/to/chapters" --preview
```

### Login

```bash
node "{baseDir}/scripts/login_fanqie.js" --cdp http://127.0.0.1:9222
```

### Upload as draft (default — no extra flag needed)

```bash
# Single chapter
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --file "/path/to/chapter.md"

# Range
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --dir "/path/to/chapters" --range "5-10"

# All
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --dir "/path/to/chapters"
```

### Publish for real (skip draft)

```bash
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --file "/path/to/chapter.md" --confirm-publish

node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --dir "/path/to/chapters" --range "1-3" --confirm-publish
```

### Scheduled publish

```bash
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --file "/path/to/chapter.md" --confirm-publish --mode scheduled --schedule-at "2026-03-13 21:00"

# Batch schedule with 30min intervals
node "{baseDir}/scripts/publish_fanqie.js" --cdp http://127.0.0.1:9222 --book-id "..." --dir "/path/to/chapters" --range "第018章-第020章" --confirm-publish --mode scheduled --schedule-at "2026-03-13 21:00" --schedule-step-minutes 30
```

## Flag reference

| Flag | Purpose |
|------|---------|
| `--cdp` | Chrome DevTools Protocol endpoint |
| `--book-id` | Book ID from Fanqie writer URL |
| `--book-name` | Book name (for URL construction) |
| `--file` | Single chapter file |
| `--dir` | Directory containing chapter files |
| `--range` | Chapter range, e.g. `"5-10"` or `"第05章-第10章"` |
| `--start-from` | Start from this chapter (used alone or with `--limit`) |
| `--end-at` | End at this chapter (used with `--start-from`) |
| `--limit` | Max chapters to process |
| `--confirm-publish` | Actually publish (default is save as draft) |
| `--mode` | `immediate` or `scheduled` (only with `--confirm-publish`) |
| `--schedule-at` | Schedule datetime, e.g. `"2026-03-13 21:00"` |
| `--schedule-step-minutes` | Minutes between chapters in batch schedule |
| `--skip-published` | Skip already-published chapters |
| `--volume` | Volume name to assign |
