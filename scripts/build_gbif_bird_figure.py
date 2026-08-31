#!/usr/bin/env python3
"""Build the GBIF-backed bird activity screening figure.

The figure uses the raw GBIF Darwin Core archive stored in data/birds and the
same read-only transmission network used by the other report maps. It converts
occurrence records into a province-clipped activity surface, highlights the
transmission segments intersecting the strongest activity cells, and reports
only derived aggregate counts.
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
from matplotlib.path import Path as MplPath

from build_report_spatial_figures import geometry_rings, load_network, map_context, draw_geography, draw_network, mercator
from map_style import BG, LAND, MUTED, OUTER, TEXT, WHITE, resolve_soffice

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
    names = zf.namelist()
    for wanted in ("occurrence.txt", "occurrence.tsv"):
        for name in names:
            if name.lower().endswith(wanted):
                return name
    for name in names:
        lower = name.lower()
        if (lower.endswith(".txt") or lower.endswith(".tsv")) and "occurrence" in lower:
            return name
    raise FileNotFoundError("GBIF ZIP 中未找到 occurrence.txt/occurrence.tsv")


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
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="replace"), delimiter="\t")
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
    outer_threshold = float(np.quantile(positive, 0.72))
    core_threshold = float(np.quantile(positive, 0.91))
    radius = 6_378_137.0
    x_grid = radius * np.radians(lon_grid)
    y_grid = radius * np.log(np.tan(np.pi / 4 + np.radians(lat_grid) / 2))
    return x_grid, y_grid, score, outer_threshold, core_threshold, (lon_min, lon_max, lat_min, lat_max)


def score_at(lon: float, lat: float, score, bounds):
    lon_min, lon_max, lat_min, lat_max = bounds
    ny, nx = score.shape
    ix = int((lon - lon_min) / max(lon_max - lon_min, 1e-12) * nx)
    iy = int((lat - lat_min) / max(lat_max - lat_min, 1e-12) * ny)
    ix = min(max(ix, 0), nx - 1)
    iy = min(max(iy, 0), ny - 1)
    if np.ma.getmaskarray(score)[iy, ix]:
        return -1.0
    return float(score[iy, ix])


def affected_segments(network, score, threshold, bounds):
    segments = []
    lines = set()
    for start, end, line_name, _category in network["segments"]:
        samples = [
            start, end,
            ((2 * start[0] + end[0]) / 3, (2 * start[1] + end[1]) / 3),
            ((start[0] + 2 * end[0]) / 3, (start[1] + 2 * end[1]) / 3),
        ]
        if max(score_at(lon, lat, score, bounds) for lon, lat in samples) >= threshold:
            segments.append([mercator(*start), mercator(*end)])
            lines.add(line_name)
    return segments, lines


def build():
    points, stats = load_occurrences()
    network = load_network()
    province, districts, map_bounds = map_context()
    x_grid, y_grid, score, outer_t, core_t, data_bounds = activity_surface(points)
    hit_segments, hit_lines = affected_segments(network, score, core_t, data_bounds)

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    ax = fig.add_axes([0.055, 0.075, 0.69, 0.82], facecolor=BG)
    draw_geography(ax, province, districts, map_bounds)
    outer = np.ma.masked_where(score < outer_t, score)
    core = np.ma.masked_where(score < core_t, score)
    ax.contourf(x_grid, y_grid, outer, levels=7, cmap="YlGn", alpha=0.42, zorder=2)
    ax.contourf(x_grid, y_grid, core, levels=6, cmap="YlOrRd", alpha=0.56, zorder=3)

    sample = points[np.linspace(0, len(points) - 1, min(len(points), 8000), dtype=int)]
    projected = np.asarray([mercator(lon, lat) for lon, lat in sample])
    ax.scatter(projected[:, 0], projected[:, 1], s=1.1, c="#128A3C", alpha=0.28, linewidths=0, zorder=4)
    draw_network(ax, network["display"], "color", 0.96, z_offset=5)
    if hit_segments:
        ax.add_collection(LineCollection(hit_segments, colors="#D94B3E", linewidths=0.95, alpha=0.94, zorder=18, capstyle="round"))
    ax.add_collection(LineCollection(province, colors=OUTER, linewidths=0.75, alpha=0.96, zorder=20))

    fig.text(0.055, 0.94, "提效案例2：鸟类活动重点区域筛查", fontsize=24, weight="bold", color=TEXT)
    fig.text(0.055, 0.905, "GBIF鸟类活动记录 → 活动热点 → 输电线路叠加 → 外协重点核验区段", fontsize=10.5, color=MUTED)

    panel = fig.add_axes([0.775, 0.11, 0.19, 0.75], facecolor=LAND)
    panel.set_xlim(0, 1); panel.set_ylim(0, 1); panel.axis("off")
    panel.text(0.05, 0.95, "筛选结果", fontsize=15, weight="bold", color=TEXT, va="top")
    cards = [("江苏省域GBIF记录", f"{stats['jiangsu_records']:,}条"), ("活动热点阈值", "省域分位数自动识别"), ("重点核验线路", f"{len(hit_lines):,}条")]
    y = 0.78
    for label, value in cards:
        panel.add_patch(plt.Rectangle((0.04, y - 0.12), 0.92, 0.15, facecolor="#F7FAFE", edgecolor="#D8E1EC", lw=0.8))
        panel.text(0.08, y - 0.01, label, fontsize=8.5, color=MUTED, va="center")
        panel.text(0.92, y - 0.01, value, fontsize=12.5, weight="bold", color="#174EA6", va="center", ha="right")
        y -= 0.20
    panel.text(0.06, 0.19, "管理用途", fontsize=10, weight="bold", color=TEXT)
    panel.text(0.06, 0.14, "系统先识别鸟类活动重点区域，\n再把穿越热点的线路转成外协\n重点巡视与防鸟装置核验清单。", fontsize=8.7, color=MUTED, va="top", linespacing=1.55)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#128A3C", markersize=4, label="GBIF鸟类活动记录"),
        Line2D([0], [0], color="#76B947", lw=5, alpha=0.55, label="活动关联区"),
        Line2D([0], [0], color="#F08B38", lw=5, alpha=0.70, label="活动热点区"),
        Line2D([0], [0], color="#D94B3E", lw=1.8, label="重点核验线路"),
    ]
    leg = ax.legend(handles=handles, loc="lower left", ncol=2, frameon=True, facecolor=WHITE, edgecolor="#D9DEE4", fontsize=7.2, framealpha=0.96)
    for item in leg.get_texts(): item.set_color(MUTED)

    fig.text(0.055, 0.028, f"数据来源：GBIF occurrence download 0046920-260806074905277｜省域内有效坐标记录 {stats['jiangsu_records']:,} 条｜仅输出聚合热点和脱敏线路关系", fontsize=7.4, color="#777A7D")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = OUT_DIR / f"{OUTPUT_STEM}.svg"
    png = OUT_DIR / f"{OUTPUT_STEM}.png"
    emf = OUT_DIR / f"{OUTPUT_STEM}.emf"
    fig.savefig(svg, format="svg", facecolor=BG)
    fig.savefig(png, format="png", dpi=320, facecolor=BG)
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
        "outer_quantile": 0.72,
        "core_quantile": 0.91,
        "affected_lines": len(hit_lines),
        "affected_segments": len(hit_segments),
        "network_poles": network["total_poles"],
        "network_lines": network["total_lines"],
        "outputs": {"svg": str(svg), "png": str(png), "emf": str(emf)},
    })
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
