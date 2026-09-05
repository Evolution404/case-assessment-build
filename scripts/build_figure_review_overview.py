#!/usr/bin/env python3
"""Build a single contact sheet for reviewing the ten approved case figures."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "dist" / "figures"
OUT = ROOT / "dist" / "review" / "案例报告10图审核总览.png"

FIGURES = [
    "01-外协管理两大痛点.png",
    "02-省域线路杆塔任务规模.png",
    "03-增效提质总体模型.png",
    "04-外协任务数字化筛选流程.png",
    "05-交叉跨越自动筛查.png",
    "06-鸟类活动重点区域筛查.png",
    "07-集中燃放点周边杆塔筛查.png",
    "08-照片质量督查流程与示例.png",
    "09-告警工单照片全量查重成果.png",
    "10-外协管理前后对比.png",
]


def font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def fit_image(path: Path, max_w: int, max_h: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = min(max_w / image.width, max_h / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def main():
    missing = [name for name in FIGURES if not (FIG / name).exists()]
    if missing:
        raise FileNotFoundError("审核总览缺少正式图片：" + "、".join(missing))

    page_w = 3200
    margin = 70
    gap = 50
    header_h = 150
    card_w = (page_w - margin * 2 - gap) // 2
    card_h = 980
    label_h = 78
    image_h = card_h - label_h - 24
    page_h = header_h + margin + card_h * 5 + gap * 4 + margin
    canvas = Image.new("RGB", (page_w, page_h), "#F4F5F6")
    draw = ImageDraw.Draw(canvas)
    title_font = font(58, bold=True)
    label_font = font(34, bold=True)
    note_font = font(28)
    draw.text((margin, 42), "案例报告 10 图审核总览", fill="#20242A", font=title_font)
    draw.text((page_w - margin, 58), "正式数据链 · 暂未替换 Word", fill="#737B86", font=note_font, anchor="ra")

    for index, name in enumerate(FIGURES):
        row, col = divmod(index, 2)
        x = margin + col * (card_w + gap)
        y = header_h + margin + row * (card_h + gap)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=22, fill="#FFFFFF", outline="#D9DEE4", width=2)
        draw.text((x + 26, y + 20), name.removesuffix(".png"), fill="#20242A", font=label_font)
        image = fit_image(FIG / name, card_w - 48, image_h)
        image_x = x + (card_w - image.width) // 2
        image_y = y + label_h + 14 + (image_h - image.height) // 2
        canvas.paste(image, (image_x, image_y))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, format="PNG", optimize=True)
    print(f"[review-overview] {OUT}")


if __name__ == "__main__":
    main()
