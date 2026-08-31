# 从人海作业到数智协同

输电运检外协队伍提质增效个人案例的可编译工程。所有正文来自 `content/case.json` 与生成代码，Word、HTML、PDF均为构建产物，禁止手工修改最终文件。

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

原始杆塔数据库只在 `make data` 时以只读方式访问。仓库只保存不可逆的脱敏演示数据，不保存真实经纬度、线路名、杆号、组织机构或原始业务记录。

## 逻辑基准

所有报告、PPT、逐字稿和配图必须遵循 `docs/CASE-LOGIC-BASELINE.md`。主线固定为：**外协队伍管理 → 工作量大/质量难保证 → 提效/增质 → 数智协同管理**。

## 内容维护

- 修改事实、标题、统计值：`content/case.json`
- 修改报告结构：`scripts/build_report.py`
- 修改逐字稿：`scripts/build_script.py`
- 修改答辩页面：`src/presentation.html`
- 修改效果图：`src/visuals.html`
