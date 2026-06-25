# DaisyWriter for Codex CLI

Codex CLI adapter for DaisyWriter — AI-powered writing toolkit.

## Installation

```bash
# Clone DaisyWriter
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter

# Run Codex setup
python adapters/codex/setup.py
```

The setup script creates `.codex/skills/` symlinks pointing to each DaisyWriter skill.

## Usage

In Codex CLI, skills are loaded by name:

```
/skill webnovel-write
```

## Skills

All 24 skills are available under `.codex/skills/` after setup:

| Skill | Description |
|-------|-------------|
| webnovel-init | 网文项目立项 |
| webnovel-write | 网文写章 |
| webnovel-review | 章节审查 |
| shortstory-write | 短篇写章 |
| tech-write | 技术博文写作 |
| fanqie-publish | 番茄小说发布 |
| cover-maker | 封面生成 |

## Requirements

- Python ≥ 3.8
- Node.js ≥ 18 (for fanqie/cover-maker)