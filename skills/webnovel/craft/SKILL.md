---
name: webnovel-craft
description: 写作工艺强约束层。句长、句式、节奏、感官、情绪等跨书通用写作质量标准，扫描脚本 + 工艺手册。所有新书继承，写章/审查时强制执行。
allowed-tools: Read Bash
argument-hint: "[--scan <chapter_path>]"
---

# 写作工艺约束

## 加载规则

- `webnovel-write`：Step 2 起草前必读 `references/writing-standards.md`，Step 3 必跑 `scripts/prose_scanner.py`
- `webnovel-review`：加载本技能作为品味审查的量化基准
- `webnovel-batch`：每章 agent prompt 内联核心约束摘要
- 任何 `webnovel-write` 或 `webnovel-review` 会话均须加载本技能

## 运行扫描脚本

```bash
python -X utf8 "<skill_dir>/scripts/prose_scanner.py" "<章节正文路径>"
```

输出 JSON 到 stdout，字段：
- `avg_sentence_len`：平均句长
- `very_short_pct`：极短句占比（≤8字）
- `long_pct`：长句占比（>30字）
- `issues`：违规清单，每项含 `check`、`value`、`limit`、`severity`
- `blocking_count`：阻断级问题数

## 质量门禁

| 指标 | 标准 | 阻断 |
|------|------|:---:|
| 平均句长 | 30-55 字 | <25 或 >55 |
| 极短句占比 | ≤15% | >15% |
| 长句占比 | ≥30% | — |
| 不是A是B句式 | ≤3/章 | >3 |
| 身体部位拟人 | ≤4/章 | >4 |
| 哲理收束句 | ≤2/章 | >2 |
| 情绪标签词 | 0 | >0 |
| 副词修饰情绪 | 0 | >0 |
| 连续同主语开头 | ≤2 | >2 |

## 参考文件

- `references/writing-standards.md`：完整工艺手册（句长校准逻辑、豆包专家维度、审查策略、阈值制定理由）
- `scripts/prose_scanner.py`：量化扫描脚本
