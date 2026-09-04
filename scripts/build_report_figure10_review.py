#!/usr/bin/env python3
"""Build review-only Figure 10 with journal-style main panels + supporting insets.

This script does NOT modify the report or existing Figure 9. The figure keeps
only the four evidence photos and the necessary date labels. The two feedback
photos are the visual main panels; the work-order originals overlap them as
smaller supporting evidence panels, each with a PPT-style local magnifier.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WHITE = "#FFFFFF"


class FigureCanvas:
    """Minimal 2x Pillow canvas used by Figure 10; intentionally dependency-free."""

    def __init__(self, width: int, height: int, scale: int = 2):
        self.width = width
        self.height = height
        self.scale = scale
        self.image = Image.new("RGB", (width * scale, height * scale), WHITE)
        self.draw = ImageDraw.Draw(self.image)

    def _s(self, value: float) -> int:
        return int(round(value * self.scale))

    def line(self, p1: tuple[float, float], p2: tuple[float, float], *, color: str, width: float = 1.5) -> None:
        self.draw.line(
            [(self._s(p1[0]), self._s(p1[1])), (self._s(p2[0]), self._s(p2[1]))],
            fill=color,
            width=max(1, self._s(width)),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.resize((self.width, self.height), Image.Resampling.LANCZOS).save(path, "PNG", optimize=True)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".build" / "review-图10-告警工单反馈照片与工单原图对照.png"
ZOOM = json.loads((ROOT / "content" / "workorder_zoom.json").read_text(encoding="utf-8"))

PHOTO = {
    "525_feedback": ROOT / "assets" / "images" / "reference-demos" / "feedback-0525.webp",
    "522_feedback": ROOT / "assets" / "images" / "reference-demos" / "feedback-0522.webp",
    # User-confirmed visual mapping after the work-order source swap.
    "525_workorder": ROOT / "assets" / "images" / "reference-demos" / "order-0522-workorder.webp",
    "522_workorder": ROOT / "assets" / "images" / "reference-demos" / "order-0525-workorder.webp",
}

W, H = 1448, 1086
INK = "#22252A"
RED = "#C9453D"
KEYLINE = "#34383D"

OUTER_MARGIN = 40
COLUMN_GAP = 6
ROW_GAP = 8
MAIN_Y = 24
MAIN_W = (W - 2 * OUTER_MARGIN - COLUMN_GAP) / 2
MAIN_H = 500
LEFT_X = OUTER_MARGIN
RIGHT_X = LEFT_X + MAIN_W + COLUMN_GAP

# Feedback photos form the upper row; the larger alarm-photo panels form the
# lower row on exactly the same two-column grid.
SUPPORT_W = MAIN_W
SUPPORT_H = 530
SUPPORT_Y = MAIN_Y + MAIN_H + ROW_GAP
LEFT_SUPPORT_X = LEFT_X
RIGHT_SUPPORT_X = RIGHT_X

MAG_W = 220
MAG_H = 156
REPORT_ZOOM_SCALE = 1.5
SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"


def _open(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGB")


def _cover(img: Image.Image, target_w: int, target_h: int, *, focus_y: float = 0.5) -> Image.Image:
    """Aspect-fill with adjustable vertical focus, used for clean journal panels."""
    ratio = max(target_w / img.width, target_h / img.height)
    rw = max(1, round(img.width * ratio))
    rh = max(1, round(img.height * ratio))
    resized = img.resize((rw, rh), Image.Resampling.LANCZOS)
    left = max(0, (rw - target_w) // 2)
    max_top = max(0, rh - target_h)
    top = round(max_top * max(0.0, min(1.0, focus_y)))
    return resized.crop((left, top, left + target_w, top + target_h))


def _paste_main(c: FigureCanvas, img: Image.Image, x: float, y: float, w: float, h: float) -> None:
    # The portrait feedback photos are shown nearly full-frame with no card,
    # no shadow and only a hairline keyline.
    crop = _cover(img, c._s(w), c._s(h), focus_y=0.48)
    c.image.paste(crop, (c._s(x), c._s(y)))
    c.draw = ImageDraw.Draw(c.image)
    c.draw.rectangle(
        [c._s(x), c._s(y), c._s(x + w), c._s(y + h)],
        outline=KEYLINE, width=max(1, c._s(0.8)),
    )


def _paste_support_with_mapper(
    c: FigureCanvas,
    img: Image.Image,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    trim_x: float = 0.035,
    trim_y: float = 0.065,
):
    """Place work-order original as an overlapping 4:3 evidence inset.

    Returns a mapper from original-image coordinates to canvas coordinates so
    the ROI box remains geometrically tied to the original photo.
    """
    sx0 = round(img.width * trim_x)
    sx1 = img.width - sx0
    sy0 = round(img.height * trim_y)
    sy1 = img.height - sy0
    trimmed = img.crop((sx0, sy0, sx1, sy1))

    tw, th = c._s(w), c._s(h)
    scale = max(tw / trimmed.width, th / trimmed.height)
    rw = max(1, round(trimmed.width * scale))
    rh = max(1, round(trimmed.height * scale))
    resized = trimmed.resize((rw, rh), Image.Resampling.LANCZOS)
    left = max(0, (rw - tw) // 2)
    top = max(0, (rh - th) // 2)
    crop = resized.crop((left, top, left + tw, top + th))

    # Keep the support image on the exact same column edges as the main image.
    # No extra matte is drawn, so the center gutter remains a single clean line.
    c.image.paste(crop, (c._s(x), c._s(y)))
    c.draw = ImageDraw.Draw(c.image)
    c.draw.rectangle(
        [c._s(x), c._s(y), c._s(x + w), c._s(y + h)],
        outline=KEYLINE, width=max(1, c._s(1.0)),
    )

    def mapper(src_x: float, src_y: float) -> tuple[float, float]:
        px = (src_x - sx0) * scale - left
        py = (src_y - sy0) * scale - top
        return x + px / c.scale, y + py / c.scale

    return mapper


def _magnifier(
    c: FigureCanvas,
    img: Image.Image,
    support_box: tuple[float, float, float, float],
    mapper,
    cfg: dict,
    *,
    side: str,
) -> None:
    x, y, w, h = support_box
    fx = float(cfg["x"]) * img.width
    fy = float(cfg["y"]) * img.height
    zoom = float(cfg["zoom"]) * REPORT_ZOOM_SCALE

    crop_w = img.width / zoom
    crop_h = crop_w * (MAG_H / MAG_W)
    left = max(0.0, min(img.width - crop_w, fx - crop_w / 2))
    top = max(0.0, min(img.height - crop_h, fy - crop_h / 2))
    detail = img.crop((round(left), round(top), round(left + crop_w), round(top + crop_h)))

    p1 = mapper(left, top)
    p2 = mapper(left + crop_w, top + crop_h)
    rx1 = max(x + 3, min(x + w - 3, p1[0]))
    ry1 = max(y + 3, min(y + h - 3, p1[1]))
    rx2 = max(x + 3, min(x + w - 3, p2[0]))
    ry2 = max(y + 3, min(y + h - 3, p2[1]))
    c.draw.rectangle(
        [c._s(rx1), c._s(ry1), c._s(rx2), c._s(ry2)],
        outline=RED, width=c._s(2.2),
    )

    # Keep both magnifiers away from the center gutter. The left-column inset
    # sits on the outer-left side; the right-column inset sits outer-right.
    if side == "left":
        mx = x + 12
    else:
        mx = x + w - MAG_W - 12
    my = y + h - MAG_H - 12

    detail = detail.resize((c._s(MAG_W), c._s(MAG_H)), Image.Resampling.LANCZOS)
    c.draw.rectangle(
        [c._s(mx - 5), c._s(my - 5), c._s(mx + MAG_W + 5), c._s(my + MAG_H + 5)],
        fill=WHITE,
    )
    c.image.paste(detail, (c._s(mx), c._s(my)))
    c.draw = ImageDraw.Draw(c.image)
    c.draw.rectangle(
        [c._s(mx), c._s(my), c._s(mx + MAG_W), c._s(my + MAG_H)],
        outline=KEYLINE, width=max(1, c._s(1.0)),
    )

    # A restrained red leader line only; no label text inside the figure.
    sx = rx1 if side == "left" else rx2
    sy = (ry1 + ry2) / 2
    ex = mx + MAG_W if side == "left" else mx
    ey = my + MAG_H / 2
    c.line((sx, sy), (ex, ey), color=RED, width=1.2)


def _panel_label(c: FigureCanvas, x: float, y: float, value: str) -> None:
    """Overlay date + photo type directly on the image in red Songti."""
    font = ImageFont.truetype(SONGTI, c._s(27))
    c.draw.text(
        (c._s(x), c._s(y)),
        value,
        font=font,
        fill=RED,
        stroke_width=c._s(1.2),
        stroke_fill=WHITE,
    )


def build() -> Path:
    c = FigureCanvas(width=W, height=H, scale=2)

    feedback_525 = _open(PHOTO["525_feedback"])
    feedback_522 = _open(PHOTO["522_feedback"])
    order_525 = _open(PHOTO["525_workorder"])
    order_522 = _open(PHOTO["522_workorder"])

    # Upper row: feedback photos, deliberately smaller than the alarm-photo row.
    _paste_main(c, feedback_525, LEFT_X, MAIN_Y, MAIN_W, MAIN_H)
    _paste_main(c, feedback_522, RIGHT_X, MAIN_Y, MAIN_W, MAIN_H)
    _panel_label(c, LEFT_X + 18, MAIN_Y + 14, "5月25日 · 反馈照片")
    _panel_label(c, RIGHT_X + 18, MAIN_Y + 14, "5月22日 · 反馈照片")

    # Lower row: larger alarm photos on the same aligned grid.
    left_box = (LEFT_SUPPORT_X, SUPPORT_Y, SUPPORT_W, SUPPORT_H)
    right_box = (RIGHT_SUPPORT_X, SUPPORT_Y, SUPPORT_W, SUPPORT_H)
    map_l = _paste_support_with_mapper(c, order_525, *left_box)
    map_r = _paste_support_with_mapper(c, order_522, *right_box)
    _panel_label(c, LEFT_SUPPORT_X + 18, SUPPORT_Y + 14, "5月25日 · 告警照片")
    _panel_label(c, RIGHT_SUPPORT_X + 18, SUPPORT_Y + 14, "5月22日 · 告警照片")

    _magnifier(c, order_525, left_box, map_l, ZOOM["a"], side="left")
    _magnifier(c, order_522, right_box, map_r, ZOOM["b"], side="right")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    c.save(OUT)
    print(f"[figure10-review] -> {OUT}")
    return OUT


if __name__ == "__main__":
    build()
