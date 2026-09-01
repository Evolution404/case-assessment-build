#!/usr/bin/env python3
import os,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
REPORT=DIST/'案例考核报告-从人海作业到数智协同.docx';SCRIPT=DIST/'答辩逐字稿-从人海作业到数智协同.docx';HTML=DIST/'课题答辩-从人海作业到数智协同.html';PDF=DIST/'课题答辩-从人海作业到数智协同.pdf'
def fail(msg):print('[verify] ERROR '+msg);sys.exit(1)
for p in (REPORT,SCRIPT,HTML,PDF):
 if not p.exists() or p.stat().st_size<1000:fail(f'missing or empty: {p.name}')
html=HTML.read_text('utf-8')
if len(re.findall(r'<section class="slide(?:\s|\")',html))!=15:fail('HTML slide count is not 15')
if re.search(r'__[A-Z0-9_]+__',html):fail('HTML contains unresolved placeholder')
info=subprocess.run(['pdfinfo',str(PDF)],check=True,text=True,capture_output=True).stdout
if not re.search(r'^Pages:\s+15$',info,re.M):fail('PDF page count is not 15')
pdf_text=subprocess.run(['pdftotext',str(PDF),'-'],check=True,text=True,capture_output=True).stdout
if len(pdf_text)<1500 or '电力信息公司没搞定的千万级照片查重' not in re.sub(r'\s+','',pdf_text):fail('PDF text layer incomplete')
def docx_xml(p):
 with zipfile.ZipFile(p) as z:return z.read('word/document.xml').decode('utf-8')
rx=docx_xml(REPORT);sx=docx_xml(SCRIPT)
if len(re.findall(r'[\u4e00-\u9fff]',rx))<3000:fail('report body text incomplete')
for forbidden in ('质量督查','本次质量督查','杆塔台账','9217条线路','2026-02-28','2026-06-29'):
 if forbidden in rx:fail(f'report contains obsolete wording: {forbidden}')
for required in ('40.1万基输电杆塔','9200余条输电线路','全省220kV及以上线路连续三个月','核心算法与程序均由我自主设计、开发和验证','此前由电力信息公司提供的既有照片查重能力主要覆盖少量特高压巡视照片','形成每月1245万张巡视照片的规模化全量筛查能力','相关成果已在省公司开展试点应用','向其他地市公司复制推广'):
 if required not in rx:fail(f'report missing required wording: {required}')
report_page_starts=len(re.findall(r'w:type="page"',rx))+len(re.findall(r'w:pageBreakBefore',rx))
if report_page_starts!=0:fail('report must use template-style natural pagination without explicit page breaks')
if len(re.findall(r'w:type="page"',sx))!=14:fail('script explicit pagination is not 15 pages')
renderer=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/render_docx.py'
if not renderer.exists():fail('DOCX renderer not found')
render_python=Path(os.environ.get('PYTHON',Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'))
if not render_python.exists():render_python=Path(sys.executable)
render_env=os.environ.copy();render_env['FONTCONFIG_FILE']='/opt/homebrew/etc/fonts/fonts.conf'
with tempfile.TemporaryDirectory(prefix='case-docx-verify-') as tmp:
 for source,name,expected in ((REPORT,'report',None),(SCRIPT,'script',15)):
  out=Path(tmp)/name;subprocess.run([str(render_python),str(renderer),str(source),'--output_dir',str(out)],cwd=ROOT,env=render_env,check=True,stdout=subprocess.DEVNULL)
  pages=len(list(out.glob('page-*.png')))
  if name=='report':
   if not 10<=pages<=18:fail(f'report rendered to {pages} pages; template-style report should remain within 10-18 pages')
  elif pages!=expected:fail(f'{name} rendered to {pages} pages, expected {expected}')
env=os.environ.copy();env['NODE_PATH']=os.environ.get('NODE_MODULES','');subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/smoke_deck.mjs')],cwd=ROOT,env=env,check=True);subprocess.run([sys.executable,str(ROOT/'scripts/privacy_check.py')],cwd=ROOT,check=True)
print('[verify] passed: report uses template-style natural pagination, deck 15 pages, script 15 pages, text/privacy/interaction checks OK')
