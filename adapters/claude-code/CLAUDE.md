# DaisyWriter for Claude Code

DaisyWriter 是一个 AI 写作工具包，包含 24 个技能，覆盖网文、短篇、技术博文和发布自动化。

## 快速开始

```bash
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter
```

在 Claude Code 中加载技能：

```
/skill skills/webnovel/write
```

## 技能索引

所有技能在 `skills/` 目录下，按领域组织：

| 领域 | 技能 | 命令 |
|------|------|------|
| 📚 网文 | 立项、规划、写章、批量、审查、工艺 | `/skill skills/webnovel/init` |
| 📝 短篇 | 立项、写章、审查、工艺、拆解 | `/skill skills/shortstory/write` |
| 💻 博文 | 写作、拆解、批量、CSDN 同步 | `/skill skills/tech/write` |
| 🤖 发布 | 番茄小说发布 | `/skill skills/fanqie/publish_fanqie` |
| 🔧 工具 | AI 封面生成 | `/skill skills/cover-maker` |

## 依赖

- Python 3.8+（工艺扫描脚本）
- Node.js 18+（番茄发布、封面生成）
- Playwright（浏览器自动化，可选）

## 更多文档

详见 `docs/` 目录。