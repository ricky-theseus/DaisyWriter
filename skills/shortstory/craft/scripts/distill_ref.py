#!/usr/bin/env python3
"""
短篇参考书蒸馏脚本。

读取 短篇/参考书/{类型}/{每本书}/ 的拆解数据，
输出：
  1. 每本书 → 短篇参考卡.md（300-400字浓缩卡）
  2. 每个类型 → 类型总结.md（跨书模式聚合）

用法:
  python distill_ref.py                            # 蒸馏所有类型
  python distill_ref.py 言情                        # 仅蒸馏言情
  python distill_ref.py 言情 悬疑                   # 蒸馏指定多个类型
"""
import io, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 短篇参考书根目录（从脚本位置上溯到 D:\Writer）
ROOT = Path(__file__).resolve().parents[4] / '短篇' / '参考书'


# ── 柔性字段读取 ──

def get_field(obj, *names):
    """从 obj 中取第一个存在的字段，支持嵌套如 'structure.hook'"""
    for name in names:
        parts = name.split('.')
        cur = obj
        for p in parts:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                cur = None
                break
        if cur is not None:
            return cur
    return None


def get_field_str(obj, *names, fallback=''):
    v = get_field(obj, *names)
    return str(v) if v else fallback


def get_field_list(obj, *names):
    for name in names:
        v = get_field(obj, name)
        if isinstance(v, list) and len(v) > 0:
            return v
    return []


def read_json_safe(path):
    try:
        data = json.loads(path.read_text('utf-8'))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return None


def read_text_safe(path):
    try:
        return path.read_text('utf-8')
    except (FileNotFoundError, UnicodeDecodeError):
        return ''


# ── 卡提取函数 ──

def extract_hook_technique(data, report_text):
    """提取钩子手法"""
    # 先找 JSON 中的 hook.technique
    t = get_field_str(data, 'hook.technique', 'hook.technique', 'opening_hook.technique')
    if t:
        return t

    # 从报告中提取
    for line in report_text.split('\n'):
        line_lower = line.lower()
        for kw in ['身份反转', '意外撞见', '危机开场', '金句', '反常情境',
                    '震撼对话', '倒计时', '身份反转', '意外撞见']:
            if kw in line:
                return kw
    return '未提取'


def extract_one_liner(data, report_text):
    """提取一句话钩子"""
    ol = get_field_str(data, 'hook.one_liner', 'hook.one_liner',
                        'hook.hook', 'opening_hook.content', 'opening_hook.text')
    if ol and len(ol) > 5:
        return ol

    # 从报告"开场钩子分析"章节提取
    lines = report_text.split('\n')
    for i, line in enumerate(lines):
        if '开场钩子' in line or '钩子手法' in line or '一句话钩子' in line:
            for j in range(i, min(i + 5, len(lines))):
                if '：' in lines[j] or ':' in lines[j]:
                    candidate = lines[j].split('：', 1)[-1].split(':', 1)[-1].strip()
                    if len(candidate) > 10:
                        return candidate
    return '未提取'


def extract_structure_acts(data):
    """提取结构幕信息"""
    acts = get_field_list(data, 'structure.acts', 'acts', 'phases', 'segments')
    if acts:
        return acts
    return []


def extract_characters(data):
    """提取角色信息"""
    chars = get_field_list(data, 'characters', 'character', '人物表', 'roles')
    if not chars:
        return []
    result = []
    for c in chars:
        if isinstance(c, str):
            result.append(c)
        elif isinstance(c, dict):
            name = c.get('name') or c.get('角色') or c.get('关系') or ''
            role = c.get('role') or c.get('关系') or c.get('type') or ''
            archetype = c.get('archetype') or c.get('标签') or ''
            if isinstance(archetype, list):
                archetype = '/'.join(archetype)
            trait = c.get('trait') or c.get('核心动机') or ''
            parts = []
            if name:
                parts.append(name)
            if role:
                parts.append(f'（{role}）')
            if archetype:
                parts.append(f'→ {archetype}')
            if parts:
                result.append(''.join(parts))
        elif isinstance(c, (list, tuple)):
            result.append(str(c[0]) if c else '')
    return result


def extract_patterns(data):
    """提取可借鉴模式"""
    return get_field_list(data, 'patterns', 'patterns', '可借鉴模式', 'reusable_patterns',
                           'patterns_to_borrow', 'strengths', 'pros', 'techniques')


def extract_rhythm_formula(data, report_text):
    """提取节奏公式"""
    formula = get_field_str(data, 'rhythm.formula', 'rhythm.formula', 'pacing.formula', 'formula')
    if formula:
        return formula

    for line in report_text.split('\n'):
        if '节奏公式' in line or '钩(' in line or '铺(' in line:
            return line.strip()
    return ''


def extract_ending_type(data, report_text):
    """提取结尾类型"""
    et = get_field_str(data, 'structure.ending_type', 'ending_type',
                        'structure.ending', 'ending.type', 'ending.ending_type')
    if et:
        return et

    for line in report_text.split('\n'):
        for kw in ['反转型', '情绪收束型', '开放式', '循环型']:
            if kw in line:
                return kw
    return ''


def extract_card(data, report_text):
    """从数据中提取一张短篇参考卡的所有信息"""
    card = {
        'tags': get_field_str(data, 'category', 'type', 'category'),
        'hook_technique': extract_hook_technique(data, report_text),
        'one_liner': extract_one_liner(data, report_text),
        'acts': extract_structure_acts(data),
        'characters': extract_characters(data),
        'patterns': extract_patterns(data),
        'rhythm_formula': extract_rhythm_formula(data, report_text),
        'ending_type': extract_ending_type(data, report_text),
    }
    return card


def render_card(card, book_title):
    """将卡信息渲染为 markdown"""
    lines = []
    lines.append(f'# 短篇参考卡：{book_title}')
    lines.append('')

    tags = card.get('tags', '')
    if tags:
        lines.append(f'**类型标签**：{tags}')
        lines.append('')

    hook = card.get('hook_technique', '')
    one_liner = card.get('one_liner', '')
    if hook or one_liner:
        lines.append('**钩子模式**')
        if hook:
            lines.append(f'- 手法：{hook}')
        if one_liner and one_liner != '未提取':
            lines.append(f'- 一句话钩子：{one_liner}')
        lines.append('')

    chars = card.get('characters', [])
    if chars:
        lines.append('**角色原型**')
        for c in chars[:4]:
            lines.append(f'- {c}')
        lines.append('')

    acts = card.get('acts', [])
    if acts:
        lines.append('**结构骨架**')
        for a in acts:
            if isinstance(a, dict):
                aname = a.get('name', a.get('label', '')) or ''
                afunc = a.get('function', '') or ''
                if aname or afunc:
                    lines.append(f'- {aname}：{afunc}')
            elif isinstance(a, str):
                lines.append(f'- {a}')
        lines.append('')

    formula = card.get('rhythm_formula', '')
    if formula and '钩' in formula:
        lines.append(f'**节奏模板**')
        lines.append(f'```')
        lines.append(formula)
        lines.append(f'```')
        lines.append('')

    ending = card.get('ending_type', '')
    if ending:
        lines.append(f'**结尾方式**：{ending}')
        lines.append('')

    patterns = card.get('patterns', [])
    if patterns:
        lines.append('**可借鉴模式**')
        for p in patterns[:5]:
            line = p if isinstance(p, str) else str(p)
            if line:
                lines.append(f'- {line}')
        lines.append('')

    return '\n'.join(lines)


def write_card(book_dir, card, book_title):
    """写短篇参考卡.md"""
    content = render_card(card, book_title)
    card_path = book_dir / '短篇参考卡.md'
    card_path.write_text(content, 'utf-8')
    return len(content)


# ── 类型总结生成 ──

def render_type_summary(type_name, cards):
    """从该类型所有卡生成聚合总结"""
    hook_counts = Counter()
    ending_counts = Counter()
    all_patterns = []
    all_chars = []
    all_hooks = []

    for book_title, card in cards:
        t = card.get('hook_technique', '')
        if t and t != '未提取':
            hook_counts[t] += 1

        et = card.get('ending_type', '')
        if et:
            ending_counts[et] += 1

        for p in card.get('patterns', []):
            if isinstance(p, str) and len(p) > 5:
                all_patterns.append(p)

        for c in card.get('characters', []):
            if c:
                all_chars.append(c)

        ol = card.get('one_liner', '')
        if ol and ol != '未提取':
            all_hooks.append((book_title, ol))

    lines = []
    lines.append(f'# {type_name}参考书类型总结（{len(cards)}本）')
    lines.append('')

    if hook_counts:
        lines.append('## 开篇钩子类型分布')
        total = sum(hook_counts.values())
        lines.append(f'共识别 {total} 条钩子手法记录：')
        for technique, count in hook_counts.most_common():
            pct = count / total * 100 if total else 0
            bars = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            lines.append(f'- {technique}：{count}本（{pct:.0f}%）{bars}')
        lines.append('')

    if all_hooks:
        lines.append('## 一句话钩子示例')
        for title, hook in all_hooks[:10]:
            lines.append(f'- 「{title}」：{hook}')
        lines.append('')

    if all_chars:
        lines.append('## 角色原型分布')
        archetype_counter = Counter()
        for c in all_chars:
            # 提取→后面的原型描述
            if '→' in c:
                archetype = c.split('→')[-1].strip()
                archetype_counter[archetype] += 1
        for archetype, count in archetype_counter.most_common(10):
            lines.append(f'- {archetype}：{count}次')
        lines.append('')

    if ending_counts:
        lines.append('## 结尾类型分布')
        for et, count in ending_counts.most_common():
            lines.append(f'- {et}：{count}本')
        lines.append('')

    if all_patterns:
        lines.append('## 高频可借鉴模式')
        pattern_counter = Counter()
        for p in all_patterns:
            # 取前15字作为key
            short = p[:20]
            pattern_counter[short] += 1
        for pattern, count in pattern_counter.most_common(15):
            lines.append(f'- {pattern}（{count}次）')
        lines.append('')

    lines.append('---')
    lines.append(f'*由 distill_ref.py 自动生成，覆盖 {len(cards)} 本参考书*')
    return '\n'.join(lines)


# ── 主流程 ──

def process_type(type_name):
    """处理单个类型"""
    type_dir = ROOT / type_name
    if not type_dir.is_dir():
        print(f'  [SKIP] 类型目录不存在：{type_dir}')
        return

    books = sorted([d for d in type_dir.iterdir() if d.is_dir()])
    if not books:
        print(f'  [SKIP] {type_name} 下无子目录')
        return

    print(f'\n{"="*50}')
    print(f'类型：{type_name}（{len(books)}本书）')
    print(f'{"="*50}')

    cards = []  # (book_title, card_dict)
    for book_dir in books:
        book_title = book_dir.name
        json_path = book_dir / '拆解数据.json'
        report_path = book_dir / '拆解报告.md'

        data = read_json_safe(json_path)
        report_text = read_text_safe(report_path)

        if not data and not report_text:
            print(f'  [SKIP] {book_title}：无拆解数据')
            continue

        data = data or {}
        card = extract_card(data, report_text)
        char_count = write_card(book_dir, card, book_title)
        cards.append((book_title, card))
        print(f'  ✓ {book_title}（{char_count}字）')

    if cards:
        summary = render_type_summary(type_name, cards)
        summary_path = type_dir / '类型总结.md'
        summary_path.write_text(summary, 'utf-8')
        print(f'\n  → 类型总结.md 已生成（{len(summary)}字）')
    else:
        print(f'  [SKIP] 无可处理的参考书')


def main():
    types = sys.argv[1:] if len(sys.argv) > 1 else None

    if not ROOT.is_dir():
        print(f'错误：参考书目录不存在 {ROOT}')
        return 1

    all_types = sorted([d.name for d in ROOT.iterdir() if d.is_dir()])

    if types:
        selected = [t for t in types if t in all_types]
        if not selected:
            print(f'可用类型：{", ".join(all_types)}')
            return 1
        for t in selected:
            process_type(t)
    else:
        for t in all_types:
            process_type(t)

    print(f'\n完成。输出位置：{ROOT}/{{类型}}/{{书名}}/短篇参考卡.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
