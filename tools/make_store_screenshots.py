#!/usr/bin/env python3
"""Generate Chrome Web Store marketing screenshots (1280x800 PNG) plus a
1400x560 marquee and a 440x280 small promo tile — ready to upload.

These are stylized mockups of the popup UI and the stitched-image result,
drawn with PIL. Run:  python3 tools/make_store_screenshots.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "store")
os.makedirs(OUT, exist_ok=True)

# ---- palette ----
BG0, BG1 = (11, 20, 26), (5, 11, 16)        # WhatsApp dark
PANEL = (17, 27, 33)                         # #111b21
PANEL2 = (32, 44, 51)
GREEN = (37, 211, 102)                       # #25D366
GREEN_D = (18, 140, 126)
BUBBLE_IN = (32, 44, 51)                     # incoming
BUBBLE_OUT = (0, 92, 75)                     # #005c4b outgoing
TEXT = (233, 237, 239)
MUTED = (142, 154, 162)
WHITE = (255, 255, 255)

AR = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def vgrad(w, h, top, bot):
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return img.resize((w, h))


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def shadow_card(base, box, radius, fill, blur=18, alpha=120):
    """Draw a rounded card with a soft drop shadow onto base (RGBA)."""
    from PIL import ImageFilter
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0, y0 + 8, x1, y1 + 12], radius=radius, fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh)
    ImageDraw.Draw(base).rounded_rectangle(box, radius=radius, fill=fill)


def wallpaper(w, h):
    """WhatsApp-ish dotted dark wallpaper."""
    img = Image.new("RGB", (w, h), (10, 18, 22))
    d = ImageDraw.Draw(img)
    step = 26
    for y in range(0, h, step):
        for x in range(0, w, step):
            d.ellipse([x, y, x + 3, y + 3], fill=(16, 26, 31))
    return img


def bubble(d, x, y, w, text, lines, outgoing, fbody, ftime, time="08:21"):
    pad = 14
    lh = 26
    h = pad * 2 + lh * lines + 6
    col = BUBBLE_OUT if outgoing else BUBBLE_IN
    if outgoing:
        x = x  # caller positions right-aligned already
    d.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=col)
    ty = y + pad
    for ln in text:
        d.text((x + pad, ty), ln, font=fbody, fill=TEXT)
        ty += lh
    d.text((x + w - 54, y + h - 24), time, font=ftime, fill=(170, 190, 185) if outgoing else MUTED)
    if outgoing:
        d.text((x + w - 22, y + h - 24), "✓✓", font=ftime, fill=(90, 200, 255))
    return h


def headline(img, title, sub):
    d = ImageDraw.Draw(img)
    ft = font(ARB, 52)
    fs = font(AR, 26)
    d.text((80, 70), title, font=ft, fill=WHITE)
    if sub:
        d.text((80, 138), sub, font=fs, fill=GREEN)


def chat_panel(img, box):
    """Render a mock WhatsApp chat into box. Returns nothing."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    wp = wallpaper(w, h)
    img.paste(wp, (x0, y0))
    d = ImageDraw.Draw(img)
    # header
    d.rectangle([x0, y0, x1, y0 + 56], fill=PANEL)
    d.ellipse([x0 + 14, y0 + 12, x0 + 46, y0 + 44], fill=GREEN_D)
    fb = font(ARB, 20)
    fsm = font(AR, 15)
    d.text((x0 + 58, y0 + 12), "Anna", font=fb, fill=TEXT)
    d.text((x0 + 58, y0 + 34), "online", font=fsm, fill=MUTED)

    fbody = font(AR, 17)
    ftime = font(AR, 12)
    cy = y0 + 72
    msgs = [
        (False, ["Wir müssen heute telefonieren.", "Wann passt es dir?"], 2),
        (True, ["Samstag wäre ein guter", "Zeitraum für Besichtigungen."], 2),
        (False, ["Wann genau bei dir?"], 1),
        (True, ["Ich melde mich nachher.", "Passt 18 Uhr?"], 2),
        (False, ["Ist das jetzt bei der", "nächsten Miete auch so?"], 2),
    ]
    for outgoing, lines, n in msgs:
        bw = 320
        bx = x1 - bw - 16 if outgoing else x0 + 16
        bh = bubble(d, bx, cy, bw, None, n, outgoing, fbody, ftime, lines=lines) if False else None
        # simpler: inline
        pad = 12
        lh = 24
        bh = pad * 2 + lh * n
        col = BUBBLE_OUT if outgoing else BUBBLE_IN
        d.rounded_rectangle([bx, cy, bx + bw, cy + bh], radius=12, fill=col)
        ty = cy + pad
        for ln in lines:
            d.text((bx + pad, ty), ln, font=fbody, fill=TEXT)
            ty += lh
        d.text((bx + bw - 58, cy + bh - 20), "08:2" + str(n), font=ftime,
               fill=(170, 195, 188) if outgoing else MUTED)
        cy += bh + 12


def draw_popup(img, x, y):
    d = ImageDraw.Draw(img)
    w, h = 290, 200
    shadow_card(img, [x, y, x + w, y + h], 14, PANEL, blur=20, alpha=150)
    icon = Image.open(os.path.join(ROOT, "icons", "icon-48.png")).convert("RGBA")
    img.alpha_composite(icon, (x + 18, y + 18))
    fb = font(ARB, 18)
    fs = font(AR, 14)
    d.text((x + 74, y + 22), "Full chat", font=fb, fill=GREEN)
    d.text((x + 74, y + 44), "screenshot", font=fb, fill=GREEN)
    d.text((x + 18, y + 78), "Capture the whole conversation", font=fs, fill=MUTED)
    d.text((x + 18, y + 96), "from the first message.", font=fs, fill=MUTED)
    # button
    d.rounded_rectangle([x + 18, y + 128, x + w - 18, y + 168], radius=9, fill=GREEN)
    bt = font(ARB, 16)
    label = "Capture full conversation"
    tw = text_w(d, label, bt)
    d.text((x + w / 2 - tw / 2, y + 140), label, font=bt, fill=(8, 20, 12))


def base_canvas(w=1280, h=800):
    img = vgrad(w, h, BG0, BG1).convert("RGBA")
    return img


def badge(d, x, y, text, f):
    tw = text_w(d, text, f)
    d.rounded_rectangle([x, y, x + tw + 36, y + 44], radius=22, fill=PANEL2)
    d.ellipse([x + 12, y + 14, x + 28, y + 30], outline=GREEN, width=3)
    d.line([x + 16, y + 22, x + 20, y + 27], fill=GREEN, width=3)
    d.line([x + 20, y + 27, x + 26, y + 17], fill=GREEN, width=3)
    d.text((x + 36, y + 11), text, font=f, fill=TEXT)
    return tw + 36


# ============================ SCREENSHOT 1: HERO ============================
def ss1():
    img = base_canvas()
    headline(img, "Your whole WhatsApp chat,", "one click → one image")
    # chat panel (right)
    chat_panel(img, (640, 210, 1200, 760))
    ImageDraw.Draw(img).rounded_rectangle([640, 210, 1200, 760], radius=18, outline=PANEL2, width=2)
    # popup (left, overlapping)
    draw_popup(img, 110, 300)
    d = ImageDraw.Draw(img)
    fs = font(AR, 22)
    for i, t in enumerate(["From the first message to the last",
                           "No manual scrolling",
                           "Saved straight to your Downloads"]):
        y = 560 + i * 50
        d.ellipse([110, y + 4, 130, y + 24], fill=GREEN)
        d.line([114, y + 14, 119, y + 20], fill=(8, 20, 12), width=3)
        d.line([119, y + 20, 126, y + 9], fill=(8, 20, 12), width=3)
        d.text((146, y), t, font=fs, fill=TEXT)
    img.convert("RGB").save(os.path.join(OUT, "screenshot-1-hero.png"))


# ====================== SCREENSHOT 2: STITCHED RESULT ======================
def ss2():
    img = base_canvas()
    headline(img, "The entire conversation,", "stitched into a single PNG")
    d = ImageDraw.Draw(img)
    # tall "image" preview, centered
    px0, py0, pw = 470, 220, 340
    ph = 540
    shadow_card(img, [px0, py0, px0 + pw, py0 + ph], 14, (10, 18, 22), blur=24, alpha=160)
    # fill with mini chat
    sub = Image.new("RGBA", (pw - 16, ph - 16))
    chat_panel(sub, (0, 0, pw - 16, ph - 16))
    img.alpha_composite(sub, (px0 + 8, py0 + 8))
    d.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=14, outline=PANEL2, width=2)
    # download chip
    d.rounded_rectangle([px0 + pw - 210, py0 + ph - 50, px0 + pw - 14, py0 + ph - 12],
                        radius=10, fill=(0, 0, 0, 180) if False else PANEL)
    fchip = font(AR, 15)
    d.text((px0 + pw - 196, py0 + ph - 42), "whatsapp-Anna.png  ↓", font=fchip, fill=TEXT)

    # right column: callouts
    fb = font(ARB, 28)
    fs = font(AR, 21)
    cx = 880
    items = [
        ("Pixel-perfect", "Bubbles, wallpaper and timestamps,\nexactly as WhatsApp draws them."),
        ("Seamless", "Each scroll step adds only the new\nstrip — no overlaps, no gaps."),
        ("Auto-split", "Very long chats are saved as\nnumbered parts automatically."),
    ]
    y = 250
    for title, body in items:
        d.rounded_rectangle([cx - 30, y - 6, cx - 14, y + 70], radius=8, fill=GREEN)
        d.text((cx, y), title, font=fb, fill=WHITE)
        d.multiline_text((cx, y + 38), body, font=fs, fill=MUTED, spacing=6)
        y += 150
    img.convert("RGB").save(os.path.join(OUT, "screenshot-2-result.png"))


# ========================= SCREENSHOT 3: PRIVACY ===========================
def ss3():
    img = base_canvas()
    headline(img, "100% local.", "Nothing ever leaves your browser")
    d = ImageDraw.Draw(img)
    # big lock
    lx, ly = 250, 420
    d.rounded_rectangle([lx - 80, ly - 30, lx + 80, ly + 110], radius=20, fill=GREEN_D)
    d.arc([lx - 55, ly - 120, lx + 55, ly - 10], 180, 360, fill=GREEN, width=18)
    d.ellipse([lx - 16, ly + 10, lx + 16, ly + 42], fill=(8, 20, 12))
    d.rectangle([lx - 6, ly + 32, lx + 6, ly + 70], fill=(8, 20, 12))
    # checklist
    f = font(ARB, 26)
    items = ["No servers", "No analytics or tracking", "No network requests",
             "No accounts", "Open source (MIT)"]
    x, y = 620, 250
    for t in items:
        badge(d, x, y, t, f)
        y += 70
    img.convert("RGB").save(os.path.join(OUT, "screenshot-3-privacy.png"))


# ======================= SCREENSHOT 4: HOW IT WORKS ========================
def ss4():
    img = base_canvas()
    headline(img, "How it works", "three steps, fully automatic")
    d = ImageDraw.Draw(img)
    steps = [
        ("1", "Scroll to the top", "Loads every older message\nuntil the chat starts."),
        ("2", "Capture & stitch", "Walks down, appending each\nnew strip seamlessly."),
        ("3", "Save as PNG", "Drops the image(s) into\nyour Downloads folder."),
    ]
    cw, gap = 340, 40
    total = cw * 3 + gap * 2
    x = (1280 - total) // 2
    y = 280
    fb = font(ARB, 30)
    fs = font(AR, 20)
    fn = font(ARB, 46)
    for i, (n, title, body) in enumerate(steps):
        cx = x + i * (cw + gap)
        shadow_card(img, [cx, y, cx + cw, y + 320], 16, PANEL, blur=18, alpha=120)
        d.ellipse([cx + cw / 2 - 38, y + 36, cx + cw / 2 + 38, y + 112], fill=GREEN)
        nw = text_w(d, n, fn)
        d.text((cx + cw / 2 - nw / 2, y + 50), n, font=fn, fill=(8, 20, 12))
        tw = text_w(d, title, fb)
        d.text((cx + cw / 2 - tw / 2, y + 140), title, font=fb, fill=WHITE)
        d.multiline_text((cx + 40, y + 200), body, font=fs, fill=MUTED, spacing=8, align="center")
        if i < 2:
            ax = cx + cw + gap / 2
            d.text((ax - 10, y + 150), "→", font=fn, fill=GREEN)
    img.convert("RGB").save(os.path.join(OUT, "screenshot-4-how.png"))


# ============================ MARQUEE 1400x560 =============================
def marquee():
    img = vgrad(1400, 560, GREEN, GREEN_D).convert("RGBA")
    d = ImageDraw.Draw(img)
    icon = Image.open(os.path.join(ROOT, "icons", "icon-128.png")).convert("RGBA")
    big = icon.resize((220, 220), Image.LANCZOS)
    img.alpha_composite(big, (120, 170))
    ft = font(ARB, 60)
    fs = font(AR, 30)
    d.text((400, 195), "Full Chat Screenshot", font=ft, fill=WHITE)
    d.text((400, 270), "for WhatsApp Web", font=ft, fill=(8, 30, 18))
    d.text((402, 365), "Save an entire conversation as one image — in a click.",
           font=fs, fill=(8, 40, 26))
    img.convert("RGB").save(os.path.join(OUT, "marquee-1400x560.png"))


# ============================ SMALL PROMO 440x280 ==========================
def promo():
    img = vgrad(440, 280, GREEN, GREEN_D).convert("RGBA")
    d = ImageDraw.Draw(img)
    icon = Image.open(os.path.join(ROOT, "icons", "icon-128.png")).convert("RGBA")
    img.alpha_composite(icon.resize((110, 110), Image.LANCZOS), (28, 40))
    ft = font(ARB, 28)
    fs = font(AR, 16)
    d.text((150, 52), "Full Chat", font=ft, fill=WHITE)
    d.text((150, 86), "Screenshot", font=ft, fill=(8, 30, 18))
    d.multiline_text((150, 140), "for WhatsApp Web —\nwhole chat as one image.",
                     font=fs, fill=(8, 40, 26), spacing=6)
    img.convert("RGB").save(os.path.join(OUT, "promo-440x280.png"))


ss1(); ss2(); ss3(); ss4(); marquee(); promo()
for f in sorted(os.listdir(OUT)):
    print("wrote store/" + f)
