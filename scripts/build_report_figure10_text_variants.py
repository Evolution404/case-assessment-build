#!/usr/bin/env python3
"""Generate four text-label variants for review-only Figure 10.

Layout, photos, crops and magnifier geometry stay identical across variants.
Only the annotation typography changes so the reviewer can compare fairly.
This script does not modify the report or existing Figure 9.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import build_report_figure10_review as base
from management_figure_style import FigureCanvas

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".build" / "figure10-text-variants"
CONTACT = ROOT / ".build" / "review-图10-文字方案-A-D对比.png"

SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
RED = "#A93B32"
DARK = "#30343A"
MUTED = "#555B63"
WHITE = "#FFFFFF"
BORDER = "#D8DCE1"

LABELS = [
    (base.LEFT_X + 18, base.MAIN_Y + 14, "5月25日", "反馈照片"),
    (base.RIGHT_X + 18, base.MAIN_Y + 14, "5月22日", "反馈照片"),
    (base.LEFT_SUPPORT_X + 18, base.SUPPORT_Y + 14, "5月25日", "告警照片"),
    (base.RIGHT_SUPPORT_X + 18, base.SUPPORT_Y + 14, "5月22日", "告警照片"),
]


def _font(path: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, round(size * 2))


def _draw_split_line(c: FigureCanvas, x: float, y: float, date: str, kind: str, *, font_path: str, date_size: float, kind_size: float, gap: float = 18) -> None:
    fd = _font(font_path, date_size)
    fk = _font(font_path, kind_size)
    sx, sy = c._s(x), c._s(y)
    c.draw.text((sx, sy), date, font=fd, fill=RED)
    bb = c.draw.textbbox((sx, sy), date, font=fd)
    kind_x = bb[2] + c._s(gap)
    # Align optical baseline by nudging smaller type down slightly.
    kind_y = sy + c._s(max(0, (date_size - kind_size) * 0.30))
    c.draw.text((kind_x, kind_y), kind, font=fk, fill=DARK)


def _label_a(c: FigureCanvas, x: float, y: float, date: str, kind: str) -> None:
    # A: clean journal sans-serif. Date carries accent; type stays neutral.
    _draw_split_line(c, x, y, date, kind, font_path=SANS, date_size=30, kind_size=26, gap=18)


def _label_b(c: FigureCanvas, x: float, y: float, date: str, kind: str) -> None:
    # B: Songti/serif academic style, regular weight, no outline or shadow.
    _draw_split_line(c, x, y, date, kind, font_path=SONGTI, date_size=31, kind_size=27, gap=16)


def _label_c(c: FigureCanvas, x: float, y: float, date: str, kind: str) -> None:
    # C: compact journal tag with a flat white backing for predictable legibility.
    fd = _font(SANS, 27)
    fk = _font(SANS, 24)
    sx, sy = c._s(x), c._s(y)
    date_bb = c.draw.textbbox((0, 0), date, font=fd)
    kind_bb = c.draw.textbbox((0, 0), kind, font=fk)
    gap = c._s(16)
    pad_x, pad_y = c._s(11), c._s(8)
    text_w = (date_bb[2] - date_bb[0]) + gap + (kind_bb[2] - kind_bb[0])
    text_h = max(date_bb[3] - date_bb[1], kind_bb[3] - kind_bb[1])
    box = [sx - pad_x, sy - pad_y, sx + text_w + pad_x, sy + text_h + pad_y + c._s(3)]
    c.draw.rectangle(box, fill=WHITE, outline=BORDER, width=max(1, c._s(0.8)))
    c.draw.text((sx, sy), date, font=fd, fill=RED)
    c.draw.text((sx + (date_bb[2] - date_bb[0]) + gap, sy + c._s(1)), kind, font=fk, fill=DARK)


def _label_d(c: FigureCanvas, x: float, y: float, date: str, kind: str) -> None:
    # D: two-line hierarchy; date is primary, photo type is subordinate.
    fd = _font(SANS, 30)
    fk = _font(SANS, 23)
    sx, sy = c._s(x), c._s(y)
    c.draw.text((sx, sy), date, font=fd, fill=RED)
    c.draw.text((sx, sy + c._s(38)), kind, font=fk, fill=MUTED)


VARIANTS = {
    "A": ("无衬线期刊风", _label_a),
    "B": ("宋体论文风", _label_b),
    "C": ("白底小标签风", _label_c),
    "D": ("两级两行风", _label_d),
}


def _render_base() -> tuple[FigureCanvas, list[tuple[str, float, float, float, float]]]:
    c = FigureCanvas(width=base.W, height=base.H, scale=2)

    feedback_525 = base._open(base.PHOTO["525_feedback"])
    feedback_522 = base._open(base.PHOTO["522_feedback"])
    order_525 = base._open(base.PHOTO["525_workorder"])
    order_522 = base._open(base.PHOTO["522_workorder"])

    base._paste_main(c, feedback_525, base.LEFT_X, base.MAIN_Y, base.MAIN_W, base.MAIN_H)
    base._paste_main(c, feedback_522, base.RIGHT_X, base.MAIN_Y, base.MAIN_W, base.MAIN_H)

    left_box = (base.LEFT_SUPPORT_X, base.SUPPORT_Y, base.SUPPORT_W, base.SUPPORT_H)
    right_box = (base.RIGHT_SUPPORT_X, base.SUPPORT_Y, base.SUPPORT_W, base.SUPPORT_H)
    map_l = base._paste_support_with_mapper(c, order_525, *left_box)
    map_r = base._paste_support_with_mapper(c, order_522, *right_box)
    base._magnifier(c, order_525, left_box, map_l, base.ZOOM["a"], side="left")
    base._magnifier(c, order_522, right_box, map_r, base.ZOOM["b"], side="right")
    return c, []


def render_variant(key: str, title: str, drawer) -> Path:
    c, _ = _render_base()
    for x, y, date, kind in LABELS:
        drawer(c, x, y, date, kind)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"方案{key}-{title}.png"
    c.save(path)
    return path


def build_contact(paths: list[tuple[str, str, Path]]) -> Path:
    thumb_w, thumb_h = 700, 525
    margin = 26
    header_h = 48
    sheet = Image.new("RGB", (margin * 3 + thumb_w * 2, margin * 3 + (header_h + thumb_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(SANS, 26)
    meta_font = ImageFont.truetype(SANS, 22)
    for i, (key, title, path) in enumerate(paths):
        row, col = divmod(i, 2)
        x = margin + col * (thumb_w + margin)
        y = margin + row * (header_h + thumb_h + margin)
        draw.text((x, y), f"方案{key}  {title}", font=title_font, fill="#25272A")
        img = Image.open(path).convert("RGB")
        img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        px = x + (thumb_w - img.width) // 2
        py = y + header_h + (thumb_h - img.height) // 2
        sheet.paste(img, (px, py))
        draw.rectangle((px, py, px + img.width - 1, py + img.height - 1), outline="#C9CDD2", width=1)
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, "PNG", optimize=True)
    return CONTACT


def main() -> None:
    outputs = []
    for key, (title, drawer) in VARIANTS.items():
        path = render_variant(key, title, drawer)
        outputs.append((key, title, path))
        print(f"[variant {key}] {path}")
    contact = build_contact(outputs)
    print(f"[contact] {contact}")


if __name__ == "__main__":
    main()
