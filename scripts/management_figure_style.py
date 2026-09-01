"""Shared Nature-style visual language for management figures.

The style is intentionally restrained: white background, thin rules, low-saturation
accent colours, compact typography and generous whitespace. Management logic is
always visually dominant; technical methods are secondary annotations.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle

# Paper-like palette: restrained and colour-blind-friendly enough for print use.
WHITE = "#FFFFFF"
INK = "#202124"
MUTED = "#666B73"
FAINT = "#8A9099"
RULE = "#D9DDE3"
RULE_LIGHT = "#ECEEF1"
BLUE = "#356A9A"
BLUE_DARK = "#244D70"
BLUE_TINT = "#EEF4F8"
AMBER = "#B7752A"
AMBER_DARK = "#86551F"
AMBER_TINT = "#FBF4EA"
TEAL = "#4D7D73"
TEAL_DARK = "#365D55"
TEAL_TINT = "#EEF5F2"
RED = "#A95046"
RED_TINT = "#FAEFED"
GRAY = "#7D838A"
GRAY_TINT = "#F4F5F6"

def _pick_font_family() -> str:
    candidates = [
        "PingFang SC",
        "Hiragino Sans GB",
        "Microsoft YaHei",
        "Noto Sans CJK SC",
        "SimHei",
        "Arial Unicode MS",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    return next((name for name in candidates if name in installed), "sans-serif")


plt.rcParams.update({
    "font.family": _pick_font_family(),
    "axes.unicode_minus": False,
    "savefig.transparent": False,
    "figure.facecolor": WHITE,
})


def make_canvas(title: str, subtitle: str | None = None):
    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(0.72, 8.38, title, fontsize=22, weight="semibold", color=INK, va="center")
    if subtitle:
        ax.text(0.72, 8.00, subtitle, fontsize=10.8, color=MUTED, va="center")
        rule_y = 7.72
    else:
        rule_y = 7.90
    ax.plot([0.72, 15.28], [rule_y, rule_y], color=RULE, lw=0.8)
    return fig, ax, rule_y


def txt(ax, x, y, value, *, size=12.5, color=INK, weight="normal", ha="left", va="center", z=5, rotation=0):
    resolved_weight = 600 if weight in {"semibold", "medium", "bold"} else weight
    return ax.text(
        x, y, value, fontsize=size, color=color, weight=resolved_weight,
        ha=ha, va=va, zorder=z, rotation=rotation,
    )


def rect(ax, x, y, w, h, *, fc=WHITE, ec=RULE, lw=0.9, radius=0.08, z=1):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z,
    )
    ax.add_patch(patch)
    return patch


def node(ax, x, y, w, h, label, *, edge=RULE, fill=WHITE, color=INK, size=13.2, weight="semibold", radius=0.07):
    rect(ax, x, y, w, h, fc=fill, ec=edge, lw=0.9, radius=radius)
    txt(ax, x + w / 2, y + h / 2, label, size=size, color=color, weight=weight, ha="center")


def chip(ax, x, y, label, *, edge=RULE, fill=WHITE, color=MUTED, size=10.5, width=None):
    if width is None:
        width = max(1.0, 0.28 * len(label) + 0.42)
    h = 0.38
    rect(ax, x, y, width, h, fc=fill, ec=edge, lw=0.75, radius=0.18)
    txt(ax, x + width / 2, y + h / 2, label, size=size, color=color, weight="medium", ha="center")
    return width


def arrow(ax, start, end, *, color=FAINT, lw=1.25, mutation=12, z=3, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=mutation,
        color=color, linewidth=lw, zorder=z,
        shrinkA=0, shrinkB=0,
    ))


def line(ax, start, end, *, color=RULE, lw=0.9, z=2, ls="-"):
    ax.plot([start[0], end[0]], [start[1], end[1]], color=color, lw=lw, zorder=z, ls=ls)


def dot(ax, x, y, *, color=BLUE, r=0.055, z=4):
    ax.add_patch(Circle((x, y), r, facecolor=color, edgecolor="none", zorder=z))


def metric(ax, x, y, value, label, *, color=BLUE, align="left"):
    ha = "left" if align == "left" else "right"
    txt(ax, x, y, value, size=18, color=color, weight="semibold", ha=ha)
    txt(ax, x, y - 0.34, label, size=10.5, color=MUTED, ha=ha)


def lane_tag(ax, x, y, label, *, color=BLUE, tint=BLUE_TINT, width=1.32):
    rect(ax, x, y, width, 0.46, fc=tint, ec=color, lw=0.8, radius=0.20)
    txt(ax, x + width / 2, y + 0.23, label, size=11.5, color=color, weight="semibold", ha="center")


def section_label(ax, x, y, label, *, color=MUTED):
    txt(ax, x, y, label.upper(), size=9.4, color=color, weight="semibold")


def bracket_label(ax, x, y0, y1, label, *, color=RULE, text_color=MUTED):
    line(ax, (x, y0), (x, y1), color=color, lw=0.9)
    line(ax, (x, y0), (x + 0.16, y0), color=color, lw=0.9)
    line(ax, (x, y1), (x + 0.16, y1), color=color, lw=0.9)
    txt(ax, x - 0.08, (y0 + y1) / 2, label, size=9.7, color=text_color, ha="right", rotation=90)


def save_figure(fig, out_dir: Path, filename: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    fig.savefig(path, dpi=160, facecolor=WHITE, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"[management-figure] {path}")
