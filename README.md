# 从人海作业到数智协同

输电运检外协队伍提质增效个人案例的可编译工程。所有正文来自 `content/case.json` 与生成代码，Word、HTML、PDF均为构建产物。

## 构建

```bash
make all CASE_ID="案例编号：XXXX"
```

输出位于 `dist/`：

- 案例考核报告（DOCX，目标15—20页）
- 课题答辩（自包含交互HTML + 15页PDF）
- 答辩逐字稿（DOCX）

## 数据安全

原始杆塔数据库只在 `make data` 时以只读方式访问。仓库只保存不可逆的脱敏演示数据，不保存真实经纬度、线路名、杆号、组织机构或原始业务记录。

## 内容维护

- 修改事实、标题、统计值：`content/case.json`
- 修改报告结构：`scripts/build_report.py`
- 修改逐字稿：`scripts/build_script.py`
- 修改答辩页面：`src/presentation.template.html`
- 修改效果图：`src/visuals.html`

