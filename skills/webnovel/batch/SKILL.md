---
name: webnovel-batch
description: 批量写章。从指定章节起自动逐章生成至指定结束章（默认卷末），单章撰写agent + 单章审查agent，严格串行（写→审→过→写下一章）。默认批量入口。
allowed-tools: Read Write Edit Grep Bash Agent AskUserQuestion
argument-hint: "N [M]（从第N章起批量至第M章，省略M则写至卷末）"
---

# 批量写章

## 核心原则

**写章agent和审查agent不能是同一个。写章agent负责产出，审查agent负责把关，互不越界。**

审查agent的职责是**验证**，不是创新。它的判断基准只有三个：
1. 这章有没有做到它该做的事？（CBN/CEN是否全覆盖？章纲目标是否达成？）
2. 有没有做了它不该做的事？（禁区是否踩到？设定是否被破坏？行文约束是否违反？）
3. 前后衔接断没断？（上一章钩子是否承接？这一章钩子是否指向下一章起始状态？）

**回答「是」→ 通过。回答「否」→ blocking，标记具体问题，退回重写。** 审查agent不提替代方案、不"建议加个伏笔"、不管下一章怎么写。越界建议直接忽略。

## 架构

```
主对话（串行循环，同步）
│
├─ ① 写进度文件 .webnovel/stream_progress.json
│
└─ for N in [start_chapter..end_chapter]:
    │
    ├─ ② 派发单章撰写agent(N)
    │      prompt 内联：章纲全文 + 设定块 + 行文约束
    │      agent 自行执行：context→起草→自审→润色→commit
    │      返回 {chapter, status, word_count, summary}
    │
    ├─ ③ 等待写章agent返回
    │
    ├─ ④ 派发单章审查agent(N)  — 这是独立于写章agent的调用
    │      prompt 内联：第N章章纲 + 审查三问
    │      agent 执行：Read正文 → 对照章纲/设定/约束审查 →
    │      返回 {chapter, passed:true|false, blocking_items:[], issues:[]}
    │
    ├─ ⑤ 读审查结果
    │      │
    │      ├─ passed=true → 更新进度，N+1
    │      │
    │      ├─ passed=false, blocking_items可修复 →
    │      │   重派写章agent(N) 重写（最多2次重试）
    │      │
    │      └─ passed=false, blocking_items不可修复 →
    │           标记 failed，暂停循环，提示用户
    │
    └─ 用户随时 Ctrl+C → 下次启动读 stream_progress.json 从 current 继续
```

**为什么不用持久/后台审查agent：** 当前工具不支持 daemon 进程。审查agent每次以单次 Task 调用执行，完成即退出。效果一样——每章都有独立第三方把关——且更简单可靠。

## 文件即 IPC

| 文件 | 写入方 | 读取方 | 内容 |
|------|--------|--------|------|
| `stream_progress.json` | 主对话 | 主对话 | `{chapters:[], completed:N, failed:N, current:N, status}` |

只用这一个文件。审查结果不写队列，直接在主对话中持有关闭审查agent的返回。

## 执行流程

### 0. 预检

确认必要文件存在：
- `大纲/第{卷号}卷-详细大纲.md`
- `设定集/世界观.md`
- `设定集/力量体系.md`
- `设定集/主角卡.md`
- `.webnovel/state.json`

### 1. 读取章纲

从 `大纲/第{卷}卷-详细大纲.md` 解析第 N 章到第 M 章的章纲范围。每章提取：目标/阻力/代价/CBN/CPNs/CEN/禁区/钩子/时间锚点。

### 2. 串行循环

```
for N in [start_chapter..end_chapter]:
```

#### 2a. 写章agent(N)

派发一个 Task(general)，prompt 包含：

```
撰写第{N}章"{章名}"正文。

项目根：{PROJECT_ROOT}

本章章纲（内联，不重读文件）：
目标：{}
阻力：{}
代价：{}
CBN（必须出现的节点）：{}
CPNs（可选节点）：{}
CEN（章节结束状态，必须达成）：{}
禁区（绝不能出现）：{}
钩子到下一章：{}
时间锚点：{}

上章收尾：{上一章最后一段摘要}

设定块（内联）：
- 行文约束：句长30-55字、段落≤7句、触觉>听觉>视觉、无情绪标签词、无副词修饰情绪动词、不是A是B≤3次、身体拟人≤4次、哲理收束≤2次
- 世界观：{关键设定摘要}

执行：起草→自审（对照章纲）→润色→保存到 正文/第{四位数}章-{章名}.md

返回：{"chapter":N, "status":"accepted", "word_count":N, "summary":"..."}
```

写章agent返回后，**不要推进进度**。

#### 2b. 审查agent(N)

派发一个新的 Task(general)，prompt 包含：

```
独立审查{book_name}第{N}章"{章名}"。

先 Read 以下基准文件：
- 大纲/第{卷}卷-详细大纲.md（只看本章章纲）
- 设定集/世界观.md
- 设定集/力量体系.md
- 设定集/主角卡.md

然后 Read 正文：正文/第{四位数}章-{章名}.md

审查三问，逐问回答 yes/no，no 必须列出具体位置和原因：

Q1: CBN 是否全部出现？CEN 是否达成？
    列出每个CBN是否覆盖，CEN状态是否达成。
     若否 → blocking_item: "CBN未覆盖：{具体节点}"

Q2: 禁区是否被触犯？设定是否被破坏？
    检查禁区列表，每条逐一确认未出现。
    检查是否有与世界观/力量体系/角色卡片矛盾的描写。
     若否 → blocking_item: "禁区触犯：{具体内容}"

Q3: 与上一章的钩子是否衔接？与下一章章纲要求的起始状态是否一致？
    检查本章开头是否自然承接上章结尾。
    检查本章结尾钩子是否与下一章章纲目标兼容。
     若否 → blocking_item: "衔接断裂：{具体问题}"

**审查agent不提出替代方案。** 只回答三问。发现 blocking 列问题即可。

返回：{"chapter":N, "passed":true|false, "blocking_items":[], "issues":[]}
```

#### 2c. 验收

审查agent返回后：

- `passed=true` → 更新 `stream_progress.json`，标记 completed，current=N+1，写入磁盘。继续下一章。
- `passed=false`，有 blocking_items → 判断是否可修复（写章agent重写是否能解决）。可修复 → 回到 2a 重写本章（最多2次）。不可修复 → 标记 failed，暂停循环，提示用户。

**关键：审查agent不通过，绝不派发下一章。**

### 3. 断点续跑

`stream_progress.json` 结构：

```json
{
  "volume": 1,
  "start_chapter": 11,
  "end_chapter": 20,
  "chapters": [
    {"N": 11, "status": "completed", "word_count": 2340},
    {"N": 12, "status": "pending", "word_count": 0}
  ],
  "current": 12,
  "completed": 1,
  "failed": [],
  "status": "running"
}
```

重新运行时先读此文件，从 `current` 继续。跳过已 completed 的章节。

## 硬规则

- **写章agent和审查agent永远是两次独立的 Task 调用，禁止合并**
- **审查不通过不写下一章，绝无例外**
- 审查agent禁止提替代方案、禁止建议创新、禁止越过三问回答任何额外内容
- blocking 不可修复时暂停，不静默跳过
- 进度文件实时更新，每次通过一章立即写盘
