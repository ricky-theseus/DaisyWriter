# 初始化收集对象（内部数据模型）

> `/webnovel-init` 在 Deep 采集阶段按本结构逐项收集信息；字段齐全并过「充分性闸门」后再执行 `webnovel.py init`。本文件是字段参考，不是执行脚本。

```json
{
  "project": {
    "title": "",
    "genre": "",
    "target_words": 0,
    "target_chapters": 0,
    "one_liner": "",
    "core_conflict": "",
    "target_reader": "",
    "platform": ""
  },
  "protagonist": {
    "name": "",
    "desire": "",
    "flaw": "",
    "archetype": "",
    "structure": "单主角"
  },
  "relationship": {
    "heroine_config": "",
    "heroine_names": [],
    "heroine_role": "",
    "co_protagonists": [],
    "co_protagonist_roles": [],
    "antagonist_tiers": {},
    "antagonist_level": "",
    "antagonist_mirror": ""
  },
  "golden_finger": {
    "type": "",
    "name": "",
    "style": "",
    "visibility": "",
    "irreversible_cost": "",
    "growth_rhythm": ""
  },
  "world": {
    "scale": "",
    "factions": "",
    "power_system_type": "",
    "social_class": "",
    "resource_distribution": "",
    "currency_system": "",
    "currency_exchange": "",
    "sect_hierarchy": "",
    "cultivation_chain": "",
    "cultivation_subtiers": ""
  },
  "constraints": {
    "anti_trope": "",
    "hard_constraints": [],
    "core_selling_points": [],
    "opening_hook": ""
  }
}
```

## 字段与采集步骤对应

| 字段组 | 对应 Step | 说明 |
|--------|-----------|------|
| `project.*` | Step 2 | 故事核与商业定位（书名/题材/规模/一句话/核心冲突/读者/平台） |
| `protagonist.*` | Step 3 | 主角骨架（姓名/欲望/缺陷/原型/结构） |
| `relationship.*` | Step 3 | 感情线与反派分层、镜像对抗 |
| `golden_finger.*` | Step 4 | 金手指类型、风格、可见度、不可逆代价、成长节奏 |
| `world.*` | Step 5 | 世界规模、力量体系、势力、阶层、货币、境界链 |
| `constraints.*` | Step 6 | 反套路、硬约束、核心卖点、开篇钩子 |

必填项以 SKILL.md 的「充分性闸门」为准；可空字段允许留空或填「无」。
