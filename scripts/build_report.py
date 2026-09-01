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
    para(doc,"从日常工作看，外协任务并不只发生在现场。任务下达前，往往要先整理线路、杆塔、坐标、隐患和外部环境信息，确定哪些区段需要去、哪些点位需要查；任务完成后，还要查看反馈照片、核对工单内容、确认处置结果。前端任务筛选和后端履职核验都需要主业人员投入大量时间，这两部分工作共同决定了外协管理效率。")
    para(doc,"过去业务量较小时，这套方式依靠熟悉线路的人员还能运转。随着设备范围扩大、专项任务增多，同一批线路和杆塔资料被反复整理，不同人员又按照各自经验判断，管理人员很容易陷入查资料、核台账、看照片等重复工作。现场外协力量增加以后，如果后台任务组织和质量核验仍沿用原来的人工方式，管理端同样会成为瓶颈。")
    h2(doc,"（二）外协管理面临“工作量大、质量难保证”两大痛点")
    bullet(doc,"工作量大：一项专项排查任务往往需要从多类台账和海量设备中重新寻找目标。以交叉跨越、防鸟、集中燃放点等工作为例，需要反复关联线路、杆塔、坐标和外部信息，再由外协人员逐项查找、现场摸排。任务对象越多、范围越大，人员投入几乎同步增加，大量精力消耗在重复查询和全量排查上。")
    bullet(doc,f"质量难保证：外协履职涉及大量工单、现场反馈和长期积累的历史数据。仅{ALARM_SCOPE}的告警工单数量就超过11万条，同时还沉淀了大量现场反馈照片和历史处置记录。面对数量庞大、时间跨度长、跨工单分散存储的作业数据，管理人员很难依靠人工逐一核验，更难在历史数据中发现同一照片跨时间、跨工单重复使用等异常情况，传统抽查方式难以全面判断外协工作是否真实、规范、到位。")
    bullet(doc,"共同症结：任务侧依赖“人去找”，质量侧依赖“人去查”，管理能力基本随人员投入线性增长，而设备规模和业务数据已经进入规模化增长阶段。单纯增加人员已难以支撑，排查范围难收敛、历史数据难全量核验、业务经验难固化复用等问题日益突出。")
    figure(doc,"pain-points","图1　外协队伍管理面临的两大痛点",12.3)
    page_break(doc)
    # 4 现状量级
    h2(doc,"（三）数据规模决定了“人海作业”不可持续")
    para(doc,f"目前全省约有{CFG['metrics']['province_poles']/10000:.1f}万基输电杆塔、{PROVINCE_LINES_LABEL}。围绕日常运维和专项治理，需要按照不同业务口径持续统计、更新各类台账，例如交叉跨越、防鸟、集中燃放点等，往往都要重新关联线路、杆塔、坐标及外部数据。传统方式主要依靠人工整理、逐项核对，既耗费大量人力，同一基础数据又在不同专项中反复处理，设备规模越大，重复工作越突出。")
    para(doc,"这类排查通常包含多轮人工操作。先要确认线路名称和杆号顺序，再检查坐标是否缺失、重复或偏离；随后把外部目标与线路位置逐一对应，发现疑似点位后还要回到原始资料核对。交叉跨越需要查铁路、公路等地理要素，防鸟要叠加鸟类活动和生态环境信息，集中燃放点又需要按距离筛选周边杆塔。业务规则不同，但前面的数据整理工作高度重复。")
    para(doc,f"业务过程数据同样持续增长。{ALARM_SCOPE}共形成{CFG['metrics']['alarm_workorders']:,}条告警工单、{CFG['metrics']['alarm_photos']:,}张现场反馈照片；巡视照片每月约{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张。数据跨线路、跨任务、跨时间积累，人工不仅难以逐一核验，更难与历史记录进行全量比对。以月度{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张巡视照片为例，若采用简单两两比较，理论组合约77.5万亿，依靠人工或简单穷举均无法支撑。")
    figure(doc,"province-map","图2　省域线路杆塔任务规模与电压等级分布",12.8)
    para(doc,"40.1万基杆塔、9200余条线路以及持续增长的千万级业务照片，使传统“增加人员、提高频次”的管理方式逐渐触及能力上限。继续增加人手只能有限提高处理量，需要建立一种不受人工规模直接约束的处理方式。")
    page_break(doc)
    # 5 根因
    h2(doc,"（四）根因分析：传统人工方式难以支撑全量管理")
    para(doc,"一是数据“能看不能算”。表格里已经有线路、杆塔、坐标、照片等信息，但来源不同、字段写法不同，杆号顺序和坐标质量也并不一致。人工查看单条记录时问题不大，一旦需要批量计算，相同对象如果名称不统一、坐标异常没有处理，结果就会出现漏算或错算。因此，真正开始计算前，必须先把业务数据整理成程序能够稳定读取的结构。")
    para(doc,"二是业务经验“能做不能复用”。长期从事线路运维的人员知道怎样判断重要跨越、哪些环境容易发生鸟害、什么样的照片值得重点核对，但这些判断往往停留在个人经验和临时表格里。人员变化、任务变化以后，许多步骤又要重新摸索。把经验拆成明确条件并写进程序，才能在不同线路和不同专项中按同一标准重复执行。")
    para(doc,"三是工具与流程没有完全接上。程序算出一个点位或一对相似照片，只完成了第一步。点位还需要有人去现场确认，照片还需要结合时间、工单和现场细节判断，确认后的结论还要回到任务管理中。计算结果如果停留在单独文件里，业务人员仍要二次整理，实际管理效果会受到很大影响。")
    para(doc,"因此，本案例把重点放在两件事情上：一方面让程序承担适合批量处理的计算和筛选工作，另一方面保留人工对现场真实性、专业风险和处置结果的判断。这样既能扩大覆盖范围，也能保证最后的管理结论由业务人员负责。")
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
    para(doc,"这套流程对人和程序的职责作了明确区分。程序负责处理数量大、重复性强、规则相对明确的工作，例如空间求交、距离筛选、相似照片召回；外协人员负责现场核验和任务执行；主业人员负责风险判断、结果确认和问题处置。程序输出只作为任务线索和复核入口，不直接替代专业结论。")
    para(doc,"实际使用中，数据质量和规则口径同样重要。杆塔位置变化、线路改造、外部环境更新后，基础数据需要同步更新；现场核验发现规则过宽或过窄时，也要调整筛选条件。这样，前一次任务留下的数据和复核结果可以直接服务下一次任务，减少重复整理。")
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
    para(doc,"早期一次实际数据整理中，纳入计算的基础数据包含6438个杆塔坐标、249条线路，既有资料中记录了241处铁路跨越结果。人工排查时，需要先按线路逐段查看，再把地图上的铁路、公路位置与杆塔区段对应起来。线路数量一多，单纯依赖翻表和地图浏览很容易出现重复查看，也容易遗漏位置不明显的跨越点。")
    para(doc,"程序开发过程中，首先解决的是线路如何正确连接。杆塔坐标只有点，必须根据线路和杆号顺序连接成线段；遇到缺失坐标、重复点和明显离群点时，需要先标记并排除。随后再处理外部地理要素，把线路段与铁路、公路放到统一坐标体系中。为了减少无效计算，先用包围盒判断两条线段是否可能接近，只有可能相交的组合才进入精确几何求交。")
    figure(doc,"crossing","图5　交叉跨越自动筛查及候选分布",15.2)
    para(doc,"在某地市实际应用中，原需十余人、近两周完成的全量排查，程序数分钟即可完成，同时还补充识别出十余处此前人工排查遗漏的铁路、公路等重要跨越信息。")
    para(doc,"程序输出后先生成候选清单，由熟悉线路的人员结合图形位置和现场情况复核，确认后的点位再进入正式管理。这个过程也暴露出一批基础数据问题，例如杆号顺序异常、坐标偏移和外部地图要素名称不统一。把这些问题修正以后，同一套线路空间数据能够继续用于后面的防鸟和燃放点筛选。")
    page_break(doc)
    # 10 bird
    h2(doc,"2.防鸟：公开生态资料与线路空间叠加")
    para(doc,"交叉跨越程序完成后，我又把同样的空间计算方法用到防鸟排查中。通过引入GBIF鸟类活动数据并结合公开生态资料，对鸟类活动记录进行空间汇总，再与输电线路叠加，筛出活动较集中以及湿地、水网、迁徙廊道等区域内需要重点核验的线路区段，为防鸟装置排查和差异化巡视生成任务清单。")
    figure(doc,"bird","图6　鸟类活动重点区域与输电线路空间叠加筛查",12.8)
    para(doc,"鸟类活动数据与输电线路叠加后，可以先筛出鸟类活动相对集中的线路区段，再安排外协人员现场核验。这样不需要沿线大范围摸排，防鸟装置排查和差异化巡视的任务范围也更明确。")
    para(doc,"鸟类数据本身具有采集时间、地点分布不均等特点，因此程序只用于缩小排查范围，不把公开记录直接等同于现场风险。实际筛选时，还要结合湿地、水网、迁徙廊道等环境信息综合判断，再把候选区段交给现场核验。现场发现的鸟巢、防鸟装置状态和周边环境情况可以反过来修正后续任务范围。")
    para(doc,"这一场景的重要意义在于验证了线路空间数据的通用性。交叉跨越关注线路与铁路、公路是否相交，防鸟关注线路是否位于鸟类活动相对集中的区域，两项工作的业务规则完全不同，但底层都依赖线路位置和空间关系计算，因此不需要重新整理一套线路基础数据。")
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
    para(doc,"实际筛查中，重复照片的表现形式并不完全相同。有的是相邻日期直接上传同一张照片，有的是不同工单之间重复使用，还有的会修改水印时间、裁剪边缘或调整颜色后再次提交。同时也存在看起来很像、但现场确实发生变化的照片，例如车辆位置、吊臂姿态或作业对象发生了变化。正因为存在这些情况，程序只负责把疑似照片对找出来，人工复核环节不能省略。")
    para(doc,"复核时需要同时查看两张原图、拍摄时间、所属线路、工单对象和现场细节。对告警工单，还要确认反馈照片是否能够真实反映当次隐患核实和处置情况；对巡视照片，则要判断照片是否对应当次巡视区段和时间。只有完成这些业务核对后，才能认定是否属于重复使用。")
    page_break(doc)
    # 13 innovation 1
    h2(doc,"1.从无到有建立告警工单照片查重")
    para(doc,"当时告警工单反馈照片没有可直接使用的全量查重手段。我先确定什么样的照片应进入疑似重复候选，再编写查重程序，设计机器筛选、原图对照和人工终审流程，并用真实业务样本反复校准参数。由此建立了告警工单照片全量查重方法。")
    figure(doc,"photo-cases","图9　真实复核案例：同图篡改水印日期与高相似但不同照片",12.2)
    para(doc,"图9上部三张照片主体、构图和现场细节一致，但水印日期分别显示为06-27、06-10和05-30，人工复核后确认属于同图修改水印日期后重复使用；下部两张照片虽然相似度达到97.63%，但车辆位置、吊臂姿态和现场物体存在真实变化，人工确认并非重复。全量查重把这些原本依靠人工记忆才能发现的问题先筛出来，再交给管理人员结合工单和现场情况判断。省公司实际督查中，还发现某500千伏特殊通道区段两次人工巡视使用重复照片，相关问题被认定为人工巡视不到位，并定性为较大运检质量问题。")
    para(doc,"这项特殊通道问题具有较强代表性。特殊通道本身需要更高频次、更可靠的巡视记录，照片重复意味着系统里虽然留下了两次巡视记录，但其中至少一次记录不能真实反映当时通道情况。照片查重把两次相隔时间的记录自动关联起来，管理人员再结合巡视任务和线路区段确认问题，使原先依赖抽查和记忆发现的异常具备了稳定的筛查入口。")
    para(doc,"省公司试点以后，查重结果已经进入日常管理流程。累计形成通报的19项照片重复类问题中，11项来自告警工单反馈照片，8项来自人工巡视照片。问题来源覆盖不同任务类型，说明照片复用并非单一场景现象，也说明把历史照片放在同一套筛查规则下比较具有实际管理价值。")
    page_break(doc)
    # 14 algorithm
    h2(doc,"2.构建pHash + CLIP双阶段筛选流程")
    para(doc,"为兼顾全量筛选效率和疑似重复识别能力，本案例设计并实现了基于pHash与CLIP的双阶段处理流程。第一阶段利用感知哈希pHash和汉明距离，以较低计算成本快速召回构图近似照片；第二阶段利用CLIP图像向量对候选进行语义相似度复核，识别经过裁剪、调色、旋转、局部消除后仍表达相同现场内容的照片。结合真实样本验证，现有告警工单规则采用“pHash＜10且CLIP＞0.80”生成候选。")
    para(doc,"阈值确定时重点考虑两类风险。阈值过严会漏掉经过裁剪、压缩或修改水印的重复照片；阈值过宽又会把大量正常相似照片推给人工，失去筛选意义。因此，参数通过真实工单样本反复查看误报和漏报情况进行校准，并把候选量控制在人工能够复核的范围内。")
    para(doc,"pHash更关注画面整体结构，速度快，适合承担第一轮筛选；CLIP对画面语义和主体内容的表达更稳定，适合对候选进行第二轮判断。两者结合后，可以先用低成本方法缩小范围，再把计算资源集中到少量更值得检查的照片对上。")
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
    para(doc,"1245万张照片如果直接两两比较，理论组合约77.5万亿。这个数量级下，提高单次比较速度只能解决很小一部分问题，核心是减少真正进入精细比对的照片组合。程序先为每张照片计算一次可复用特征，再根据低成本特征寻找候选，只有候选才进入后续语义比较。已经处理过的照片特征保存下来，后续任务直接读取，避免重复计算。")
    para(doc,"千万级数据还带来运行可靠性问题。一次任务可能持续较长时间，如果中途因机器重启、网络中断或单批数据异常而从头开始，实际使用成本会很高。因此程序把任务拆成稳定批次，每批结束后记录进度和结果；出现异常时只重跑受影响批次，已完成部分继续保留。")
    para(doc,"程序按批次处理照片，并保存已完成进度；任务中断后可以从上次位置继续。已经计算过的特征直接复用，不同批次的结果统一去重归并，以保证千万级数据可以持续处理。")
    para(doc,"查重程序只负责给出疑似照片对，最终是否属于重复使用仍由管理人员结合任务时间、作业对象、现场细节和业务要求判断。这样既能覆盖海量历史照片，又不会把算法相似度直接当作管理结论。")
    page_break(doc)
    # 17 effects
    h1(doc,"四、实施效果")
    h2(doc,"（一）增效：把外协全量排查变成精准核验")
    para(doc,"交叉跨越、防鸟和集中燃放点共用线路、杆塔及空间位置等基础数据，不同专项不再重复整理同一批资料。某地市重要跨越排查原需十余人、近两周，程序数分钟即可完成，并补充发现十余处此前人工遗漏的重要跨越信息；后续集中燃放点任务直接复用已有程序，调整参数后即可批量计算。")
    para(doc,"从人员分工看，原来外协人员拿到的是大范围排查要求，需要花时间找目标、查位置、判断是否需要到现场；现在先由程序生成候选清单，外协人员主要负责现场确认。主业人员也减少了反复整理基础资料的工作，可以把时间放在候选复核、风险判断和问题处置上。")
    h2(doc,"（二）提质：把有限人工抽查变成全量质量监督")
    para(doc,f"告警工单照片查重从无到有，在{CFG['metrics']['alarm_photos']:,}张反馈照片中筛出{CFG['metrics']['alarm_candidates']:,}对疑似相似照片，目前已确认{CFG['metrics']['alarm_confirmed_pairs']:,}对重复照片。省公司试点同时覆盖告警工单反馈照片和巡视照片，累计发现并形成通报的照片重复类问题{CFG['metrics']['province_trial_duplicate_issues']}项，其中告警工单反馈照片重复{CFG['metrics']['province_trial_alarm_duplicate_issues']}项、人工巡视照片重复{CFG['metrics']['province_trial_patrol_duplicate_issues']}项；其中{CFG['metrics']['province_trial_major_special_corridor_issues']}项500千伏特殊通道人工巡视照片重复问题被定性为较大运检质量问题。巡视照片查重也已从原有少量特高压范围扩展到全电压等级，目前可按月处理约1245万张巡视照片。")
    para(doc,"管理方式也发生了实际变化。过去照片问题主要靠抽查，能否发现重复很大程度取决于抽查范围以及人员是否见过历史照片。现在进入筛查范围的照片都先经过程序比对，再由人工集中处理候选。19项问题能够进入省公司通报，说明查重结果已经直接服务于履职质量监督。")
    h2(doc,"（三）管理方式：从人海式管理转向数智协同")
    para(doc,"交叉跨越、防鸟和集中燃放点可以共用线路空间数据和筛选程序，告警工单与巡视照片查重也采用同一套候选筛选思路。相关核心算法和程序均由我自主设计、开发和验证。告警工单反馈照片查重和巡视照片查重已经在省公司试点，发现的问题已多次进入省公司运检工作质量远程督查通报，说明这些程序已经用于实际管理。")
    para(doc,"这套方法推广时不依赖新增现场硬件。线路、杆塔、工单和照片都是现有业务数据，其他地市主要需要统一字段、坐标格式和任务规则，再根据本地业务要求配置筛选参数。空间筛选和照片查重的程序主体可以直接复用，减少重复开发。")
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
    para(doc,"下一步结合省公司试点情况，把现场核验结果、设备变更信息和照片复核结论及时回写，并同步记录专项排查耗时、候选核验量和异常发现数量。推广前重点统一数据接口、规则参数和处理流程，再向其他地市公司推广应用。")
    para(doc,"推广前要明确线路、杆塔、坐标和外部数据的更新责任，并固定照片候选生成、人工复核和问题反馈流程。已经确认的正常相似照片和异常样本保留复核结果，供后续参数校准。")
    para(doc,"推广后的评价以实际工作结果为主。任务侧统计候选数量、现场核验量和人工耗时，质量侧统计候选照片对、确认问题数量和复核工作量，再根据这些数据调整规则。")
    h2(doc,"结语")
    para(doc,"这项工作最初只是为了解决一次交叉跨越排查，后来同一套空间计算方法又用到了防鸟和集中燃放点；照片查重也从告警工单扩展到了全电压等级巡视照片。回过头看，做法其实很明确：增效管任务、提质管履职，程序先处理全量数据，人再对筛出的重点对象作专业判断。对外协管理来说，真正减少的是重复查找和低效抽查，把有限的人力留给现场核验和问题处置。",14,True)
    OUT.parent.mkdir(parents=True,exist_ok=True);doc.save(OUT)
    print(f"[report] generated {OUT}")

if __name__=="__main__":build()
