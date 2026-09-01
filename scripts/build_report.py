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

def h1(doc,text):return para(doc,text,14,True,indent=True,keep=True)
def h2(doc,text):return para(doc,text,14,True,indent=True,keep=True)
def bullet(doc,text):return para(doc,text,14,False,indent=True)

def report_title(doc,title,subtitle):
    p=para(doc,title,18,False,WD_ALIGN_PARAGRAPH.CENTER,False,line=28)
    p=doc.add_paragraph();f=p.paragraph_format
    f.line_spacing_rule=WD_LINE_SPACING.EXACTLY;f.line_spacing=Pt(28);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("—"),16,False)
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
    para(doc,"随着输电线路规模持续扩大、运检任务不断增加，巡视、隐患排查、现场值守、工单处置和台账采集等大量基础工作需要外协力量参与。外协队伍已经成为输电运检专业的重要执行力量，其任务组织效率和履职质量，直接影响专业管理效能和现场工作质量。")
    h2(doc,"（二）外协管理面临“工作量大、质量难保证”两大痛点")
    bullet(doc,"工作量大：一项专项排查任务往往需要从多类台账和海量设备中重新寻找目标。以交叉跨越、防鸟、集中燃放点等工作为例，需要反复关联线路、杆塔、坐标和外部信息，再由外协人员逐项查找、现场摸排。任务对象越多、范围越大，人员投入几乎同步增加，大量精力消耗在重复查询和全量排查上。")
    bullet(doc,f"质量难保证：外协履职涉及大量工单、现场反馈和长期积累的历史数据。仅{ALARM_SCOPE}的告警工单数量就超过11万条，同时还沉淀了大量现场反馈照片和历史处置记录。面对数量庞大、时间跨度长、跨工单分散存储的作业数据，管理人员很难依靠人工逐一核验，更难在历史数据中发现同一照片跨时间、跨工单重复使用等异常情况，传统抽查方式难以全面判断外协工作是否真实、规范、到位。")
    bullet(doc,"共同症结：任务侧依赖“人去找”，质量侧依赖“人去查”，管理能力基本随人员投入线性增长，而设备规模和业务数据已经进入规模化增长阶段。单纯增加人员已难以支撑，排查范围难收敛、历史数据难全量核验、业务经验难固化复用等问题日益突出。")
    figure(doc,"pain-points","图1　外协队伍管理面临的两大痛点",12.3)
    page_break(doc)
    # 4 现状量级
    h2(doc,"（三）数据规模决定了“人海作业”不可持续")
    para(doc,f"目前全省约有{CFG['metrics']['province_poles']/10000:.1f}万基输电杆塔、{PROVINCE_LINES_LABEL}。围绕日常运维和专项治理，需要按照不同业务口径持续统计、更新各类台账，例如交叉跨越、防鸟、集中燃放点等，往往都要重新关联线路、杆塔、坐标及外部数据。传统方式主要依靠人工整理、逐项核对，既耗费大量人力，同一基础数据又在不同专项中反复处理，设备规模越大，重复工作越突出。")
    para(doc,f"业务过程数据同样持续增长。{ALARM_SCOPE}共形成{CFG['metrics']['alarm_workorders']:,}条告警工单、{CFG['metrics']['alarm_photos']:,}张现场反馈照片；巡视照片每月约{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张。数据跨线路、跨任务、跨时间积累，人工不仅难以逐一核验，更难与历史记录进行全量比对。以月度{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张巡视照片为例，若采用简单两两比较，理论组合约77.5万亿，依靠人工或简单穷举均无法支撑。")
    figure(doc,"province-map","图2　省域线路杆塔任务规模与电压等级分布",12.8)
    para(doc,"40.1万基杆塔、9200余条线路以及持续增长的千万级业务照片，使传统“增加人员、提高频次”的管理方式逐渐触及能力上限。继续增加人手只能有限提高处理量，需要建立一种不受人工规模直接约束的处理方式。")
    page_break(doc)
    # 5 根因
    h2(doc,"（四）根因分析：传统人工方式难以支撑全量管理")
    para(doc,"一是数据“能看不能算”。表格中虽然存在坐标、线路、照片等信息，但字段标准、顺序关系和异常处理并不统一，难以直接进行批量处理。二是业务经验“能做不能复用”。交跨如何判断、鸟害区域如何收敛、重复照片如何认定，规则长期存在于个人经验中。三是工具与流程脱节。即使发现重点对象或异常线索，如果不能与任务派发、现场核验、结果回写相衔接，也难以形成稳定的管理闭环。")
    para(doc,"归根到底，传统方式依靠人员数量和个人经验支撑业务，难以同时满足全量覆盖、统一标准和持续闭环三个要求。破解问题需要重新分工：适合机器完成的全量计算和重复劳动交给机器，有限的人力集中到现场核验、专业判断和管理闭环。")
    page_break(doc)
    # 6 模型
    h1(doc,"二、总体思路：构建“增效 + 提质”的外协数智管理模式")
    h2(doc,"（一）“增效管任务、提质管履职”双线协同")
    para(doc,"针对上述问题，我从输电运检实际业务出发，自主开展数据梳理、规则设计和程序开发，把空间计算用于任务筛选，把图像相似度识别用于照片查重，并归纳为“增效管任务、提质管履职”两条主线：任务侧由系统从全量对象中筛选重点，外协按清单精准核验；履职侧由系统对作业照片全量查重，管理人员重点复核疑似异常照片对。相关算法、计算程序和业务筛选流程均为自主设计、开发和验证成果。")
    figure(doc,"dual-wheel","图3　外协管理增效提质总体模型",14.4)
    para(doc,"整个模式可以概括为“两条主线、一个机制”：增效管任务、提质管履职；机器负责全量筛选，人员负责精准核验。通过重新划分人机职责，把人的精力从重复劳动转向专业判断。")
    page_break(doc)
    # 7 architecture
    h2(doc,"（二）外协数智管理的共用闭环")
    para(doc,"在双线模式基础上，本案例把计算结果直接接入任务组织、现场执行和主业复核流程。多源数据汇集后，系统按业务规则筛出重点任务并生成清单，外协人员按清单执行，主业复核结果再回写数据和规则，用于后续任务调整。")
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
    para(doc,"围绕“增效管任务”，最先解决的是交叉跨越排查。交叉跨越程序跑通后，线路空间数据和计算方法继续用于防鸟、集中燃放点等专项。三个场景的做法基本一致：程序先从全量对象中筛出重点，再由外协人员按清单现场核验。")
    para(doc,"一是建立可复用的数据底座。对既有杆塔和线路数据进行清洗，检查空坐标、重复点、离群点和杆号顺序，将相邻杆塔连接为线路段；同时对铁路、鸟类活动、燃放点和气象节假日等外部数据统一标准化，将分散数据整理为可直接计算、可供不同专项重复调用的任务底座。")
    para(doc,"二是把业务经验转化为可计算规则。在统一数据底座基础上，将“是否相交”“是否进入重点活动区域”“是否落入安全距离”等业务判断转化为空间叠加、风险分级和距离阈值，并编写对应计算逻辑，把个人经验固化为可重复执行的程序规则，批量生成重点核验清单。")
    para(doc,"三是以任务清单组织外协精准核验。候选点位和区段按风险、区域和任务类型整理为清单，定向推送给外协人员并规划巡视路线。外协上传现场结果，主业复核后回写状态，形成“自动筛选—定向执行—反馈复核—规则优化”的闭环。")
    para(doc,"完成线路、杆塔和外部数据整理后，不同专项可以直接调用同一套基础数据和计算规则。外协人员根据程序生成的清单开展现场核验，省去了从全量设备中逐项查找的过程。")
    page_break(doc)
    # 9 crossing
    h2(doc,"1.交叉跨越：包围盒预筛与精确几何求交")
    para(doc,"交叉跨越排查是这套数字化方法最早落地的业务场景。面对需要人员逐条线路、逐个区段查找的重要跨越信息，我利用既有全量杆塔坐标自主编写程序，将相邻杆塔连接形成线路空间模型，引入铁路、公路等地理要素，并设计“包围盒预筛＋精确几何求交”的批量计算方法，先快速排除明显无关对象，再对剩余对象进行精确求交。")
    figure(doc,"crossing","图5　交叉跨越自动筛查及候选分布",15.2)
    para(doc,"在某地市实际应用中，原需十余人、近两周完成的全量排查，程序数分钟即可完成，同时还补充识别出十余处此前人工排查遗漏的铁路、公路等重要跨越信息。")
    page_break(doc)
    # 10 bird
    h2(doc,"2.防鸟：公开生态资料与线路空间叠加")
    para(doc,"交叉跨越程序完成后，我又把同样的空间计算方法用到防鸟排查中。通过引入GBIF鸟类活动数据并结合公开生态资料，对鸟类活动记录进行空间汇总，再与输电线路叠加，筛出活动较集中以及湿地、水网、迁徙廊道等区域内需要重点核验的线路区段，为防鸟装置排查和差异化巡视生成任务清单。")
    figure(doc,"bird","图6　鸟类活动重点区域与输电线路空间叠加筛查",12.8)
    para(doc,"鸟类活动数据与输电线路叠加后，可以先筛出鸟类活动相对集中的线路区段，再安排外协人员现场核验。这样不需要沿线大范围摸排，防鸟装置排查和差异化巡视的任务范围也更明确。")
    page_break(doc)
    # 11 fireworks
    h2(doc,"3.集中燃放点：影响范围分析与周边杆塔批量筛查")
    para(doc,"2025年年底接到集中燃放点周边输电杆塔排查任务后，我直接复用前期形成的线路空间数据和距离计算方法，只调整距离参数和筛选规则，算上修改调试不到半小时即完成批量计算和清单输出。")
    figure(doc,"fireworks","图7　集中燃放点影响范围与周边杆塔筛查",12.8)
    para(doc,"程序一次计算即可给出集中燃放点周边需要核验的杆塔和线路清单，外协人员按清单到现场确认，不再逐个燃放点、逐基杆塔查询判断。交叉跨越、防鸟和集中燃放点虽然业务对象不同，但实际都采用“程序先筛、人员核验”的办法。")
    page_break(doc)
    # 12 quality problem
    h2(doc,"（二）提质：照片查重强化外协履职质量监督")
    para(doc,f"任务筛选解决的是“去哪查”，照片查重解决的是“是否真正查到位”。外协人员完成任务后要上传反馈照片，过去主要靠管理人员抽查。面对十万级乃至千万级历史照片，人工很难记住既往画面，也无法逐一比对。{ALARM_SCOPE}共形成{CFG['metrics']['alarm_workorders']:,}条告警工单和{CFG['metrics']['alarm_photos']:,}张现场反馈照片，这已经超出人工逐张核验的处理能力。")
    figure(doc,"photo-scale","图8　告警工单照片全量筛选与人工复核结果",15.2)
    para(doc,f"系统对{CFG['metrics']['alarm_photos']:,}张现场反馈照片进行全量筛选，形成{CFG['metrics']['alarm_candidates']:,}对疑似相似照片，其中{CFG['metrics']['alarm_reviewed']:,}对已完成人工复核，确认重复{CFG['metrics']['alarm_confirmed_pairs']:,}对、确认不同{CFG['metrics']['alarm_confirmed_different']:,}对，另有{CFG['metrics']['alarm_pending']:,}对待复核。管理人员不再需要在11万余张照片中逐张查找，只需重点查看约5千对候选。目前，告警工单反馈照片查重和巡视照片查重均已在省公司层面开展试点，并用于生产管控中心运检工作质量远程督查。")
    page_break(doc)
    # 13 innovation 1
    h2(doc,"1.从无到有建立告警工单照片查重")
    para(doc,"当时告警工单反馈照片没有可直接使用的全量查重手段。我先确定什么样的照片应进入疑似重复候选，再编写查重程序，设计机器筛选、原图对照和人工终审流程，并用真实业务样本反复校准参数。由此建立了告警工单照片全量查重方法。")
    figure(doc,"photo-cases","图9　真实复核案例：同图篡改水印日期与高相似但不同照片",12.2)
    para(doc,"图9上部三张照片主体、构图和现场细节一致，但水印日期分别显示为06-27、06-10和05-30，人工复核后确认属于同图修改水印日期后重复使用；下部两张照片虽然相似度达到97.63%，但车辆位置、吊臂姿态和现场物体存在真实变化，人工确认并非重复。全量查重把这些原本依靠人工记忆才能发现的问题先筛出来，再交给管理人员结合工单和现场情况判断。省公司实际督查中，还发现某500千伏特殊通道区段两次人工巡视使用重复照片，相关问题被认定为人工巡视不到位，并定性为较大运检质量问题。")
    page_break(doc)
    # 14 algorithm
    h2(doc,"2.构建pHash + CLIP双阶段筛选流程")
    para(doc,"为兼顾全量筛选效率和疑似重复识别能力，本案例设计并实现了基于pHash与CLIP的双阶段处理流程。第一阶段利用感知哈希pHash和汉明距离，以较低计算成本快速召回构图近似照片；第二阶段利用CLIP图像向量对候选进行语义相似度复核，识别经过裁剪、调色、旋转、局部消除后仍表达相同现场内容的照片。结合真实样本验证，现有告警工单规则采用“pHash＜10且CLIP＞0.80”生成候选。")
    para(doc,"分层候选生成主要包括以下四个步骤：",14,True,keep=True)
    bullet(doc,"图像标准化：统一尺寸、方向和颜色通道，降低格式差异。")
    bullet(doc,"pHash快速召回：用低成本结构指纹从全量照片中筛出近似候选。")
    bullet(doc,"CLIP语义复核：对候选进行更精细的场景和对象相似度比较。")
    bullet(doc,"双阈值筛选：同时满足结构与语义条件时进入人工复核队列。")
    para(doc,"人工复核与业务认定。系统将原图对比、相似度和关联业务信息集中呈现，复核人员结合拍摄时间、工单对象、现场细节和水印变化开展业务认定。通过分层筛选，大幅压缩需要人工查看的数据范围，使管理人员从海量照片逐张核对转向疑似异常照片对重点复核，提高质量监督效率。")
    page_break(doc)
    # 15 innovation 2
    h2(doc,"3.突破少量特高压限制，扩展到全电压等级")
    para(doc,"告警工单查重跑通后，我开始处理规模更大的巡视照片。此前由电力信息公司提供的既有照片查重能力主要覆盖少量特高压巡视照片，尚无法满足全电压等级海量照片的常态化筛查需求。扩展到全电压等级后，每月需要处理约1245万张巡视照片，理论两两组合约77.5万亿，原有处理方式无法直接放大。因此重新设计了候选生成、特征复用、分批调度、结果去重和断点续算等处理流程。")
    para(doc,"与原有处理范围相比，主要有三点变化：",14,True,keep=True)
    bullet(doc,"覆盖范围：从少量特高压扩展到全电压等级。")
    bullet(doc,"处理规模：从小规模照片筛查提升至每月1245万张。")
    bullet(doc,"运行方式：从单次处理转为可分批、可续算、可持续运行的规模化全量筛查。")
    para(doc,"完成上述改造后，查重范围从少量特高压照片扩展到全电压等级，目前能够按月处理约1245万张巡视照片。")
    page_break(doc)
    # 16 scale technical
    h2(doc,"4.建立千万级照片工程化处理能力")
    para(doc,"为支撑每月1245万张照片持续运行，计算路径采用“特征预计算—低成本候选召回—高成本语义复核”的分层方式，将实际计算集中到极小比例的候选数据上。")
    para(doc,"程序按批次处理照片，并保存已完成进度；任务中断后可以从上次位置继续。已经计算过的特征直接复用，不同批次的结果统一去重归并，以保证千万级数据可以持续处理。")
    para(doc,"查重程序只负责给出疑似照片对，最终是否属于重复使用仍由管理人员结合任务时间、作业对象、现场细节和业务要求判断。这样既能覆盖海量历史照片，又不会把算法相似度直接当作管理结论。")
    page_break(doc)
    # 17 effects
    h1(doc,"四、实施效果")
    h2(doc,"（一）增效：把外协全量排查变成精准核验")
    para(doc,"交叉跨越、防鸟和集中燃放点共用线路、杆塔及空间位置等基础数据，不同专项不再重复整理同一批资料。某地市重要跨越排查原需十余人、近两周，程序数分钟即可完成，并补充发现十余处此前人工遗漏的重要跨越信息；后续集中燃放点任务直接复用已有程序，调整参数后即可批量计算。")
    h2(doc,"（二）提质：把有限人工抽查变成全量质量监督")
    para(doc,f"告警工单照片查重从无到有，在{CFG['metrics']['alarm_photos']:,}张反馈照片中筛出{CFG['metrics']['alarm_candidates']:,}对疑似相似照片，目前已确认{CFG['metrics']['alarm_confirmed_pairs']:,}对重复照片。省公司试点同时覆盖告警工单反馈照片和巡视照片，累计发现并形成通报的照片重复类问题{CFG['metrics']['province_trial_duplicate_issues']}项，其中告警工单反馈照片重复{CFG['metrics']['province_trial_alarm_duplicate_issues']}项、人工巡视照片重复{CFG['metrics']['province_trial_patrol_duplicate_issues']}项；其中{CFG['metrics']['province_trial_major_special_corridor_issues']}项500千伏特殊通道人工巡视照片重复问题被定性为较大运检质量问题。巡视照片查重也已从原有少量特高压范围扩展到全电压等级，目前可按月处理约1245万张巡视照片。")
    h2(doc,"（三）管理方式：从人海式管理转向数智协同")
    para(doc,"交叉跨越、防鸟和集中燃放点可以共用线路空间数据和筛选程序，告警工单与巡视照片查重也采用同一套候选筛选思路。相关核心算法和程序均由我自主设计、开发和验证。告警工单反馈照片查重和巡视照片查重已经在省公司试点，发现的问题已多次进入省公司运检工作质量远程督查通报，说明这些程序已经用于实际管理，而不只是技术验证。后续可在统一数据接口和业务规则后向其他地市公司推广。")
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
    para(doc,"下一步结合省公司试点情况，把现场核验结果、设备变更信息和照片复核结论及时回写，并同步记录专项排查耗时、候选核验量和异常发现数量。推广前重点统一数据接口、规则参数和处理流程，再向其他地市公司复制应用。")
    h2(doc,"结语")
    para(doc,"这项工作最初只是为了解决一次交叉跨越排查，后来同一套空间计算方法又用到了防鸟和集中燃放点；照片查重也从告警工单扩展到了全电压等级巡视照片。回过头看，做法其实很明确：增效管任务、提质管履职，程序先处理全量数据，人再对筛出的重点对象作专业判断。对外协管理来说，真正减少的是重复查找和低效抽查，把有限的人力留给现场核验和问题处置。",14,True)
    OUT.parent.mkdir(parents=True,exist_ok=True);doc.save(OUT)
    print(f"[report] generated {OUT}")

if __name__=="__main__":build()
