# DaisyWriter 快速上手 🚀

5 分钟写出你的第一章网文。

---

## 1. 安装

```bash
git clone https://github.com/ricky-theseus/DaisyWriter.git
cd DaisyWriter
```

在 OpenCode 中配置技能路径：

```json
// opencode.json
{
  "skills": ["path/to/DaisyWriter"]
}
```

## 2. 立项一个小说

在 AI 编程助手中输入：

```
/webnovel-init "我的修仙之旅"
```

技能会引导你完成交互式采访：
- 题材、规模、目标读者
- 主角（欲望、缺陷、弧光）
- 世界规则和力量体系
- 金手指类型

> **不必追求一次性完美** —— 充分性闸门会确保收集足够信息后才生成。

**输出：**
```
❖ 项目初始化完成 ❖
📁 我的修仙之旅/
├── 设定集/           # 世界设定
├── 大纲/总纲.md      # 总纲
├── .webnovel/state.json
└── .story-system/    # 故事合约
```

## 3. 规划第一卷

```
/webnovel-plan 1
```

生成：
- 卷节拍表（章节级节奏）
- 卷时间线（故事内时间）
- 逐章大纲（CBN、CPN、CEN）

## 4. 写第一章

```
/webnovel-write 1
```

全流程自动运行：
1. **前置检查** — 检查项目状态
2. **上下文 agent** — 构建写作简报（本章目标、前情、未解决线索）
3. **起草** — 写 2500-3500 字
4. **工艺扫描** — 运行 `prose_scanner.py` 量化质检
5. **审查** — 盲审 agent 检查问题
6. **润色并提交** — 修复问题、保存文件、记录指标

## 5. 审查和迭代

```
/webnovel-review 1
```

盲审检查：
- CBN/CEN 覆盖
- 与前章的连续性
- 角色语气一致性
- 节奏和信息密度

**阻断级问题**会暂停流程，由你决定如何处理。

## 6. 批量写更多章节

```
/webnovel-batch 2 30
```

批量写 2-30 章：
- 串行循环：写 → 审 → 过 → 下一章
- 断点续跑（崩溃后从上一通过章节继续）
- 进度持久化到 `stream_progress.json`

---

## 下一步

- 📖 [网文教程](guide-webnovel.md) — 12 个网文技能详解
- 📝 [短篇指南](guide-shortstory.md) — 写知乎盐选故事
- 💻 [技术博文指南](guide-tech.md) — 发表技术文章
- 🐛 [报告问题](https://github.com/ricky-theseus/DaisyWriter/issues)