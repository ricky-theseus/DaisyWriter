<p align="center">
  <img src="https://img.shields.io/badge/DaisyWriter-v1.0.0-8B5CF6?style=for-the-badge&logo=openai&logoColor=white" alt="DaisyWriter">
  <img src="https://img.shields.io/badge/OpenCode-Skill_Collection-6C47FF?style=for-the-badge&logo=readme&logoColor=white" alt="OpenCode">
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL_v3-blue.svg?style=flat-square" alt="GPL v3"></a>
  <a href="https://github.com/anomalyco/opencode"><img src="https://img.shields.io/badge/OpenCode-0.6+-blue?style=flat-square" alt="OpenCode"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js"></a>
  <a href="https://playwright.dev/"><img src="https://img.shields.io/badge/Playwright-45ba4b?style=flat-square&logo=playwright" alt="Playwright"></a>
  <br>
  <a href="#-project-overview">English</a> ·
  <a href="#-项目概览">中文</a>
</p>

---

<h1 align="center">✍️ DaisyWriter</h1>

<p align="center">
  <b>Multi-agent writing toolkit — Web novels, Short stories, Technical blogs, Publishing automation.</b><br>
  <b>多 Agent 写作工具包 — 网文、短篇、技术博文、发布自动化。</b>
</p>

<p align="center">
  A cross-platform skill collection for <a href="https://github.com/anomalyco/opencode">OpenCode</a>,
  <a href="./adapters/claude-code/">Claude Code</a>, and more AI coding assistants.
  <br>
  跨平台 AI 编程助手技能合集。
</p>

---

## 📋 Project Overview

**DaisyWriter** is a modular, production-grade skill collection for AI coding assistants. It transforms your AI assistant into a full-fledged writing studio with structured pipelines for web novels, short stories, technical blogs, and automated publishing.

### Architecture

```
DaisyWriter/
├── README.md              # This file
├── SKILL.md               # Root skill index
├── LICENSE                # MIT
├── .github/               # Templates (issues, PRs)
│
├── skills/                # Core writing skills by domain
│   ├── webnovel/          #   12 skills — full web novel pipeline
│   ├── shortstory/        #   4 skills — short story writing
│   ├── tech/              #   4 skills — technical blogging
│   └── fanqie/            #   1 skill — Fanqie Novel publishing
│
├── adapters/              # Platform-specific entry points
│   ├── opencode/          #   OpenCode SKILL.md entry
│   ├── claude-code/       #   CLAUDE.md + instructions
│   └── codex/             #   Codex CLI (in development)
│
├── scripts/               # Project-level utilities
└── shared/                # Cross-domain reference files
```

---

## 🚀 Skills Overview

### 📚 Web Novel Creation (`skills/webnovel/`)

| Skill | Path | Description |
|-------|------|-------------|
| init | [`skills/webnovel/init/`](skills/webnovel/init/) | Project initialization with sufficiency gates |
| plan | [`skills/webnovel/plan/`](skills/webnovel/plan/) | Volume & chapter outlining |
| write | [`skills/webnovel/write/`](skills/webnovel/write/) | Single chapter production (3 modes) |
| batch | [`skills/webnovel/batch/`](skills/webnovel/batch/) | Batch chapter writing with checkpoint resume |
| craft | [`skills/webnovel/craft/`](skills/webnovel/craft/) | Prose quality constraints + scanner |
| review | [`skills/webnovel/review/`](skills/webnovel/review/) | Chapter quality review |
| review-settings | [`skills/webnovel/review-settings/`](skills/webnovel/review-settings/) | Setting consistency audit |
| deconstruct | [`skills/webnovel/deconstruct/`](skills/webnovel/deconstruct/) | Reference novel analysis |
| query | [`skills/webnovel/query/`](skills/webnovel/query/) | Information retrieval |
| learn | [`skills/webnovel/learn/`](skills/webnovel/learn/) | Pattern extraction |
| doctor | [`skills/webnovel/doctor/`](skills/webnovel/doctor/) | Health diagnostic |
| dashboard | [`skills/webnovel/dashboard/`](skills/webnovel/dashboard/) | Web UI dashboard |

### 📝 Short Story (`skills/shortstory/`)

| Skill | Path | Description |
|-------|------|-------------|
| init | [`skills/shortstory/init/`](skills/shortstory/init/) | Project init + blind review |
| write | [`skills/shortstory/write/`](skills/shortstory/write/) | Full writing pipeline |
| craft | [`skills/shortstory/craft/`](skills/shortstory/craft/) | Craft quality constraints |
| deconstruct | [`skills/shortstory/deconstruct/`](skills/shortstory/deconstruct/) | Reference analysis |

### 💻 Technical Blog (`skills/tech/`)

| Skill | Path | Description |
|-------|------|-------------|
| write | [`skills/tech/write/`](skills/tech/write/) | Blog post writing |
| deconstruct | [`skills/tech/deconstruct/`](skills/tech/deconstruct/) | Article analysis |
| batch | [`skills/tech/batch/`](skills/tech/batch/) | Batch production |
| sync-csdn | [`skills/tech/sync-csdn/`](skills/tech/sync-csdn/) | CSDN sync |

### 🤖 Publishing (`skills/fanqie/`)

| Skill | Path | Description |
|-------|------|-------------|
| fanqie-publish | [`skills/fanqie/`](skills/fanqie/) | Browser-automated publishing to Fanqie Novel |

---

## ✨ Key Design Philosophy

### Sub-agent Isolation
Every production skill enforces **separate AI agents** for writing vs. reviewing. The reviewer is always "blind" — no memory of prior passes.

### Quality Gates
- **Sufficiency gates**: Prevent generation before enough information is collected
- **Craft gates**: Quantitative metrics enforced by prose scanner scripts
- **Review gates**: Blind review with blocking/warning/suggestion severity
- **Pre-commit gates**: Validation before asset extraction and git backup

### Incremental by Default
- Plan only appends, never rewrites
- Learning only appends, never overwrites
- Review validates, never suggests alternatives
- Failure retries the failed step, not the whole pipeline

### Clean Output
No version markers, revision notes, or AI metadata in final files.

---

## 🛠️ Getting Started

### Prerequisites

- [OpenCode](https://opencode.ai) v0.6+ (or [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview))
- Python 3.8+ (for prose scanner and utility scripts)
- Node.js 18+ (for Fanqie publisher)
- [Playwright](https://playwright.dev/) (for browser automation)

### Installation

```bash
# Clone the repository
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter

# For Fanqie Publisher (optional):
cd skills/fanqie
npm install
npx playwright install chromium
cd ../..
```

### Usage

In your AI coding assistant, load a skill:

```
/webnovel-init "My Epic Fantasy Novel"
/shortstory-write "The Last Train" --draft
/tech-write "Build a REST API with FastAPI"
```

### For Fanqie Publisher

See the [dedicated README](skills/fanqie/README.md) for setup and usage instructions including CDP browser connection, QR login, and batch publishing.

---

## 🧩 Platform Support

| Platform | Status | Entry Point |
|----------|--------|-------------|
| OpenCode | ✅ Ready | [`SKILL.md`](./SKILL.md) or [`adapters/opencode/`](./adapters/opencode/) |
| Claude Code | ✅ Ready | [`adapters/claude-code/CLAUDE.md`](./adapters/claude-code/CLAUDE.md) |
| Codex CLI | 🚧 In dev | [`adapters/codex/`](./adapters/codex/) |
| GitHub Copilot | 📋 Planned | — |

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md).

**Areas we'd love help with:**
- English translations and internationalization
- Additional AI assistant adapters
- More publishing platforms (Webnovel, Royal Road, etc.)
- New genre-specific craft constraints
- Prose scanner improvements
- Dashboard UI enhancements

---

## 📄 License

**GNU General Public License v3.0** — see [LICENSE](./LICENSE).

### Acknowledgements / 致谢

This project is derived from two open-source projects:

| Source | License | What's used |
|--------|---------|-------------|
| [lingfengQAQ/webnovel-writer](https://github.com/lingfengQAQ/webnovel-writer) | **GPL v3** | Web novel creation skills (`skills/webnovel/`, `skills/shortstory/`, `skills/tech/`) |
| [amm10090/fanqie-publisher-skill](https://github.com/amm10090/fanqie-publisher-skill) | **MIT** | Fanqie Novel publisher (`skills/fanqie/`) — retains its own MIT license |

The `skills/fanqie/` subdirectory retains its original **MIT License** (see its [LICENSE](skills/fanqie/LICENSE)). The rest of the project is **GPL v3**.

---

<p align="true">
  Made with ❤️ for the writer community
</p>

---

## 📖 项目概览

**DaisyWriter** 基于以下开源项目开发：

| 来源 | 许可证 | 使用部分 |
|------|--------|----------|
| [lingfengQAQ/webnovel-writer](https://github.com/lingfengQAQ/webnovel-writer) | **GPL v3** | 网文/短篇/技术博文技能 |
| [amm10090/fanqie-publisher-skill](https://github.com/amm10090/fanqie-publisher-skill) | **MIT** | 番茄发布模块（保留 MIT 许可证） |

---


