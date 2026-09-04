#!/usr/bin/env python3
import json,os,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
REPORT=DIST/'案例考核报告-从人海作业到数智协同.docx';SCRIPT=DIST/'答辩逐字稿-从人海作业到数智协同.docx';HTML=DIST/'课题答辩-从人海作业到数智协同.html';PDF=DIST/'课题答辩-从人海作业到数智协同.pdf'
CASE=json.loads((ROOT/'content/case.json').read_text('utf-8'));DEFENSE=json.loads((ROOT/'content/defense.json').read_text('utf-8'));BASELINE=(ROOT/'docs/CASE-LOGIC-BASELINE.md').read_text('utf-8')
def fail(msg):print('[verify] ERROR '+msg);sys.exit(1)
for p in (REPORT,SCRIPT,HTML,PDF):
 if not p.exists() or p.stat().st_size<1000:fail(f'missing or empty: {p.name}')
if REPORT.stat().st_size>5*1024*1024:fail(f'report DOCX exceeds 5 MB size budget: {REPORT.stat().st_size/1024/1024:.2f} MB')
html=HTML.read_text('utf-8')
if len(re.findall(r'<section class="slide(?:\s|\")',html))!=13:fail('HTML slide count is not 13')
if re.search(r'__[A-Z0-9_]+__',html):fail('HTML contains unresolved placeholder')
info=subprocess.run(['pdfinfo',str(PDF)],check=True,text=True,capture_output=True).stdout
if not re.search(r'^Pages:\s+13$',info,re.M):fail('PDF page count is not 13')
pdf_text=subprocess.run(['pdftotext',str(PDF),'-'],check=True,text=True,capture_output=True).stdout
normalized_pdf=re.sub(r'\s+','',pdf_text)
if len(pdf_text)<1500 or any(term not in normalized_pdf for term in ('系统显示“已完成”','相隔3天','反馈画面存在拼改嫌疑','用算法从海量照片中筛出可核查线索')):fail('PDF text layer incomplete')
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
expected_titles=[
 '从人海作业到数智协同','规模增长后，两种人海管理都难以持续','我把外协管理问题拆成增效和提质两条线',
 '我把点、线、面三类空间对象转成可执行的任务筛选规则','一套线路数据支撑三类专项任务筛选','同一批数据的前期筛查由近两周缩短到数分钟',
 '系统显示“已完成”，就等于真的履职到位了吗？','相隔3天，两次工单出现高度相似的反馈画面','再看对应工单照片，反馈画面存在拼改嫌疑','用算法从海量照片中筛出可核查线索',
 '全量筛查结果已经进入省级管理闭环','两项实践遵循同一套人机协同机制','任务筛选更精准，履职监督更全面'
]
actual_titles=[item.get('title') for item in DEFENSE.get('slides',[])]
if actual_titles!=expected_titles:fail(f'defense 13-page title structure mismatch: {actual_titles}')
slide_visible=[re.sub(r'\s+','',re.sub(r'<[^>]+>',' ',block)) for block in slide_blocks]
for index,title in enumerate(expected_titles):
 if re.sub(r'\s+','',title) not in slide_visible[index]:fail(f'deck slide {index+1} title does not match defense plan: {title}')
if any('class="mirror-method' in block for block in slide_blocks[:11]):fail('shared method summary must not appear before slide 12')
if 'class="mirror-method' not in slide_blocks[11]:fail('shared method summary must appear on slide 12')
for index,phrases in ((3,('传统方式','数字化筛选')),(4,('铁路交叉跨越','集中燃放点','防鸟重点区域')),(5,('近两周','数分钟')),(6,('工单状态','照片已上传','真的履职到位了吗')),(7,('5月25日','5月22日','反馈照片')),(8,('工单照片','局部放大','5月22日有伞','5月25日无伞','规避人工审查')),(9,('直接两两比较','感知哈希','语义特征','系统候选','核查确认重复','进入照片查重工作台')),(10,('省级管理通报','查重结果经核查后进入管理通报'))):
 for phrase in phrases:
  if phrase not in slide_visible[index]:fail(f'double-line business evidence missing {phrase} on slide {index+1}')
if 'data-open-photo' in slide_blocks[7] or 'workbench-launch' in slide_blocks[7] or 'open-label' in slide_blocks[7]:fail('slide 8 must be static two-photo evidence only; workbench trigger is forbidden')
if slide_blocks[7].count('data-proof=')!=2 or 'zoom-box' in slide_blocks[7] or 'data-proof-zoom' in slide_blocks[7] or 'order-zoom' in slide_blocks[7]:fail('slide 8 must contain exactly two feedback photos without local magnifier crops')
if 'data-open-photo' in slide_blocks[8] or slide_blocks[8].count('data-order-proof=')!=2 or slide_blocks[8].count('data-order-zoom=')!=2 or slide_blocks[8].count('order-zoom-box')<2:fail('slide 9 must be static two-workorder-photo proof with local magnifier crops')
if slide_blocks[9].count('data-open-photo')!=1 or 'workbench-launch' not in slide_blocks[9]:fail('slide 10 must contain exactly one workbench launch after algorithm/effect')
if 'data-metric="theoretical_pairs"' not in slide_blocks[9]:fail('slide 10 must bind the 77.5万亿 theoretical-combination metric')
levels=CASE['metrics'].get('metric_levels',{})
required_levels={
 'alarm_confirmed_pairs':'照片对层级','patrol_duplicate_pairs':'照片对层级','province_trial_duplicate_issues':'管理问题层级',
 'province_trial_alarm_duplicate_issues':'管理问题层级','province_trial_patrol_duplicate_issues':'管理问题层级'
}
for key,level in required_levels.items():
 if level not in levels.get(key,''):fail(f'metric level metadata missing for {key}: {level}')
slide10=slide_visible[10];slide10_html=slide_blocks[10]
for required in ('告警工单查重结果','人工巡视查重结果','查重结果经核查后进入管理通报','省级管理通报'):
 if required not in slide10:fail(f'slide 10 missing audience-facing result chain: {required}')
for metric_key in ('alarm_confirmed_pairs','patrol_duplicate_pairs','province_trial_duplicate_issues','province_trial_alarm_duplicate_issues','province_trial_patrol_duplicate_issues'):
 if f'data-metric="{metric_key}"' not in slide10_html:fail(f'slide 10 missing metric binding: {metric_key}')
for required in ('348','55,411','19','11','8'):
 if required not in normalized_defense:fail(f'rendered defense artifacts missing metric hierarchy value: {required}')
expected_spatial_model='点—线—面：交叉跨越对应线，防鸟对应面，集中燃放点对应点'
for required_baseline_fact in ('点—线—面','交叉跨越对应线','防鸟对应面','集中燃放点对应点'):
 if required_baseline_fact not in BASELINE:fail(f'case logic baseline lost required spatial classification fact: {required_baseline_fact}')
if CASE.get('technical',{}).get('spatial_model')!=expected_spatial_model:fail(f'case spatial model must exactly follow baseline: {CASE.get("technical",{}).get("spatial_model")}')
slide4=slide_visible[3]
for required in ('点—线—面','集中燃放点','交叉跨越','防鸟重点区域'):
 if required not in slide4:fail(f'slide 4 missing point-line-area classification: {required}')
for forbidden in ('线—线','点—距','面—线','线、点、面三类','个人突破一','个人突破二','把经验写成规则，把计算结果接回管理'):
 if forbidden in normalized_defense:fail(f'defense artifacts contain forbidden or superseded wording: {forbidden}')
for internal_phrase in ('本人行动','演示证据','实际结果','责任边界','规模扩展','统计层级不同','照片关系层','管理问题层','管理变化：','实践一：','实践二：'):
 if internal_phrase in re.sub(r'\s+','',slide_text) or internal_phrase in re.sub(r'\s+','',pdf_text):fail(f'presentation leaks internal-facing wording: {internal_phrase}')
for name,text in (('deck HTML',html),('deck PDF',pdf_text),('speaker script',script_text)):
 if '脱敏' in text:fail(f'{name} contains forbidden privacy wording')
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
for name,text in (('deck HTML',slide_text),('deck PDF',pdf_text)):
 if '×' in text or re.search(r'\s[xX]\s',text):fail(f'{name} contains banned A x B structure')
for obsolete in ('287对','287对认定','5.2%','候选命中率','500千伏特殊通道','较大运检质量问题'):
 if obsolete in normalized_defense:fail(f'defense artifacts contain obsolete or out-of-scope wording: {obsolete}')
for production_note in ('原演示','交互保留','完整保留','点击右上角关闭','仅展示','不涉及具体单位','按要求','根据要求','用户要求','制作说明','验收口径'):
 if production_note in normalized_defense:fail(f'defense artifacts contain production note or user instruction: {production_note}')
for forbidden_review_volume in ('4,630','已人工复核','人工复核量','候选人工复核','人工复核结论'):
 if forbidden_review_volume in normalized_defense:fail(f'defense artifacts expose forbidden intermediate review volume: {forbidden_review_volume}')
for required in ('40.1万','9200余','111,519','5,472','348','1245万','77.5万亿','55,411','系统显示“已完成”','相隔3天','拼改嫌疑','系统候选','核查确认重复','接数据','配规则','走闭环'):
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
program_allowlist={
 'report':(),
 'speaker script':(),
 'deck HTML':(),
 'deck PDF':(),
}
def assert_no_unapproved_program(name,text):
 cleaned=text
 for phrase in program_allowlist.get(name,()):cleaned=cleaned.replace(phrase,'')
 if '程序' in cleaned:fail(f'{name} contains unapproved wording: 程序')
for name,text in (('report',report_text),('speaker script',script_text),('deck HTML',slide_text),('deck PDF',pdf_text)):
 assert_no_ai_contrast(name,text)
 assert_no_unapproved_program(name,text)
approved_quality_review_term='运检工作质量远程督查'
if approved_quality_review_term not in report_text:fail('report missing official proper noun: 运检工作质量远程督查')
if '督查' in report_text.replace(approved_quality_review_term,''):fail('report contains non-official 督查 wording; use the exact proper noun 运检工作质量远程督查 when referring to the official mechanism')
for forbidden in ('运检质量监督工作','杆塔台账','9217条线路','2026-02-28','2026-06-29','本人','个疑似相似候选','个候选，并已人工确认','人工投入无法支撑全量计算','1.创新一：','2.双阶段算法：','3.创新二：','4.千万级工程化处理：','点到线段的最短距离','相同或相邻空间单元','计算坐标统一','log(1+n)','而不是简单比较两个清单数量','空间网格索引预筛','0.025°经纬度网格','pHash距离','增效 + 提质','气象节假日','170×210经纬度栅格统计数量','活动区域进入阈值','同图篡改水印日期','裁剪压缩','全电压等级月度千万级巡视照片','正常变化是否能留给人工终审','重复度高','单点提效','2025年年底','把人工和高成本计算','表5已经把','交叉跨越这种单项排查','约5千对','0到1区间','显式保留','问题覆盖两类业务，说明照片查重已经从个人开发工具进入省级生产管理应用','这个事件说明，照片查重已经从“能找到相似照片”进入“能够支撑履职质量判断和管理闭环”的阶段','推广条件也比较清晰','这次排查也让我确认','真正推动照片查重进入实际管理的，是','这一案例成为照片查重进入实际管理的典型节点','从“个人解决问题”进入“组织持续使用”的阶段','高价值疑似照片对','4,282对“确认不同”同样具有价值'):
 if forbidden in report_text:fail(f'report contains obsolete or inaccurate wording: {forbidden}')
if re.search(r'(?:图|表)\d+\u3000',report_text):fail('report captions still use ideographic-space separator; use normal spaces for stable PDF text extraction')
if any(v in core_xml for v in ('Administrator','Evolution')):fail('report core metadata still contains template/editor identity')
if any(name.startswith('word/comments') for name in report_parts):fail('report must not contain reviewer comments in final review artifact')
if re.search(r'<w:(?:ins|del)(?:\s|>)',rx):fail('report must not contain tracked changes')
if re.search(r'[，。；：！？、]{2,}',report_text):fail('report contains duplicated Chinese punctuation')
for left,right in (('“','”'),('（','）')):
 if report_text.count(left)!=report_text.count(right):fail(f'report punctuation pair is unbalanced: {left}{right}')
W_NS='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
report_paragraphs=[]
for p in ET.fromstring(rx).iter(W_NS+'p'):
 text=''.join(p.itertext()).strip()
 if text:report_paragraphs.append(re.sub(r'\s+',' ',text))
table_numbers=[int(m.group(1)) for t in report_paragraphs if (m:=re.match(r'^表(\d+)\s',t))]
figure_numbers=[int(m.group(1)) for t in report_paragraphs if (m:=re.match(r'^图(\d+)\s',t))]
equation_numbers=[int(m.group(1)) for t in report_paragraphs if (m:=re.search(r'\((\d+)\)$',t))]
numbered_subheads=[int(m.group(1)) for t in report_paragraphs if (m:=re.match(r'^([1-9])\.(?=[\u4e00-\u9fff])',t))]
primary_headings=[m.group(1) for t in report_paragraphs if (m:=re.match(r'^([一二三四五])、',t))]
parenthetical_headings=[m.group(1) for t in report_paragraphs if (m:=re.match(r'^（([一二三四五六七八九十]+)）',t))]
if primary_headings!=['一','二','三','四','五']:fail(f'report primary heading sequence is wrong: {primary_headings}')
if parenthetical_headings!=['一','二','三','四','一','二','一','二','一','二','三','四']:fail(f'report parenthetical heading sequence is wrong: {parenthetical_headings}')
if table_numbers!=list(range(1,11)):fail(f'report table numbering is not sequential 1-10: {table_numbers}')
if figure_numbers!=list(range(1,12)):fail(f'report figure numbering is not sequential 1-11: {figure_numbers}')
if equation_numbers!=list(range(1,5)):fail(f'report equation numbering is not sequential 1-4: {equation_numbers}')
if numbered_subheads!=[1,2,3,1,2,3,4,5,1,2,3,4]:fail(f'report numbered subheading sequence is wrong: {numbered_subheads}')
for required in ('图10　告警工单反馈照片与对应告警照片对照','5月22日告警照片中现场人员持伞','5月25日告警照片中现场人员未持伞','局部图像编辑','40.1万基输电杆塔','9200余条输电线路','全省220kV及以上线路连续三个月','相关核心算法和数字化工具均由我自主设计、开发和验证','此前由电力信息公司提供的既有照片查重能力主要覆盖少量特高压巡视照片','目前能够按月处理约1245万张巡视照片','向其他地市公司推广','传统人工方式难以支撑全量管理','已经成为输电运检专业必须解决的管理问题','面向省域输电运检管理','5,472对疑似相似照片','确认重复348对','约62.18亿对','7.52%','1.告警工单照片查重：从零建立全量筛查方法','2.照片查重：pHash先筛，CLIP再比','4.千万级处理：让1245万张照片稳定跑完','管理层面，把外协管理归纳为“增效管任务、提质管履职”两条主线','方法层面，把空间关系、距离条件和历史照片相似关系转成机器可执行的筛选规则','工程层面，把原有少量特高压照片筛查扩展到全电压等级','两条主线、一个机制','告警工单反馈照片查重和巡视照片查重均已在省公司层面开展试点','照片重复类问题19项','告警工单反馈照片重复11项','人工巡视照片重复8项','省公司试点中，照片智能筛查模块筛出一组500千伏特殊通道高相似照片','照片查重已在省公司生产管控中心实际应用','该结果已直接用于履职质量判断和管理闭环','接数据、配规则、走闭环','6438个杆塔坐标','249条线路','既有资料中记录了241处铁路跨越结果','照片智能筛查模块只负责把疑似照片对找出来','约77.5万亿对','不依赖新增现场硬件','燃放点—杆塔','ln(1+n)','连续执行7次3×3邻域均值平滑','70%、84%、94%分位点','229,561条有效记录','170×210个经纬度栅格','pHash汉明距离＜10且CLIP相似度＞0.80','包围盒预筛','0.0005°','Shapely','三个空间专项可以用“点—线—面”三个空间对象统一理解','三类空间专项的点—线—面对象与筛选逻辑','三类专项分别以点、线、面为分析入口','案例实施成效与管理方式变化','从“大范围找目标”到“拿清单去核验”','从“抽到才发现”到“全量先筛一遍”'):
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
if len(re.findall(r'<w:tbl(?:\s|>)',rx))!=10:fail('report should contain exactly 10 high-value academic tables; low-value engineering tables must not regress into the report')
if rx.count('w:tblHeader')!=10:fail('every academic table must repeat its header row across page breaks')
if rx.count('w:cantSplit')<45:fail('academic table rows must prevent row-level page splitting')
if len(re.findall(r'<w:drawing>',rx))!=11:fail('report should contain exactly 11 approved figures')
report_page_starts=len(re.findall(r'w:type="page"',rx))+len(re.findall(r'w:pageBreakBefore',rx))
if report_page_starts!=0:fail('report must use template-style natural pagination without explicit page breaks')
if len(re.findall(r'w:type="page"',sx))!=12:fail('script explicit pagination is not 13 pages')
renderer_root=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents'
renderer_candidates=sorted(renderer_root.glob('*/skills/documents/render_docx.py'),reverse=True)
if not renderer_candidates:fail('DOCX renderer not found')
renderer=renderer_candidates[0]
render_python=Path(os.environ.get('PYTHON',Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'))
if not render_python.exists():render_python=Path(sys.executable)
render_env=os.environ.copy()
# Use the native macOS font environment. For this report, forcing a Homebrew FONTCONFIG_FILE changes
# the Chinese font fallback metrics and can inflate the same Word document from 24 to 35 rendered pages.
with tempfile.TemporaryDirectory(prefix='case-docx-verify-') as tmp:
 for source,name,expected in ((REPORT,'report',None),(SCRIPT,'script',13)):
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
print('[verify] passed: report preserved, deck 13 pages, script 13 pages, text/privacy/interaction checks OK')
