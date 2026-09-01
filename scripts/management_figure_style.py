"""Reference-matched drawing primitives for management figures.

The renderer targets the 1448×1086, 4:3 visual language approved in the
management-figure reference set: white paper background, blue/orange accent
system, rounded white cards, gradient title tabs, thin dashed separators and
large line-art icons.  All drawing is code-generated with Pillow; no reference
image is used as a background.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from matplotlib import font_manager

WIDTH = 1448
HEIGHT = 1086
SCALE = 2

WHITE = "#FFFFFF"
INK = "#16181B"
TEXT = "#25272A"
MUTED = "#555B63"
FAINT = "#8E969F"
BLUE = "#15569B"
BLUE_DARK = "#0F4B8D"
BLUE_MID = "#2F72AD"
BLUE_BORDER = "#729BC9"
BLUE_LIGHT = "#EEF4FA"
BLUE_LIGHT_2 = "#F6F9FC"
ORANGE = "#EF790D"
ORANGE_DARK = "#D96706"
ORANGE_LIGHT = "#FFF5EA"
GREEN = "#4D8C5E"
GREEN_LIGHT = "#EFF7F1"
RED = "#D84C3F"
GRAY = "#7C8187"
GRAY_LIGHT = "#F1F3F5"
RULE = "#B9C6D4"
RULE_LIGHT = "#D8E0E8"
SHADOW = "#DDE3EA"


def _find_font_path(weight: str) -> str:
    # Prefer known CJK font files first; font-manager family aliases vary across OSes.
    known = {
        "regular": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ],
    }
    for path in known[weight]:
        if Path(path).exists():
            return path

    weight_value = "bold" if weight == "bold" else "regular"
    families = [
        "PingFang SC",
        "Hiragino Sans GB",
        "Noto Sans CJK SC",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
    ]
    for family in families:
        try:
            prop = font_manager.FontProperties(family=family, weight=weight_value)
            path = font_manager.findfont(prop, fallback_to_default=False)
            if path and Path(path).exists():
                return path
        except Exception:
            pass
    fallback = font_manager.findfont(font_manager.FontProperties(weight=weight_value))
    return fallback


_FONT_PATH = {
    "regular": _find_font_path("regular"),
    "bold": _find_font_path("bold"),
}


class FigureCanvas:
    def __init__(self, width: int = WIDTH, height: int = HEIGHT, scale: int = SCALE):
        self.width = width
        self.height = height
        self.scale = scale
        self.image = Image.new("RGB", (width * scale, height * scale), WHITE)
        self.draw = ImageDraw.Draw(self.image)
        self._font_cache: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}

    def _s(self, v: float) -> int:
        return int(round(v * self.scale))

    def _xy(self, p: tuple[float, float]) -> tuple[int, int]:
        return self._s(p[0]), self._s(p[1])

    def font(self, size: float, weight: str = "regular") -> ImageFont.FreeTypeFont:
        key = (self._s(size), weight)
        if key not in self._font_cache:
            self._font_cache[key] = ImageFont.truetype(_FONT_PATH[weight], key[0])
        return self._font_cache[key]

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: float = 22,
        color: str = TEXT,
        weight: str = "regular",
        align: str = "left",
        valign: str = "top",
        spacing: float = 5,
    ) -> None:
        font = self.font(size, weight)
        sx, sy = self._s(x), self._s(y)
        lines = value.split("\n")
        widths: list[int] = []
        heights: list[int] = []
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line or " ", font=font)
            widths.append(bbox[2] - bbox[0])
            heights.append(bbox[3] - bbox[1])
        line_h = max(heights) if heights else self._s(size)
        spacing_px = self._s(spacing)
        total_h = line_h * len(lines) + spacing_px * max(0, len(lines) - 1)
        if valign == "middle":
            sy -= total_h // 2
        elif valign == "bottom":
            sy -= total_h
        for i, line in enumerate(lines):
            w = widths[i]
            tx = sx
            if align == "center":
                tx -= w // 2
            elif align == "right":
                tx -= w
            ty = sy + i * (line_h + spacing_px)
            self.draw.text((tx, ty), line, font=font, fill=color)

    def text_fit(
        self,
        box: tuple[float, float, float, float],
        value: str,
        *,
        max_size: float,
        min_size: float = 12,
        color: str = TEXT,
        weight: str = "regular",
        align: str = "center",
        valign: str = "middle",
    ) -> None:
        x, y, w, h = box
        size = max_size
        while size >= min_size:
            f = self.font(size, weight)
            bb = self.draw.multiline_textbbox((0, 0), value, font=f, spacing=self._s(3))
            if bb[2] - bb[0] <= self._s(w) and bb[3] - bb[1] <= self._s(h):
                break
            size -= 1
        self.text(x + w / 2, y + h / 2, value, size=size, color=color, weight=weight, align=align, valign=valign)

    def line(
        self,
        p1: tuple[float, float],
        p2: tuple[float, float],
        *,
        color: str = RULE,
        width: float = 1.5,
    ) -> None:
        self.draw.line([self._xy(p1), self._xy(p2)], fill=color, width=max(1, self._s(width)))

    def dashed_line(
        self,
        p1: tuple[float, float],
        p2: tuple[float, float],
        *,
        color: str = RULE,
        width: float = 1.4,
        dash: float = 7,
        gap: float = 6,
    ) -> None:
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return
        ux, uy = dx / length, dy / length
        pos = 0.0
        while pos < length:
            end = min(length, pos + dash)
            self.line((x1 + ux * pos, y1 + uy * pos), (x1 + ux * end, y1 + uy * end), color=color, width=width)
            pos += dash + gap

    def rounded_rect(
        self,
        box: tuple[float, float, float, float],
        *,
        fill: str = WHITE,
        outline: str | None = BLUE_BORDER,
        width: float = 1.5,
        radius: float = 16,
        shadow: bool = False,
        shadow_offset: tuple[float, float] = (4, 5),
    ) -> None:
        x, y, w, h = box
        if shadow:
            layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ox, oy = shadow_offset
            ld.rounded_rectangle(
                [self._s(x + ox), self._s(y + oy), self._s(x + w + ox), self._s(y + h + oy)],
                radius=self._s(radius), fill=(55, 75, 95, 30),
            )
            layer = layer.filter(ImageFilter.GaussianBlur(self._s(4)))
            self.image.paste(layer, (0, 0), layer)
            self.draw = ImageDraw.Draw(self.image)
        self.draw.rounded_rectangle(
            [self._s(x), self._s(y), self._s(x + w), self._s(y + h)],
            radius=self._s(radius),
            fill=fill,
            outline=outline,
            width=max(1, self._s(width)) if outline else 0,
        )

    def gradient_rect(
        self,
        box: tuple[float, float, float, float],
        *,
        top: str = BLUE_DARK,
        bottom: str = BLUE_MID,
        radius: float = 14,
        outline: str | None = None,
    ) -> None:
        x, y, w, h = box
        sw, sh = self._s(w), self._s(h)
        grad = Image.new("RGB", (sw, sh), top)
        gd = ImageDraw.Draw(grad)
        c1 = tuple(int(top[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(bottom[i:i+2], 16) for i in (1, 3, 5))
        for yy in range(sh):
            t = yy / max(1, sh - 1)
            c = tuple(round(a * (1 - t) + b * t) for a, b in zip(c1, c2))
            gd.line((0, yy, sw, yy), fill=c)
        mask = Image.new("L", (sw, sh), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, sw - 1, sh - 1), radius=self._s(radius), fill=255)
        self.image.paste(grad, (self._s(x), self._s(y)), mask)
        self.draw = ImageDraw.Draw(self.image)
        if outline:
            self.draw.rounded_rectangle(
                [self._s(x), self._s(y), self._s(x + w), self._s(y + h)],
                radius=self._s(radius), outline=outline, width=self._s(1.2),
            )

    def circle(self, cx: float, cy: float, r: float, *, fill: str | None = None, outline: str | None = None, width: float = 1.5) -> None:
        box = [self._s(cx-r), self._s(cy-r), self._s(cx+r), self._s(cy+r)]
        self.draw.ellipse(box, fill=fill, outline=outline, width=max(1, self._s(width)) if outline else 1)

    def ellipse(self, box: tuple[float, float, float, float], *, fill: str | None = None, outline: str | None = None, width: float = 1.5) -> None:
        x, y, w, h = box
        self.draw.ellipse([self._s(x), self._s(y), self._s(x+w), self._s(y+h)], fill=fill, outline=outline, width=max(1, self._s(width)) if outline else 1)

    def polygon(self, points: Iterable[tuple[float, float]], *, fill: str | None = None, outline: str | None = None) -> None:
        pts = [self._xy(p) for p in points]
        self.draw.polygon(pts, fill=fill)
        if outline:
            self.draw.line(pts + [pts[0]], fill=outline, width=self._s(1.5), joint="curve")

    def arc(self, box: tuple[float, float, float, float], start: float, end: float, *, color: str = BLUE, width: float = 3) -> None:
        x, y, w, h = box
        self.draw.arc([self._s(x), self._s(y), self._s(x+w), self._s(y+h)], start=start, end=end, fill=color, width=self._s(width))

    def arrow(
        self,
        p1: tuple[float, float],
        p2: tuple[float, float],
        *,
        color: str = GRAY,
        width: float = 3,
        head: float = 12,
        glow: bool = False,
    ) -> None:
        x1, y1 = p1
        x2, y2 = p2
        if glow:
            layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.line([self._xy(p1), self._xy(p2)], fill=(68, 113, 173, 70), width=self._s(14))
            layer = layer.filter(ImageFilter.GaussianBlur(self._s(6)))
            self.image.paste(layer, (0, 0), layer)
            self.draw = ImageDraw.Draw(self.image)
        self.line(p1, p2, color=color, width=width)
        angle = math.atan2(y2 - y1, x2 - x1)
        a1 = angle + math.radians(150)
        a2 = angle - math.radians(150)
        p3 = (x2 + head * math.cos(a1), y2 + head * math.sin(a1))
        p4 = (x2 + head * math.cos(a2), y2 + head * math.sin(a2))
        self.polygon([p2, p3, p4], fill=color)

    def title(self, number: int, title: str) -> None:
        self.text(18, 16, f"图{number}  {title}", size=34, color=INK, weight="bold")

    def tab(self, box: tuple[float, float, float, float], label: str, *, orange: bool = False, size: float = 25) -> None:
        if orange:
            self.gradient_rect(box, top="#F28B22", bottom=ORANGE, radius=12)
        else:
            self.gradient_rect(box, top=BLUE_DARK, bottom=BLUE_MID, radius=12)
        x, y, w, h = box
        self.text(x + w/2, y + h/2 - 2, label, size=size, color=WHITE, weight="bold", align="center", valign="middle")

    def bottom_rule(self, y: float = 1014, caption: str | None = None, *, caption_color: str = TEXT, caption_size: float = 23) -> None:
        self.dashed_line((50, y), (1398, y), color="#6D94BF", width=1.5, dash=6, gap=5)
        self.circle(50, y, 4, fill=BLUE)
        self.circle(1398, y, 4, fill=BLUE)
        if caption:
            f = self.font(caption_size, "regular")
            bb = self.draw.textbbox((0, 0), caption, font=f)
            tw = (bb[2]-bb[0]) / self.scale
            self.rounded_rect((724 - tw/2 - 24, y - 19, tw + 48, 42), fill=WHITE, outline=None, radius=0)
            self.text(724, y + 18, caption, size=caption_size, color=caption_color, align="center", valign="middle")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        out = self.image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        out.save(path, "PNG", optimize=True)

    def paste_photo(self, path: Path, box: tuple[float, float, float, float], *, radius: float = 7) -> None:
        x, y, w, h = box
        if not path.exists():
            self.rounded_rect(box, fill=GRAY_LIGHT, outline=RULE, width=1, radius=radius)
            self.text(x+w/2, y+h/2, "脱敏示例照片", size=16, color=MUTED, align="center", valign="middle")
            return
        img = Image.open(path).convert("RGB")
        target_ratio = w / h
        src_ratio = img.width / img.height
        if src_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))
        img = img.resize((self._s(w), self._s(h)), Image.Resampling.LANCZOS)
        mask = Image.new("L", img.size, 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, img.width-1, img.height-1), radius=self._s(radius), fill=255)
        self.image.paste(img, (self._s(x), self._s(y)), mask)
        self.draw = ImageDraw.Draw(self.image)

    def icon(self, name: str, cx: float, cy: float, size: float, *, color: str = BLUE, accent: str | None = None) -> None:
        fn = getattr(self, f"_icon_{name}", None)
        if not fn:
            raise ValueError(f"unknown icon: {name}")
        fn(cx, cy, size, color, accent or color)

    def _icon_users(self, cx, cy, s, c, a):
        self.circle(cx, cy-s*.20, s*.13, fill=c)
        self.circle(cx-s*.23, cy-s*.14, s*.10, fill=c)
        self.circle(cx+s*.23, cy-s*.14, s*.10, fill=c)
        self.rounded_rect((cx-s*.19, cy-s*.03, s*.38, s*.30), fill=c, outline=None, radius=s*.09)
        self.rounded_rect((cx-s*.37, cy, s*.20, s*.22), fill=c, outline=None, radius=s*.07)
        self.rounded_rect((cx+s*.17, cy, s*.20, s*.22), fill=c, outline=None, radius=s*.07)

    def _icon_clock(self, cx, cy, s, c, a):
        self.circle(cx, cy, s*.37, outline=c, width=s*.035)
        self.line((cx, cy-s*.23), (cx, cy+s*.03), color=c, width=s*.04)
        self.line((cx, cy+s*.03), (cx+s*.18, cy+s*.12), color=c, width=s*.04)

    def _icon_shield(self, cx, cy, s, c, a):
        pts=[(cx,cy-s*.38),(cx+s*.30,cy-s*.25),(cx+s*.26,cy+s*.15),(cx,cy+s*.38),(cx-s*.26,cy+s*.15),(cx-s*.30,cy-s*.25)]
        self.draw.line([self._xy(p) for p in pts+[pts[0]]], fill=c, width=self._s(s*.035), joint="curve")
        self.line((cx-s*.11, cy), (cx-s*.01, cy+s*.11), color=c, width=s*.04)
        self.line((cx-s*.01, cy+s*.11), (cx+s*.17, cy-s*.10), color=c, width=s*.04)

    def _icon_shield_alert(self, cx, cy, s, c, a):
        self._icon_shield(cx, cy, s, c, a)
        self.line((cx,cy-s*.12),(cx,cy+s*.09),color=c,width=s*.04)
        self.circle(cx,cy+s*.20,s*.025,fill=c)

    def _icon_scale(self, cx, cy, s, c, a):
        self.line((cx,cy-s*.30),(cx,cy+s*.30),color=c,width=s*.035)
        self.line((cx-s*.27,cy-s*.20),(cx+s*.27,cy-s*.20),color=c,width=s*.035)
        self.line((cx-s*.18,cy-s*.20),(cx-s*.28,cy+s*.05),color=c,width=s*.025)
        self.line((cx-s*.18,cy-s*.20),(cx-s*.08,cy+s*.05),color=c,width=s*.025)
        self.arc((cx-s*.30,cy-.02*s,s*.25,s*.15),0,180,color=c,width=s*.025)
        self.line((cx+s*.18,cy-s*.20),(cx+s*.28,cy+s*.05),color=c,width=s*.025)
        self.line((cx+s*.18,cy-s*.20),(cx+s*.08,cy+s*.05),color=c,width=s*.025)
        self.arc((cx+s*.05,cy-.02*s,s*.25,s*.15),0,180,color=c,width=s*.025)
        self.line((cx-s*.16,cy+s*.31),(cx+s*.16,cy+s*.31),color=c,width=s*.035)

    def _icon_chart(self, cx, cy, s, c, a):
        self.line((cx-s*.28,cy+s*.28),(cx+s*.29,cy+s*.28),color=c,width=s*.025)
        for i,h in enumerate([.18,.30,.45]):
            x=cx-s*.18+i*s*.18
            self.rounded_rect((x,cy+s*.28-s*h,s*.10,s*h),fill=c,outline=None,radius=s*.015)
        self.arc((cx-s*.25,cy-s*.32,s*.58,s*.35),20,120,color=c,width=s*.035)
        self.arrow((cx+s*.10,cy-s*.18),(cx+s*.27,cy-s*.36),color=c,width=s*.025,head=s*.08)

    def _icon_network(self, cx, cy, s, c, a):
        self.circle(cx,cy,s*.16,fill=c)
        for ang in [0,72,144,216,288]:
            r=s*.32; ex=cx+math.cos(math.radians(ang))*r; ey=cy+math.sin(math.radians(ang))*r
            self.line((cx,cy),(ex,ey),color=c,width=s*.025)
            self.circle(ex,ey,s*.055,fill=WHITE,outline=c,width=s*.025)

    def _icon_folder(self, cx, cy, s, c, a):
        pts=[(cx-s*.34,cy-s*.18),(cx-s*.05,cy-s*.18),(cx+s*.04,cy-s*.08),(cx+s*.34,cy-s*.08),(cx+s*.27,cy+s*.28),(cx-s*.37,cy+s*.28)]
        self.polygon(pts,fill=c)
        self.polygon([(cx-s*.30,cy-s*.07),(cx+s*.32,cy-s*.07),(cx+s*.25,cy+s*.23),(cx-s*.34,cy+s*.23)],fill=BLUE_MID if c==BLUE else c)

    def _icon_image(self, cx, cy, s, c, a):
        self.rounded_rect((cx-s*.33,cy-s*.26,s*.66,s*.52),fill=WHITE,outline=c,width=s*.03,radius=s*.04)
        self.circle(cx-s*.17,cy-s*.10,s*.045,fill=c)
        self.polygon([(cx-s*.27,cy+s*.18),(cx-s*.08,cy-.01*s),(cx+s*.03,cy+s*.09),(cx+s*.15,cy-s*.03),(cx+s*.28,cy+s*.18)],fill=c)

    def _icon_database(self, cx, cy, s, c, a):
        self.ellipse((cx-s*.30,cy-s*.31,s*.60,s*.18),fill=c)
        self.rounded_rect((cx-s*.30,cy-s*.22,s*.60,s*.48),fill=c,outline=None,radius=s*.03)
        for yy in [-.08,.08,.24]:
            self.arc((cx-s*.30,cy+s*yy-s*.09,s*.60,s*.18),0,180,color=WHITE,width=s*.018)

    def _icon_warning(self, cx, cy, s, c, a):
        pts=[(cx,cy-s*.36),(cx+s*.36,cy+s*.28),(cx-s*.36,cy+s*.28)]
        self.draw.line([self._xy(p) for p in pts+[pts[0]]],fill=c,width=self._s(s*.035),joint="curve")
        self.line((cx,cy-s*.12),(cx,cy+s*.10),color=c,width=s*.04)
        self.circle(cx,cy+s*.19,s*.025,fill=c)

    def _icon_person_check(self, cx, cy, s, c, a):
        self.circle(cx-s*.08,cy-s*.16,s*.12,fill=c)
        self.rounded_rect((cx-s*.25,cy-s*.01,s*.34,s*.28),fill=c,outline=None,radius=s*.10)
        self.circle(cx+s*.20,cy+s*.14,s*.13,fill=BLUE_MID)
        self.line((cx+s*.14,cy+s*.14),(cx+s*.19,cy+s*.19),color=WHITE,width=s*.035)
        self.line((cx+s*.19,cy+s*.19),(cx+s*.27,cy+s*.09),color=WHITE,width=s*.035)

    def _icon_clipboard(self, cx, cy, s, c, a):
        self.rounded_rect((cx-s*.28,cy-s*.29,s*.56,s*.62),fill=WHITE,outline=c,width=s*.03,radius=s*.05)
        self.rounded_rect((cx-s*.10,cy-s*.38,s*.20,s*.16),fill=WHITE,outline=c,width=s*.03,radius=s*.04)
        for yy in [-.10,.05,.20]:
            self.line((cx-s*.15,cy+s*yy),(cx+s*.18,cy+s*yy),color=c,width=s*.025)
        self.line((cx-s*.20,cy-.10*s),(cx-s*.15,cy-.05*s),color=c,width=s*.025)
        self.line((cx-s*.15,cy-.05*s),(cx-s*.08,cy-.15*s),color=c,width=s*.025)

    def _icon_camera(self, cx, cy, s, c, a):
        self.rounded_rect((cx-s*.34,cy-s*.20,s*.68,s*.45),fill=c,outline=None,radius=s*.06)
        self.rounded_rect((cx-s*.15,cy-s*.31,s*.30,s*.14),fill=c,outline=None,radius=s*.04)
        self.circle(cx,cy+s*.02,s*.14,fill=WHITE)
        self.circle(cx,cy+s*.02,s*.09,fill=c)
        self.circle(cx+s*.23,cy-s*.10,s*.035,fill=WHITE)

    def _icon_camera_check(self, cx, cy, s, c, a):
        self._icon_camera(cx-s*.05,cy-s*.03,s*.80,c,a)
        self.circle(cx+s*.25,cy+s*.22,s*.16,fill=ORANGE)
        self.line((cx+s*.17,cy+s*.22),(cx+s*.23,cy+s*.28),color=WHITE,width=s*.035)
        self.line((cx+s*.23,cy+s*.28),(cx+s*.34,cy+s*.15),color=WHITE,width=s*.035)

    def _icon_upload(self, cx, cy, s, c, a):
        self.line((cx,cy+s*.20),(cx,cy-s*.24),color=c,width=s*.045)
        self.arrow((cx-s*.01,cy-s*.08),(cx,cy-s*.29),color=c,width=s*.04,head=s*.11)
        self.arc((cx-s*.30,cy+s*.05,s*.60,s*.32),0,180,color=c,width=s*.035)
        self.line((cx-s*.30,cy+s*.21),(cx-s*.30,cy+s*.05),color=c,width=s*.035)
        self.line((cx+s*.30,cy+s*.21),(cx+s*.30,cy+s*.05),color=c,width=s*.035)

    def _icon_magnifier(self, cx, cy, s, c, a):
        self.circle(cx-s*.07,cy-s*.08,s*.20,outline=c,width=s*.04)
        self.line((cx+s*.08,cy+s*.07),(cx+s*.30,cy+s*.30),color=c,width=s*.05)

    def _icon_bell(self, cx, cy, s, c, a):
        self.arc((cx-s*.24,cy-s*.30,s*.48,s*.48),180,360,color=c,width=s*.035)
        self.line((cx-s*.24,cy-s*.06),(cx-s*.24,cy+s*.15),color=c,width=s*.035)
        self.line((cx+s*.24,cy-s*.06),(cx+s*.24,cy+s*.15),color=c,width=s*.035)
        self.line((cx-s*.30,cy+s*.15),(cx+s*.30,cy+s*.15),color=c,width=s*.035)
        self.circle(cx,cy+s*.23,s*.05,fill=c)

    def _icon_funnel(self, cx, cy, s, c, a):
        pts=[(cx-s*.32,cy-s*.28),(cx+s*.32,cy-s*.28),(cx+s*.10,cy-.02*s),(cx+s*.04,cy+s*.25),(cx-s*.05,cy+s*.31),(cx-s*.10,cy-.02*s)]
        self.draw.line([self._xy(p) for p in pts+[pts[0]]],fill=c,width=self._s(s*.035),joint="curve")

    def _icon_target(self, cx, cy, s, c, a):
        for r in [.32,.20,.07]:
            self.circle(cx,cy,s*r,outline=c,width=s*.03)
        self.arrow((cx+s*.06,cy-s*.06),(cx+s*.31,cy-s*.31),color=c,width=s*.03,head=s*.09)

    def _icon_route(self, cx, cy, s, c, a):
        self.rounded_rect((cx-s*.25,cy-s*.30,s*.50,s*.60),fill=WHITE,outline=c,width=s*.03,radius=s*.05)
        self.circle(cx+s*.08,cy-s*.06,s*.08,outline=c,width=s*.025)
        self.circle(cx+s*.08,cy-s*.06,s*.025,fill=c)
        self.dashed_line((cx-s*.10,cy+s*.20),(cx+s*.08,cy+s*.02),color=c,width=s*.02,dash=s*.05,gap=s*.03)

    def _icon_management(self, cx, cy, s, c, a):
        self.circle(cx,cy-s*.24,s*.09,fill=c)
        self.circle(cx-s*.23,cy+s*.02,s*.08,fill=c)
        self.circle(cx+s*.23,cy+s*.02,s*.08,fill=c)
        self.line((cx,cy-s*.10),(cx,cy+s*.04),color=c,width=s*.025)
        self.line((cx,cy),(cx-s*.15,cy+s*.02),color=c,width=s*.025)
        self.line((cx,cy),(cx+s*.15,cy+s*.02),color=c,width=s*.025)
        self.rounded_rect((cx-s*.32,cy+s*.11,s*.18,s*.16),fill=c,outline=None,radius=s*.06)
        self.rounded_rect((cx+s*.14,cy+s*.11,s*.18,s*.16),fill=c,outline=None,radius=s*.06)
        self.rounded_rect((cx-s*.09,cy-s*.01,s*.18,s*.16),fill=c,outline=None,radius=s*.06)

    def _icon_worker_phone(self, cx, cy, s, c, a):
        self.circle(cx-s*.13,cy-s*.08,s*.10,outline=c,width=s*.025)
        self.arc((cx-s*.26,cy-s*.20,s*.26,s*.18),180,360,color=c,width=s*.035)
        self.line((cx-s*.27,cy-s*.10),(cx-s*.02,cy-s*.10),color=c,width=s*.035)
        self.arc((cx-s*.30,cy+s*.02,s*.36,s*.30),180,360,color=c,width=s*.035)
        self.rounded_rect((cx+s*.08,cy-s*.20,s*.25,s*.48),fill=WHITE,outline=c,width=s*.028,radius=s*.05)
        self.circle(cx+s*.20,cy+s*.02,s*.045,outline=c,width=s*.025)
        self.line((cx+s*.18,cy+s*.02),(cx+s*.25,cy+s*.08),color=c,width=s*.022)

    def _icon_tower(self, cx, cy, s, c, a):
        self.line((cx,cy-s*.35),(cx-s*.18,cy+s*.32),color=c,width=s*.025)
        self.line((cx,cy-s*.35),(cx+s*.18,cy+s*.32),color=c,width=s*.025)
        for yy,w in [(-.22,.22),(-.08,.34),(.08,.42),(.24,.30)]:
            self.line((cx-s*w/2,cy+s*yy),(cx+s*w/2,cy+s*yy),color=c,width=s*.022)
        self.line((cx-s*.18,cy+s*.32),(cx+s*.18,cy+s*.32),color=c,width=s*.025)

    def _icon_bird(self, cx, cy, s, c, a):
        self.arc((cx-s*.30,cy-s*.12,s*.34,s*.25),195,340,color=c,width=s*.035)
        self.arc((cx-s*.02,cy-s*.17,s*.32,s*.30),205,345,color=c,width=s*.035)
        self.line((cx-s*.02,cy+s*.02),(cx-s*.12,cy+s*.28),color=c,width=s*.025)
        self.line((cx-s*.02,cy+s*.02),(cx+s*.10,cy+s*.25),color=c,width=s*.025)

    def _icon_firework(self, cx, cy, s, c, a):
        for ang in range(0,360,45):
            r1=s*.10; r2=s*.34
            self.line((cx+math.cos(math.radians(ang))*r1,cy+math.sin(math.radians(ang))*r1),(cx+math.cos(math.radians(ang))*r2,cy+math.sin(math.radians(ang))*r2),color=c,width=s*.025)
        self.circle(cx,cy,s*.045,fill=c)
        for ang in [22,112,202,292]:
            r=s*.27
            self.circle(cx+math.cos(math.radians(ang))*r,cy+math.sin(math.radians(ang))*r,s*.025,fill=c)

    def _icon_weather(self, cx, cy, s, c, a):
        self.arc((cx-s*.26,cy-s*.10,s*.35,s*.25),180,360,color=c,width=s*.03)
        self.arc((cx-s*.05,cy-s*.18,s*.35,s*.30),180,360,color=c,width=s*.03)
        self.line((cx-s*.20,cy+s*.03),(cx+s*.27,cy+s*.03),color=c,width=s*.03)
        for dx in [-.12,.02,.16]:
            self.line((cx+s*dx,cy+s*.12),(cx+s*(dx-.04),cy+s*.23),color=c,width=s*.022)

    def _icon_monitor(self, cx, cy, s, c, a):
        self.rounded_rect((cx-s*.34,cy-s*.24,s*.68,s*.42),fill=WHITE,outline=c,width=s*.03,radius=s*.04)
        for i,h in enumerate([.12,.20,.30]):
            self.rounded_rect((cx-s*.20+i*s*.15,cy+s*.10-s*h,s*.07,s*h),fill=c,outline=None,radius=s*.01)
        self.line((cx,cy+s*.18),(cx,cy+s*.30),color=c,width=s*.03)
        self.line((cx-s*.17,cy+s*.30),(cx+s*.17,cy+s*.30),color=c,width=s*.03)
        self._icon_warning(cx+s*.25,cy-s*.17,s*.30,ORANGE,ORANGE)

    def _icon_shield_loop(self, cx, cy, s, c, a):
        self._icon_shield(cx,cy-s*.06,s*.55,c,a)
        self.arc((cx-s*.34,cy+s*.08,s*.68,s*.42),10,165,color=c,width=s*.025)
        self.arrow((cx-s*.23,cy+s*.19),(cx-s*.34,cy+s*.10),color=c,width=s*.022,head=s*.07)
        self.arc((cx-s*.34,cy+s*.10,s*.68,s*.42),190,345,color=c,width=s*.025)
        self.arrow((cx+s*.23,cy+s*.27),(cx+s*.34,cy+s*.20),color=c,width=s*.022,head=s*.07)
