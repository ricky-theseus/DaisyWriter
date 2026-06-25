#!/usr/bin/env python3
"""
短篇审查引擎。

用法: python review_shortstory.py <项目目录>

功能:
  1. 读取 正文.md + shortstory-craft 工艺标准
  2. 计算句长/极短句占比/钩子位置/节奏结构等量化指标
  3. 评分、标记阻断、生成审查报告
  4. 输出 审查报告.md + review_result.json
  5. 更新 write_status.json（设置 blocking 或 passed）

退出码: 0=无阻断, 1=有阻断
"""
import io, json, math, os, re, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SKILL_DIR = Path(__file__).parent

CRAFT_STANDARDS_PATH = SKILL_DIR.parent / 'shortstory-craft' / 'references' / 'writing-standards.md'
DIMENSIONS_PATH = SKILL_DIR / 'references' / 'review-dimensions.md'

WEIGHT_HOOK = 25
WEIGHT_PACING = 20
WEIGHT_CRAFT = 20
WEIGHT_PLOT = 15
WEIGHT_CHARACTER = 10
WEIGHT_ENDING = 10

BLOCKING_NO_HOOK = '前500字无钩子'
BLOCKING_WORD_COUNT = '字数不在8000-30000范围'
BLOCKING_AVG_SENT_LEN = '平均句长<18或>55'
BLOCKING_SHORT_SENT_RATIO = '极短句占比>12%'
BLOCKING_NO_TWIST = '结尾无twist或情绪收束'
BLOCKING_NO_INFO_PUSH = '超过1500字无新信息推进'
BLOCKING_CONTINUOUS_SAME_SUBJECT = '连续同主语开头超过2句'
BLOCKING_EMOTION_TAG = '出现情绪标签词'
BLOCKING_ADVERB_EMOTION = '副词修饰情绪'


def load_craft_standards():
    if not CRAFT_STANDARDS_PATH.exists():
        return {}
    text = CRAFT_STANDARDS_PATH.read_text('utf-8')
    lines = text.split('\n')
    standards = {}
    for line in lines:
        stripped = line.strip()
        m = re.match(r'\|\s*(.+?)\s*\|\s*(\d+)\s*(?:-(\d+))?\s*字?\s*\|', stripped)
        if m:
            key = m.group(1).strip()
            lo = int(m.group(2))
            hi = int(m.group(3)) if m.group(3) else None
            standards[key] = {'min': lo, 'max': hi}
    standards['word_count'] = {'min': 8000, 'max': 30000}
    return standards


def extract_text_by_chapter(body_text):
    chapters = {}
    pat = re.compile(r'^##\s*第(\d+)章[：:].*?$', re.MULTILINE)
    matches = list(pat.finditer(body_text))
    if not matches:
        return {'full': body_text}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        chapters[n] = body_text[start:end].strip()
    return chapters


def split_sentences(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    parts = re.split(r'([。！？\n])', text)
    sentences = []
    buf = ''
    for p in parts:
        buf += p
        if p in ('。', '！', '？', '\n'):
            s = buf.strip()
            if s:
                sentences.append(s)
            buf = ''
    if buf.strip():
        sentences.append(buf.strip())
    return sentences if sentences else [text]


EMOTION_TAG_WORDS = [
    '感到', '觉得', '感觉', '心中', '心里', '内心',
    '一种', '一股', '一阵',
]


def count_chinese_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def analyze_sentences(sentences):
    if not sentences:
        return {'avg_len': 0, 'short_ratio': 0, 'long_ratio': 0, 'count': 0, 'lens': []}
    lens = [count_chinese_chars(s) for s in sentences]
    total = len(lens)
    avg = sum(lens) / total if total else 0
    short_count = sum(1 for l in lens if l <= 8 and l > 0)
    long_count = sum(1 for l in lens if l > 30)
    return {
        'avg_len': round(avg, 1),
        'short_ratio': round(short_count / total * 100, 1) if total else 0,
        'long_ratio': round(long_count / total * 100, 1) if total else 0,
        'count': total,
        'lens': lens,
    }


def check_hook(text):
    segment = text[:500]
    if not segment:
        return False, '正文为空'
    patterns = [
        (r'\?', '悬疑问题'),
        (r'死了|杀了|死了|死|尸体|血|殡|葬|棺材|死了人', '情绪冲击'),
        (r'跑|逃|追|喊|救命|不要|住手|住口', '矛盾场景'),
        (r'"', '对话开场'),
    ]
    for pat, label in patterns:
        if re.search(pat, segment):
            return True, label
    if count_chinese_chars(segment) < 100:
        return False, '前500字信息量太少'
    return False, '无识别钩子'


def check_info_push(text):
    info_triggers = [
        r'原来|突然|发现|没想到|其实|竟然|居然',
        r'因为|所以|但|却|然而|不过|可是',
        r'第[一二三四五六七八九十\d]',
        r'名字|叫|是.*人|来自|出生',
        r'不是.*而是',
    ]
    segments = [text[i:i+500] for i in range(0, len(text), 500)]
    max_gap = 0
    current_gap = 0
    for seg in segments:
        found = any(re.search(p, seg) for p in info_triggers)
        if found:
            current_gap = 0
        else:
            current_gap += 1
            max_gap = max(max_gap, current_gap)
    max_gap_chars = max_gap * 500
    return max_gap_chars <= 1500, max_gap_chars


def check_ending(text, last_1000):
    if not last_1000:
        return False, '无结尾内容'
    twist_patterns = [
        r'原来|其实|竟然|居然|没想到|不是.*而是',
        r'如果.*就|假如.*那么|或许|也许|可能',
        r'哭|笑|泪|叹',
        r'结束|完|最后|从此',
        r'梦|醒|睁眼|闭眼',
    ]
    found = [p for p in twist_patterns if re.search(p, last_1000)]
    if found:
        return True, f'检测到收束迹象: {", ".join(found[:3])}'
    return False, '平铺直叙结束，无twist或情绪收束'


def check_emotion_tags(text, sentences):
    found_tags = []
    found_adverbs = []
    adverb_emotion_pattern = re.compile(r'(深深|默默|悄悄|狠狠|狠狠|轻轻|微微)(地|的)?(叹|吸|呼|笑|哭|说)')
    for s in sentences:
        for word in EMOTION_TAG_WORDS:
            if word in s:
                found_tags.append(f'"{word}"出现在: "{s[:40]}..."')
                break
    for m in adverb_emotion_pattern.finditer(text):
        found_adverbs.append(m.group(0))
    return found_tags, found_adverbs


def check_subject_repetition(sentences):
    same_subject_pattern = re.compile(r'^(他|她|它|我|你)')
    max_count = 0
    current = 0
    for s in sentences:
        if same_subject_pattern.match(s):
            current += 1
            max_count = max(max_count, current)
        else:
            current = 0
    return max_count


def analyze_pacing(text):
    paragraphs = re.split(r'\n\s*\n', text)
    # Count dialogue-only paragraphs and narration paragraphs
    dialogue_paras = 0
    action_paras = 0
    narra_paras = 0
    action_words = re.compile(r'(走|跑|跳|抓|打|踢|拿|放|推|拉|看|听|说|问|答|笑|哭)')

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        lines = p.split('\n')
        has_dialogue = any('"' in line or '“' in line or '」' in line for line in lines)
        has_action = bool(action_words.search(p))
        if has_dialogue:
            dialogue_paras += 1
        elif has_action:
            action_paras += 1
        else:
            narra_paras += 1

    total = dialogue_paras + action_paras + narra_paras
    active_ratio = round((dialogue_paras + action_paras) / total * 100, 1) if total else 0
    return {
        'dialogue_paras': dialogue_paras,
        'action_paras': action_paras,
        'narra_paras': narra_paras,
        'active_ratio': active_ratio,
    }


def check_character_setup(text):
    # Simple heuristics for character count and memory points
    char_mentions = re.findall(r'[\u4e00-\u9fff]{2,4}(?=说[：:]|道[：:]| walked|said|asked)', text)
    char_mentions += re.findall(r'[\u4e00-\u9fff]{2,4}[地说]道[：:]', text)
    unique_chars = set()
    for c in char_mentions:
        if len(c) in (2, 3, 4):
            unique_chars.add(c)
    memory_points = []
    memory_patterns = [
        r'(口头禅|习惯|总是|从来不|每次|从不|总是会)',
        r'(但|却|而是|偏偏).{0,20}(不|竟然|居然)',
        r'(人称|外号|绰号|大家都叫)',
    ]
    for pat in memory_patterns:
        matches = re.findall(pat, text)
        if matches:
            memory_points.extend(matches)
    return {
        'speaking_chars_detected': len(unique_chars),
        'estimated_role_count': min(len(unique_chars) + 2, 10),
        'memory_points_found': len(memory_points),
    }


def calculate_score(hook_ok, hook_note, sa, pacing, char_info, ending_ok, ending_note, emotion_tags, adverb_tags, info_push_ok):
    score = 0
    details = {}

    # Hook (25)
    hook_score = 0
    if hook_ok:
        hook_score += 25
    elif '信息量太少' in hook_note:
        hook_score += 5
    else:
        hook_score += 10
    score += hook_score
    details['hook'] = {'score': hook_score, 'max': 25, 'note': hook_note}

    # Pacing (20)
    pacing_score = 0
    if pacing['active_ratio'] >= 40:
        pacing_score += 10
    else:
        pacing_score += max(0, int(pacing['active_ratio'] / 4))
    if pacing['active_ratio'] >= 55:
        pacing_score += 5
    if pacing['active_ratio'] <= 80:
        pacing_score += 5
    else:
        pacing_score += max(0, 5 - (pacing['active_ratio'] - 80) // 5)
    score += pacing_score
    details['pacing'] = {'score': pacing_score, 'max': 20, 'note': f'对话+动作段落占比 {pacing["active_ratio"]}%'}

    # Craft (20)
    craft_score = 0
    craft_notes = []
    if 25 <= sa['avg_len'] <= 50:
        craft_score += 7
        craft_notes.append(f'平均句长 {sa["avg_len"]}字，达标')
    elif 18 <= sa['avg_len'] <= 55:
        craft_score += 4
        craft_notes.append(f'平均句长 {sa["avg_len"]}字，在容忍范围')
    else:
        craft_notes.append(f'平均句长 {sa["avg_len"]}字，超标')
    if sa['short_ratio'] <= 12:
        craft_score += 5
    else:
        craft_notes.append(f'极短句占比 {sa["short_ratio"]}%，超标')
    if not emotion_tags:
        craft_score += 4
    else:
        craft_notes.append(f'发现{len(emotion_tags)}个情绪标签词')
    if not adverb_tags:
        craft_score += 4
    else:
        craft_notes.append(f'发现{len(adverb_tags)}处副词修饰情绪')
    details['craft'] = {'score': craft_score, 'max': 20, 'note': '; '.join(craft_notes) if craft_notes else '文笔达标'}
    score += craft_score

    # Plot (15)
    plot_score = 0
    plot_notes = []
    if info_push_ok:
        plot_score += 8
    else:
        plot_notes.append('信息推进间隔过长')
    if hook_ok:
        plot_score += 7
    else:
        plot_notes.append('开篇钩子缺失影响情节投入')
    details['plot'] = {'score': plot_score, 'max': 15, 'note': '; '.join(plot_notes) if plot_notes else '情节推进合理'}
    score += plot_score

    # Character (10)
    char_score = 0
    if char_info['memory_points_found'] >= 1:
        char_score += 5
    if char_info['estimated_role_count'] <= 5:
        char_score += 5
    else:
        char_score += max(0, 5 - (char_info['estimated_role_count'] - 5))
    details['character'] = {
        'score': char_score, 'max': 10,
        'note': f'预估角色数 {char_info["estimated_role_count"]}, 记忆点 {char_info["memory_points_found"]}',
    }
    score += char_score

    # Ending (10)
    ending_score = 0
    if ending_ok:
        ending_score += 10
    else:
        ending_score += 2
    details['ending'] = {'score': ending_score, 'max': 10, 'note': ending_note}
    score += ending_score

    return score, details


def blocking_detection(text, sa, hook_ok, ending_ok, info_push_ok, emotion_tags, adverb_tags, subject_repeat):
    blocks = []

    total_chars = count_chinese_chars(text)
    if total_chars < 8000 or total_chars > 30000:
        blocks.append(f'{BLOCKING_WORD_COUNT} (当前{total_chars}字)')

    if not hook_ok:
        blocks.append(BLOCKING_NO_HOOK)

    if sa['avg_len'] and (sa['avg_len'] < 18 or sa['avg_len'] > 55):
        blocks.append(f'{BLOCKING_AVG_SENT_LEN} (当前{sa["avg_len"]})')

    if sa['short_ratio'] > 12:
        blocks.append(f'{BLOCKING_SHORT_SENT_RATIO} (当前{sa["short_ratio"]}%)')

    if subject_repeat > 2:
        blocks.append(f'{BLOCKING_CONTINUOUS_SAME_SUBJECT} (连续{subject_repeat}句)')

    if emotion_tags:
        blocks.append(f'{BLOCKING_EMOTION_TAG}: {emotion_tags[0][:50]}')

    if adverb_tags:
        blocks.append(f'{BLOCKING_ADVERB_EMOTION}: {adverb_tags[0]}')

    if not ending_ok:
        blocks.append(BLOCKING_NO_TWIST)

    if not info_push_ok:
        blocks.append(BLOCKING_NO_INFO_PUSH)

    return blocks


def generate_report(project, total_chars, hook_ok, hook_note, sa, pacing, char_info,
                     ending_ok, ending_note, emotion_tags, adverb_tags,
                     subject_repeat, info_push_ok, info_push_gap, blocks, score, details):
    lines = []
    lines.append(f'# {project} · 审查报告')
    lines.append(f'')
    lines.append(f'> 生成时间: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'> 总字数: {total_chars} 字')
    lines.append(f'> 总分: {score}/100')
    lines.append(f'> 状态: {"🚫 有阻断需修复" if blocks else "✅ 无阻断通过"}')
    lines.append(f'')

    if blocks:
        lines.append(f'## 阻断问题')
        for b in blocks:
            lines.append(f'- 🔴 {b}')
        lines.append(f'')

    lines.append(f'## 维度评分')
    dim_labels = {
        'hook': '开篇钩子',
        'pacing': '节奏结构',
        'craft': '文笔句法',
        'plot': '情节推进',
        'character': '人物塑造',
        'ending': '结尾收束',
    }
    for key, label in dim_labels.items():
        d = details.get(key, {})
        bar = '█' * max(1, d.get('score', 0) // 2) + '░' * max(0, 10 - d.get('score', 0) // 2)
        lines.append(f'- **{label}**: {d.get("score", 0)}/{d.get("max", 10)} {bar}')
        lines.append(f'  - {d.get("note", "")}')
    lines.append(f'')

    lines.append(f'## 量化指标')
    lines.append(f'| 指标 | 值 | 标准 | 判定 |')
    lines.append(f'|------|----|------|:----:|')
    lines.append(f'| 总字数 | {total_chars} | 8000-30000 | {"✅" if 8000 <= total_chars <= 30000 else "❌"} |')
    lines.append(f'| 平均句长 | {sa["avg_len"]} | 25-50 | {"✅" if 25 <= sa.get("avg_len", 0) <= 50 else ("⚠" if 18 <= sa.get("avg_len", 0) <= 55 else "❌")} |')
    lines.append(f'| 极短句占比 | {sa["short_ratio"]}% | ≤12% | {"✅" if sa["short_ratio"] <= 12 else "❌"} |')
    lines.append(f'| 长句占比 | {sa["long_ratio"]}% | ≥25% | {"✅" if sa["long_ratio"] >= 25 else "⚠"} |')
    lines.append(f'| 开篇钩子 | {"有" if hook_ok else "无"} ({hook_note}) | 前500字 | {"✅" if hook_ok else "❌"} |')
    lines.append(f'| 结尾收束 | {"有" if ending_ok else "无"} | 必须有 | {"✅" if ending_ok else "❌"} |')
    lines.append(f'| 对话+动作占比 | {pacing["active_ratio"]}% | ≥50% | {"✅" if pacing["active_ratio"] >= 50 else "⚠"} |')
    lines.append(f'| 连续同主语开头 | {subject_repeat}句 | ≤2句 | {"✅" if subject_repeat <= 2 else "❌"} |')
    lines.append(f'| 情绪标签词 | {len(emotion_tags)}个 | 0 | {"✅" if not emotion_tags else "❌"} |')
    lines.append(f'| 副词修饰情绪 | {len(adverb_tags)}处 | 0 | {"✅" if not adverb_tags else "❌"} |')
    lines.append(f'| 新信息推进 | {"正常" if info_push_ok else f"最大间隔{info_push_gap}字"} | ≤1500字 | {"✅" if info_push_ok else "❌"} |')
    lines.append(f'')

    lines.append(f'## 修改建议')
    if not blocks:
        lines.append(f'无阻断问题，可以定稿或继续下一章。')
    else:
        for b in blocks:
            if BLOCKING_NO_HOOK in b:
                lines.append(f'- **前500字加钩子**: 悬疑问题/情绪冲击/矛盾场景/金句开篇，任选一种在开篇呈现')
            if BLOCKING_WORD_COUNT in b:
                lines.append(f'- **调整字数**: 当前{total_chars}字，需在8000-30000范围内')
            if BLOCKING_AVG_SENT_LEN in b:
                lines.append(f'- **调整句长**: ' +
                             ('加入较多短句打断节奏' if sa.get('avg_len', 0) > 55 else '增加描述性长句丰富节奏'))
            if BLOCKING_SHORT_SENT_RATIO in b:
                lines.append(f'- **减少极短句**: 合并部分短句，用长句做铺垫，短句留到爆发段落用')
            if BLOCKING_NO_TWIST in b:
                lines.append(f'- **强化结尾**: 加入反转型/情绪收束型/开放式/循环型结尾')
            if BLOCKING_NO_INFO_PUSH in b:
                lines.append(f'- **加快信息释放**: 每500字至少有一个新信息节点，避免大段无推进的描写')
        lines.append(f'')
        lines.append(f'修复后重新运行审查确认阻断消除。')
    lines.append(f'')

    lines.append(f'---')
    lines.append(f'审查维度参考: `shortstory-craft/references/writing-standards.md`')
    lines.append(f'详细维度定义: `shortstory-review/references/review-dimensions.md`')
    lines.append(f'')

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "reason": "用法: python review_shortstory.py <项目目录>"}, ensure_ascii=False))
        sys.exit(1)

    proj = Path(sys.argv[1]).resolve()
    status_file = proj / 'write_status.json'
    body_file = proj / '正文.md'
    report_dir = proj / '审查报告'
    report_file = report_dir / 'review_result.json'

    if not body_file.exists():
        print(json.dumps({"ok": False, "reason": "缺少 正文.md"}, ensure_ascii=False))
        sys.exit(1)

    body_text = body_file.read_text('utf-8').strip()
    total_chars = count_chinese_chars(body_text)

    # Load standards
    standards = load_craft_standards()

    # Analyze
    chapters = extract_text_by_chapter(body_text)
    full_text = chapters.get('full', body_text)
    sentences = split_sentences(full_text)
    sa = analyze_sentences(sentences)

    hook_ok, hook_note = check_hook(full_text)

    ending_segment = full_text[-1000:] if len(full_text) >= 1000 else full_text
    ending_ok, ending_note = check_ending(full_text, ending_segment)

    emotion_tags, adverb_tags = check_emotion_tags(full_text, sentences)
    subject_repeat = check_subject_repetition(sentences)

    pacing = analyze_pacing(full_text)
    char_info = check_character_setup(full_text)

    info_push_ok, info_push_gap = check_info_push(full_text)

    # Scoring
    score, details = calculate_score(
        hook_ok, hook_note, sa, pacing, char_info,
        ending_ok, ending_note, emotion_tags, adverb_tags, info_push_ok,
    )

    # Blocking
    blocks = blocking_detection(
        full_text, sa, hook_ok, ending_ok, info_push_ok,
        emotion_tags, adverb_tags, subject_repeat,
    )

    # Generate report
    report_md = generate_report(
        proj.name, total_chars,
        hook_ok, hook_note, sa, pacing, char_info,
        ending_ok, ending_note, emotion_tags, adverb_tags,
        subject_repeat, info_push_ok, info_push_gap,
        blocks, score, details,
    )

    # Write report
    report_dir.mkdir(parents=True, exist_ok=True)

    report_md_path = report_dir / '审查报告.md'
    report_md_path.write_text(report_md, 'utf-8')

    result = {
        'ok': len(blocks) == 0,
        'project': proj.name,
        'total_chars': total_chars,
        'score': score,
        'blocking': blocks,
        'dimensions': {k: v for k, v in details.items()},
        'metrics': {
            'avg_sentence_len': sa['avg_len'],
            'short_sentence_ratio': sa['short_ratio'],
            'hook_found': hook_ok,
            'ending_closed': ending_ok,
            'active_ratio': pacing['active_ratio'],
            'subject_repetition': subject_repeat,
            'emotion_tags': len(emotion_tags),
            'adverb_modifiers': len(adverb_tags),
            'character_count_est': char_info['estimated_role_count'],
            'memory_points': char_info['memory_points_found'],
        },
        'report_md_path': str(report_md_path),
    }
    report_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')

    # Update write_status.json
    if status_file.exists():
        status = json.loads(status_file.read_text('utf-8'))
        if blocks:
            status['chapters'][str(status['current_chapter'])]['status'] = 'blocking'
        status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')

    print(json.dumps(result, ensure_ascii=False))
    return 0 if not blocks else 1


if __name__ == '__main__':
    sys.exit(main())
