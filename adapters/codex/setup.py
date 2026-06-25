"""
Codex CLI adapter setup for DaisyWriter.

Creates `.codex/skills/<name>/SKILL.md` stubs that reference
the real skill files in the DaisyWriter `skills/` directory.
"""

import json
import os
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills"
CODEX_DIR = Path.cwd() / ".codex" / "skills"

SKILL_MAP = {
    # webnovel
    "webnovel-init": "webnovel/init",
    "webnovel-plan": "webnovel/plan",
    "webnovel-write": "webnovel/write",
    "webnovel-batch": "webnovel/batch",
    "webnovel-craft": "webnovel/craft",
    "webnovel-review": "webnovel/review",
    "webnovel-review-settings": "webnovel/review-settings",
    "webnovel-deconstruct": "webnovel/deconstruct",
    "webnovel-query": "webnovel/query",
    "webnovel-learn": "webnovel/learn",
    "webnovel-doctor": "webnovel/doctor",
    "webnovel-dashboard": "webnovel/dashboard",
    # shortstory
    "shortstory-init": "shortstory/init",
    "shortstory-write": "shortstory/write",
    "shortstory-review": "shortstory/review",
    "shortstory-craft": "shortstory/craft",
    "shortstory-deconstruct": "shortstory/deconstruct",
    # tech
    "tech-write": "tech/write",
    "tech-deconstruct": "tech/deconstruct",
    "tech-batch": "tech/batch",
    "sync-csdn": "tech/sync-csdn",
    "csdn-upload": "tech/csdn-upload",
    # fanqie
    "fanqie-publish": "fanqie",
    # cover-maker
    "cover-maker": "cover-maker",
}


def setup():
    base = SKILL_DIR
    if not base.exists():
        print(f"Error: skills directory not found at {base}")
        sys.exit(1)

    CODEX_DIR.mkdir(parents=True, exist_ok=True)

    for name, rel_path in SKILL_MAP.items():
        skill_dir = base / rel_path
        target_dir = CODEX_DIR / name
        target_skill = target_dir / "SKILL.md"

        if not skill_dir.exists():
            print(f"  ⚠  Skipping {name}: source not found at {skill_dir}")
            continue

        source_skill = skill_dir / "SKILL.md"
        if not source_skill.exists():
            print(f"  ⚠  Skipping {name}: no SKILL.md at {source_skill}")
            continue

        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy SKILL.md
        shutil.copy2(source_skill, target_skill)

        # Copy references/ if exists
        src_refs = skill_dir / "references"
        dst_refs = target_dir / "references"
        if src_refs.exists() and not dst_refs.exists():
            shutil.copytree(src_refs, dst_refs, ignore=lambda d, files: {"__pycache__"})

        # Copy scripts/ if exists
        src_scripts = skill_dir / "scripts"
        dst_scripts = target_dir / "scripts"
        if src_scripts.exists() and not dst_scripts.exists():
            shutil.copytree(src_scripts, dst_scripts, ignore=lambda d, files: {"__pycache__"})

        # Copy evals/ if exists
        src_evals = skill_dir / "evals"
        dst_evals = target_dir / "evals"
        if src_evals.exists() and not dst_evals.exists():
            shutil.copytree(src_evals, dst_evals, ignore=lambda d, files: {"__pycache__"})

        print(f"  ✓ {name} → .codex/skills/{name}/")

    print(f"\nDone. {len(SKILL_MAP)} skills installed to {CODEX_DIR}")


if __name__ == "__main__":
    setup()