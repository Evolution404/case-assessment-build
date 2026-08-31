"""Shared cartographic palette and export helpers for province-scale report figures."""

from pathlib import Path
import shutil


def resolve_soffice() -> str:
    """Return a usable LibreOffice soffice binary for SVG -> EMF export."""
    candidates = [
        shutil.which("soffice"),
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        str(Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        "未找到 LibreOffice soffice，无法生成正式 EMF；请安装 LibreOffice，禁止跳过或伪造 EMF。"
    )


BG = "#F7F7F5"
LAND = "#FEFEFD"
CARD = "#FBFBFA"
WHITE = "#FFFFFF"
TEXT = "#20242A"
MUTED = "#737B86"
FAINT = "#DCE1E6"
DISTRICT = "#B6BDC1"
OUTER = "#828E97"

STYLE = {
    "35": {"label": "35kV", "color": "#C4D2CD", "width": 0.14, "alpha": 0.34, "z": 2},
    "110": {"label": "110kV", "color": "#9DB8CF", "width": 0.18, "alpha": 0.54, "z": 3},
    "220": {"label": "220kV", "color": "#D7B36D", "width": 0.24, "alpha": 0.66, "z": 4},
    "other_dc": {"label": "其他直流", "color": "#B9B2C6", "width": 0.27, "alpha": 0.54, "z": 5},
    "500plus": {"label": "500kV及以上", "color": "#E66F62", "width": 0.42, "alpha": 0.82, "z": 6},
}
