#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REPORT = DIST / "案例考核报告-从人海作业到数智协同.docx"
SCRIPT = DIST / "答辩逐字稿-从人海作业到数智协同.docx"
HTML = DIST / "课题答辩-从人海作业到数智协同.html"
PDF = DIST / "课题答辩-从人海作业到数智协同.pdf"


def fail(message):
    print("[verify-review] ERROR " + message)
    sys.exit(1)


for path in (REPORT, SCRIPT, HTML, PDF):
    if not path.exists() or path.stat().st_size < 1000:
        fail(f"missing or empty: {path.name}")

if REPORT.stat().st_size > 5 * 1024 * 1024:
    fail(f"report DOCX exceeds 5 MB: {REPORT.stat().st_size / 1024 / 1024:.2f} MB")

with zipfile.ZipFile(REPORT) as archive:
    document_xml = archive.read("word/document.xml").decode("utf-8")
    core_xml = archive.read("docProps/core.xml").decode("utf-8")
    parts = set(archive.namelist())

report_text = "".join(ET.fromstring(document_xml).itertext())
normalized = re.sub(r"\s+", "", report_text)
chinese_count = len(re.findall(r"[\u4e00-\u9fff]", report_text))
if not 6000 <= chinese_count <= 14000:
    fail(f"report narrative size out of review range: {chinese_count} Chinese chars")

required = (
    "摘要",
    "关键词：外协管理；任务筛选；照片查重；人机协同；输电运检",
    "一、背景、问题、现状",
    "二、总体思路：构建“增效+提质”的外协数智管理模式",
    "三、具体做法",
    "四、实施效果",
    "五、推广应用建议",
    "机器给候选，人员下结论",
    "本案例使用Shapely、pHash、CLIP等成熟方法作为技术组件",
    "表1 个人贡献、协同角色与验证依据",
    "表2 交叉跨越前后耗时口径及边界",
    "新增候选",
    "确认漏项",
    "图8 真实复核案例：同图修改水印日期与高相似但不同照片",
    "相似候选不等于履职问题",
    "111,519张",
    "5,472对",
    "4,630对",
    "确认重复348对",
    "确认不同4,282对",
    "842对待复核",
    "运检工作质量远程督查",
    "形成通报",
    "整改闭环完成",
    "接数据、配规则、走闭环",
    "以下内容属于建议性试点方案，不作为本案例已实施成果",
    "表5 建议性试点的最小配置与验收要点",
    "附录 技术机制与运行记录核验项",
    "表A4 月度运行记录核验项",
    "理论77.5万亿对只代表1245万张照片在无约束情况下的组合量级",
)
for phrase in required:
    if phrase not in report_text:
        fail(f"report missing required review wording: {phrase}")

for forbidden in (
    "相关核心算法和数字化工具均由我自主设计、开发和验证",
    "路线精准推送",
    "规划巡视路线",
    "持续优化规则",
    "即可复用现有方法",
    "即可在现有业务数据和管理流程上复用这套方法",
):
    if forbidden in report_text:
        fail(f"report still contains over-claimed or superseded wording: {forbidden}")

primary = [m.group(1) for m in re.finditer(r"([一二三四五])、(?:背景、问题、现状|总体思路|具体做法|实施效果|推广应用建议)", report_text)]
if primary != ["一", "二", "三", "四", "五"]:
    fail(f"primary five-part structure mismatch: {primary}")

main_figures = [int(n) for n in re.findall(r"(?<!附)图(\d+) ", report_text)]
if main_figures != list(range(1, 11)):
    fail(f"main figure numbering mismatch: {main_figures}")

main_tables = [int(n) for n in re.findall(r"表([1-5]) ", report_text)]
if main_tables != [1, 2, 3, 4, 5]:
    fail(f"main table numbering mismatch: {main_tables}")
for appendix_table in ("表A1", "表A2", "表A3", "表A4"):
    if appendix_table not in report_text:
        fail(f"appendix table missing: {appendix_table}")

if document_xml.count("<m:oMath>") != 4:
    fail("technical appendix must keep exactly four editable equations")
for equation_ref in ("式（1）", "式（2）", "式（3）", "式（4）"):
    if equation_ref not in report_text:
        fail(f"missing appendix equation reference: {equation_ref}")

if len(re.findall(r"<w:tbl(?:\s|>)", document_xml)) != 9:
    fail("review report should contain exactly 9 tables: 5 main + 4 appendix")
if len(re.findall(r"<w:drawing>", document_xml)) != 10:
    fail("review report should contain exactly 10 main figures")
if len(re.findall(r'w:type="page"', document_xml)) != 0:
    fail("report must use natural pagination")

if any(value in core_xml for value in ("Administrator", "Evolution")):
    fail("report metadata still contains editor identity")
if any(name.startswith("word/comments") for name in parts):
    fail("report must not contain comments")
if re.search(r"<w:(?:ins|del)(?:\s|>)", document_xml):
    fail("report must not contain tracked changes")

# Verify the report actually renders. Page count is deliberately flexible because
# formal submission requirements, not an obsolete 24-26 page gate, control length.
renderer_root = Path.home() / ".codex/plugins/cache/openai-primary-runtime/documents"
renderer_candidates = sorted(renderer_root.glob("*/skills/documents/render_docx.py"), reverse=True)
if not renderer_candidates:
    fail("DOCX renderer not found")
renderer = renderer_candidates[0]
render_python = Path(os.environ.get("PYTHON", Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"))
if not render_python.exists():
    render_python = Path(sys.executable)
with tempfile.TemporaryDirectory(prefix="case-report-review-") as tmp:
    out = Path(tmp) / "report"
    render_env = os.environ.copy()
    fontconfig_file = Path("/opt/homebrew/etc/fonts/fonts.conf")
    if fontconfig_file.exists():
        # The headless LibreOffice profile otherwise misses user-installed CJK fonts
        # and can produce a false-success PDF whose text layer exists but glyphs are blank.
        render_env["FONTCONFIG_FILE"] = str(fontconfig_file)
    subprocess.run(
        [str(render_python), str(renderer), str(REPORT), "--output_dir", str(out), "--emit_pdf"],
        cwd=ROOT,
        env=render_env,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    pages = len(list(out.glob("page-*.png")))
    if not 16 <= pages <= 30:
        fail(f"rendered report page count is implausible: {pages}")
    rendered_pdf = next(out.glob("*.pdf"), None)
    if rendered_pdf is None:
        fail("renderer did not emit report PDF")
    pdf_fonts = subprocess.run(
        ["pdffonts", str(rendered_pdf)], check=True, text=True, capture_output=True
    ).stdout
    if not re.search(r"ArialUnicode|Songti|Song|Hiragino|Fang|SimSun|Heiti|Noto.*CJK", pdf_fonts, re.I):
        fail("rendered report PDF contains no detectable CJK-capable font; glyph rendering may be blank")
    page_pngs = sorted(
        out.glob("page-*.png"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))
    )
    for page_index, page_png in enumerate(page_pngs, 1):
        image = Image.open(page_png).convert("RGB")
        bbox = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
        if bbox is None:
            fail(f"rendered report page {page_index} is visually blank")
        left, top, right, bottom = bbox
        margins = (left, top, image.width - right, image.height - bottom)
        if min(margins) < 70:
            fail(f"rendered report page {page_index} content approaches page edge: margins={margins}")
    layout_text = subprocess.run(
        ["pdftotext", "-layout", str(rendered_pdf), "-"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    if "摘要" not in layout_text or "附录" not in layout_text:
        fail("rendered report text layer misses abstract or appendix")
    for page_index, page_text in enumerate(layout_text.split("\f"), 1):
        first_line = next((line.strip() for line in page_text.splitlines() if line.strip()), "")
        if first_line.startswith("注："):
            fail(f"page {page_index} starts with orphaned table note")

# Keep the existing defense artifacts smoke-tested while this branch focuses on the report.
html = HTML.read_text("utf-8")
if len(re.findall(r'<section class="slide(?:\s|\")', html)) != 13:
    fail("deck slide count is not 13")
pdf_info = subprocess.run(["pdfinfo", str(PDF)], check=True, text=True, capture_output=True).stdout
if not re.search(r"^Pages:\s+13$", pdf_info, re.M):
    fail("defense PDF page count is not 13")

env = os.environ.copy()
default_node_modules = str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")
node_modules = os.environ.get("NODE_MODULES", default_node_modules)
env["NODE_MODULES"] = node_modules
env["NODE_PATH"] = node_modules
node_bin = os.environ.get("NODE", str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"))
subprocess.run([node_bin, str(ROOT / "scripts/smoke_deck.mjs")], cwd=ROOT, env=env, check=True)
subprocess.run([sys.executable, str(ROOT / "scripts/privacy_check.py")], cwd=ROOT, check=True)
print(f"[verify-review] passed: event-first report, {chinese_count} Chinese chars, five-part structure, appendix, render QA")
