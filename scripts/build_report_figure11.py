#!/usr/bin/env python3
"""Copy the editable project-owned Figure 11 source into dist/confirm.

The source image is intentionally kept inside assets/images so it can be edited
manually in place. Report builds always consume the latest saved project copy.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "images" / "report-11-照片查重管理通报.png"
OUT = ROOT / "dist" / "confirm" / "10-照片查重管理通报证据.png"


def build() -> Path:
    if not SOURCE.exists():
        raise FileNotFoundError(f"缺少项目内图11源图：{SOURCE}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, OUT)
    print(f"[report-figure11] project source -> {OUT}")
    return OUT


if __name__ == "__main__":
    build()
