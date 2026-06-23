---
name: daisywriter
description: "DaisyWriter — AI-powered writing toolkit / AI 驱动写作工具包"
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion
---

# DaisyWriter for OpenCode

This adapter provides OpenCode-specific loading instructions for DaisyWriter.

## Installation

Add to your `opencode.json`:

```json
{
  "skills": ["path/to/DaisyWriter/skills"]
}
```

Or load a skill directly:

```
skill("skills/webnovel/write")
```

## Skill Index

The master skill index is at `../../SKILL.md` (project root) or browse `../../skills/`.
