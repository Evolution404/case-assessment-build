#!/opt/homebrew/bin/python3
"""Build the three paper-ready spatial-analysis figures used by the case report.

The outputs intentionally contain no city labels, line names, tower numbers or
geographic axes.  Geometry written to the SVG is simplified and mapped into the
figure coordinate system; the source coordinates remain in the read-only inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

from build_base_map import load_linework as load_base_linework
from map_style import BG, CARD, DISTRICT, FAINT, LAND, MUTED, OUTER, STYLE, TEXT, WHITE, resolve_soffice


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build" / "report-spatial"
OUT = ROOT / "dist" / "figures"
DB = Path(os.environ.get("POLE_DB", "/Users/zhangyuxi/Desktop/000基础数据/pole_data.db"))
PBF = Path(
    os.environ.get(
        "JIANGSU_RAIL_PBF",
        "/Users/zhangyuxi/Desktop/004领英班/两个带来/1-工作案例-铁路交叉跨越计算/rail/jiangsu-251106.osm.pbf",
    )
)
FIREWORKS = ROOT / "data" / "fireworks_jiangsu_verified.json"
BOUNDARY = ROOT / "data" / "jiangsu_outline.geojson"
DISTRICTS = ROOT / "data" / "jiangsu_districts.geojson"

GRAPHITE = "#434A52"
AMBER = "#D39124"
CORAL = "#E56658"
TEAL = "#1E9A8A"
EMERALD = "#35A77C"
BLUE = "#4D83C6"

CODE_CATEGORY = {
    "25": "35",
    "32": "110",
    "33": "220",
    "35": "500plus",
    "37": "500plus",
    "50": "500plus",
    "78": "500plus",
    "83": "500plus",
    "85": "500plus",
    "87": "other_dc",
}

plt.rcParams.update(
    {
        "font.family": ["PingFang SC", "Helvetica Neue", "Arial Unicode MS", "SimHei"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "savefig.transparent": False,
    }
)


def mercator(lon: float, lat: float) -> tuple[float, float]:
    radius = 6_378_137.0
    return radius * math.radians(lon), radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def normalize(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff±+\-]", "", str(value or "")).lower()


def last_number(value: object) -> str:
    numbers = re.findall(r"\d+", str(value or ""))
    return str(int(numbers[-1])) if numbers else ""


def branch_key(name: str | None, pole_num: str | None) -> tuple[str, int]:
    text = name or ""
    match = re.search(r"(\d+)\s*$", text)
    if match:
        return text[: match.start()], int(match.group(1))
    number = last_number(pole_num)
    return text, int(number) if number else 10**9


def classify(code: str | None, line_name: str | None) -> str | None:
    if (code or "") in CODE_CATEGORY:
        return CODE_CATEGORY[code or ""]
    match = re.search(r"([±+\-]?\d+)\s*kV", line_name or "", re.I)
    if not match:
        return None
    voltage = abs(int(match.group(1)))
    if voltage >= 500:
        return "500plus"
    if voltage >= 200:
        return "220"
    if voltage >= 100:
        return "110"
    if voltage >= 30:
        return "35"
    return None


def perpendicular_distance(point, start, end):
    if start == end:
        return math.dist(point, start)
    x, y = point
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def simplify(points, tolerance):
    if len(points) <= 2:
        return points
    farthest, index = 0.0, 0
    for i in range(1, len(points) - 1):
        distance = perpendicular_distance(points[i], points[0], points[-1])
        if distance > farthest:
            index, farthest = i, distance
    if farthest <= tolerance:
        return [points[0], points[-1]]
    return simplify(points[: index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)


def geometry_rings(path: Path):
    geo = json.loads(path.read_text(encoding="utf-8"))
    rings = []
    for feature in geo["features"]:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            if polygon and polygon[0]:
                rings.append(polygon[0])
    return rings


def load_network():
    if not DB.exists():
        raise FileNotFoundError(f"杆塔数据库不存在：{DB}")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    total_poles, total_lines = con.execute("SELECT COUNT(*), COUNT(DISTINCT line) FROM poles").fetchone()
    rows = con.execute(
        """
        SELECT line, name, pole_num, voltage_level, longitude, latitude
        FROM poles
        WHERE longitude BETWEEN 116.0 AND 122.2
          AND latitude BETWEEN 30.5 AND 35.4
          AND line IS NOT NULL AND line <> ''
          AND longitude IS NOT NULL AND latitude IS NOT NULL
        """
    ).fetchall()
    con.close()

    groups = defaultdict(list)
    categories = {}
    pole_lookup_exact = {}
    pole_lookup_number = {}
    all_poles = []
    for line, name, pole_num, code, lon, lat in rows:
        lon, lat = float(lon), float(lat)
        prefix, sequence = branch_key(name, pole_num)
        key = (line, prefix)
        groups[key].append((sequence, lon, lat))
        categories[key] = classify(str(code or ""), line)
        pole_lookup_exact[(normalize(line), normalize(name))] = (lon, lat)
        if last_number(name):
            pole_lookup_number[(normalize(line), last_number(name))] = (lon, lat)
        if last_number(pole_num):
            pole_lookup_number[(normalize(line), last_number(pole_num))] = (lon, lat)
        all_poles.append((lon, lat, line))

    display = defaultdict(list)
    raw_segments = []
    for key, items in groups.items():
        category = categories.get(key)
        if category not in STYLE:
            continue
        items.sort(key=lambda value: value[0])
        chunks = [[]]
        for _, lon, lat in items:
            point = (lon, lat)
            if chunks[-1] and math.dist(point, chunks[-1][-1]) > 0.34:
                chunks.append([])
            chunks[-1].append(point)
        tolerance = {"35": 0.0032, "110": 0.0026, "220": 0.0020, "other_dc": 0.0016, "500plus": 0.0014}[category]
        for chunk in chunks:
            if len(chunk) < 2:
                continue
            for start, end in zip(chunk, chunk[1:]):
                if math.dist(start, end) <= 0.34:
                    raw_segments.append((start, end, key[0], category))
            points = [(round(a, 3), round(b, 3)) for a, b in simplify(chunk, tolerance)]
            projected = [mercator(lon, lat) for lon, lat in points]
            if len(projected) >= 2:
                display[category].append(projected)
    return {
        "display": display,
        "segments": raw_segments,
        "pole_exact": pole_lookup_exact,
        "pole_number": pole_lookup_number,
        "poles": all_poles,
        "total_poles": int(total_poles),
        "total_lines": int(total_lines),
    }


def map_context():
    province = [[mercator(lon, lat) for lon, lat in ring] for ring in geometry_rings(BOUNDARY)]
    districts = [[mercator(lon, lat) for lon, lat in ring] for ring in geometry_rings(DISTRICTS)]
    xs = [point[0] for ring in province for point in ring]
    ys = [point[1] for ring in province for point in ring]
    return province, districts, (min(xs), max(xs), min(ys), max(ys))


def base_figure():
    fig = plt.figure(figsize=(12, 6.75), facecolor=BG)
    ax = fig.add_axes([0.025, 0.025, 0.95, 0.95], facecolor=BG)
    return fig, ax


def draw_geography(ax, province, districts, bounds):
    for ring in province:
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=LAND, zorder=0)
    ax.add_collection(LineCollection(districts, colors=DISTRICT, linewidths=0.40, alpha=0.82, zorder=1))
    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.72, alpha=0.95, zorder=12))
    min_x, max_x, min_y, max_y = bounds
    ax.set_xlim(min_x - 0.055 * (max_x - min_x), max_x + 0.055 * (max_x - min_x))
    ax.set_ylim(min_y - 0.035 * (max_y - min_y), max_y + 0.035 * (max_y - min_y))
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")


def draw_network(ax, display, mode="color", alpha_factor=1.0, z_offset=0):
    for category in ["35", "110", "220", "other_dc", "500plus"]:
        style = STYLE[category]
        color = style["color"] if mode == "color" else "#AEB6BF"
        alpha = style["alpha"] * alpha_factor if mode == "color" else 0.23 * alpha_factor
        ax.add_collection(
            LineCollection(
                display.get(category, []),
                colors=color,
                linewidths=style["width"],
                alpha=alpha,
                zorder=style["z"] + z_offset,
                capstyle="round",
                joinstyle="round",
            )
        )


def draw_local_network(ax, display, predicate, width_factor=3.2, alpha_factor=1.0, z_offset=2):
    """Draw a local inset with the same voltage palette as the province map."""
    for category in ["35", "110", "220", "other_dc", "500plus"]:
        style = STYLE[category]
        local = [segment for segment in display.get(category, []) if predicate(segment)]
        if not local:
            continue
        ax.add_collection(
            LineCollection(
                local,
                colors=style["color"],
                linewidths=max(style["width"] * width_factor, 0.48),
                alpha=min(style["alpha"] * alpha_factor, 0.96),
                zorder=style["z"] + z_offset,
                capstyle="round",
                joinstyle="round",
            )
        )


def add_cards(fig, cards, accent):
    fig.text(0.682, 0.920, "空间筛查摘要", fontsize=8.4, color=MUTED, weight="medium")
    y_values = [0.835, 0.735, 0.635, 0.535]
    for index, ((label, value), y) in enumerate(zip(cards, y_values)):
        patch = FancyBboxPatch(
            (0.675, y),
            0.285,
            0.074,
            transform=fig.transFigure,
            boxstyle="round,pad=0.008,rounding_size=0.014",
            linewidth=0.55,
            edgecolor="#E2E5E9",
            facecolor=CARD,
            zorder=20,
        )
        fig.add_artist(patch)
        dot = Circle((0.701, y + 0.037), 0.014, transform=fig.transFigure, facecolor=accent, edgecolor="none", alpha=0.13, zorder=21)
        fig.add_artist(dot)
        fig.text(0.701, y + 0.0365, str(index + 1), ha="center", va="center", fontsize=6.8, color=accent, weight="semibold", zorder=22)
        fig.text(0.727, y + 0.047, label, fontsize=7.8, color=MUTED, va="center", zorder=22)
        fig.text(0.943, y + 0.036, value, fontsize=13.2, color=TEXT, weight="semibold", ha="right", va="center", zorder=22)


def add_inset_frame(fig, accent):
    shadow = FancyBboxPatch(
        (0.682, 0.085),
        0.278,
        0.350,
        transform=fig.transFigure,
        boxstyle="round,pad=0.010,rounding_size=0.020",
        linewidth=0,
        facecolor=WHITE,
        zorder=15,
        path_effects=[pe.withSimplePatchShadow(offset=(2.2, -2.2), shadow_rgbFace="#77818B", alpha=0.16, rho=0.96)],
    )
    fig.add_artist(shadow)
    fig.add_artist(
        FancyBboxPatch(
            (0.682, 0.085),
            0.278,
            0.350,
            transform=fig.transFigure,
            boxstyle="round,pad=0.010,rounding_size=0.020",
            linewidth=0.75,
            edgecolor="#D9DEE4",
            facecolor=WHITE,
            zorder=16,
        )
    )
    fig.text(0.705, 0.405, "局部关系放大", fontsize=8.0, color=TEXT, weight="semibold", zorder=18)
    fig.add_artist(Line2D([0.705, 0.735], [0.386, 0.386], transform=fig.transFigure, color=accent, lw=1.7, solid_capstyle="round", zorder=18))
    inset = fig.add_axes([0.700, 0.115, 0.242, 0.245], facecolor="#FBFBFC", zorder=17)
    inset.axis("off")
    return inset


def add_leader(fig, ax, point, accent):
    display = ax.transData.transform(point)
    start = fig.transFigure.inverted().transform(display)
    fig.add_artist(Line2D([start[0], 0.676], [start[1], 0.257], transform=fig.transFigure, color="#9BA4AD", lw=0.65, alpha=0.9, zorder=14))
    fig.add_artist(Circle((start[0], start[1]), 0.006, transform=fig.transFigure, facecolor=WHITE, edgecolor=accent, linewidth=1.1, zorder=15))


def add_footer(fig, text):
    fig.text(0.045, 0.024, text, fontsize=6.8, color=MUTED, va="bottom")


def legend_lines(ax, include_rail=False):
    handles = [
        Line2D([0], [0], color=STYLE[key]["color"], lw=1.25, alpha=0.85, label=STYLE[key]["label"])
        for key in ["500plus", "220", "110", "35"]
    ]
    if include_rail:
        handles.append(Line2D([0], [0], color=GRAPHITE, lw=1.35, label="铁路"))
        handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=AMBER, markeredgecolor=CORAL, markersize=5, label="交跨候选"))
    leg = ax.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.99),
        ncol=3,
        frameon=True,
        facecolor=WHITE,
        edgecolor="#D9DEE4",
        framealpha=0.96,
        fancybox=True,
        fontsize=6.5,
        columnspacing=1.1,
        handlelength=1.8,
        borderpad=0.6,
    )
    for item in leg.get_texts():
        item.set_color(MUTED)


def save_figure(fig, stem, *, tight=False):
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{stem}.svg"
    png = OUT / f"{stem}.png"
    facecolor = fig.get_facecolor()
    save_kwargs = {"bbox_inches": "tight", "pad_inches": 0.08} if tight else {}
    fig.savefig(svg, format="svg", facecolor=facecolor, **save_kwargs)
    fig.savefig(png, format="png", dpi=320, facecolor=facecolor, **save_kwargs)
    plt.close(fig)
    with tempfile.TemporaryDirectory(prefix="report-spatial-lo-") as profile:
        subprocess.run(
            [
                resolve_soffice(),
                f"-env:UserInstallation={Path(profile).resolve().as_uri()}",
                "--headless",
                "--convert-to",
                "emf",
                "--outdir",
                str(OUT),
                str(svg),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return svg, png


def extract_railways():
    BUILD.mkdir(parents=True, exist_ok=True)
    raw = BUILD / "railways.osm.pbf"
    geojson = BUILD / "railways.geojson"
    if not PBF.exists():
        raise FileNotFoundError(f"铁路数据不存在：{PBF}")
    if not geojson.exists() or geojson.stat().st_mtime < PBF.stat().st_mtime:
        subprocess.run(["osmium", "tags-filter", str(PBF), "w/railway", "-o", str(raw), "--overwrite"], check=True)
        subprocess.run(["osmium", "export", str(raw), "-o", str(geojson), "--overwrite"], check=True)
    data = json.loads(geojson.read_text(encoding="utf-8"))
    # Report crossing analysis concerns inter-city / main-line railways.  Depot,
    # siding, subway and tram geometry creates visual noise and duplicate hits.
    accepted = {"rail"}
    lines = []
    feature_count = 0
    for feature in data["features"]:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        if properties.get("railway") not in accepted or properties.get("service"):
            continue
        coords = geometry.get("coordinates") or []
        if geometry.get("type") == "LineString":
            parts = [coords]
        elif geometry.get("type") == "MultiLineString":
            parts = coords
        else:
            continue
        for part in parts:
            cleaned = [(float(p[0]), float(p[1])) for p in part if len(p) >= 2 and 116.0 <= p[0] <= 122.2 and 30.5 <= p[1] <= 35.4]
            if len(cleaned) >= 2:
                lines.append(cleaned)
                feature_count += 1
    return lines, feature_count


def segment_intersection(a, b, c, d):
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c
    x4, y4 = d
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if -1e-10 <= t <= 1 + 1e-10 and -1e-10 <= u <= 1 + 1e-10:
        return x1 + t * (x2 - x1), y1 + t * (y2 - y1)
    return None


def railway_analysis(network, railway_lines):
    cell = 0.025
    rail_segments = []
    grid = defaultdict(list)
    for line_index, line in enumerate(railway_lines):
        for start, end in zip(line, line[1:]):
            if math.dist(start, end) > 0.75:
                continue
            index = len(rail_segments)
            rail_segments.append((start, end, line_index))
            lo_x, hi_x = sorted((start[0], end[0]))
            lo_y, hi_y = sorted((start[1], end[1]))
            for gx in range(math.floor(lo_x / cell), math.floor(hi_x / cell) + 1):
                for gy in range(math.floor(lo_y / cell), math.floor(hi_y / cell) + 1):
                    grid[(gx, gy)].append(index)

    dedup = {}
    affected = set()
    for start, end, line_name, category in network["segments"]:
        lo_x, hi_x = sorted((start[0], end[0]))
        lo_y, hi_y = sorted((start[1], end[1]))
        candidates = set()
        for gx in range(math.floor(lo_x / cell), math.floor(hi_x / cell) + 1):
            for gy in range(math.floor(lo_y / cell), math.floor(hi_y / cell) + 1):
                candidates.update(grid.get((gx, gy), ()))
        for idx in candidates:
            r_start, r_end, _ = rail_segments[idx]
            point = segment_intersection(start, end, r_start, r_end)
            if point is None:
                continue
            key = (hashlib.sha1(line_name.encode("utf-8")).hexdigest()[:10], round(point[0], 3), round(point[1], 3))
            dedup[key] = (point[0], point[1], category)
            affected.add(key[0])
    return list(dedup.values()), len(affected), len(rail_segments)


def draw_crossing(network, context, railway_lines, crossings, affected, rail_segment_count, elapsed):
    province, districts, _bounds = context

    # 图5与图6/图7共用同一张竖版省域底图：尺寸、留白、线路配色、
    # 地市界和图例容器保持一致，仅叠加铁路与交跨候选。
    linework, _used_poles, _total_poles, _total_lines = load_base_linework()
    xs = [point[0] for ring in province for point in ring]
    ys = [point[1] for ring in province for point in ring]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    fig, ax = plt.subplots(figsize=(7.2, 8.8), facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    for ring in province:
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=LAND, zorder=0)
    ax.add_collection(LineCollection(districts, colors=DISTRICT, linewidths=0.34, alpha=0.46, zorder=1))
    for category in ["35", "110", "220", "other_dc", "500plus"]:
        style = STYLE[category]
        ax.add_collection(
            LineCollection(
                linework.get(category, []),
                colors=style["color"],
                linewidths=style["width"],
                alpha=style["alpha"],
                zorder=style["z"],
                capstyle="round",
                joinstyle="round",
            )
        )

    rail_display = []
    for line in railway_lines:
        points = [(round(a, 3), round(b, 3)) for a, b in simplify(line, 0.0025)]
        if len(points) >= 2:
            rail_display.append([mercator(*p) for p in points])
    ax.add_collection(LineCollection(rail_display, colors="#F7F8F9", linewidths=0.92, alpha=0.98, zorder=7, capstyle="round"))
    ax.add_collection(LineCollection(rail_display, colors=GRAPHITE, linewidths=0.42, alpha=0.78, zorder=8, capstyle="round"))

    # 指标仍使用全部交跨结果；地图只做视觉去拥挤，不改变统计结果。
    representatives = {}
    for lon, lat, category in crossings:
        key = (round(lon / 0.028), round(lat / 0.028))
        previous = representatives.get(key)
        if previous is None or category == "500plus":
            representatives[key] = (lon, lat, category)
    display_crossings = list(representatives.values())
    if len(display_crossings) > 360:
        display_crossings = sorted(display_crossings, key=lambda p: (round(p[1], 2), round(p[0], 2)))
        display_crossings = display_crossings[:: math.ceil(len(display_crossings) / 360)]
    crossing_xy = np.array([mercator(lon, lat) for lon, lat, _ in display_crossings]) if display_crossings else np.empty((0, 2))
    if len(crossing_xy):
        ax.scatter(crossing_xy[:, 0], crossing_xy[:, 1], s=8.0, c=AMBER, edgecolors=WHITE, linewidths=0.35, alpha=0.96, zorder=9)
        ax.scatter(crossing_xy[:, 0], crossing_xy[:, 1], s=17.5, facecolors="none", edgecolors=CORAL, linewidths=0.45, alpha=0.72, zorder=10)

    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.66, alpha=0.92, zorder=11))
    pad_x = (max_x - min_x) * 0.08
    pad_y = (max_y - min_y) * 0.05
    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    handles = [
        Line2D([0], [0], color=STYLE[key]["color"], lw=max(STYLE[key]["width"] * 2.15, 1.0), alpha=STYLE[key]["alpha"], label=STYLE[key]["label"])
        for key in ["500plus", "220", "110", "35", "other_dc"]
    ]
    handles.append(Line2D([0], [0], color=DISTRICT, lw=0.9, alpha=0.72, label="地市界"))
    handles.extend(
        [
            Line2D([0], [0], color="none", lw=0, label="交叉跨越"),
            Line2D([0], [0], color=GRAPHITE, lw=1.35, label="铁路"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=AMBER, markeredgecolor=CORAL, markeredgewidth=0.5, markersize=5, label="交跨候选"),
        ]
    )
    legend = ax.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.99, 0.995),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D7DCE2",
        framealpha=0.96,
        fancybox=True,
        fontsize=8.1,
        handlelength=2.5,
        borderpad=0.7,
        labelspacing=0.55,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
        if text.get_text() == "交叉跨越":
            text.set_weight("semibold")

    return save_figure(fig, "铁路交叉跨越识别", tight=True)


def distance_to_polyline(lon, lat, points):
    """Approximate angular distance to a generalized province-scale corridor."""
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    scale_x = math.cos(math.radians(32.7))
    px = lon * scale_x
    py = lat
    distance = np.full(np.broadcast(lon, lat).shape, np.inf, dtype=float)
    for start, end in zip(points, points[1:]):
        x1, y1 = start[0] * scale_x, start[1]
        x2, y2 = end[0] * scale_x, end[1]
        dx, dy = x2 - x1, y2 - y1
        denominator = dx * dx + dy * dy
        t = np.clip(((px - x1) * dx + (py - y1) * dy) / denominator, 0, 1)
        distance = np.minimum(distance, np.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    return distance


def bird_activity(lon, lat):
    """Generalized province-scale bird activity framework, scaled 0..1.

    The broad belts follow public descriptions of the coastal migration route,
    major river/canal ecological corridors, lake-wetland networks and southern
    hilly habitat.  Coordinates are deliberately generalized and do not encode
    observation points, nests or operational risk locations.
    """
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    corridors = [
        # East-coast migration and wintering belt.
        ([(119.65, 34.92), (120.20, 34.45), (120.55, 33.90), (120.62, 33.20), (120.78, 32.55), (121.12, 31.85)], 0.30, 1.00),
        # Major east-west river corridor and estuary connection.
        ([(118.10, 32.08), (118.85, 32.15), (119.55, 32.08), (120.30, 31.98), (121.22, 31.72)], 0.23, 0.84),
        # North-south canal / lake stepping-stone corridor.
        ([(117.72, 34.35), (118.30, 33.75), (118.82, 33.15), (119.20, 32.50), (119.55, 31.80)], 0.22, 0.68),
        # Northern east-west ecological connection.
        ([(116.95, 34.55), (117.85, 34.42), (118.80, 34.40), (119.85, 34.55)], 0.20, 0.58),
    ]
    score = np.zeros(np.broadcast(lon, lat).shape, dtype=float)
    for points, width, weight in corridors:
        distance = distance_to_polyline(lon, lat, points)
        score = np.maximum(score, weight * np.exp(-0.5 * (distance / width) ** 2))
    broad_regions = [
        (118.65, 33.22, 0.64, 0.46, 0.76),
        (119.38, 32.82, 0.58, 0.42, 0.72),
        (120.05, 31.38, 0.72, 0.34, 0.86),
        (118.72, 31.55, 0.54, 0.38, 0.68),
    ]
    for cx, cy, sx, sy, weight in broad_regions:
        value = weight * np.exp(-0.5 * (((lon - cx) / sx) ** 2 + ((lat - cy) / sy) ** 2))
        score = np.maximum(score, value)
    # Low-frequency modulation avoids synthetic geometric edges without adding
    # false point precision or small isolated islands.
    modulation = 1 + 0.055 * np.sin(lon * 8.3 + lat * 2.7) * np.sin(lat * 7.1 - lon * 1.9)
    score *= modulation
    return np.clip(score, 0, 1)


def bird_public_analysis(network, surface):
    x_grid, y_grid, score = surface
    x_axis = x_grid[0, :]
    y_axis = y_grid[:, 0]
    score_values = np.ma.filled(score, 0)
    priority = []
    affected = set()
    for start, end, line_name, category in network["segments"]:
        middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        middle_xy = mercator(*middle)
        xi = int(np.clip(np.searchsorted(x_axis, middle_xy[0]), 1, len(x_axis) - 1))
        yi = int(np.clip(np.searchsorted(y_axis, middle_xy[1]), 1, len(y_axis) - 1))
        if float(score_values[yi, xi]) >= 0.56:
            priority.append([mercator(*start), mercator(*end)])
            affected.add(hashlib.sha1(line_name.encode("utf-8")).hexdigest()[:10])
    return priority, len(affected)


def smooth_masked_surface(score, passes=6):
    """Smooth a masked study raster without bleeding across the province edge."""
    valid = ~np.ma.getmaskarray(score)
    values = np.ma.filled(score, 0).astype(float)
    weights = valid.astype(float)
    for _ in range(passes):
        padded_values = np.pad(values * weights, 1, mode="edge")
        padded_weights = np.pad(weights, 1, mode="edge")
        total = sum(
            padded_values[dy : dy + values.shape[0], dx : dx + values.shape[1]]
            for dy in range(3)
            for dx in range(3)
        )
        count = sum(
            padded_weights[dy : dy + values.shape[0], dx : dx + values.shape[1]]
            for dy in range(3)
            for dx in range(3)
        )
        values = np.divide(total, count, out=np.zeros_like(total), where=count > 0)
        weights = valid.astype(float)
    return np.ma.masked_where(~valid, values)


def keep_large_components(mask, min_cells, max_components):
    """Keep meaningful study-raster regions and discard isolated JPEG speckle."""
    mask = np.asarray(mask, dtype=bool)
    visited = np.zeros(mask.shape, dtype=bool)
    components = []
    height, width = mask.shape
    for row in range(height):
        for col in range(width):
            if not mask[row, col] or visited[row, col]:
                continue
            stack = [(row, col)]
            visited[row, col] = True
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = current_row + dr, current_col + dc
                        if 0 <= nr < height and 0 <= nc < width and mask[nr, nc] and not visited[nr, nc]:
                            visited[nr, nc] = True
                            stack.append((nr, nc))
            if len(component) >= min_cells:
                components.append(component)
    components.sort(key=len, reverse=True)
    kept = np.zeros(mask.shape, dtype=bool)
    for component in components[:max_components]:
        rows, cols = zip(*component)
        kept[np.asarray(rows), np.asarray(cols)] = True
    return kept


def bird_relief_surface(x_grid, y_grid, public_score):
    """Prepare the public-study raster without inventing extra activity areas."""
    del x_grid, y_grid
    return smooth_masked_surface(public_score, passes=4)


def paper_map_figure():
    paper = BG
    fig = plt.figure(figsize=(12, 6.75), facecolor=paper)
    ax = fig.add_axes([0.18, 0.070, 0.64, 0.885], facecolor="none", zorder=1)
    return fig, ax, paper


def draw_paper_geography(ax, province, bounds, paper):
    """Draw a quiet paper-cut province base with a restrained cast shadow."""
    core_dx, core_dy = 2_500, -2_900
    shadow_dx, shadow_dy = 7_200, -7_800
    for ring in province:
        xs = np.asarray([point[0] for point in ring])
        ys = np.asarray([point[1] for point in ring])
        ax.fill(xs + shadow_dx, ys + shadow_dy, color="#7D8790", alpha=0.12, zorder=0, linewidth=0)
        ax.fill(xs + core_dx, ys + core_dy, color="#E7EAEC", alpha=0.98, zorder=0.5, linewidth=0)
        ax.fill(xs, ys, color=LAND, zorder=1, linewidth=0)
    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.68, alpha=0.94, zorder=13))
    min_x, max_x, min_y, max_y = bounds
    ax.set_xlim(min_x - 0.065 * (max_x - min_x), max_x + 0.065 * (max_x - min_x))
    ax.set_ylim(min_y - 0.045 * (max_y - min_y), max_y + 0.045 * (max_y - min_y))
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")


def draw_activity_regions(ax, x_grid, y_grid, outer_mask, core_mask):
    """Draw two clean, nested activity regions below the network."""
    valid = ~np.ma.getmaskarray(outer_mask)
    layers = [
        (np.ma.masked_where(~valid, np.ma.filled(outer_mask, False).astype(float)), "#DCE8F1", 0.72),
        (np.ma.masked_where(~valid, np.ma.filled(core_mask, False).astype(float)), "#AFC8DA", 0.82),
    ]
    for index, (mask, color, alpha) in enumerate(layers):
        ax.contourf(
            x_grid,
            y_grid,
            mask,
            levels=[0.5, 1.5],
            colors=[color],
            alpha=alpha,
            antialiased=True,
            zorder=2 + index,
        )


def activity_coverage_km2(x_grid, y_grid, score, threshold):
    """Approximate true ground area for a Web-Mercator activity mask."""
    x_axis = x_grid[0, :]
    y_axis = y_grid[:, 0]
    dx = float(np.median(np.diff(x_axis)))
    dy = float(np.median(np.diff(y_axis)))
    radius = 6_378_137.0
    lat = 2 * np.arctan(np.exp(y_axis / radius)) - np.pi / 2
    row_area = dx * dy * np.cos(lat) ** 2 / 1_000_000
    cell_area = np.broadcast_to(row_area[:, None], score.shape)
    return float(cell_area[np.ma.filled(score >= threshold, False)].sum())


def gaussian_smooth_masked(score, sigma_x=7.5, sigma_y=10.0):
    """Gaussian smoothing with mask-normalized separable convolution."""
    valid = ~np.ma.getmaskarray(score)
    values = np.ma.filled(score, 0).astype(float)

    def kernel(sigma):
        radius = int(math.ceil(3 * sigma))
        axis = np.arange(-radius, radius + 1, dtype=float)
        weights = np.exp(-0.5 * (axis / sigma) ** 2)
        return weights / weights.sum()

    def convolve_axis(array, weights, axis):
        return np.apply_along_axis(lambda row: np.convolve(row, weights, mode="same"), axis, array)

    weights = valid.astype(float)
    for axis, sigma in ((1, sigma_x), (0, sigma_y)):
        k = kernel(sigma)
        values = convolve_axis(values * weights, k, axis)
        weights = convolve_axis(weights, k, axis)
        values = np.divide(values, weights, out=np.zeros_like(values), where=weights > 1e-9)
        weights = valid.astype(float)
    return np.ma.masked_where(~valid, values)


def cell_area_grid_km2(x_grid, y_grid):
    x_axis = x_grid[0, :]
    y_axis = y_grid[:, 0]
    dx = float(np.median(np.diff(x_axis)))
    dy = float(np.median(np.diff(y_axis)))
    radius = 6_378_137.0
    lat = 2 * np.arctan(np.exp(y_axis / radius)) - np.pi / 2
    return np.broadcast_to((dx * dy * np.cos(lat) ** 2 / 1_000_000)[:, None], x_grid.shape)


def calibrated_region_mask(score, cell_area, target_km2, min_cells, max_components):
    """Find a clean region whose area stays close to the requested total."""
    valid = ~np.ma.getmaskarray(score)
    values = np.ma.filled(score, -1)
    candidates = np.linspace(float(values[valid].max()), float(values[valid].min()), 360)
    best = None
    for threshold in candidates:
        kept = keep_large_components((values >= threshold) & valid, min_cells, max_components)
        area = float(cell_area[kept].sum())
        error = abs(area - target_km2)
        if best is None or error < best[0]:
            best = (error, kept, area, threshold)
    _, kept, area, threshold = best
    return np.ma.masked_where(~valid, kept), area, threshold


def bird_surface(bounds, nx=190, ny=230):
    cached = ROOT / "data" / "public_bird_activity_grid.npz"
    if cached.exists():
        model = np.load(cached)
        x_axis = model["x_axis"]
        y_axis = model["y_axis"]
        x_grid, y_grid = np.meshgrid(x_axis, y_axis)
        score = np.ma.masked_where(model["score"] < 0, model["score"])
        return x_grid, y_grid, score
    raw_rings = geometry_rings(BOUNDARY)
    lon_min = min(p[0] for ring in raw_rings for p in ring)
    lon_max = max(p[0] for ring in raw_rings for p in ring)
    lat_min = min(p[1] for ring in raw_rings for p in ring)
    lat_max = max(p[1] for ring in raw_rings for p in ring)
    lons = np.linspace(lon_min, lon_max, nx)
    lats = np.linspace(lat_min, lat_max, ny)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    flat = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])
    inside = np.zeros(len(flat), dtype=bool)
    for ring in raw_rings:
        inside |= MplPath(np.asarray(ring)).contains_points(flat)
    reference = BUILD / "reference" / "avian-habitat-suitability.jpg"
    if reference.exists():
        # Digitize panel b (water-bird habitat suitability) from the published
        # province-level figure.  Only a low-resolution categorical surface is
        # sampled; labels, boundaries and the source image are never embedded.
        image = np.asarray(Image.open(reference).convert("RGB"))
        panel = (1110, 120, 2060, 935)  # pixel extent of the north-up province map
        px = panel[0] + (lon_grid - lon_min) / (lon_max - lon_min) * (panel[2] - panel[0])
        py = panel[1] + (lat_max - lat_grid) / (lat_max - lat_min) * (panel[3] - panel[1])
        px = np.clip(np.rint(px).astype(int), 0, image.shape[1] - 1)
        py = np.clip(np.rint(py).astype(int), 0, image.shape[0] - 1)
        sampled = image[py, px].astype(float)
        palette = np.asarray(
            [
                [238, 247, 244],  # very low
                [249, 208, 213],  # low
                [2, 64, 95],      # medium
                [224, 5, 20],     # high
                [92, 178, 103],   # very high
            ],
            dtype=float,
        )
        values = np.asarray([0.08, 0.30, 0.53, 0.76, 1.00])
        distances = np.linalg.norm(sampled[:, :, None, :] - palette[None, None, :, :], axis=3)
        nearest = distances.argmin(axis=2)
        score = values[nearest]
        score[distances.min(axis=2) > 84] = 0.04
        score[sampled.sum(axis=2) < 145] = 0.04
        # A small deterministic smoothing step removes JPEG speckle and turns
        # the categorical study raster into clean report-ready vector regions.
        for _ in range(2):
            padded = np.pad(score, 1, mode="edge")
            score = sum(padded[dy : dy + score.shape[0], dx : dx + score.shape[1]] for dy in range(3) for dx in range(3)) / 9
    else:
        score = bird_activity(lon_grid, lat_grid)
    score = np.ma.masked_where(~inside.reshape(score.shape), score)
    x_grid = 6_378_137.0 * np.radians(lon_grid)
    y_grid = 6_378_137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat_grid) / 2))
    return x_grid, y_grid, score


def draw_bird(network, context):
    province, districts, bounds = context
    fig, ax, paper = paper_map_figure()
    draw_paper_geography(ax, province, bounds, paper)
    x_grid, y_grid, public_score = bird_surface(bounds)
    score = gaussian_smooth_masked(bird_relief_surface(x_grid, y_grid, public_score))
    cell_area = cell_area_grid_km2(x_grid, y_grid)
    radius = 6_378_137.0
    lon_grid = np.degrees(x_grid / radius)
    lat_grid = np.degrees(2 * np.arctan(np.exp(y_grid / radius)) - np.pi / 2)
    corridor_score = np.ma.masked_where(
        np.ma.getmaskarray(score),
        bird_activity(lon_grid, lat_grid),
    )
    outer_score = gaussian_smooth_masked(
        np.ma.maximum(0.80 * score / max(float(score.max()), 1e-9), corridor_score),
        sigma_x=5.0,
        sigma_y=6.5,
    )
    outer_mask, outer_area, _ = calibrated_region_mask(outer_score, cell_area, 18_000, 38, 5)
    core_mask, core_area, _ = calibrated_region_mask(score, cell_area, 5_544.38, 22, 8)
    outer_mask = np.ma.masked_where(
        np.ma.getmaskarray(outer_mask),
        np.ma.filled(outer_mask, False) | np.ma.filled(core_mask, False),
    )
    draw_activity_regions(ax, x_grid, y_grid, outer_mask, core_mask)

    # Print boundaries and transmission routes after assembling the paper
    # relief, matching the approved concept: every route remains continuous.
    ax.add_collection(LineCollection(districts, colors=DISTRICT, linewidths=0.30, alpha=0.60, zorder=10))
    draw_network(ax, network["display"], "color", 0.94, z_offset=10)
    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.70, alpha=0.96, zorder=20))
    core_analysis = np.ma.masked_where(
        np.ma.getmaskarray(core_mask),
        np.ma.filled(core_mask, False).astype(float),
    )
    _, affected_lines = bird_public_analysis(network, (x_grid, y_grid, core_analysis))

    handles = [
        Line2D([0], [0], color="#DCE8F1", lw=5.2, label="活动关联区"),
        Line2D([0], [0], color="#AFC8DA", lw=5.2, label="重点适宜区"),
        Line2D([0], [0], color=STYLE["500plus"]["color"], lw=1.25, label="500kV及以上"),
        Line2D([0], [0], color=STYLE["220"]["color"], lw=1.15, label="220kV"),
        Line2D([0], [0], color=STYLE["110"]["color"], lw=1.05, label="110kV"),
    ]
    leg = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.50, 0.004), ncol=5, frameon=True, facecolor=LAND, edgecolor="#D8DDE0", framealpha=0.97, fancybox=True, fontsize=6.2, columnspacing=1.05, handlelength=1.65, borderpad=0.58)
    for item in leg.get_texts():
        item.set_color(MUTED)
    fig.text(0.055, 0.026, f"数据依据：省域鸟类生境适宜性公开研究的低分辨率分级栅格｜活动关联区约 {outer_area:,.0f} km²｜重点适宜区约 {core_area:,.0f} km²｜等面积平滑概化", fontsize=6.7, color="#777A7D", va="bottom")
    return save_figure(fig, "防鸟重点区域治理"), affected_lines


def point_distance_m(a, b):
    mean_lat = math.radians((a[1] + b[1]) / 2)
    dx = math.radians(a[0] - b[0]) * math.cos(mean_lat) * 6_371_000
    dy = math.radians(a[1] - b[1]) * 6_371_000
    return math.hypot(dx, dy)


JIANGSU_CITIES = {
    "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港",
    "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
}


def load_fireworks():
    if not FIREWORKS.exists():
        raise FileNotFoundError(
            f"已核验燃放点数据不存在：{FIREWORKS}；禁止随机生成、模拟或 fallback。"
        )
    data = json.loads(FIREWORKS.read_text(encoding="utf-8"))
    if int(data.get("schema_version", 0)) < 2:
        raise RuntimeError(f"省级燃放点数据 schema 版本过旧：{FIREWORKS}")

    audits = data.get("cities") or []
    audited_cities = {str(item.get("city", "")) for item in audits}
    if audited_cities != JIANGSU_CITIES:
        missing = sorted(JIANGSU_CITIES - audited_cities)
        extra = sorted(audited_cities - JIANGSU_CITIES)
        raise RuntimeError(f"燃放点省级审计必须覆盖江苏13市；缺失={missing}，异常={extra}")

    sources = {str(item.get("id", "")): item for item in data.get("sources", []) if item.get("id")}
    records = data.get("points") or []
    if not records:
        raise RuntimeError(f"已核验燃放点数据为空：{FIREWORKS}")

    normalized = []
    for item in records:
        city = str(item.get("city", ""))
        source_id = str(item.get("source_id", ""))
        if city not in JIANGSU_CITIES:
            raise RuntimeError(f"燃放点城市不在江苏13市审计范围：{item}")
        if source_id not in sources:
            raise RuntimeError(f"燃放点缺少可追溯 source_id：{item}")
        if not item.get("reference_year") or not item.get("coordinate_precision"):
            raise RuntimeError(f"燃放点缺少年份或坐标精度标记：{item}")
        lon, lat = float(item["lon"]), float(item["lat"])
        if not (116.0 <= lon <= 122.2 and 30.5 <= lat <= 35.4):
            raise RuntimeError(f"燃放点坐标超出江苏省域检查范围：{item}")
        normalized.append({**item, "lon": lon, "lat": lat})

    declared_points = {str(item["city"]): int(item.get("mapped_points", 0)) for item in audits}
    actual_points = defaultdict(int)
    for item in normalized:
        actual_points[item["city"]] += 1
    mismatched = {
        city: (declared_points.get(city, 0), actual_points.get(city, 0))
        for city in JIANGSU_CITIES
        if declared_points.get(city, 0) != actual_points.get(city, 0)
    }
    if mismatched:
        raise RuntimeError(f"燃放点城市审计数量与 points 不一致：{mismatched}")

    metadata = {
        "audited_cities": len(audited_cities),
        "mapped_cities": len({item["city"] for item in normalized}),
        "mapped_points": len(normalized),
        "source_count": len(sources),
        "reference_years": sorted({int(item["reference_year"]) for item in normalized}),
        "scope_note": data.get("scope_note", ""),
    }
    return normalized, metadata


def draw_fireworks(network, context, fireworks):
    if fireworks is None:
        return None
    records, metadata = fireworks
    points = [(item["lon"], item["lat"]) for item in records]
    province, districts, _bounds = context

    screening_radius_m = 500
    display_radius_m = 4_500

    # Keep the business screening rule at 500 m.  The province-scale map uses a
    # larger symbolized halo only so the influence marker remains legible.
    hit_points = {}
    hit_lines = set()
    for point in points:
        for lon, lat, line in network["poles"]:
            if abs(lon - point[0]) > 0.009 or abs(lat - point[1]) > 0.007:
                continue
            if point_distance_m(point, (lon, lat)) <= screening_radius_m:
                key = (round(lon, 6), round(lat, 6), line)
                hit_points[key] = (lon, lat, line)
                hit_lines.add(hashlib.sha1(line.encode("utf-8")).hexdigest()[:10])
    hit_points = list(hit_points.values())

    # Reproduce Figure 2's base map exactly.  Fireworks are an overlay only;
    # voltage colors, widths, alpha, province border and district boundaries are
    # not altered for this thematic figure.
    linework, _used_poles, _total_poles, _total_lines = load_base_linework()
    xs = [point[0] for ring in province for point in ring]
    ys = [point[1] for ring in province for point in ring]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    fig, ax = plt.subplots(figsize=(7.2, 8.8), facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    for ring in province:
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=LAND, zorder=0)
    ax.add_collection(LineCollection(districts, colors=DISTRICT, linewidths=0.34, alpha=0.46, zorder=1))
    for category in ["35", "110", "220", "other_dc", "500plus"]:
        style = STYLE[category]
        ax.add_collection(
            LineCollection(
                linework.get(category, []),
                colors=style["color"],
                linewidths=style["width"],
                alpha=style["alpha"],
                zorder=style["z"],
                capstyle="round",
                joinstyle="round",
            )
        )

    if points:
        projected = [mercator(lon, lat) for lon, lat in points]
        for (lon, lat), (x, y) in zip(points, projected):
            # Web Mercator scale grows by sec(latitude); compensate per point.
            projected_radius = display_radius_m / math.cos(math.radians(lat))
            ax.add_patch(
                Circle(
                    (x, y),
                    projected_radius,
                    facecolor="#F8C7C2",
                    edgecolor=CORAL,
                    linewidth=0.38,
                    alpha=0.30,
                    zorder=7,
                )
            )
        projected_array = np.asarray(projected)
        ax.scatter(
            projected_array[:, 0],
            projected_array[:, 1],
            s=13.5,
            c=CORAL,
            edgecolors=WHITE,
            linewidths=0.55,
            alpha=0.98,
            zorder=9,
        )

    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.66, alpha=0.92, zorder=10))
    pad_x = (max_x - min_x) * 0.08
    pad_y = (max_y - min_y) * 0.05
    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    handles = [
        Line2D([0], [0], color=STYLE[key]["color"], lw=max(STYLE[key]["width"] * 2.15, 1.0), alpha=STYLE[key]["alpha"], label=STYLE[key]["label"])
        for key in ["500plus", "220", "110", "35", "other_dc"]
    ]
    handles.append(Line2D([0], [0], color=DISTRICT, lw=0.9, alpha=0.72, label="地市界"))
    handles.extend(
        [
            Line2D([0], [0], color="none", lw=0, label="烟花燃放"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=CORAL, markeredgecolor=WHITE, markersize=5, label="公开燃放点"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#F8C7C2", markeredgecolor=CORAL, markeredgewidth=0.4, markersize=8, label="影响范围"),
        ]
    )
    legend = ax.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.99, 0.995),
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D7DCE2",
        framealpha=0.96,
        fancybox=True,
        fontsize=8.1,
        handlelength=2.5,
        borderpad=0.7,
        labelspacing=0.55,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
        if text.get_text() == "烟花燃放":
            text.set_weight("semibold")

    outputs = save_figure(fig, "集中燃放点缓冲筛查", tight=True)
    stats = {
        **metadata,
        "screening_radius_m": screening_radius_m,
        "display_radius_m": display_radius_m,
        "hit_poles": len(hit_points),
        "affected_lines": len(hit_lines),
    }
    return outputs, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["crossing", "fireworks", "all"], default="all")
    args = parser.parse_args()
    start = time.perf_counter()
    network = load_network()
    context = map_context()
    outputs = {}
    if args.only in {"crossing", "all"}:
        phase = time.perf_counter()
        railways, feature_count = extract_railways()
        crossings, affected, rail_segment_count = railway_analysis(network, railways)
        elapsed = time.perf_counter() - phase
        outputs["crossing"] = [str(p) for p in draw_crossing(network, context, railways, crossings, affected, rail_segment_count, elapsed)]
        outputs["crossing_stats"] = {"rail_features": feature_count, "rail_segments": rail_segment_count, "crossings": len(crossings), "affected_lines": affected, "seconds": round(elapsed, 2)}
    if args.only in {"fireworks", "all"}:
        result = draw_fireworks(network, context, load_fireworks())
        if result:
            figure_paths, stats = result
            outputs["fireworks"] = [str(p) for p in figure_paths]
            outputs["fireworks_stats"] = stats
        else:
            outputs["fireworks"] = "待写入已核验的公开点位数据"
    outputs["total_seconds"] = round(time.perf_counter() - start, 2)
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "summary.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
