# 从人海作业到数智协同

输电运检外协队伍提效增质个人案例的可编译工程。所有正文来自 `content/case.json` 与生成代码，Word、HTML、PDF均为构建产物，禁止手工修改最终文件。

## 构建

```bash
make all CASE_ID="案例编号：XXXX"
make privacy-check
```

输出位于 `dist/`：

- 案例考核报告（DOCX，固定18页）
- 课题答辩（自包含交互HTML + 15页PDF）
- 答辩逐字稿（DOCX）

## 报告配图

报告配图不手工绘制，统一由代码生成。审核版十张图使用固定编号和文件名：

```bash
make case-figures
```

生成到 `dist/figures/`：

1. `01-外协管理两大痛点.png`
2. `02-省域线路杆塔任务规模.png`
3. `03-提效增质总体模型.png`
4. `04-外协任务数字化筛选流程.png`
5. `05-交叉跨越自动筛查.png`
6. `06-鸟类活动重点区域筛查.png`
7. `07-集中燃放点周边杆塔筛查.png`
8. `08-照片质量督查流程与示例.png`
9. `09-告警工单照片全量查重成果.png`
10. `10-外协管理前后对比.png`

其中：

- 图1/3/4/8/9/10：`scripts/build_management_figures.py`，使用 Matplotlib/PIL 程序化绘制；
- 图2：复用 `scripts/build_base_map.py` 的省域输电网络；
- 图5/7：复用 `scripts/build_report_spatial_figures.py` 的交叉跨越、集中燃放点空间分析；
- 图6：`scripts/build_gbif_bird_figure.py` 直接读取 `data/birds/gbif-occurrence-0046920-260806074905277.zip`，生成江苏省域鸟类活动热点并与输电线路叠加；
- `scripts/build_case_figures.py` 负责统一十张图的最终文件名并检查是否 10/10 齐全。

当前 `make case-figures` 仅用于生成审核版配图；报告正文仍可独立构建，待图片审核通过后再切换为这套固定十图。

## 数据安全

原始杆塔数据库只在 `make data` 时以只读方式访问。仓库只保存不可逆的脱敏演示数据，不保存真实经纬度、线路名、杆号、组织机构或原始业务记录。

GBIF 鸟类活动数据仅用于生成省域聚合热点和线路空间关系，报告图不输出原始观察点的精确坐标清单。

## 逻辑基准

所有报告、PPT、逐字稿和配图必须遵循 `docs/CASE-LOGIC-BASELINE.md`。主线固定为：**外协队伍管理 → 工作量大/质量难保证 → 提效/增质 → 数智协同管理**。

## 内容维护

- 修改事实、标题、统计值：`content/case.json`
- 修改报告结构：`scripts/build_report.py`
- 修改逐字稿：`scripts/build_script.py`
- 修改答辩页面：`src/presentation.html`
- 修改旧版效果图：`src/visuals.html`
- 修改审核版管理逻辑图：`scripts/build_management_figures.py`
- 修改 GBIF 鸟类活动图：`scripts/build_gbif_bird_figure.py`
