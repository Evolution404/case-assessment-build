#!/usr/bin/env python3
"""Build the approved C2 composite for report Figure 10.

The evidence-photo geometry and 18x local magnifier reuse the reviewed Figure 10
layout. Labels use the approved C2 treatment: pale-red date segment + white
photo-type segment. This script writes the formal figure into dist/confirm.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw, ImageFont

import build_report_figure10_review as base

FigureCanvas = base.FigureCanvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "confirm" / "09-告警工单反馈照片与告警照片对照.png"

SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
RED = "#A63A32"
DARK = "#30343A"
WHITE = "#FFFFFF"
BORDER = "#D7DBE0"
PALE_RED = "#F6E9E7"

LABELS = [
    (base.LEFT_X + 14, base.MAIN_Y + 12, "5月25日", "反馈照片"),
    (base.RIGHT_X + 14, base.MAIN_Y + 12, "5月22日", "反馈照片"),
    (base.LEFT_SUPPORT_X + 14, base.SUPPORT_Y + 12, "5月25日", "告警照片"),
    (base.RIGHT_SUPPORT_X + 14, base.SUPPORT_Y + 12, "5月22日", "告警照片"),
]


def _font(size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(SANS, round(size * 2))


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _label_c2(c: FigureCanvas, x: float, y: float, date: str, kind: str) -> None:
    """Approved C2 label: emphasized date segment plus neutral photo type."""
    date_font = _font(26)
    kind_font = _font(24)
    date_w, date_h = _measure(c.draw, date, date_font)
    kind_w, kind_h = _measure(c.draw, kind, kind_font)

    sx, sy = c._s(x), c._s(y)
    pad_x, pad_y = c._s(11), c._s(7)
    height = max(date_h, kind_h) + 2 * pad_y
    date_segment_w = date_w + 2 * pad_x
    kind_segment_w = kind_w + 2 * pad_x
    x0, y0 = sx - pad_x, sy - pad_y

    c.draw.rectangle(
        [x0, y0, x0 + date_segment_w + kind_segment_w, y0 + height],
        fill=WHITE,
        outline=BORDER,
        width=max(1, c._s(0.8)),
    )
    c.draw.rectangle(
        [x0, y0, x0 + date_segment_w, y0 + height],
        fill=PALE_RED,
    )
    c.draw.line(
        [x0 + date_segment_w, y0, x0 + date_segment_w, y0 + height],
        fill=BORDER,
        width=max(1, c._s(0.8)),
    )
    c.draw.text((sx, sy), date, font=date_font, fill=RED)
    c.draw.text((x0 + date_segment_w + pad_x, sy + c._s(1)), kind, font=kind_font, fill=DARK)


def build() -> Path:
    c = FigureCanvas(width=base.W, height=base.H, scale=2)

    feedback_525 = base._open(base.PHOTO["525_feedback"])
    feedback_522 = base._open(base.PHOTO["522_feedback"])
    order_525 = base._open(base.PHOTO["525_workorder"])
    order_522 = base._open(base.PHOTO["522_workorder"])

    base._paste_main(c, feedback_525, base.LEFT_X, base.MAIN_Y, base.MAIN_W, base.MAIN_H)
    base._paste_main(c, feedback_522, base.RIGHT_X, base.MAIN_Y, base.MAIN_W, base.MAIN_H)

    left_box = (base.LEFT_SUPPORT_X, base.SUPPORT_Y, base.SUPPORT_W, base.SUPPORT_H)
    right_box = (base.RIGHT_SUPPORT_X, base.SUPPORT_Y, base.SUPPORT_W, base.SUPPORT_H)
    map_left = base._paste_support_with_mapper(c, order_525, *left_box)
    map_right = base._paste_support_with_mapper(c, order_522, *right_box)
    base._magnifier(c, order_525, left_box, map_left, base.ZOOM["a"], side="left")
    base._magnifier(c, order_522, right_box, map_right, base.ZOOM["b"], side="right")

    for x, y, date, kind in LABELS:
        _label_c2(c, x, y, date, kind)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    c.save(OUT)
    print(f"[report-figure10] -> {OUT}")
    return OUT


if __name__ == "__main__":
    build()
