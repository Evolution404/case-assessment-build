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
FIG=ROOT/".build/visuals"
CFG=json.loads((ROOT/"content/case.json").read_text(encoding="utf-8"))
CASE_ID=os.environ.get("CASE_ID",CFG["case_id_default"])
# SimSun is present on both the local Word installation and the headless
# LibreOffice renderer.  FangSong_GB2312 looks correct in Word but loses CJK
# glyphs in headless PDF export, so use the more portable document body font.
FONT="SimSun"

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

def h1(doc,text):return para(doc,text,14,True,indent=False,before=4,after=4,keep=True)
def h2(doc,text):return para(doc,text,14,True,indent=False,before=2,after=2,keep=True)
def bullet(doc,text):return para(doc,"● "+text,13.5,False,indent=False,after=1,line=25)

def figure(doc,name,caption,width=15.0):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(0)
    p.add_run().add_picture(str(FIG/f"{name}.png"),width=Cm(width))
    c=doc.add_paragraph();c.alignment=WD_ALIGN_PARAGRAPH.CENTER;c.paragraph_format.space_after=Pt(5)
    set_run(c.add_run(caption),10.5,False,"555555")

def page_break(doc):doc.add_page_break()

def footer(doc):
    sec=doc.sections[0];p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    fld=OxmlElement("w:fldSimple");fld.set(qn("w:instr"),"PAGE");p._p.append(fld)
    for r in p.runs:set_run(r,10,False,"666666")

def add_summary_table(doc):
    tbl=doc.add_table(rows=3,cols=3);tbl.alignment=WD_TABLE_ALIGNMENT.CENTER;tbl.autofit=False
    widths=[Cm(3.4),Cm(5.7),Cm(5.7)]
    rows=[("双轮","增效轮","提质轮"),("场景","交叉跨越、防鸟、集中燃放点","告警工单、巡视照片查重"),("目标","机器批量计算，人员精准核验","照片全量比对，履职质量可验证")]
    for ri,row in enumerate(tbl.rows):
        for ci,cell in enumerate(row.cells):
            cell.width=widths[ci];cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.text="";p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            set_run(p.add_run(rows[ri][ci]),11.5,ri==0 or ci==0,"FFFFFF" if ri==0 else "000000")
            tcpr=cell._tc.get_or_add_tcPr();shd=OxmlElement("w:shd");shd.set(qn("w:fill"),"27333A" if ri==0 else ("E9E3D9" if ci==0 else "F7F3EC"));tcpr.append(shd)

def build():
    doc=Document(str(TEMPLATE));wipe_body(doc)
    sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(2.35);sec.bottom_margin=Cm(2.2);sec.left_margin=Cm(2.7);sec.right_margin=Cm(2.7)
    footer(doc)
    # 1 封面
    para(doc,"个人案例考核报告",16,False,WD_ALIGN_PARAGRAPH.CENTER,False,before=52,after=32,line=30,color="666666")
    para(doc,CFG["title"],24,True,WD_ALIGN_PARAGRAPH.CENTER,False,after=10,line=38)
    para(doc,"——"+CFG["subtitle"],18,False,WD_ALIGN_PARAGRAPH.CENTER,False,after=40,line=32)
    para(doc,"增效：交叉跨越 · 防鸟 · 集中燃放点",14,True,WD_ALIGN_PARAGRAPH.CENTER,False,after=8,color="C76142")
    para(doc,"提质：告警工单查重 · 巡视照片查重",14,True,WD_ALIGN_PARAGRAPH.CENTER,False,after=54,color="6D8063")
    para(doc,CASE_ID,14,False,WD_ALIGN_PARAGRAPH.CENTER,False)
    page_break(doc)
    # 2 摘要
    h1(doc,"摘要")
    para(doc,"输电运检外协工作长期面临两类矛盾：一类是交叉跨越、防鸟、集中燃放点等空间排查任务对象多、范围广，传统方式依赖人海摸排；另一类是告警工单和巡视照片规模巨大，人工抽查难以有效验证照片真实性和巡视履职质量。围绕上述问题，本案例从业务现场出发，将杆塔坐标、公开地理图层和海量业务照片转化为机器可计算的数据底座，形成增效与提质两条数字化路径。")
    para(doc,"增效方面，构建线线求交、点面聚类、点线缓冲三类空间分析能力，使外协人员从全量排查转向按候选清单重点核验。提质方面，从无到有独立完成告警工单照片查重，并通过算法与工程流程创新，将少量特高压照片筛查扩展到全电压等级，实现每月1245万张巡视照片的规模化查重。")
    add_summary_table(doc)
    para(doc,"关键词：外协队伍；数智协同；空间计算；照片查重；提质增效",11.5,False,indent=False,before=8)
    page_break(doc)
    # 3 背景
    h1(doc,"一、背景、问题、现状")
    h2(doc,"（一）外协力量已成为输电运检的重要延伸")
    para(doc,"随着设备规模扩大、运检任务增加以及专业人员结构性紧张，巡视、隐患排查、现场值守、工单处置和台账采集等工作越来越多地需要外协力量参与。外协工作覆盖的线路长、点位多、任务频次高，任何一个环节的效率或质量问题都会沿生产流程放大。")
    para(doc,"传统管理习惯把问题归结为“人员是否认真”，但深入分析后可以发现，很多低效和质量问题首先是工具能力不足：全量空间排查只能靠脚底板，千万级照片只能做有限抽查。仅靠增加人员、提高频次，既难以持续，也不能形成稳定、可复核的结果。")
    h2(doc,"（二）两类问题需要两种数字能力")
    bullet(doc,"效率问题：空间对象分散、排查范围大，人员大量时间消耗在查找和核对上。")
    bullet(doc,"质量问题：照片数量远超人工审核能力，重复上传和处理造假往往依靠偶然发现。")
    bullet(doc,"共同问题：数据、规则和经验未沉淀为可重复执行的程序能力。")
    page_break(doc)
    # 4 现状量级
    h2(doc,"（三）数据规模决定了“人海作业”不可持续")
    para(doc,f"杆塔台账包含约{CFG['metrics']['province_poles']/10000:.1f}万基杆塔、{CFG['metrics']['province_lines']}条线路。若依赖人工逐段判断交叉跨越、逐点核对燃放风险、逐片研判鸟害区域，工作量会随设备规模同步增长。更关键的是，不同专项往往重复整理相同坐标，数据没有形成可复用底座。")
    para(doc,f"照片侧的规模矛盾更为突出。告警工单照片约{CFG['metrics']['alarm_photos']/10000:.1f}万张，巡视照片每月达到{CFG['metrics']['patrol_photos_monthly']/10000:.0f}万张。后者理论两两组合约77.5万亿种，任何依赖人工或简单穷举的方案都无法运行。")
    figure(doc,"province-map","图1　全省杆塔数据规模与脱敏演示范围",15.2)
    para(doc,"说明：图中线路仅用于展示省域覆盖和数据密度，已进行匿名化、强扰动、量化与抽样，不对应任何真实线路。",10.5,False,indent=False,line=20,color="666666")
    page_break(doc)
    # 5 根因
    h2(doc,"（四）根因分析：缺的不是更多人，而是可计算的方法")
    para(doc,"一是数据“能看不能算”。表格中虽然存在坐标、线路、照片等信息，但字段标准、顺序关系和异常处理并不统一，机器无法直接批量计算。二是业务经验“能做不能复用”。交跨如何判断、鸟害区域如何收敛、重复照片如何认定，规则长期存在于个人经验中。三是工具与流程脱节。程序即使输出结果，如果没有人工复核、任务派发、整改回写，仍然不能转化为管理成效。")
    para(doc,"本案例的破题方向不是建设一个孤立系统，而是把数据、规则、计算、复核和闭环连接起来。空间分析首先服务增效，照片全量比对首先服务提质，二者共同形成数智协同。")
    figure(doc,"outcomes","图2　从人海作业到数智协同的工作方式变化",15.2)
    page_break(doc)
    # 6 模型
    h1(doc,"二、内涵介绍")
    h2(doc,"（一）“增效—提质”双轮驱动")
    para(doc,"增效轮解决“海量空间排查任务如何处理得动”。机器依据坐标和空间规则批量生成候选，人员只对候选项进行现场确认。提质轮解决“照片真实性和巡视履职如何验证”。机器对海量照片进行全量筛选，人员对少量高价值候选作最终认定。")
    figure(doc,"dual-wheel","图3　增效与提质双轮模型",15.2)
    para(doc,"两个轮子共享一个轴心：标准化数据、明确规则、批量计算、人工复核和结果沉淀。增效不是单纯追求快，提质也不是简单增加处罚，而是用技术把人的精力重新配置到真正需要专业判断的环节。")
    page_break(doc)
    # 7 architecture
    h2(doc,"（二）数智协同的五层架构")
    figure(doc,"architecture","图4　数据到闭环的技术架构",15.2)
    bullet(doc,"数据底座：统一坐标、线路关系、公开地理图层和照片输入。")
    bullet(doc,"规则引擎：把相交、距离、密度、相似度等业务判断转成计算条件。")
    bullet(doc,"批量计算：以空间预筛和分层候选召回压缩计算范围。")
    bullet(doc,"人工复核：机器输出候选而非直接代替专业结论。")
    bullet(doc,"闭环沉淀：结果回写清单，规则和方法供下一次任务复用。")
    para(doc,"这套架构也是个人创新能够扩展的关键：改变数据对象和规则参数，可以从空间排查迁移到照片查重；改变照片规模和电压范围，又可以从告警工单迁移到全电压等级巡视照片。")
    page_break(doc)
    # 8 efficiency overview
    h1(doc,"三、具体做法")
    h2(doc,"（一）增效轮：同一坐标底座复用三类规则")
    para(doc,"空间排查的共同输入是杆塔坐标和线路拓扑，差异只在规则：交叉跨越是线与线求交，防鸟是点聚类形成重点区域后与线路叠加，集中燃放点是点与线路计算距离。将三个场景统一后，坐标清洗、线路排序、异常检查、结果制图和清单输出均可复用。")
    figure(doc,"spatial-compare","图5　交叉跨越、防鸟、燃放点的规则复用",15.2)
    para(doc,"技术处理首先检查空坐标、重复点、离群点和杆号顺序，再将相邻杆塔连接为线段。计算结果统一输出匿名候选点或候选区段，现场人员按照清单核验，不在演示文件中保存真实坐标。")
    page_break(doc)
    # 9 crossing
    h2(doc,"1.交叉跨越：包围盒预筛与精确几何求交")
    para(doc,"若把所有输电线段与全部铁路要素逐一比较，计算量会随两类线段数量相乘。为提高效率，先为每条线段生成最小包围盒，只保留包围盒存在重叠可能的组合；随后进行精确线段求交，计算候选交点。该方法把大量明显不相交的对象挡在精确计算之前。")
    figure(doc,"crossing","图6　全省交叉跨越脱敏演示",15.2)
    para(doc,"候选结果需要经过线路拓扑检查和人工确认。程序负责不遗漏地扫过全部对象，人员负责判断支线连接关系、图层误差和现场实际情况，最终形成可派发、可核验的清单。")
    page_break(doc)
    # 10 bird
    h2(doc,"2.防鸟：密度聚类与凸包收敛重点区域")
    para(doc,"鸟害风险不是简单围绕单点画圆。样本中既可能存在稳定聚集区，也可能存在孤立噪声点。本案例采用密度思路识别空间聚集：在给定邻域和最小样本条件下形成簇，孤立点保留为待复核噪声；再对每个簇计算凸包，将零散点收敛成可与线路叠加的重点区域。")
    figure(doc,"bird","图7　鸟害样本聚类与重点区域演示",15.2)
    para(doc,"该处理使外协人员不必在全线平均投入力量，而是优先关注进入重点区域的区段。演示中的鸟害点为脱敏仿真样本，只用于说明算法，不作为实际风险清单。")
    page_break(doc)
    # 11 fireworks
    h2(doc,"3.集中燃放点：N米缓冲与周边杆塔批量筛查")
    para(doc,"集中燃放点排查本质上是点到线路或杆塔的距离问题。程序以每个燃放点生成N米缓冲区，利用包围盒先筛出周边对象，再计算精确距离。落入阈值范围的杆塔形成候选清单，外协人员结合现场地形、风向、障碍物和实际管控要求复核。")
    figure(doc,"fireworks","图8　集中燃放点缓冲分析演示",15.2)
    para(doc,"三个增效场景共同实现了工作方式转换：过去是外协人员先全量寻找、再判断风险；现在是机器先批量算出候选、人员再精准核验。效率提升来自排查范围的收敛，而不是降低现场确认标准。")
    page_break(doc)
    # 12 quality problem
    h2(doc,"（二）提质轮：照片真实性由抽查走向全量验证")
    para(doc,"外协人员提交的告警工单和巡视照片，是证明现场处置、巡视到位的重要依据。人工审核通常关注照片是否清晰、回复是否完整，却难以记住大量历史画面。历史照片再次上传、裁剪调色、旋转扭曲或局部消除后，肉眼抽查更难发现。")
    para(doc,"照片查重的质量价值不在于找出两张完全相同的文件，而在于识别“现场构图和业务对象高度相似、但文件已经被处理”的疑似复用行为。程序必须同时考虑低层视觉结构与高层语义，再由人员结合工单和巡视任务作最终认定。")
    figure(doc,"photo-compare","图9　去除敏感水印后的重复照片演示样本",15.2)
    page_break(doc)
    # 13 innovation 1
    h2(doc,"1.创新一：从无到有独创告警工单照片查重")
    para(doc,"此前告警工单照片缺少面向全量数据的重复核查手段。本案例由本人从0到1完成：先明确什么情况属于疑似重复，梳理历史照片复用和图像处理方式；再设计机器筛选与人工认定流程；最后用真实业务样本反复校准阈值，形成可执行的查重方法。")
    figure(doc,"dedup-funnel","图10　告警工单照片查重筛选漏斗",15.2)
    para(doc,f"在{CFG['metrics']['alarm_photos']/10000:.1f}万张告警工单照片中，机器生成{CFG['metrics']['alarm_candidates']}对候选，经人工复核认定{CFG['metrics']['alarm_confirmed_pairs']}对真实重复，候选命中率约{CFG['metrics']['alarm_candidate_hit_rate']}%。这一漏斗说明机器没有代替认定，而是把人工注意力集中到最值得看的少量候选。")
    page_break(doc)
    # 14 algorithm
    h2(doc,"2.双阶段算法：pHash快速召回，CLIP语义复核")
    para(doc,"第一阶段计算感知哈希pHash，将图像压缩为反映整体结构的短指纹，以汉明距离快速发现构图近似的照片。第二阶段使用CLIP图像向量计算语义相似度，识别经过裁剪、调色、旋转、局部消除后仍然表达相同现场内容的照片。现有告警工单规则采用“pHash＜10且CLIP＞0.80”生成候选。")
    figure(doc,"dedup-pipeline","图11　照片查重分层候选生成流程",15.2)
    para(doc,"分层设计的核心是避免直接穷举全部组合。照片先标准化和计算特征，再在近似候选空间中进行更精细比较；处理结果按批次归并并支持断点续算。最后保留原图对比、相似度和业务信息供人工终审。")
    page_break(doc)
    # 15 innovation 2
    h2(doc,"3.创新二：突破少量特高压限制，扩展到全电压等级")
    para(doc,"既有照片查重能力只能处理极少量特高压巡视照片，无法支撑全电压等级和千万级数据规模。问题不只是算力不足，更在于比较空间随照片数量快速膨胀，简单两两比较无法运行。本人围绕候选生成、分批调度、特征复用、结果去重和断点续算重构处理流程，显著降低无效比较。")
    figure(doc,"scale","图12　从少量特高压到全电压等级的能力突破",15.2)
    para(doc,"电力信息公司没搞定的千万级照片查重，我搞定了。这不是一句口号，而是能力边界的实质变化：筛查对象从少量特高压照片扩展到全电压等级，月度处理规模达到1245万张。")
    page_break(doc)
    # 16 scale technical
    h2(doc,"4.千万级工程化处理：让算法真正跑得动")
    para(doc,"1245万张照片理论上包含约77.5万亿种两两组合。若全部计算，即使单次比较极快，也无法在可接受时间内完成。本案例先生成可复用特征，再利用低成本特征快速召回候选，对候选执行高成本语义复核，从而将计算集中到极小比例的数据上。")
    para(doc,"工程流程按照稳定批次运行，每批记录输入范围、特征状态、候选数量和输出校验值；发生中断后从已完成批次继续，避免重复计算。不同批次结果归并时依据匿名标识去重，最终输出候选对、相似度、复核状态和问题闭环字段。")
    h2(doc,"技术边界与人工责任")
    bullet(doc,"相似度高不等于业务违规，必须结合任务时间、对象和现场要求认定。")
    bullet(doc,"算法阈值需通过真实样本校准，并持续关注漏检和误报。")
    bullet(doc,"照片查重用于质量核查，不公开传播原始照片和人员信息。")
    bullet(doc,"模型负责给出证据线索，最终结论和处置责任仍由专业人员承担。")
    page_break(doc)
    # 17 effects
    h1(doc,"四、实施效果")
    h2(doc,"（一）增效：把全量排查变成候选核验")
    para(doc,"交叉跨越、防鸟和集中燃放点由同一坐标底座驱动，专项任务不再重复整理数据。程序在全量对象中批量筛选候选，外协人员围绕候选区段开展现场核实，工作重心从“到处找”转向“精准查”。")
    h2(doc,"（二）提质：把偶然发现变成全量验证")
    para(doc,"告警工单查重从无到有，巡视照片查重从少量特高压扩展到全电压等级。月度1245万张照片具备规模化筛查能力，重复上传、历史照片复用和图像处理不再只能依靠人工偶然发现。")
    h2(doc,"（三）个人能力：从解决一个问题到沉淀一套方法")
    para(doc,"本案例的核心成果不仅是五个演示场景，更是业务人员自主定义规则、理解数据、设计验证、推动落地的完整路径。空间底座可以继续扩展到其他风险图层，照片特征与候选流程也可以复用到其他图像质量核查任务。")
    figure(doc,"outcomes","图13　数智协同前后的工作方式对比",15.2)
    page_break(doc)
    # 18 recommendations
    h1(doc,"五、推广应用建议")
    h2(doc,"1.数据底账先行")
    para(doc,"统一坐标、线路顺序、照片标识和任务关联字段，明确数据质量责任，为批量计算提供稳定输入。")
    h2(doc,"2.能力模块化沉淀")
    para(doc,"将求交、缓冲、聚类、pHash、CLIP和人工复核界面拆分为可组合模块，使新的专项任务能够复用已有能力。")
    h2(doc,"3.坚持机器初筛、人工终审")
    para(doc,"程序追求全量覆盖和高效召回，人员负责业务真实性判断和处置闭环，避免把算法相似度直接等同于管理结论。")
    h2(doc,"4.建立脱密演示与生产数据隔离机制")
    para(doc,"生产计算与答辩演示彻底分离。演示只使用省级汇总、匿名画布坐标和去除水印的样本，不保存真实线路、杆号、经纬度、工单号和人员信息。")
    h2(doc,"结语")
    para(doc,CFG["thesis"]+" 从人海作业到数智协同，真正改变的不是某一个工具，而是业务人员解决问题、验证结果和沉淀能力的方式。",14,True)
    OUT.parent.mkdir(parents=True,exist_ok=True);doc.save(OUT)
    print(f"[report] generated {OUT}")

if __name__=="__main__":build()
