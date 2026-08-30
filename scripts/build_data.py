#!/usr/bin/env python3
import hashlib
import json
import math
import os
import random
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("POLE_DB", "/Users/zhangyuxi/Desktop/000基础数据/pole_data.db"))
OUT = ROOT / "data/demo.json"
HV_CODES = {"35", "37", "50", "78", "83", "85"}


def seq_key(value):
    nums = re.findall(r"\d+", value or "")
    return tuple(int(n) for n in nums[-2:]) if nums else (10**9,)


def hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    hi = []
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def simplify(points, limit=48):
    if len(points) <= limit:
        return points
    step = (len(points)-1)/(limit-1)
    return [points[round(i*step)] for i in range(limit)]


def segment_intersection(a, b, c, d):
    x1,y1=a; x2,y2=b; x3,y3=c; x4,y4=d
    den=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if abs(den) < 1e-9: return None
    px=((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/den
    py=((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/den
    if min(x1,x2)-1 <= px <= max(x1,x2)+1 and min(y1,y2)-1 <= py <= max(y1,y2)+1 and min(x3,x4)-1 <= px <= max(x3,x4)+1 and min(y3,y4)-1 <= py <= max(y3,y4)+1:
        return [round(px), round(py)]
    return None


def main():
    if not DB.exists():
        raise SystemExit(f"杆塔数据库不存在：{DB}")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    total, lines = con.execute("SELECT COUNT(*), COUNT(DISTINCT line) FROM poles").fetchone()
    rows = con.execute("""
        SELECT line, pole_num, longitude, latitude, voltage_level
        FROM poles
        WHERE voltage_level IN ('35','37','50','78','83','85')
        ORDER BY line
    """).fetchall()
    con.close()
    grouped = defaultdict(list)
    all_xy = []
    for line, pole, lon, lat, voltage in rows:
        if lon is None or lat is None: continue
        grouped[(line or "", voltage)].append((pole or "", float(lon), float(lat)))
        all_xy.append((float(lon), float(lat)))
    minx=min(p[0] for p in all_xy); maxx=max(p[0] for p in all_xy)
    miny=min(p[1] for p in all_xy); maxy=max(p[1] for p in all_xy)
    def norm(lon, lat):
        x=90+(lon-minx)/(maxx-minx)*1020
        y=650-(lat-miny)/(maxy-miny)*570
        x += 22*math.sin(y/83)+12*math.sin(x/47)
        y += 18*math.sin(x/96)-10*math.cos(y/61)
        return [round(x/6)*6, round(y/6)*6]

    outline = simplify(hull([tuple(norm(x,y)) for x,y in all_xy]), 30)
    candidates = sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True)
    routes=[]
    for idx, ((real_name, voltage), pts) in enumerate(candidates[:84], 1):
        pts=sorted(pts, key=lambda p: seq_key(p[0]))
        mapped=[norm(lon,lat) for _,lon,lat in pts]
        digest=int(hashlib.sha256(real_name.encode()).hexdigest()[:8],16)
        dx=((digest%11)-5)*5; dy=(((digest//11)%11)-5)*4
        mapped=[[min(1120,max(80,x+dx)),min(660,max(60,y+dy))] for x,y in mapped]
        mapped=simplify(mapped, 44)
        if len(mapped)>=2:
            routes.append({"id":f"DL-{idx:03d}","level":voltage,"points":mapped})

    railways=[]
    for i in range(7):
        pts=[]
        for j in range(13):
            x=60+j*95
            y=105+i*72+42*math.sin((j+i*1.7)/2.0)+10*math.cos(j*1.3+i)
            pts.append([round(x),round(y)])
        railways.append({"id":f"R-{i+1:02d}","kind":"公开铁路示意","points":pts})
    crossings=[]
    for route in routes[:36]:
        for rail in railways:
            for a,b in zip(route["points"],route["points"][1:]):
                for c,d in zip(rail["points"],rail["points"][1:]):
                    p=segment_intersection(a,b,c,d)
                    if p:
                        crossings.append(p)
                        break
                if len(crossings)>=42: break
            if len(crossings)>=42: break
        if len(crossings)>=42: break

    rng=random.Random(260830)
    fireworks=[]
    for i in range(28):
        x=rng.randint(130,1060); y=rng.randint(105,610)
        fireworks.append({"id":f"F-{i+1:02d}","point":[x,y],"risk":i<9})
    bird_clusters=[]
    centers=[(270,220),(510,445),(770,235),(930,485)]
    for ci,(cx,cy) in enumerate(centers,1):
        pts=[]
        for _ in range(13):
            pts.append([round(cx+rng.gauss(0,42)),round(cy+rng.gauss(0,34))])
        bird_clusters.append({"id":f"B-{ci}","points":pts,"hull":hull([tuple(p) for p in pts])})

    result={
      "meta":{
        "scope":"全省脱敏仿真",
        "notice":"原始坐标未写入本文件；线路已匿名化、强扰动、量化和抽样。",
        "provincePoles":total,
        "provinceLines":lines,
        "modelPoles":len(rows),
        "modelLines":len(grouped),
        "displayRoutes":len(routes)
      },
      "outline":outline,
      "routes":routes,
      "railways":railways,
      "crossings":crossings,
      "fireworks":fireworks,
      "birdClusters":bird_clusters
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"[data] {total}基/{lines}线 -> {len(routes)}条匿名演示线路；{OUT.stat().st_size/1024:.1f} KiB")


if __name__ == "__main__":
    main()

