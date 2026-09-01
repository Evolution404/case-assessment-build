#!/usr/bin/env python3
import json, os
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT.parent/"06 研讨报告模板【研讨报告可参考，根据实际.docx"
OUT=ROOT/"dist/案例考核报告-从人海作业到数智协同.docx"
CONFIRM_FIG=ROOT/"dist/confirm"
CFG=json.loads((ROOT/"content/case.json").read_text(encoding="utf-8"))
CASE_ID=os.environ.get("CASE_ID",CFG["case_id_default"])
ALARM_SCOPE=CFG["metrics"]["alarm_scope_label"]
PROVINCE_LINES_LABEL=CFG["metrics"]["province_lines_report_label"]
FONT="仿宋_GB2312"

def wipe_body(doc):
    body=doc._element.body
    for child in list(body):
        if child.tag!=qn("w:sectPr"):
            body.remove(child)

def set_run(run,size=14,bold=False,color="000000",font=FONT):
    run.font.name=font;run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=RGBColor.from_string(color)
    rpr=run._element.get_or_add_rPr();rf=rpr.find(qn("w:rFonts"))
    if rf is None: rf=OxmlElement("w:rFonts");rpr.append(rf)
    for k in ("ascii","hAnsi","eastAsia","cs"):rf.set(qn("w:"+k),font)

def para(doc,text="",size=14,bold=False,align=None,indent=True,before=0,after=0,line=28,color="000000",keep=False):
    p=doc.add_paragraph();f=p.paragraph_format
    f.line_spacing_rule=WD_LINE_SPACING.EXACTLY;f.line_spacing=Pt(line);f.space_before=Pt(before);f.space_after=Pt(after)
    if align is not None:f.alignment=align
    if indent:f.first_line_indent=Pt(size*2)
    if keep:f.keep_with_next=True
    set_run(p.add_run(text),size,bold,color)
    return p

def h1(doc,text):return para(doc,text,15,True,indent=True,keep=True)
def h2(doc,text):return para(doc,text,14,True,indent=True,keep=True)
def bullet(doc,text):return para(doc,text,14,False,indent=True)

def report_title(doc,title,subtitle):
    p=para(doc,title,22,False,WD_ALIGN_PARAGRAPH.CENTER,True,line=28)
    p.paragraph_format.first_line_indent=Pt(44)
    p=doc.add_paragraph();f=p.paragraph_format
    f.line_spacing_rule=WD_LINE_SPACING.EXACTLY;f.line_spacing=Pt(28);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("—"),18,False)
    set_run(p.add_run(subtitle),16,False)
    return p

def figure(doc,name,caption,width=15.0):
    confirmed={
        "pain-points":"01-外协管理两大痛点.png",
        "province-map":"02-省域线路杆塔任务规模.png",
        "dual-wheel":"03-增效提质总体模型.png",
        "workflow":"04-外协任务数字化筛选流程.png",
        "crossing":"05-交叉跨越自动筛查.png",
        "bird":"06-鸟类活动重点区域筛查.png",
        "fireworks":"07-集中燃放点周边杆塔筛查.png",
        "photo-scale":"08-告警工单照片筛选-1-核心规模与筛选复核.png",
        "photo-cases":"08-告警工单照片筛选-2-真实案例.png",
        "outcomes":"10-外协管理模式转型总结.png",
    }
    if name not in confirmed:
        raise KeyError(f"未配置的确认插图：{name}")
    image_path=CONFIRM_FIG/confirmed[name]
    if not image_path.exists():
        raise FileNotFoundError(f"缺少确认插图：{image_path}")
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(0)
    shape=p.add_run().add_picture(str(image_path),width=Cm(width))
    shape._inline.docPr.set("title",caption)
    shape._inline.docPr.set("descr",caption)
    c=doc.add_paragraph();c.alignment=WD_ALIGN_PARAGRAPH.CENTER;c.paragraph_format.space_after=Pt(0)
    c.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY;c.paragraph_format.line_spacing=Pt(24)
    set_run(c.add_run(caption),12,False,"000000")

def page_break(doc):
    # 模板采用连续研讨报告排版，不主动插入分页符；由 Word 根据正文与图片自然分页。
    return None

def footer(doc):
    sec=doc.sections[0];p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    fld=OxmlElement("w:fldSimple");fld.set(qn("w:instr"),"PAGE");p._p.append(fld)
    for r in p.runs:set_run(r,10,False,"666666")

def add_summary_table(doc):
    tbl=doc.add_table(rows=3,cols=3);tbl.alignment=WD_TABLE_ALIGNMENT.CENTER;tbl.autofit=False
    trpr=tbl.rows[0]._tr.get_or_add_trPr();tbl_header=OxmlElement("w:tblHeader");tbl_header.set(qn("w:val"),"true");trpr.append(tbl_header)
    widths=[Cm(3.4),Cm(5.7),Cm(5.7)]
    rows=[("外协管理","增效：解决工作量大","提质：解决质量难保证"),("手段","交叉跨越、防鸟、集中燃放点等数字化筛选","告警工单、巡视照片全量查重"),("变化","全量人工排查 → 外协精准核验","有限人工抽查 → 异常重点复核")]
    for ri,row in enumerate(tbl.rows):
        for ci,cell in enumerate(row.cells):
            cell.width=widths[ci];cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text="";p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            set_run(p.add_run(rows[ri][ci]),11.5,ri==0 or ci==0,"FFFFFF" if ri==0 else "000000")
            tcpr=cell._tc.get_or_add_tcPr();shd=OxmlElement("w:shd");shd.set(qn("w:fill"),"27333A" if ri==0 else ("E9E3D9" if ci==0 else "F7F3EC"));tcpr.append(shd)

def build():
    doc=Document(str(TEMPLATE));wipe_body(doc)
    # 保留真实模板自身的 A4 页面设置与页边距：上下 2.54 cm，左右 3.175 cm；不增加页码。
    report_title(doc,CFG["title"],CFG["subtitle"])
    # 按模板结构，标题后直接进入正文，不设置独立封面、摘要、关键词、案例编号或摘要表。
    h1(doc,"一、背景、问题、现状")
    h2(doc,"（一）外协力量已成为输电运检的重要延伸")
    para(doc,"随着设备规模扩大、运检任务增加，巡视、隐患排查、现场值守、工单处置和台账采集等工作越来越多地需要外协力量参与。外协队伍是业务执行的重要支撑，其管理效能直接影响业务质量与交付效率。")
    h2(doc,"（二）外协管理面临“工作量大、质量难保证”两大痛点")
    bullet(doc,"工作量大：输电运检专项任务对象多、覆盖范围广，交叉跨越、防鸟、集中燃放点等工作往往需要依托大量台账、坐标和现场信息逐项排查。传统方式主要依靠外协人员全量查找、逐项核对和现场摸排，重复性工作多、人员投入大，任务越多，工作量越呈线性增长。")
    bullet(doc,f"质量难保证：外协履职涉及大量工单、现场反馈和长期积累的历史数据。仅{ALARM_SCOPE}的告警工单数量就超过11万条，同时还沉淀了大量现场反馈照片和历史处置记录。面对数量庞大、时间跨度长、跨工单分散存储的作业数据，管理人员很难依靠人工逐一核验，更难在历史数据中发现同一照片跨时间、跨工单重复使用等异常情况，传统抽查方式难以全面判断外协工作是否真实、规范、到位。")
    bullet(doc,"共同症结：传统外协管理主要依靠“人去找任务、人去查质量”：任务侧把大量人力消耗在全量排查上，质量侧又受限于人工审核能力只能进行有限抽查。随着业务数据持续增长，单纯增加人力已难以解决问题，需要由机器承担全量筛选和异常发现，人员集中开展现场核验、专业判断和管理闭环。")
    figure(doc,"pain-points","图1　外协队伍管理面临的两大痛点",12.3)
    page_break(doc)
    # 4 现状量级
    h2(doc,"（三）数据规模决定了“人海作业”不可持续")
    para(doc,f"目前全省约有{CFG['metrics']['province_poles']/10000:.1f}万基输电杆塔、{PROVINCE_LINES_LABEL}。围绕日常运维和专项治理，需要按照不同业务口径持续统计、更新各类台账，例如交叉跨越、防鸟、集中燃放点等，往往都要重新关联线路、杆塔、坐标及外部数据。传统方式主要依靠人工整理、逐项核对，既耗费大量人力，同一基础数据又在不同专项中反复处理，设备规模越大，重复工作越突出。")
    para(doc,f"业务过程数据同样持续增长。{ALARM_SCOPE}共形成{CFG['metrics']['alarm_workorders']:,}条告警工单、{CFG['metrics']['alarm_photos']:,}张现场反馈照片；巡视照片每月约{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张。数据跨线路、跨任务、跨时间积累，人工不仅难以逐一核验，更难与历史记录进行全量比对。以月度{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张巡视照片为例，若采用简单两两比较，理论组合约77.5万亿，依靠人工或简单穷举均无法支撑。")
    figure(doc,"province-map","图2　省域线路杆塔任务规模与电压等级分布",12.8)
    para(doc,"以线路、杆塔及其空间位置作为统一基础数据底座后，交叉跨越、防鸟、集中燃放点等专项可直接复用同一套基础数据，仅根据业务规则叠加不同外部信息，减少不同口径台账反复整理、重复核对的工作量，为后续批量筛查和任务生成提供统一基础。")
    page_break(doc)
    # 5 根因
    h2(doc,"（四）根因分析：人工投入无法支撑全量计算")
    para(doc,"一是数据“能看不能算”。表格中虽然存在坐标、线路、照片等信息，但字段标准、顺序关系和异常处理并不统一，机器无法直接批量计算。二是业务经验“能做不能复用”。交跨如何判断、鸟害区域如何收敛、重复照片如何认定，规则长期存在于个人经验中。三是工具与流程脱节。程序即使输出结果，如果没有人工复核、任务派发、整改回写，仍然不能转化为管理成效。")
    para(doc,"本案例把外协任务管理和质量监督分别改造成两条人机协同闭环：增效让机器先筛任务、外协精准核验；提质让机器全量查重、管理人员重点复核。")
    para(doc,"因此，问题不能继续通过单纯增加人手解决，而应重新划分人机职责：机器承担全量筛选和重复劳动，人员负责现场核验、专业判断与管理闭环。这一重构既是效率改进，也是质量治理机制的升级。")
    page_break(doc)
    # 6 模型
    h1(doc,"二、总体思路：构建“增效 + 提质”的外协数智管理模式")
    h2(doc,"（一）“增效管任务、提质管履职”双线协同")
    para(doc,"增效解决“外协任务量大、人员到底去哪里查什么”的问题：系统在全量对象中自动筛选重点，形成清单后由外协人员精准核验。提质解决“外协工作是否真实、质量是否可靠”的问题：系统对作业照片全量查重，管理人员只对异常候选重点复核。")
    figure(doc,"dual-wheel","图3　外协管理增效提质总体模型",14.4)
    para(doc,"两条主线共享同一机制：全部对象先由机器全量筛选，再把少量候选交给人。增效把外协人员从无效排查中解放出来，提质把管理人员从有限抽查升级到异常重点复核。")
    page_break(doc)
    # 7 architecture
    h2(doc,"（二）外协数智管理的共用闭环")
    para(doc,"数字化筛选不是孤立的算法环节，而是一条贯通任务组织、现场执行和主业复核的完整管理链。多源数据先统一汇集，系统依据安全距离、风险等级等规则进行空间叠加和自动识别，再将重点任务定向推送给外协队伍，最终由主业复核并把反馈用于规则优化。")
    figure(doc,"workflow","图4　外协任务数字化筛选与闭环管理流程",15.2)
    bullet(doc,"多源数据汇集：统一交叉跨越、鸟类活动、燃放点、气象节假日和杆塔线路底账。")
    bullet(doc,"空间叠加与规则筛查：把安全距离、风险等级等业务要求转成可计算条件。")
    bullet(doc,"重点任务自动识别：生成高风险、高影响点位清单，减少全量人工排查。")
    bullet(doc,"外协定向巡视：任务和路线精准推送，现场执行并上传反馈。")
    bullet(doc,"主业复核与闭环：确认结果、处置问题并持续优化规则。")
    page_break(doc)
    # 8 efficiency overview
    h1(doc,"三、具体做法")
    h2(doc,"（一）增效：数字化筛选减少外协无效排查")
    para(doc,"交叉跨越、防鸟和集中燃放点三个场景解决的是同一个外协管理问题：专项对象数量大、分布范围广，依靠人员开展全量排查投入高、效率低。系统共用杆塔坐标、线路拓扑和外部数据底座，根据不同业务规则生成重点候选清单，再由外协人员定向巡视、现场核验。")
    h2(doc,"1.建立可复用的数据底座")
    para(doc,"首先检查空坐标、重复点、离群点和杆号顺序，将相邻杆塔连接为线路段；同时对铁路、鸟类活动、燃放点和气象节假日等外部数据进行统一标准化。相同线路底账不再被不同专项重复整理，形成可以复用的省域任务底座。")
    h2(doc,"2.把业务经验转化为可计算规则")
    para(doc,"把“是否相交”“是否进入重点活动区域”“是否落入安全距离”等业务判断转化为空间叠加、风险分级和距离阈值，将原先依赖个人经验逐项判断的工作固化为可重复执行的计算规则，使同类专项能够批量生成重点核验清单，减少重复判断和人为漏项。")
    h2(doc,"3.以任务清单组织外协精准核验")
    para(doc,"候选点位和区段按风险、区域和任务类型整理为清单，定向推送给外协人员并规划巡视路线。外协上传现场结果，主业复核后回写状态，形成“自动筛选—定向执行—反馈复核—规则优化”的闭环。")
    h2(doc,"4.统一的增效价值")
    bullet(doc,"把全量人工排查转变为重点候选核验。")
    bullet(doc,"把分散任务来源转变为统一清单和路线。")
    bullet(doc,"把一次性人工经验转变为可复用、可迭代的规则资产。")
    page_break(doc)
    # 9 crossing
    h2(doc,"1.交叉跨越：包围盒预筛与精确几何求交")
    para(doc,"若把所有输电线段与全部铁路要素逐一比较，计算量会随两类线段数量相乘。为提高效率，先为每条线段生成最小包围盒，只保留包围盒存在重叠可能的组合；随后进行精确线段求交，计算候选交点。该方法把大量明显不相交的对象挡在精确计算之前。")
    figure(doc,"crossing","图5　交叉跨越自动筛查及候选分布",15.2)
    para(doc,"通过对输电线路与铁路、公路等地理要素进行批量空间计算，可一次性从全量线路中筛选潜在重要跨越点，将原来依靠人员逐条线路、逐个区段查找的工作转化为候选点定向核验。以某地市应用为例，原需十余人、近两周开展的全量排查，程序数分钟即可完成，并补充识别出十余处此前人工排查遗漏的铁路、公路等重要跨越信息，既显著压缩排查时间，也进一步提高了重要跨越底数的完整性。")
    page_break(doc)
    # 10 bird
    h2(doc,"2.防鸟：公开生态资料与线路空间叠加")
    para(doc,"利用GBIF鸟类活动数据并结合公开生态资料，对鸟类活动记录进行空间汇总，识别活动较集中及湿地、水网、迁徙廊道等重点区域，再与输电线路空间叠加，批量筛选需要外协重点核验的线路区段，为防鸟装置排查和差异化巡视提供任务清单。")
    figure(doc,"bird","图6　鸟类活动重点区域与输电线路空间叠加筛查",12.8)
    para(doc,"通过将鸟类活动数据与输电线路空间位置进行批量叠加，可从全省线路中快速筛选鸟类活动相对集中的重点区段，为防鸟专项排查提供明确的任务范围。相比依靠外协人员沿线大范围摸排，系统可先完成全量分析，再将有限人力集中到重点区段开展现场核验，有效减少无效巡视和重复排查，提高防鸟专项工作的组织效率和针对性。")
    page_break(doc)
    # 11 fireworks
    h2(doc,"3.集中燃放点：N米缓冲与周边杆塔批量筛查")
    para(doc,"集中燃放点排查本质上是点到线路或杆塔的距离问题。程序以每个燃放点生成N米缓冲区，利用包围盒先筛出周边对象，再计算精确距离。落入阈值范围的杆塔形成候选清单，外协人员结合现场地形、风向、障碍物和实际管控要求复核。")
    figure(doc,"fireworks","图7　集中燃放点影响范围与周边杆塔筛查",12.8)
    para(doc,"集中燃放点排查由逐点查询、逐塔判断转变为批量计算，可在较短时间内形成重点杆塔和线路清单。尤其在节假日等集中排查时段，可避免外协人员围绕大量点位反复查询和判断，将工作重心直接聚焦到可能受影响的设备。交叉跨越、防鸟和集中燃放点三个场景由此形成统一的“系统全量筛选—清单定向派发—外协精准核验”任务组织模式。")
    page_break(doc)
    # 12 quality problem
    h2(doc,"（二）提质：照片查重强化外协履职质量监督")
    para(doc,f"外协人员提交的反馈照片是证明现场处置和巡视到位的重要依据。{ALARM_SCOPE}共形成{CFG['metrics']['alarm_workorders']:,}条告警工单和{CFG['metrics']['alarm_photos']:,}张现场反馈照片。面对跨线路、跨任务、跨时间持续积累的历史数据，人工抽查既难以记住海量历史画面，也不易发现同一照片跨时间、跨工单重复使用，或篡改水印日期后再次上传等异常情况。")
    figure(doc,"photo-scale","图8　告警工单照片全量筛选与人工复核结果",15.2)
    para(doc,f"系统对{CFG['metrics']['alarm_photos']:,}张现场反馈照片进行全量筛选，形成{CFG['metrics']['alarm_candidates']:,}个疑似相似候选，其中{CFG['metrics']['alarm_reviewed']:,}个已完成人工复核：确认重复{CFG['metrics']['alarm_confirmed_pairs']:,}个，确认不同{CFG['metrics']['alarm_confirmed_different']:,}个，另有{CFG['metrics']['alarm_pending']:,}个待复核。原本需要在海量历史照片中逐张查找的问题，被压缩为对异常候选的重点复核，管理人员能够把有限精力集中在真正需要判断的对象上。")
    page_break(doc)
    # 13 innovation 1
    h2(doc,"1.创新一：从无到有建立告警工单照片查重")
    para(doc,"此前告警工单照片缺少面向全量数据的重复核查手段。本案例从0到1明确疑似重复的识别边界，设计“机器召回候选—人工对照原图—结合工单信息终审”的流程，并用真实业务样本校准规则。")
    figure(doc,"photo-cases","图9　真实复核案例：同图篡改水印日期与高相似但不同照片",12.2)
    para(doc,"图9上部三张照片主体、构图和现场细节一致，但水印日期分别显示为06-27、06-10和05-30，人工复核后确认属于同图修改水印日期后重复使用；下部两张照片虽然相似度达到97.63%，但车辆位置、吊臂姿态和现场物体存在真实变化，人工确认并非重复。通过全量查重，历史照片复用、跨工单重复上传和水印异常等问题由过去依靠人工记忆偶然发现，转变为系统持续生成异常线索、管理人员重点核验。")
    page_break(doc)
    # 14 algorithm
    h2(doc,"2.双阶段算法：pHash快速召回，CLIP语义复核")
    para(doc,"第一阶段计算感知哈希pHash，将图像压缩为反映整体结构的短指纹，以汉明距离快速发现构图近似的照片。第二阶段使用CLIP图像向量计算语义相似度，识别经过裁剪、调色、旋转、局部消除后仍然表达相同现场内容的照片。现有告警工单规则采用“pHash＜10且CLIP＞0.80”生成候选。")
    h2(doc,"分层候选生成")
    bullet(doc,"图像标准化：统一尺寸、方向和颜色通道，降低格式差异。")
    bullet(doc,"pHash快速召回：用低成本结构指纹从全量照片中筛出近似候选。")
    bullet(doc,"CLIP语义复核：对候选进行更精细的场景和对象相似度比较。")
    bullet(doc,"双阈值筛选：同时满足结构与语义条件时进入人工复核队列。")
    h2(doc,"人工复核与业务认定")
    para(doc,"系统将原图对比、相似度和关联业务信息集中呈现，复核人员结合拍摄时间、工单对象、现场细节和水印变化开展业务认定。通过分层筛选，大幅压缩需要人工查看的数据范围，使管理人员从海量照片逐张核对转向异常线索重点复核，提高质量监督效率。")
    page_break(doc)
    # 15 innovation 2
    h2(doc,"3.创新二：突破少量特高压限制，扩展到全电压等级")
    para(doc,"既有照片查重能力只能处理极少量特高压巡视照片，无法支撑全电压等级和千万级数据规模。核心瓶颈包括算力有限，以及照片数量增长带来的比较空间急剧膨胀。简单两两比较无法运行。本人围绕候选生成、分批调度、特征复用、结果去重和断点续算重构处理流程，显著降低无效比较。")
    h2(doc,"能力边界的实质变化")
    bullet(doc,"对象范围：从少量特高压照片扩展到全电压等级。")
    bullet(doc,"处理规模：形成每月1245万张巡视照片的规模化筛查能力。")
    bullet(doc,"计算方式：从不可运行的全量两两比较转为特征复用与分层候选生成。")
    bullet(doc,"运行保障：通过稳定分批、断点续算和结果归并支撑持续运行。")
    para(doc,"通过候选生成、特征复用、分批调度和断点续算等工程化重构，照片查重能力由少量特高压照片扩展至全电压等级，月度处理规模达到1245万张，实现了从小规模试用到千万级持续运行的能力突破。")
    page_break(doc)
    # 16 scale technical
    h2(doc,"4.千万级工程化处理：让算法真正跑得动")
    para(doc,"1245万张照片理论上包含约77.5万亿种两两组合。若全部计算，即使单次比较极快，也无法在可接受时间内完成。本案例先生成可复用特征，再利用低成本特征快速召回候选，对候选执行高成本语义复核，从而将计算集中到极小比例的数据上。")
    para(doc,"工程流程按照稳定批次运行，每批记录输入范围、特征状态、候选数量和输出校验值；发生中断后从已完成批次继续，避免重复计算。不同批次结果归并时依据匿名标识去重，最终输出候选对、相似度、复核状态和问题闭环字段。")
    h2(doc,"建立人机协同复核机制")
    para(doc,"照片查重将海量历史数据筛选为可复核的异常线索，管理人员再结合任务时间、作业对象、现场细节和业务要求进行综合判断。通过“机器全量筛选、人员重点复核”的职责分工，既发挥算法处理规模化数据的效率优势，又保留专业判断和处置闭环，形成可持续运行的外协履职质量监督机制。")
    page_break(doc)
    # 17 effects
    h1(doc,"四、实施效果")
    h2(doc,"（一）增效：把外协全量排查变成精准核验")
    para(doc,"交叉跨越、防鸟和集中燃放点由同一空间数据底座驱动，不同专项无需重复整理线路和杆塔基础信息。系统先对全量对象进行批量筛选，再形成重点点位和区段清单供外协人员现场核实，工作重心由“全量找、反复查”转向“按清单、精准核验”。其中，某地市重要跨越排查由原需十余人、近两周压缩至程序数分钟计算，并补充识别出十余处此前人工排查遗漏的重要跨越信息，增效效果得到实际验证。")
    h2(doc,"（二）提质：把有限人工抽查变成全量质量监督")
    para(doc,f"告警工单查重从无到有，在{CFG['metrics']['alarm_photos']:,}张反馈照片中形成{CFG['metrics']['alarm_candidates']:,}个候选，并已人工确认{CFG['metrics']['alarm_confirmed_pairs']:,}个重复问题；巡视照片查重则从少量特高压扩展到全电压等级。重复上传、历史照片复用和篡改水印日期等问题，不再只能依靠人工偶然发现。")
    h2(doc,"（三）管理方式：从人海式管理转向数智协同")
    para(doc,"本案例把外协管理中两类最消耗人力的工作重新分工：任务侧由机器先筛重点、外协按清单核验；质量侧由机器全量检查、管理人员复核异常。空间筛选和照片查重因此从单点工具上升为可复制的外协数智管理机制。")
    figure(doc,"outcomes","图10　外协管理由粗放管理向数智协同管理转型",12.8)
    # 18 recommendations
    h1(doc,"五、推广应用建议")
    h2(doc,"1.建立外协任务数字筛选机制")
    para(doc,"统一坐标、线路顺序和任务关联字段，以交叉跨越、防鸟、燃放点等专项为模板，把全量对象自动筛选为候选清单，形成“系统先筛、外协精准核验”的常态化任务组织方式。")
    h2(doc,"2.建立外协质量全量监督机制")
    para(doc,"将照片查重作为外协履职质量监督的常态化手段，按任务、时间和对象形成异常候选清单，并由管理人员重点复核、闭环处置。")
    h2(doc,"3.坚持机器全量筛选、人员精准核验")
    para(doc,"程序追求全量覆盖和高效召回，人员负责业务真实性判断和处置闭环，避免把算法相似度直接等同于管理结论。")
    h2(doc,"4.建立数据持续更新与成效评价机制")
    para(doc,"将现场核验结果、设备变更信息和照片复核结论持续回写数据底座，及时更新候选清单和业务规则；同步跟踪专项排查耗时、候选核验量、异常发现等指标，定期评估增效提质成效，推动外协数智管理由一次性应用转向常态化运行。")
    h2(doc,"结语")
    para(doc,CFG["thesis"]+" 从人海作业到数智协同，输电运检专业解决问题、验证结果和沉淀能力的方式已经发生改变。",14,True)
    OUT.parent.mkdir(parents=True,exist_ok=True);doc.save(OUT)
    print(f"[report] generated {OUT}")

if __name__=="__main__":build()
