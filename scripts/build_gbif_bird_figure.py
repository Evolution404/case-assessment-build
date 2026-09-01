#!/usr/bin/env python3
"""Build the GBIF-backed bird activity overlay on the formal base map.

The figure uses the raw GBIF Darwin Core archive stored in data/birds and the
same formal transmission-network styling as Figure 2. Bird observations are
used only to derive a province-clipped activity surface; raw occurrence points
and any derived "priority line" styling are intentionally not rendered.
"""
from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.path import Path as MplPath

from build_base_map import geometry_rings, load_linework, mercator
from map_style import BG, DISTRICT, LAND, OUTER, STYLE, TEXT, resolve_soffice

ROOT = Path(__file__).resolve().parents[1]
GBIF_ZIP = ROOT / "data" / "birds" / "gbif-occurrence-0046920-260806074905277.zip"
BOUNDARY = ROOT / "data" / "jiangsu_outline.geojson"
OUT_DIR = ROOT / "dist" / "figures"
OUTPUT_STEM = "06-鸟类活动重点区域筛查"
SUMMARY = ROOT / ".build" / "report-spatial" / "gbif-bird-summary.json"

plt.rcParams.update({
    "font.family": ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "Arial Unicode MS"],
    "axes.unicode_minus": False,
    "savefig.transparent": False,
    "svg.fonttype": "none",
})


def occurrence_member(zf: zipfile.ZipFile) -> str:
    names = [name for name in zf.namelist() if not name.endswith("/")]
    for wanted in ("occurrence.txt", "occurrence.tsv", "occurrence.csv"):
        for name in names:
            if name.lower().endswith(wanted):
                return name
    tabular = [name for name in names if name.lower().endswith((".txt", ".tsv", ".csv"))]
    for name in tabular:
        if "occurrence" in name.lower():
            return name
    if len(tabular) == 1:
        return tabular[0]
    raise FileNotFoundError("GBIF ZIP 中未找到可识别的 occurrence TXT/TSV/CSV 数据表")


def load_occurrences() -> tuple[np.ndarray, dict]:
    if not GBIF_ZIP.exists():
        raise FileNotFoundError(f"GBIF 数据不存在：{GBIF_ZIP}")
    rings = geometry_rings(BOUNDARY)
    paths = [MplPath(np.asarray(ring, dtype=float)) for ring in rings]
    lon_min = min(point[0] for ring in rings for point in ring)
    lon_max = max(point[0] for ring in rings for point in ring)
    lat_min = min(point[1] for ring in rings for point in ring)
    lat_max = max(point[1] for ring in rings for point in ring)

    kept = []
    scanned = rejected_missing = rejected_bounds = rejected_outside = 0
    with zipfile.ZipFile(GBIF_ZIP) as zf:
        member = occurrence_member(zf)
        with zf.open(member) as raw:
            import io
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace")
            header = text.readline()
            delimiter = "\t" if header.count("\t") >= header.count(",") else ","
            fieldnames = next(csv.reader([header], delimiter=delimiter))
            reader = csv.DictReader(text, fieldnames=fieldnames, delimiter=delimiter)
            required = {"decimalLongitude", "decimalLatitude"}
            if not required.issubset(set(fieldnames)):
                raise RuntimeError(f"GBIF occurrence 表缺少必要坐标字段：{sorted(required - set(fieldnames))}")
            for row in reader:
                scanned += 1
                try:
                    lon = float(row.get("decimalLongitude") or "")
                    lat = float(row.get("decimalLatitude") or "")
                except ValueError:
                    rejected_missing += 1
                    continue
                if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
                    rejected_bounds += 1
                    continue
                if not any(path.contains_point((lon, lat)) for path in paths):
                    rejected_outside += 1
                    continue
                kept.append((lon, lat))
    if not kept:
        raise RuntimeError("GBIF 数据在江苏省域内没有可用坐标记录")
    return np.asarray(kept, dtype=float), {
        "archive": GBIF_ZIP.name,
        "scanned_records": scanned,
        "jiangsu_records": len(kept),
        "rejected_missing_coordinates": rejected_missing,
        "rejected_outside_bbox": rejected_bounds,
        "rejected_outside_boundary": rejected_outside,
    }


def smooth(surface: np.ndarray, passes: int = 7) -> np.ndarray:
    values = surface.astype(float)
    for _ in range(passes):
        padded = np.pad(values, 1, mode="edge")
        values = sum(
            padded[dy:dy + values.shape[0], dx:dx + values.shape[1]]
            for dy in range(3) for dx in range(3)
        ) / 9.0
    return values


def activity_surface(points: np.ndarray, nx=170, ny=210):
    rings = geometry_rings(BOUNDARY)
    lon_min = min(point[0] for ring in rings for point in ring)
    lon_max = max(point[0] for ring in rings for point in ring)
    lat_min = min(point[1] for ring in rings for point in ring)
    lat_max = max(point[1] for ring in rings for point in ring)
    counts, lon_edges, lat_edges = np.histogram2d(points[:, 0], points[:, 1], bins=[nx, ny], range=[[lon_min, lon_max], [lat_min, lat_max]])
    score = smooth(np.log1p(counts.T), 7)
    lon_centers = (lon_edges[:-1] + lon_edges[1:]) / 2
    lat_centers = (lat_edges[:-1] + lat_edges[1:]) / 2
    lon_grid, lat_grid = np.meshgrid(lon_centers, lat_centers)
    flat = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])
    inside = np.zeros(len(flat), dtype=bool)
    for ring in rings:
        inside |= MplPath(np.asarray(ring, dtype=float)).contains_points(flat)
    score = np.ma.masked_where(~inside.reshape(score.shape), score)
    positive = score.compressed()
    positive = positive[positive > 0]
    if not len(positive):
        raise RuntimeError("GBIF 活动栅格为空")
    low_threshold = float(np.quantile(positive, 0.70))
    medium_threshold = float(np.quantile(positive, 0.84))
    high_threshold = float(np.quantile(positive, 0.94))
    radius = 6_378_137.0
    x_grid = radius * np.radians(lon_grid)
    y_grid = radius * np.log(np.tan(np.pi / 4 + np.radians(lat_grid) / 2))
    return x_grid, y_grid, score, low_threshold, medium_threshold, high_threshold


def build():
    points, stats = load_occurrences()
    linework, _used_poles, total_poles, total_lines = load_linework()
    province = [[mercator(lon, lat) for lon, lat in ring] for ring in geometry_rings(BOUNDARY)]
    districts = [[mercator(lon, lat) for lon, lat in ring] for ring in geometry_rings(ROOT / "data" / "jiangsu_districts.geojson")]
    x_grid, y_grid, score, low_t, medium_t, high_t = activity_surface(points)

    xs = [point[0] for ring in province for point in ring]
    ys = [point[1] for ring in province for point in ring]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Reproduce Figure 2 exactly, then place the bird-activity surface above it.
    fig, ax = plt.subplots(figsize=(7.2, 8.8), facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    for ring in province:
        ax.fill([p[0] for p in ring], [p[1] for p in ring], color=LAND, zorder=0)
    ax.add_collection(LineCollection(districts, colors=DISTRICT, linewidths=0.34, alpha=0.46, zorder=1))

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

    activity = np.ma.masked_where(score < low_t, score)
    max_score = float(score.max())
    ax.contourf(
        x_grid,
        y_grid,
        activity,
        levels=[low_t, medium_t, high_t, max_score + 1e-9],
        colors=["#F4D77E", "#E9A344", "#C65C32"],
        alpha=0.26,
        antialiased=True,
        zorder=7,
    )
    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.66, alpha=0.92, zorder=8))

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
            Line2D([0], [0], color="none", lw=0, label="鸟类活动"),
            Patch(facecolor="#F4D77E", edgecolor="none", alpha=0.52, label="一般"),
            Patch(facecolor="#E9A344", edgecolor="none", alpha=0.58, label="较活跃"),
            Patch(facecolor="#C65C32", edgecolor="none", alpha=0.64, label="高活跃"),
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
        if text.get_text() == "鸟类活动":
            text.set_weight("semibold")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = OUT_DIR / f"{OUTPUT_STEM}.svg"
    png = OUT_DIR / f"{OUTPUT_STEM}.png"
    emf = OUT_DIR / f"{OUTPUT_STEM}.emf"
    fig.savefig(svg, format="svg", bbox_inches="tight", pad_inches=0.08, facecolor=BG)
    fig.savefig(png, format="png", dpi=320, bbox_inches="tight", pad_inches=0.08, facecolor=BG)
    plt.close(fig)
    with tempfile.TemporaryDirectory(prefix="gbif-bird-lo-") as profile:
        subprocess.run(
            [
                resolve_soffice(),
                f"-env:UserInstallation={Path(profile).resolve().as_uri()}",
                "--headless",
                "--convert-to",
                "emf",
                "--outdir",
                str(OUT_DIR),
                str(svg),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if not emf.exists():
        raise RuntimeError(f"EMF 导出失败：{emf}")

    stats.update({
        "activity_quantiles": {"general": 0.70, "active": 0.84, "high": 0.94},
        "network_poles": total_poles,
        "network_lines": total_lines,
        "outputs": {"svg": str(svg), "png": str(png), "emf": str(emf)},
    })
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
