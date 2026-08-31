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
FIREWORKS = ROOT / "data" / "fireworks_public_anonymized.json"
BOUNDARY = ROOT / "data" / "jiangsu_outline.geojson"
DISTRICTS = ROOT / "data" / "jiangsu_districts.geojson"

BG = "#F2F2F7"
LAND = "#FCFCFD"
CARD = "#F8F8FA"
WHITE = "#FFFFFF"
TEXT = "#20242A"
MUTED = "#737B86"
FAINT = "#DCE1E6"
DISTRICT = "#B7C0CA"
OUTER = "#7C8996"
GRAPHITE = "#434A52"
AMBER = "#D39124"
CORAL = "#E56658"
TEAL = "#1E9A8A"
EMERALD = "#35A77C"
BLUE = "#4D83C6"

STYLE = {
    "35": {"label": "35kV", "color": "#299873", "width": 0.16, "alpha": 0.36, "z": 2},
    "110": {"label": "110kV", "color": "#3375D6", "width": 0.20, "alpha": 0.44, "z": 3},
    "220": {"label": "220kV", "color": "#CF9015", "width": 0.27, "alpha": 0.54, "z": 4},
    "other_dc": {"label": "其他直流", "color": "#755CA7", "width": 0.31, "alpha": 0.58, "z": 5},
    "500plus": {"label": "500kV及以上", "color": "#D94F5C", "width": 0.45, "alpha": 0.66, "z": 6},
}
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
    ax = fig.add_axes([0.035, 0.055, 0.60, 0.90], facecolor=BG)
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


def draw_network(ax, display, mode="color", alpha_factor=1.0):
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
                zorder=style["z"],
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
        loc="lower left",
        bbox_to_anchor=(0.015, 0.01),
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


def save_figure(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{stem}.svg"
    png = OUT / f"{stem}.png"
    fig.savefig(svg, format="svg", facecolor=BG)
    fig.savefig(png, format="png", dpi=320, facecolor=BG)
    plt.close(fig)
    with tempfile.TemporaryDirectory(prefix="report-spatial-lo-") as profile:
        subprocess.run(
            [
                "soffice",
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
    province, districts, bounds = context
    fig, ax = base_figure()
    draw_geography(ax, province, districts, bounds)
    draw_network(ax, network["display"], "color", 0.82)
    rail_display = []
    for line in railway_lines:
        points = [(round(a, 3), round(b, 3)) for a, b in simplify(line, 0.0025)]
        if len(points) >= 2:
            rail_display.append([mercator(*p) for p in points])
    ax.add_collection(LineCollection(rail_display, colors="#F7F8F9", linewidths=0.92, alpha=0.98, zorder=7, capstyle="round"))
    ax.add_collection(LineCollection(rail_display, colors=GRAPHITE, linewidths=0.42, alpha=0.78, zorder=8, capstyle="round"))
    # Preserve full counts in the metrics, but show at most one representative
    # crossing per small map cell.  This is a visual de-cluttering operation only.
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
    legend_lines(ax, True)
    add_cards(
        fig,
        [
            ("杆塔底账", f"{network['total_poles'] / 10000:.1f}万基"),
            ("输电线路", f"{network['total_lines']:,}条"),
            ("交跨候选", f"{len(crossings):,}处"),
            ("涉及线路", f"{affected:,}条"),
        ],
        AMBER,
    )
    inset = add_inset_frame(fig, AMBER)
    if crossings:
        focus = max(crossings, key=lambda p: p[2] == "500plus")
        focus_xy = mercator(focus[0], focus[1])
        rx = 5_200
        ry = 5_400
        for segments in network["display"].values():
            local = [s for s in segments if any(abs(x - focus_xy[0]) < rx and abs(y - focus_xy[1]) < ry for x, y in s)]
            if local:
                inset.add_collection(LineCollection(local, colors="#6C8FB5", linewidths=0.8, alpha=0.75, zorder=2))
        local_rail = [s for s in rail_display if any(abs(x - focus_xy[0]) < rx and abs(y - focus_xy[1]) < ry for x, y in s)]
        inset.add_collection(LineCollection(local_rail, colors=WHITE, linewidths=3.2, alpha=1, zorder=3))
        inset.add_collection(LineCollection(local_rail, colors=GRAPHITE, linewidths=1.35, alpha=0.90, zorder=4))
        inset.scatter([focus_xy[0]], [focus_xy[1]], s=74, c=AMBER, edgecolors=WHITE, linewidths=1.4, zorder=5)
        inset.scatter([focus_xy[0]], [focus_xy[1]], s=140, facecolors="none", edgecolors=CORAL, linewidths=1.1, zorder=6)
        inset.set_xlim(focus_xy[0] - rx, focus_xy[0] + rx)
        inset.set_ylim(focus_xy[1] - ry, focus_xy[1] + ry)
        inset.set_aspect("equal")
        add_leader(fig, ax, focus_xy, AMBER)
    inset.text(0.05, 0.05, "粗筛定位  ·  几何求交  ·  人工复核", transform=inset.transAxes, fontsize=6.7, color=MUTED, zorder=8)
    add_footer(fig, f"数据来源：输电杆塔台账与公开铁路要素｜铁路线段 {rail_segment_count:,}段｜计算用时 {elapsed:.1f}s｜图中不保存线路名称、杆号和坐标")
    return save_figure(fig, "铁路交叉跨越识别")


def bird_activity(lon, lat):
    """Public-study-informed bird habitat/activity potential, scaled 0..1.

    The centres and anisotropy follow the province-level forest/water-bird
    suitability map and its published interpretation.  This is a redrawn,
    generalized surface; it is not a copy of the article's raster figure.
    """
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    zones = [
        # southwest lake group and southern water network
        (120.12, 31.30, 0.36, 0.20, 1.00),
        (119.55, 31.55, 0.55, 0.25, 0.92),
        (118.72, 31.72, 0.43, 0.30, 0.88),
        # major river corridor from west to east
        (118.70, 32.08, 0.40, 0.18, 0.84),
        (119.55, 32.03, 0.56, 0.18, 0.78),
        (120.52, 32.00, 0.58, 0.17, 0.82),
        # coastal wetlands / migratory flyway
        (120.39, 32.72, 0.20, 0.50, 0.86),
        (120.35, 33.42, 0.19, 0.63, 1.00),
        (120.04, 34.16, 0.23, 0.45, 0.84),
        (119.30, 34.66, 0.24, 0.23, 0.88),
        # northern and central lake/wetland stepping stones
        (117.78, 34.24, 0.31, 0.22, 0.48),
        (118.72, 33.20, 0.33, 0.24, 0.48),
        (119.15, 32.72, 0.30, 0.22, 0.46),
    ]
    score = np.zeros(np.broadcast(lon, lat).shape, dtype=float)
    for cx, cy, sx, sy, weight in zones:
        value = weight * np.exp(-0.5 * (((lon - cx) / sx) ** 2 + ((lat - cy) / sy) ** 2))
        score = np.maximum(score, value)
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
    fig, ax = base_figure()
    draw_geography(ax, province, districts, bounds)
    x_grid, y_grid, score = bird_surface(bounds)
    levels = [0.18, 0.36, 0.56, 0.74, 1.01]
    colors = ["#DDEFE9", "#B8DED2", "#75C0A5", "#2E9C7B"]
    ax.contourf(x_grid, y_grid, score, levels=levels, colors=colors, alpha=0.56, antialiased=True, zorder=2)
    ax.contour(x_grid, y_grid, score, levels=[0.36, 0.56, 0.74], colors=["#80BDAA", "#4FA98E", "#23866F"], linewidths=[0.28, 0.38, 0.48], alpha=0.55, zorder=3)
    draw_network(ax, network["display"], "gray", 0.72)
    priority, affected_lines = bird_public_analysis(network, (x_grid, y_grid, score))
    ax.add_collection(LineCollection(priority, colors="#147F72", linewidths=0.40, alpha=0.55, zorder=8, capstyle="round"))

    add_cards(
        fig,
        [
            ("省域记录鸟类", "468种"),
            ("模型目标物种", "64种"),
            ("识别生境斑块", "274个"),
            ("重要生态廊道", "12条"),
        ],
        TEAL,
    )
    inset = add_inset_frame(fig, TEAL)
    score_values = np.ma.filled(score, -1)
    focus_index = np.unravel_index(np.argmax(score_values), score_values.shape)
    focus_xy = (float(x_grid[focus_index]), float(y_grid[focus_index]))
    rx, ry = 34_000, 29_000
    x_mask = np.abs(x_grid[0, :] - focus_xy[0]) < rx
    y_mask = np.abs(y_grid[:, 0] - focus_xy[1]) < ry
    inset.contourf(x_grid[np.ix_(y_mask, x_mask)], y_grid[np.ix_(y_mask, x_mask)], score[np.ix_(y_mask, x_mask)], levels=levels, colors=colors, alpha=0.66, zorder=1)
    local_network = []
    local_priority = []
    for segments in network["display"].values():
        local_network.extend([segment for segment in segments if any(abs(x - focus_xy[0]) < rx and abs(y - focus_xy[1]) < ry for x, y in segment)])
    for segment in priority:
        if any(abs(x - focus_xy[0]) < rx and abs(y - focus_xy[1]) < ry for x, y in segment):
            local_priority.append(segment)
    inset.add_collection(LineCollection(local_network, colors="#9AA8B5", linewidths=0.55, alpha=0.48, zorder=2))
    inset.add_collection(LineCollection(local_priority, colors="#147F72", linewidths=1.25, alpha=0.86, zorder=3, capstyle="round"))
    sample_nodes = []
    for segment in local_priority[:: max(1, len(local_priority) // 55)]:
        sample_nodes.append(segment[0])
    if sample_nodes:
        sample_nodes = np.asarray(sample_nodes)
        inset.scatter(sample_nodes[:, 0], sample_nodes[:, 1], s=8, c=TEAL, edgecolors=WHITE, linewidths=0.35, alpha=0.85, zorder=4)
    inset.set_xlim(focus_xy[0] - rx, focus_xy[0] + rx)
    inset.set_ylim(focus_xy[1] - ry, focus_xy[1] + ry)
    inset.set_aspect("equal")
    add_leader(fig, ax, focus_xy, TEAL)
    inset.text(0.05, 0.05, "活动潜势  ·  重点区  ·  优先治理区段", transform=inset.transAxes, fontsize=6.7, color=MUTED, zorder=8)

    handles = [
        Line2D([0], [0], color="#B8DED2", lw=6, alpha=0.65, label="中等活动潜势"),
        Line2D([0], [0], color="#2E9C7B", lw=6, alpha=0.70, label="高活动潜势"),
        Line2D([0], [0], color="#147F72", lw=1.4, alpha=0.88, label="优先治理线路区段"),
    ]
    leg = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.015, 0.01), ncol=3, frameon=True, facecolor=WHITE, edgecolor="#D9DEE4", framealpha=0.96, fancybox=True, fontsize=6.5, columnspacing=1.1, handlelength=1.8, borderpad=0.6)
    for item in leg.get_texts():
        item.set_color(MUTED)
    add_footer(fig, f"数据依据：《江苏省域鸟类多样性保护格局构建与生态廊道优化》（DOI:10.31497/zrzyxb.20241206）｜生境分布区 5,544.38 km²｜涉及优先治理线路 {affected_lines:,}条")
    return save_figure(fig, "防鸟重点区域治理"), affected_lines


def point_distance_m(a, b):
    mean_lat = math.radians((a[1] + b[1]) / 2)
    dx = math.radians(a[0] - b[0]) * math.cos(mean_lat) * 6_371_000
    dy = math.radians(a[1] - b[1]) * 6_371_000
    return math.hypot(dx, dy)


def load_fireworks():
    if not FIREWORKS.exists():
        return None
    data = json.loads(FIREWORKS.read_text(encoding="utf-8"))
    return [(float(item["lon"]), float(item["lat"])) for item in data.get("points", [])], data.get("source_count", 0), data.get("source_note", "")


def draw_fireworks(network, context, fireworks):
    if fireworks is None:
        return None
    points, source_count, source_note = fireworks
    province, districts, bounds = context
    hit_points = []
    hit_lines = set()
    for point in points:
        nearest = []
        for lon, lat, line in network["poles"]:
            if abs(lon - point[0]) > 0.009 or abs(lat - point[1]) > 0.007:
                continue
            distance = point_distance_m(point, (lon, lat))
            if distance <= 500:
                nearest.append((lon, lat, line))
                hit_lines.add(hashlib.sha1(line.encode("utf-8")).hexdigest()[:10])
        if nearest:
            hit_points.extend(nearest)

    fig, ax = base_figure()
    draw_geography(ax, province, districts, bounds)
    draw_network(ax, network["display"], "color", 0.55)
    projected = np.array([mercator(*p) for p in points]) if points else np.empty((0, 2))
    hit_projected = np.array([mercator(p[0], p[1]) for p in hit_points]) if hit_points else np.empty((0, 2))
    if len(projected):
        # A 500 m ground buffer is slightly enlarged in Web Mercator by sec(latitude).
        for x, y in projected:
            ax.add_patch(Circle((x, y), 595, facecolor=CORAL, edgecolor=CORAL, linewidth=0.32, alpha=0.095, zorder=7))
        ax.scatter(projected[:, 0], projected[:, 1], s=10, c=CORAL, edgecolors=WHITE, linewidths=0.45, alpha=0.94, zorder=9)
    if len(hit_projected):
        ax.scatter(hit_projected[:, 0], hit_projected[:, 1], s=2.8, c=AMBER, alpha=0.72, linewidths=0, zorder=8)
    add_cards(
        fig,
        [
            ("公开燃放点", f"{len(points):,}处"),
            ("500米缓冲区", f"{len(points):,}个"),
            ("命中杆塔", f"{len(hit_points):,}基"),
            ("涉及线路", f"{len(hit_lines):,}条"),
        ],
        CORAL,
    )
    inset = add_inset_frame(fig, CORAL)
    if points:
        focus = max(points, key=lambda point: sum(1 for lon, lat, _ in network["poles"] if abs(lon - point[0]) < 0.009 and abs(lat - point[1]) < 0.007 and point_distance_m(point, (lon, lat)) <= 500))
        focus_xy = mercator(*focus)
        inset.add_patch(Circle(focus_xy, 595, facecolor=CORAL, edgecolor=CORAL, linewidth=1.0, alpha=0.12, zorder=2))
        inset.scatter([focus_xy[0]], [focus_xy[1]], s=58, c=CORAL, edgecolors=WHITE, linewidths=1.2, zorder=5)
        local_nodes = [mercator(lon, lat) for lon, lat, _ in network["poles"] if abs(lon - focus[0]) < 0.014 and abs(lat - focus[1]) < 0.011]
        if local_nodes:
            local_nodes = np.array(local_nodes)
            inset.scatter(local_nodes[:, 0], local_nodes[:, 1], s=7.5, c="#7190AE", edgecolors=WHITE, linewidths=0.3, alpha=0.8, zorder=4)
        for segments in network["display"].values():
            local = [s for s in segments if any(abs(x - focus_xy[0]) < 1600 and abs(y - focus_xy[1]) < 1600 for x, y in s)]
            if local:
                inset.add_collection(LineCollection(local, colors="#527DA4", linewidths=0.9, alpha=0.72, zorder=3))
        inset.set_xlim(focus_xy[0] - 1600, focus_xy[0] + 1600)
        inset.set_ylim(focus_xy[1] - 1600, focus_xy[1] + 1600)
        inset.set_aspect("equal")
        add_leader(fig, ax, focus_xy, CORAL)
    inset.text(0.05, 0.05, "公开点位  ·  500米缓冲  ·  杆塔命中", transform=inset.transAxes, fontsize=6.7, color=MUTED, zorder=8)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CORAL, markeredgecolor=WHITE, markersize=5, label="公开燃放点"),
        Line2D([0], [0], marker="o", color=CORAL, markerfacecolor=CORAL, alpha=0.17, markersize=9, label="500米缓冲区"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=AMBER, markersize=4, label="命中杆塔"),
    ]
    leg = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.015, 0.01), ncol=3, frameon=True, facecolor=WHITE, edgecolor="#D9DEE4", framealpha=0.96, fancybox=True, fontsize=6.5, columnspacing=1.1, handlelength=1.8, borderpad=0.6)
    for item in leg.get_texts():
        item.set_color(MUTED)
    add_footer(fig, f"数据来源：省内政府及公安机关公开通告（汇总 {source_count}份）｜仅保留脱敏点位用于方法演示｜{source_note}")
    return save_figure(fig, "集中燃放点缓冲筛查")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["crossing", "bird", "fireworks", "all"], default="all")
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
    if args.only in {"bird", "all"}:
        result, affected_lines = draw_bird(network, context)
        outputs["bird"] = [str(p) for p in result]
        outputs["bird_stats"] = {
            "public_model": "DOI:10.31497/zrzyxb.20241206",
            "target_species": 64,
            "habitat_area_km2": 5544.38,
            "habitat_patches": 274,
            "important_corridors": 12,
            "affected_lines": affected_lines,
        }
    if args.only in {"fireworks", "all"}:
        result = draw_fireworks(network, context, load_fireworks())
        if result:
            outputs["fireworks"] = [str(p) for p in result]
        else:
            outputs["fireworks"] = "待写入已核验的公开点位数据"
    outputs["total_seconds"] = round(time.perf_counter() - start, 2)
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "summary.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
