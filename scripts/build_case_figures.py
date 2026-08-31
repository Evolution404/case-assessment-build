#!/usr/bin/env python3
"""Normalize all ten approved report figures into one stable output set.

Prerequisites are produced by Makefile targets:
- management figures: build_management_figures.py
- province base map: build_base_map.py
- crossing/fireworks: build_report_spatial_figures.py
- GBIF bird map: build_gbif_bird_figure.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "dist" / "figures"

ALIASES = {
    "江苏省域输电线路电压等级分布.png": "02-省域线路杆塔任务规模.png",
    "铁路交叉跨越识别.png": "05-交叉跨越自动筛查.png",
    "集中燃放点缓冲筛查.png": "07-集中燃放点周边杆塔筛查.png",
}

EXPECTED = [
    "01-外协管理两大痛点.png",
    "02-省域线路杆塔任务规模.png",
    "03-提效增质总体模型.png",
    "04-外协任务数字化筛选流程.png",
    "05-交叉跨越自动筛查.png",
    "06-鸟类活动重点区域筛查.png",
    "07-集中燃放点周边杆塔筛查.png",
    "08-照片质量督查流程与示例.png",
    "09-告警工单照片全量查重成果.png",
    "10-外协管理前后对比.png",
]


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    for source, target in ALIASES.items():
        src = FIG / source
        dst = FIG / target
        if not src.exists():
            raise FileNotFoundError(f"缺少上游专题图：{src}")
        shutil.copy2(src, dst)
        print(f"[case-figure] {dst.name} <- {src.name}")

    missing = [name for name in EXPECTED if not (FIG / name).exists()]
    if missing:
        raise FileNotFoundError("十张报告图未生成完整：" + "、".join(missing))
    print("[case-figure] 10/10 figures ready")


if __name__ == "__main__":
    main()
