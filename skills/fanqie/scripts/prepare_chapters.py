#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from typing import Dict, List

HEADING_RE = re.compile(r"^#\s*(.+?)\s*$")
FILENAME_RE = re.compile(r"^(第\d+章)[_\s-]*(.+?)?\.md$", re.IGNORECASE)
TITLE_SPLIT_RE = re.compile(r"^(第\d+章)[：:\s]+(.+)$")


def clean_body(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if lines and HEADING_RE.match(lines[0].strip()):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    return body


def title_from_file(path: Path) -> str:
    m = FILENAME_RE.match(path.name)
    if not m:
        return path.stem
    prefix = m.group(1)
    suffix = (m.group(2) or "").strip(" _-")
    return f"{prefix} {suffix}".strip()


def split_serial_and_title(title: str) -> tuple[str | None, str]:
    m = TITLE_SPLIT_RE.match(title.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, title.strip()


def parse_chapter(path: Path) -> Dict:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    heading = None
    if lines:
        m = HEADING_RE.match(lines[0].strip())
        if m:
            heading = m.group(1).strip()
    title = heading or title_from_file(path)
    serial, pure_title = split_serial_and_title(title)
    body = clean_body(raw)
    return {
        "file": str(path),
        "name": path.name,
        "title": title,
        "serial": serial,
        "display_title": pure_title,
        "word_count": len(body),
        "preview": body[:120].replace("\n", " "),
        "content": body,
    }


def collect(directory: Path) -> List[Dict]:
    files = sorted([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".md"])
    chapters: List[Dict] = []
    for p in files:
        try:
            chapters.append(parse_chapter(p))
        except Exception as e:
            print(f"WARN prepare_chapters skip: {p} :: {e}", file=sys.stderr)
    return chapters


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare Fanqie chapters from markdown files")
    ap.add_argument("--dir", required=True, help="Directory containing markdown chapter files")
    ap.add_argument("--preview", action="store_true", help="Print a human preview instead of full JSON")
    ap.add_argument("--output", help="Write JSON to file")
    args = ap.parse_args()

    directory = Path(args.dir).expanduser()
    chapters = collect(directory)

    if args.output:
        out = Path(args.output).expanduser()
        out.write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.preview:
        print(f"章节数: {len(chapters)}")
        for idx, ch in enumerate(chapters, 1):
            print(f"[{idx}] {ch['title']} | 字数: {ch['word_count']} | 文件: {ch['name']}")
            print(f"    预览: {ch['preview']}")
        return

    print(json.dumps(chapters, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
