"""Draws the painted bits of the look with Pillow - flat matte button faces, thin rules, the paper
background and its grain, toolbar icons - and remembers each picture so it's only drawn once. If Pillow
isn't installed, every function here quietly gives back None and the screens fall back to flat colors."""

import math
import random
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageTk
    OK = True
except Exception:
    OK = False

from app.ui import theme

BACKGROUNDS_DIR = Path(__file__).resolve().parents[2] / "assets" / "backgrounds"
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

_cache = {}
_sparkles_on = True
_grain_on = True
GRAIN_STRENGTH = 0.085   # how strongly the paper grain shows; small on purpose
_GRAIN_TILE = 192        # the noise is drawn once at this size and tiled


def ready():
    """Says whether Pillow is there, so the fancy pictures can be drawn."""
    return OK


def set_sparkles(on):
    """Turns the star-field and sparkle decorations on or off (the glass and gradients stay)."""
    global _sparkles_on
    if _sparkles_on != bool(on):
        _sparkles_on = bool(on)
        _cache.clear()


def sparkles_on():
    """Says whether the sparkle decorations are switched on."""
    return _sparkles_on


def set_grain(on):
    """Turns the paper grain over the background on or off."""
    global _grain_on
    if _grain_on != bool(on):
        _grain_on = bool(on)
        _bg_cache.clear()


def grain_on():
    """Says whether the paper grain is switched on."""
    return _grain_on


def clear_cache():
    """Forgets every drawn picture (call after the mode or accent changes, to free memory)."""
    _cache.clear()


def _remember(key, make):
    """Gives back the cached picture for this key, drawing it first if it isn't there yet."""
    if key not in _cache:
        _cache[key] = make()
    return _cache[key]


def _rgb(hex_color):
    """Turns '#rrggbb' into three numbers."""
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _mix(a, b, t):
    """Mixes two (r, g, b) tuples; t = 0 gives a, t = 1 gives b."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _hgrad(w, h, colors):
    """A left-to-right gradient through the given '#hex' colors, evenly spaced."""
    strip = Image.new("RGB", (w, 1))
    rgbs = [_rgb(c) for c in colors]
    pix = []
    for x in range(w):
        t = x / max(1, w - 1) * (len(rgbs) - 1)
        i = min(len(rgbs) - 2, int(t))
        pix.append(tuple(int(round(v)) for v in _mix(rgbs[i], rgbs[i + 1], t - i)))
    strip.putdata(pix)
    return strip.resize((w, h), Image.NEAREST)


_sparkle_cache = {}


def _sparkle(radius, color, alpha, fat=0.16):
    """A little four-point star as an RGBA picture, remembered so the same star is only drawn once."""
    key = (round(radius, 2), color, round(alpha, 2), fat)
    sprite = _sparkle_cache.get(key)
    if sprite is None:
        sprite = _sparkle_draw(key[0], color, key[2], fat)
        _sparkle_cache[key] = sprite
    return sprite


def _sparkle_draw(radius, color, alpha, fat):
    """Draws a four-point star big and shrinks it so the edges are smooth."""
    size = max(3, int(math.ceil(radius * 2)) + 2)
    big = 8
    mask = Image.new("L", (size * big, size * big), 0)
    cx = cy = size * big / 2
    r = radius * big
    k = r * fat
    pts = []
    corners = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    ctrls = [(cx + k, cy - k), (cx + k, cy + k), (cx - k, cy + k), (cx - k, cy - k)]
    for i in range(4):
        p0, p1, c = corners[i], corners[(i + 1) % 4], ctrls[i]
        for s in range(10):
            u = s / 10
            pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0],
                        (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]))
    ImageDraw.Draw(mask).polygon(pts, fill=int(255 * alpha))
    mask = mask.resize((size, size), Image.LANCZOS)
    sprite = Image.new("RGBA", (size, size), _rgb(color) + (0,))
    sprite.putalpha(mask)
    return sprite


def _stamp(canvas, sprite, x, y):
    """Lays a small RGBA sprite onto an RGBA canvas, centred on (x, y), even if it hangs off an edge."""
    left = int(round(x - sprite.width / 2))
    top = int(round(y - sprite.height / 2))
    sx, sy = max(0, -left), max(0, -top)
    if sx >= sprite.width or sy >= sprite.height:
        return
    canvas.alpha_composite(sprite, (max(0, left), max(0, top)), (sx, sy, sprite.width, sprite.height))


# ---------- buttons ----------

_BUTTON_COLORS_BY_MODE = {
    # kind -> (top, bottom, edge, ink). Top and bottom are the same now: the faces are flat.
    "dark": {
        "danger": ("#C56BFF", "#C56BFF", "#8F42C0", "#15061C"),
        "ok": ("#5E9CFF", "#5E9CFF", "#3A6FC4", "#060E1C"),
    },
    "light": {
        "danger": ("#DD9A8C", "#DD9A8C", "#B06D5E", "#2B1510"),
        "ok": ("#A2CAC4", "#A2CAC4", "#729B95", "#17251F"),
    },
}


def _button_colors(kind):
    """The (top, bottom, edge, ink) colors for a danger or ok button in the mode that's on, or None."""
    return _BUTTON_COLORS_BY_MODE[theme.MODE if theme.MODE in _BUTTON_COLORS_BY_MODE else "dark"].get(kind)


def button_fill(kind):
    """The flat color a button of this kind is painted in, in the mode that's on."""
    if kind == "primary":
        return theme.ACCENT
    colors = _button_colors(kind)
    return colors[0] if colors is not None else theme.BTN_TOP


def button_ink(kind):
    """The text color that reads well on a button of this kind."""
    if kind == "primary":
        return theme.ACCENT_INK
    colors = _button_colors(kind)
    if colors is not None:
        return colors[3]
    return theme.BTN_INK


def _button_picture(w, h, kind, state, icon):
    """Draws one button face: one flat matte color and a 1 pixel edge. No gradient, no shine."""
    if kind == "primary":
        fill, edge = theme.ACCENT, theme.ACCENT_EDGE
    else:
        colors = _button_colors(kind)
        if colors is not None:
            fill, _bottom, edge, _ink = colors
        else:
            fill, edge = theme.BTN_TOP, theme.BTN_EDGE
    img = Image.new("RGB", (w, h), _rgb(fill))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=_rgb(edge))
    if icon:
        _draw_icon(img, icon, theme.ACCENT_TEXT)
    if state == "hover":
        # A matte lift: a touch lighter in the dark, a touch deeper on paper.
        tint = "#FFFFFF" if theme.MODE == "dark" else "#2B2620"
        img = Image.blend(img, Image.new("RGB", (w, h), _rgb(tint)), 0.09)
    elif state == "disabled":
        img = Image.blend(img, Image.new("RGB", (w, h), _rgb(theme.PANEL)), 0.55)
    return img


def button(w, h, kind="secondary", state="normal", icon=None):
    """A Tk picture for a button face of this size, kind (primary/secondary/danger/ok/toolbar) and state."""
    if not OK:
        return None
    key = ("button", w, h, kind, state, icon, theme.MODE, theme.ACCENT, _sparkles_on)
    return _remember(key, lambda: ImageTk.PhotoImage(_button_picture(w, h, kind, state, icon)))


# ---------- stripes, bars, lines ----------

def aurora_bar(w, h=2):
    """The thin flat rule that sits along the top of panels."""
    if not OK or w < 2:
        return None
    key = ("aurora", w, h, theme.MODE)
    return _remember(key, lambda: ImageTk.PhotoImage(Image.new("RGB", (w, h), _rgb(theme.AURORA[0]))))


def fade_line(w, bg, alpha=0.7, fade=True, h=1):
    """A thin rule, blended toward the given background color so it looks see-through.
    With fade=True it melts away toward the right end."""
    if not OK or w < 2:
        return None
    key = ("line", w, h, bg, alpha, fade, theme.MODE)

    def make():
        """Draws the line."""
        line = Image.new("RGB", (w, h), _rgb(theme.AURORA[0]))
        base = Image.new("RGB", (w, h), _rgb(bg))
        mask = Image.new("L", (w, h), int(255 * alpha))
        if fade:
            ramp = Image.new("L", (w, 1))
            ramp.putdata([int(255 * alpha * (1 - max(0, (x / max(1, w - 1) - 0.66)) / 0.34)) for x in range(w)])
            mask = ramp.resize((w, h), Image.NEAREST)
        base.paste(line, (0, 0), mask)
        return ImageTk.PhotoImage(base)
    return _remember(key, make)


def gradient_bar(w, h, left, right, dust=True):
    """A flat color bar (team headers, pop-up headers). Both colors are the same now, so `right` is
    only used when something still asks for two; star dust shows only if sparkles are switched on."""
    if not OK or w < 2:
        return None
    key = ("bar", w, h, left, right, dust and _sparkles_on)

    def make():
        """Draws the bar and, if sparkles are on, the dust."""
        img = Image.new("RGB", (w, h), _rgb(left)) if left == right else _hgrad(w, h, [left, right])
        if dust and _sparkles_on:
            rgba = img.convert("RGBA")
            tile = 96
            spots = [(14, 22, 2.8, .8), (66, 12, 2.0, .6), (40, 58, 3.2, .7), (84, 70, 2.2, .65), (10, 84, 1.8, .55)]
            scale = max(1.0, h / 40)
            for ox in range(0, w + tile, int(tile * scale)):
                for (x, y, r, a) in spots:
                    px, py = ox + x * scale, (y / tile) * h
                    if px < w:
                        _stamp(rgba, _sparkle(r * scale, "#FFFFFF", a), px, py)
            img = rgba.convert("RGB")
        return ImageTk.PhotoImage(img)
    return _remember(key, make)


def accent_bar(w, h):
    """A wide flat accent-colored strip (top of the Start panel)."""
    if not OK or w < 2:
        return None
    key = ("accentbar", w, h, theme.ACCENT)
    return _remember(key, lambda: ImageTk.PhotoImage(Image.new("RGB", (w, h), _rgb(theme.ACCENT))))


def vertical_swatch(w, h, stops):
    """A filled rectangle. The look is flat, so the middle stop's color fills the whole thing."""
    if not OK:
        return None
    key = ("vswatch", w, h, tuple(stops))

    def make():
        """Picks the stop nearest the middle and fills with it."""
        ordered = sorted(stops, key=lambda s: abs(s[0] - 0.5))
        return ImageTk.PhotoImage(Image.new("RGB", (max(1, w), max(1, h)), _rgb(ordered[0][1])))
    return _remember(key, make)


def channel_track(w, h, left, right):
    """The slider track for one color channel: a left-to-right gradient from one color to another."""
    if not OK or w < 2:
        return None
    key = ("track", w, h, left, right)
    return _remember(key, lambda: ImageTk.PhotoImage(_hgrad(w, h, [left, right])))


def swatch(size, c1, c2):
    """A small flat square (used before section titles)."""
    if not OK:
        return None
    key = ("swatch", size, c1, c2)
    return _remember(key, lambda: ImageTk.PhotoImage(Image.new("RGB", (size, size), _rgb(c1))))


# ---------- icons ----------

def _icon_mask(name, box):
    """Draws an icon as a white-on-black picture (box x box pixels) that can be used as a stencil."""
    big = 6
    mask = Image.new("L", (box * big, box * big), 0)
    d = ImageDraw.Draw(mask)
    u = box * big / 24.0
    lw = max(2, int(round(2.1 * u)))

    def line(pts):
        """Draws a rounded line through the points (given in 24-unit space)."""
        pix = [(x * u, y * u) for x, y in pts]
        d.line(pix, fill=255, width=lw, joint="curve")
        for (x, y) in (pix[0], pix[-1]):
            d.ellipse([x - lw / 2, y - lw / 2, x + lw / 2, y + lw / 2], fill=255)

    def ring(cx, cy, r, a0=0, a1=360):
        """Draws part of a circle outline."""
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
               for a in range(int(a0), int(a1) + 1, 6)]
        line(pts)

    if name == "moon":
        d.ellipse([4 * u, 4 * u, 20 * u, 20 * u], fill=255)
        d.ellipse([9 * u, 1.5 * u, 22.5 * u, 15 * u], fill=0)
    elif name == "sun":
        ring(12, 12, 4, 0, 360)
        for k in range(8):
            a = math.radians(k * 45)
            line([(12 + 7 * math.cos(a), 12 + 7 * math.sin(a)), (12 + 9.5 * math.cos(a), 12 + 9.5 * math.sin(a))])
    elif name in ("sound", "mute"):
        line([(4, 9), (4, 15), (8, 15), (13, 19), (13, 5), (8, 9), (4, 9)])
        if name == "sound":
            ring(13, 12, 4.5, -50, 50)
            ring(13, 12, 8.5, -50, 50)
        else:
            line([(16, 9), (21, 15)])
            line([(21, 9), (16, 15)])
    elif name == "minus":
        line([(6, 12), (18, 12)])
    elif name == "plus":
        line([(6, 12), (18, 12)])
        line([(12, 6), (12, 18)])
    elif name == "full":
        line([(4, 9), (4, 4), (9, 4)])
        line([(20, 9), (20, 4), (15, 4)])
        line([(4, 15), (4, 20), (9, 20)])
        line([(20, 15), (20, 20), (15, 20)])
    elif name == "exitfull":
        line([(9, 4), (9, 9), (4, 9)])
        line([(15, 4), (15, 9), (20, 9)])
        line([(9, 20), (9, 15), (4, 15)])
        line([(15, 20), (15, 15), (20, 15)])
    elif name == "search":
        ring(11, 11, 6, 0, 360)
        line([(15.5, 15.5), (20, 20)])
    elif name == "pencil":
        line([(4, 20), (5, 16), (16, 5), (19, 8), (8, 19), (4, 20)])
        line([(14, 7), (17, 10)])
    elif name == "lock":
        line([(5, 11), (19, 11), (19, 20), (5, 20), (5, 11)])
        line([(8, 11), (8, 8)])
        ring(12, 8, 4, 180, 360)
        line([(16, 8), (16, 11)])
    elif name == "arrow":
        line([(5, 12), (19, 12)])
        line([(13, 6), (19, 12), (13, 18)])
    elif name == "back":
        line([(19, 12), (5, 12)])
        line([(11, 6), (5, 12), (11, 18)])
    elif name == "down":
        line([(6, 9), (12, 15), (18, 9)])
    elif name == "up":
        line([(6, 15), (12, 9), (18, 15)])
    elif name == "x":
        line([(6, 6), (18, 18)])
        line([(18, 6), (6, 18)])
    elif name == "check":
        line([(5, 13), (10, 18), (19, 7)])
    elif name == "info":
        ring(12, 12, 9, 0, 360)
        line([(12, 11), (12, 17)])
        line([(12, 7.2), (12, 7.4)])
    elif name == "trophy":
        line([(7, 4), (17, 4), (17, 10), (12, 14), (7, 10), (7, 4)])
        line([(7, 6), (4, 6), (4, 9), (7, 11)])
        line([(17, 6), (20, 6), (20, 9), (17, 11)])
        line([(12, 14), (12, 18)])
        line([(8, 20), (16, 20)])
    return mask.resize((box, box), Image.LANCZOS)


def _draw_icon(img, name, color):
    """Draws a toolbar icon in the middle of an RGB image.
    The special name 'swatch' draws a little accent-colored square at the left instead."""
    w, h = img.size
    if name == "swatch":
        side = theme.S(12)
        left, top = theme.S(12), (h - side) // 2
        img.paste(Image.new("RGB", (side, side), _rgb(theme.ACCENT)), (left, top))
        return
    box = max(8, int(min(w, h) * 0.5))
    img.paste(Image.new("RGB", (box, box), _rgb(color)), ((w - box) // 2, (h - box) // 2), _icon_mask(name, box))


def icon_alpha(name, size, color):
    """A small see-through Tk picture of an icon, for drawing on top of other pictures."""
    if not OK:
        return None
    key = ("iconalpha", name, size, color)

    def make():
        """Draws the icon as a colored shape with a see-through background."""
        sprite = Image.new("RGBA", (size, size), _rgb(color) + (0,))
        sprite.putalpha(_icon_mask(name, size))
        return ImageTk.PhotoImage(sprite)
    return _remember(key, make)


def icon_image(name, size, color, bg):
    """A small Tk picture of an icon (size in real pixels) in the given color on a flat background color."""
    if not OK:
        return None
    key = ("icon", name, size, color, bg)

    def make():
        """Draws the icon onto its background."""
        img = Image.new("RGB", (size, size), _rgb(bg))
        img.paste(Image.new("RGB", (size, size), _rgb(color)), (0, 0), _icon_mask(name, size))
        return ImageTk.PhotoImage(img)
    return _remember(key, make)


# ---------- backgrounds ----------

def _custom_background(w, h, mode=None):
    """Looks for assets/backgrounds/dark.* or light.* and fits it to the window. Gives back None if there isn't one."""
    if not BACKGROUNDS_DIR.exists():
        return None
    mode = mode or theme.MODE
    for ext in _IMAGE_EXTS:
        path = BACKGROUNDS_DIR / f"{mode}{ext}"
        if path.exists():
            try:
                img = Image.open(path).convert("RGB")
            except Exception:
                return None
            scale = max(w / img.width, h / img.height)
            img = img.resize((max(w, int(img.width * scale)), max(h, int(img.height * scale))), Image.LANCZOS)
            left, top = (img.width - w) // 2, (img.height - h) // 2
            return img.crop((left, top, left + w, top + h))
    return None


_grain_cache = {}


def _grain_tile():
    """One square of soft grey noise, drawn once and reused for every paper background."""
    tile = _grain_cache.get("tile")
    if tile is None:
        tile = Image.effect_noise((_GRAIN_TILE, _GRAIN_TILE), 24).convert("L")
        _grain_cache["tile"] = tile
    return tile


def _add_grain(img, mode):
    """Lays the paper grain over a background: the noise square tiled across it and blended in lightly."""
    tile = _grain_tile()
    noise = Image.new("L", img.size)
    for y in range(0, img.height, _GRAIN_TILE):
        for x in range(0, img.width, _GRAIN_TILE):
            noise.paste(tile, (x, y))
    strength = GRAIN_STRENGTH * (0.75 if mode == "dark" else 1.0)
    return Image.blend(img, ImageChops.overlay(img, noise.convert("RGB")), strength)


def _background_picture(w, h, mode=None, accent=None):
    """Draws the whole-window background for a mode: one flat matte paper color with a very faint grain
    over it, or the user's own picture from assets/backgrounds/ when there is one. `accent` is only part
    of the cache key these days - the paper itself doesn't take the accent color any more."""
    mode = mode or theme.MODE
    img = _custom_background(w, h, mode)
    if img is None:
        img = Image.new("RGB", (w, h), _rgb(theme.color_for(mode, "BG")))
    if _grain_on:
        img = _add_grain(img, mode)
    if _sparkles_on:
        _paint_stars(img, mode == "dark")
    return img


def _paint_stars(img, dark):
    """Scatters the star-field (and the faint crescent halo in the corner) over a background."""
    w, h = img.size
    fx, fy = w / 1280.0, h / 720.0
    unit = (fx + fy) / 2
    rnd = random.Random(7 if dark else 11)
    pal = (["#FFFFFF", "#9BEBF7", "#FFB0D8", "#C9B6FF", "#F6DC8C"] if dark
           else ["#F59BC6", "#A98FF0", "#6FCFE6", "#FFB877", "#E8B84A"])
    lo, hi = (0.32, 0.8) if dark else (0.55, 0.95)
    dot = "#FFFFFF" if dark else "#B6A6EE"
    ho = 0.65 if dark else 0.8
    halo = ["#6FE0F2", "#FF8FC8", "#B79CFF"] if dark else ["#7FD8EA", "#F7A3CC", "#B8A6F6"]

    rgba = img.convert("RGBA")
    # crescent halo: a big soft disc with a bite taken out, plus two thin rings
    cx, cy = 1170 * fx, 64 * fy
    r1 = 150 * unit
    size = int(r1 * 2) + 4
    left, topy = int(cx - r1) - 2, int(cy - r1) - 2
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([2, 2, size - 3, size - 3], fill=int(255 * 0.16 * ho))
    bite_cx, bite_cy, bite_r = (1218 * fx) - left, (20 * fy) - topy, 132 * unit
    md.ellipse([bite_cx - bite_r, bite_cy - bite_r, bite_cx + bite_r, bite_cy + bite_r], fill=0)
    fill = _hgrad(size, size, halo)
    layer = fill.convert("RGBA")
    layer.putalpha(mask)
    _safe_composite(rgba, layer, left, topy)
    ring_layer = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_layer)
    for radius, op in ((196, 0.24), (238, 0.14)):
        rr = radius * unit
        rd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                   outline=_rgb(halo[1]) + (int(255 * op * ho),), width=1)
    rgba.alpha_composite(ring_layer)

    cols, rows = 9, 5
    cw, ch = 1280 / cols, 720 / rows
    for r in range(rows):
        for c in range(cols):
            if rnd.random() < 0.2:
                continue
            x = (c * cw + rnd.uniform(0.15, 0.85) * cw) * fx
            y = (r * ch + rnd.uniform(0.15, 0.85) * ch) * fy
            t = rnd.random()
            rad = rnd.uniform(2.0, 3.4) if t < 0.68 else (rnd.uniform(3.6, 5.2) if t < 0.94 else rnd.uniform(6.0, 8.5))
            col = rnd.choice(pal)
            op = round(rnd.uniform(lo, hi), 2)
            _stamp(rgba, _sparkle(max(1.5, rad * unit), col, op), x, y)
    px = rgba.load()
    dot_rgb = _rgb(dot)
    for _ in range(70):
        x, y = int(rnd.uniform(0, 1280) * fx), int(rnd.uniform(0, 720) * fy)
        op = rnd.uniform(0.25, 0.6)
        if 0 <= x < w and 0 <= y < h:
            base = px[x, y]
            px[x, y] = tuple(int(round(v)) for v in _mix(base[:3], dot_rgb, op)) + (255,)
    img.paste(rgba.convert("RGB"))


def _safe_composite(rgba, layer, left, top):
    """Lays a layer onto an image even when part of it hangs off the edge."""
    canvas = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    canvas.paste(layer, (left, top))
    rgba.alpha_composite(canvas)


def burst(size, color):
    """A big faint fan of thin rays that fades out toward the edge, as a see-through picture (behind the winner screen)."""
    if not OK:
        return None
    key = ("burst", size, color)

    def make():
        """Draws the rays, then fades them out from the middle."""
        from PIL import ImageChops, ImageOps
        mask = Image.new("L", (size, size), 0)
        d = ImageDraw.Draw(mask)
        c = size / 2
        reach = size * 1.5
        for k in range(24):
            a0, a1 = math.radians(k * 15 - 2.5), math.radians(k * 15 + 2.5)
            d.polygon([(c, c), (c + reach * math.cos(a0), c + reach * math.sin(a0)),
                       (c + reach * math.cos(a1), c + reach * math.sin(a1))], fill=255)
        ramp = Image.radial_gradient("L").resize((size, size), Image.BILINEAR)
        fade = ImageOps.invert(ramp.point(lambda v: min(255, int(v * 1.45))))
        alpha = ImageChops.multiply(mask, fade).point(lambda v: int(v * 0.09))
        layer = Image.new("RGBA", (size, size), _rgb(color) + (0,))
        layer.putalpha(alpha)
        return ImageTk.PhotoImage(layer)
    return _remember(key, make)


_bg_cache = {}        # key -> {"pil": big picture waiting for the screen, "photo": Tk picture, "thumb": small copy for sampling}
_BG_KEEP = 4
_last_thumb = None
_THUMB = 8            # the sampling copy is this many times smaller


def _bg_key(w, h, mode, accent):
    """Everything that makes one background different from another."""
    return ("bg", w, h, mode, accent, _sparkles_on, _grain_on, _custom_background_exists(mode))


def _bg_entry(w, h, mode, accent, with_photo=True):
    """Finds (or draws) the background for this size and mode and keeps it for next time."""
    key = _bg_key(w, h, mode, accent)
    entry = _bg_cache.get(key)
    if entry is None:
        pil = _background_picture(w, h, mode, accent)
        entry = {"pil": pil, "photo": None,
                 "thumb": pil.resize((max(1, w // _THUMB), max(1, h // _THUMB)), Image.BOX)}
        _bg_cache[key] = entry
        while len(_bg_cache) > _BG_KEEP:
            _bg_cache.pop(next(iter(_bg_cache)))
    if with_photo and entry["photo"] is None:
        entry["photo"] = ImageTk.PhotoImage(entry["pil"])
        entry["pil"] = None
    return entry


def background_ready(w, h):
    """Says whether the background for this size is already drawn (so showing it costs nothing)."""
    return OK and _bg_key(w, h, theme.MODE, theme.accent_for(theme.MODE)) in _bg_cache


def background(w, h):
    """The whole-window background picture for the current mode and accent."""
    global _last_thumb
    if not OK or w < 8 or h < 8:
        return None
    entry = _bg_entry(w, h, theme.MODE, theme.accent_for(theme.MODE))
    _last_thumb = (entry["thumb"], w, h)
    return entry["photo"]


def prewarm_background(w, h, mode):
    """Draws the background for a size and mode ahead of time (while the app is idle) without showing it."""
    if OK and w >= 8 and h >= 8:
        _bg_entry(w, h, mode, theme.accent_for(mode), with_photo=False)


def sample_background(x, y):
    """The background's color at a spot (the last background drawn), so thin lines can blend into it."""
    if _last_thumb is None:
        return theme.BG
    thumb, w, h = _last_thumb
    tx = max(0, min(thumb.width - 1, int(x * thumb.width / max(1, w))))
    ty = max(0, min(thumb.height - 1, int(y * thumb.height / max(1, h))))
    r, g, b = thumb.getpixel((tx, ty))[:3]
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def _custom_background_exists(mode=None):
    """Says which custom background file (if any) is in use for a mode, so changing it makes a fresh picture."""
    if not BACKGROUNDS_DIR.exists():
        return None
    mode = mode or theme.MODE
    for ext in _IMAGE_EXTS:
        path = BACKGROUNDS_DIR / f"{mode}{ext}"
        if path.exists():
            try:
                return (path.name, path.stat().st_mtime_ns)
            except OSError:
                return path.name
    return None
