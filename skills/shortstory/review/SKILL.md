---
name: shortstory-review
description: 短中篇盲审指南。分单章审和全篇终审两阶段，子 agent 按调用场景切换标准和输出格式。
allowed-tools: Read Bash
argument-hint: "[项目路径，如 短篇/悬疑民俗/xxx] [--final]"
---

# 短中篇盲审

## 加载工艺标准

```bash
cat <skill_dir>/../shortstory-craft/references/writing-standards.md
```

## 加载审查维度

```bash
cat <skill_dir>/references/review-dimensions.md
```

## 两阶段判断

审查维度定义文件包含两套标准：

| 场景 | 调用方式 | 适用阶段 |
|------|----------|----------|
| 单章审 | `skill("shortstory-review")` | 循环一：每写完一章 |
| 全篇终审 | `skill("shortstory-review")` + `--final` 参数 | 循环二：所有章通过后 |

**单章审** — 读当前章节内容，按单章审维度打分（信息增量/文笔/节奏/章末钩子/人设）。阻断消除即通过，不设分数门槛。

**全篇终审** — 读完整正文，按全篇终审维度打分（开篇/情绪/闭环/人设/水文/结局）。阻断消除 **且** ≥95 分才能定稿。

## 执行流程

1. 判断是单章审还是全篇终审
2. 读对应范围的正文
3. 对照阻断清单逐条检查。有任意阻断 → status = "blocking"
4. 按对应阶段的维度逐项打分（0–10，定性判断）
5. 加权计算总分
6. 按对应阶段输出 JSON

## 阻断

阻断是硬红线。阻断未消除之前，即使总分 98 也不能通过。

## 辅助统计（可选）

```bash
python <skill_dir>/review_shortstory.py 短篇/{类型}/{项目名}/
```

输出句长/极短句占比/情绪标签词等，可作为判断参考。
