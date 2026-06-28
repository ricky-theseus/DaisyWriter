import sys
import os
import json
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

NEED_DIMENSIONS = {
    '钩子': ['hook', '钩子', '开篇', '开头', '开场'],
    '结构': ['structure', '结构', '骨架', '布局', '框架'],
    '节奏': ['rhythm', '节奏', '快慢', '密度', '推进'],
    '悬念': ['suspense', '悬念', '伏笔', '铺垫', '反转'],
    '人物': ['character', '人物', '角色', '人设', '立像'],
    '结尾': ['ending', '结尾', '收束', '收尾', '结局', 'twist'],
    '情绪': ['emotion', '情绪', '情感', '氛围'],
    '对话': ['dialogue', '对话', '对白'],
}

def detect_need_dimensions(need_text):
    """Detect which dimensions the user's need maps to."""
    need_lower = need_text.lower()
    matched = []
    for dim, keywords in NEED_DIMENSIONS.items():
        for kw in keywords:
            if kw in need_lower:
                matched.append(dim)
                break
    return matched if matched else ['全部']

def extract_section(text, *headers):
    lines = text.split('\n')
    result = []
    capture = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(h) for h in headers) or any(stripped == h for h in headers):
            capture = True
            continue
        if capture:
            if stripped.startswith('##') or (stripped.startswith('---') and i > 0 and lines[i-1].strip() == ''):
                break
            if stripped:
                result.append(stripped)
    return '\n'.join(result[:10])

def parse_project_path(proj_path):
    parts = proj_path.replace('\\', '/').strip('/').split('/')
    if len(parts) >= 2 and parts[0] in ('短篇', 'short-story'):
        genre = parts[1]
        name = parts[2] if len(parts) > 2 else None
        return genre, name
    return None, None

def find_workspace_base(proj_path):
    """Resolve 短篇/ directory from project path."""
    if os.path.isabs(proj_path):
        workspace = proj_path
        for _ in range(4):
            if os.path.basename(workspace) in ('短篇', 'short-story') or (workspace and os.path.isdir(os.path.join(workspace, '短篇'))):
                break
            parent = os.path.dirname(workspace)
            if parent == workspace:
                break
            workspace = parent
        if os.path.isdir(os.path.join(workspace, '短篇')):
            return os.path.join(workspace, '短篇')
        else:
            return os.path.join(os.path.dirname(SCRIPT_DIR), '短篇')
    else:
        base = os.path.normpath(os.path.join(os.path.dirname(SCRIPT_DIR), proj_path.split('/')[0] if '/' in proj_path else '..'))
        if not os.path.isdir(base):
            base = os.path.join(os.path.dirname(SCRIPT_DIR), '短篇')
        for candidate in [os.getcwd(), os.path.dirname(SCRIPT_DIR)]:
            candidate_base = os.path.join(candidate, '短篇')
            if os.path.isdir(candidate_base):
                base = candidate_base
                break
        return base

def load_json_data(json_path):
    """Load 拆解数据.json if it exists and has content."""
    if not os.path.isfile(json_path):
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

def scan_references(ref_dir):
    """Scan reference directory, load both report text and JSON data.
    Supports both 拆解报告.md and 拆书报告.md naming conventions."""
    if not os.path.isdir(ref_dir):
        return []
    results = []
    for item in sorted(os.listdir(ref_dir)):
        sub = os.path.join(ref_dir, item)
        report = os.path.join(sub, '拆解报告.md')
        if not os.path.isfile(report):
            report = os.path.join(sub, '拆书报告.md')
        json_data = os.path.join(sub, '拆解数据.json')
        rhythm_file = os.path.join(sub, '节奏统计.md')
        template_file = os.path.join(sub, '句式模板.md')

        entry = {
            'title': item,
            'report_text': '',
            'json': None,
            'has_rhythm': os.path.isfile(rhythm_file),
            'has_templates': os.path.isfile(template_file),
            'hook': '',
            'structure': '',
            'takeaways': '',
        }

        if os.path.isfile(report):
            with open(report, 'r', encoding='utf-8') as f:
                entry['report_text'] = f.read()
            entry['hook'] = extract_section(entry['report_text'],
                '# 开场钩子', '## 开场钩子', '### 开场钩子', '## 核心设定',
                '### 开篇钩子', '### 开篇钩子（前300字）', '## 开篇钩子分析')
            entry['structure'] = extract_section(entry['report_text'],
                '## 结构分析', '### 结构分析', '## 结构骨架', '## 结构分析（已发布部分）')
            entry['takeaways'] = extract_section(entry['report_text'],
                '## 可借鉴模式', '### 可借鉴模式', '## 可借鉴点', '### 可借鉴点',
                '## 可复用的模式总结', '## 亮点', '### 亮点')

        entry['json'] = load_json_data(json_data)

        has_content = bool(entry['hook'] or entry['structure'] or entry['takeaways'] or entry['json'])
        if has_content:
            results.append(entry)
    return results

def match_references_to_need(references, need_text, need_dims):
    """Score references by relevance to the user's need.
    Uses pre-extracted fields from scan_references for reliability."""
    scored = []
    for ref in references:
        score = 0
        matched_reasons = []

        # Check JSON data for relevant patterns (highest confidence)
        if ref['json']:
            json_data = ref['json']

            # Search all string values in JSON for matching keywords
            json_text = json.dumps(json_data, ensure_ascii=False)

            # Check specific known fields
            for field in ['strengths', 'techniques', '亮点总结', '可借模式', '可复用模式', '可提取模板',
                          'patterns', 'reusable_patterns', 'patterns_of_interest', 'patterns_to_borrow',
                          'borrowable_patterns']:
                items = json_data.get(field, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str):
                            for dim in need_dims:
                                for kw in NEED_DIMENSIONS[dim]:
                                    if kw in item.lower():
                                        score += 2
                                        matched_reasons.append(f"模式匹配: {item[:80]}")
                                        break

            # Check hook-related fields
            if any(d in ['钩子', '全部'] for d in need_dims):
                for field in ['hook', 'hook_analysis', 'opening_hook', '开场钩子', '第一章钩子分析', '各级钩子']:
                    val = json_data.get(field)
                    if val:
                        if isinstance(val, str) and len(val) > 10:
                            score += 2
                            matched_reasons.append(f"有开篇钩子分析")
                            break
                        elif isinstance(val, dict):
                            score += 2
                            matched_reasons.append(f"有开篇钩子分析")
                            break

            # Check ending-related fields
            if any(d in ['结尾', '全部'] for d in need_dims):
                for field in ['ending', 'ending_quality', '结尾质量', '结局评价']:
                    val = json_data.get(field)
                    if val:
                        if isinstance(val, str) and len(val) > 10:
                            score += 2
                            matched_reasons.append(f"有结尾分析")
                            break
                        elif isinstance(val, dict):
                            score += 2
                            matched_reasons.append(f"有结尾分析")
                            break

            # Check rhythm-related fields
            if any(d in ['节奏', '全部'] for d in need_dims):
                for field in ['rhythm', 'rhythm_analysis', 'pacing', 'pace_control', '节奏控制', '节奏参数']:
                    val = json_data.get(field)
                    if val:
                        score += 2
                        if 'formula' in json_text or '公式' in json_text:
                            matched_reasons.append(f"有节奏公式")
                        else:
                            matched_reasons.append(f"有节奏分析")
                        break

            # Check structure-related fields
            if any(d in ['结构', '全部'] for d in need_dims):
                for field in ['structure', 'plot_structure', '结构分析', '结构骨架', '结构类型']:
                    val = json_data.get(field)
                    if val:
                        score += 2
                        matched_reasons.append(f"有结构分析")
                        break

        # Check pre-extracted hook/structure/takeaways for relevance
        if ref['hook']:
            for dim in need_dims:
                for kw in NEED_DIMENSIONS[dim]:
                    if kw in ref['hook'].lower():
                        score += 1
                        if not matched_reasons or f"{dim}维度匹配" not in ' '.join(matched_reasons):
                            matched_reasons.append(f"{dim}维度有详细分析")
                        break

        if ref['structure'] and any(dim in ['结构', '节奏', '全部'] for dim in need_dims):
            for dim in need_dims:
                for kw in NEED_DIMENSIONS[dim]:
                    if kw in ref['structure'].lower():
                        score += 1
                        break
            if not any('结构' in r for r in matched_reasons):
                matched_reasons.append("有结构分析")

        if ref['takeaways']:
            for dim in need_dims:
                for kw in NEED_DIMENSIONS[dim]:
                    if kw in ref['takeaways'].lower():
                        score += 1
                        break

        # File presence bonus
        if ref['has_rhythm'] and '节奏' in need_dims:
            score += 1
        if ref['has_templates']:
            score += 1

        # Baseline: references with content get minimum score 1
        has_any = bool(ref['hook'] or ref['structure'] or ref['takeaways'] or ref['json'])
        if has_any and score == 0:
            score = 1
            matched_reasons.append("该类型下可用参考")

        if score > 0:
            scored.append((score, ref, matched_reasons))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:5]  # Top 5 matches

def print_full_scan(references):
    """Original behavior: print all references (backward compatibility)."""
    print(f"\n{'='*50}")
    print(f"参考书目录扫描")
    print(f"找到 {len(references)} 篇参考拆解")
    print(f"{'='*50}")

    if not references:
        print(f"\n[提示] 该类型下没有拆书报告。")
        print("可以撰写时直接调用写作常识。")
        return

    for ref in references:
        print(f"\n--- {ref['title']} ---")
        status = []
        if ref['json']:
            status.append("有结构化数据")
        if ref['has_rhythm']:
            status.append("有节奏统计")
        if ref['has_templates']:
            status.append("有句式模板")
        if status:
            print(f"  [{', '.join(status)}]")

        if ref['hook']:
            print(f"\n[开篇钩子]")
            print(ref['hook'][:300])
        if ref['structure']:
            print(f"\n[结构]")
            print(ref['structure'][:300])
        if ref['takeaways']:
            print(f"\n[可借鉴]")
            print(ref['takeaways'][:300])
        print()

    print(f"{'='*50}")
    print("写作时请将以上模式融入当前章节。")
    print("重点：开篇钩子、结构节奏、信息密度控制。")
    print(f"{'='*50}\n")

def print_need_matching(scored, need_text, need_dims):
    """Print on-demand matching results."""
    print(f"\n{'='*50}")
    print(f"写作需求: {need_text}")
    print(f"匹配维度: {'/'.join(need_dims)}")
    print(f"找到 {len(scored)} 篇相关参考")
    print(f"{'='*50}")

    if not scored:
        print(f"\n没有找到与当前需求匹配的参考拆解。")
        print("可以尝试：")
        print("  1. 用更具体的关键词重新搜索（如'开篇钩子'、'节奏控制'）")
        print("  2. 使用跨类型参考（该类型不同题材的书也可能有借鉴价值）")
        print("  3. 直接调用写作常识")
        return

    for score, ref, reasons in scored:
        print(f"\n--- {ref['title']} (匹配度: {score}) ---")

        # Show relevant pre-extracted content based on need
        show_hook = any(d in ['钩子', '全部'] for d in need_dims)
        show_structure = any(d in ['结构', '节奏', '全部'] for d in need_dims)

        if show_hook and ref['hook']:
            print(f"\n  [开篇钩子]")
            for line in ref['hook'].split('\n')[:6]:
                if line.strip():
                    print(f"    {line.strip()[:120]}")

        if show_structure and ref['structure']:
            print(f"\n  [结构]")
            for line in ref['structure'].split('\n')[:6]:
                if line.strip():
                    print(f"    {line.strip()[:120]}")

        # Show rhythm info if available and relevant
        if ref['has_rhythm'] and any(d in ['节奏', '全部'] for d in need_dims):
            print(f"\n  [节奏统计] 有段落级节奏数据")
            if ref['json'] and ref['json'].get('rhythm', {}).get('formula'):
                print(f"    公式: {ref['json']['rhythm']['formula']}")

        # Show templates if available
        if ref['has_templates']:
            print(f"\n  [句式模板] 有可复用句式模板")

        # Show reasons why matched
        print(f"\n  → 匹配原因:")
        for r in reasons[:3]:
            print(f"    · {r[:120]}")

        # Show takeaways (always useful)
        if ref['takeaways']:
            print(f"\n  [可借鉴]")
            for line in ref['takeaways'].split('\n')[:4]:
                if line.strip():
                    print(f"    {line.strip()[:120]}")
        print()

    print(f"{'='*50}")
    print("写作时请优先参考以上匹配结果。")
    print("对匹配度最高的参考书，强制引用其模式至少一条。")
    print(f"{'='*50}\n")

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python load_ref.py 短篇/{类型}/{项目名}/          # 全量扫描")
        print("  python load_ref.py 短篇/{类型}/{项目名}/ --need \"描述你的写作难点\"")
        print()
        print("示例:")
        print("  python load_ref.py 短篇/言情/我的项目/")
        print("  python load_ref.py 短篇/悬疑/我的项目/ --need \"开篇钩子不知道怎么设计\"")
        print("  python load_ref.py 短篇/脑洞/我的项目/ --need \"节奏太平淡，缺少爆发段\"")
        print("  python load_ref.py 短篇/言情/我的项目/ --need \"结尾收不住，不知道怎么写twist\"")
        sys.exit(1)

    proj_path = sys.argv[1]
    need_text = ''
    if len(sys.argv) >= 4 and sys.argv[2] == '--need':
        need_text = sys.argv[3]

    genre, name = parse_project_path(proj_path)
    if not genre:
        print(f"无法解析项目路径: {proj_path}")
        print("路径格式应为: 短篇/{类型}/{项目名}/")
        sys.exit(1)

    base = find_workspace_base(proj_path)
    ref_dir = os.path.join(base, '参考书', genre)
    references = scan_references(ref_dir)

    if need_text:
        need_dims = detect_need_dimensions(need_text)
        scored = match_references_to_need(references, need_text, need_dims)
        print_need_matching(scored, need_text, need_dims)
    else:
        print_full_scan(references)

if __name__ == '__main__':
    main()