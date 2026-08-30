#!/usr/bin/env python3
import os, shutil, sqlite3, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
checks = {
    "python": Path(sys.executable).exists(),
    "node": Path(os.environ.get("NODE", "node")).exists() or shutil.which(os.environ.get("NODE", "node")),
    "chrome": Path(os.environ.get("CHROME_PATH", "")).exists(),
    "soffice": bool(shutil.which("soffice")),
    "pdftotext": bool(shutil.which("pdftotext")),
    "tesseract": bool(shutil.which("tesseract")),
    "sqlite3": bool(shutil.which("sqlite3")),
    "content": (root / "content/case.json").exists(),
}
for name, ok in checks.items():
    print(f"[doctor] {'OK' if ok else 'MISSING'} {name}")
if not all(checks.values()):
    raise SystemExit(2)

