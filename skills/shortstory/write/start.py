#!/usr/bin/env python3
"""
shortstory-write 入口脚本。唯一入口。

用法: python start.py <项目目录> [--resume|--advance|--finalize]

功能:
  1. 运行 validate_chapter.py 字数门禁 + 状态推进
  2. 读取 write_status.json 确定当前进度
  3. 输出当前状态和下一步指令给主 agent

参数:
  --resume   续写（跳过字数门禁错误，仅显示状态）
  --advance  将当前章标记为 passed，推进到下一章（子 agent 盲审通过后用）
  --finalize 全篇终审通过后用（≥95 分），标记定稿
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
        print("用法: python start.py <项目目录> [--resume|--advance|--finalize]")
        sys.exit(1)

    proj = Path(sys.argv[1])
    args = set(sys.argv[2:])
    script_dir = Path(__file__).parent
    validate_script = script_dir / "validate_chapter.py"
    status_file = proj / "write_status.json"

    # 1. 先跑字数门禁（除非 --resume 跳过）
    if "--resume" not in args and validate_script.exists():
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
  状态: 首次启动，尚无 write_status.json

  请按以下顺序执行:
    1. 按 章节规划.md 写第一章，追加到 正文.md
    2. 运行 python start.py <项目目录>
       - 字数门禁自动校验
       - 字数达到目标 -> 状态变为 in_review
    3. in_review 状态下 spawn 全新子 agent 做盲审
    4. 零阻断 -> --advance 推进
       有阻断 -> 修改正文.md 后重跑本脚本
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

    # --advance: 当前章标记 passed，推进到下一章
    if "--advance" in args:
        if loop == "chapter" and str(cc) in status["chapters"]:
            status["chapters"][str(cc)]["status"] = "passed"
            # 重新推进指针（validate_chapter 也会做，但这里先推）
            nxt = None
            for k in sorted(status["chapters"], key=int):
                if status["chapters"][k].get("status") != "passed":
                    nxt = int(k)
                    break
            if nxt is not None:
                status["current_chapter"] = nxt
            elif loop == "chapter":
                status["loop"] = "final_review"
            status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')
            print_step("已推进", f"第{cc}章标记为 passed")
            if nxt is not None:
                nxt_plan = status["chapter_plan"].get(str(nxt), {})
                print(f"  下一章: 第{nxt}章（目标{nxt_plan.get('target_chars', 0)}字）")
            else:
                print("  所有章节已通过，进入全篇终审阶段。")
        return

    # --finalize: 全篇终审标记定稿
    if "--finalize" in args:
        if loop == "final_review":
            status["final_review"]["status"] = "passed"
            status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')
            print_step("定稿", f"项目 {status.get('project')} 已定稿")
        else:
            print("  尚未进入全篇终审阶段。")
        return

    # 3. 根据状态输出指令
    if loop == "final_review":
        frs = status.get("final_review", {}).get("status", "pending")
        if frs == "passed":
            print_step("已完成", f"项目 {status.get('project')} 已定稿")
        else:
            report_path = proj / '审查报告' / '审查报告.md'
            print_step("全篇终审", "所有章节已通过，需要全篇盲审")
            print("""
  请执行:
    1. 从 正文.md 读取完整正文
    2. 加载 skill shortstory-review
    3. spawn 全新子 agent 做全篇盲审（不要复用之前的子 agent）
    4. 子 agent 参考 shortstory-review/SKILL.md 标准：
       - 六维度评分
       - 标记阻断问题
       - 给出总分
    5. 子 agent 返回后:
       有阻断或总分 < 95 -> 修正文.md，然后重跑本脚本
       无阻断且 ≥ 95 -> 运行 python start.py <项目目录> --finalize
""")
            if report_path.exists():
                print(f"  上次审查报告: {report_path}")
        return

    state_map = {
        "pending": ("待开写", f"第{cc}章「{plan.get('title', '')}」目标{target}字"),
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
    1. 按章节规划写第N章，追加到 正文.md
    2. 运行 python start.py <项目目录>
       -> 字数通过后进入 in_review ->  spawn 子 agent 盲审
""")
    elif s == "writing":
        if actual < target:
            print(f"  [WARN] 字数不足: 当前{actual}字, 目标{target}字, 还差{target - actual}字")
        print("""  写完或修改后，运行 python start.py <项目目录> 校验字数。""")
    elif s == "in_review":
        print("""
  字数已通过。请执行:
    1. 加载 skill shortstory-review
    2. spawn 全新子 agent 做盲审
       - 子 agent 读 正文.md + shortstory-review/SKILL.md
       - 按六维度评分，标记阻断
       - 返回 JSON 格式结果
    3. 子 agent 返回后:
       有阻断 -> 修改正文.md 修复，然后重跑本脚本（回到 in_review 重审）
       零阻断 -> 运行 python start.py <项目目录> --advance
""")
    elif s == "blocking":
        report_path = proj / '审查报告' / '审查报告.md'
        if report_path.exists():
            text = report_path.read_text('utf-8')
            lines = text.split('\n')
            in_block = False
            print("  上次审查发现的阻断问题:")
            for line in lines:
                if line.startswith('## 阻断问题'):
                    in_block = True
                elif line.startswith('## ') and in_block:
                    break
                elif in_block and line.startswith('- 🔴'):
                    print(f"    {line.strip()}")
        print(f"""
  请根据审查报告修改正文.md，修完后运行:
    python start.py <项目目录>
  -> 字数校验 -> in_review -> 重新 spawn 子 agent 盲审
""")


if __name__ == '__main__':
    main()