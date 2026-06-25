<p align="center">
  <img src="https://img.shields.io/badge/DaisyWriter-v1.0.0-8B5CF6?style=for-the-badge&logo=openai&logoColor=white" alt="DaisyWriter">
  <img src="https://img.shields.io/badge/24_Skills-6C47FF?style=for-the-badge&logo=readme&logoColor=white" alt="24 Skills">
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-GPL_v3-blue.svg?style=flat-square" alt="GPL v3"></a>
  <a href="https://github.com/anomalyco/opencode"><img src="https://img.shields.io/badge/OpenCode-0.6+-blue?style=flat-square" alt="OpenCode"></a>
  <a href="./docs/QUICKSTART.md"><img src="https://img.shields.io/badge/Quick_Start-8B5CF6?style=flat-square" alt="Quick Start"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python_3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node_18+-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js"></a>
  <br>
  <a href="#-project-overview">English</a> ·
  <a href="./docs/README.md">中文</a>
</p>

---

<h1 align="center">✍️ DaisyWriter</h1>

<p align="center">
  <b>AI writing toolkit — from blank page to published novel.</b><br>
  <b>A skill collection for OpenCode, Claude Code, and beyond.</b>
</p>

<p align="center">
  <i>大纲 → 设定 → 写章 → 审查 → 发布 —— 一个指令完成</i>
</p>

---

## 📋 Project Overview

**DaisyWriter** turns your AI coding assistant into a professional writing studio. It provides **24 composable skills** across the full content creation lifecycle:

| Domain | Skills | What you can do |
|--------|--------|-----------------|
| 📚 **Web Novel** | 12 | Plan, write, review, and batch-produce web novels |
| 📝 **Short Story** | 5 | Init, write, and blind-review Zhihu Yanxuan stories |
| 💻 **Tech Blog** | 5 | Write, batch, and auto-publish technical articles |
| 🤖 **Publishing** | 1 | Browser-automated publish to Fanqie Novel |
| 🔧 **Tools** | 1 | AI-generated book covers |

### Architecture

```
DaisyWriter/
├── skills/                     # 24 skills by domain
│   ├── webnovel/               #   12 — full web novel pipeline
│   │   ├── init/ plan/ write/ batch/ craft/
│   │   └── review/ review-settings/ query/ learn/
│   │   └── deconstruct/ doctor/ dashboard/
│   ├── shortstory/             #    5 — short story pipeline
│   │   └── init/ write/ review/ craft/ deconstruct/
│   ├── tech/                   #    5 — tech blog pipeline
│   │   └── write/ deconstruct/ batch/ sync-csdn/ csdn-upload/
│   ├── fanqie/                 #    1 — Fanqie Novel publishing
│   └── cover-maker/            #    1 — AI cover generation
├── adapters/                   # Platform entry points
│   ├── opencode/               #   OpenCode
│   ├── claude-code/            #   Claude Code
│   └── codex/                  #   Codex CLI (WIP)
├── docs/                       # Tutorials & reference
│   ├── QUICKSTART.md           #   5-minute setup
│   ├── guide-webnovel.md       #   Web novel tutorial
│   ├── guide-shortstory.md     #   Short story tutorial
│   └── ...                     #   More guides
└── shared/                     # Cross-domain references
```

---

## 🚀 30-Second Demo

```bash
# 1. Initialize a web novel project
/webnovel-init "My Epic Fantasy"

# 2. Plan the first volume
/webnovel-plan 1

# 3. Write chapter 1
/webnovel-write 1

# 4. Review it
/webnovel-review 1

# 5. Publish to Fanqie Novel
/fanqie-publish --file "正文/第0001章-觉醒.md"
```

**That's it.** Each command runs a complete AI-powered pipeline with built-in quality gates, blind review, and failure recovery.

---

## 🛠️ Quick Start

### Prerequisites

| Requirement | Version | For |
|-------------|---------|-----|
| [OpenCode](https://opencode.ai) | ≥ 0.6 | Running skills |
| Python | ≥ 3.8 | Prose scanner, utility scripts |
| Node.js | ≥ 18 | Fanqie publisher, cover generator |
| Playwright | latest | Browser automation |

### Install

```bash
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter

# For Fanqie publishing (optional):
cd skills/fanqie
npm install && npx playwright install chromium
cd ../..

# For cover generation (optional):
cd skills/cover-maker
npm install
cd ../..
```

### Load in OpenCode

Add to your `opencode.json`:
```json
{
  "skills": ["path/to/DaisyWriter"]
}
```

Or load a skill directly:
```python
skill("skills/webnovel/write")
```

> 📖 Full walkthrough: [docs/QUICKSTART.md](./docs/QUICKSTART.md)

---

## 🎯 Skills by Domain

### 📚 Web Novel — 12 skills

Complete pipeline from deconstruction to dashboard:

| Step | Command | What happens |
|------|---------|-------------|
| 1 | `/webnovel-deconstruct 书名` | Analyze a reference novel |
| 2 | `/webnovel-init "我的小说"` | Interactive worldbuilding + sufficiency gates |
| 3 | `/webnovel-plan 1` | Generate volume beat sheet + chapter outlines |
| 4 | `/webnovel-write 1` | Write chapter with prose quality scan |
| 5 | `/webnovel-batch 1 30` | Batch-write chapters 1-30 with checkpoint resume |
| 6 | `/webnovel-review 5` | Blind review chapter 5 |
| 7 | `/webnovel-review-settings` | Audit setting consistency |
| 8 | `/webnovel-query 主角` | Query project state |
| 9 | `/webnovel-learn 这段对话写得妙` | Save writing pattern to memory |
| 10 | `/webnovel-doctor` | Health diagnostic |
| 11 | `/webnovel-dashboard` | Launch web UI |

> 📖 Tutorial: [docs/guide-webnovel.md](./docs/guide-webnovel.md)

### 📝 Short Story — 5 skills

Zhihu Yanxuan / medium-length rolling write:

| Step | Command | What happens |
|------|---------|-------------|
| 1 | `/shortstory-init 3 悬疑` | Init 3 suspense stories + blind review loop |
| 2 | `/shortstory-write 悬疑/白骨墙` | Rolling write with word-count gate |
| 3 | `/shortstory-review 悬疑/白骨墙` | Stage-aware blind review |
| 4 | `/shortstory-deconstruct 参考文` | Extract hook/suspense/pacing patterns |

> 📖 Tutorial: [docs/guide-shortstory.md](./docs/guide-shortstory.md)

### 💻 Tech Blog — 5 skills

Structured technical writing:

| Step | Command | What happens |
|------|---------|-------------|
| 1 | `/tech-deconstruct 参考文` | Analyze reference article |
| 2 | `/tech-write "用FastAPI写API"` | Structure → Draft → Review → Final |
| 3 | `/tech-batch 项目目录` | Batch produce multiple articles |
| 4 | `/csdn-upload --dry-run` | Preview upload state |
| 5 | `/csdn-upload` | Upload drafts to CSDN |

> 📖 Tutorial: [docs/guide-tech.md](./docs/guide-tech.md)

### 🤖 Publishing — 1 skill

Browser-automated chapter publishing to Fanqie Novel:

| Step | Command | What happens |
|------|---------|-------------|
| 1 | `/fanqie-publish --preview` | Preview chapter parse result |
| 2 | `/fanqie-publish --login` | QR code login |
| 3 | `/fanqie-publish --fill-only` | Save as draft (safe) |
| 4 | `/fanqie-publish --confirm-publish` | Publish immediately |

> 📖 Setup: [skills/fanqie/README.md](./skills/fanqie/README.md)

### 🔧 Cover Maker — 1 skill

| Command | What happens |
|---------|-------------|
| `node skills/cover-maker/generate_cover.js "长篇/奇幻/我的小说"` | Generate 600×800 covers for all candidate titles |

---

## ✨ Design Philosophy

| Principle | What it means |
|-----------|---------------|
| 🧠 **Sub-agent isolation** | Writer and reviewer are always separate AI agents |
| 🙈 **Blind review** | Reviewer has no memory of previous passes |
| 🚪 **Quality gates** | Sufficiency → Craft → Review → Pre-commit |
| 📈 **Incremental** | Only append, never overwrite. Retry only the failed step |
| 🧹 **Clean output** | No version markers, no AI metadata in final files |

---

## 🧩 Platform Support

| Platform | Status | Entry |
|----------|--------|-------|
| [OpenCode](https://opencode.ai) | ✅ Native | [`SKILL.md`](./SKILL.md) |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | ✅ Ready | [`adapters/claude-code/`](./adapters/claude-code/) |
| Codex CLI | 🚧 WIP | [`adapters/codex/`](./adapters/codex/) |
| GitHub Copilot | 📋 Planned | — |

---

## 🧭 Documentation

| Document | Description | 中文 |
|----------|-------------|------|
| [`docs/QUICKSTART.md`](./docs/QUICKSTART.md) | 5-min setup & first novel | [快速上手](./docs/QUICKSTART.md) |
| [`docs/guide-webnovel.md`](./docs/guide-webnovel.md) | Complete web novel tutorial | [网文写作指南](./docs/guide-webnovel.md) |
| [`docs/guide-shortstory.md`](./docs/guide-shortstory.md) | Short story writing guide | [短篇写作指南](./docs/guide-shortstory.md) |
| [`docs/guide-tech.md`](./docs/guide-tech.md) | Technical blogging guide | [技术博文指南](./docs/guide-tech.md) |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to contribute |

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

**Help wanted:**
- 🌐 English translations & i18n
- 🔌 Additional AI assistant adapters
- 📖 More tutorial content
- 🎨 Dashboard UI
- 🐛 Bug reports & fixes

---

## 📄 License

**GNU General Public License v3.0** — see [LICENSE](./LICENSE).

| Component | License | Source |
|-----------|---------|--------|
| `skills/webnovel/`, `skills/shortstory/`, `skills/tech/` | GPL v3 | Derived from [@lingfengQAQ/webnovel-writer](https://github.com/lingfengQAQ/webnovel-writer) |
| `skills/fanqie/` | MIT | Forked from [@amm10090/fanqie-publisher-skill](https://github.com/amm10090/fanqie-publisher-skill) |
| Everything else | GPL v3 | Original work |

---

<p align="center">
  <b>DaisyWriter</b> — built by <a href="https://github.com/ricky-theseus">@ricky-theseus</a>
  <br>
  <sub>Star us on GitHub — it helps others discover the project ⭐</sub>
</p>