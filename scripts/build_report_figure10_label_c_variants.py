#!/usr/bin/env python3
"""Generate C1-C4 white-backed label variants for review-only Figure 10.

Photo layout, crops and magnifier geometry stay identical. Only the label design
changes. This script does not modify the report or existing Figure 9.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import build_report_figure10_review as base
from management_figure_style import FigureCanvas

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".build" / "figure10-label-c-variants"
CONTACT = ROOT / ".build" / "review-图10-C1-C4标签方案对比.png"

SANS = "/System/Library/Fonts/Hiragino Sans GB.ttc"
SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
RED = "#A63A32"
DARK = "#30343A"
WHITE = "#FFFFFF"
BORDER = "#D7DBE0"
PALE_RED = "#F6E9E7"

LABELS = [
    (base.LEFT_X + 14, base.MAIN_Y + 12, "5月25日", "反馈照片"),
    (base.RIGHT_X + 14, base.MAIN_Y + 12, "5月22日", "反馈照片"),
    (base.LEFT_SUPPORT_X + 14, base.SUPPORT_Y + 12, "5月25日", "告警照片"),
    (base.RIGHT_SUPPORT_X + 14, base.SUPPORT_Y + 12, "5月22日", "告警照片"),
]


def font(path: str, size: float):
    return ImageFont.truetype(path, round(size * 2))


def measure(draw: ImageDraw.ImageDraw, text: str, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2]-b[0], b[3]-b[1]


def label_c1(c: FigureCanvas, x: float, y: float, date: str, kind: str):
    """C1: minimal academic tag, flat white rectangle, hairline border."""
    fd, fk = font(SANS, 27), font(SANS, 24)
    dw, dh = measure(c.draw, date, fd); kw, kh = measure(c.draw, kind, fk)
    gap = c._s(14); px = c._s(11); py = c._s(7)
    sx, sy = c._s(x), c._s(y)
    h = max(dh, kh)
    box = [sx-px, sy-py, sx+dw+gap+kw+px, sy+h+py+c._s(2)]
    c.draw.rectangle(box, fill=WHITE, outline=BORDER, width=max(1, c._s(.8)))
    c.draw.text((sx, sy), date, font=fd, fill=RED)
    c.draw.text((sx+dw+gap, sy+c._s(1)), kind, font=fk, fill=DARK)


def label_c2(c: FigureCanvas, x: float, y: float, date: str, kind: str):
    """C2: date emphasis, pale-red date segment + white type segment."""
    fd, fk = font(SANS, 26), font(SANS, 24)
    dw, dh = measure(c.draw, date, fd); kw, kh = measure(c.draw, kind, fk)
    sx, sy = c._s(x), c._s(y); px = c._s(11); py = c._s(7)
    h = max(dh, kh) + 2*py
    left_w = dw + 2*px
    right_w = kw + 2*px
    x0, y0 = sx-px, sy-py
    c.draw.rectangle([x0, y0, x0+left_w+right_w, y0+h], fill=WHITE, outline=BORDER, width=max(1,c._s(.8)))
    c.draw.rectangle([x0, y0, x0+left_w, y0+h], fill=PALE_RED)
    c.draw.line([x0+left_w, y0, x0+left_w, y0+h], fill=BORDER, width=max(1,c._s(.8)))
    c.draw.text((sx, sy), date, font=fd, fill=RED)
    c.draw.text((x0+left_w+px, sy+c._s(1)), kind, font=fk, fill=DARK)


def label_c3(c: FigureCanvas, x: float, y: float, date: str, kind: str):
    """C3: integrated top-edge strip, flush to panel edge."""
    fd, fk = font(SANS, 25), font(SANS, 23)
    dw, dh = measure(c.draw, date, fd); kw, kh = measure(c.draw, kind, fk)
    sx, sy = c._s(x), c._s(y)
    gap = c._s(13); px = c._s(12); py = c._s(7)
    h = max(dh, kh) + 2*py
    w = dw + gap + kw + 2*px
    x0, y0 = sx-c._s(14), sy-c._s(12)
    c.draw.rectangle([x0, y0, x0+w, y0+h], fill=WHITE, outline=BORDER, width=max(1,c._s(.8)))
    c.draw.line([x0, y0+h, x0+w, y0+h], fill=RED, width=max(1,c._s(1.5)))
    c.draw.text((x0+px, y0+py), date, font=fd, fill=RED)
    c.draw.text((x0+px+dw+gap, y0+py+c._s(1)), kind, font=fk, fill=DARK)


def label_c4(c: FigureCanvas, x: float, y: float, date: str, kind: str):
    """C4: translucent white frosted tag with soft opacity, no shadow."""
    fd, fk = font(SANS, 26), font(SANS, 23)
    dw, dh = measure(c.draw, date, fd); kw, kh = measure(c.draw, kind, fk)
    sx, sy = c._s(x), c._s(y); gap=c._s(14); px=c._s(11); py=c._s(7)
    h=max(dh,kh)+2*py; w=dw+gap+kw+2*px
    x0,y0=sx-px,sy-py
    overlay = Image.new("RGBA", c.image.size, (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([x0,y0,x0+w,y0+h], fill=(255,255,255,232), outline=(210,214,220,245), width=max(1,c._s(.8)))
    c.image.paste(overlay,(0,0),overlay); c.draw=ImageDraw.Draw(c.image)
    c.draw.text((sx,sy), date, font=fd, fill=RED)
    c.draw.text((sx+dw+gap,sy+c._s(1)), kind, font=fk, fill=DARK)


VARIANTS = {
    "C1": ("极简论文标签", label_c1),
    "C2": ("日期强调型", label_c2),
    "C3": ("上沿条签型", label_c3),
    "C4": ("半透明磨砂型", label_c4),
}


def render_base() -> FigureCanvas:
    c = FigureCanvas(width=base.W, height=base.H, scale=2)
    f525=base._open(base.PHOTO["525_feedback"]); f522=base._open(base.PHOTO["522_feedback"])
    o525=base._open(base.PHOTO["525_workorder"]); o522=base._open(base.PHOTO["522_workorder"])
    base._paste_main(c,f525,base.LEFT_X,base.MAIN_Y,base.MAIN_W,base.MAIN_H)
    base._paste_main(c,f522,base.RIGHT_X,base.MAIN_Y,base.MAIN_W,base.MAIN_H)
    lb=(base.LEFT_SUPPORT_X,base.SUPPORT_Y,base.SUPPORT_W,base.SUPPORT_H)
    rb=(base.RIGHT_SUPPORT_X,base.SUPPORT_Y,base.SUPPORT_W,base.SUPPORT_H)
    ml=base._paste_support_with_mapper(c,o525,*lb); mr=base._paste_support_with_mapper(c,o522,*rb)
    base._magnifier(c,o525,lb,ml,base.ZOOM["a"],side="left")
    base._magnifier(c,o522,rb,mr,base.ZOOM["b"],side="right")
    return c


def render_variant(key: str, title: str, fn) -> Path:
    c=render_base()
    for x,y,date,kind in LABELS: fn(c,x,y,date,kind)
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    p=OUT_DIR/f"{key}-{title}.png"; c.save(p); return p


def build_contact(items):
    tw,th=700,525; margin=26; hh=50
    sheet=Image.new("RGB",(margin*3+tw*2,margin*3+(hh+th)*2),WHITE)
    d=ImageDraw.Draw(sheet); tf=ImageFont.truetype(SANS,26)
    for i,(key,title,p) in enumerate(items):
        r,c=divmod(i,2); x=margin+c*(tw+margin); y=margin+r*(hh+th+margin)
        d.text((x,y),f"{key}  {title}",font=tf,fill="#25272A")
        im=Image.open(p).convert("RGB"); im.thumbnail((tw,th),Image.Resampling.LANCZOS)
        px=x+(tw-im.width)//2; py=y+hh+(th-im.height)//2; sheet.paste(im,(px,py))
        d.rectangle((px,py,px+im.width-1,py+im.height-1),outline="#C9CDD2",width=1)
    CONTACT.parent.mkdir(parents=True,exist_ok=True); sheet.save(CONTACT,"PNG",optimize=True); return CONTACT


def main():
    outs=[]
    for key,(title,fn) in VARIANTS.items():
        p=render_variant(key,title,fn); outs.append((key,title,p)); print(f"[{key}] {p}")
    print(f"[contact] {build_contact(outs)}")

if __name__ == "__main__": main()
