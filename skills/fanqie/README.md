# fanqie-publisher

[![Release](https://img.shields.io/github/v/release/amm10090/fanqie-publisher-skill?display_name=tag&style=flat-square)](https://github.com/amm10090/fanqie-publisher-skill/releases/tag/v0.1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](./LICENSE)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue?style=flat-square)](./SKILL.md)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-45ba4b?style=flat-square)](https://playwright.dev/)

> 一个面向 OpenClaw 的番茄小说发布 Skill：把本地 Markdown 章节转成可重复执行的作者后台发布流程，覆盖单章发布、批量发布、平台原生定时发布与发布后状态校验。

## 简介

`fanqie-publisher` 是一个以 **OpenClaw Skill** 形式组织的自动化项目，核心目标是把“本地章节文件 → 番茄作者后台发布”这条重复操作流程工具化。

它不是番茄官方 SDK，也不是公开 API 封装，而是基于浏览器自动化的实战方案，适合希望保留平台原生发布链路、又想减少重复手工操作的人使用。

## 适用场景

适合：

- 已经有结构化的章节 Markdown 文件
- 希望减少作者后台重复填表操作
- 接受浏览器自动化方案
- 希望同时支持立即发布与平台原生定时发布
- 希望发布后自动核对章节管理页状态

不适合：

- 依赖官方开放 API 的场景
- 无法提供可接管浏览器环境的场景
- 追求完全无 UI、纯接口式调用的场景

## 当前能力

目前已经实现或验证过的能力：

- 解析本地 Markdown 章节文件
- 自动拆分章节号与章节标题
- 自动填写番茄章节编辑器
- 单章立即发布
- 批量立即发布
- 使用番茄后台原生“定时发布”创建待发布章节
- 发布后跳转章节管理页进行状态校验
- 通过 Playwright + CDP 接管已有浏览器会话
- 支持安全模式（只填充 / 只走到最终发布弹窗）
- 增加疑似单日 5 万字发布上限的保护阈值

## 项目结构

```text
fanqie-publisher/
├── SKILL.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── scripts/
│   ├── prepare_chapters.py
│   ├── login_fanqie.js
│   ├── publish_fanqie.js
│   └── state.py
├── references/
│   ├── workflow.md
│   ├── selectors.md
│   ├── data-format.md
│   └── recon-notes-2026-03-12.md
├── package.json
└── .gitignore
```

## 核心脚本

### `scripts/prepare_chapters.py`

负责读取章节目录中的 Markdown 文件，并输出结构化章节数据。

当前默认支持的格式特征：

- 一个 `.md` 文件对应一章
- 标题通常位于第一行 Markdown 标题中
- 形如 `第001章 标题` 的标题会自动拆成：
  - 章节号：`1`
  - 标题：`标题`

### `scripts/login_fanqie.js`

负责连接浏览器、识别未登录状态、切到二维码登录并保存登录态。

当检测到需要扫码时，会额外输出机器可读事件：

- `QR_READY:/abs/path/to/login-qr.png`
- `LOGIN_OK`
- `LOGIN_ALREADY_OK`
- `LOGIN_TIMEOUT`

并在标准输出中包含一段可供 OpenClaw 转发的 `MEDIA:` 回复块。

### `scripts/login_fanqie_notify.js`

这是一个轻量包装器，用来运行 `login_fanqie.js`，并把关键结果整理成 JSON，便于上层编排逻辑读取：

- 是否成功登录
- 二维码图片路径
- 可直接发送到聊天渠道的 `mediaReply`

适合场景：

- 本地有图形浏览器
- 或在 WSL 中通过 CDP 接管 Windows 浏览器
- 登录态过期，需要重新扫码

当前会在需要扫码时自动把二维码截图保存到 `state/login-qr.png`。

另外已加入二维码失效检测：优先读取页面文本判断是否出现“二维码已失效 / 点击刷新”等提示；如果系统安装了 `tesseract`，还会对登录面板截图做 OCR 兜底检测，并在需要时自动尝试刷新二维码。

### `scripts/publish_fanqie.js`

主发布脚本，负责：

- 优先复用正确的番茄 writer 页面，并自动收敛多余 writer 标签
- 当 remote 浏览器未运行时，自动尝试恢复 Windows Chrome 9222 会话
- 打开章节编辑页
- 自动检测登录态是否失效
- 失效时切到二维码登录并等待重新扫码
- 自动填充标题 / 正文
- 处理中间拦截弹窗
- 进入最终发布弹窗
- 立即发布或定时发布
- 发布后去章节管理页校验状态
- 对页面漂移、最终弹窗未稳定关闭、短暂验证失败等可恢复问题自动重试一次

## 使用方式

### 1）预览章节解析结果

```bash
python3 scripts/prepare_chapters.py --dir "/path/to/chapters" --preview
```

### 2）保存登录态

如果通过 CDP 接管已有浏览器：

```bash
node scripts/login_fanqie.js --cdp http://127.0.0.1:9222
```

如果你希望上层自动读取二维码路径和可发送附件内容：

```bash
node scripts/login_fanqie_notify.js --cdp http://127.0.0.1:9222
```

### 3）单章安全填充（不发布）

```bash
node scripts/publish_fanqie.js \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapter.md" \
  --mode immediate \
  --fill-only
```

### 4）单章立即发布

```bash
node scripts/publish_fanqie.js \
  --cdp http://127.0.0.1:9222 \
  --file "/path/to/chapter.md" \
  --mode immediate \
  --confirm-publish
```

### 5）批量立即发布

```bash
node scripts/publish_fanqie.js \
  --cdp http://127.0.0.1:9222 \
  --dir "/path/to/chapters" \
  --start-from "第018章" \
  --limit 3 \
  --mode immediate \
  --confirm-publish
```

### 6）使用番茄后台原生定时发布

```bash
node scripts/publish_fanqie.js \
  --cdp http://127.0.0.1:9222 \
  --dir "/path/to/chapters" \
  --start-from "第018章" \
  --limit 3 \
  --mode scheduled \
  --schedule-at "2026-03-13 21:00" \
  --schedule-step-minutes 30 \
  --confirm-publish
```

## 已知平台限制

### 1）疑似单日发布字数上限

根据真实后台行为推断，番茄存在一个大约 **50,000 字 / 日** 的实际发布上限。

> 这是基于后台提示和真实操作经验的安全阈值，**不是当前 README 中引用的官方文档结论**。

脚本中已加入保护参数：

- `--daily-limit-chars`
- `--already-published-chars`

### 2）定时发布的修改锁窗

如果后台提示：

```text
请在发布时间前30分钟提交修改内容，否则无法完成修改
```

应当视为：

- 该定时章节在接近发布时间时基本无法可靠修改
- 定时发布时间应尽量一次设置正确
- 不要假设临近发布时间还能安全调整内容或时间

### 3）平台前置拦截弹窗

在点击“下一步”后，番茄后台可能出现多层中间弹窗，例如：

- 内容风险检测
- 错别字智能纠错
- 提交确认提示
- 编辑器版本冲突提示
- 引导浮层

这些拦截层会影响自动化稳定性，因此需要持续维护 selector 与处理逻辑。

## 安全与隐私

本仓库**不应提交**以下内容：

- 登录态文件
- 浏览器会话数据
- 后台截图
- 页面勘测产物
- `node_modules`
- 临时状态文件

这些内容应留在本地，并通过 `.gitignore` 排除。

## 当前状态

当前版本已经可以完成真实发布流程，但仍依赖：

- 页面结构相对稳定
- 本地浏览器可接管
- 对番茄后台交互细节的持续维护

## 后续方向

- 更稳的页面选择与恢复策略
- 更稳的章节管理页状态解析
- 对“已排定时章节”的修改流程支持
- 更精细的错误分类和恢复策略
- 对更多弹窗/异常态的覆盖

## 许可证

本项目采用 [MIT License](./LICENSE)。
