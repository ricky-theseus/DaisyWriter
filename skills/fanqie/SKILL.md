---
name: fanqie-publish
description: Publish novel chapters from local Markdown files to the Fanqie Novel writer backend via browser automation. Supports single/batch/scheduled publish with login state persistence.
allowed-tools: Read Write Grep Bash Agent
argument-hint: "[--preview | --login | --publish [--file ...] [--dir ...] [--mode immediate|scheduled] [--confirm-publish] [--fill-only]]"
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
- first line example: `# 第001章 标题`
- body starts after the heading

## Files

- `scripts/prepare_chapters.py` — parse `.md` files into normalized chapter data
- `scripts/browser_page_picker.js` — pick an existing Fanqie writer tab or open a safe fallback page
- `scripts/fanqie_login_flow.js` — shared login helpers used by the login and publish entrypoints
- `scripts/login_fanqie.js` — open browser, detect login page, capture QR code, and save login state
- `scripts/login_fanqie_notify.js` — wrap login flow and emit machine-readable QR/media-ready output
- `scripts/publish_fanqie.js` — publish one or more chapters with Playwright; auto-restore Chrome 9222 session; fall back to QR login if expired; auto-retry once for retryable failures
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
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Or launch Chrome normally, then run:
# node "{baseDir}/scripts/login_fanqie.js" --launch-browser
```

4. First-time login: scan QR code with Fanqie Novel app

## Safe workflow

1. Parse chapters first
2. Preview chapter list and extracted titles
3. Log in and save browser state
4. Publish **one chapter** as a live test
5. Only then run batch or scheduled publishing

## Commands

### 1) Preview parsed chapters

```bash
# Windows: python, Linux/macOS: python3
python "{baseDir}/scripts/prepare_chapters.py" \
  --dir "/path/to/chapters" \
  --preview
```

### 2) Save login state

```bash
node "{baseDir}/scripts/login_fanqie.js" --cdp http://127.0.0.1:9222
```

This will connect to the writer backend, switch to QR login when needed, save a QR screenshot to `{baseDir}/state/login-qr.png`, and wait for manual scan / login completion.

### 3) Save as draft (recommended mode — bypasses dialog/publish issues)

Fills editor + saves as draft. You then manually publish from drafts at your own pace.

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapters/第001章_标题.md" \
  --mode immediate \
  --draft-only
```

### 4) Batch save drafts

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --dir "/path/to/chapters" \
  --start-from "第006章" \
  --limit 36 \
  --mode immediate \
  --draft-only
```

### 5) Go to final publish modal (stop before publish)

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapters/第001章_标题.md" \
  --mode immediate \
  --to-final-modal
```

### 6) Immediate publish

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapters/第001章_标题.md" \
  --mode immediate \
  --confirm-publish
```

### 7) Batch immediate publish

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --dir "/path/to/chapters" \
  --start-from "第014章" \
  --limit 3 \
  --mode immediate \
  --confirm-publish
```

### 8) Schedule one chapter

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapters/第018章_标题.md" \
  --mode scheduled \
  --schedule-at "2026-03-13 21:00" \
  --confirm-publish
```

### 9) Batch schedule

```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --cdp http://127.0.0.1:9222 \
  --dir "/path/to/chapters" \
  --start-from "第018章" \
  --limit 3 \
  --mode scheduled \
  --schedule-at "2026-03-13 21:00" \
  --schedule-step-minutes 30 \
  --confirm-publish
```

### Required: book ID

Before publishing, you need your Fanqie book ID. Find it in the writer backend URL:
`https://fanqienovel.com/main/writer/{BOOK_ID}/publish/`

Pass it to every publish command:
```bash
node "{baseDir}/scripts/publish_fanqie.js" \
  --book-id "7653355066706889790" \
  --book-name "拒演者" \
  ...other args
```

### Useful flags

- `--skip-published` — skip chapters already in `{baseDir}/state/publish-state.json`
- `--to-final-modal` — batch-safe stop before final publish
- `--fill-only` — only fill the draft editor for the first selected chapter
- `--daily-limit-chars 50000` — safety guard for suspected Fanqie daily publish ceiling
- `--already-published-chars 47796` — already published chars today
- `--schedule-step-minutes 30` — offset each chapter by N minutes from `--schedule-at`
- `--volume "<分卷名>"` — specify volume before publishing
- `--launch-browser` — let the script launch Chrome instead of using CDP

## Current workflow understanding

Validated publish flow (2026-03-20):
1. Open chapter management for the target book
2. Switch to the target volume on chapter management
3. Enter `新建章节` from chapter management so the draft inherits the chosen volume
4. Fill chapter number, title, and body
5. Save draft and confirm word count is not `0`
6. Click top-right `下一步`
7. Handle typo/spellcheck modal → `提交`
8. Handle risk-detection modal → `确定`
9. In final publish modal, choose `是否使用AI` → `否`
10. For scheduled release, click `定时发布` and set date/time
11. Click `确认发布`
12. Return to chapter management and verify row status is `审核中` or `已发布`

## Rules

- Prefer publishing one chapter first before batch mode
- Never assume a selector is stable without confirming it
- Record each successful publish in state to avoid duplicates
- If login state expires, re-run `login_fanqie.js`
- Treat `50000` chars/day as a practical safety ceiling
- Scheduled chapters become locked ~30 min before publish time
