"""Generates creaper's brand images: the mark, a README banner and a video thumbnail.

The mark is a "c" drawn as waveform bars sweeping around an arc, with a playhead
dot glowing in its opening. Run with Pillow installed:

    python assets/make_brand.py

Writes SVGs (crisp at any size, used in the README) and PNGs (for video/social).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent / "brand"

BG = (14, 17, 23)
BG_LIFT = (24, 30, 42)
TEAL = (46, 230, 197)
VIOLET = (139, 92, 246)
PINK = (244, 114, 182)
TEXT = (236, 240, 246)
MUTED = (139, 148, 163)

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
SVG_FONT = "'Segoe UI', Inter, 'Helvetica Neue', Arial, sans-serif"


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def gradient(t: float) -> tuple:
    """Teal -> violet -> pink along the arc."""
    return lerp(TEAL, VIOLET, t * 2) if t < 0.5 else lerp(VIOLET, PINK, (t - 0.5) * 2)


def hexcolor(c: tuple) -> str:
    return "#%02X%02X%02X" % c


def bars(cx: float, cy: float, radius: float, scale: float) -> list[tuple]:
    """The mark's bars: (x1, y1, x2, y2, width, color) radial strokes around a "c"."""
    count = 30
    start, end = math.radians(42), math.radians(318)  # opening on the right
    out = []
    for i in range(count):
        t = i / (count - 1)
        angle = start + (end - start) * t
        # A waveform: two overlapping sines, tapering toward the opening.
        wave = 0.55 + 0.45 * abs(math.sin(i * 0.9) * 0.7 + math.sin(i * 0.37 + 1.0) * 0.3)
        taper = math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.6
        half = (16 + 46 * wave * taper) * scale
        dx, dy = math.cos(angle), -math.sin(angle)
        out.append((cx + dx * (radius - half), cy + dy * (radius - half),
                    cx + dx * (radius + half), cy + dy * (radius + half), 11 * scale, gradient(t)))
    return out


def playhead(cx: float, cy: float, radius: float, scale: float) -> tuple:
    return cx + radius, cy, 15 * scale


# ----------------------------------------------------------------------- SVG

def svg_mark(cx: float, cy: float, radius: float, scale: float) -> str:
    parts = []
    for x1, y1, x2, y2, w, c in bars(cx, cy, radius, scale):
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{hexcolor(c)}" '
                     f'stroke-width="{w:.1f}" stroke-linecap="round"/>')
    px, py, r = playhead(cx, cy, radius, scale)
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r * 2.6:.1f}" fill="url(#halo)"/>')
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r:.1f}" fill="{hexcolor(TEAL)}"/>')
    return "\n  ".join(parts)


SVG_DEFS = f"""<defs>
    <radialGradient id="bg" cx="35%" cy="40%" r="80%">
      <stop offset="0" stop-color="{hexcolor(BG_LIFT)}"/><stop offset="1" stop-color="{hexcolor(BG)}"/>
    </radialGradient>
    <radialGradient id="halo">
      <stop offset="0" stop-color="{hexcolor(TEAL)}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{hexcolor(TEAL)}" stop-opacity="0"/>
    </radialGradient>
  </defs>"""


def write_svgs() -> None:
    icon = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  {SVG_DEFS}
  <rect width="512" height="512" rx="112" fill="url(#bg)"/>
  {svg_mark(246, 256, 150, 1.0)}
</svg>
"""
    (OUT / "creaper-icon.svg").write_text(icon, encoding="utf-8")
    banner = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="320" viewBox="0 0 1280 320">
  {SVG_DEFS}
  <rect width="1280" height="320" rx="28" fill="url(#bg)"/>
  {svg_mark(196, 160, 96, 0.64)}
  <text x="350" y="178" font-family="{SVG_FONT}" font-size="112" font-weight="700" fill="{hexcolor(TEXT)}" letter-spacing="-2">creaper</text>
  <text x="354" y="232" font-family="{SVG_FONT}" font-size="30" fill="{hexcolor(MUTED)}">An AI producer that lives inside REAPER</text>
</svg>
"""
    (OUT / "creaper-banner.svg").write_text(banner, encoding="utf-8")


# ----------------------------------------------------------------------- PNG

SS = 4  # supersampling for smooth edges


def background(w: int, h: int, radius: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(glow)
    for i in range(40, 0, -1):  # soft lift toward the upper left
        t = i / 40
        d.ellipse([w * 0.35 - w * t, h * 0.4 - h * t * 1.2, w * 0.35 + w * t, h * 0.4 + h * t * 1.2],
                  fill=lerp(BG_LIFT, BG, t))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    img.paste(glow, (0, 0), mask)
    return img


def draw_mark(img: Image.Image, cx: float, cy: float, radius: float, scale: float) -> None:
    d = ImageDraw.Draw(img)
    for x1, y1, x2, y2, w, c in bars(cx, cy, radius, scale):
        d.line([x1, y1, x2, y2], fill=c, width=round(w))
        for x, y in ((x1, y1), (x2, y2)):  # round caps
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=c)
    px, py, r = playhead(cx, cy, radius, scale)
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([px - r * 2.2, py - r * 2.2, px + r * 2.2, py + r * 2.2], fill=TEAL + (150,))
    halo = halo.filter(ImageFilter.GaussianBlur(r * 1.2))
    img.alpha_composite(halo)
    ImageDraw.Draw(img).ellipse([px - r, py - r, px + r, py + r], fill=TEAL)


def text(img: Image.Image, xy: tuple, s: str, size: int, color: tuple, bold: bool = False) -> None:
    font = ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)
    ImageDraw.Draw(img).text(xy, s, font=font, fill=color, anchor="ls")


def save(img: Image.Image, name: str, w: int, h: int) -> None:
    img.resize((w, h), Image.LANCZOS).save(OUT / name)


def write_pngs() -> None:
    icon = background(512 * SS, 512 * SS, 112 * SS)
    draw_mark(icon, 246 * SS, 256 * SS, 150 * SS, 1.0 * SS)
    save(icon, "creaper-icon.png", 512, 512)

    banner = background(1280 * SS, 320 * SS, 28 * SS)
    draw_mark(banner, 196 * SS, 160 * SS, 96 * SS, 0.64 * SS)
    text(banner, (350 * SS, 178 * SS), "creaper", 112 * SS, TEXT, bold=True)
    text(banner, (354 * SS, 232 * SS), "An AI producer that lives inside REAPER", 30 * SS, MUTED)
    save(banner, "creaper-banner.png", 1280, 320)

    thumb = background(1280 * SS, 720 * SS, 0)
    draw_mark(thumb, 330 * SS, 360 * SS, 190 * SS, 1.27 * SS)
    text(thumb, (600 * SS, 380 * SS), "creaper", 150 * SS, TEXT, bold=True)
    text(thumb, (606 * SS, 460 * SS), "an AI producer", 54 * SS, MUTED)
    text(thumb, (606 * SS, 530 * SS), "inside REAPER", 54 * SS, TEAL, bold=True)
    save(thumb, "creaper-thumbnail.png", 1280, 720)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_svgs()
    write_pngs()
    for f in sorted(OUT.iterdir()):
        print(f.name, f.stat().st_size)
