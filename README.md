# 从人海作业到数智协同

输电运检外协队伍增效提质个人案例的可编译工程。所有正文来自 `content/case.json` 与生成代码，Word、HTML、PDF均为构建产物，禁止手工修改最终文件。

## 构建

```bash
make all CASE_ID="案例编号：XXXX"
make privacy-check
```

输出位于 `dist/`：

- 案例考核报告（DOCX，固定18页）
- 课题答辩（自包含交互HTML + 15页PDF）
- 答辩逐字稿（DOCX）

## 数据安全

原始杆塔数据库只在正式空间图/数据构建时以只读方式访问。仓库只保存不可逆的脱敏演示数据，不保存真实经纬度、线路名、杆号、组织机构或原始业务记录。

## 逻辑基准

所有报告、PPT、逐字稿和配图必须遵循 `docs/CASE-LOGIC-BASELINE.md`。主线固定为：**外协队伍管理 → 工作量大/质量难保证 → 增效/提质 → 数智协同管理**。

## 配图数据源基准

空间业务图必须遵循 `docs/FIGURE-SOURCE-POLICY.md`。

**`data/demo.json` 禁止用于正式报告的省域线路图、交叉跨越图、防鸟图和集中燃放点图。**

正式空间图统一走既有矢量链：

- 省域 SVG / PNG / EMF：`scripts/build_base_map.py`
- 交叉跨越、集中燃放点：`scripts/build_report_spatial_figures.py`
- GBIF 鸟类活动 + 正式输电线路叠加：`scripts/build_gbif_bird_figure.py`

如果 `POLE_DB`、铁路 PBF 或正式上游结果缺失，构建必须失败或跳过，不能自动退化为仿真地图。

## 报告10张核心图

管理图由代码直接生成：

1. `01-外协管理两大痛点.png`
2. `03-增效提质总体模型.png`
3. `04-外协任务数字化筛选流程.png`
4. `08-照片质量督查流程与示例.png`
5. `09-告警工单照片全量查重成果.png`
6. `10-外协管理前后对比.png`

正式空间图：

7. `02-省域线路杆塔任务规模.png`
8. `05-交叉跨越自动筛查.png`
9. `06-鸟类活动重点区域筛查.png`
10. `07-集中燃放点周边杆塔筛查.png`

统一检查入口：

```bash
make case-figures
```

注意：`make case-figures` 要求正式空间图源已经由上述生产脚本生成，不存在 demo fallback。

## 内容维护

- 修改事实、标题、统计值：`content/case.json`
- 修改报告结构：`scripts/build_report.py`
- 修改逐字稿：`scripts/build_script.py`
- 修改答辩页面：`src/presentation.html`
- 修改管理逻辑图：`scripts/build_management_figures.py`
- 修改正式空间图：`scripts/build_base_map.py` / `scripts/build_report_spatial_figures.py` / `scripts/build_gbif_bird_figure.py`
