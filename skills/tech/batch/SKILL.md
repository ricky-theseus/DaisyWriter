---
name: tech-batch
description: 批量生产内容。外层循环按计划调度条目，内层循环走产→审→改→再审直到零问题。产和审由不同 agent 完成。
allowed-tools: Read Write Edit Grep Bash Agent
argument-hint: "[项目目录]"
---

# 批量生产流水线

## 核心原则

**产 agent 和审 agent 不能是同一个。** 产 agent 负责产出内容，审 agent 负责质量把关。

**审 agent 每次调用都是新的子 agent 调用，不带历史上下文**——真正做到双重验证，不依赖前一次的判断。

## 二层架构

```
外层循环（调度器）
┌────────────────────────────────────────────────────┐
│  read 计划文件 → 解析条目标清单                     │
│  for each item in plan:                            │
│    if item.completed → skip                        │
│    dispatch 内层循环(item)                         │
│    collect result                                  │
│    update progress                                 │
└────────────────────────────────────────────────────┘

内层循环（产审循环）
┌────────────────────────────────────────────────┐
│  产 agent（产出初稿）                           │
│    → 按 item 配置加载素材/参考/规范             │
│    → 产出 → 保存到 {output_dir}                │
└──────────┬─────────────────────────────────────┘
           ▼
┌────────────────────────────────────────────────┐
│  审 agent（盲审，无上下文记忆）                 │
│    → 只读产出物                                 │
│    → 按审查标准逐项检查                         │
│    → 返回 {passed, blocking}                   │
└──────────┬─────────────────────────────────────┘
      ┌────┴────┐
      ▼         ▼
   passed    not passed
      │         │
      │         └──→ 产 agent 修改
      │                → 逐条处理 blocking
      │                → 保存修改
      │                → 回到审 agent
      │
 ┌────┴────┐
 ▼
标记 completed
```

## 计划文件格式

计划文件定义一批生产条目。路径由外层循环指定。

```yaml
# plan.yaml 示例
project: "AI Agent 框架生态篇"
output_root: "博文/AI/Agent/草稿"
reference_root: "博文/参考文章/Agent"

items:
  - id: "langchain-lcel"
    title: "LangChain LCEL 核心模式与组合"
    produce_prompt: >
      写一篇 LangChain LCEL 的技术文章。
      风格：概念速查 → 底层原理 → 架构设计原则。
      包含 Mermaid 图 + 可运行代码。
    review_questions:
      - "字数 ≥ 800？"
      - "结构是否三段齐全？"
      - "Mermaid 图独立代码块、无嵌套 subgraph？"
      - "代码可复制、版本号/API 明确？"
      - "无面试八股、无博文关联、无下一篇引导？"
    references:
      - "LangChain/LangChain_WanZheng_JiaoCheng"
      - "LangChain/LangChain_Agent_ReAct"

  - id: "crewai-core"
    title: "CrewAI 核心概念"
    ...
```

计划文件与内层循环的审查标准解耦。每个条目可以定义不同的 `review_questions`，外层循环不需要知道具体审查什么，只负责调度流转。

## 内层循环：产审循环

### 产 agent

- 接收 item 配置（title, produce_prompt, references, format_guidelines）
- 加载参考素材
- 产出内容并保存到 `{output_root}/{id}.md`
- 返回 `{id, status: "produced", word_count}`

### 审 agent（盲审）

- **只读产出物，不带历史上下文**
- 按 item 的 `review_questions` 逐条回答 yes/no
- no 必须指出具体位置
- 全部 yes → passed。任意 no → blocking

### 循环

审不过 → 产 agent 按 blocking 逐条修改 → 保存 → 调审 agent（新调用） → 再审，直到零 blocking 才退出。

不设重试上限。审不过是流程的一部分，不是异常。

## 进度文件

每完成一条实时写入 `batch_progress.json`：

```json
{
  "project": "AI Agent 框架生态篇",
  "plan": "series_plan.md",
  "items": [
    {"id": "langchain-lcel", "status": "completed", "review_rounds": 2},
    {"id": "crewai-core", "status": "pending", "review_rounds": 0}
  ],
  "current": 0,
  "completed": 1,
  "failed": [],
  "status": "running"
}
```

中断后重新运行时读进度文件，跳过已 completed 的条目。

## 硬规则

- **产 agent 和审 agent 永远是两次独立的 Task 调用**
- **审 agent 每次调用不带历史上下文（盲审）**
- **审不通过不进下一个条目，不设重试上限**
- 审 agent 不提替代方案，只按问题逐条回答
- blocking 不可修复时暂停提示用户
- 进度文件每完成一条实时更新
