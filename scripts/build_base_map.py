#!/opt/homebrew/bin/python3
"""Build the Jiangsu transmission-network base map from the read-only pole database.

The figure follows the visual hierarchy of the earlier Nanjing crossing map:
administrative boundaries below, voltage-coded transmission lines above, and
high-voltage backbone lines drawn last with greater line weight. No line name,
tower number, city label, or coordinate axis is written into the figure.
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from map_style import BG, DISTRICT, LAND, OUTER, STYLE, TEXT, resolve_soffice


ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("POLE_DB", "/Users/zhangyuxi/Desktop/000基础数据/pole_data.db"))
BOUNDARY = ROOT / "data" / "jiangsu_outline.geojson"
DISTRICTS = ROOT / "data" / "jiangsu_districts.geojson"
OUT = ROOT / "dist" / "figures"
OUTPUT_STEM = "江苏省域输电线路电压等级分布"

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
    }
)


def mercator(lon: float, lat: float) -> tuple[float, float]:
    radius = 6_378_137.0
    return radius * math.radians(lon), radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def trailing_number(value: str | None) -> int:
    nums = re.findall(r"\d+", value or "")
    return int(nums[-1]) if nums else 10**9


def branch_key(name: str | None, pole_num: str | None) -> tuple[str, int]:
    text = name or ""
    match = re.search(r"(\d+)\s*$", text)
    if match:
        return text[: match.start()], int(match.group(1))
    return text, trailing_number(pole_num)


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
    farthest = 0.0
    index = 0
    for i in range(1, len(points) - 1):
        distance = perpendicular_distance(points[i], points[0], points[-1])
        if distance > farthest:
            index, farthest = i, distance
    if farthest <= tolerance:
        return [points[0], points[-1]]
    left = simplify(points[: index + 1], tolerance)
    right = simplify(points[index:], tolerance)
    return left[:-1] + right


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


def load_linework():
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
    for line, name, pole_num, code, lon, lat in rows:
        prefix, sequence = branch_key(name, pole_num)
        key = (line, prefix)
        groups[key].append((sequence, float(lon), float(lat)))
        categories[key] = classify(str(code or ""), line)

    collections = defaultdict(list)
    used_poles = defaultdict(int)
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
        tolerance = {"35": 0.0028, "110": 0.0022, "220": 0.0016, "other_dc": 0.0012, "500plus": 0.0010}[category]
        for chunk in chunks:
            if len(chunk) < 2:
                continue
            points = simplify(chunk, tolerance)
            # Quantization limits recoverable precision in the vector deliverable.
            points = [(round(lon, 4), round(lat, 4)) for lon, lat in points]
            projected = [mercator(lon, lat) for lon, lat in points]
            if len(projected) >= 2:
                collections[category].append(projected)
                used_poles[category] += len(chunk)
    return collections, used_poles, total_poles, total_lines


def draw_map():
    province = geometry_rings(BOUNDARY)
    districts = geometry_rings(DISTRICTS)
    linework, used_poles, total_poles, total_lines = load_linework()

    province_xy = [[mercator(lon, lat) for lon, lat in ring] for ring in province]
    district_xy = [[mercator(lon, lat) for lon, lat in ring] for ring in districts]
    xs = [point[0] for ring in province_xy for point in ring]
    ys = [point[1] for ring in province_xy for point in ring]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    fig, ax = plt.subplots(figsize=(7.2, 8.8), facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    for ring in province_xy:
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=LAND, zorder=0)
    # A quiet administrative layer stays below the thematic network.
    ax.add_collection(LineCollection(district_xy, colors=DISTRICT, linewidths=0.34, alpha=0.46, zorder=1))

    order = ["35", "110", "220", "other_dc", "500plus"]
    for category in order:
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
    ax.add_collection(LineCollection(province_xy, colors=OUTER, linewidths=0.66, alpha=0.92, zorder=8))

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

    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{OUTPUT_STEM}.svg"
    png = OUT / f"{OUTPUT_STEM}.png"
    fig.savefig(svg, format="svg", bbox_inches="tight", pad_inches=0.08, facecolor=BG)
    fig.savefig(png, format="png", dpi=320, bbox_inches="tight", pad_inches=0.08, facecolor=BG)
    plt.close(fig)

    with tempfile.TemporaryDirectory(prefix="base-map-lo-") as profile:
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

    summary = {key: {"segments": len(linework.get(key, [])), "poles": used_poles.get(key, 0)} for key in STYLE}
    print(f"[base-map] {total_poles} poles / {total_lines} lines -> {png}")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    draw_map()
