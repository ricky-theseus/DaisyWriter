#!/usr/bin/env python3
"""
shortstory-batch 进度管理脚本（场景级）。

用法:
  python batch.py <项目目录> status                    — 查看当前进度
  python batch.py <项目目录> advance                   — 当前批标记通过，推进到下一批
  python batch.py <项目目录> block                     — 当前批标记阻断
  python batch.py <项目目录> reset [场景号]             — 重置指定场景为 pending（不传则重置全部）

进度文件: {项目目录}/batch_progress.json
"""
import io, json, sys, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BATCH_SIZE = 5  # 每批场景数


def parse_scene_plan(text):
    """从 场景规划.md 中解析场景列表。"""
    scenes = []
    for m in re.finditer(r'^\|\s*(\d+)\s*\|', text, re.MULTILINE):
        num = int(m.group(1))
        scenes.append({"scene": num, "status": "pending", "blocked_count": 0})
    return sorted(scenes, key=lambda s: s["scene"])


def load_or_init(proj):
    status_file = proj / 'batch_progress.json'
    plan_file = proj / '场景规划.md'

    if status_file.exists():
        return json.loads(status_file.read_text('utf-8'))

    if not plan_file.exists():
        print(f"[ERROR] 未找到 {plan_file}")
        sys.exit(1)

    plan = parse_scene_plan(plan_file.read_text('utf-8'))
    if not plan:
        print(f"[ERROR] 无法从场景规划.md 解析场景")
        sys.exit(1)

    # 计算批次
    total = len(plan)
    batches = []
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_scenes = [s["scene"] for s in plan[start:end]]
        batches.append({
            "batch_id": len(batches) + 1,
            "scenes": batch_scenes,
            "status": "pending",
            "blocked_count": 0,
        })

    status = {
        "project": proj.name,
        "total_scenes": total,
        "scenes": {str(s["scene"]): {
            "status": "pending",
            "blocked_count": 0,
        } for s in plan},
        "batches": batches,
        "current_batch_index": 0,
    }
    status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')
    return status


def save(status, proj):
    (proj / 'batch_progress.json').write_text(
        json.dumps(status, ensure_ascii=False, indent=2), 'utf-8')


def get_current_batch(status):
    idx = status["current_batch_index"]
    if idx < len(status["batches"]):
        return status["batches"][idx]
    return None


def cmd_status(proj):
    status = load_or_init(proj)
    total = status["total_scenes"]
    done = sum(1 for s in status["scenes"].values() if s["status"] == "passed")
    blocked = sum(1 for s in status["scenes"].values() if s["status"] == "blocked")

    print(f"项目: {status['project']}")
    print(f"进度: {done}/{total} 场景完成, {blocked} 场景阻断")
    print()

    # 打印批次概况
    for batch in status["batches"]:
        batch_id = batch["batch_id"]
        scenes = batch["scenes"]
        bs = batch["status"]
        marker = " →" if status["batches"].index(batch) == status["current_batch_index"] else "  "
        icon = {"pending": "○", "in_review": "◎", "passed": "✓", "blocked": "✗", "writing": "✎"}
        print(f"  {icon.get(bs, '?')} 批{batch_id}: 场景{scenes[0]}-{scenes[-1]} ({len(scenes)}个){marker}")
        if bs == "blocked":
            print(f"      阻断 {batch['blocked_count']} 次")

    current = get_current_batch(status)
    if current:
        print(f"\n当前: 批{current['batch_id']} 场景{current['scenes'][0]}-{current['scenes'][-1]} 状态={current['status']}")
    else:
        print("\n全部场景已完成!")


def cmd_advance(proj):
    status = load_or_init(proj)
    current = get_current_batch(status)
    if not current:
        print("所有批次已完成，无需推进")
        return

    # 标记当前批中的所有场景为 passed
    for s in current["scenes"]:
        status["scenes"][str(s)]["status"] = "passed"
    current["status"] = "passed"

    # 找下一个未完成的批次
    nxt_idx = None
    for i, b in enumerate(status["batches"]):
        if b["status"] != "passed" and b["status"] != "blocked":
            nxt_idx = i
            break
    if nxt_idx is None:
        # 标记所有 blocked 之后的批次... 实际上，找第一个当前之后未 blocked 的
        for i in range(status["current_batch_index"] + 1, len(status["batches"])):
            if status["batches"][i]["status"] != "blocked":
                nxt_idx = i
                break

    scene_str = f"场景{current['scenes'][0]}-{current['scenes'][-1]}"
    if nxt_idx is not None:
        status["current_batch_index"] = nxt_idx
        next_scenes = status["batches"][nxt_idx]["scenes"]
        print(f"{scene_str} 通过 → 推进到 场景{next_scenes[0]}-{next_scenes[-1]}")
    else:
        status["current_batch_index"] = len(status["batches"])
        print(f"{scene_str} 通过 → 全部场景完成!")
    save(status, proj)


def cmd_block(proj):
    status = load_or_init(proj)
    current = get_current_batch(status)
    if not current:
        print("没有活跃批次可阻断")
        return

    current["blocked_count"] = current.get("blocked_count", 0) + 1
    scene_str = f"场景{current['scenes'][0]}-{current['scenes'][-1]}"

    if current["blocked_count"] >= 3:
        current["status"] = "blocked"
        for s in current["scenes"]:
            status["scenes"][str(s)]["status"] = "blocked"
        print(f"{scene_str} 阻断已达3次 → 标记 blocked，跳过")
    else:
        current["status"] = "blocking"
        print(f"{scene_str} 阻断 (第{current['blocked_count']}次)")
    save(status, proj)


def cmd_reset(proj, scene=None):
    status = load_or_init(proj)
    if scene:
        s = status["scenes"].get(str(scene))
        if s:
            s["status"] = "pending"
            s["blocked_count"] = 0
            print(f"场景{scene} 已重置为 pending")
            # 重置包含该场景的批次
            for batch in status["batches"]:
                if scene in batch["scenes"]:
                    batch["status"] = "pending"
                    batch["blocked_count"] = 0
                    status["current_batch_index"] = status["batches"].index(batch)
                    break
    else:
        for s in status["scenes"].values():
            s["status"] = "pending"
            s["blocked_count"] = 0
        for batch in status["batches"]:
            batch["status"] = "pending"
            batch["blocked_count"] = 0
        status["current_batch_index"] = 0
        print("全部场景已重置")
    save(status, proj)


def main():
    if len(sys.argv) < 3:
        print("用法: python batch.py <项目目录> <status|advance|block|reset> [场景号]")
        sys.exit(1)

    proj = Path(sys.argv[1])
    if not proj.is_dir():
        print(f"[ERROR] 目录不存在: {proj}")
        sys.exit(1)

    cmd = sys.argv[2]
    if cmd == "status":
        cmd_status(proj)
    elif cmd == "advance":
        cmd_advance(proj)
    elif cmd == "block":
        cmd_block(proj)
    elif cmd == "reset":
        ch = int(sys.argv[3]) if len(sys.argv) >= 4 else None
        cmd_reset(proj, ch)
    else:
        print(f"[ERROR] 未知命令: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
