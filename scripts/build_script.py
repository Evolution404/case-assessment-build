#!/usr/bin/env python3
import json,os
from pathlib import Path
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/"content/case.json").read_text(encoding="utf-8"));OUT=ROOT/"dist/答辩逐字稿-从人海作业到数智协同.docx";CASE_ID=os.environ.get("CASE_ID",CFG["case_id_default"]);FONT="SimSun"

SLIDES=[
("0:00—0:35","封面","翻到封面后停顿，面向评委","各位评委老师，大家好。今天汇报的题目是《从人海作业到数智协同——输电运检外协队伍提质增效实践》。这是一项由我从实际工作问题出发、自主设计并推动落地的个人案例。全文讲两个方面：第一，如何用空间计算增效；第二，如何用照片全量查重提质。"),
("0:35—1:20","外协工作同时面临效率和质量压力","指向左右两类问题","外协工作点多、线长、任务频繁。交叉跨越、防鸟、燃放点等专项排查，如果全靠人工逐段找、逐点查，会投入大量时间；另一方面，告警工单和巡视照片数量巨大，靠人工抽查无法稳定发现重复上传。一个是处理不动，一个是验证不了，必须用两类数字能力同时破题。"),
("1:20—2:00","数字化双轮驱动","先指增效轮，再指提质轮","我的思路是建立增效和提质两个轮子。增效轮对应交叉跨越、防鸟、集中燃放点，用机器批量算，减少人海排查。提质轮对应告警工单和巡视照片查重，用全量比对验证照片真实性。两个轮子不是互相替代，而是共同把外协人员的精力拉回到专业判断和现场处置。"),
("2:00—2:40","共用能力轴心","按流程从左到右讲","两个轮子共用同一个轴心：先把坐标、图层和照片整理成机器能算的数据；再把业务经验转成求交、缓冲、聚类和相似度规则；机器完成全量筛选；人员复核候选；最后把清单、结论和规则沉淀下来。机器负责全量与速度，人员负责判断与责任。"),
("2:40—3:20","全省数据底座与脱密","强调真实库不进入演示文件","原始杆塔库包含约40.1万基杆塔、9217条线路。生产分析使用真实数据，但答辩演示不保存真实经纬度、线路名和杆号。演示层只使用匿名、扰动、量化后的画布坐标，并优先加载500千伏及以上数据模型，既保证全省效果，也保证现场交互流畅和数据安全。"),
("3:20—4:00","增效轮：空间计算替代人海排查","指出线、点、面三类对象","增效轮看起来有三个场景，底层其实是一套方法。交叉跨越是线和线求交；防鸟是把鸟害点聚成重点区域，再和线路叠加；集中燃放点是点和线路算距离。换的是规则，不换的是坐标底座。下面我用全省脱敏地图现场演示。"),
("4:00—5:35","全省地图交互演示","依次点击“交叉跨越”“防鸟”“燃放点”，每次停留约20秒","先看交叉跨越。程序先用包围盒排除不可能相交的组合，再做精确求交，把候选点直接标出来。再看防鸟，鸟害样本先做密度聚类，孤立点作为噪声，聚集区用凸包收敛成重点区域。最后看燃放点，围绕点位生成N米缓冲区，批量筛出周边杆塔。人的工作从全量寻找变成候选核验，这就是增效。"),
("5:35—6:15","三类规则共用一套底座","关闭弹层，回到对照页","三类场景分别是线线求交、点面聚类和点线距离，但坐标清洗、线路排序、异常检查、结果制图和清单输出都能复用。专项任务再来时，不需要重新从表格开始，只要换图层、换条件、换阈值。一次整理不只解决一次问题，效率提升才能持续。"),
("6:15—6:55","增效成果","强调程序候选不是最终结论","空间计算并不是取消现场。程序负责无遗漏地扫过全量对象，人员负责确认图层误差、现场条件和真实风险。过去是外协人员先到处找，再判断；现在是机器先把范围收敛，外协人员带着候选清单精准核验。效率提高了，现场确认标准并没有降低。"),
("6:55—7:40","提质轮：照片真实性全量验证","从增效转入提质","接下来讲提质。外协工单和巡视照片是证明到位、处置和履职的重要依据。人工能看清一张照片，却记不住成千上万张历史照片。照片经过裁剪、调色、旋转甚至局部消除后，更难靠肉眼发现。提质的关键，是把有限抽查变成机器全量筛选、人员终审认定。"),
("7:40—8:55","创新一：从0到1告警工单查重","点击照片查重，切换A/B并拖动滑块","告警工单照片查重是我从无到有独立做出来的。我先定义什么叫疑似重复，再设计机器筛选和人工认定流程。11.3万张照片先通过pHash和CLIP生成5472对候选，最终人工认定287对，候选命中率约5.2%。大家看这组脱敏照片，文件并不完全相同，但现场构图高度一致，这正是普通文件哈希发现不了的情况。"),
("8:55—10:00","双阶段查重算法","按五个步骤讲，不展开公式","算法第一层使用pHash感知哈希，以较低成本召回构图近似照片；第二层用CLIP图像向量复核语义相似度。告警工单阶段采用pHash小于10、CLIP大于0.80的双阈值生成候选。照片先标准化和计算特征，候选按批次归并，最后由人工结合业务信息终审。算法只提供证据线索，不直接代替管理结论。"),
("10:00—11:40","创新二：突破千万级规模","大标题停顿后再说直接表述","接下来是这项案例最核心的个人突破。既有能力只能实现极少量特高压巡视照片查重，无法覆盖全电压等级。电力信息公司没搞定的千万级照片查重，我搞定了。我重构了候选生成和工程处理流程，把筛查范围扩展到全电压等级，实现每月1245万张巡视照片的规模化查重。这里解决的不只是“有没有算法”，而是算法能不能真正跑得动。"),
("11:40—13:15","1245万张照片如何跑得动","指向77.5万亿和分层收敛","1245万张照片如果两两组合，大约有77.5万亿种可能，不能全部算一遍。我的做法是先生成可复用特征，用低成本规则快速召回候选，再对候选做高成本语义复核。任务分批运行，支持断点续算，结果统一归并去重。最终识别55411对重复照片，平均约14亿种理论组合中才出现一对结果，真正实现了大海捞针。"),
("13:15—15:00","结论与推广","放慢语速，最后一句停顿","回到这项案例的两条主线。增效，让交叉跨越、防鸟和燃放点排查从人海摸排转向机器计算、人员核验；提质，让告警工单和巡视照片从有限抽查转向全量验证。更重要的是，我完成了两个从无到有、从小到大的突破：独创告警工单查重，并把巡视照片查重扩展到全电压等级、每月千万级。机器承担重复劳动，专业判断回到关键环节——这就是从人海作业到数智协同。我的汇报完毕，谢谢各位评委。")]

def set_run(r,size=16,bold=False,color="000000",font=FONT):
 r.font.name=font;r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=RGBColor.from_string(color);rp=r._element.get_or_add_rPr();rf=rp.find(qn('w:rFonts'))
 if rf is None:rf=OxmlElement('w:rFonts');rp.append(rf)
 for k in ('ascii','hAnsi','eastAsia','cs'):rf.set(qn('w:'+k),font)
def p(doc,text,size=16,bold=False,color="000000",indent=True,align=None,before=0,after=0,line=28):
 x=doc.add_paragraph();x.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY;x.paragraph_format.line_spacing=Pt(line);x.paragraph_format.space_before=Pt(before);x.paragraph_format.space_after=Pt(after)
 if indent:x.paragraph_format.first_line_indent=Pt(size*2)
 if align is not None:x.alignment=align
 set_run(x.add_run(text),size,bold,color);return x
def build():
 d=Document();s=d.sections[0];s.page_width=Cm(21);s.page_height=Cm(29.7);s.top_margin=Cm(2.3);s.bottom_margin=Cm(2.2);s.left_margin=Cm(2.6);s.right_margin=Cm(2.6)
 p(d,"答辩逐字稿",24,True,align=WD_ALIGN_PARAGRAPH.CENTER,indent=False,before=10,line=36);p(d,CFG['title']+"——"+CFG['subtitle'],16,False,align=WD_ALIGN_PARAGRAPH.CENTER,indent=False,after=6);p(d,CASE_ID,12,False,"666666",False,WD_ALIGN_PARAGRAPH.CENTER,after=18)
 for i,(time,title,cue,text) in enumerate(SLIDES,1):
  p(d,f"第{i}页｜{title}",18,True,"C76142",False,before=6,after=2,line=30)
  p(d,f"时间：{time}　操作：{cue}",11.5,False,"666666",False,after=5,line=22)
  p(d,text,16,False,"000000",True,line=29)
  if i!=len(SLIDES):d.add_page_break()
 OUT.parent.mkdir(parents=True,exist_ok=True);d.save(OUT);print(f"[script] generated {OUT}")
if __name__=='__main__':build()
