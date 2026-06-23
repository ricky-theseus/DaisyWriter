# DaisyWriter for Claude Code

This directory contains Claude Code-specific instructions for loading DaisyWriter skills.

## Getting Started

Add to your `.claude/settings.json` or reference in CLAUDE.md:

```json
{
  "skills": ["../skills"]
}
```

## Available Skills

Browse `../skills/` for all available skills organized by domain:

- `skills/webnovel/` — Web novel creation pipeline
- `skills/shortstory/` — Short story writing
- `skills/tech/` — Technical blogging
- `skills/fanqie/` — Fanqie Novel publishing

## Usage

In Claude Code, reference a skill by its path:

```
@skills/webnovel/write
```
