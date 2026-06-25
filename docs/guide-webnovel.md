# 网文写作指南 📚

12 个网文技能完整教程。

---

## 概览

```
参考书                新书
  │                    │
  ▼                    ▼
拆书 ───┐           立项
        │              │
        └──► 灵感      │
                       ▼
                     规划
                       │
                       ▼
               ┌── 写章 ──┐
               │          │
               ▼          ▼
             批量      审查
               │          │
               └──► 审查 ◄┘
                       │
                       ▼
                    发布
```

---

## 技能 1：拆书 (`webnovel-deconstruct`)

分析参考书，提取写作模式。

```
/webnovel-deconstruct 盗墓笔记
```

**输出：**
```
参考书/盗墓笔记/
├── 盗墓笔记.txt                  # 原文
├── 盗墓笔记-拆书报告.md          # 分析报告
├── 盗墓笔记-拆书数据.json        # 结构化数据
├── 盗墓笔记-情绪曲线.md          # 情绪曲线
└── 盗墓笔记-节奏统计.md          # 节奏统计
```

**拆书报告的用途：**
- 识别钩子放置模式
- 理解章节级节奏
- 提取可借用的收束结构

---

## 技能 2：立项 (`webnovel-init`)

创建新小说项目，结构化世界设定。

```
/webnovel-init "诡异熔炉"
```

分阶段交互采访：

| 阶段 | 收集内容 | 闸门 |
|------|----------|------|
| 灵感 | 创意库、参考书 | 至少 1 个灵感 |
| 故事核心 | 题材、书名、钩子、目标字数 | 书名 + 题材 |
| 角色 | 主角、配角 | 主角有欲望和缺陷 |
| 金手指 | 力量体系类型、限制 | 类型已确定 |
| 世界规则 | 设定、势力、历史 | 世界规模 |
| 约束 | 创意边界、反套路 | 命名规则 |

**充分性闸门**防止在信息不足时生成 —— 不会有半成品项目。

---

## 技能 3：规划 (`webnovel-plan`)

生成卷纲和章纲。

```
/webnovel-plan 1
```

**10 步流程：**
1. 加载项目状态
2. 从现有文件回填设定
3. 选择目标卷
4. 生成节拍表（卷级节奏）
5. 生成时间线（故事内时间）
6. 构建卷骨架
7. 批量章纲（每批 8-12 章）
8. 增量写回新设定到文件
9. 验证完整性
10. 刷新故事合约

**每章大纲包含：**
- CBN（关键叙事节点——必须出现的）
- CPN（可选节点）
- CEN（章节结束状态）
- 时间锚点
- 指向下一章的钩子
- 禁区

---

## 技能 4：写章 (`webnovel-write`)

单章撰写，带质量门禁。

```
/webnovel-write 5
```

**三种模式：**

| 模式 | 流程 | 适用场景 |
|------|------|----------|
| 默认 | 完整 6 步：前置 → 上下文 → 起草 → 扫描 → 审查 → 润色 | 正常章 |
| `--fast` | 轻量审查（跳过完整盲审） | 过渡章 |
| `--minimal` | 不审查，最小润色 | 初稿 / 脑暴 |

**工艺质量门禁（prose_scanner.py 强制执行）：**

| 指标 | 标准 | 阻断 |
|------|------|:----:|
| 平均句长 | 30-55 字 | <25 或 >55 |
| 极短句占比 | ≤15% | >15% |
| 长句占比 | ≥30% | — |
| 情绪标签词 | 0 | >0 |

---

## 技能 5：批量 (`webnovel-batch`)

批量写章，断点续跑。

```
/webnovel-batch 5 50
```

**架构：**
```
主对话
  │
  ├── 写手 agent（第 N 章）→ 自审 → 通过
  ├── 审查 agent（第 N 章，盲审）→ 通过
  ├── 保存断点
  ├── 写手 agent（第 N+1 章）→ ...
  └── ...
```

- 进度持久化到 `stream_progress.json`
- 崩溃后续跑：`/webnovel-batch 18 50`
- 每章使用全新写手 agent（无上下文串扰）

---

## 技能 6：工艺 (`webnovel-craft`)

量化散文质量约束。

这是一个**支撑技能**——由 `webnovel-write` 和 `webnovel-review` 自动加载。很少直接调用：

```
python skills/webnovel/craft/scripts/prose_scanner.py "正文/第0005章-觉醒.md"
```

返回 JSON 格式的阻断/非阻断问题列表。

---

## 技能 7：审查 (`webnovel-review`)

盲审章节质量。

```
/webnovel-review 5
```

**审查者接收：**
- 章纲（CBN/CEN）
- 上一章摘要
- 全文
- 工艺约束参考

**三个审查问题：**
1. 所有 CBN 都出现了吗？所有 CEN 都达成了吗？
2. 本章至少有一个情绪节拍吗？
3. 有散文质量问题吗？

**结果：**
- 全部通过 → 标记为已通过
- 阻断问题 → 用户决定：立即修复、保存报告、或放弃

---

## 技能 8：设定审查 (`webnovel-review-settings`)

审查世界观一致性。

```
/webnovel-review-settings
/webnovel-review-settings --quick      # 仅阻断+高级
/webnovel-review-settings --scope power # 单一维度
```

**严重度等级：**
- 🔴 **阻断** — 逻辑矛盾，导致无法写作
- 🟠 **高** — 明显漏洞
- 🟡 **中** — 潜在边界隐患
- 🟢 **低** — 润色建议

---

## 技能 9：查询 (`webnovel-query`)

从项目状态中检索信息。

```
/webnovel-query 主角
/webnovel-query 伏笔
/webnovel-query 力量体系
```

读取来源：
- `.webnovel/state.json`
- `.story-system/MASTER_SETTING.json`
- `设定集/` 中的设定文件
- RAG（WordPress 知识库，如已配置）

---

## 技能 10：学习 (`webnovel-learn`)

提取成功写作模式到项目记忆。

```
/webnovel-learn 本章的悬念设计很有层次感
```

追加到 `.webnovel/project_memory.json`，自动分类 pattern_type：
- hook, pacing, dialogue, payoff, emotion, format, other

**自动跳过重复条目。**

---

## 技能 11：医生 (`webnovel-doctor`)

只读健康检查。

```
/webnovel-doctor
/webnovel-doctor --chapter 5
/webnovel-doctor --deep
```

检查：
- 目录结构完整性
- 文件存在性和完整性
- JSON/SQLite 状态有效性
- RAG 配置
- Dashboard 构建产物

---

## 技能 12：仪表盘 (`webnovel-dashboard`)

启动只读 Web UI。

```
/webnovel-dashboard
/webnovel-dashboard --port 8080
```

功能：
- 项目概览（字数、章节状态）
- 实体关系图（角色、势力、地点）
- 章节内容查看
- 追读力数据