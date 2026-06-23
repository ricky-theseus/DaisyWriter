# Changelog

## [1.0.0] - 2026-06-23

### Added
- **Root project structure**: `.gitignore`, `.editorconfig`, `.gitattributes`, `LICENSE`
- **Bilingual README**: English primary + Chinese translation, badges, architecture diagram, skill tables
- **Root SKILL.md**: Collection entry point with categorized skill listing
- **CONTRIBUTING.md**: Comprehensive contribution guidelines
- **CODE_OF_CONDUCT.md**: Contributor Covenant v2.0
- **GitHub templates**: Issue templates (bug report, feature request) and PR template
- **CHANGELOG.md**: Version tracking
- **adapter system**: `adapters/opencode/`, `adapters/claude-code/CLAUDE.md`, `adapters/codex/`
- **shared/**: Cross-domain reference directory

### Changed
- **Project name**: `DaisyWriter`
- **License**: MIT → **GPL v3** (required by derived work from lingfengQAQ/webnovel-writer)
- **Structure**: Skills grouped by domain under `skills/{domain}/`:
  - `webnovel-*` → `skills/webnovel/*`
  - `shortstory-*` → `skills/shortstory/*`
  - `tech-*` → `skills/tech/*`
  - `fanqie-publisher/` → `skills/fanqie/`
- **All SKILL_ROOT paths** updated for new directory depth
- **All cross-skill references** (e.g. `../craft/scripts/`) updated

### Fixed
- Hardcoded book name `《诡异熔炉》` in `webnovel-batch/SKILL.md` → parameterized `{book_name}`
- Missing `argument-hint` in 4 skills: root SKILL.md, webnovel-craft, shortstory-craft, webnovel-dashboard
- Inconsistent `version` field removed from `webnovel-doctor`
- Duplicate Chinese section in README

### Notes
- All 21 original skills preserved unchanged in content and logic
- `skills/fanqie/` retains its own MIT license (forked from amm10090/fanqie-publisher-skill)
- Web novel / short story / tech skills derived from lingfengQAQ/webnovel-writer (GPL v3)
