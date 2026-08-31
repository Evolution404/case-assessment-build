#!/usr/bin/env python3
"""Generate the six management-oriented figures for the case report.

These figures intentionally put external-workforce management first and keep
algorithms in a supporting role. They read all metrics from content/case.json
so report figures cannot silently drift from the locked narrative baseline.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "figures"
CASE = json.loads((ROOT / "content" / "case.json").read_text(encoding="utf-8"))

BG = "#F7F8FA"
CARD = "#FFFFFF"
TEXT = "#172033"
MUTED = "#687386"
BLUE = "#2F6FDB"
BLUE_DARK = "#174EA6"
BLUE_LIGHT = "#EAF2FF"
ORANGE = "#EA7A25"
ORANGE_LIGHT = "#FFF1E7"
GREEN = "#2C9A5B"
GREEN_LIGHT = "#EAF7F0"
RED = "#D84A3A"
BORDER = "#DCE2EA"
GRAY = "#8B939E"
GRAY_LIGHT = "#F0F2F4"

plt.rcParams.update({
    "font.family": ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "Arial Unicode MS"],
    "axes.unicode_minus": False,
    "savefig.transparent": False,
})


def canvas(title: str):
    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(0.55, 8.48, title, fontsize=25, weight="bold", color=TEXT, va="center")
    ax.plot([0.45, 15.55], [8.08, 8.08], color=BORDER, lw=1.2)
    return fig, ax


def box(ax, x, y, w, h, *, fc=CARD, ec=BORDER, lw=1.3, radius=0.16, z=1):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z,
    )
    ax.add_patch(patch)
    return patch


def text(ax, x, y, value, *, size=14, color=TEXT, weight="normal", ha="left", va="center", z=5, rotation=0):
    return ax.text(x, y, value, fontsize=size, color=color, weight=weight, ha=ha, va=va, zorder=z, rotation=rotation)


def arrow(ax, start, end, *, color=BLUE, lw=2.6, style="-|>", z=3):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=18, color=color, lw=lw, zorder=z))


def header(ax, x, y, w, label, color):
    box(ax, x, y, w, 0.58, fc=color, ec=color, lw=0, radius=0.16)
    text(ax, x + w / 2, y + 0.29, label, size=18, color="white", weight="bold", ha="center")


def metric_row(ax, x, y, metric, desc, color):
    ax.add_patch(Circle((x, y), 0.12, fc=color, ec="none"))
    text(ax, x + 0.28, y, metric, size=17, color=color, weight="bold")
    text(ax, x + 1.62, y, desc, size=13, color=TEXT)


def flow_box(ax, x, y, w, label, *, color=BLUE, light=BLUE_LIGHT, size=15):
    box(ax, x, y, w, 0.62, fc=light, ec=color, lw=1.4, radius=0.12)
    text(ax, x + w / 2, y + 0.31, label, size=size, color=color, weight="bold", ha="center")


def save(fig, filename: str):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fig.savefig(path, dpi=150, facecolor=BG, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"[management-figure] {path}")


def fig01():
    fig, ax = canvas("外协管理两大痛点")
    box(ax, 0.7, 1.45, 5.2, 6.0, fc=CARD, ec=BLUE, lw=1.5, radius=0.18)
    header(ax, 1.2, 7.0, 4.2, "工作量大", BLUE)
    metric_row(ax, 1.35, 6.25, f"{CASE['metrics']['province_poles']/10000:.1f}万基", "杆塔", BLUE_DARK)
    metric_row(ax, 1.35, 5.55, f"{CASE['metrics']['province_lines']}条", "输电线路", BLUE_DARK)
    metric_row(ax, 1.35, 4.85, "多类", "专项任务", BLUE_DARK)
    metric_row(ax, 1.35, 4.15, "大量", "人工逐项排查", BLUE_DARK)
    header(ax, 1.35, 2.25, 3.9, "提效", BLUE)
    text(ax, 3.3, 1.84, "减少外协无效排查", size=13, color=BLUE_DARK, weight="bold", ha="center")

    ax.add_patch(Circle((8.0, 4.75), 1.45, fc=CARD, ec=BLUE, lw=2.0))
    ax.add_patch(Circle((8.0, 4.75), 1.72, fc="none", ec="#A8C4F3", lw=1.2, ls="--"))
    text(ax, 8.0, 5.08, "输电运检", size=17, weight="bold", ha="center")
    text(ax, 8.0, 4.55, "外协队伍管理", size=22, color=BLUE_DARK, weight="bold", ha="center")

    box(ax, 10.1, 1.45, 5.2, 6.0, fc=CARD, ec=ORANGE, lw=1.5, radius=0.18)
    header(ax, 10.6, 7.0, 4.2, "质量难保证", ORANGE)
    metric_row(ax, 10.75, 6.25, f"{CASE['metrics']['alarm_photos']/10000:.1f}万张", "告警工单照片", ORANGE)
    metric_row(ax, 10.75, 5.55, f"{CASE['metrics']['patrol_photos_monthly']/10000:.0f}万张/月", "巡视照片", ORANGE)
    metric_row(ax, 10.75, 4.85, "有限", "人工抽查", ORANGE)
    metric_row(ax, 10.75, 4.15, "困难", "重复照片发现", ORANGE)
    header(ax, 10.75, 2.25, 3.9, "增质", ORANGE)
    text(ax, 12.7, 1.84, "强化外协履职监督", size=13, color=RED, weight="bold", ha="center")

    arrow(ax, (5.55, 2.0), (7.1, 1.05), color=BLUE)
    arrow(ax, (10.45, 2.0), (8.9, 1.05), color=ORANGE)
    box(ax, 5.25, 0.55, 5.5, 0.8, fc=GREEN, ec=GREEN, lw=0, radius=0.16)
    text(ax, 8.0, 0.95, "数智协同外协管理", size=20, color="white", weight="bold", ha="center")
    save(fig, "01-外协管理两大痛点.png")


def fig03():
    fig, ax = canvas("“提效管任务、增质管履职”总体模型")
    box(ax, 3.2, 7.05, 9.6, 0.75, fc=BLUE_DARK, ec=BLUE_DARK, lw=0, radius=0.14)
    text(ax, 8.0, 7.43, "输电运检外协队伍管理", size=23, color="white", weight="bold", ha="center")
    left = ["工作量大", "提效", "数字化筛选", "候选任务清单", "外协精准核验"]
    right = ["质量难保证", "增质", "照片全量查重", "异常候选", "管理人员重点复核"]
    ys = [6.1, 5.05, 4.0, 2.95, 1.9]
    for i, (l, r, y) in enumerate(zip(left, right, ys)):
        flow_box(ax, 1.25, y, 5.1, l, color=BLUE, light=BLUE_LIGHT, size=17 if i < 2 else 15)
        flow_box(ax, 9.65, y, 5.1, r, color=ORANGE, light=ORANGE_LIGHT, size=17 if i < 2 else 15)
        if i < len(ys) - 1:
            arrow(ax, (3.8, y), (3.8, ys[i+1] + 0.67), color=BLUE, lw=2.2)
            arrow(ax, (12.2, y), (12.2, ys[i+1] + 0.67), color=ORANGE, lw=2.2)
    box(ax, 4.2, 0.55, 7.6, 0.82, fc=GREEN_LIGHT, ec=GREEN, lw=1.5, radius=0.14)
    text(ax, 8.0, 0.96, "人海式管理  →  数智协同管理", size=21, color=GREEN, weight="bold", ha="center")
    arrow(ax, (3.8, 1.9), (6.2, 1.36), color=BLUE, lw=2.0)
    arrow(ax, (12.2, 1.9), (9.8, 1.36), color=ORANGE, lw=2.0)
    save(fig, "03-提效增质总体模型.png")


def fig04():
    fig, ax = canvas("提效：外协任务数字化筛选统一流程")
    box(ax, 0.6, 1.25, 5.7, 6.5, fc=CARD, ec="#C8CDD4", lw=1.4)
    header(ax, 0.6, 7.17, 5.7, "传统模式（人海排查）", GRAY)
    trad = ["全量台账 / 数据", "外协人员逐项查找", "大范围现场排查", "管理人员复核"]
    ty = [6.1, 4.9, 3.7, 2.5]
    for i, (label, y) in enumerate(zip(trad, ty)):
        flow_box(ax, 2.0, y, 3.5, label, color=GRAY, light=GRAY_LIGHT, size=14)
        if i < 3:
            arrow(ax, (3.75, y), (3.75, ty[i+1] + 0.67), color=GRAY, lw=1.8)
    text(ax, 1.05, 4.55, "人找问题", size=15, color=TEXT, weight="bold", rotation=90, ha="center")
    text(ax, 6.85, 4.5, "VS", size=30, color=BLUE_DARK, weight="bold", ha="center")

    box(ax, 7.35, 1.25, 8.05, 6.5, fc=CARD, ec=BLUE, lw=1.5)
    header(ax, 7.35, 7.17, 8.05, "数字化模式（精准核验）", BLUE)
    digi = ["全量数据", "系统自动筛选", "候选任务清单", "外协精准核验", "结果回写闭环"]
    dy = [6.22, 5.15, 4.08, 3.01, 1.94]
    for i, (label, y) in enumerate(zip(digi, dy)):
        flow_box(ax, 9.1, y, 3.8, label, color=BLUE, light=BLUE_LIGHT, size=14)
        if i < 4:
            arrow(ax, (11.0, y), (11.0, dy[i+1] + 0.67), color=BLUE, lw=1.8)
    text(ax, 8.15, 4.6, "系统找重点\n人做判断", size=15, color=BLUE_DARK, weight="bold", ha="center")

    scenarios = [("交叉跨越", "自动筛查"), ("鸟类活动", "重点区域筛查"), ("集中燃放点", "周边杆塔筛查")]
    sy = [5.72, 4.38, 3.04]
    for (a, b), y in zip(scenarios, sy):
        box(ax, 13.25, y, 1.72, 0.94, fc=CARD, ec=BLUE, lw=1.2, radius=0.1)
        text(ax, 14.11, y + 0.60, a, size=11.8, weight="bold", ha="center")
        text(ax, 14.11, y + 0.28, b, size=10.5, color=MUTED, ha="center")

    box(ax, 0.9, 0.36, 14.2, 0.62, fc="#F7FAFF", ec="#D4E2FA", lw=1.0, radius=0.12)
    text(ax, 1.25, 0.67, "价值提升：", size=13.5, color=BLUE_DARK, weight="bold")
    text(ax, 3.0, 0.67, "✓ 排查范围更精准    ✓ 人员投入更高效    ✓ 风险识别更及时    ✓ 管理闭环更可靠", size=12.7, color=TEXT, weight="bold")
    save(fig, "04-外协任务数字化筛选流程.png")


def fig08():
    fig, ax = canvas("增质：外协照片质量督查原理与示例")
    labels = [
        ("外协完成任务", BLUE), ("海量作业照片", BLUE), ("照片全量查重", BLUE),
        ("疑似异常", ORANGE), ("管理人员重点复核", GREEN),
    ]
    xs = [0.55, 3.7, 6.85, 10.0, 13.15]
    for i, ((label, c), x) in enumerate(zip(labels, xs)):
        box(ax, x, 4.75, 2.3, 2.6, fc=CARD, ec=c, lw=1.3)
        header(ax, x + 0.14, 6.98, 2.02, label, c)
        body = {
            "外协完成任务": ("拍照 / 上传", ""),
            "海量作业照片": ("人工无法逐张检查", "数量远超人工能力"),
            "照片全量查重": ("系统自动比对", "全量检测相似照片"),
            "疑似异常": ("疑似重复 / 异常", "自动生成清单"),
            "管理人员重点复核": ("聚焦疑似问题", "重点复核与处置"),
        }[label]
        text(ax, x + 1.15, 5.85, body[0], size=14, color=RED if label == "疑似异常" else (GREEN if label == "管理人员重点复核" else BLUE_DARK if label == "照片全量查重" else TEXT), weight="bold", ha="center")
        if body[1]: text(ax, x + 1.15, 5.38, body[1], size=11, color=MUTED, ha="center")
        if i < 4: arrow(ax, (x + 2.32, 6.0), (xs[i+1] - 0.05, 6.0), color=BLUE, lw=2.0)

    text(ax, 8.0, 4.35, "系统全量检查，人员重点复核", size=20, color=BLUE_DARK, weight="bold", ha="center")
    paths = [ROOT / "assets" / "images" / "pair-1-a.jpg", ROOT / "assets" / "images" / "pair-1-b.jpg"]
    slots = [(0.75, 0.62, 5.65, 3.35, "示例A"), (9.6, 0.62, 5.65, 3.35, "示例B")]
    for path, (x, y, w, h, tag) in zip(paths, slots):
        box(ax, x, y, w, h, fc="#EAF2FF", ec=BLUE_DARK, lw=1.2, radius=0.04)
        if path.exists():
            img = Image.open(path).convert("RGB")
            ax.imshow(img, extent=[x + 0.04, x + w - 0.04, y + 0.04, y + h - 0.04], aspect="auto", zorder=2)
        else:
            text(ax, x + w/2, y + h/2, "脱敏示例照片", size=17, color=BLUE_DARK, weight="bold", ha="center")
        box(ax, x, y + h - 0.38, 0.9, 0.38, fc=BLUE_DARK, ec=BLUE_DARK, lw=0, radius=0.02, z=4)
        text(ax, x + 0.45, y + h - 0.19, tag, size=11.5, color="white", weight="bold", ha="center", z=5)
    box(ax, 6.75, 1.55, 2.5, 0.78, fc=BLUE_DARK, ec=BLUE_DARK, lw=0, radius=0.24)
    text(ax, 8.0, 1.94, "高度相似", size=18, color="white", weight="bold", ha="center")
    text(ax, 8.0, 0.44, "技术支撑：pHash 快速召回 + CLIP 语义复核；管理结论仍由人员终审", size=11.5, color=MUTED, ha="center")
    save(fig, "08-照片质量督查流程与示例.png")


def fig09():
    fig, ax = canvas("增质成果：告警工单照片全量查重")
    box(ax, 5.6, 7.05, 4.8, 0.62, fc=GREEN_LIGHT, ec=GREEN, lw=1.2, radius=0.16)
    text(ax, 8.0, 7.36, f"候选命中率  {CASE['metrics']['alarm_candidate_hit_rate']}%", size=18, color=GREEN, weight="bold", ha="center")
    cards = [
        ("1", "全量检查", f"{CASE['metrics']['alarm_photos']/10000:.1f}万张", "告警工单照片", BLUE),
        ("2", "机器筛选", f"{CASE['metrics']['alarm_candidates']:,}对", "疑似重复候选", ORANGE),
        ("3", "人工终审", f"{CASE['metrics']['alarm_confirmed_pairs']}对", "确认重复", RED),
    ]
    xs = [0.55, 5.55, 10.55]
    for i, ((n, title, big, sub, color), x) in enumerate(zip(cards, xs)):
        box(ax, x, 4.25, 4.15, 2.35, fc=CARD, ec=color, lw=1.5, radius=0.14)
        header(ax, x, 6.0, 4.15, f"{n}  {title}", color)
        text(ax, x + 2.075, 5.20, big, size=30, color=color, weight="bold", ha="center")
        text(ax, x + 2.075, 4.62, sub, size=14, weight="bold", ha="center")
        if i < 2: arrow(ax, (x + 4.2, 5.35), (xs[i+1] - 0.08, 5.35), color="#B6C9EB" if i == 0 else "#F4B47E", lw=2.4)

    text(ax, 8.0, 3.72, "能力升级对比", size=18, color=BLUE_DARK, weight="bold", ha="center")
    box(ax, 0.85, 0.72, 14.3, 2.72, fc=CARD, ec="#C8D3E1", lw=1.2, radius=0.12)
    rows = [
        ("覆盖范围", "少量特高压", "全电压等级"),
        ("处理规模", "小规模", f"{CASE['metrics']['patrol_photos_monthly']/10000:.0f}万张/月"),
        ("管理作用", "局部发现", "全量质量监督"),
    ]
    text(ax, 6.9, 3.05, "过去", size=14, color=GRAY, weight="bold", ha="center")
    text(ax, 12.0, 3.05, "现在", size=14, color=BLUE_DARK, weight="bold", ha="center")
    for i, (label, before, after) in enumerate(rows):
        y = 2.55 - i * 0.72
        text(ax, 2.1, y, label, size=13.5, color=BLUE_DARK, weight="bold")
        text(ax, 6.9, y, before, size=13.5, color=TEXT, ha="center")
        arrow(ax, (8.6, y), (9.5, y), color="#9CB8E8", lw=1.6)
        text(ax, 12.0, y, after, size=13.5, color=BLUE_DARK, weight="bold", ha="center")
    save(fig, "09-告警工单照片全量查重成果.png")


def fig10():
    fig, ax = canvas("外协管理方式前后对比")
    header(ax, 2.2, 7.1, 5.5, "过去（人海式管理）", "#666A70")
    header(ax, 8.3, 7.1, 5.5, "现在（数智协同管理）", BLUE)
    labels = ["任务管理", "质量管理", "人的精力"]
    before = ["外协全量摸排", "管理人员有限抽查", "大量重复劳动"]
    after = ["系统筛选 + 外协精准核验", "照片全量查重 + 管理人员重点复核", "专业判断 + 管理闭环"]
    ys = [5.9, 4.45, 3.0]
    for label, b, a, y in zip(labels, before, after, ys):
        box(ax, 0.6, y, 1.35, 1.0, fc=CARD, ec=BORDER, lw=1.0, radius=0.08)
        text(ax, 1.275, y + 0.5, label, size=13.5, color=TEXT, weight="bold", ha="center")
        box(ax, 2.2, y, 5.5, 1.0, fc="#F3F3F3", ec=BORDER, lw=1.0, radius=0.08)
        box(ax, 8.3, y, 5.5, 1.0, fc="#F5FAFF", ec="#D3E2F8", lw=1.0, radius=0.08)
        text(ax, 4.95, y + 0.5, b, size=15, color=TEXT, weight="bold", ha="center")
        text(ax, 11.05, y + 0.5, a, size=14.5, color=BLUE_DARK, weight="bold", ha="center")
        arrow(ax, (7.82, y + 0.5), (8.18, y + 0.5), color="#A7ADB5", lw=1.8)
    box(ax, 0.7, 0.62, 14.6, 1.35, fc=GREEN, ec=GREEN, lw=0, radius=0.14)
    text(ax, 8.0, 1.46, "提效管任务，增质管履职", size=25, color="white", weight="bold", ha="center")
    text(ax, 8.0, 0.96, "实现外协队伍管理由人海式管理向数智协同管理转变", size=14.2, color="white", weight="bold", ha="center")
    save(fig, "10-外协管理前后对比.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig01(); fig03(); fig04(); fig08(); fig09(); fig10()


if __name__ == "__main__":
    main()
