---
name: webnovel-review-settings
description: 设定集审核专家。深度检查世界观、力量体系、角色、势力、经济、历史、创意约束等设定文件的质量与自洽性，输出问题清单。
allowed-tools: Read Grep Bash Edit Write Agent AskUserQuestion
argument-hint: "[--quick] [--scope worldview|power|character|faction|economy|all]"
---

# 设定集审核 (Setting Review Expert)

## 目标

逐文件、逐维度检查项目设定集的质量与自洽性，输出结构化问题清单。不评分，只找问题 + 给修复方向。

## 原则

1. 只读审核，不修改设定文件（除非用户明确要求）。
2. 每条问题必须有证据（引用设定原文），不凭感觉。
3. 问题按维度分组，标注严重度（阻断/高/中/低）。
4. 无问题也显式声明"该维度通过"。

## 执行流程

### Step 1：解析项目根 + 加载设定文件

```bash
export WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-${OPENCODE_PROJECT_DIR:-$PWD}}"
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${OPENCODE_PLUGIN_ROOT:-}}"
export SCRIPTS_DIR="${CLAUDE_PLUGIN_ROOT}/scripts"
export PROJECT_ROOT="$(python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" where 2>/dev/null || echo "${WORKSPACE_ROOT}")"
```

确认设定集目录存在：
```bash
Get-ChildItem -LiteralPath "${PROJECT_ROOT}/设定集" -Name
```

### Step 2：逐文件加载设定

必须读取的设定文件（根据 `--scope` 过滤）：
- `世界观.md` — always
- `力量体系.md` — always
- `主角卡.md` — always
- `反派设计.md` — always
- `行文约束集.md` — if exists
- `女主卡.md` — if exists
- `主角组.md` — if exists (多主角)
- `大纲/总纲.md` — 创意约束对齐用
- `.story-system/MASTER_SETTING.json` — 调性/禁忌参照
- `.webnovel/idea_bank.json` — 创意约束来源

### Step 3：逐维度审核

详见 `references/setting-review-dimensions.md`。核心维度：

| 维度 | 检查要点 |
|------|---------|
| **世界观自洽性** | 物理法则无矛盾、地理-历史-社会逻辑链完整、核心规则不可绕过 |
| **力量体系完整性** | 境界有战力参照、代价明确、越级规则清晰、漏洞有解释 |
| **角色设定深度** | 欲望→缺陷→弧线对齐、OOC警戒合理、关系网无遗漏 |
| **势力格局合理性** | 各方有动机非标签化、平衡有制衡因素、关系表自洽 |
| **经济与资源** | 货币锚定物明确、购买力稳定、稀缺性规则成立 |
| **时间线逻辑** | 关键节点有日期、因果链连续、无时序矛盾 |
| **创意约束落地** | 反套路规则已写入设定、硬约束不可绕过、卖点不空泛 |
| **行文约束与设定一致性** | 行文约束与世界观/角色匹配，不冲突 |

### Step 4：输出问题清单

```markdown
## 设定集审核报告

项目：{project_name}
审核时间：{timestamp}
审核范围：{scope}

### 通过项（无问题）
- 世界观自洽性：通过
- ...

### 问题清单

#### [阻断] 问题标题
- 文件：设定集/xxx.md 第N行
- 证据：原文引用
- 问题：具体矛盾/缺失点
- 修复方向：建议的修改方案

#### [高] ...
#### [中] ...
#### [低] ...

### 审核总结
N个阻断 / M个高优 / K个中低优
```

## 严重度定义

| 级别 | 定义 |
|------|------|
| 阻断 | 逻辑矛盾会导致写作卡死或读者出戏（如战力体系自毁、核心规则被绕过后无解释） |
| 高 | 明显漏洞，写作中大概率触发（如货币购买力忽高忽低、角色动机链断裂） |
| 中 | 潜在隐患，边缘场景触发（如某个配角关系未定义、边境地名未交代） |
| 低 | 完善性建议（如可补充日常物价参考、可增加一个历史事件） |

## 快速模式 (`--quick`)

只检查阻断级和高优问题，跳过中低优完善性建议。`--scope` 可指定单维度如 `worldview`。

## 与 webnovel-init 集成

`webnovel-init` 在 Step 7（最终确认）之后、执行生成之前，可调用本技能对已收集的设定做审核。

调用方式：在 init 流程中，收集完所有设定后，触发：

```text
设定已收集完毕，接下来由设定审核专家做最终质检：
/webnovel-review-settings --quick
```

审核通过（无阻断）→ 进入执行生成。
审核未通过（有阻断）→ 展示问题，让用户选择：修改后重审 / 跳过继续生成 / 中断。

## 作者友好最终报告契约

最终回复必须面向作者，不输出原始 JSON 或长命令日志。使用固定三段式：

```text
设定审核结果：{通过 | 发现N个问题}

一、通过项
- ...

二、问题清单（按严重度排序）
- [阻断] ...
- [高] ...
- [中] ...
- [低] ...

三、建议
- 阻断问题必须修复后才能进入写作，否则会导致……
- 高优问题建议规划阶段补全
- 可执行命令：/webnovel-plan 1 开始规划第一卷
```
