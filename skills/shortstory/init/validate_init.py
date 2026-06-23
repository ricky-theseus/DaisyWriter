#!/usr/bin/env python3
"""
初始化完整性校验 + 状态机驱动。

用法: python validate_init.py <项目目录>

校验: 6个文件存在且非空。输出 JSON: {"ok": bool, "errors": [...]}
"""
import io, json, sys, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REQUIRED_FILES = ["作品信息.md", "设定.md", "角色.md", "章节规划.md", "工艺约束.md", "正文.md"]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "errors": [{"reason": "用法: validate_init.py <project_dir>"}]}))
        return 1

    proj = Path(sys.argv[1])
    status_file = proj / 'init_status.json'

    # ---- 加载/初始化状态文件 ----
    status = None
    if status_file.exists():
        status = json.loads(status_file.read_text('utf-8'))
    if not status:
        status = {
            "project": proj.name,
            "loop": "init",
            "status": "drafting",
            "review_blocking": [],
            "review_warning": [],
        }

    # ---- 校验文件完整性 ----
    errors = []
    for fname in REQUIRED_FILES:
        fp = proj / fname
        if not fp.exists():
            errors.append({"field": "file_missing", "file": fname, "reason": f"缺少 {fname}"})
        elif len(fp.read_text('utf-8').strip()) == 0:
            errors.append({"field": "file_empty", "file": fname, "reason": f"{fname} 为空文件"})

    # 额外检查：章节规划.md 是否有章纲条目
    plan_file = proj / '章节规划.md'
    if plan_file.exists():
        text = plan_file.read_text('utf-8')
        chapters = list(re.finditer(r'第(\d+)章', text))
        if len(chapters) == 0:
            errors.append({"field": "plan_no_chapters", "file": "章节规划.md",
                           "reason": "章节规划.md 中未找到「第N章」条目"})

    # 额外检查：设定.md 是否过短（< 200 字说明太少）
    setting_file = proj / '设定.md'
    if setting_file.exists():
        text = setting_file.read_text('utf-8').strip()
        if 0 < len(text) < 200:
            errors.append({"field": "setting_too_short", "file": "设定.md",
                           "reason": f"设定.md 仅 {len(text)} 字，可能内容不足"})

    # ---- 根据校验结果自动转移状态 ----
    cs = status.get("status")

    if cs == "drafting" and not errors:
        # 文件完整 → 可进入盲审
        status["status"] = "in_review"

    # ---- 写回 ----
    status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')

    result = {"ok": len(errors) == 0, "errors": errors}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    import re
    sys.exit(main())