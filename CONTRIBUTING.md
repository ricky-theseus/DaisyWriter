# Contributing to Skill Writer

Thank you for considering contributing! We welcome contributions from everyone, whether it's bug fixes, new skills, documentation improvements, or internationalization.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Skill Development Guidelines](#skill-development-guidelines)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## How to Contribute

### 🐛 Report Bugs

Open an issue describing:
- The skill and step where the bug occurs
- Expected vs actual behavior
- OpenCode version and environment
- Steps to reproduce

### 💡 Suggest Enhancements

Open an issue with:
- A clear description of the proposed feature
- Why it would be valuable (real use cases)
- If applicable, how it fits into the existing architecture

### 📝 Improve Documentation

- Fix typos or unclear instructions in SKILL.md files
- Add or improve English translations
- Improve reference documentation

### 🌐 Internationalization

We want this project to be accessible globally:
- Add English descriptions to SKILL.md front matter
- Translate key documentation
- Add locale-specific references (e.g., platform-specific writing guides)

### ✨ Add New Skills

Follow the [Skill Development Guidelines](#skill-development-guidelines) below.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/skill-writer.git
   ```

2. For skills with scripts (e.g., `fanqie-publisher`):
   ```bash
   cd fanqie-publisher
   npm install
   ```

3. Test in OpenCode by loading the skill collection.

## Skill Development Guidelines

### Naming Convention

- Use `kebab-case` for skill directory names
- Prefix by domain: `webnovel-`, `shortstory-`, `tech-`
- Follow existing patterns for similar skills

### SKILL.md Structure

Every skill must have:

```yaml
---
name: skill-name
description: Brief description (bilingual if possible)
allowed-tools: Read Write Edit Grep Bash Agent ...
argument-hint: "[optional args]"
---
```

### Quality Standards

1. **Sub-agent Isolation**: Writer and reviewer must always be separate agent calls
2. **Blind Review**: Reviewer should have no memory of previous review passes
3. **Hard Rules**: Document rules that must not be violated
4. **Quality Gates**: Define measurable criteria for pass/fail
5. **Incremental**: Only append, never overwrite existing data

### Reference Files

- Place references in `references/` subdirectory
- Reference files should be modular (one concept per file)
- Use clear, descriptive filenames

## Pull Request Process

1. Read the [Development Workflow](docs/WORKFLOW.md) first
2. Check relevant skills before starting
3. Create a feature branch (`git checkout -b feat/amazing-skill`)
4. Commit your changes using [conventional commit format](docs/WORKFLOW.md#commit-规范)
5. Push to your fork (`git push origin feat/amazing-skill`)
6. Open a Pull Request against the `master` branch
7. Run through the [PR Checklist](docs/WORKFLOW.md#pr-checklist) before requesting review

### PR Review Criteria

- Follows existing conventions and patterns
- Has proper YAML front matter
- Quality gates are defined
- Sub-agent isolation is maintained
- Documentation is complete
- No hardcoded paths specific to one developer's machine

## Style Guide

### Markdown

- Use ATX headings (`##` not underlined)
- Use fenced code blocks with language tags
- Use relative links for internal references
- Prefer tables for structured data

### SKILL.md

- Use Chinese for operational content (since the writing task is in Chinese)
- Provide English description in YAML front matter
- Keep pipeline steps numbered and clear
- Use separate `---` section for hard rules

### Code

- Python: PEP 8, type hints where practical
- JavaScript: Standard style, async/await preferred
- Scripts should handle errors gracefully

## Questions?

Open a [Discussion](https://github.com/your-username/skill-writer/discussions) or issue. We're happy to help!
