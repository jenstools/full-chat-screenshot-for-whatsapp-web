#!/usr/bin/env python3
"""Generate the extension icon set + store assets.

Concept: a WhatsApp-green rounded tile holding a white chat bubble whose
message lines double as a camera viewfinder, with a small shutter lens in the
corner — "screenshot of a conversation". Rendered at 4x then downscaled with
LANCZOS for crisp small sizes.
"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(OUT, exist_ok=True)

GREEN_TOP = (37, 211, 102)    # #25D366
GREEN_BOT = (18, 140, 126)    # #128C7E
WHITE = (255, 255, 255)
SS = 4  # supersample factor


def vgradient(size, top, bot):
    img = Image.new("RGB", (1, size), 0)
    for y in range(size):
        t = y / max(1, size - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img.resize((size, size))


def draw_icon(px):
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # rounded tile background (gradient)
    radius = int(s * 0.22)
    grad = vgradient(s, GREEN_TOP, GREEN_BOT).convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)

    # white chat bubble
    bx0, by0 = int(s * 0.18), int(s * 0.20)
    bx1, by1 = int(s * 0.82), int(s * 0.66)
    br = int(s * 0.10)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=br, fill=WHITE)
    # bubble tail (bottom-left)
    tw = int(s * 0.10)
    d.polygon(
        [(bx0 + int(s * 0.08), by1 - 2),
         (bx0 + int(s * 0.08), by1 + tw),
         (bx0 + int(s * 0.08) + tw, by1 - 2)],
        fill=WHITE,
    )

    # message lines (green) inside bubble
    line_color = GREEN_BOT
    lh = int(s * 0.045)
    lx0 = bx0 + int(s * 0.10)
    for i, frac in enumerate([0.60, 0.46, 0.34]):
        ly = by0 + int(s * 0.11) + i * int(s * 0.115)
        lx1 = lx0 + int((bx1 - bx0) * frac)
        d.rounded_rectangle([lx0, ly, lx1, ly + lh], radius=lh // 2, fill=line_color)

    # shutter lens (capture hint), bottom-right overlapping the bubble
    cx, cy, cr = int(s * 0.74), int(s * 0.66), int(s * 0.12)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=GREEN_TOP, outline=WHITE, width=max(1, int(s * 0.018)))
    ir = int(cr * 0.42)
    d.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=WHITE)

    return img.resize((px, px), Image.LANCZOS)


for size in (16, 32, 48, 128):
    draw_icon(size).save(os.path.join(OUT, f"icon-{size}.png"))
    print("wrote icon-%d.png" % size)

# 512 store icon
draw_icon(512).save(os.path.join(OUT, "icon-512.png"))
print("wrote icon-512.png")

# 440x280 small promo tile: tile icon left, text feel via larger icon centered-left
promo = Image.new("RGB", (440, 280), GREEN_BOT)
g = vgradient(440, GREEN_TOP, GREEN_BOT)
promo.paste(g.crop((0, 0, 440, 280)))
ic = draw_icon(180)
promo.paste(ic, (40, 50), ic)
promo.save(os.path.join(OUT, "promo-440x280.png"))
print("wrote promo-440x280.png")
