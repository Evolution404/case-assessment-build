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
if len(re.findall(r'w:type="page"',rx))!=17:fail('report explicit pagination is not 18 pages')
if len(re.findall(r'w:type="page"',sx))!=14:fail('script explicit pagination is not 15 pages')
renderer=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/render_docx.py'
if not renderer.exists():fail('DOCX renderer not found')
render_env=os.environ.copy();render_env['FONTCONFIG_FILE']='/opt/homebrew/etc/fonts/fonts.conf'
with tempfile.TemporaryDirectory(prefix='case-docx-verify-') as tmp:
 for source,name,expected in ((REPORT,'report',18),(SCRIPT,'script',15)):
  out=Path(tmp)/name;subprocess.run([sys.executable,str(renderer),str(source),'--output_dir',str(out)],cwd=ROOT,env=render_env,check=True,stdout=subprocess.DEVNULL)
  pages=len(list(out.glob('page-*.png')))
  if pages!=expected:fail(f'{name} rendered to {pages} pages, expected {expected}')
env=os.environ.copy();env['NODE_PATH']=os.environ.get('NODE_MODULES','');subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/smoke_deck.mjs')],cwd=ROOT,env=env,check=True);subprocess.run([sys.executable,str(ROOT/'scripts/privacy_check.py')],cwd=ROOT,check=True)
print('[verify] passed: report 18 pages, deck 15 pages, script 15 pages, text/privacy/interaction checks OK')
