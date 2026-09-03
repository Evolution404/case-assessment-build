#!/usr/bin/env python3
import os,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
REPORT=DIST/'案例考核报告-从人海作业到数智协同.docx';SCRIPT=DIST/'答辩逐字稿-从人海作业到数智协同.docx';HTML=DIST/'课题答辩-从人海作业到数智协同.html';PDF=DIST/'课题答辩-从人海作业到数智协同.pdf'
def fail(msg):print('[verify] ERROR '+msg);sys.exit(1)
for p in (REPORT,SCRIPT,HTML,PDF):
 if not p.exists() or p.stat().st_size<1000:fail(f'missing or empty: {p.name}')
if REPORT.stat().st_size>5*1024*1024:fail(f'report DOCX exceeds 5 MB size budget: {REPORT.stat().st_size/1024/1024:.2f} MB')
html=HTML.read_text('utf-8')
if len(re.findall(r'<section class="slide(?:\s|\")',html))!=12:fail('HTML slide count is not 12')
if re.search(r'__[A-Z0-9_]+__',html):fail('HTML contains unresolved placeholder')
info=subprocess.run(['pdfinfo',str(PDF)],check=True,text=True,capture_output=True).stdout
if not re.search(r'^Pages:\s+12$',info,re.M):fail('PDF page count is not 12')
pdf_text=subprocess.run(['pdftotext',str(PDF),'-'],check=True,text=True,capture_output=True).stdout
if len(pdf_text)<1500 or '电力信息公司既有能力' not in re.sub(r'\s+','',pdf_text):fail('PDF text layer incomplete')
def docx_xml(p):
 with zipfile.ZipFile(p) as z:return z.read('word/document.xml').decode('utf-8')
def docx_part(p,name):
 with zipfile.ZipFile(p) as z:return z.read(name).decode('utf-8')
def docx_parts(p):
 with zipfile.ZipFile(p) as z:return set(z.namelist())
rx=docx_xml(REPORT);sx=docx_xml(SCRIPT);core_xml=docx_part(REPORT,'docProps/core.xml');report_parts=docx_parts(REPORT)
report_text=''.join(ET.fromstring(rx).itertext())
script_text=''.join(ET.fromstring(sx).itertext())
slide_blocks=re.findall(r'<section class="slide(?:\s|\")[\s\S]*?</section>',html)
slide_text='。'.join(re.sub(r'<[^>]+>',' ',block) for block in slide_blocks)
defense_text=slide_text+'\n'+script_text+'\n'+pdf_text
normalized_defense=re.sub(r'\s+','',defense_text)
decorative_english=(
 'PERSONAL CASE ASSESSMENT','MANAGEMENT PRESSURE','MY JUDGEMENT','ONE OPERATING LOOP',
 'EFFICIENCY IN PRACTICE','MEASURED IMPACT','QUALITY EVIDENCE','FILTERING & RESPONSIBILITY',
 'PERSONAL BREAKTHROUGH','EXISTING CAPABILITY','PROVINCIAL OUTCOME','REPLICATION','CONCLUSION',
 'DATA / RULE','EVIDENCE 01','EVIDENCE 02','EVIDENCE 03','RECALL','REVIEW','DECIDE',
 'PHOTO / DUPLICATE REVIEW','SPEAKER VIEW','NEXT /','TASK /','RESPONSIBILITY /',
)
for phrase in decorative_english:
 pattern=r'(?<![A-Za-z])'+re.escape(phrase)+r'(?![A-Za-z])'
 if any(re.search(pattern,text,re.I) for text in (slide_text,script_text,pdf_text)):
  fail(f'defense artifacts contain decorative English: {phrase}')
for match in re.finditer(r'\b[A-Za-z]{2,}(?:[ \t/&-]+[A-Za-z]{2,})+\b',slide_text):
 fail(f'deck visible text contains unapproved English phrase: {match.group(0)}')
for obsolete in ('287对','287对认定','5.2%','候选命中率','500千伏特殊通道','较大运检质量问题'):
 if obsolete in normalized_defense:fail(f'defense artifacts contain obsolete or out-of-scope wording: {obsolete}')
for required in ('40.1万','9200余','111,519','5,472','4,630','348','4,282','842','7.52%','1245万','77.5万亿','55,411','电力信息公司既有能力','接数据','配规则','走闭环'):
 if required not in normalized_defense:fail(f'defense artifacts missing required fact: {required}')
if len(re.findall(r'[\u4e00-\u9fff]',report_text))<15000:fail('report body text incomplete or under-expanded for technical-paper version')
ai_contrast_patterns=(
 ('negative contrast ...而是',r'(?:并不是|不是|并非|已不再是|不再是|没有|并没有|不再|并不)[^。！？；\n]{0,120}[，,]?\s*而是'),
 ('negative contrast ...而在于',r'(?:并不是|不是|并非|已不再是|不再是|不在于|并不在于)[^。！？；\n]{0,120}[，,]?\s*而在于'),
)
def assert_no_ai_contrast(name,text):
 normalized=re.sub(r'\s+',' ',text)
 hits=[]
 for label,pattern in ai_contrast_patterns:
  for m in re.finditer(pattern,normalized):hits.append(f'{label}: {m.group(0)}')
 if hits:fail(f'{name} contains AI-style negative contrast wording: '+' | '.join(hits))
for name,text in (('report',report_text),('speaker script',script_text),('deck HTML',slide_text),('deck PDF',pdf_text)):
 assert_no_ai_contrast(name,text)
for forbidden in ('质量督查','本次质量督查','杆塔台账','9217条线路','2026-02-28','2026-06-29','本人','个疑似相似候选','个候选，并已人工确认','人工投入无法支撑全量计算','1.创新一：','2.双阶段算法：','3.创新二：','4.千万级工程化处理：','点到线段的最短距离','相同或相邻空间单元','计算坐标统一','log(1+n)','而不是简单比较两个清单数量','包围盒预筛','pHash距离'):
 if forbidden in report_text:fail(f'report contains obsolete or inaccurate wording: {forbidden}')
if re.search(r'(?:图|表)\d+\u3000',report_text):fail('report captions still use ideographic-space separator; use normal spaces for stable PDF text extraction')
if any(v in core_xml for v in ('Administrator','Evolution')):fail('report core metadata still contains template/editor identity')
if any(name.startswith('word/comments') for name in report_parts):fail('report must not contain reviewer comments in final review artifact')
if re.search(r'<w:(?:ins|del)(?:\s|>)',rx):fail('report must not contain tracked changes')
for required in ('40.1万基输电杆塔','9200余条输电线路','全省220kV及以上线路连续三个月','相关核心算法和程序均由我自主设计、开发和验证','此前由电力信息公司提供的既有照片查重能力主要覆盖少量特高压巡视照片','目前能够按月处理约1245万张巡视照片','向其他地市公司推广','传统人工方式难以支撑全量管理','已经成为输电运检专业必须解决的管理问题','面向省域输电运检管理','5,472对疑似相似照片','确认重复348对','约62.18亿对','7.52%','1.告警工单照片查重：从零建立全量筛查方法','2.照片查重：pHash先筛，CLIP再比','4.千万级处理：让1245万张照片稳定跑完','管理层面，把外协管理归纳为“增效管任务、提质管履职”两条主线','方法层面，把空间关系、距离条件和历史照片相似关系转成程序可执行的筛选规则','工程层面，把原有少量特高压照片筛查扩展到全电压等级','两条主线、一个机制','告警工单反馈照片查重和巡视照片查重均已在省公司层面开展试点','照片重复类问题19项','告警工单反馈照片重复11项','人工巡视照片重复8项','500千伏特殊通道人工巡视照片重复问题被定性为较大运检质量问题','这一案例成为照片查重进入实际管理的典型节点','进入省公司生产管控中心实际管理通报','接数据、配规则、走闭环','6438个杆塔坐标','249条线路','既有资料中记录了241处铁路跨越结果','程序只负责把疑似照片对找出来','约77.5万亿对','推广时不依赖新增现场硬件','燃放点—杆塔','ln(1+n)','连续执行7次3×3邻域均值平滑','70%、84%、94%分位点','229,561条有效记录','170×210经纬度栅格','pHash汉明距离＜10且CLIP相似度＞0.80','空间网格索引预筛','0.025°经纬度网格'):
 if required not in rx:fail(f'report missing required wording: {required}')
for required_formula_ref in ('式（1）','式（2）','式（3）','式（4）'):
 if required_formula_ref not in report_text:fail(f'report missing sequential equation reference: {required_formula_ref}')
if 'n_grid' in report_text:fail('report equation still exposes raw underscore notation; use native math subscripts')
if rx.count('<m:oMath>')!=4:fail('report must contain exactly four native editable OMML equations')
for required_math_tag in ('<m:sSub>','<m:sSubSup>','<m:nary>','<m:f>'):
 if required_math_tag not in rx:fail(f'report native equations missing required OMML structure: {required_math_tag}')
math_run_count=rx.count('<m:r>');upright_math_count=rx.count('<m:nor')
if math_run_count==0 or upright_math_count!=math_run_count:fail('all report equation runs must use upright OMML normal-text math style; italic-variable regression detected')
if 'Smooth7' in report_text:fail('report still exposes the old flattened bird-surface equation notation')
if rx.count('w:outlineLvl')<20:fail('report headings missing Word outline levels for navigation')
if len(re.findall(r'<w:tbl(?:\s|>)',rx))!=12:fail('report should contain exactly 12 academic tables after traceability-table consolidation; equation lines must not regress to helper tables')
if rx.count('w:tblHeader')!=12:fail('every academic table must repeat its header row across page breaks')
if rx.count('w:cantSplit')<50:fail('academic table rows must prevent row-level page splitting')
if len(re.findall(r'<w:drawing>',rx))!=10:fail('report should contain exactly 10 approved figures')
report_page_starts=len(re.findall(r'w:type="page"',rx))+len(re.findall(r'w:pageBreakBefore',rx))
if report_page_starts!=0:fail('report must use template-style natural pagination without explicit page breaks')
if len(re.findall(r'w:type="page"',sx))!=11:fail('script explicit pagination is not 12 pages')
renderer=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/render_docx.py'
if not renderer.exists():fail('DOCX renderer not found')
render_python=Path(os.environ.get('PYTHON',Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'))
if not render_python.exists():render_python=Path(sys.executable)
render_env=os.environ.copy()
# Use the native macOS font environment. For this report, forcing a Homebrew FONTCONFIG_FILE changes
# the Chinese font fallback metrics and can inflate the same Word document from 24 to 35 rendered pages.
with tempfile.TemporaryDirectory(prefix='case-docx-verify-') as tmp:
 for source,name,expected in ((REPORT,'report',None),(SCRIPT,'script',12)):
  out=Path(tmp)/name
  render_cmd=[str(render_python),str(renderer),str(source),'--output_dir',str(out)]
  if name=='report':render_cmd.append('--emit_pdf')
  subprocess.run(render_cmd,cwd=ROOT,env=render_env,check=True,stdout=subprocess.DEVNULL)
  pages=len(list(out.glob('page-*.png')))
  if name=='report':
   if not 24<=pages<=26:fail(f'report rendered to {pages} pages; technical-paper report should remain within 24-26 pages')
   rendered_pdf=next(out.glob('*.pdf'),None)
   if rendered_pdf is None:fail('report renderer did not emit a PDF for pagination QA')
   layout_text=subprocess.run(['pdftotext','-layout',str(rendered_pdf),'-'],check=True,text=True,capture_output=True).stdout
   rendered_pages=layout_text.split('\f')
   for page_index,page_text in enumerate(rendered_pages,1):
    first_line=next((line.strip() for line in page_text.splitlines() if line.strip()),'')
    if first_line.startswith('注：'):fail(f'report page {page_index} starts with an orphaned table note')
   if len(re.sub(r'\s+','',rendered_pages[-2] if rendered_pages and not rendered_pages[-1].strip() else rendered_pages[-1]))<180:fail('report final page is under-filled; avoid orphaning the conclusion')
   for equation_number in ('(1)','(2)','(3)','(4)'):
    if equation_number not in layout_text:fail(f'native equation number missing from rendered PDF: {equation_number}')
   pdf_xml_base=out/'report-rendered-font-audit'
   subprocess.run(['pdftohtml','-xml','-hidden',str(rendered_pdf),str(pdf_xml_base)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   pdf_xml=Path(str(pdf_xml_base)+'.xml').read_text(errors='ignore')
   if '<i>' in pdf_xml:fail('rendered report contains italic text; equation variables must remain upright in the final PDF rendering')
  elif pages!=expected:fail(f'{name} rendered to {pages} pages, expected {expected}')
env=os.environ.copy();env['NODE_PATH']=os.environ.get('NODE_MODULES','');subprocess.run([os.environ.get('NODE','node'),str(ROOT/'scripts/smoke_deck.mjs')],cwd=ROOT,env=env,check=True);subprocess.run([sys.executable,str(ROOT/'scripts/privacy_check.py')],cwd=ROOT,check=True)
print('[verify] passed: report preserved, deck 12 pages, script 12 pages, text/privacy/interaction checks OK')
