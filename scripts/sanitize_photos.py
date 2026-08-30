#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parents[1]/"小组汇报/内部研讨/分享会资料/图表与案例/查重照片"
OUT=ROOT/"assets/images"
PAIRS=[("R1_f1p.jpg","R1_f2p.jpg"),("R6_f1p.jpg","R6_f2p.jpg"),("R9_f1p.jpg","R9_f2p.jpg"),("R12_f1p.jpg","R12_f2p.jpg")]

def sanitize(src,dst):
    im=Image.open(src).convert("RGB")
    w,h=im.size
    im=im.crop((0,0,w,int(h*0.72)))
    im=ImageOps.fit(im,(960,620),method=Image.Resampling.LANCZOS,centering=(0.5,0.42))
    im=ImageEnhance.Contrast(im).enhance(1.04)
    im.save(dst,"JPEG",quality=88,optimize=True,exif=b"")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    count=0
    for i,(a,b) in enumerate(PAIRS,1):
        for suffix,name in (("a",a),("b",b)):
            src=SOURCE/name
            if not src.exists():
                continue
            sanitize(src,OUT/f"pair-{i}-{suffix}.jpg")
            count+=1
    print(f"[assets] 已生成 {count} 张去水印、去EXIF演示照片")

if __name__=="__main__":
    main()

