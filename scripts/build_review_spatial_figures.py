#!/usr/bin/env python3
"""Render the four spatial review figures from repository-contained data only.

This renderer is intentionally GitHub/CI friendly: it never needs the local
production pole database or railway PBF. Figures 2/5/7 use the committed,
anonymized demo network; figure 6 uses the committed GBIF archive for bird
occurrence hotspots and overlays the anonymized demo routes.
"""
from __future__ import annotations

import csv
import json
import math
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "figures"
DEMO = json.loads((ROOT / "data" / "demo.json").read_text(encoding="utf-8"))
GBIF = ROOT / "data" / "birds" / "gbif-occurrence-0046920-260806074905277.zip"

BG = "#F7F8FA"
LAND = "#FFFFFF"
TEXT = "#172033"
MUTED = "#687386"
BORDER = "#DCE2EA"
BLUE = "#2F6FDB"
BLUE_DARK = "#174EA6"
ORANGE = "#EA7A25"
RED = "#D84A3A"
GREEN = "#2C9A5B"
AMBER = "#D39124"
RAIL = "#59616C"

LEVEL_COLORS = {
    "35": "#C4D2CD",
    "37": "#E66F62",
    "50": "#B9B2C6",
    "78": "#E66F62",
    "83": "#D7B36D",
    "85": "#E66F62",
}

plt.rcParams.update({
    "font.family": ["Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", "SimHei", "Arial Unicode MS"],
    "axes.unicode_minus": False,
    "savefig.transparent": False,
})


def new_canvas(title: str):
    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor=BG)
    fig.text(0.04, 0.945, title, fontsize=25, weight="bold", color=TEXT, va="center")
    fig.add_artist(Line2D([0.035, 0.965], [0.905, 0.905], transform=fig.transFigure, color=BORDER, lw=1.2))
    return fig


def add_card(fig, xywh, title, value, color=BLUE):
    x, y, w, h = xywh
    ax = fig.add_axes([x, y, w, h]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02,rounding_size=0.05", fc="white", ec=BORDER, lw=1.2))
    ax.text(0.08, 0.72, title, fontsize=13, color=MUTED, weight="bold", va="center")
    ax.text(0.08, 0.34, value, fontsize=25, color=color, weight="bold", va="center")


def draw_demo_base(ax, *, alpha=0.85):
    outline = np.asarray(DEMO["outline"])
    ax.add_patch(Polygon(outline, closed=True, fc=LAND, ec="#9BA7B4", lw=1.4, zorder=0))
    for route in DEMO["routes"]:
        pts = np.asarray(route["points"])
        ax.plot(pts[:, 0], pts[:, 1], color=LEVEL_COLORS.get(str(route.get("level")), BLUE), lw=1.0, alpha=alpha, zorder=2)
    ax.set_xlim(35, 1165); ax.set_ylim(675, 35); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=150, facecolor=BG, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"[review-spatial] {path}")


def fig02():
    fig = new_canvas("省域线路 / 杆塔任务规模")
    ax = fig.add_axes([0.04, 0.07, 0.69, 0.79], facecolor=BG)
    draw_demo_base(ax, alpha=0.9)
    ax.text(70, 640, "全省脱敏线路模型", fontsize=12, color=MUTED, weight="bold")
    add_card(fig, (0.76, 0.60, 0.20, 0.18), "输电杆塔", f"{DEMO['meta']['provincePoles']/10000:.1f}万基", BLUE_DARK)
    add_card(fig, (0.76, 0.39, 0.20, 0.18), "输电线路", f"{DEMO['meta']['provinceLines']}条", BLUE_DARK)
    ax2 = fig.add_axes([0.76, 0.12, 0.20, 0.21]); ax2.axis("off")
    ax2.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02,rounding_size=0.04", fc="#EEF5FF", ec="#C8DCF7", lw=1.1))
    ax2.text(0.08, 0.68, "点多、线长、面广", fontsize=15, color=BLUE_DARK, weight="bold")
    ax2.text(0.08, 0.42, "传统人工全量排查", fontsize=13, color=TEXT)
    ax2.text(0.08, 0.22, "工作量随设备规模同步增长", fontsize=12, color=MUTED)
    save(fig, "02-省域任务规模.png")


def fig05():
    fig = new_canvas("提效案例1：交叉跨越自动筛查")
    ax = fig.add_axes([0.035, 0.07, 0.70, 0.80], facecolor=BG)
    draw_demo_base(ax, alpha=0.68)
    for rail in DEMO["railways"]:
        pts = np.asarray(rail["points"])
        ax.plot(pts[:, 0], pts[:, 1], color=RAIL, lw=2.0, ls="--", alpha=0.8, zorder=3)
    points = np.asarray(DEMO["crossings"][:42]) if DEMO["crossings"] else np.empty((0, 2))
    if len(points):
        ax.scatter(points[:, 0], points[:, 1], s=70, facecolors="none", edgecolors=RED, linewidths=1.7, zorder=5)
        ax.scatter(points[:, 0], points[:, 1], s=14, c=RED, zorder=6)
    ax2 = fig.add_axes([0.77, 0.11, 0.19, 0.72]); ax2.axis("off")
    ax2.add_patch(FancyBboxPatch((0,0.61),1,0.37,boxstyle="round,pad=0.02,rounding_size=0.04",fc="white",ec=BORDER,lw=1.1))
    ax2.text(0.08,0.91,"处理逻辑",fontsize=15,color=BLUE_DARK,weight="bold")
    for i,t in enumerate(["全量线路", "系统自动求交", "候选交点", "外协现场核验"]):
        ax2.text(0.12,0.82-i*0.075, f"{i+1}. {t}", fontsize=12.5, color=TEXT)
    ax2.add_patch(FancyBboxPatch((0,0.24),1,0.30,boxstyle="round,pad=0.02,rounding_size=0.04",fc="#EEF5FF",ec="#C8DCF7",lw=1.1))
    ax2.text(0.08,0.48,"审核版结果",fontsize=15,color=BLUE_DARK,weight="bold")
    ax2.text(0.08,0.39,f"候选交点  {len(points):,} 处",fontsize=20,color=RED,weight="bold")
    ax2.text(0.08,0.30,"系统先筛重点，外协精准核验",fontsize=11.5,color=MUTED)
    save(fig, "05-交叉跨越筛查.png")


def _gbif_points(limit=300_000):
    if not GBIF.exists():
        return np.empty((0,2)), 0
    with zipfile.ZipFile(GBIF) as zf:
        names = zf.namelist()
        target = next((n for n in names if n.lower().endswith("occurrence.txt")), None)
        if target is None:
            target = next((n for n in names if n.lower().endswith((".tsv", ".txt", ".csv")) and "metadata" not in n.lower()), None)
        if target is None:
            raise RuntimeError("GBIF archive contains no occurrence table")
        raw = zf.open(target)
        text = (line.decode("utf-8", errors="replace") for line in raw)
        reader = csv.DictReader(text, delimiter="\t")
        pts=[]; total=0
        for row in reader:
            try:
                lon=float(row.get("decimalLongitude") or "nan")
                lat=float(row.get("decimalLatitude") or "nan")
            except ValueError:
                continue
            if not (116.0 <= lon <= 122.5 and 30.3 <= lat <= 35.5):
                continue
            total += 1
            if len(pts) < limit:
                pts.append((lon,lat))
        return np.asarray(pts, dtype=float), total


def _to_demo_xy(points):
    if not len(points): return points
    x = 90 + (points[:,0]-116.0)/(122.5-116.0)*1020
    y = 650 - (points[:,1]-30.3)/(35.5-30.3)*570
    return np.column_stack([x,y])


def fig06():
    fig = new_canvas("提效案例2：鸟类活动重点区域筛查")
    ax = fig.add_axes([0.035, 0.07, 0.72, 0.80], facecolor=BG)
    outline=np.asarray(DEMO["outline"])
    ax.add_patch(Polygon(outline,closed=True,fc=LAND,ec="#9BA7B4",lw=1.4,zorder=0))
    gbif,total=_gbif_points(); xy=_to_demo_xy(gbif)
    if len(xy):
        # density heatmap from real GBIF occurrence coordinates
        hist, xe, ye = np.histogram2d(xy[:,0], xy[:,1], bins=(72,48), range=((70,1130),(70,650)))
        # simple deterministic neighborhood smoothing
        for _ in range(4):
            p=np.pad(hist,1,mode="edge")
            hist=sum(p[dy:dy+hist.shape[0], dx:dx+hist.shape[1]] for dy in range(3) for dx in range(3))/9.0
        vmax=np.percentile(hist[hist>0], 97) if np.any(hist>0) else 1
        ax.imshow(hist.T, extent=[70,1130,650,70], cmap="YlOrRd", alpha=np.clip(hist.T/max(vmax,1),0,0.72), interpolation="bilinear", zorder=1, aspect="auto")
        sample=xy[::max(1,len(xy)//9000)]
        ax.scatter(sample[:,0],sample[:,1],s=3,c=GREEN,alpha=0.24,linewidths=0,zorder=2)
    for route in DEMO["routes"]:
        pts=np.asarray(route["points"])
        ax.plot(pts[:,0],pts[:,1],color=LEVEL_COLORS.get(str(route.get("level")),BLUE),lw=1.05,alpha=0.82,zorder=4)
    ax.set_xlim(35,1165); ax.set_ylim(675,35); ax.set_aspect("equal"); ax.axis("off")
    ax2=fig.add_axes([0.78,0.12,0.18,0.68]); ax2.axis("off")
    ax2.add_patch(FancyBboxPatch((0,0.55),1,0.42,boxstyle="round,pad=0.02,rounding_size=0.04",fc="white",ec=BORDER,lw=1.1))
    ax2.text(0.08,0.89,"数据与方法",fontsize=15,color=BLUE_DARK,weight="bold")
    ax2.text(0.08,0.78,"GBIF 鸟类活动记录",fontsize=12.5,color=TEXT)
    ax2.text(0.08,0.69,"→ 网格密度与平滑热点",fontsize=12.5,color=TEXT)
    ax2.text(0.08,0.60,"→ 与脱敏输电线路叠加",fontsize=12.5,color=TEXT)
    ax2.add_patch(FancyBboxPatch((0,0.19),1,0.27,boxstyle="round,pad=0.02,rounding_size=0.04",fc="#EEF5FF",ec="#C8DCF7",lw=1.1))
    ax2.text(0.08,0.39,"本次读取记录",fontsize=12,color=MUTED)
    ax2.text(0.08,0.29,f"{total:,} 条",fontsize=23,color=BLUE_DARK,weight="bold")
    ax2.text(0.08,0.21,"审核重点：热点表达与线路叠加层级",fontsize=10.5,color=MUTED)
    save(fig, "06-鸟类活动重点区域筛查.png")


def _point_segment_distance(p,a,b):
    p=np.asarray(p,float); a=np.asarray(a,float); b=np.asarray(b,float)
    ab=b-a; den=float(ab@ab)
    if den <= 1e-9: return float(np.linalg.norm(p-a))
    t=max(0,min(1,float((p-a)@ab/den)))
    return float(np.linalg.norm(p-(a+t*ab)))


def fig07():
    fig=new_canvas("提效案例3：集中燃放点周边杆塔筛查")
    ax=fig.add_axes([0.035,0.07,0.72,0.80],facecolor=BG)
    draw_demo_base(ax,alpha=0.72)
    risk=[f for f in DEMO["fireworks"] if f.get("risk")]
    route_nodes=[np.asarray(r["points"],float) for r in DEMO["routes"]]
    hit_nodes=[]
    for f in risk:
        p=np.asarray(f["point"],float)
        ax.add_patch(Circle(tuple(p),52,fc=RED,ec=RED,alpha=0.09,lw=1.2,zorder=3))
        ax.scatter([p[0]],[p[1]],s=80,c=RED,edgecolors="white",linewidths=1.0,zorder=6)
        for nodes in route_nodes:
            d=np.linalg.norm(nodes-p,axis=1)
            for n in nodes[d<=52]: hit_nodes.append(tuple(n))
    if hit_nodes:
        h=np.asarray(sorted(set(hit_nodes)))
        ax.scatter(h[:,0],h[:,1],s=20,c=AMBER,edgecolors="white",linewidths=0.4,zorder=5)
    ax2=fig.add_axes([0.78,0.12,0.18,0.68]); ax2.axis("off")
    ax2.add_patch(FancyBboxPatch((0,0.55),1,0.42,boxstyle="round,pad=0.02,rounding_size=0.04",fc="white",ec=BORDER,lw=1.1))
    ax2.text(0.08,0.89,"筛查逻辑",fontsize=15,color=BLUE_DARK,weight="bold")
    ax2.text(0.08,0.78,"集中燃放点",fontsize=12.5,color=TEXT)
    ax2.text(0.08,0.69,"→ 风险缓冲区",fontsize=12.5,color=TEXT)
    ax2.text(0.08,0.60,"→ 命中线路 / 杆塔",fontsize=12.5,color=TEXT)
    ax2.add_patch(FancyBboxPatch((0,0.19),1,0.27,boxstyle="round,pad=0.02,rounding_size=0.04",fc="#FFF2EC",ec="#F6C8B0",lw=1.1))
    ax2.text(0.08,0.39,"脱敏审核版",fontsize=12,color=MUTED)
    ax2.text(0.08,0.29,f"{len(risk)} 个风险点",fontsize=22,color=RED,weight="bold")
    ax2.text(0.08,0.21,f"命中演示杆塔节点 {len(set(hit_nodes))} 个",fontsize=10.8,color=MUTED)
    save(fig,"07-集中燃放点筛查.png")


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fig02(); fig05(); fig06(); fig07()

if __name__ == "__main__":
    main()
