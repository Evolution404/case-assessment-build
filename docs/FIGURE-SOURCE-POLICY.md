# 报告配图数据源基准

> 本文件用于锁定报告配图的数据来源和生成链。后续任何 AI、脚本或 CI 都不得为了“凑齐图片”降低地图数据质量。

## 1. 总原则

报告中的空间业务图必须使用已经建立的正式省域矢量地图生成链。

**禁止使用 `data/demo.json` 生成或替代正式报告中的省域线路图、交叉跨越图、防鸟图、集中燃放点图。**

`data/demo.json` 仅用于隐私安全的交互演示/原型验证，不能作为报告地图底图。

如果正式空间数据源暂不可用，应明确报错或跳过生成，**不得自动退化为仿真地图**。

## 2. 正式空间图生成链

### 图2 省域线路 / 杆塔任务规模

正式生成器：`scripts/build_base_map.py`

数据源：

- 只读 `POLE_DB` 杆塔数据库；
- `data/jiangsu_outline.geojson`；
- `data/jiangsu_districts.geojson`。

正式输出：

- `dist/figures/江苏省域输电线路电压等级分布.svg`
- `dist/figures/江苏省域输电线路电压等级分布.png`
- `dist/figures/江苏省域输电线路电压等级分布.emf`

该 SVG/PNG 的线路按真实杆塔拓扑重建、按电压等级配色，是后续省域专题图的视觉基准。

### 图5 交叉跨越自动筛查

正式生成器：`scripts/build_report_spatial_figures.py`

数据源：

- 正式 `POLE_DB`；
- 正式铁路 PBF（`JIANGSU_RAIL_PBF`）；
- 江苏省界/地市界。

必须沿用 `map_style.py` 和省域 SVG 的线路层级、颜色、线宽、行政边界风格。

不得用仿真铁路折线、随机线路或 `demo.json` 交点代替。

### 图6 鸟类活动重点区域筛查

正式生成器：`scripts/build_gbif_bird_figure.py`

数据源：

- `data/birds/gbif-occurrence-0046920-260806074905277.zip`；
- 正式 `POLE_DB` 线路网络；
- 江苏省界/地市界。

GBIF 数据用于生成鸟类活动热点；输电线路必须复用正式省域线路生成逻辑，不得叠加 `demo.json` 的脱敏仿真线路。

### 图7 集中燃放点周边杆塔筛查

正式生成器：`scripts/build_report_spatial_figures.py`

数据源：

- 正式 `POLE_DB`；
- `data/fireworks_public_anonymized.json`：已核验公开燃放点的街镇级近似定位；
- 江苏省界/地市界。

燃放点公开来源：南京市公安局《南京警方发布：春节期间烟花爆竹禁限放政策》（2026-02-13）。旧正式成果已核验分布为六合4处、栖霞4处、江宁6处、溧水4处、高淳2处，共20处；坐标仅按公开街镇和官方示意图近似定位，用于500米空间筛查方法展示，不代表精确燃放位置。

必须复用正式省域线路视觉和真实空间距离逻辑。`data/fireworks_public_anonymized.json` 缺失或为空时必须硬失败，禁止随机生成、模拟或 fallback。

## 3. 管理逻辑图

图1、图3、图4、图8、图9、图10由 `scripts/build_management_figures.py` 生成，统计值统一从 `content/case.json` 读取。

这些图可以在 GitHub Actions 中独立生成，因为不依赖本地空间数据库。

## 4. CI / 审核规则

1. CI 中没有 `POLE_DB` / 铁路 PBF 时，只允许生成管理逻辑图；
2. 正式空间图源不可用时必须失败或跳过，不得 fallback 到 `demo.json`；
3. 所有空间图优先保留 SVG 矢量版本，并同时输出高分辨率 PNG；
4. 新的空间图应首先对照 `scripts/build_base_map.py` 输出的省域 SVG 审核视觉一致性；
5. 报告正式替换图片前，必须人工审核空间图的线路拓扑、行政轮廓、图例、标记密度和数据口径。
