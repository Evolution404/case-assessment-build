#!/usr/bin/env python3
"""Build the six management figures to match the approved 4:3 reference style.

Only management figures 1/3/4/8/9/10 are generated. Figures 2/5/6/7 are not
opened or rewritten by this script.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from management_figure_style import (
    FigureCanvas,
    WHITE, INK, TEXT, MUTED, FAINT,
    BLUE, BLUE_DARK, BLUE_MID, BLUE_BORDER, BLUE_LIGHT, BLUE_LIGHT_2,
    ORANGE, ORANGE_DARK, ORANGE_LIGHT,
    GREEN, GREEN_LIGHT, RED, GRAY, GRAY_LIGHT, RULE, RULE_LIGHT,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "figures"
CASE = json.loads((ROOT / "content" / "case.json").read_text(encoding="utf-8"))
METRICS = CASE["metrics"]


def _bullet(c: FigureCanvas, x: float, y: float, label: str, *, color: str = BLUE, size: float = 21) -> None:
    c.circle(x, y + 11, 5, fill=color)
    c.text(x + 28, y, label, size=size, color=TEXT)


def _bullet_box(c: FigureCanvas, box, label, *, color=BLUE, outline=BLUE_BORDER) -> None:
    x, y, w, h = box
    c.rounded_rect(box, fill="#FBFCFE" if color == BLUE else "#FFF9F3", outline=outline, width=1.2, radius=12)
    c.circle(x + 36, y + h/2, 5.5, fill=color)
    c.text(x + 66, y + h/2, label, size=21, color=TEXT, valign="middle")


def _footer_caption(c: FigureCanvas, caption: str) -> None:
    c.bottom_rule(965)
    c.text(724, 1001, caption, size=23, color=TEXT, align="center", valign="middle")


def fig01() -> None:
    c = FigureCanvas()
    c.title(1, "外协管理两大痛点")

    c.rounded_rect((444, 101, 549, 160), fill=WHITE, outline=BLUE, width=1.7, radius=18, shadow=True)
    c.icon("users", 531, 179, 96, color=BLUE)
    c.text(646, 122, "外协队伍管理", size=32, color=BLUE_DARK, weight="bold")
    c.dashed_line((621, 174), (968, 174), color="#90AED0", width=1.2, dash=5, gap=4)
    c.text(644, 193, "外协队伍是业务执行的重要支撑，\n管理效能直接影响业务质量与交付效率。", size=19, color=TEXT, spacing=6)

    c.line((708, 261), (708, 300), color=GRAY, width=2)
    c.line((396, 300), (1010, 300), color=GRAY, width=2)
    c.arrow((396, 300), (396, 344), color=GRAY, width=2, head=10)
    c.arrow((1010, 300), (1010, 344), color=GRAY, width=2, head=10)

    c.rounded_rect((109, 344, 559, 428), fill=WHITE, outline=BLUE, width=1.8, radius=18, shadow=True)
    c.rounded_rect((741, 344, 555, 428), fill=WHITE, outline=ORANGE, width=1.5, radius=18, shadow=True)

    c.circle(210, 439, 61, fill="#EFF5FB")
    c.icon("clock", 210, 439, 112, color=BLUE_MID)
    c.text(307, 391, "痛点一：工作量大", size=30, color=BLUE_DARK, weight="bold")
    c.dashed_line((305, 438), (584, 438), color="#92B1D3", width=1.2, dash=5, gap=4)
    c.text(306, 452, "外协任务繁杂，依赖人工处理，\n全量排查投入高、效率低。", size=21, color=TEXT, spacing=7)
    _bullet_box(c, (151, 540, 477, 58), "任务来源分散", color=BLUE, outline="#8DAED4")
    _bullet_box(c, (151, 611, 477, 58), "依赖人工筛查与核对", color=BLUE, outline="#8DAED4")
    _bullet_box(c, (151, 684, 477, 58), "外协全量排查投入高", color=BLUE, outline="#8DAED4")

    c.circle(837, 439, 61, fill="#FFF1E3")
    c.icon("shield", 837, 439, 112, color=ORANGE)
    c.text(923, 391, "痛点二：质量难保证", size=30, color=ORANGE, weight="bold")
    c.dashed_line((920, 438), (1249, 438), color="#D7A776", width=1.2, dash=5, gap=4)
    c.text(921, 452, "人工抽查手段有限，难以全面识别问题，\n履职监督难以形成闭环。", size=21, color=TEXT, spacing=7)
    _bullet_box(c, (778, 540, 477, 58), "照片抽查覆盖有限", color=ORANGE, outline="#F0AE69")
    _bullet_box(c, (778, 611, 477, 58), "重复照片不易发现", color=ORANGE, outline="#F0AE69")
    _bullet_box(c, (778, 684, 477, 58), "履职监督难闭环", color=ORANGE, outline="#F0AE69")

    c.polygon([(285, 773), (641, 773), (701, 855), (606, 815)], fill="#E7EFF8")
    c.polygon([(1153, 773), (797, 773), (701, 855), (832, 811)], fill="#E7EFF8")
    c.polygon([(558, 773), (677, 773), (702, 855), (657, 813)], fill="#D5E3F3")
    c.polygon([(879, 773), (760, 773), (702, 855), (744, 813)], fill="#D5E3F3")

    c.rounded_rect((366, 884, 668, 85), fill=WHITE, outline=BLUE, width=1.8, radius=16, shadow=True)
    c.icon("scale", 455, 927, 63, color=BLUE)
    c.text(535, 927, "核心矛盾：增效与提质需求并存", size=30, color=BLUE_DARK, weight="bold", valign="middle")
    c.bottom_rule(1014)
    c.save(OUT / "01-外协管理两大痛点.png")


def fig03() -> None:
    c = FigureCanvas()
    c.title(3, "增效提质总体模型")

    c.rounded_rect((24, 330, 268, 438), fill=WHITE, outline=BLUE_DARK, width=1.8, radius=18, shadow=True)
    c.icon("users", 153, 414, 95, color=BLUE)
    c.text(157, 498, "1. 外协队伍管理", size=26, color=BLUE_DARK, weight="bold", align="center")
    c.line((44, 548), (270, 548), color="#7599C2", width=1.4)
    c.text(158, 576, "外协队伍是业务执行\n的重要支撑，管理效能\n直接影响业务质量与\n交付效率。", size=21, color=TEXT, align="center", spacing=8)

    c.arrow((302, 532), (367, 532), color="#8B8F94", width=3, head=14)

    c.rounded_rect((376, 251, 279, 606), fill=WHITE, outline=None, radius=18)
    c.dashed_line((394, 251), (638, 251), color="#96999D", width=1.5, dash=7, gap=6)
    c.dashed_line((376, 269), (376, 839), color="#96999D", width=1.5, dash=7, gap=6)
    c.dashed_line((655, 269), (655, 839), color="#96999D", width=1.5, dash=7, gap=6)
    c.dashed_line((394, 857), (638, 857), color="#96999D", width=1.5, dash=7, gap=6)
    c.text(515, 274, "2. 现状痛点", size=28, color="#404349", weight="bold", align="center")

    c.rounded_rect((401, 323, 225, 225), fill="#FAFCFE", outline="#8FAFD0", width=1.4, radius=14, shadow=True)
    c.icon("clock", 514, 378, 82, color=BLUE_MID)
    c.text(514, 421, "工作量大", size=29, color=BLUE_DARK, weight="bold", align="center")
    c.dashed_line((420, 462), (607, 462), color="#A7BBD1", width=1.1, dash=4, gap=4)
    c.text(514, 479, "依赖人工筛查与核对，\n重复劳动多，效率低下。", size=20, color=TEXT, align="center", spacing=7)

    c.rounded_rect((401, 586, 225, 250), fill="#FAFCFE", outline="#8FAFD0", width=1.4, radius=14, shadow=True)
    c.icon("shield_alert", 514, 641, 80, color=BLUE_MID)
    c.text(514, 684, "质量难保证", size=27, color=BLUE_DARK, weight="bold", align="center")
    c.dashed_line((420, 724), (607, 724), color="#A7BBD1", width=1.1, dash=4, gap=4)
    c.text(514, 741, "人工质检覆盖有限，\n查重与监督不足，\n外协履职质量波动大。", size=20, color=TEXT, align="center", spacing=7)

    c.arrow((627, 423), (765, 363), color="#777B80", width=2.6, head=13)
    c.arrow((627, 690), (765, 690), color="#777B80", width=2.6, head=13)

    c.rounded_rect((771, 258, 231, 276), fill=WHITE, outline=BLUE, width=1.7, radius=18, shadow=True)
    c.tab((797, 239, 178, 45), "3a. 增效", size=26)
    c.icon("chart", 886, 350, 91, color=BLUE)
    c.dashed_line((793, 396), (980, 396), color="#A6BBD0", width=1.0, dash=4, gap=4)
    _bullet(c, 798, 419, "数字化筛选任务", color=BLUE, size=20)
    c.circle(798, 467, 5, fill=BLUE)
    c.text(821, 453, "减少外协全量\n人工排查", size=20, color=TEXT, spacing=5)

    c.rounded_rect((771, 575, 231, 264), fill=WHITE, outline=ORANGE, width=1.7, radius=18, shadow=True)
    c.tab((797, 554, 178, 45), "3b. 提质", orange=True, size=26)
    c.icon("shield", 886, 649, 89, color=ORANGE)
    c.dashed_line((793, 700), (980, 700), color="#C5B3A4", width=1.0, dash=4, gap=4)
    _bullet(c, 798, 727, "照片全量查重", color=ORANGE, size=20)
    c.circle(798, 773, 5, fill=ORANGE)
    c.text(821, 760, "强化外协履职\n质量监督", size=20, color=TEXT, spacing=5)

    c.line((1002, 354), (1049, 354), color="#777B80", width=2.4)
    c.line((1049, 354), (1049, 690), color="#777B80", width=2.4)
    c.line((1002, 690), (1049, 690), color="#777B80", width=2.4)
    c.arrow((1049, 530), (1111, 530), color="#777B80", width=3.2, head=14)

    c.rounded_rect((1119, 325, 258, 448), fill=WHITE, outline=BLUE_DARK, width=1.8, radius=18, shadow=True)
    c.icon("network", 1248, 413, 99, color=BLUE)
    c.text(1248, 499, "4. 数智协同管理", size=27, color=BLUE_DARK, weight="bold", align="center")
    c.line((1137, 548), (1358, 548), color="#7599C2", width=1.4)
    c.text(1248, 576, "通过数字化与智能化\n手段协同驱动，\n实现外协管理的\n增效与提质闭环，\n提升整体管理效能。", size=21, color=TEXT, align="center", spacing=7)

    _footer_caption(c, "技术是支撑手段，核心是外协管理增效与提质。")
    c.save(OUT / "03-增效提质总体模型.png")


def _draw_layered_rules(c: FigureCanvas, x: float, y: float) -> None:
    colors = ["#8F7CC3", "#AABEE1", "#B9CDE7", "#B7DBD1", "#98C8AF"]
    for i in range(5):
        yy = y + i*52
        pts = [(x+30,yy),(x+222,yy),(x+182,yy+48),(x,yy+48)]
        c.polygon(pts, fill="#F7FAFD", outline=colors[i])
    c.icon("tower", x+80, y+28, 45, color="#8068B6")
    c.icon("tower", x+170, y+28, 45, color="#8068B6")
    c.icon("bird", x+76, y+83, 48, color="#4777B2")
    c.icon("firework", x+110, y+140, 55, color=ORANGE)
    c.icon("weather", x+92, y+190, 50, color="#4777B2")
    for p in [(50,244),(92,232),(132,248),(174,234),(210,246)]:
        c.circle(x+p[0], y+p[1], 3.5, fill=GREEN)
    for a,b in [((50,244),(92,232)),((92,232),(132,248)),((132,248),(174,234)),((174,234),(210,246))]:
        c.line((x+a[0],y+a[1]),(x+b[0],y+b[1]),color=GREEN,width=1)
    c.dashed_line((x+70,y+52),(x+70,y+210),color="#A0B1C6",width=1,dash=4,gap=4)
    c.dashed_line((x+160,y+52),(x+160,y+210),color="#A0B1C6",width=1,dash=4,gap=4)


def fig04() -> None:
    c = FigureCanvas()
    c.title(4, "外协任务数字化筛选流程")

    tabs = [
        (32, 219, 231, 45, "1. 多源数据汇集", False),
        (347, 219, 239, 45, "2. 空间叠加与规则筛查", False),
        (639, 219, 226, 45, "3. 重点任务自动识别", False),
        (913, 219, 192, 45, "4. 外协定向巡视", True),
        (1161, 219, 208, 45, "5. 主业复核与闭环", False),
    ]
    for x,y,w,h,label,orange in tabs:
        c.tab((x,y,w,h),label,orange=orange,size=23)

    cards = [
        (18, 280, 264, 508, BLUE),
        (329, 241, 270, 547, BLUE),
        (637, 281, 224, 507, BLUE),
        (906, 281, 201, 507, ORANGE),
        (1159, 281, 205, 507, BLUE),
    ]
    for x,y,w,h,col in cards:
        c.rounded_rect((x,y,w,h),fill=WHITE,outline=col,width=1.3,radius=14,shadow=True)

    rows = [
        (335,"tower","交叉跨越"),
        (414,"bird","鸟类活动"),
        (493,"firework","燃放点周边"),
        (574,"weather","气象/节假日"),
        (655,"tower","杆塔与线路底账"),
    ]
    for yy,icon,label in rows:
        c.icon(icon,72,yy,48,color=BLUE)
        c.text(121,yy,label,size=20,color=TEXT,valign="middle")
        if yy != rows[-1][0]:
            c.dashed_line((41,yy+39),(260,yy+39),color="#C7CDD3",width=1,dash=4,gap=4)
    c.text(150, 724, "整合结构化与非结构化数据，\n统一标准化处理。", size=17, color=TEXT, align="center", spacing=5)

    _draw_layered_rules(c, 347, 300)
    c.text(464, 588, "距离、重叠、风险规则", size=22, color=BLUE_DARK, weight="bold", align="center")
    c.dashed_line((348,655),(579,655),color="#C7CDD3",width=1,dash=4,gap=4)
    c.text(464, 677, "基于空间叠加与业务规则\n（距离、重叠、风险规则）\n进行自动筛查。", size=17, color=TEXT, align="center", spacing=5)

    c.icon("monitor", 748, 388, 140, color=BLUE)
    for xx in [670,744,818]:
        c.rounded_rect((xx-28, 519, 55, 58), fill=WHITE, outline=BLUE, width=1.3, radius=6)
        c.line((xx-16,535),(xx+15,535),color=BLUE,width=1.5)
        c.line((xx-16,548),(xx+7,548),color=BLUE,width=1.5)
        c.circle(xx+15,559,9,outline=BLUE,width=1.2)
        c.line((xx+10,559),(xx+14,563),color=BLUE,width=1.2)
        c.line((xx+14,563),(xx+20,555),color=BLUE,width=1.2)
    c.arrow((748,455),(748,510),color=BLUE,width=2,head=9)
    c.arrow((748,479),(670,510),color=BLUE,width=1.6,head=8)
    c.arrow((748,479),(826,510),color=BLUE,width=1.6,head=8)
    c.text(749, 615, "减少全量人工排查", size=21, color=BLUE_DARK, weight="bold", align="center")
    c.dashed_line((652,655),(846,655),color="#C7CDD3",width=1,dash=4,gap=4)
    c.text(749, 675, "自动识别高风险、高影响\n点位，生成外协重点任务\n清单，减少全量人工排查。", size=16.5, color=TEXT, align="center", spacing=4)

    c.icon("worker_phone", 1007, 415, 146, color=ORANGE)
    _bullet(c, 921, 539, "任务推送与路线规划", color=ORANGE, size=17)
    _bullet(c, 921, 574, "外协执行与现场反馈", color=ORANGE, size=17)
    c.dashed_line((918,655),(1091,655),color="#D5C5B7",width=1,dash=4,gap=4)
    c.text(1007, 678, "定向推送任务与巡视频径，\n外协按要求执行巡视并上\n传结果。", size=16, color=TEXT, align="center", spacing=4)

    c.icon("shield_loop", 1261, 421, 150, color=BLUE)
    c.text(1261, 562, "结果反馈与规则优化", size=20.5, color=BLUE_DARK, weight="bold", align="center")
    c.dashed_line((1171,655),(1352,655),color="#C7CDD3",width=1,dash=4,gap=4)
    c.text(1261, 678, "主业复核确认结果，形成\n闭环，并将反馈用于规则\n优化与模型迭代，持续提\n升筛查精准度与管理效能。", size=15.8, color=TEXT, align="center", spacing=4)

    for a,b in [((284,480),(326,480)),((602,480),(632,480)),((864,480),(900,480)),((1111,480),(1154,480))]:
        c.arrow(a,b,color="#8A8D91",width=3,head=12)

    c.bottom_rule(836)
    c.text(724, 873, "数字化筛选贯穿“数据-规则-任务-执行-反馈”全流程，支撑外协管理增效与风险可控。", size=20, color=TEXT, align="center")
    c.save(OUT / "04-外协任务数字化筛选流程.png")


def _flow_card(c: FigureCanvas, y: float, n: int, title: str, body: str, icon: str, *, orange=False) -> None:
    col = ORANGE if orange else BLUE
    c.rounded_rect((67, y, 485, 105), fill=WHITE, outline="#6F96C1", width=1.2, radius=13, shadow=True)
    c.icon(icon, 120, y+52, 67, color=col)
    c.circle(200, y+26, 14, fill=BLUE_DARK)
    c.text(200, y+26, str(n), size=17, color=WHITE, weight="bold", align="center", valign="middle")
    c.text(225, y+14, title, size=24, color=BLUE_DARK, weight="bold")
    c.text(224, y+52, body, size=17, color=TEXT, spacing=4)


def _sample_photo_card(c: FigureCanvas, box, label, photo: Path, meta: list[str], *, badge: str | None = None, badge_color=RED) -> None:
    x,y,w,h=box
    c.rounded_rect(box,fill=WHITE,outline="#6C91BE",width=1.2,radius=13,shadow=True)
    c.rounded_rect((x+14,y+16,w-28,h-32),fill="#F1F6FB",outline=None,radius=8)
    c.text(x+w/2,y+26,label,size=22,color=BLUE_DARK,weight="bold",align="center")
    c.paste_photo(photo,(x+26,y+74,w-52,155),radius=4)
    if badge:
        c.rounded_rect((x+w-78,y+15,72,64),fill="#FFF1F0" if badge_color==RED else ORANGE_LIGHT,outline=None,radius=6)
        c.text(x+w-42,y+20,badge,size=18,color=badge_color,weight="bold",align="center")
    icons=["clock","route","clipboard"]
    for i,line in enumerate(meta):
        yy=y+251+i*34
        c.icon(icons[i],x+35,yy+11,29,color="#587AA4")
        c.text(x+57,yy,line,size=16,color=TEXT)


def fig08() -> None:
    c = FigureCanvas()
    c.title(8, "照片质量督查流程与示例")
    c.tab((217,102,272,46),"流程：照片质量督查",size=24)
    c.tab((829,104,430,46),"示例：重复/近重复识别与复核",size=24)

    _flow_card(c,166,1,"工单/告警照片汇集","汇集外协工单或告警产生的照片，\n按工单编号、时间、地点等信息入库。","folder")
    _flow_card(c,301,2,"特征提取与标准化","提取图像特征（如感知哈希、颜色直方图等），\n统一尺寸、角度与元数据，提升比对准确性。","image")
    _flow_card(c,430,3,"全量相似度比对","对全量照片进行相似度计算，\n识别相似或近似重复的照片组合。","database")
    _flow_card(c,559,4,"重复/近重复预警","依据相似度阈值生成预警清单，\n标注重复（高相似）与近重复（中相似）。","warning",orange=True)
    _flow_card(c,687,5,"人工复核","督查人员逐条核查预警对，判定是否为\n无效重复拍摄并记录复核依据。","person_check")
    _flow_card(c,810,6,"督查反馈","形成督查结论与整改建议，反馈至外协单位，\n纳入履职考核与质量改进闭环。","clipboard")
    for y1,y2 in [(271,300),(406,429),(535,558),(664,686),(792,809)]:
        c.arrow((322,y1),(322,y2),color="#668CB8",width=2,head=8)

    c.dashed_line((553,216),(594,216),color="#628BC0",width=1.2,dash=5,gap=4)
    c.dashed_line((594,216),(594,870),color="#628BC0",width=1.2,dash=5,gap=4)
    c.dashed_line((553,870),(594,870),color="#628BC0",width=1.2,dash=5,gap=4)
    c.arrow((554,491),(588,491),color="#668CB8",width=2,head=9)
    c.rounded_rect((606,403,125,228),fill=WHITE,outline="#6B95C7",width=1.2,radius=14)
    c.dashed_line((606,403),(606,631),color="#6B95C7",width=1.1,dash=5,gap=4)
    c.dashed_line((731,403),(731,631),color="#6B95C7",width=1.1,dash=5,gap=4)
    c.text(668,421,"重复照片识别\n\n支撑外协履职\n质量监督，\n减少虚假/无效\n拍摄，提升\n问题取证有效性。",size=17,color=TEXT,align="center",spacing=5)

    img_dir=ROOT/"assets"/"images"
    a=img_dir/"pair-1-a.jpg"; b=img_dir/"pair-1-b.jpg"; near=img_dir/"pair-2-a.jpg"
    _sample_photo_card(c,(793,180,267,360),"原始照片",a,["时间：2024-06-01 09:32:15","地点：XX路段","工单：20240601-0001"])
    _sample_photo_card(c,(1074,180,294,360),"疑似重复",b,["时间：2024-06-01 09:32:28","地点：XX路段","工单：20240601-0002"],badge="相似度\n98.7%")
    _sample_photo_card(c,(793,568,275,342),"近重复",near,["时间：2024-06-01 09:34:55","地点：XX路段","工单：20240601-0003"],badge="相似度\n72.3%",badge_color=ORANGE_DARK)
    c.arrow((1219,540),(1219,565),color="#668CB8",width=2,head=8)

    c.rounded_rect((1083,568,285,342),fill=WHITE,outline="#6C91BE",width=1.2,radius=13,shadow=True)
    c.text(1225,588,"复核结论",size=23,color=BLUE_DARK,weight="bold",align="center")
    c.rounded_rect((1100,618,250,275),fill="#FCFDFE",outline="#8AA8CB",width=1.0,radius=8)
    c.circle(1134,648,17,fill="#2D9A59")
    c.text(1134,648,"✓",size=23,color=WHITE,weight="bold",align="center",valign="middle")
    c.text(1170,628,"判定：重复",size=21,color=INK,weight="bold")
    c.text(1170,663,"与原始照片为重复拍摄",size=17,color=TEXT)
    c.circle(1134,716,17,fill=RED)
    c.text(1134,716,"−",size=25,color=WHITE,weight="bold",align="center",valign="middle")
    c.text(1170,696,"判定：近重复",size=21,color=INK,weight="bold")
    c.text(1170,731,"角度/距离略有差异，\n判定为近重复",size=17,color=TEXT,spacing=4)
    c.text(1108,792,"处理：计入无效拍摄",size=19,color=INK,weight="bold")
    c.text(1108,829,"建议整改并扣减相应分值",size=17,color=TEXT)

    c.bottom_rule(965)
    c.rounded_rect((485,989,447,52),fill="#F7FAFD",outline="#759BC6",width=1.1,radius=13,shadow=True)
    c.icon("management",527,1015,45,color=BLUE)
    c.text(551,1014,"作用：强化外协履职质量监督",size=26,color=BLUE_DARK,weight="bold",valign="middle")
    c.save(OUT / "08-照片质量督查流程与示例.png")


def _mini_bars(c: FigureCanvas, x: float, y: float, values: list[float], colors: list[str]) -> None:
    c.line((x,y+62),(x+104,y+62),color="#8D99A7",width=1)
    c.line((x,y),(x,y+62),color="#8D99A7",width=1)
    bw=18
    for i,(v,col) in enumerate(zip(values,colors)):
        c.rounded_rect((x+17+i*30,y+62-v,bw,v),fill=col,outline=None,radius=2)


def _node_cluster(c: FigureCanvas, cx: float, cy: float, *, orange_nodes: bool = False, green: bool = False) -> None:
    center_col = GREEN if green else BLUE_DARK
    c.circle(cx,cy,14,fill=center_col)
    for i,ang in enumerate([15,75,135,195,255,315]):
        r=47
        ex=cx+math.cos(math.radians(ang))*r; ey=cy+math.sin(math.radians(ang))*r
        c.line((cx,cy),(ex,ey),color="#5C83B1" if not green else "#6A9573",width=1.4)
        col=ORANGE if orange_nodes and i in {0,3,5} else ("#99B0D0" if not green else "#A8C7AE")
        outline=ORANGE if orange_nodes and i in {0,3,5} else (BLUE_DARK if not green else GREEN)
        c.circle(ex,ey,8,fill=col,outline=outline,width=1)


def fig09() -> None:
    c = FigureCanvas()
    c.title(9, "告警工单照片全量查重成果")

    c.rounded_rect((18,150,363,778),fill=WHITE,outline="#4D80BD",width=1.4,radius=14,shadow=True)
    c.rounded_rect((436,150,537,778),fill=WHITE,outline="#4D80BD",width=1.4,radius=14,shadow=True)
    c.rounded_rect((1018,150,366,778),fill=WHITE,outline="#4D80BD",width=1.4,radius=14,shadow=True)
    c.tab((44,117,318,51),"1. 输入池：告警工单照片",size=25)
    c.tab((509,117,389,51),"2. 全量查重分析",size=25)
    c.tab((1041,117,321,51),"3. 督查结果",size=25)

    c.rounded_rect((44,198,318,590),fill="#F4F8FC",outline=None,radius=10)
    c.icon("camera",102,252,66,color=BLUE)
    c.text(203,232,"告警工单照片",size=26,color=BLUE_DARK,weight="bold",align="center")
    c.text(203,281,"来自各工单的现场照片\n（去重前全量）",size=18,color=TEXT,align="center",spacing=5)
    c.dashed_line((55,355),(351,355),color="#B7C4D2",width=1,dash=4,gap=4)
    photo_rows=[
        (369,ROOT/"assets"/"images"/"pair-3-a.jpg","工单 A-2024-0001","拍摄时间：2024-01-15 10:21"),
        (499,ROOT/"assets"/"images"/"pair-4-a.jpg","工单 B-2024-0156","拍摄时间：2024-01-16 09:48"),
        (659,ROOT/"assets"/"images"/"pair-2-a.jpg","工单 C-2024-0321","拍摄时间：2024-01-17 14:33"),
    ]
    for yy,path,work,time in photo_rows:
        c.rounded_rect((54,yy,297,109),fill=WHITE,outline="#7AA4D0",width=1,radius=8)
        c.paste_photo(path,(62,yy+7,91,94),radius=4)
        c.icon("clipboard",177,yy+27,32,color=BLUE)
        c.text(199,yy+16,work,size=16,color=TEXT)
        c.text(165,yy+52,time,size=14,color=TEXT)
        c.text(165,yy+81,"地点：XX 路段",size=14,color=TEXT)
    c.text(202,627,"…",size=27,color=BLUE_DARK,weight="bold",align="center")
    c.rounded_rect((43,804,319,100),fill="#F4F8FC",outline=None,radius=10)
    c.icon("upload",111,851,56,color=BLUE)
    c.text(161,820,"全量照片入库",size=19,color=BLUE_DARK,weight="bold")
    c.text(161,849,f"来源工单数：多源合并\n总照片数：{METRICS['alarm_photos']/10000:.1f}万张（全量）",size=16,color=TEXT,spacing=4)

    c.arrow((390,525),(428,525),color="#83878C",width=4,head=15)
    c.arrow((977,525),(1011,525),color="#83878C",width=4,head=15)

    c.icon("magnifier",554,211,52,color=BLUE)
    c.text(590,190,"视觉特征提取与相似性匹配",size=23,color=BLUE_DARK,weight="bold")
    c.text(590,224,"多阶段查重引擎（全量对比）",size=17,color=TEXT)

    sections=[
        (263,"1","完全重复","图像高度一致\n（相似度 ≥ 0.95）",False),
        (455,"2","近重复","存在裁剪/旋转/缩放/\n光照变化等\n（0.80 ≤ 相似度 < 0.95）",True),
        (649,"3","跨工单复用","不同工单间的\n同源或复用照片\n（相似度 ≥ 0.80）",False),
    ]
    for idx,(yy,num,title,desc,orange_nodes) in enumerate(sections):
        if idx<2:
            c.dashed_line((469,yy+188),(943,yy+188),color="#B8C9DC",width=1,dash=4,gap=4)
        c.circle(481,yy+46,13,fill=BLUE_DARK)
        c.text(481,yy+46,num,size=16,color=WHITE,weight="bold",align="center",valign="middle")
        c.text(505,yy+33,title,size=21,color=BLUE_DARK,weight="bold")
        c.text(471,yy+79,desc,size=16,color=TEXT,spacing=4)
        if title != "跨工单复用":
            _node_cluster(c,713,yy+92,orange_nodes=orange_nodes)
            c.dashed_line((637,yy+29),(790,yy+29),color="#8FB1D8",width=1,dash=4,gap=4)
            c.text(876,yy+28,"重复组数（示例）",size=14,color=TEXT,align="center")
            _mini_bars(c,822,yy+66,[38,49],[BLUE if not orange_nodes else ORANGE,"#A8C0DF" if not orange_nodes else "#F0C294"])
            c.text(875,yy+133,"照片数\n（占全量百分比）",size=14,color=TEXT,align="center",spacing=2)
        else:
            _node_cluster(c,655,yy+95)
            _node_cluster(c,772,yy+95,green=True)
            c.dashed_line((702,yy+95),(725,yy+95),color=BLUE_DARK,width=1.5,dash=4,gap=3)
            c.text(876,yy+26,"涉及工单对数\n（示例）",size=14,color=TEXT,align="center",spacing=2)
            _mini_bars(c,836,yy+75,[32,25],[GREEN,"#B2CCB8"])
            c.text(876,yy+139,"照片数\n（占全量百分比）",size=14,color=TEXT,align="center",spacing=2)

    c.rounded_rect((455,831,499,74),fill="#F3F7FB",outline=None,radius=8)
    c.icon("database",545,867,44,color=BLUE)
    c.text(584,844,"查重覆盖范围：全量",size=18,color=BLUE_DARK,weight="bold")
    c.text(584,873,f"{METRICS['alarm_photos']/10000:.1f}万张照片 · 分组结果用于督查与复核",size=16,color=TEXT)

    result_cards=[
        (1039,189,321,244,ORANGE,"bell","疑似问题自动预警","系统基于查重结果自动生成\n预警，提示可能存在的\n重复上传或复用风险。",[f"候选对：{METRICS['alarm_candidates']:,}对",f"涉及照片：自动汇总"]),
        (1039,452,321,225,BLUE,"clipboard","人工复核清单","输出可视化复核清单，支持\n按重复组快速查看与判定。",[f"确认重复：{METRICS['alarm_confirmed_pairs']}对","待复核照片：按组汇总"]),
        (1039,695,321,209,GREEN,"shield","履职质量监督","将查重结果纳入质量监督，\n支撑考核与问题追溯。",["重复率：持续监测","涉及单位数：统计汇总"]),
    ]
    for x,y,w,h,col,icon,title,body,bullets in result_cards:
        fill=ORANGE_LIGHT if col==ORANGE else GREEN_LIGHT if col==GREEN else WHITE
        c.rounded_rect((x,y,w,h),fill=fill,outline=col,width=1.2,radius=14,shadow=True)
        c.icon(icon,x+55,y+54,58,color=col)
        c.text(x+98,y+27,title,size=22,color=col if col!=BLUE else BLUE_DARK,weight="bold")
        c.text(x+98,y+71,body,size=16,color=TEXT,spacing=4)
        c.dashed_line((x+20,y+h-89),(x+w-20,y+h-89),color="#B7C3CF",width=1,dash=4,gap=4)
        for i,b in enumerate(bullets):
            c.circle(x+25,y+h-62+i*34,3.5,fill=TEXT)
            c.text(x+40,y+h-75+i*34,b,size=15,color=TEXT)
        _mini_bars(c,x+w-93,y+h-77,[35,24,10],[col,"#B7CAE1" if col==BLUE else "#EFC297" if col==ORANGE else "#A8C8AF",RULE_LIGHT])

    _footer_caption(c,"形成从发现到督查的闭环")
    c.save(OUT / "09-告警工单照片全量查重成果.png")


def _row_sep(c: FigureCanvas, y: float) -> None:
    c.dashed_line((48,y),(1368,y),color="#C1C7CE",width=1,dash=5,gap=5)


def _before_after_card(c: FigureCanvas, y: float, left_title: str, left_body: str, right_title: str, right_body: str, left_icon: str, right_icon: str) -> None:
    c.rounded_rect((323,y,421,164),fill="#FCFDFE",outline="#88A8CF",width=1.0,radius=12,shadow=True)
    c.icon(left_icon,401,y+81,98,color=BLUE)
    c.text(494,y+33,left_title,size=29,color=INK,weight="bold")
    c.text(494,y+82,left_body,size=19,color=TEXT,spacing=5)
    c.arrow((764,y+82),(831,y+82),color="#4D7EB9",width=5,head=16,glow=True)
    c.rounded_rect((850,y,485,164),fill="#FFFDFC",outline=ORANGE,width=1.0,radius=12,shadow=True)
    c.icon(right_icon,936,y+80,99,color=ORANGE)
    c.text(1028,y+31,right_title,size=28,color=INK,weight="bold")
    c.text(1028,y+82,right_body,size=19,color=TEXT,spacing=5)


def fig10() -> None:
    c = FigureCanvas()
    c.title(10, "外协管理前后对比")
    c.tab((354,106,360,61),"应用前",size=31)
    c.tab((878,106,430,61),"应用后",size=31)

    cats=[
        (196,"funnel","任务筛选"),
        (390,"magnifier","现场巡视"),
        (588,"camera","照片监督"),
        (779,"management","管理方式"),
    ]
    for y,icon,label in cats:
        c.rounded_rect((49,y,220,153),fill=WHITE,outline="#86A6CE",width=1.1,radius=13,shadow=True)
        c.icon(icon,158,y+52,76,color=BLUE)
        c.text(158,y+106,label,size=27,color=BLUE_DARK,weight="bold",align="center")

    _before_after_card(c,189,"全量人工排查","依赖人工遍历筛查，\n耗时长、效率低。","数字化定向筛选","基于数据与规则定向识别，\n精准高效。","clipboard","target")
    _row_sep(c,372)
    _before_after_card(c,390,"任务投放粗放","任务分配不聚焦，\n覆盖面广，针对性弱。","重点任务精准投放","聚焦高风险与关键区域，\n资源投放更精准。","route","target")
    _row_sep(c,570)
    _before_after_card(c,588,"照片抽查为主","抽样验证，覆盖有限，\n监督盲区较多。","照片全量查重","全量查重识别异常，\n监督更全面可靠。","image","camera_check")
    _row_sep(c,762)
    _before_after_card(c,779,"问题发现滞后","依赖事后反馈与人工汇报，\n响应慢、处置被动。","增效提质协同闭环","数智驱动协同联动，\n发现及时、处置高效、持续优化。","clock","management")

    c.dashed_line((43,986),(388,986),color="#6F96C3",width=1.3,dash=5,gap=4)
    c.circle(43,986,4,fill=BLUE)
    c.dashed_line((1028,986),(1370,986),color="#6F96C3",width=1.3,dash=5,gap=4)
    c.circle(1370,986,4,fill=BLUE)
    for xx in [428,445,462]:
        c.polygon([(xx,974),(xx+11,986),(xx,998),(xx+8,998),(xx+20,986),(xx+8,974)],fill="#88ACD3")
    c.text(701,986,"从粗放管理转向数智协同管理",size=30,color=BLUE_DARK,weight="bold",align="center",valign="middle")
    for xx in [945,962,979]:
        c.polygon([(xx,974),(xx+11,986),(xx,998),(xx+8,998),(xx+20,986),(xx+8,974)],fill="#88ACD3")

    c.save(OUT / "10-外协管理前后对比.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig01()
    fig03()
    fig04()
    fig08()
    fig09()
    fig10()


if __name__ == "__main__":
    main()
