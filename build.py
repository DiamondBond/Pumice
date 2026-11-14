#!/usr/bin/env python3
# Pumice: a quiet white-and-grey xfwm4 theme with matching xfce4-panel styling.
# Copyright (C) 2026 DiamondBond. Licensed under the GNU GPL v3 or later; see LICENSE.
"""Renders every Pumice theme: Pumice, Pumice-dark and their -grey flavours.

For each: the xfwm4 images and themerc, the panel's window-button images (unity/,
for xfce4-windowck-plugin), the menu icon, panel.css (panel-base.css plus that
variant's colours), xfce-notify-4.0/gtk.css (notify-base.css likewise) and rofi.rasi
(rofi-base.rasi likewise); and, for the README, screenshots/frames.png. Needs
pycairo. The output is committed, so installing doesn't need this; run it after
changing anything here, in panel-base.css, notify-base.css or rofi-base.rasi."""
import math, os, cairo

HERE = os.path.dirname(os.path.abspath(__file__))
H = 28          # title bar height
R = 10          # top corner radius
CW = 11         # corner piece width
BOFF = CW       # button offset: buttons stay clear of the rounded corner piece
BW, BH = 22, H  # button cell: even, so a dot centred in it lands on whole pixels
DOT = 7.5       # button dot radius

# Everything that differs between the light and dark variant. Shapes, sizes and
# hues are shared, so an edit anywhere else lands in both.
VARIANTS = {
    "Pumice": dict(
        frame={"active":   dict(bg="#ffffff", border="#2e2e2e", sep="#e2e2e2"),
               "inactive": dict(bg="#f7f7f7", border="#5c5c5c", sep="#ebebeb")},
        edge="#707070",                                  # corner edge pixels blend toward this: mid grey suits white and black behind
        idle=("#ececec", "#d0d0d0"),                     # unfocused dot: fill, rim
        grey=("#d8d8d8", "#5a5a5a"),                     # grey flavour: focused dot, hover marks
        text=("#1f1f1f", "#9a9a9a"),                     # title: focused, unfocused
        panel=dict(bg="#fbfbfb", line="#d6d6d6", text="#3a3a3a", dim="#555555",
                   strong="#111111", hover="#ededed", on="#e2e2e2", dot="#d4d4d4"),
    ),
    "Pumice-dark": dict(
        frame={"active":   dict(bg="#2c2c2c", border="#0a0a0a", sep="#1e1e1e"),
               "inactive": dict(bg="#242424", border="#151515", sep="#1c1c1c")},
        edge="#3a3a3a",
        idle=("#2e2e2e", "#1c1c1c"),                     # an empty socket, so focus shows without colour
        grey=("#4f4f4f", "#d4d4d4"),
        well="#1e1e1e",                                  # dot rim: cut darker than the frame, where a shade of the dot would vanish
        text=("#ececec", "#7c7c7c"),
        panel=dict(bg="#1e1e1e", line="#0a0a0a", text="#e2e2e2", dim="#b4b4b4",
                   strong="#ffffff", hover="#2e2e2e", on="#3a3a3a", dot="#4a4a4a"),
    ),
}
# "-grey" flavour of each variant: focused dots are just a shade off the unfocused
# ones instead of red/yellow/green; marks show on hover. Hover and press step away
# from the frame colour. Everything else is shared.
for _name in list(VARIANTS):
    VARIANTS[_name + "-grey"] = dict(VARIANTS[_name], flat_grey=True)

# focused windows get colour dots, unfocused ones plain grey dots; the hues are
# muted to sit with the greys
HUE = {"close": "#da756c", "hide": "#dab462", "maximize": "#71bb68", "maximize-toggled": "#71bb68"}
GREY = "#c4c4c4"
# per button state: how much to darken the dot (None = unfocused grey)
BTN = {"active": 0.0, "prelight": 0.07, "pressed": 0.2, "inactive": None}


def shade(h, f):
    return "#" + "".join(f"{round(int(h[i:i + 2], 16) * (1 - f)):02x}" for i in (1, 3, 5))


def tint(h, f):
    return "#" + "".join(f"{round(int(h[i:i + 2], 16) + (255 - int(h[i:i + 2], 16)) * f):02x}" for i in (1, 3, 5))


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def surface(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def save(s, name):
    s.write_to_png(os.path.join(OUT, name + ".png"))
    WROTE.add(name)


def title_bg(state, W):
    """Title bar background W px wide with both top corners rounded."""
    c = FRAME[state]
    s, cr = surface(W, H)
    # Rounded-top rect, extended below the canvas so only the top corners round.
    # Without compositing xfwm4 shapes on a hard alpha cutoff, so the outer edge can't
    # be translucent. Instead partly-covered edge pixels are made opaque and blended
    # from the border colour toward a neutral grey, which softens the stair-steps on
    # light and dark backgrounds alike.
    def rtop(cr, inset, r):
        x0, y0, x1, y1 = inset, inset, W - inset, H + 20
        cr.new_path()
        cr.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
        cr.arc(x1 - r, y0 + r, r, 1.5 * math.pi, 2 * math.pi)
        cr.line_to(x1, y1); cr.line_to(x0, y1); cr.close_path()
    rtop(cr, 0, R); cr.set_source_rgb(*rgb(c["border"])); cr.fill()
    s.flush()
    px, edge, mid = s.get_data(), rgb(c["border"]), rgb(EDGE)
    for i in range(0, len(px), 4):           # BGRA, premultiplied
        a = px[i + 3] / 255
        if a < 0.3:
            px[i:i + 4] = bytes(4)
        elif a < 1:
            r_, g_, b_ = (e * a + m * (1 - a) for e, m in zip(edge, mid))
            px[i:i + 4] = bytes((round(b_ * 255), round(g_ * 255), round(r_ * 255), 255))
    s.mark_dirty()
    rtop(cr, 1, R - 1); cr.set_source_rgb(*rgb(c["bg"])); cr.fill()
    cr.set_source_rgb(*rgb(c["sep"])); cr.rectangle(0, H - 1, W - 1, 1); cr.fill()
    return s, cr


def frame(state):
    c = FRAME[state]
    W = CW * 2 + 1
    s, cr = title_bg(state, W)

    def crop(x, w, name):
        t, tc = surface(w, H)
        tc.set_source_surface(s, -x, 0); tc.paint()
        save(t, f"{name}-{state}")

    crop(0, CW, "top-left")
    crop(W - CW, CW, "top-right")
    for i in range(1, 6):
        crop(CW, 1, f"title-{i}")
    for name, w, h in (("left", 1, 1), ("right", 1, 1), ("bottom", 1, 1),
                       ("bottom-left", 1, 1), ("bottom-right", 1, 1)):
        t, tc = surface(w, h)
        tc.set_source_rgb(*rgb(c["border"])); tc.paint()
        save(t, f"{name}-{state}")


# hover glyphs, Mac-style: dark marks inside the colour dot, all in one stroke weight
def line(cr, *pts, w=1.3):
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.set_line_width(w); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()

def g_close(cr, x, y):
    d = 2.7; line(cr, (x - d, y - d), (x + d, y + d)); line(cr, (x + d, y - d), (x - d, y + d))

def g_hide(cr, x, y):
    line(cr, (x - 3.3, y), (x + 3.3, y), w=1.4)

def g_max(cr, x, y):       # one diagonal stroke, out toward two corners; a little heavier, as it stands alone
    d = 2.7; line(cr, (x - d, y - d), (x + d, y + d), w=1.6)

def g_restore(cr, x, y):   # the same stroke, mirrored
    d = 2.7; line(cr, (x + d, y - d), (x - d, y + d), w=1.6)

GLYPHS = {"close": g_close, "hide": g_hide, "maximize": g_max, "maximize-toggled": g_restore}
NAMES = ["hide", "maximize", "maximize-toggled", "close", "menu",
         "shade", "shade-toggled", "stick", "stick-toggled"]


def dot(cr, name, bstate, cx, cy):
    b = BTN[bstate]
    if b is None:
        fill, sunk = IDLE
    elif FLAT_GREY:   # dark frames brighten on hover, light darken
        fill = (tint if DARK else shade)(GREY_DOT, b)
        sunk = WELL or shade(fill, 0.14)
    else:
        fill = shade(HUE.get(name, GREY), b)
        sunk = WELL or shade(fill, 0.22)
    # flat dot set into the frame: the darker disc shows as a rim, widest at the
    # top, as if lit from above. A well goes round the dot rather than into it, so
    # it is drawn a pixel larger and the face stays the size of a light dot's
    r = DOT + (1 if WELL else 0)
    cr.arc(cx, cy, r - 0.5, 0, 2 * math.pi)
    cr.set_source_rgb(*rgb(sunk)); cr.fill()
    cr.arc(cx, cy + 0.6, r - 1.7, 0, 2 * math.pi)
    cr.set_source_rgb(*rgb(fill)); cr.fill()
    if name in GLYPHS and bstate in ("prelight", "pressed"):
        cr.set_source_rgba(*rgb(GREY_MARK if FLAT_GREY else shade(HUE[name], 0.62)), 0.9)
        GLYPHS[name](cr, cx, cy + 1)   # centred on the face, which sits low in the dot


def buttons(frame_state):
    # buttons sit on the title bar, so paint the title tile underneath
    bg = FRAME[frame_state]
    for bstate in BTN:
        if (frame_state == "inactive") != (bstate == "inactive"):
            continue
        for name in NAMES:
            s, cr = surface(BW, BH)
            cr.set_source_rgb(*rgb(bg["bg"])); cr.paint()
            cr.set_source_rgb(*rgb(bg["border"])); cr.rectangle(0, 0, BW, 1); cr.fill()
            cr.set_source_rgb(*rgb(bg["sep"])); cr.rectangle(0, BH - 1, BW, 1); cr.fill()
            dot(cr, name, bstate, BW / 2, BH / 2)
            save(s, f"{name}-{bstate}")


def panel_buttons():
    # the same dots for the panel's Window Header plugin (wckbuttons), which shows
    # them only while a window is maximized; transparent so the panel shows through
    out = os.path.join(os.path.dirname(OUT), "unity")
    os.makedirs(out, exist_ok=True)
    states = {"focused_normal": "active", "focused_prelight": "prelight",
              "focused_pressed": "pressed", "unfocused": "inactive"}
    names = {"close": "close", "minimize": "hide", "maximize": "maximize",
             "unmaximize": "maximize-toggled", "menu": "menu"}
    for wname, name in names.items():
        for wstate, bstate in states.items():
            s, cr = surface(BW, 22)
            dot(cr, name, bstate, BW / 2, 11)
            s.write_to_png(os.path.join(out, f"{wname}_{wstate}.png"))


def preview(theme):
    """README cell: this theme's title bar focused, hovered and unfocused, on the
    grey its corners are blended toward."""
    W, GAP = 330, 12
    rows = (("active", "active", ""), ("active", "prelight", " · hover"), ("inactive", "inactive", " · unfocused"))
    s, cr = surface(W + 2 * GAP, len(rows) * (H + GAP) + GAP)
    cr.set_source_rgb(*rgb(EDGE)); cr.paint()
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); cr.set_font_size(13)
    for i, (fstate, bstate, label) in enumerate(rows):
        bar, bcr = title_bg(fstate, W)
        for j, name in enumerate(("close", "maximize", "hide")):   # where xfwm4 puts them for |HMC
            dot(bcr, name, bstate, W - 1 - BOFF - BW * (j + .5), BH / 2)
        y = GAP + i * (H + GAP)
        cr.set_source_surface(bar, GAP, y); cr.paint()
        cr.set_source_rgb(*rgb(TEXT[fstate == "inactive"]))
        cr.move_to(GAP + CW + 4, y + 19); cr.show_text(theme + label)
    return s


MENU_ICON = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 16 16" width="16" height="16">
  <!-- Pumice menu button: a ball with a wave flowing through it; faint above,
       a half-tone band, then solid below, fading toward the top right -->
  <defs>
    <clipPath id="ball"><circle cx="8" cy="8" r="7"/></clipPath>
    <linearGradient id="flow" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="{0}"/>
      <stop offset="1" stop-color="{0}" stop-opacity=".45"/>
    </linearGradient>
    <path id="wave" d="M0 10 C3 6 5.5 6 8 8.5 S13 11 16 7 V19 H0 Z"/>
  </defs>
  <g clip-path="url(#ball)" fill="url(#flow)">
    <rect width="16" height="16" fill-opacity=".2"/>
    <use xlink:href="#wave" transform="translate(0 -2.6)" fill-opacity=".45"/>
    <use xlink:href="#wave"/>
  </g>
</svg>
"""

CELLS = []
for theme, v in VARIANTS.items():
    OUT, WROTE = os.path.join(HERE, theme, "xfwm4"), set()
    FRAME, EDGE, IDLE, TEXT = v["frame"], v["edge"], v["idle"], v["text"]
    FLAT_GREY, (GREY_DOT, GREY_MARK) = v.get("flat_grey", False), v["grey"]
    DARK = "dark" in theme
    WELL = v.get("well")
    root = os.path.join(HERE, theme)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(root, "menu.svg"), "w") as f:
        f.write(MENU_ICON.format(v["panel"]["strong"]))
    with open(os.path.join(root, "panel.css"), "w") as f:
        f.write(f"/* {theme} panel colours; rules live in panel-base.css (generated, edit build.py) */\n")
        f.write("".join(f"@define-color pm_{k} {c};\n" for k, c in v["panel"].items()))
        f.write(open(os.path.join(HERE, "panel-base.css")).read())
    os.makedirs(os.path.join(root, "xfce-notify-4.0"), exist_ok=True)
    with open(os.path.join(root, "xfce-notify-4.0", "gtk.css"), "w") as f:
        f.write(f"/* {theme} notification colours; rules live in notify-base.css (generated, edit build.py) */\n")
        f.write("".join(f"@define-color pm_{k} {c};\n" for k, c in {**v["panel"], "border": FRAME["active"]["border"]}.items()))
        f.write(open(os.path.join(HERE, "notify-base.css")).read())
    with open(os.path.join(root, "rofi.rasi"), "w") as f:
        f.write(f"/* {theme} rofi colours; rules live in rofi-base.rasi (generated, edit build.py) */\n* {{\n")
        f.write("".join(f"  pm-{k}: {c};\n" for k, c in {**v["panel"], "bg": FRAME["active"]["bg"],
                                                          "line": FRAME["active"]["sep"], "border": FRAME["active"]["border"]}.items()))
        f.write("}\n" + open(os.path.join(HERE, "rofi-base.rasi")).read())
    with open(os.path.join(root, "index.theme"), "w") as f:
        f.write(f"[Desktop Entry]\nType=X-GNOME-Metatheme\nName={theme}\n\n[X-GNOME-Metatheme]\n"
                f"GtkTheme={'Adwaita-dark' if 'dark' in theme else 'Adwaita'}\nMetacityTheme={theme}\n")
    for st in FRAME:
        frame(st)
        buttons(st)
    panel_buttons()
    CELLS.append(preview(theme))

    with open(os.path.join(OUT, "themerc"), "w") as f:
        f.write(f"""\
active_text_color={TEXT[0]}
inactive_text_color={TEXT[1]}
full_width_title=true
title_shadow_active=false
title_shadow_inactive=false
title_vertical_offset_active=0
title_vertical_offset_inactive=0
button_offset={BOFF}
button_spacing=0
title_horizontal_offset=0
show_app_icon=false
""")

    # sanity: this run wrote every image xfwm4 looks up (files left by earlier runs don't count)
    need = [f"{p}-{s}" for p in ("top-left", "top-right", "left", "right", "bottom", "bottom-left", "bottom-right",
                                 *[f"title-{i}" for i in range(1, 6)]) for s in FRAME]
    need += [f"{g}-{s}" for g in NAMES for s in BTN]
    missing = [n for n in need if n not in WROTE]
    assert not missing, missing
    print("ok:", OUT)

# README strip: colour flavours left, grey right; light above, dark below
cw, ch = CELLS[0].get_width(), CELLS[0].get_height()
s, cr = surface(2 * cw, 2 * ch)
for i, cell in enumerate(CELLS):
    cr.set_source_surface(cell, i // 2 * cw, i % 2 * ch); cr.paint()
s.write_to_png(os.path.join(HERE, "screenshots", "frames.png"))
