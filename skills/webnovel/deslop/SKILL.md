---
name: webnovel-deslop
description: 网文去AI味。基于 7-Gate 检测+中文文学技法的系统性去AI流程。扫描→分级→逐门清除→复扫验证。
allowed-tools: Read Write Edit Grep Bash Agent
argument-hint: "<正文文件路径> [--check-only]"
---

# 网文去AI味 · webnovel-deslop

合并自 story-deslop（7-Gate 检测系统）+ chinese-novelist（AI 词汇黑名单、中文文学技法）+ webnovel-craft（prose_scanner.py 量化扫描）。

**核心信念：AI 味的主要问题并非语法错误，而是过度圆滑、工整、解释充分。改写目标是保留剧情功能，同时增加口语、停顿、跳跃和具体动作。**

## 核心原则

### 原则 1：改味优先，别当改错
AI味属于风格问题：过于书面化、对仗工整、面面俱到。目标是让文字回归具体、自然、可读。

### 原则 2：改最少，效果最大
能改一个词就不改一句，能删一句就不重写一段。没有问题的句子尽量保留原句。删除比例上限：轻度 ≤15%，中度 ≤25%，重度 ≤35%。

### 原则 3：保留创作意图
只改"怎么说"，不改"说什么"。剧情、人设、情节走向一概不动。不能删除伏笔、钩子、角色特征、关键信息或必要转折。

## 检测流程

### Phase 1：AI味扫描

运行量化扫描 + 7-Gate 关键词检测：

```bash
python -X utf8 "<webnovel-craft_skill_dir>/scripts/prose_scanner.py" "<正文文件>"
```

同时运行本 skill 自带的 AI 模式检测脚本（如部署了 node 环境）：

```bash
node scripts/check-ai-patterns.js --check <正文文件>
```

扫描结果标记 Gate A-G 问题位置，输出 AI味检测报告：

```
## AI味检测报告

### 整体评估
- AI味等级：{轻度/中度/重度}
- 主要问题：{1-3 个关键词}

### 问题标记
| 位置 | 类型 | Gate | 原文 | 问题 |
|------|------|------|------|------|
| 第X段 | 禁用词 | A | "眼中闪过一丝..." | 典型AI高频词 |
| 第Y段 | 句式 | B | "...，带着..." | AI惯用句式 |
| 第Z段 | 心理描写 | C | "他感到..." | 告诉而非展示 |
| 第M段 | 节奏 | D | 段段4-6句、长度均匀 | 整段同节奏 |
| 第P段 | 解释腔 | G | "她不知道的是…" | 叙述者跳出角色 |
```

### Phase 2：诊断与分级

| 程度 | 禁用词密度 | 特征 | 处理策略 |
|------|-----------|------|----------|
| 轻度 | ≤5/千字 | 少量禁用词，偶有书面腔 | 只过 Gate A + B |
| 中度 | 6-15/千字 | 多处禁用词+句式套路+心理描写抽象 | 过 Gate A+B+C+D+G |
| 重度 | >15/千字 | 全文明显，节奏/对话/结尾/解释腔均有问题 | 完整 7 Gate + 重点段落重写 |

综合判定规则：取六项指标（禁用词密度、连续排比段数、心理词占比、对话标签密度、平均段落句数、重复描写密度）的最高档位。

### Phase 3：逐门清除

#### 门禁 A：禁用词替换

加载 [references/banned-words.md](references/banned-words.md)，对照禁用词表逐项检查。替换规则：
- 禁用词 → 具体动作/细节描写
- 不能简单换成另一个形容词
- 要用"展示"替代"告诉"

白名单机制：项目根目录下的 `.deslop-whitelist` 定义豁免词汇（一行一个，`#` 开头为注释）。

#### 门禁 B：句式去套路

| 句式 | 替代方案 |
|------|----------|
| 否定铺垫后接肯定翻转 | 直接写后项，或改成动作/细节呈现 |
| "...，带着..." | 用独立短句或动作描写 |
| "仿佛/犹如/宛如/如同" | 口语化表达或白描 |
| 连续排比 | 保留 1-2 个，删掉其余 |
| 修饰词冗余 | 多余即删 |

#### 门禁 C：心理描写外化

直接陈述情绪 → 用行为展示："他很紧张"→"他的手在抖"。
同一信息/动作/情绪在相邻段重复 → 合并去重。

#### 门禁 D：节奏打碎

- 打断连续排比句
- 长句拆短句，偶尔用不完整句
- 段落长短交错
- 标点节奏跟语气走

#### 门禁 E：对话去腔调

- 加入口语化表达（"嗯""哦""行吧"）
- 适当打断对话，用动作穿插
- 删掉解释性对话
- 角色说话有差异

#### 门禁 F：结尾去升华

- 删掉总结性语句
- 用动作/场景收尾
- 结尾有"他知道..."→ 基本可以删

#### 门禁 G：去解释腔/上帝感

- 删解释因果：「之所以…是因为」「原来…」
- 删上帝视角剧透：「她不知道的是」「殊不知」
- 删替读者定性：「演得真好」「他就是这样薄情」

### Phase 3.5：复扫验证

```bash
python -X utf8 "<webnovel-craft_skill_dir>/scripts/prose_scanner.py" "<正文文件>"
node scripts/check-degeneration.js --check <正文文件>
node scripts/normalize-punctuation.js <正文文件>
```

### Phase 4：输出润色报告

```
## 去AI味润色报告

### 字数协议
- 原文字符数：{N0}
- 修订后字符数：{N1}
- 净变化：{N1 - N0}（{百分比}）
- 是否在比例上限内：{是/否}

### 修改统计
- 总修改数：{N} 处
- 禁用词替换：{N} 处
- 句式调整：{N} 处
- 修饰词清扫：{N} 处
- 心理外化：{N} 处
- 重复描写合并：{N} 处
- 节奏调整：{N} 处
- 对话优化：{N} 处
- 结尾修正：{N} 处
- Gate G 处理：{N} 处
```

## 参考资料

| 文件 | 何时加载 |
|------|----------|
| [references/banned-words.md](references/banned-words.md) | 检测和替换禁用词时 |
| [references/anti-ai-writing.md](references/anti-ai-writing.md) | 去AI味完整指南 |
| [scripts/normalize-punctuation.js](scripts/normalize-punctuation.js) | Phase 3.5 标点兜底 |
| [scripts/check-ai-patterns.js](scripts/check-ai-patterns.js) | Phase 1 预检与 Phase 3.5 复扫 |
| [scripts/check-degeneration.js](scripts/check-degeneration.js) | Phase 3.5 退化检测 |

## 流程衔接

| 时机 | 跳转到 | 命令 |
|------|--------|------|
| 去完AI味继续写作 | webnovel-write | `/webnovel-write N` |
| 发现结构问题 | webnovel-review | `/webnovel-review N` |
