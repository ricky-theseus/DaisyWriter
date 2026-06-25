---
name: shortstory-write
description: 中短篇滚动写。逐章写→字数门禁→子 agent 盲审→单章循环→全篇终审→定稿(≥95分)
allowed-tools: Read Write Edit Grep Glob Bash Task
argument-hint: "[类型/项目名] [--resume|--advance|--finalize]"
---

# 中短篇 · 滚动写

## 核心约定

- 所有章节在 `短篇/{类型}/{项目名}/正文.md`，`## 第N章：标题` 分隔
- 进度由 `write_status.json` 驱动，不靠对话记忆
- **写由主 agent（当前会话）完成，审由全新子 agent（Task tool）完成**
- 脚本只做字数门禁和状态流转，防止 AI 中断循环

## 格式约束

- 章节之间只用 `## 第N章：标题` 分隔，禁止 `---` 或其他 markdown 分隔线
- 段落间距由自然换行控制
- 例外：系统界面、电子屏幕内容可以使用 `---` 表示屏幕切换

## 启动（唯一入口）

```bash
python <skill_dir>/start.py 短篇/{类型}/{项目名}/ [--resume|--advance|--finalize]
```

start.py 自动执行：
1. 字数门禁校验
2. 读状态文件确定当前进度
3. 输出当前状态和下一步指令

参数：

| 参数 | 用途 |
|------|------|
| （无） | 默认，校验字数 + 显示状态 |
| `--resume` | 续写，跳过字数门禁错误 |
| `--advance` | 子 agent 审查通过后，推进到下一章 |
| `--finalize` | 全篇终审通过后（≥95 分），标记定稿 |

## 参考书检查（写前必做）

```bash
python <skill_dir>/load_ref.py 短篇/{类型}/{项目名}/
```

## 完整流程（两个无限循环）

### 循环一：单章循环

```
查参考书 → 主 agent 写第N章（追加到 正文.md）
  → start.py（字数门禁）
    → 字数不够 → 继续写
    → 字数通过 → 状态变 in_review
  → 主 agent spawn 全新子 agent 做盲审（Task tool）
    → 子 agent 加载 shortstory-review，读正文，独立评分
    → 返回结构化结果（评分 + 阻断 + 建议）
  → 主 agent 读结果：
    → 有阻断 → 修改正文.md → 重跑 start.py → 字数通过 → in_review → 重新 spawn 子 agent
    → 零阻断 → start.py --advance → 推进到下一章 → 回到循环开头
```

**关键规则：**
- 主 agent 写，子 agent 审，**角色不能互换**
- 每次盲审 spawn **全新**子 agent，不复用，保证客观
- 阻断后修改正文.md，重跑 start.py（validate 自动将 blocking 推回 in_review）
- 禁止绕过脚本手动改状态

### 循环二：全篇终审循环

```
所有章节 passed → loop = final_review
  → start.py 显示"全篇终审"指令
  → 主 agent spawn 全新子 agent 做全篇盲审
    → 子 agent 读完整正文，六维度评分
    → 返回 {total_score, blocking, dimensions}
  → 主 agent 读结果：
    → 有阻断或总分 < 95 → 修改正文.md → 重跑 start.py
    → 零阻断且 ≥ 95 → start.py --finalize → 定稿
```

## 审查集成

子 agent 加载审查标准：

```bash
skill("shortstory-review")
```

然后依次读两份参考文件：
1. `shortstory-craft/references/writing-standards.md` — 工艺标准（句长、阻断基线）
2. `shortstory-review/references/review-dimensions.md` — 维度定义（两套标准：单章审 + 全篇终审）

**两阶段对应两套评分维度和权重：**

| 阶段 | 子 agent 审什么 | 维度 | 通过条件 |
|------|----------------|------|----------|
| 单章审 | 当前章节正文 | 信息增量/文笔/节奏/章末钩子/人设 | 零阻断 |
| 全篇终审 | 完整正文 | 开篇/情绪反转/闭环/人设/水文/结局 | 零阻断 **且** ≥95 分 |

**关键：评分与阻断分离**
- 阻断是硬红线（钩子、情绪标签、句长超标等），不因总分高赦免
- 阻断未消除前，任何分数都不能定稿

可用 `review_shortstory.py` 辅助统计（可选），但判定以子 agent 定性为准。

## 辅助脚本

| 脚本 | 功能 | 谁调 |
|------|------|------|
| `start.py` | 字数门禁 + 状态展示 + 状态推进 | 主 agent（入口） |
| `validate_chapter.py` | 字数校验 + 状态机流转 | start.py 自动 |
| `load_ref.py` | 加载参考书拆解（写前参考） | 主 agent（写前） |
| `review_shortstory.py` | 句长/统计辅助（可选） | 子 agent（可选） |

## 常见错误

- ❌ 子 agent 代笔写正文 → 主 agent 写，子 agent 只审
- ❌ 复用同一个子 agent → 每次 spawn 新的
- ❌ 手动改 write_status.json 跳过审查 → 只能通过脚本推进
- ❌ 80 分就定稿 → 全篇终审必须 ≥95 分
- ❌ 放水通过阻断 → 阻断就是阻断，不因总分高赦免
- ❌ 阻断和评分混为一谈 → 阻断先判，评分后算，互不覆盖
- ❌ 无关景物描写不算灌水 → 只有服务人物心境或主题的氛围段才算有效
