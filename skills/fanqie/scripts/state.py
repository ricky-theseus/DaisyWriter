#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "publish-state.json"


def load_state(path: Path = STATE_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"published": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(data: Dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_published(file_path: str, state: Dict[str, Any]) -> bool:
    return any(item.get("file") == file_path for item in state.get("published", []))


def mark_published(file_path: str, title: str, mode: str, schedule_at: str | None = None, path: Path = STATE_PATH) -> None:
    state = load_state(path)
    if is_published(file_path, state):
        return
    state.setdefault("published", []).append(
        {
            "file": file_path,
            "title": title,
            "mode": mode,
            "scheduleAt": schedule_at,
            "recordedAt": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_state(state, path)


if __name__ == "__main__":
    print(json.dumps(load_state(), ensure_ascii=False, indent=2))
