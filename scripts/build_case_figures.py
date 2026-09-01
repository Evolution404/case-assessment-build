#!/usr/bin/env python3
"""Normalize the ten approved report figures into one stable output set.

Source policy:
- management figures: scripts/build_management_figures.py
- province base map: scripts/build_base_map.py
- crossing/fireworks: scripts/build_report_spatial_figures.py
- bird map: scripts/build_gbif_bird_figure.py

Spatial figures are PRODUCTION-ONLY. There is deliberately no demo.json
fallback. If POLE_DB / railway PBF or upstream production outputs are missing,
this script must fail instead of fabricating a visually degraded review map.
See docs/FIGURE-SOURCE-POLICY.md.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "dist" / "figures"

SPATIAL_ALIASES = {
    "江苏省域输电线路电压等级分布": "02-省域线路杆塔任务规模",
    "铁路交叉跨越识别": "05-交叉跨越自动筛查",
    "集中燃放点缓冲筛查": "07-集中燃放点周边杆塔筛查",
}
SPATIAL_FORMATS = ("svg", "png", "emf")

FINAL_SPATIAL_STEMS = (*SPATIAL_ALIASES.values(), "06-鸟类活动重点区域筛查")
FINAL_SPATIAL_FILES = tuple(
    f"{stem}.{ext}"
    for stem in FINAL_SPATIAL_STEMS
    for ext in SPATIAL_FORMATS
)

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

    for source_stem, target_stem in SPATIAL_ALIASES.items():
        sources = [FIG / f"{source_stem}.{ext}" for ext in SPATIAL_FORMATS]
        targets = [FIG / f"{target_stem}.{ext}" for ext in SPATIAL_FORMATS]
        if all(path.exists() for path in sources):
            for src, dst in zip(sources, targets):
                shutil.copy2(src, dst)
                print(f"[case-figure] {dst.name} <- {src.name}")
        elif all(path.exists() for path in targets):
            print(f"[case-figure] reuse committed production deliverables: {target_stem}")
        else:
            missing = [path.name for path in sources if not path.exists()]
            raise FileNotFoundError(
                "正式空间图源缺失，且无已提交正式成果可复用；禁止使用 demo.json fallback："
                + "、".join(missing)
            )

    missing_spatial = [name for name in FINAL_SPATIAL_FILES if not (FIG / name).exists()]
    if missing_spatial:
        raise FileNotFoundError("正式空间图三格式未生成完整：" + "、".join(missing_spatial))

    missing = [name for name in EXPECTED if not (FIG / name).exists()]
    if missing:
        raise FileNotFoundError("十张报告图未生成完整：" + "、".join(missing))
    print("[case-figure] 10/10 production figures ready")


if __name__ == "__main__":
    main()
