#!/usr/bin/env python3
"""
shortstory-write 入口脚本。必须最先运行。

用法: python start.py <项目目录> [--resume|--chapter N]

功能:
  1. 运行 validate_chapter.py 字数门禁
  2. 读取 write_status.json 当前状态
  3. 输出下一步该做什么
"""
import io, json, sys, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_step(label, detail=""):
    print(f"\n{'='*60}")
    print(f"  [{label}]")
    if detail:
        print(f"  {detail}")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("用法: python start.py <项目目录> [--resume|--chapter N]")
        sys.exit(1)

    proj = Path(sys.argv[1])
    args = set(sys.argv[2:])
    script_dir = Path(__file__).parent
    validate_script = script_dir / "validate_chapter.py"
    status_file = proj / "write_status.json"

    # 1. 先跑字数门禁
    if validate_script.exists():
        result = subprocess.run(
            [sys.executable, str(validate_script), str(proj)],
            capture_output=True, encoding='utf-8'
        )
        try:
            v = json.loads(result.stdout)
            if not v.get("ok"):
                for e in v.get("errors", []):
                    print(f"  [FAIL] {e['reason']}")
        except json.JSONDecodeError:
            pass

    # 2. 读状态
    if not status_file.exists():
        if "--resume" not in args:
            print("""
  状态: 首次启动

  请按以下顺序执行:
    1. 按 章节规划.md 写第一章
    2. 追加到 正文.md，格式: ## 第1章：标题
    3. 运行: python validate_chapter.py <项目目录>
    4. 字数通过后调子 agent 盲审
    5. 零阻断后继续下一章
""")
        else:
            print("  状态文件不存在，无法 resume。请去掉 --resume 重新开始。")
        return

    status = json.loads(status_file.read_text('utf-8'))
    loop = status.get("loop", "chapter")
    cc = status.get("current_chapter")
    cs = status["chapters"].get(str(cc), {}) if loop == "chapter" else {}
    s = status.get("status") if loop == "init" else cs.get("status", "unknown")
    plan = status.get("chapter_plan", {}).get(str(cc), {})
    actual = cs.get("actual_chars", 0)
    target = plan.get("target_chars", 0)

    # 3. 根据状态输出指令
    if loop == "final_review":
        frs = status.get("final_review", {}).get("status", "pending")
        if frs == "passed":
            print_step("完成", f"项目 {status.get('project')} 已定稿")
        else:
            print_step("全篇终审", "所有章节已写完，需要全篇盲审")
            print("""
  请执行:
    1. 新建子 agent 做全篇盲审
    2. 无阻断+无警告 -> 将 final_review.status 改为 done
    3. 有阻断或警告 -> 修正文.md，然后重新运行本脚本
""")
        return

    state_map = {
        "pending": ("待开写", f"第{cc}章目标{target}字，尚未开始"),
        "writing": ("写/修中", f"第{cc}章当前{actual}字，目标{target}字"),
        "in_review": ("待盲审", f"第{cc}章字数已够 ({actual}/{target})"),
        "blocking": ("有阻断需修复", f"第{cc}章盲审查出阻断"),
        "passed": ("已通过", f"第{cc}章已完成"),
    }

    label, detail = state_map.get(s, ("未知状态", ""))
    print_step(label, detail)

    if s == "pending":
        print("""
  请:
    1. 按章节规划写本章，追加到 正文.md
    2. 运行 python validate_chapter.py <项目目录>
    3. 字数通过 -> 调盲审 -> 零阻断 -> 改状态为 passed
""")
    elif s == "writing":
        if actual < target:
            print(f"  [WARN] 字数不足: 当前{actual}字, 目标{target}字, 还差{target - actual}字")
        print("""  写完或修改后，运行 python validate_chapter.py <项目目录> 校验字数。""")
    elif s == "in_review":
        print("""
  请调子 agent 盲审本章。
  零阻断 -> 将本章 status 改为 passed
  有阻断 -> 将本章 status 改为 blocking，修完后重新运行本脚本
""")
    elif s == "blocking":
        print("""
  请根据盲审结果修复本章内容。
  修完后运行 python validate_chapter.py <项目目录> -> 调盲审重新审核。
""")


if __name__ == '__main__':
    main()