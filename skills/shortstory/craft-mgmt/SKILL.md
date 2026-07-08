---
name: shortstory-craft-mgmt
description: 短篇工艺约束管理。对话式查看/编辑/新建工艺约束。
allowed-tools: Read Write Edit Grep Bash Glob
---

# 短篇工艺管理

## 通用硬规则（继承自 craft.yaml base 类）

| 规则 | 说明 |
|------|------|
| 禁用词 | 35 个，含书面连接词、情绪套话、万能动词、总结体、叙述判断、第一人称AI套话 |
| 过渡词 | 9 个（日子一天天过去、时间过得很快、不知不觉、转眼间、就这样、没过多久、仿佛、终于、忽然），全文≤3处 |
| 禁用句式 | 5 种正则模式（否定前置、递进堆叠、虚假范围、三段式升华、否定对举） |
| 检查清单 | 38 项，覆盖结构/格式/禁用词/句式/开场/结尾/情感/节奏/细节/对话 |

> 单源真相：`短篇/工艺/约束体系/craft.yaml`。
> 项目级覆盖在 `工艺约束.md` 的 YAML 块中声明。

## 触发方式

| 用户说 | 对应动作 |
|--------|---------|
| "看一下工艺约束" | /craft show base |
| "加一个禁用词" | 对话确认词→`/craft edit global` |
| "新建一个约束子类" | /craft new <名称> --parent base |
| "看看我的项目和全局有什么差异" | /craft diff <项目路径> |

## 可用命令

### /craft list

列出所有约束类及其继承关系。

```bash
python 短篇/工艺/约束体系/craft_cli.py --list
```

### /craft show <类名|项目路径>

显示指定的约束（含继承链合并）。

**查看全局约束：**

```bash
python 短篇/工艺/约束体系/craft_cli.py --natural base
```

**查看项目级约束（含覆盖）：**

```bash
python 短篇/工艺/约束体系/craft_cli.py --natural base --with-project <项目路径>
```

### /craft edit global

编辑全局 `craft.yaml`。

```bash
Read 短篇/工艺/约束体系/craft.yaml
```

对话引导用户指定修改内容（追加禁用词、改字数范围、加检查项等），然后：

```bash
# 追加禁用词
python 短篇/工艺/约束体系/craft_cli.py --add-banned "突然"

# 直接编辑 YAML（适用复杂改动）
Edit 短篇/工艺/约束体系/craft.yaml
```

修改确认后，可通过以下命令验证格式：

```bash
python 短篇/工艺/约束体系/craft_cli.py --list
python 短篇/工艺/约束体系/craft_cli.py --natural base
```

### /craft edit <项目路径>

编辑项目级 `工艺约束.md`。

```bash
Read <项目路径>/工艺约束.md
```

对话引导用户指定覆盖内容（如追加本项目的禁用词、调整字数范围），在文件的 YAML 块中修改。

```yaml
# 示例：在项目的 工艺约束.md 的 YAML 块中追加
custom_rules:
  banned_words:
    add:
      - "突然"
  rules:
    scene:
      max_words: 400
```

### /craft new <名称> --parent base

新建一个工艺约束子类（适用于需要高度自定义的项目）。

对话引导用户输入：
1. 显示名称
2. 说明
3. 父类（默认 base）
4. 硬铆钉（人称、视角）
5. 格式规则（对话符号、段落句数、场景字数）
6. 检查清单追加项

新建完成后自动验证：

```bash
python 短篇/工艺/约束体系/craft_cli.py --list
python 短篇/工艺/约束体系/craft_cli.py --natural <新名称>
```

### /craft diff <项目路径>

显示项目级覆盖与全局约束的差异。

```bash
# 读取全局约束
python 短篇/工艺/约束体系/craft_cli.py --natural base

# 读取项目级约束（含覆盖）
python 短篇/工艺/约束体系/craft_cli.py --natural base --with-project <项目路径>

# 对比
Read <项目路径>/工艺约束.md  # 查看 YAML 覆盖块中的 custom_rules
```

输出差异说明（LLM 分析对比结果）。

### /craft reset <类名>

将指定约束类恢复为默认值。

```bash
Read 短篇/工艺/约束体系/craft.yaml
```

删除该类的自定义条目（如果是从其他地方拷贝的非标准内容），恢复为 clean 版本。

## 使用流程示例

**场景：用户想加一个禁用词**

```
用户：帮我加一个禁用词"突然"

Agent: 确认想加在全局还是某个项目？
用户：全局

Agent: 执行
  python 短篇/工艺/约束体系/craft_cli.py --add-banned "突然"
  → "突然" 已加入所有约束类的禁用词列表
  → 下次任何 shortstory skill 触发时自动生效
```

**场景：用户想新建一个约束子类**

```
用户：新建一个带特殊规则的约束类

Agent: 对话收集规则信息...
  - 父类？ base
  - 人称？ 第一人称
  - 对话符号？ 「」
  - 场景字数范围？ 200-500
  - ...

  写入 craft.yaml → 验证通过
  → 后续项目可继承此类
```
