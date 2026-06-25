#!/usr/bin/env python3
"""
字数门禁 + 状态机驱动。

用法: python validate_chapter.py <项目目录>

自动读取/创建 write_status.json，校验当前章字数，更新状态。
输出 JSON: {"ok": bool, "errors": [...]}
"""
import io, json, sys, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def parse_chapter_plan(text):
    """从章节规划.md 提取每章目标字数。"""
    chapters = {}
    for m in re.finditer(r'##\s*第(\d+)章[：:]\s*(.+?)[（(]\s*([\d,]+)\s*字', text):
        n, t, c = int(m.group(1)), m.group(2).strip(), int(m.group(3).replace(',', ''))
        chapters[n] = {"title": t, "target_chars": c}
    if not chapters:  # fallback: 总字数表
        for m in re.finditer(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([\d,]+)\s*\|', text):
            n, t, c = int(m.group(1)), m.group(2).strip(), int(m.group(3).replace(',', ''))
            if n not in chapters:
                chapters[n] = {"title": t, "target_chars": c}
    return chapters


def extract_actual_chapters(body_text):
    """从正文.md 按 ## 标题解析实际章节与字数。"""
    chapters = {}
    pat = re.compile(r'^##\s*第(\d+)章[：:].*?$', re.MULTILINE)
    matches = list(pat.finditer(body_text))
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        chapters[n] = len(body_text[start:end].strip())
    return chapters


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "errors": [{"reason": "用法: validate_chapter.py <project_dir>"}]}))
        return 1

    proj = Path(sys.argv[1])
    status_file = proj / 'write_status.json'
    body_file = proj / '正文.md'
    plan_file = proj / '章节规划.md'

    # ---- 加载/初始化状态文件 ----
    status = None
    if status_file.exists():
        status = json.loads(status_file.read_text('utf-8'))

    if not status:
        if not plan_file.exists():
            print(json.dumps({"ok": False, "errors": [{"reason": "缺少 章节规划.md"}]}))
            return 1
        plan = parse_chapter_plan(plan_file.read_text('utf-8'))
        if not plan:
            print(json.dumps({"ok": False, "errors": [{"reason": "无法从章节规划.md 解析章节"}]}))
            return 1
        keys = sorted(plan)
        status = {
            "project": proj.name,
            "chapter_total": len(keys),
            "chapter_plan": {str(k): {"title": plan[k]["title"], "target_chars": plan[k]["target_chars"]} for k in keys},
            "current_chapter": keys[0],
            "loop": "chapter",
            "chapters": {str(k): {"status": "pending", "actual_chars": None} for k in keys},
            "final_review": {"status": "pending", "review_blocking": [], "review_warning": []},
        }
        status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')

    # ---- 解析正文 ----
    body = body_file.read_text('utf-8') if body_file.exists() else ''
    actual = extract_actual_chapters(body)

    # ---- 更新实际字数 ----
    for n, c in actual.items():
        if str(n) in status["chapters"]:
            status["chapters"][str(n)]["actual_chars"] = c

    # ---- 校验当前章 ----
    cc = status["current_chapter"]
    cs = status["chapters"].get(str(cc), {})
    cp = status["chapter_plan"].get(str(cc), {})
    target = cp.get("target_chars", 0)
    actual_chars = actual.get(cc, 0)
    min_req = target

    errors = []
    writable = cs.get("status") in ("pending", "writing", "blocking")

    if writable:
        # 如果是 pending，标记为 writing（首次开写）
        if cs.get("status") == "pending" and actual_chars == 0:
            status["chapters"][str(cc)]["status"] = "writing"

        # 已有内容才校验
        if actual_chars > 0:
            # 字数门禁
            if actual_chars < min_req:
                errors.append({
                    "chapter": cc,
                    "field": "word_count",
                    "actual": actual_chars,
                    "target": target,
                    "min_required": min_req,
                    "reason": f"第{cc}章「{cp.get('title','')}」目标{target}字，实际{actual_chars}字，不足{target}字"
                })

            # 格式门禁
            if not re.search(rf'^##\s*第{cc}章[：:]', body, re.MULTILINE):
                errors.append({
                    "chapter": cc,
                    "field": "title_format",
                    "reason": f"正文.md 中未找到「## 第{cc}章：标题」。格式必须为 ## 第N章：标题"
                })

            # 字数通过 → 推进状态
            if not errors:
                if cs.get("status") == "writing":
                    status["chapters"][str(cc)]["status"] = "in_review"
                elif cs.get("status") == "blocking":
                    status["chapters"][str(cc)]["status"] = "in_review"

    # ---- 自动推进当前章指针 ----
    nxt = None
    for k in sorted(status["chapters"], key=int):
        if status["chapters"][k].get("status") != "passed":
            nxt = int(k)
            break
    if nxt is not None:
        status["current_chapter"] = nxt
    elif status["loop"] == "chapter":
        status["loop"] = "final_review"

    # ---- 写回 ----
    status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({"ok": len(errors) == 0, "errors": errors}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())