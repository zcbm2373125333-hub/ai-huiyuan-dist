"""千古人物志 · 第贰拾壹集 · 孔子 (前551–前479)
Look: 赭石 + 杏花粉, 回纹 corner borders, falling apricot petals; a 竹简 chapter card that unrolls more slips each chapter.
Set pieces: 6-beat 杏坛讲学 (students fill the yard up to 三千), custom 8-beat scene 'travel' (周游列国 route map),
6-beat 陈蔡绝粮 (seven days, the qin keeps playing), 8-beat 删述六经 (six bundles one per beat).
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_yuqian as Yq          # engine + helpers (previous episode)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
import epkit
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wangyangming import desk, scroll, lamp, sitter, leaf

F.RIPPLE = False
OCHRE = (140, 92, 42)               # 赭石
APRICOT = (226, 146, 136)           # 杏花粉
S.LAYERS.append(('ochre', OCHRE, 0.85, 1.0))
S.LAYERS.append(('apricot', APRICOT, 0.85, 1.4))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='仁', life='丘', court='礼', night='夜', war='乱', empire='周', works='学', fate='行', death='逝', end='仁')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['empire']['sun'] = (APRICOT, 230, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (OCHRE, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

TREES = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(TREES)
_r = random.Random(4)
for _x, _y in ((90, 1320), (990, 1300)):
    _d.line((_x, 1500, _x + 10, _y), fill=OCHRE + (50,), width=12)
    for _k in range(5):
        _a = -math.pi / 2 + _r.uniform(-1.0, 1.0)
        _ex, _ey = _x + 10 + 120 * math.cos(_a), _y + 120 * math.sin(_a)
        _d.line((_x + 10, _y, _ex, _ey), fill=OCHRE + (50,), width=6)
        for _j in range(6):
            _px, _py = _ex + _r.uniform(-40, 40), _ey + _r.uniform(-40, 40)
            _d.ellipse((_px - 9, _py - 9, _px + 9, _py + 9), fill=APRICOT + (70,))
MTN_COL = {'night': (44, 40, 36), 'death': (64, 62, 58), 'war': (100, 64, 44), 'fate': (96, 76, 56)}
def draw_background(t, theme):
    """鲁地丘陵: soft ochre hills, flowering apricot trees at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 182, 160), (166, 140, 110), MTN_COL.get(theme, (124, 96, 66))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.9))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(TREES)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """回纹: a square meander key in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = OCHRE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=4); d.line((x, y, x, y + sy * 180), fill=col, width=4)
        def P_(u, v): return (x + sx * u, y + sy * v)
        key = [(14, 14), (70, 14), (70, 70), (28, 70), (28, 28), (56, 28), (56, 56), (42, 56)]
        d.line([P_(*p) for p in key], fill=col, width=4)
        for off in (100, 140):
            d.rectangle((min(P_(off, 12)[0], P_(off + 22, 34)[0]), min(P_(off, 12)[1], P_(off + 22, 34)[1]),
                         max(P_(off, 12)[0], P_(off + 22, 34)[0]), max(P_(off, 12)[1], P_(off + 22, 34)[1])), outline=APRICOT + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def kong(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """孔子: tall robe, small 缁布冠 bun-cap with a hairpin, long beard."""
    capped = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if capped else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if capped:
        d = A.d[layer]
        d.chord((x - 0.06 * h, y - 1.04 * h, x + 0.06 * h, y - 0.92 * h), 180, 360, fill=255)
        d.line((x - 0.11 * h, y - 0.99 * h, x + 0.11 * h, y - 0.99 * h), fill=255, width=max(2, int(0.012 * h)))
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.62 * h)], fill=255)
    return hand

def slips(A, x, y, n, h, layer='ochre', tied=True):
    w = 16
    for i in range(n):
        A.d[layer].rectangle((x + i * (w + 3), y - h, x + i * (w + 3) + w, y), fill=255)
    if tied and n:
        for yy in (y - h * 0.25, y - h * 0.75):
            A.d['ink'].line((x - 4, yy, x + n * (w + 3), yy), fill=220, width=3)

def bundle(A, x, y, s, layer='ochre'):
    A.d[layer].polygon([(x - 0.5 * s, y), (x + 0.5 * s, y), (x + 0.45 * s, y - 0.5 * s), (x - 0.45 * s, y - 0.5 * s)], fill=255)
    A.d['ink'].ellipse((x - 0.5 * s, y - 0.62 * s, x + 0.5 * s, y - 0.38 * s), outline=220, width=4)
    A.d['ink'].line((x - 0.5 * s, y - 0.25 * s, x + 0.5 * s, y - 0.25 * s), fill=255, width=4)

def qin(A, x, y, s, t, playing=True):
    A.d['ochre'].polygon([(x - s, y - 0.1 * s), (x + s, y - 0.18 * s), (x + s, y - 0.05 * s), (x - s, y + 0.02 * s)], fill=255)
    for k in range(7):
        yy = y - 0.04 * s - k * 0.016 * s
        vib = 2 * math.sin(t * 40 + k) if playing else 0
        A.d['ink'].line((x - 0.9 * s, yy, x + 0.9 * s, yy - 0.08 * s + vib), fill=170, width=1)

def ox_cart(A, x, y, s, dir=1, ph=0.0, moving=True, layer='ink'):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    bob = 0.02 * math.sin(ph * 2) if moving else 0
    d.polygon([T(*p) for p in ellipse_pts(0.75, 0.45 + bob, 0.32, 0.17)], fill=255)
    d.polygon([T(1.0, 0.55 + bob), T(1.2, 0.5 + bob), T(1.22, 0.38 + bob), T(1.05, 0.36 + bob)], fill=255)
    d.line([T(1.12, 0.56), T(1.05, 0.68)], fill=255, width=max(2, int(0.03 * s)))
    d.line([T(1.12, 0.56), T(1.22, 0.66)], fill=255, width=max(2, int(0.03 * s)))
    for k, off in enumerate((0, 1.7, 3.1, 4.6)):
        a = 0.3 * math.sin(ph + off) if moving else 0
        hu = 0.55 + 0.4 * (k // 2)
        d.line([T(hu, 0.32), T(hu + 0.12 * math.sin(a), 0.0)], fill=255, width=max(3, int(0.05 * s)))
    d.line([T(0.45, 0.5), T(-0.2, 0.45)], fill=255, width=max(2, int(0.03 * s)))
    d.rectangle((min(T(-0.75, 0.75)[0], T(-0.15, 0.3)[0]), T(-0.75, 0.75)[1], max(T(-0.75, 0.75)[0], T(-0.15, 0.3)[0]), T(-0.15, 0.3)[1]), fill=255)
    A.d['ochre'].chord((min(T(-0.85, 1.0)[0], T(-0.05, 0.6)[0]), T(-0.85, 1.0)[1], max(T(-0.85, 1.0)[0], T(-0.05, 0.6)[0]), T(-0.05, 0.6)[1] + 0.3 * s), 180, 360, fill=255)
    cx, cy = T(-0.45, 0.22)
    r = 0.22 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=max(3, int(0.04 * s)))
    a = ph * 0.8
    for k in range(4):
        d.line((cx, cy, cx + r * math.cos(a + k * math.pi / 2), cy + r * math.sin(a + k * math.pi / 2)), fill=255, width=2)

def apricot_tree(A, x, base, s, t, bloom=1.0, seed=0):
    r = random.Random(seed)
    A.d['ochre'].line((x, base, x + 0.05 * s, base - 0.6 * s), fill=255, width=int(0.08 * s))
    tips = []
    for k in range(6):
        a = -math.pi / 2 + r.uniform(-1.1, 1.1)
        L_ = s * r.uniform(0.35, 0.55)
        ex, ey = x + 0.05 * s + L_ * math.cos(a), base - 0.6 * s + L_ * math.sin(a)
        A.d['ochre'].line((x + 0.05 * s, base - 0.6 * s, ex, ey), fill=255, width=int(0.035 * s))
        tips.append((ex, ey))
    for (ex, ey) in tips:
        for j in range(int(9 * bloom)):
            px, py = ex + r.uniform(-0.12, 0.12) * s, ey + r.uniform(-0.12, 0.12) * s
            rr = 0.03 * s * (1 + 0.15 * math.sin(t * 2 + j))
            A.d['apricot'].ellipse((px - rr, py - rr, px + rr, py + rr), fill=240)

def vessel(A, x, base, s, kind=0, layer='ink'):
    """俎豆: kind 0 = 豆 (stemmed bowl), 1 = 俎 (offering table)."""
    if kind == 0:
        A.d[layer].chord((x - 0.5 * s, base - 1.0 * s, x + 0.5 * s, base - 0.4 * s), 0, 180, fill=255)
        A.d[layer].rectangle((x - 0.07 * s, base - 0.7 * s, x + 0.07 * s, base - 0.15 * s), fill=255)
        A.d[layer].polygon([(x - 0.35 * s, base), (x + 0.35 * s, base), (x + 0.1 * s, base - 0.2 * s), (x - 0.1 * s, base - 0.2 * s)], fill=255)
    else:
        A.d[layer].rectangle((x - 0.7 * s, base - 0.55 * s, x + 0.7 * s, base - 0.45 * s), fill=255)
        for sx in (-1, 1):
            A.d[layer].polygon([(x + sx * 0.6 * s, base - 0.45 * s), (x + sx * 0.5 * s, base - 0.45 * s), (x + sx * 0.6 * s, base), (x + sx * 0.7 * s, base)], fill=255)

# ================================================================ chapter card
CH = {16: 5, 48: 9, 80: 13, 112: 18, 144: 24}
def art_slips_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 9)
    shown = int(lerp(max(1, n - 5), n, ease_out(u / (1.2 * P))))
    w = shown * 19
    x0 = 540 - w / 2
    slips(A, x0, 1180, shown, 360, tied=True)
    A.d['ochre'].ellipse((x0 - 40, 820, x0 + 10, 1180), fill=255)
    r = random.Random(kb)
    for i in range(shown):
        for j in range(5):
            yy = 860 + j * 60 + r.uniform(-6, 6)
            A.d['ink'].rectangle((x0 + i * 19 + 4, yy, x0 + i * 19 + 12, yy + 22), fill=150)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_slips_chapter)
    ink_in(cv, text_img(no, SERIF, 56, OCHRE, 'Black', bleed=False, spacing=12), W / 2, 1280, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1425, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_k_hook_3000(A, cv, t, u):
    ground(A, GROUND)
    n = min(60, int(clamp(u / (1.6 * P)) * 60) + 1)
    for i in range(n):
        row = i // 12
        x = 110 + (i % 12) * 78 + (row % 2) * 30; y = GROUND - row * 46
        sitter(A, x, y, 70 - row * 6, dir=1, layer='ink' if row < 2 else 'mid')

def art_k_hook_14(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(-150, 640, (u / (1.8 * P)))
    ox_cart(A, x, GROUND, 180, dir=1, ph=t * 6)
    for k in range(3):
        person(A, x - 260 - k * 80, GROUND, 130, dir=1, robe=True, hat='knot', ph=t * 6 + k, arm=10, layer='mid')

def art_k_hook_qin(A, cv, t, u):
    ground(A, GROUND)
    sitter(A, 470, GROUND, 220, dir=1)
    qin(A, 640, GROUND - 40, 170, t)
    for k in range(5):
        A.d['ink'].ellipse((760 + k * 40, GROUND - 30, 790 + k * 40, GROUND - 10), outline=200, width=3)

def art_k_hook_east(A, cv, t, u):
    p = ease_out(u / (1.6 * P))
    for i in range(14):
        a = i * 2 * math.pi / 14
        r = 380 * p
        x, y = 540 + r * math.cos(a), 1060 + r * 0.55 * math.sin(a)
        A.d['apricot'].ellipse((x - 22, y - 22, x + 22, y + 22), fill=230)
    kong(A, 540, 1200, 300, dir=1, arm=40)
    ground(A, 1200, x0=360, x1=720)

# ================================================================ 第一回 少年志学
def art_k_niqiu(A, cv, t, u):
    A.d['mid'].polygon([(160, GROUND), (420, 1000), (560, 1060), (760, 960), (960, GROUND)], fill=200)
    ground(A, GROUND)
    person(A, 420, GROUND, 190, dir=1, robe=True, hat='knot', female=True, kneel=True, bow=30, arm=90, layer='ink')
    for k in range(10):
        q = (t * 0.3 + k / 10) % 1
        A.d['wash'].ellipse((520 + 30 * math.sin(k + t), lerp(1250, 900, q) - 8, 540 + 30 * math.sin(k + t), lerp(1250, 900, q) + 8), fill=int(200 * (1 - q)))
    A.flush(cv)
    stamp(cv, seal('尼丘山', 46), 760, 900, t, t - u + P, rot=6)

def art_k_father(A, cv, t, u):
    A.d['mid'].chord((380, 1180, 700, GROUND + 160), 180, 360, fill=230)
    ground(A, GROUND)
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='knot', female=True, bow=20, arm=-10, layer='ink')
    person(A, 840, GROUND, 90, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('叔梁纥', 46, INK), 540, 1060, t, t - u + P)

def art_k_play_rites(A, cv, t, u):
    ground(A, GROUND)
    vessel(A, 420, GROUND, 80, 0, layer='ochre')
    vessel(A, 560, GROUND, 110, 1, layer='ochre')
    vessel(A, 700, GROUND, 80, 0, layer='ochre')
    person(A, 300, GROUND, 140, dir=1, robe=True, hat='knot', bow=lerp(0, 50, 0.5 + 0.5 * math.sin(t * 2.5)), arm=100, layer='ink')
    for k in range(3):
        person(A, 800 + k * 70, GROUND, 110, dir=-1, robe=False, hat='knot', arm=lerp(-8, 140, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('俎豆', 50), 560, 960, t, t - u + P)

def art_k_resolve(A, cv, t, u):
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 6) + 1):
        bundle(A, 700 + (k % 3) * 90, GROUND - (k // 3) * 60, 80)
    sitter(A, 380, GROUND, 230, dir=1, bow=10)
    scroll(A, 500, GROUND - 120, 160, 70, u / 0.5)
    A.flush(cv)
    type_in(cv, text_img('吾十有五而志于学', SERIF, 46, OCHRE, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + P, 0.5)

def art_k_mother(A, cv, t, u):
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        x = 80 + (k * 29) % 920
        A.d['mid'].line((x, lerp(620, 1420, q), x - 6, lerp(620, 1420, q) + 30), fill=180, width=2)
    A.d['mid'].chord((340, 1220, 740, GROUND + 180), 180, 360, fill=230)
    ground(A, GROUND)
    person(A, 820, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, bow=60, arm=90, layer='ink')
    A.flush(cv)
    stamp(cv, seal('防山', 50, INK), 540, 1100, t, t - u + P)

def art_k_carp(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, ease_out(u / 0.6)), layer='mid')
    kong(A, 380, GROUND, 230, dir=1, bow=0, arm=lerp(20, 70, ease_out((u - P) / 0.5)))
    p = ease_out((u - 0.3) / (1.5 * P))
    fx, fy = lerp(700, 470, p), 1140 + 20 * math.sin(t * 6)
    A.d['red'].polygon([(fx - 70, fy), (fx - 20, fy - 26), (fx + 40, fy - 10), (fx + 70, fy - 30), (fx + 64, fy + 20), (fx + 40, fy + 6), (fx - 20, fy + 24)], fill=255)
    A.flush(cv)
    stamp(cv, seal('孔鲤', 50), 300, 900, t, t - u + 2 * P, rot=-5)

def art_k_clerk(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['ochre'].rectangle((140 + k * 120, GROUND - 200, 240 + k * 120, GROUND), fill=255)
        A.d['ochre'].polygon([(130 + k * 120, GROUND - 200), (190 + k * 120, GROUND - 250), (250 + k * 120, GROUND - 200)], fill=255)
    kong(A, 560, GROUND, 200, dir=1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 3)))
    for k in range(3):
        x = 720 + k * 110 + 10 * math.sin(t + k)
        A.d['mid'].ellipse((x - 50, GROUND - 90, x + 40, GROUND - 40), fill=230)
        A.d['mid'].ellipse((x + 30, GROUND - 100, x + 60, GROUND - 70), fill=230)
        for j in (-30, 20):
            A.d['mid'].line((x + j, GROUND - 50, x + j, GROUND), fill=230, width=8)
    A.flush(cv)
    stamp(cv, seal('委吏', 50), 260, 920, t, t - u + 0.5, rot=-4)
    stamp(cv, seal('乘田', 50), 820, 920, t, t - u + 1.5 * P, rot=5)

def art_k_thirty(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 540, GROUND, 300, dir=1, arm=lerp(-8, 20, ease_out(u / 0.6)))
    A.d['ochre'].rectangle((330, GROUND - 30, 750, GROUND), fill=255)
    A.flush(cv)
    stamp(cv, seal('私学', 54), 840, 960, t, t - u + 0.5, rot=6)

# ================================================================ 第二回 有教无类
def art_k_xingtan(A, cv, t, u):
    """6-beat set piece: 杏坛 — the altar under the apricot tree; students arrive from every rank until 三千."""
    ph = u / P
    apricot_tree(A, 540, 1160, 420, t, bloom=clamp(ph / 2) * 0.7 + 0.3, seed=21)
    A.d['ochre'].rectangle((360, 1160, 720, 1200), fill=255)
    kong(A, 540, 1160, 190, dir=1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)))
    ground(A, GROUND)
    n = min(36, int(clamp(ph / 5) * 36) + 1)
    for i in range(n):
        row = i // 12; col = i % 12
        x = 100 + col * 80 + (row % 2) * 40; y = GROUND - row * 42 + 30
        if 1150 < y and abs(x - 540) < 200 and row == 0: pass
        sitter(A, x, min(GROUND, y), 66 - row * 6, dir=1 if x < 540 else -1, layer='ink' if row == 0 else 'mid')
    A.flush(cv)
    total = int(lerp(1, 3000, ease_out(ph / 5.2)))
    paste(cv, text_img(f'弟子 {total} 人' if total < 3000 else '弟子三千 · 贤者七十二', SERIF, 48, OCHRE, 'Black', bleed=False, spacing=4), W / 2, 820, 1, 1)
    if ph >= 1.5:
        stamp(cv, seal('束脩', 46), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_k_laozi(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 360, GROUND, 230, dir=1, bow=0, arm=lerp(20, 90, ease_out(u / 0.6)))
    person(A, 720, GROUND, 230, dir=-1, robe=True, hat='knot', bow=15, arm=40, layer='ink')
    A.d['ink'].line((790, GROUND - 200, 820, GROUND), fill=255, width=6)
    for k in range(6):
        y = 860 + k * 40
        A.d['wash'].arc((420, y, 660, y + 40), 200, 340, fill=200, width=3)
    A.flush(cv)
    stamp(cv, seal('老聃', 50, INK), 720, 900, t, t - u + P, rot=6)

def art_k_shao(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        x = 600 + k * 100
        A.d['ochre'].rectangle((x - 10, GROUND - 260, x + 10, GROUND), fill=255)
        A.d['ink'].ellipse((x - 34, GROUND - 230 - 10 * math.sin(t * 6 + k), x + 34, GROUND - 190 - 10 * math.sin(t * 6 + k)), fill=255)
    sitter(A, 330, GROUND, 230, dir=1, bow=-6)
    for k in range(6):
        q = (t * 0.6 + k / 6) % 1
        A.d['ink'].line((560 - 200 * q, 1040 - 60 * q, 580 - 200 * q, 1020 - 60 * q), fill=int(200 * (1 - q)), width=4)
    A.flush(cv)
    stamp(cv, seal('韶', 64), 860, 900, t, t - u + P, rot=6)

def art_k_zhongdu(A, cv, t, u):
    city_wall(A, 160, 920, 1160, gate_x=540, label='中都', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        person(A, 160 + k * 150, GROUND, 120, dir=1 if k % 2 else -1, robe=False, hat='knot', load=k % 3 == 0, ph=t * 4 + k, arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('道不拾遗', SERIF, 50, OCHRE, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_k_jiagu(A, cv, t, u):
    A.d['ochre'].polygon([(300, 1160), (780, 1160), (720, 1080), (360, 1080)], fill=255)
    for k in range(3):
        A.d['ochre'].rectangle((360 + k * 30, 1160 + k * 40, 720 - k * 30, 1200 + k * 40), fill=255)
    ground(A, GROUND)
    person(A, 460, 1080, 150, dir=1, robe=True, hat='crown', arm=30, layer='ink')
    person(A, 620, 1080, 150, dir=-1, robe=True, hat='crown', arm=30, layer='ink')
    kong(A, 300, GROUND, 230, dir=1, arm=lerp(20, 120, ease_out((u - P) / 0.4)))
    for k in range(3):
        person(A, 860 + k * 50, GROUND, 130, dir=-1, robe=False, hat='helmet', spear=True, fall=-50 * ease_out((u - 1.6 * P) / 0.5), arm=30, layer='mid')
    A.flush(cv)
    stamp(cv, seal('齐鲁会盟', 44), 540, 900, t, t - u + 0.4)

def art_k_three_cities(A, cv, t, u):
    for i in range(3):
        x0 = 120 + i * 300
        drop = ease_out((u - P - i * 0.5 * P) / 0.6) if i < 2 else 0
        top = 1140 + 200 * drop
        A.d['mid'].rectangle((x0, top, x0 + 240, GROUND), fill=220)
        for k in range(5):
            A.d['mid'].rectangle((x0 + k * 50, top - 30, x0 + k * 50 + 30, top), fill=220)
    ground(A, GROUND)
    A.flush(cv)
    for i, nm in enumerate(('郈', '费', '成')):
        stamp(cv, seal(nm, 46, INK if i < 2 else ZHU), 240 + i * 300, 980, t, t - u + 0.3 + i * 0.2)
    if u > 2.5 * P:
        paste(cv, text_img('成邑未下 功败垂成', SERIF, 46, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 2.5 * P) / 0.3))

def art_k_leave_lu(A, cv, t, u):
    palace(A, 760, GROUND, 380, layer='mid')
    for k in range(4):
        x = 640 + k * 70
        person(A, x, GROUND, 140, dir=-1, robe=True, hat='knot', female=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='apricot')
    ground(A, GROUND)
    x = lerp(400, 60, ease_out((u - P) / (2.5 * P)))
    kong(A, x, GROUND, 220, dir=-1, ph=t * 4 if u > P else None, arm=10)
    A.flush(cv)
    stamp(cv, seal('女乐', 50), 760, 900, t, t - u + 0.4, rot=6)

# ================================================================ 第三回 周游列国
STATES = [('鲁', 760, 900, -497), ('卫', 520, 820, -497), ('匡', 470, 960, -496), ('曹', 640, 1000, -492),
          ('宋', 680, 1120, -492), ('郑', 400, 1100, -492), ('陈', 480, 1260, -489), ('蔡', 330, 1300, -489), ('楚', 200, 1380, -489)]
def scene_travel(cv, t, c, k):
    """8-beat custom scene: 周游列国 — the route through the states, one stop per beat; then it bends back to 鲁."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((120, 760, 960, 1440), radius=30, fill=200)
    A.d['ocean'].line([(140, 980), (420, 1010), (700, 960), (960, 980)], fill=150, width=14)
    A.d['ocean'].line([(140, 1330), (420, 1300), (700, 1340), (960, 1310)], fill=130, width=10)
    stops = min(len(STATES), int(ph * 1.1) + 1)
    pts = [(x, y) for _, x, y, _ in STATES[:stops]]
    if ph >= 7:
        back = ease_out((ph - 7) / 0.9)
        lx, ly = STATES[-1][1], STATES[-1][2]
        pts.append((lerp(lx, 760, back), lerp(ly, 900, back)))
    if len(pts) > 1:
        A.d['red'].line(pts, fill=230, width=8)
    if pts:
        ox_cart(A, pts[-1][0], pts[-1][1] + 10, 70, dir=1, ph=t * 6)
    A.flush(cv)
    for i, (nm, x, y, yr) in enumerate(STATES[:stops]):
        stamp(cv, seal(nm, 38, ZHU if i == 0 else OCHRE), x + 50, y - 40, t, s0 + (i / 1.1) * P)
    yrs = min(14, int(lerp(1, 14, clamp(ph / 7.8))))
    fx = Art()
    chars_in(cv, fx, '周游列国', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=82)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(yrs)}年', SERIF, 52, ZHU, 'Black', bleed=False, spacing=4), W / 2, 570, 1, 1)
    sub = '游说诸侯 · 无一国重用' if ph < 7 else '十四年后 · 回到鲁国'
    paste(cv, text_img(sub, SERIF, 44, OCHRE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_k_kuang(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 540, GROUND, 220, dir=1, arm=40)
    for k in range(4):
        sitter(A, 460 + k * 50 - 60, GROUND, 80, dir=1, layer='mid')
    n = int(clamp(u / (1.5 * P)) * 14)
    for k in range(n):
        a = math.pi + k * math.pi / 13
        x = 540 + 420 * math.cos(a); y = GROUND - 30 + 20 * math.sin(a)
        person(A, x, GROUND, 130, dir=1 if x < 540 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('误作阳虎', 44, INK), 860, 900, t, t - u + P, rot=6)

def art_k_nanzi(A, cv, t, u):
    A.d['apricot'].rectangle((560, 860, 900, GROUND - 40), fill=120)
    for k in range(8):
        A.d['ink'].line((580 + k * 42, 860, 580 + k * 42, GROUND - 40), fill=150, width=3)
    person(A, 740, GROUND - 40, 220, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mid')
    ground(A, GROUND)
    kong(A, 380, GROUND, 230, dir=1, kneel=True, bow=40, arm=90)
    person(A, 170, GROUND, 200, dir=1, robe=False, hat='helmet', arm=lerp(-8, 70, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('子路不悦', 44, INK), 200, 900, t, t - u + 1.5 * P, rot=-5)

def art_k_tree_felled(A, cv, t, u):
    fall = ease_out((u - P) / 0.8)
    cx, cy = 600, GROUND
    ang = -math.pi / 2 + fall * 1.35
    tx, ty = cx + 420 * math.cos(ang), cy + 420 * math.sin(ang)
    A.d['ochre'].line((cx, cy, tx, ty), fill=255, width=30)
    for k in range(5):
        f = 0.5 + k * 0.1
        bx, by = cx + 420 * f * math.cos(ang), cy + 420 * f * math.sin(ang)
        A.d['ochre'].line((bx, by, bx + 90 * math.cos(ang - 0.7), by + 90 * math.sin(ang - 0.7)), fill=255, width=10)
        A.d['apricot'].ellipse((bx + 90 * math.cos(ang - 0.7) - 26, by + 90 * math.sin(ang - 0.7) - 26, bx + 90 * math.cos(ang - 0.7) + 26, by + 90 * math.sin(ang - 0.7) + 26), fill=230)
    ground(A, GROUND)
    for k in range(2):
        person(A, 730 + k * 70, GROUND, 160, dir=-1, robe=False, hat='helmet', arm=lerp(20, 150, 0.5 + 0.5 * math.sin(t * 8 + k)), layer='ink')
    x = lerp(400, 120, ease_out((u - 1.5 * P) / P))
    kong(A, x, GROUND, 200, dir=-1, ph=t * 5 if u > 1.5 * P else None, arm=10)
    A.flush(cv)
    stamp(cv, seal('桓魋', 50, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_k_stray_dog(A, cv, t, u):
    city_wall(A, 260, 1020, 1140, gate_x=760, label='郑', layer='mid')
    ground(A, GROUND)
    kong(A, 760, GROUND, 230, dir=-1, arm=-10)
    for k in range(4):
        q = (t * 0.6 + k * 0.25) % 1
        A.d['wash'].line((140, 1100 + k * 40, 140 + 200 * q, 1100 + k * 40 + 10 * math.sin(q * 6)), fill=200, width=4)
    x = lerp(-80, 300, ease_out(u / (2 * P)))
    person(A, x, GROUND, 190, dir=1, robe=True, hat='knot', ph=t * 7, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('然哉', 54), 860, 900, t, t - u + 2.5 * P, rot=6)

def art_k_starving(A, cv, t, u):
    """6-beat set piece: 陈蔡绝粮 — encircled in the wilds; day counter to 七; disciples sink, the qin keeps playing."""
    ph = u / P
    day = min(7, int(ph * 7 / 5.5) + 1)
    for k in range(10):
        x = 100 + k * 100
        A.d['grass'].polygon([(x - 40, GROUND), (x, GROUND - 90 - 30 * math.sin(k)), (x + 40, GROUND)], fill=150)
    ground(A, GROUND)
    for k in range(5):
        sitter(A, 200 + k * 80, GROUND, 110, dir=1, bow=min(60, 8 * day + k * 3), layer='mid')
    sitter(A, 720, GROUND, 200, dir=-1, bow=0)
    qin(A, 600, GROUND - 30, 130, t)
    for k in range(12):
        a = math.pi + k * math.pi / 11
        x = 540 + 500 * math.cos(a)
        person(A, x, GROUND - 230, 70, dir=1 if x < 540 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    for k in range(4):
        q = (t * 0.7 + k / 4) % 1
        A.d['ink'].line((640 - 120 * q, 1180 - 120 * q, 655 - 120 * q, 1165 - 120 * q), fill=int(220 * (1 - q)), width=4)
    A.flush(cv)
    paste(cv, text_img(f'断粮第{cn_num(day)}天', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph >= 4:
        type_in(cv, text_img('君子固穷 小人穷斯滥矣', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + 4 * P, 0.5)

# ================================================================ 第四回 晚年归鲁
def art_k_return(A, cv, t, u):
    city_wall(A, 520, 1020, 1100, gate_x=760, label='曲阜', layer='mid', open_=1.0)
    ground(A, GROUND)
    x = lerp(-150, 560, ease_out(u / (3 * P)))
    ox_cart(A, x, GROUND, 150, dir=1, ph=t * 5, moving=u < 3 * P)
    kong(A, x - 160, GROUND, 190, dir=1, ph=t * 4 if u < 3 * P else None, arm=10)
    A.flush(cv)
    stamp(cv, seal('归鲁', 54), 260, 900, t, t - u + 2 * P, rot=-5)

CLASSICS = ['诗', '书', '礼', '乐', '易', '春秋']
def art_k_six(A, cv, t, u):
    """8-beat set piece: 删述六经 — one classic per beat appears as a bundle with its seal; the old man writes on."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='ochre')
    sitter(A, 300, GROUND, 220, dir=1, bow=lerp(10, 20, 0.5 + 0.5 * math.sin(t * 2)))
    lamp(A, 700, GROUND - 70, 40, t, glow=0.5)
    n = min(6, int(ph) + 1)
    for i in range(n):
        x = 180 + i * 145
        y = 1080 - 30 * ease_out(clamp((ph - i) / 0.4))
        bundle(A, x, y, 100)
    A.flush(cv)
    for i in range(n):
        stamp(cv, seal(CLASSICS[i], 40 if i < 5 else 34), 180 + i * 145, 940, t, t - u + i * P + 0.15)
    if ph >= 6.5:
        paste(cv, text_img('述而不作 信而好古', SERIF, 46, OCHRE, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 6.5) / 0.3))

def art_k_son_dies(A, cv, t, u):
    A.d['mid'].chord((380, 1240, 640, GROUND + 120), 180, 360, fill=230)
    for k in range(20):
        q = (t * 0.2 + k / 20) % 1
        x = 100 + (k * 47) % 880
        A.d['apricot'].ellipse((x - 6, lerp(620, 1400, q) - 6, x + 6, lerp(620, 1400, q) + 6), fill=int(200 * (1 - q)))
    ground(A, GROUND)
    kong(A, 780, GROUND, 230, dir=-1, kneel=True, bow=30, arm=40)
    A.flush(cv)
    stamp(cv, seal('孔鲤', 50, INK), 510, 1100, t, t - u + P)

def art_k_yanhui(A, cv, t, u):
    ground(A, GROUND)
    A.d['ochre'].rectangle((620, GROUND - 60, 940, GROUND - 40), fill=255)
    person(A, 780, GROUND - 60, 140, dir=1, robe=True, hat='knot', fall=-88, layer='mid')
    kong(A, 380, GROUND, 240, dir=1, kneel=True, bow=lerp(0, 50, ease_out((u - P) / 0.6)), arm=lerp(20, 160, ease_out((u - P) / 0.6)))
    vessel(A, 860, GROUND - 60, 30, 0)
    A.flush(cv)
    stamp(cv, seal('颜回', 50), 780, 940, t, t - u + 0.4, rot=6)

def art_k_qilin(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['grass'].polygon([(x - 80, GROUND), (x, GROUND - 160), (x + 80, GROUND)], fill=140)
    ground(A, GROUND)
    d = A.d['ink']
    x, y, s = 540, GROUND - 4, 160
    d.polygon([(x - s, y - 0.3 * s), (x + 0.9 * s, y - 0.45 * s), (x + 1.0 * s, y - 0.2 * s), (x - s, y - 0.05 * s)], fill=255)
    d.ellipse((x + 0.8 * s, y - 0.6 * s, x + 1.25 * s, y - 0.25 * s), fill=255)
    d.line((x + 1.05 * s, y - 0.6 * s, x + 1.1 * s, y - 0.85 * s), fill=255, width=8)
    for k in range(8):
        A.d['apricot'].ellipse((x - 0.8 * s + k * 0.2 * s - 10, y - 0.42 * s - 10, x - 0.8 * s + k * 0.2 * s + 10, y - 0.42 * s + 10), fill=255)
    arrow(A, x - 0.3 * s, y - 0.6 * s, math.pi / 2 + 0.4, 100)
    kong(A, 200, GROUND, 220, dir=1, arm=lerp(-8, 60, ease_out((u - P) / 0.5)))
    A.flush(cv)
    stamp(cv, seal('获麟', 54), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_k_zilu(A, cv, t, u):
    for k in range(6):
        ang = -2.6 + k * 0.25
        arrow(A, 540 + 420 * math.cos(ang) * (1 - (t * 0.8 % 1) * 0.5), 1080 + 300 * math.sin(ang), ang + math.pi, 70)
    ground(A, GROUND)
    p = ease_out((u - 1.5 * P) / 0.8)
    person(A, 540, GROUND, 260, dir=1, robe=False, hat='helmet', sword=lerp(30, 120, p), arm=lerp(140, 60, p), kneel=p > 0.5, layer='ink')
    A.flush(cv)
    stamp(cv, seal('结缨', 54), 860, 880, t, t - u + 1.8 * P, rot=6)

def art_k_taishan(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (540, 860), (880, GROUND)], fill=200)
    crack = ease_out((u - P) / P)
    A.d['ink'].line((540, 870, 520, 980 * 1 + 0 * crack, 560, 1080, 530, 1080 + 200 * crack), fill=200, width=6)
    ground(A, GROUND)
    kong(A, 220, GROUND, 220, dir=1, arm=lerp(-8, 30, 0.5 + 0.5 * math.sin(t)))
    A.d['ink'].line((310, GROUND - 160, 330, GROUND), fill=255, width=6)
    A.flush(cv)
    type_in(cv, text_img('泰山其颓乎 梁木其坏乎', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + P, 0.5)

# ================================================================ 第五回 万世师表
def art_k_death(A, cv, t, u):
    A.d['ocean'].line([(60, 1360), (400, 1340), (700, 1370), (1020, 1350)], fill=160, width=20)
    A.d['mid'].chord((380, 1180, 700, 1480), 180, 360, fill=230)
    ground(A, GROUND)
    for k in range(6):
        person(A, 160 + k * 60 if k < 3 else 760 + (k - 3) * 60, GROUND, 130, dir=1 if k < 3 else -1, robe=True, hat='knot', kneel=True, bow=55, arm=100, layer='ink')
    A.flush(cv)
    stamp(cv, seal('泗上', 50, INK), 540, 1060, t, t - u + P)

def art_k_zigong(A, cv, t, u):
    A.d['mid'].chord((180, 1180, 500, 1480), 180, 360, fill=230)
    A.d['ochre'].polygon([(620, 1180), (760, 1080), (900, 1180)], fill=255)
    A.d['ochre'].rectangle((640, 1180, 880, GROUND), fill=255)
    A.d['wash'].rectangle((730, 1260, 790, GROUND), fill=255)
    ground(A, GROUND)
    sitter(A, 560, GROUND, 150, dir=-1, bow=10)
    yrs = min(6, int(clamp(u / (3 * P)) * 6) + 1)
    A.flush(cv)
    paste(cv, text_img(f'守墓第{cn_num(yrs)}年', SERIF, 50, OCHRE, 'Black', bleed=False, spacing=6), W / 2, 880, 1, 1)

def art_k_analects(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        sitter(A, 160 + k * 110, GROUND, 130, dir=1, bow=20)
    p = ease_out(u / (2.5 * P))
    slips(A, 620, GROUND - 60, int(4 + 12 * p), 260)
    A.flush(cv)
    lines = ['学而时习之', '三人行 必有我师焉', '己所不欲 勿施于人']
    for i, ln in enumerate(lines):
        type_in(cv, text_img(ln, SERIF, 42, OCHRE if i == 2 else INK, 'Black', bleed=False, spacing=4), W / 2, 820 + i * 66, t, t - u + 0.3 + i * 0.8 * P, 0.4)

def art_k_hanwu(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 240, dir=1, robe=True, hat='crown', arm=lerp(20, 110, ease_out(u / 0.6)), layer='ink')
    for k in range(4):
        x = 160 + k * 70 if k < 2 else 780 + (k - 2) * 90
        bundle(A, x, GROUND, 70) if k >= 2 else person(A, x, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, bow=45, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('独尊儒术', 44), 860, 900, t, t - u + P, rot=6)

def art_k_wenxuan(A, cv, t, u):
    palace(A, 540, GROUND, 620, layer='ochre')
    ground(A, GROUND)
    A.d['yellow'].rectangle((420, 1000, 660, 1060), fill=255)
    A.flush(cv)
    ink_in(cv, text_img('文宣王', SERIF, 44, INK, 'Black', bleed=False, spacing=8), W / 2, 1030, t, t - u + 0.5, dur=0.3)

def art_k_plaque(A, cv, t, u):
    palace(A, 540, GROUND, 680, layer='mid')
    ground(A, GROUND)
    p = ease_out(u / (1.2 * P))
    A.d['ochre'].rectangle((540 - 260 * p, 900, 540 + 260 * p, 1020), fill=255)
    A.d['yellow'].rectangle((540 - 240 * p, 912, 540 + 240 * p, 1008), fill=255)
    A.flush(cv)
    if p > 0.9:
        ink_in(cv, text_img('万世师表', BRUSH, 80, INK), W / 2, 960, t, t - u + 1.2 * P, dur=0.3, settle=1.2)
    stamp(cv, seal('康熙御书', 44), 860, 1180, t, t - u + 2 * P, rot=6)

def art_k_legacy(A, cv, t, u):
    apricot_tree(A, 540, GROUND, 620, t, bloom=1.0, seed=99)
    ground(A, GROUND)

def art_k_title(A, cv, t, u):
    apricot_tree(A, 820, 1460, 560, t, bloom=1.0, seed=7)
    kong(A, 430, 1460, 720, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年志学'), 48: ('第二回', '有教无类'), 80: ('第三回', '周游列国'),
            112: ('第四回', '晚年归鲁'), 144: ('第五回', '万世师表')}

CARDS = [
    C(0, 2, 'works', 'num', num='弟子三千', line='贤者七十二人', art=art_k_hook_3000),
    C(2, 4, 'fate', 'num', num='十四年', line='周游列国 无人重用', art=art_k_hook_14),
    C(4, 6, 'night', 'num', num='七天', line='断粮仍在弹琴', art=art_k_hook_qin),
    C(6, 8, 'empire', 'num', num='两千五百年', line='影响了整个东亚', art=art_k_hook_east),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年志学
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-551, main='尼丘祈子', sub='生于鲁国陬邑 · 名丘 字仲尼', note='传说 父母祷于尼丘得孔子', art=art_k_niqiu),
    C(22, 26, 'death', 'card', year=-549, main='幼年丧父', sub='随母移居曲阜 · 家境贫寒', art=art_k_father),
    C(26, 30, 'life', 'card', year=-545, main='陈俎豆', sub='儿时游戏 · 摆礼器演礼仪', note='常陈俎豆 设礼容', art=art_k_play_rites),
    C(30, 34, 'works', 'card', year=-536, main='十五志学', sub='立志求学', art=art_k_resolve),
    C(34, 38, 'night', 'card', year=-534, main='母亲去世', sub='少年丧母 · 独自谋生', note='合葬父母于防山', art=art_k_mother),
    C(38, 42, 'court', 'card', year=-532, main='鲁君赐鲤', sub='得子 · 取名孔鲤', note='鲁昭公以鲤鱼赐孔子', art=art_k_carp),
    C(42, 46, 'life', 'card', year=-531, main='委吏乘田', sub='管仓库 管牛羊 · 件件做好', note='料量平 畜蕃息', art=art_k_clerk),
    C(46, 48, 'works', 'card', year=-522, main='三十而立', sub='开办私学', art=art_k_thirty),
    # ---- 第二回 有教无类
    C(48, 50, 'works', 'chapter'),
    C(50, 56, 'works', 'card', year=-522, main='杏坛讲学', sub='有教无类 · 不问出身', note='自行束脩以上 吾未尝无诲焉', art=art_k_xingtan),
    C(56, 60, 'life', 'card', year=-518, main='问礼老子', sub='适周 · 向老子请教', note='一说 孔子问礼于老聃', art=art_k_laozi),
    C(60, 64, 'court', 'card', year=-517, main='在齐闻韶', sub='三月不知肉味', note='不图为乐之至于斯也', art=art_k_shao),
    C(64, 68, 'empire', 'card', year=-501, main='中都宰', sub='五十出仕 · 一年大治', note='四方皆则之', art=art_k_zhongdu),
    C(68, 72, 'war', 'card', year=-500, main='夹谷之会', sub='以礼折服齐君 · 收回失地', art=art_k_jiagu),
    C(72, 76, 'court', 'card', year=-498, main='隳三都', sub='拆除权臣城池 · 半途而废', art=art_k_three_cities),
    C(76, 80, 'night', 'card', year=-497, main='去鲁', sub='齐国送来女乐 · 鲁君三日不朝', note='孔子遂行', art=art_k_leave_lu),
    # ---- 第三回 周游列国
    C(80, 82, 'fate', 'chapter'),
    C(82, 90, 'fate', 'travel', year=-497),
    C(90, 94, 'war', 'card', year=-496, main='畏于匡', sub='被误认作阳虎 · 围困五日', note='文王既没 文不在兹乎', art=art_k_kuang),
    C(94, 98, 'court', 'card', year=-495, main='子见南子', sub='卫灵公夫人召见', art=art_k_nanzi),
    C(98, 102, 'war', 'card', year=-492, main='宋人伐树', sub='桓魋欲杀孔子 · 拔其树', note='天生德于予 桓魋其如予何', art=art_k_tree_felled),
    C(102, 106, 'fate', 'card', year=-492, main='丧家之犬', sub='郑国东门 · 与弟子走散', note='累累若丧家之狗', art=art_k_stray_dog),
    C(106, 112, 'night', 'card', year=-489, main='陈蔡绝粮', sub='被困荒野 · 弦歌不辍', note='从者病 莫能兴', art=art_k_starving),
    # ---- 第四回 晚年归鲁
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'life', 'card', year=-484, main='回到鲁国', sub='十四年漂泊 · 终回故土', art=art_k_return),
    C(118, 126, 'works', 'card', year=-484, main='删述六经', sub='诗 书 礼 乐 易 春秋', note='晚而喜易 韦编三绝', art=art_k_six),
    C(126, 130, 'death', 'card', year=-483, main='老年丧子', sub='孔鲤先他而去', art=art_k_son_dies),
    C(130, 134, 'death', 'card', year=-481, main='颜回早逝', sub='最得意的弟子', note='噫 天丧予 天丧予', art=art_k_yanhui),
    C(134, 138, 'fate', 'card', year=-481, main='西狩获麟', sub='麒麟被猎 · 绝笔春秋', note='吾道穷矣', art=art_k_qilin),
    C(138, 142, 'war', 'card', year=-480, main='子路战死', sub='死于卫国内乱', note='君子死 冠不免', art=art_k_zilu),
    C(142, 144, 'night', 'card', year=-479, main='泰山其颓', sub='自知将逝', art=art_k_taishan),
    # ---- 第五回 万世师表
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=-479, main='辞世', sub='葬于泗水之上', note='弟子皆服丧三年', art=art_k_death),
    C(150, 154, 'life', 'card', year=-479, main='子贡守墓', sub='庐于冢上 · 凡六年', art=art_k_zigong),
    C(154, 158, 'works', 'card', year=-400, main='论语', sub='弟子辑录其言行', note='战国初年成书', art=art_k_analects),
    C(158, 162, 'empire', 'card', year=-134, main='独尊儒术', sub='汉武帝时 · 儒学成为正统', art=art_k_hanwu),
    C(162, 166, 'court', 'card', year=739, main='文宣王', sub='唐玄宗追封', art=art_k_wenxuan),
    C(166, 170, 'end', 'card', year=1684, main='御书匾额', sub='康熙亲题 · 悬于孔庙', art=art_k_plaque),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾壹', col=OCHRE, acc=APRICOT, born=-551, died=-479, age0=-550.25,
    born_lab='前551年', died_lab='前479年', years_txt='公元前551 — 前479',
    hook_q='一个失败的政客 · 为何成了万世师表？',
    name_line='孔丘 · 字仲尼', name='孔子', seal='仲尼', title_art=art_k_title,
    q1='万世师表？', q2='丧家之犬？',
    end_art=art_k_legacy, end_big='万世师表', end_seal='尼山',
    end_l1='活着时 他四处碰壁', end_l2='死后 影响了两千五百年',
    end_brush='知其不可而为之', end_ask='他哪句话你最认同？评论区聊聊', next='屈原'),
    scenes=dict(chapter=scene_chapter, travel=scene_travel))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
