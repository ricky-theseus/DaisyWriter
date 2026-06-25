# DaisyWriter Development Workflow

DaisyWriter 的开发遵循 **Superpower PR Flow**——每次变更都是一个独立 PR，经过规范流程。

---

## 核心原则

1. **一次 PR 只做一件事** —— 修复一个 bug、添加一个 skill、更新一个文档
2. **先检查再动手** —— 加载相关 skill，确认流程再改代码
3. **分支命名规范** —— `feat/xxx`、`fix/xxx`、`docs/xxx`、`sync/xxx`
4. **PR 必须审查** —— 至少自己过一遍 checklist
5. **每次 Writer 同步必须独立 PR**

---

## 标准 PR 流程

```
1. 发现问题 / 收到需求
       │
       ▼
2. 加载相关技能（skill check）
       │
       ▼
3. 创建分支 (git checkout -b feat/my-change)
       │
       ▼
4. 修改代码 / 文档
       │
       ▼
5. 本地验证 (git status / git diff)
       │
       ▼
6. 提交 (git commit -m "type: description")
       │
       ▼
7. 推送 (git push origin feat/my-change)
       │
       ▼
8. 创建 PR → 自检 checklist → 合并
       │
       ▼
9. 删除分支
```

---

## 分支命名

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能、新 skill | `feat/cover-maker-v2` |
| `fix/` | 修复 bug | `fix/batch-resume-crash` |
| `docs/` | 文档更新 | `docs/translate-en` |
| `sync/` | 从 Writer 同步 | `sync/shortstory-update` |
| `refactor/` | 重构 | `refactor/adapter-arch` |
| `chore/` | 杂务 | `chore/ci-upgrade` |

---

## Commit 规范

```
<type>: <简短描述>

<可选的详细说明>
```

**type：**
- `feat` — 新功能
- `fix` — 修复
- `docs` — 文档
- `sync` — 从 Writer 同步
- `refactor` — 重构
- `chore` — 构建/CI/杂务

**示例：**
```
feat: add shortstory-review skill with blind review pipeline
fix: prose_scanner.py crashes on empty chapter
sync: pull fanqie SKILL.md updates from Writer
docs: translate guide-webnovel to English
```

---

## PR Checklist

每次创建 PR 前检查：

- [ ] 我只改了一个逻辑单元（一个功能 / 一个修复）
- [ ] 分支名遵循规范
- [ ] 提交信息清晰且有 type 前缀
- [ ] 所有新文件都有 SKILL.md YAML front matter
- [ ] 路径引用在目标平台下有效
- [ ] 没有泄漏个人信息或作品内容
- [ ] 没有硬编码的本地路径
- [ ] 文档已同步更新（如果适用）

---

## Writer 同步流程

从 `D:\Writer\.opencode\skills\` 同步到 DaisyWriter：

```
1. git checkout -b sync/description
2. 运行 diff 比较两边的文件
3. 只复制实际变更的文件（不是路径调整）
4. 排除个人作品、个人信息、调试脚本
5. git commit -m "sync: <description>"
6. git push origin sync/description
7. 创建 PR
```

**禁止：**
- 同步 `未命名者/`、`诡异熔炉/`、`小说/`、`博文/` 等作品目录
- 同步 `.author/`、有个人信息的内容
- 修正在同步中发现的与同步无关的 bug（另开 PR）

---

## 技能加载检查（Skill Check）

每次开始任务前，执行：

```python
skill("using-superpowers")
skill("relevant-skill-name")
```

如果不知道该加载哪个 skill，先加载 `using-superpowers` 获取指导。

---

## 参考

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)