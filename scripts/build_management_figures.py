#!/usr/bin/env python3
"""Generate the six management-oriented figures for the case report.

The management narrative is locked by docs/CASE-LOGIC-BASELINE.md:
external-workforce management -> workload / quality pain points -> efficiency /
quality improvement -> digitally enabled collaborative management.

Technical methods are intentionally rendered as secondary supporting notes.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from management_figure_style import (
    AMBER,
    AMBER_DARK,
    AMBER_TINT,
    BLUE,
    BLUE_DARK,
    BLUE_TINT,
    FAINT,
    GRAY,
    GRAY_TINT,
    INK,
    MUTED,
    RED,
    RED_TINT,
    RULE,
    RULE_LIGHT,
    TEAL,
    TEAL_DARK,
    TEAL_TINT,
    WHITE,
    arrow,
    bracket_label,
    chip,
    dot,
    lane_tag,
    line,
    make_canvas,
    metric,
    node,
    rect,
    save_figure,
    section_label,
    txt,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "figures"
CASE = json.loads((ROOT / "content" / "case.json").read_text(encoding="utf-8"))
METRICS = CASE["metrics"]


def fig01() -> None:
    fig, ax, _ = make_canvas(
        "外协队伍管理：两类痛点与两条改进路径",
        "管理主线：工作量大 → 提效；质量难保证 → 增质",
    )

    node(
        ax, 5.2, 6.72, 5.6, 0.72, "输电运检外协队伍管理",
        edge=BLUE_DARK, fill=WHITE, color=BLUE_DARK, size=17,
    )
    line(ax, (8.0, 6.72), (8.0, 6.36), color=RULE, lw=1.0)
    line(ax, (3.9, 6.36), (12.1, 6.36), color=RULE, lw=1.0)
    arrow(ax, (3.9, 6.36), (3.9, 6.02), color=BLUE, lw=1.25)
    arrow(ax, (12.1, 6.36), (12.1, 6.02), color=AMBER, lw=1.25)

    node(ax, 1.55, 5.22, 4.7, 0.78, "工作量大", edge=BLUE, fill=BLUE_TINT, color=BLUE_DARK, size=17)
    node(ax, 9.75, 5.22, 4.7, 0.78, "质量难保证", edge=AMBER, fill=AMBER_TINT, color=AMBER_DARK, size=17)

    section_label(ax, 1.55, 4.72, "管理压力")
    metric(ax, 1.55, 4.28, f"{METRICS['province_poles']/10000:.1f}万基", "杆塔", color=BLUE_DARK)
    metric(ax, 3.55, 4.28, f"{METRICS['province_lines']}条", "输电线路", color=BLUE_DARK)
    metric(ax, 5.35, 4.28, "多类", "专项任务", color=BLUE_DARK, align="right")
    txt(ax, 1.55, 3.62, "传统方式依靠外协全量摸排、逐项核验，重复劳动多。", size=11.2, color=MUTED)

    section_label(ax, 9.75, 4.72, "监督压力")
    metric(ax, 9.75, 4.28, f"{METRICS['alarm_photos']/10000:.1f}万张", "告警工单照片", color=AMBER_DARK)
    metric(ax, 12.10, 4.28, f"{METRICS['patrol_photos_monthly']/10000:.0f}万张/月", "巡视照片", color=AMBER_DARK)
    txt(ax, 9.75, 3.62, "人工抽查覆盖有限，重复照片与履职异常难以全量发现。", size=11.2, color=MUTED)

    lane_tag(ax, 2.03, 2.82, "提效", color=BLUE, tint=BLUE_TINT, width=1.38)
    node(ax, 3.62, 2.68, 3.15, 0.74, "数字化筛选任务", edge=BLUE, fill=WHITE, color=BLUE_DARK, size=14.3)
    txt(ax, 5.20, 2.22, "减少外协全量人工排查", size=11.4, color=BLUE_DARK, weight="semibold", ha="center")
    arrow(ax, (3.41, 3.05), (3.60, 3.05), color=BLUE, lw=1.1)

    lane_tag(ax, 10.22, 2.82, "增质", color=AMBER, tint=AMBER_TINT, width=1.38)
    node(ax, 11.81, 2.68, 3.15, 0.74, "照片全量查重", edge=AMBER, fill=WHITE, color=AMBER_DARK, size=14.3)
    txt(ax, 13.39, 2.22, "强化外协履职质量监督", size=11.4, color=AMBER_DARK, weight="semibold", ha="center")
    arrow(ax, (11.60, 3.05), (11.79, 3.05), color=AMBER, lw=1.1)

    line(ax, (5.20, 2.12), (5.20, 1.55), color=BLUE, lw=1.0)
    line(ax, (13.39, 2.12), (13.39, 1.55), color=AMBER, lw=1.0)
    line(ax, (5.20, 1.55), (13.39, 1.55), color=RULE, lw=1.0)
    arrow(ax, (8.0, 1.55), (8.0, 1.22), color=TEAL, lw=1.25)
    node(ax, 5.30, 0.52, 5.40, 0.70, "数智协同外协管理", edge=TEAL, fill=TEAL_TINT, color=TEAL_DARK, size=17)

    save_figure(fig, OUT, "01-外协管理两大痛点.png")


def fig03() -> None:
    fig, ax, _ = make_canvas(
        "提效管任务，增质管履职",
        "统一机制：机器负责全量筛选和重复劳动，人员负责专业判断、现场核验和管理责任",
    )

    txt(ax, 0.86, 6.96, "输电运检外协队伍管理", size=14.2, color=INK, weight="semibold")
    line(ax, (3.28, 6.96), (15.10, 6.96), color=RULE, lw=0.9)

    columns = [
        (2.35, "管理痛点"),
        (5.15, "管理目标"),
        (7.98, "全量筛选"),
        (10.82, "人员判断"),
        (13.66, "管理闭环"),
    ]
    for x, label in columns:
        txt(ax, x, 6.45, label, size=10.4, color=MUTED, weight="semibold", ha="center")

    lane_tag(ax, 0.84, 5.02, "提效", color=BLUE, tint=BLUE_TINT, width=1.20)
    eff_nodes = [
        (1.25, 4.62, 2.20, "工作量大"),
        (4.05, 4.62, 2.20, "减少无效排查"),
        (6.85, 4.62, 2.25, "数字化筛选"),
        (9.65, 4.62, 2.35, "外协精准核验"),
        (12.55, 4.62, 2.45, "任务结果闭环"),
    ]
    for i, (x, y, w, label) in enumerate(eff_nodes):
        node(ax, x, y, w, 0.82, label, edge=BLUE if i in (0, 2) else RULE, fill=BLUE_TINT if i == 0 else WHITE, color=BLUE_DARK if i in (0, 1, 2) else INK, size=13.2)
        if i < len(eff_nodes) - 1:
            nx = eff_nodes[i + 1][0]
            arrow(ax, (x + w, y + 0.41), (nx - 0.10, y + 0.41), color=BLUE, lw=1.15)
    txt(ax, 8.0, 4.12, "全部任务 → 机器筛选 → 人工核验", size=10.4, color=BLUE_DARK, ha="center")

    lane_tag(ax, 0.84, 2.86, "增质", color=AMBER, tint=AMBER_TINT, width=1.20)
    qua_nodes = [
        (1.25, 2.46, 2.20, "质量难保证"),
        (4.05, 2.46, 2.20, "强化履职监督"),
        (6.85, 2.46, 2.25, "照片全量查重"),
        (9.65, 2.46, 2.35, "异常重点复核"),
        (12.55, 2.46, 2.45, "质量问题闭环"),
    ]
    for i, (x, y, w, label) in enumerate(qua_nodes):
        node(ax, x, y, w, 0.82, label, edge=AMBER if i in (0, 2) else RULE, fill=AMBER_TINT if i == 0 else WHITE, color=AMBER_DARK if i in (0, 1, 2) else INK, size=13.2)
        if i < len(qua_nodes) - 1:
            nx = qua_nodes[i + 1][0]
            arrow(ax, (x + w, y + 0.41), (nx - 0.10, y + 0.41), color=AMBER, lw=1.15)
    txt(ax, 8.0, 1.96, "全部照片 → 机器筛选 → 人工核验", size=10.4, color=AMBER_DARK, ha="center")

    arrow(ax, (8.0, 1.65), (8.0, 1.28), color=TEAL, lw=1.2)
    node(ax, 5.22, 0.52, 5.56, 0.72, "人海式管理  →  数智协同管理", edge=TEAL, fill=TEAL_TINT, color=TEAL_DARK, size=16.5)

    save_figure(fig, OUT, "03-提效增质总体模型.png")


def _flow_lane(ax, y: float, nodes: list[tuple[float, float, str]], *, color: str, tint: str, active_indices: set[int]) -> None:
    for i, (x, w, label) in enumerate(nodes):
        node(
            ax, x, y, w, 0.74, label,
            edge=color if i in active_indices else RULE,
            fill=tint if i == min(active_indices) else WHITE,
            color=color if i in active_indices else INK,
            size=12.5,
        )
        if i < len(nodes) - 1:
            next_x = nodes[i + 1][0]
            arrow(ax, (x + w, y + 0.37), (next_x - 0.10, y + 0.37), color=color, lw=1.0)


def fig04() -> None:
    fig, ax, _ = make_canvas(
        "提效：数字化筛选减少外协全量人工排查",
        "从“外协到处找”转为“系统先筛选、外协按清单精准核验”",
    )

    section_label(ax, 0.85, 6.83, "传统模式")
    txt(ax, 2.10, 6.83, "人海排查", size=12.4, color=GRAY, weight="semibold")
    trad = [
        (1.15, 2.40, "全量台账 / 数据"),
        (4.08, 2.55, "外协逐项查找"),
        (7.18, 2.65, "大范围现场排查"),
        (10.42, 2.60, "管理人员复核"),
    ]
    _flow_lane(ax, 5.85, trad, color=GRAY, tint=GRAY_TINT, active_indices={0, 1, 2, 3})
    txt(ax, 13.55, 6.22, "全量投入", size=11.0, color=GRAY, weight="semibold", ha="center")
    txt(ax, 13.55, 5.86, "范围大 · 重复劳动多", size=10.0, color=MUTED, ha="center")

    line(ax, (0.85, 4.90), (15.15, 4.90), color=RULE_LIGHT, lw=0.9)
    txt(ax, 8.0, 4.63, "管理方式改变", size=10.2, color=MUTED, ha="center")
    arrow(ax, (8.0, 4.43), (8.0, 4.07), color=BLUE, lw=1.15)

    section_label(ax, 0.85, 3.82, "数字化模式", color=BLUE_DARK)
    txt(ax, 2.10, 3.82, "精准核验", size=12.4, color=BLUE_DARK, weight="semibold")
    digi = [
        (0.98, 2.08, "全量数据"),
        (3.55, 2.20, "系统自动筛选"),
        (6.34, 2.12, "候选清单"),
        (9.06, 2.48, "外协精准核验"),
        (12.10, 2.28, "结果回写闭环"),
    ]
    _flow_lane(ax, 2.95, digi, color=BLUE, tint=BLUE_TINT, active_indices={0, 1, 2})
    txt(ax, 8.0, 2.43, "核心价值：把“全量人工排查”压缩为“重点候选核验”", size=11.3, color=BLUE_DARK, weight="semibold", ha="center")

    bracket_label(ax, 1.12, 0.63, 1.62, "技术支撑场景")
    chips = [
        (1.45, "交叉跨越自动筛查"),
        (5.30, "鸟类活动重点区域筛查"),
        (9.80, "集中燃放点周边筛查"),
    ]
    for x, label in chips:
        chip(ax, x, 0.92, label, edge=RULE, fill=WHITE, color=MUTED, size=10.3, width=3.45 if x < 9 else 3.55)
    txt(ax, 14.58, 1.11, "技术只负责找重点", size=10.2, color=FAINT, ha="right")

    save_figure(fig, OUT, "04-外协任务数字化筛选流程.png")


def _photo(ax, path: Path, x: float, y: float, w: float, h: float, tag: str) -> None:
    rect(ax, x, y, w, h, fc=WHITE, ec=RULE, lw=0.8, radius=0.03)
    if path.exists():
        img = Image.open(path).convert("RGB")
        ax.imshow(img, extent=[x + 0.03, x + w - 0.03, y + 0.03, y + h - 0.03], aspect="auto", zorder=2)
    else:
        txt(ax, x + w / 2, y + h / 2, "脱敏示例照片", size=13.0, color=MUTED, ha="center")
    rect(ax, x + 0.12, y + h - 0.43, 0.78, 0.30, fc=WHITE, ec=RULE, lw=0.65, radius=0.12, z=4)
    txt(ax, x + 0.51, y + h - 0.28, tag, size=9.2, color=INK, weight="semibold", ha="center", z=5)


def fig08() -> None:
    fig, ax, _ = make_canvas(
        "增质：照片全量查重强化外协履职质量监督",
        "从有限人工抽查升级为“全量筛选 + 异常重点复核”",
    )

    flow = [
        (0.78, 2.05, "外协完成任务"),
        (3.25, 2.05, "全量作业照片"),
        (5.72, 2.05, "照片全量查重"),
        (8.19, 1.90, "异常候选"),
        (10.50, 2.28, "管理人员重点复核"),
        (13.20, 2.05, "质量问题闭环"),
    ]
    for i, (x, w, label) in enumerate(flow):
        is_screen = i == 2
        is_review = i == 4
        is_alert = i == 3
        edge = BLUE if is_screen else AMBER if is_alert else TEAL if is_review else RULE
        fill = BLUE_TINT if is_screen else AMBER_TINT if is_alert else TEAL_TINT if is_review else WHITE
        color = BLUE_DARK if is_screen else AMBER_DARK if is_alert else TEAL_DARK if is_review else INK
        node(ax, x, 6.05, w, 0.78, label, edge=edge, fill=fill, color=color, size=12.4)
        if i < len(flow) - 1:
            nx = flow[i + 1][0]
            arrow(ax, (x + w, 6.44), (nx - 0.09, 6.44), color=BLUE if i < 2 else AMBER if i == 2 else TEAL, lw=1.0)

    txt(ax, 8.0, 5.52, "系统全量检查，人员只聚焦疑似问题；最终管理结论仍由人员终审。", size=11.2, color=INK, weight="semibold", ha="center")

    section_label(ax, 0.84, 4.88, "监督方式变化")
    node(ax, 0.84, 3.72, 3.20, 0.72, "有限人工抽查", edge=GRAY, fill=GRAY_TINT, color=GRAY, size=13.0)
    arrow(ax, (4.18, 4.08), (4.98, 4.08), color=BLUE, lw=1.1)
    node(ax, 5.10, 3.72, 3.55, 0.72, "照片全量查重", edge=BLUE, fill=BLUE_TINT, color=BLUE_DARK, size=13.0)
    txt(ax, 0.86, 3.18, "覆盖有限", size=10.3, color=MUTED)
    txt(ax, 5.12, 3.18, "覆盖全部照片，自动生成异常候选", size=10.3, color=BLUE_DARK)

    section_label(ax, 9.34, 4.88, "脱敏示例")
    p1 = ROOT / "assets" / "images" / "pair-1-a.jpg"
    p2 = ROOT / "assets" / "images" / "pair-1-b.jpg"
    _photo(ax, p1, 9.34, 2.45, 2.70, 2.05, "示例 A")
    _photo(ax, p2, 12.30, 2.45, 2.70, 2.05, "示例 B")
    arrow(ax, (12.03, 3.47), (12.26, 3.47), color=AMBER, lw=1.1)
    chip(ax, 11.44, 1.92, "疑似高度相似", edge=AMBER, fill=AMBER_TINT, color=AMBER_DARK, size=10.2, width=1.95)

    line(ax, (0.84, 1.52), (15.10, 1.52), color=RULE_LIGHT, lw=0.9)
    txt(ax, 0.84, 1.16, "技术支撑", size=9.8, color=FAINT, weight="semibold")
    txt(ax, 2.05, 1.16, "pHash 快速召回 + CLIP 语义复核", size=10.1, color=MUTED)
    txt(ax, 15.10, 1.16, "技术只负责生成候选，不替代管理判断", size=10.1, color=FAINT, ha="right")

    save_figure(fig, OUT, "08-照片质量督查流程与示例.png")


def fig09() -> None:
    fig, ax, _ = make_canvas(
        "增质成果：告警工单照片全量查重",
        "从0到1建立外协作业成果真实性全量核查能力，并向常态化规模监督扩展",
    )

    section_label(ax, 0.86, 6.86, "告警工单全量查重结果")
    cards = [
        (1.00, 3.55, f"{METRICS['alarm_photos']/10000:.1f}万张", "全量检查照片", BLUE_DARK, BLUE_TINT, BLUE),
        (6.20, 3.55, f"{METRICS['alarm_candidates']:,}对", "疑似重复候选", AMBER_DARK, AMBER_TINT, AMBER),
        (11.40, 3.55, f"{METRICS['alarm_confirmed_pairs']}对", "人工确认重复", RED, RED_TINT, RED),
    ]
    for i, (x, w, big, label, color, fill, edge) in enumerate(cards):
        rect(ax, x, 5.18, w, 1.30, fc=fill, ec=edge, lw=0.9, radius=0.07)
        txt(ax, x + w / 2, 5.93, big, size=23, color=color, weight="semibold", ha="center")
        txt(ax, x + w / 2, 5.47, label, size=10.8, color=INK, weight="semibold", ha="center")
        if i < 2:
            nx = cards[i + 1][0]
            arrow(ax, (x + w + 0.20, 5.83), (nx - 0.20, 5.83), color=FAINT, lw=1.0)
    chip(ax, 12.05, 4.58, f"候选复核确认率 {METRICS['alarm_candidate_hit_rate']}%", edge=RULE, fill=WHITE, color=MUTED, size=10.2, width=2.80)

    section_label(ax, 0.86, 4.05, "监督能力扩展")
    txt(ax, 5.92, 3.76, "过去", size=10.5, color=GRAY, weight="semibold", ha="center")
    txt(ax, 11.85, 3.76, "现在", size=10.5, color=BLUE_DARK, weight="semibold", ha="center")
    rows = [
        ("覆盖范围", "少量特高压", "全电压等级"),
        ("处理规模", "小规模筛查", f"{METRICS['patrol_photos_monthly']/10000:.0f}万张/月"),
        ("管理作用", "局部发现", "全量质量监督"),
    ]
    y0 = 3.18
    for i, (label, before, after) in enumerate(rows):
        y = y0 - i * 0.72
        line(ax, (0.86, y - 0.35), (15.05, y - 0.35), color=RULE_LIGHT, lw=0.75)
        txt(ax, 1.06, y, label, size=11.2, color=MUTED, weight="semibold")
        txt(ax, 5.92, y, before, size=12.0, color=GRAY, ha="center")
        arrow(ax, (7.60, y), (9.20, y), color=BLUE, lw=1.0)
        txt(ax, 11.85, y, after, size=12.2, color=BLUE_DARK, weight="semibold", ha="center")

    node(ax, 4.95, 0.52, 6.10, 0.72, "有限人工抽查  →  全量履职质量监督", edge=TEAL, fill=TEAL_TINT, color=TEAL_DARK, size=15.0)

    save_figure(fig, OUT, "09-告警工单照片全量查重成果.png")


def fig10() -> None:
    fig, ax, _ = make_canvas(
        "外协管理方式前后对比",
        "最终变化不是“多了几个算法”，而是外协管理方式由人海式转向数智协同",
    )

    txt(ax, 4.65, 6.86, "过去｜人海式管理", size=13.6, color=GRAY, weight="semibold", ha="center")
    txt(ax, 11.50, 6.86, "现在｜数智协同管理", size=13.6, color=BLUE_DARK, weight="semibold", ha="center")
    line(ax, (7.95, 1.82), (7.95, 6.58), color=RULE, lw=0.9)

    rows = [
        ("任务管理", "外协全量摸排", "系统筛选 + 外协精准核验", BLUE),
        ("质量管理", "管理人员有限抽查", "照片全量查重 + 异常重点复核", AMBER),
        ("人的精力", "大量重复劳动", "专业判断 + 现场核验 + 管理闭环", TEAL),
    ]
    y_positions = [5.62, 4.22, 2.82]
    for (label, before, after, color), y in zip(rows, y_positions):
        txt(ax, 0.94, y, label, size=11.2, color=MUTED, weight="semibold")
        dot(ax, 2.48, y, color=GRAY, r=0.045)
        txt(ax, 2.72, y, before, size=13.0, color=INK, weight="medium")
        arrow(ax, (7.25, y), (8.65, y), color=color, lw=1.1)
        dot(ax, 9.02, y, color=color, r=0.052)
        txt(ax, 9.30, y, after, size=13.0, color=BLUE_DARK if color == BLUE else AMBER_DARK if color == AMBER else TEAL_DARK, weight="semibold")
        line(ax, (0.94, y - 0.64), (15.05, y - 0.64), color=RULE_LIGHT, lw=0.8)

    lane_tag(ax, 2.68, 1.22, "提效管任务", color=BLUE, tint=BLUE_TINT, width=2.05)
    lane_tag(ax, 5.12, 1.22, "增质管履职", color=AMBER, tint=AMBER_TINT, width=2.05)
    arrow(ax, (7.40, 1.45), (8.42, 1.45), color=TEAL, lw=1.2)
    node(ax, 8.62, 1.07, 4.70, 0.76, "数智协同外协管理", edge=TEAL, fill=TEAL_TINT, color=TEAL_DARK, size=15.4)
    txt(ax, 8.0, 0.55, "机器承担全量筛选与重复劳动，人员回归专业判断与管理责任", size=10.5, color=MUTED, ha="center")

    save_figure(fig, OUT, "10-外协管理前后对比.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig01()
    fig03()
    fig04()
    fig08()
    fig09()
    fig10()


if __name__ == "__main__":
    main()
