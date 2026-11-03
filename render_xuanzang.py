"""千古人物志 · 第叁拾玖集 · 玄奘 (602–664)
Look: 袈裟赭 + 经卷黄, 法轮 corner borders, a 经笈 (sutra backpack) chapter card: the frame fills with more scrolls each
chapter; in the last the lamp on its canopy is lit.
Set pieces: 6-beat 莫贺延碛, custom 8-beat scene 'westward' (route map 长安 → 天竺), 6-beat 那烂陀,
8-beat 曲女城大会, 6-beat 回到长安, 6-beat 译经.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_fanzhongyan as Fz     # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter
from render_quyuan import river
from render_kongzi import bundle
from render_wudi import camel
from render_zhangqian import yurt
from render_qianlong import palm

F.RIPPLE = False
KASAYA = (178, 84, 44)              # 袈裟赭
SUTRA = (214, 182, 100)             # 经卷黄
S.LAYERS.append(('kasaya', KASAYA, 0.88, 1.0))
S.LAYERS.append(('sutra', SUTRA, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='经', life='奘', court='唐', night='夜', war='难', empire='唐', works='经', fate='行', death='寂', end='经')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (SUTRA, 230, (W * 0.5, 820))
G.THEMES['fate']['sun'] = (KASAYA, 220, (W * 0.5, 780))
G.THEMES['end']['sun'] = (SUTRA, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

STUPA = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STUPA)
for _x, _s in ((110, 1.0), (970, 0.8)):
    _d.chord((_x - 60 * _s, 1360 - 90 * _s, _x + 60 * _s, 1360 + 30 * _s), 180, 360, fill=KASAYA + (44,))
    _d.rectangle((_x - 70 * _s, 1360, _x + 70 * _s, 1480), fill=KASAYA + (34,))
    _d.line((_x, 1360 - 90 * _s, _x, 1360 - 170 * _s), fill=KASAYA + (60,), width=4)
MTN_COL = {'night': (40, 36, 34), 'death': (62, 60, 58), 'war': (110, 70, 44), 'fate': (120, 96, 62)}
def draw_background(t, theme):
    """西行: dry ridges, small stupas at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(200, 190, 172), (166, 146, 118), MTN_COL.get(theme, (128, 104, 78))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.8))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STUPA)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """法轮: an eight-spoked wheel in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=KASAYA + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=KASAYA + (220,), width=3)
        cx, cy, r = x + sx * 52, y + sy * 52, 28
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SUTRA + (240,), width=5)
        for k in range(8):
            a = k * math.pi / 4
            d.line((cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)), fill=SUTRA + (240,), width=3)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=KASAYA + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xz(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, pack=False, staff=True, **kw):
    """玄奘: shaven head, kasaya over one shoulder, 锡杖 staff; optionally the 经笈 backpack."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, kneel=kneel, bow=bow, **kw)
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    if up:
        A.d['kasaya'].polygon([(x - 0.09 * h, y - 0.78 * h), (x + 0.1 * h, y - 0.5 * h), (x + 0.16 * h, y - 0.1 * h), (x + 0.02 * h, y - 0.1 * h)], fill=255)
        if staff:
            sx = x + dir * 0.22 * h
            A.d[layer].line((sx, y, sx + dir * 0.02 * h, y - 1.2 * h), fill=255, width=max(2, int(0.016 * h)))
            A.d['sutra'].ellipse((sx + dir * 0.02 * h - 0.05 * h, y - 1.28 * h, sx + dir * 0.02 * h + 0.05 * h, y - 1.18 * h), outline=255, width=max(2, int(0.012 * h)))
        if pack:
            jx = x - dir * 0.16 * h
            backpack(A, jx, y - 0.35 * h, 0.55 * h, 6)
    return hand

def backpack(A, x, base, s, scrolls, lit=0.0, t=0.0):
    """经笈: a frame with shelves of scrolls and a canopy; an oil lamp hangs from the canopy edge."""
    A.d['ink'].rectangle((x - 0.32 * s, base - s, x + 0.32 * s, base), outline=255, width=max(3, int(0.03 * s)))
    for k in range(1, 4):
        A.d['ink'].line((x - 0.32 * s, base - k * 0.25 * s, x + 0.32 * s, base - k * 0.25 * s), fill=255, width=max(2, int(0.02 * s)))
    n = min(scrolls, 12)
    for i in range(n):
        r, c = i // 3, i % 3
        cx = x - 0.2 * s + c * 0.2 * s; cy = base - 0.12 * s - r * 0.25 * s
        A.d['sutra'].ellipse((cx - 0.08 * s, cy - 0.08 * s, cx + 0.08 * s, cy + 0.08 * s), fill=255)
    A.d['kasaya'].polygon([(x - 0.5 * s, base - s), (x + 0.5 * s, base - s), (x + 0.36 * s, base - 1.14 * s), (x - 0.36 * s, base - 1.14 * s)], fill=255)
    A.d['ink'].line((x + 0.46 * s, base - s, x + 0.46 * s, base - 0.86 * s), fill=255, width=2)
    if lit > 0:
        lamp(A, x + 0.46 * s, base - 0.76 * s, 0.1 * s, t, glow=lit)

def bodhi(A, x, base, s, t):
    A.d['ink'].line((x, base, x + 0.05 * s, base - 0.5 * s), fill=255, width=int(0.07 * s))
    r = random.Random(9)
    for k in range(30):
        a = r.uniform(0, 2 * math.pi); rr = r.uniform(0, 1) ** 0.5 * 0.45 * s
        px, py = x + rr * math.cos(a), base - 0.75 * s + 0.6 * rr * math.sin(a)
        A.d['grass'].polygon([(px, py - 0.06 * s), (px + 0.04 * s, py), (px, py + 0.03 * s), (px - 0.04 * s, py)], fill=230)

# ================================================================ chapter card
CH = {16: (2, 0.0), 48: (4, 0.0), 80: (8, 0.0), 112: (12, 0.0), 144: (12, 1.0)}
def art_pack_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n, lit = CH.get(kb, (4, 0.0))
    q = ease_out(u / (1.2 * P))
    prev = {48: 2, 80: 4, 112: 8}.get(kb, 0)
    backpack(A, 540, 1160, 340, int(lerp(prev, n, q)), lit=lit * q, t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_pack_chapter)
    ink_in(cv, text_img(no, SERIF, 56, KASAYA, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_road(A, cv, t, u):
    p = ease_out(u / (1.6 * P))
    pts = [(lerp(940, 140, f), 1240 - 160 * math.sin(f * 3)) for f in np.linspace(0, p, 30)]
    if len(pts) > 1:
        A.d['kasaya'].line(pts, fill=230, width=8)
        xz(A, pts[-1][0], pts[-1][1], 90, dir=-1, ph=t * 5, pack=True)
    ground(A, GROUND)

def art_x_hook_17(A, cv, t, u):
    ground(A, GROUND)
    n = min(17, int(clamp(u / (1.6 * P)) * 17) + 1)
    for i in range(n):
        x = 140 + i * 48
        A.d['sutra' if i % 4 else 'kasaya'].rectangle((x - 16, GROUND - 40 - (i % 3) * 20, x + 16, GROUND), fill=255)

def art_x_hook_scrolls(A, cv, t, u):
    ground(A, GROUND)
    n = min(130, int(clamp(u / (1.6 * P)) * 130) + 1)
    for i in range(n):
        x = 110 + (i % 26) * 34; y = GROUND - 20 - (i // 26) * 40
        A.d['sutra'].ellipse((x - 14, y - 14, x + 14, y + 14), fill=255)

def art_x_hook_monkey(A, cv, t, u):
    ground(A, GROUND)
    horse(A, 700, GROUND, 170, dir=-1, ph=t * 4, layer='mid')
    xz(A, 420, GROUND, 250, dir=1, ph=t * 3, arm=40)

# ================================================================ 第一回 少年出家
def art_x_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 260), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('洛州缑氏', 46), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('俗姓陈 名祎', SERIF, 48, KASAYA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_father(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    ground(A, GROUND)
    for k in range(2):
        person(A, 780 + k * 80, GROUND, 150 - k * 20, dir=-1, robe=True, hat='knot', kneel=True, bow=50, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('幼年丧父 · 随兄入寺', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_ordain(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='kasaya')
    ground(A, GROUND)
    person(A, 720, GROUND, 220, dir=-1, robe=True, hat='none', arm=lerp(20, 90, ease_out(u / P)), layer='ink')
    xz(A, 380, GROUND, 160, dir=1, kneel=u < 2 * P, bow=30 if u < 2 * P else 0, arm=100, staff=False)
    A.flush(cv)
    stamp(cv, seal('破格度僧', 46), 260, 880, t, t - u + 0.4, rot=-5)
    type_in(cv, text_img('远绍如来 近光遗法', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)

def art_x_shu(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 130, GROUND), (x, GROUND - 440 - 80 * (k % 2)), (x + 130, GROUND)], fill=200)
    pts = [(x, GROUND - 160 - 90 * math.sin(x / 130)) for x in range(80, W - 79, 20)]
    A.d['sutra'].line(pts, fill=230, width=8)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    xz(A, pts[i][0], pts[i][1], 100, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    stamp(cv, seal('隋末大乱', 46, INK), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('入蜀', 54), 860, 880, t, t - u + 2 * P, rot=6)

def art_x_vow(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mid')
    ground(A, GROUND)
    for k in range(6):
        sitter(A, 160 + k * 60 if k < 3 else 780 + (k - 3) * 70, GROUND, 120, dir=1 if k < 3 else -1, bow=20, layer='mid')
    xz(A, 540, GROUND, 230, dir=1, kneel=True, bow=10, arm=100, staff=False)
    A.flush(cv)
    stamp(cv, seal('成都', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('二十岁 受具足戒', SERIF, 48, KASAYA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_masters(A, cv, t, u):
    pts = [(200, 1100), (440, 1000), (680, 1120), (880, 980)]
    p = ease_out(u / (3 * P))
    n = max(1, int(p * len(pts)))
    A.d['kasaya'].line(pts[:n + 1] if n < len(pts) else pts, fill=200, width=6)
    for k, (x, y) in enumerate(pts[:n]):
        sitter(A, x, y + 100, 120, dir=1, bow=10, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    for k, nm in enumerate(('荆州', '相州', '赵州', '长安')[:n]):
        stamp(cv, seal(nm, 30, KASAYA), pts[k][0], pts[k][1] - 40, t, t - u + k * 0.75 * P)
    paste(cv, text_img('遍访名师 · 诸说纷纭 莫衷一是', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_resolve(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    lamp(A, 700, GROUND, 50, t, glow=0.6)
    sitter(A, 460, GROUND, 220, dir=1, bow=lerp(20, 0, ease_out((u - P) / P)))
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('誓游西方 以问所惑', SERIF, 50, KASAYA, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)

def art_x_denied(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='none', arm=lerp(20, 150, ease_out(u / 0.6)), layer='ink')
    xz(A, 360, GROUND, 210, dir=1, kneel=True, bow=30, arm=100, staff=False)
    A.flush(cv)
    stamp(cv, seal('不许', 60, INK), 860, 860, t, t - u + 0.5, rot=6)

# ================================================================ 第二回 冒禁西行
def art_x_sneak(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    city_wall(A, 520, 1020, 1100, gate_x=770, label='长安', layer='mid')
    ground(A, GROUND)
    xz(A, lerp(560, 100, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 4, pack=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('二十五岁 · 私自西行', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('一说 贞观三年', 34, INK), 860, 1060, t, t - u + P, rot=6)

def art_x_liangzhou(A, cv, t, u):
    city_wall(A, 160, 700, 1100, gate_x=430, label='凉州', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(3):
        rider(A, lerp(-200, 300, ease_out(u / (2 * P))) - k * 100, GROUND, 110, 1, t * 10 + k, layer='ink', spear=True)
    xz(A, lerp(600, 980, ease_out(u / (2.5 * P))), GROUND, 180, dir=1, ph=t * 6, pack=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('官府追捕 · 昼伏夜行', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_beacons(A, cv, t, u):
    A.d['dune'].polygon([(60, 1300), (W - 60, 1280), (W - 60, GROUND), (60, GROUND)], fill=120)
    for k in range(5):
        x = 150 + k * 200
        A.d['ink'].rectangle((x - 20, 1180, x + 20, 1290), fill=255)
    xz(A, 560, 1290, 150, dir=1, kneel=True, bow=10, arm=60, staff=False)
    A.d['ocean'].ellipse((600, 1270, 660, 1290), fill=200)
    for k in range(3):
        ax = lerp(370, 520, ((t * 0.8 + k * 0.33) % 1))
        arrow(A, ax, 1200 + k * 20 + ((t * 0.8 + k * 0.33) % 1) * 60, 0.4, 70)
    A.flush(cv)
    stamp(cv, seal('玉门关外五烽', 38), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('取水时 飞箭擦膝而过', SERIF, 44, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_desert(A, cv, t, u):
    """6-beat set piece: 莫贺延碛 — eight hundred li of desert; the water bag slips and spills; four nights and five days
    without water; he collapses; the old horse finds a spring."""
    ph = u / P
    sun(cv, 860, 820, 110, KASAYA, 160)
    A.d['dune'].polygon([(60, 1200), (300, 1160), (600, 1210), (900, 1170), (W - 60, 1200), (W - 60, GROUND), (60, GROUND)], fill=150)
    for k in range(6):
        x = 120 + k * 170
        A.d['wash'].ellipse((x - 10, GROUND - 6, x + 10, GROUND + 2), fill=230)
    day = min(5, int(ph * 5 / 4.5) + 1)
    if ph < 1:
        xz(A, 500, 1280, 180, dir=1, ph=t * 3, pack=True, arm=60)
        A.d['ocean'].ellipse((600, 1180 + 100 * ph, 640, 1210 + 100 * ph), fill=220)
    elif ph < 4:
        xz(A, 460, 1280, 180, dir=1, ph=t * 2, pack=True, arm=-8)
        horse(A, 650, 1280, 130, dir=1, ph=t * 2, layer='mid')
    else:
        xz(A, 440, 1280, 170, dir=1, fall=-80, arm=-8, staff=False)
        hx = lerp(650, 850, ease_out((ph - 4.5) / 1))
        horse(A, hx, 1280, 130, dir=1, ph=t * 4, layer='mid')
        if ph > 5:
            A.d['ocean'].ellipse((860, 1260, 980, 1300), fill=200)
            A.d['grass'].polygon([(860, 1260), (900, 1220), (940, 1260)], fill=220)
    A.flush(cv)
    paste(cv, text_img(f'四夜五日 滴水不进 · 第{cn_num(day)}天', SERIF, 44, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph >= 5:
        paste(cv, text_img('老马识途 · 寻到水草', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 5) / 0.3))

def art_x_gaochang(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='sutra')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', kneel=True, bow=30, arm=110, layer='ink')
    xz(A, 360, GROUND, 230, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('高昌王', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('结为兄弟 · 资助西行', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

ROUTE = [('高昌', 900, 1000), ('凌山', 760, 900), ('碎叶', 620, 880), ('飒秣建', 520, 1000), ('铁门', 440, 1100),
         ('梵衍那', 360, 1180), ('迦湿弥罗', 300, 1260), ('天竺', 220, 1360)]
def scene_westward(cv, t, c, k):
    """8-beat custom scene: 西行之路 — the route crawls west and south across mountains; one stop per beat; at 凌山 the
    snow kills a third of the caravan."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=180)
    for x, y in ((760, 860), (400, 1060), (300, 1160)):
        A.d['mid'].polygon([(x - 90, y + 60), (x, y - 60), (x + 90, y + 60)], fill=200)
        A.d['wash'].polygon([(x - 30, y - 20), (x, y - 60), (x + 30, y - 20)], fill=255)
    stops = min(len(ROUTE), int(ph) + 1)
    pts = [(x, y) for _, x, y in ROUTE[:stops]]
    if stops >= 2:
        f = clamp(ph - (stops - 1) + 1)
        A.d['kasaya'].line(pts, fill=230, width=7)
    camel(A, pts[-1][0], pts[-1][1] + 30, 50, -1, t * 6, layer='ink')
    if 1 <= ph < 2.5:
        for j in range(40):
            q = (t * 0.6 + j / 40) % 1
            A.d['wash'].ellipse((600 + (j * 37) % 360 - 4, lerp(800, 1000, q) - 4, 600 + (j * 37) % 360 + 4, lerp(800, 1000, q) + 4), fill=230)
    A.flush(cv)
    for i, (nm, x, y) in enumerate(ROUTE[:stops]):
        stamp(cv, seal(nm, 28, ZHU if nm in ('凌山', '天竺') else KASAYA), x, y - 46, t, s0 + i * P + 0.2)
    fx = Art()
    chars_in(cv, fx, '西行之路', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=72)
    fx.flush(cv)
    lab = '翻越凌山 · 冻死者十有三四' if 1 <= ph < 2.5 else ('西突厥可汗 遣使护送' if ph < 4 else '穿越中亚 · 南下天竺')
    paste(cv, text_img(lab, SERIF, 44, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)

# ================================================================ 第三回 那烂陀
def art_x_arrive(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['grass'].polygon([(x - 150, GROUND), (x, GROUND - 200), (x + 150, GROUND)], fill=160)
    ground(A, GROUND)
    palm(A, 200, GROUND - 360, t)
    palm(A, 880, GROUND - 320, t)
    xz(A, lerp(1000, 540, ease_out(u / (2.5 * P))), GROUND, 220, dir=-1, ph=t * 4, pack=True, arm=-8)
    A.flush(cv)
    stamp(cv, seal('天竺', 56), 540, 880, t, t - u + 2 * P)

def art_x_bodhi(A, cv, t, u):
    bodhi(A, 620, GROUND, 520, t)
    ground(A, GROUND)
    xz(A, 340, GROUND, 210, dir=1, kneel=True, bow=lerp(0, 60, ease_out(u / P)), arm=110, staff=False)
    A.flush(cv)
    stamp(cv, seal('菩提伽耶', 44), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('至佛陀成道处 · 悲泣不已', SERIF, 44, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_nalanda(A, cv, t, u):
    """6-beat set piece: 那烂陀寺 — a sprawling monastery; thousands of monks; the 106-year-old 戒贤 receives him;
    five years of study."""
    ph = u / P
    for k in range(5):
        x = 140 + k * 200
        A.d['kasaya'].rectangle((x - 80, 1060, x + 80, 1240), fill=200)
        A.d['ink'].polygon([(x - 100, 1060), (x + 100, 1060), (x, 980)], fill=255)
    ground(A, GROUND)
    n = int(clamp(ph / 3) * 30)
    for i in range(n):
        sitter(A, 110 + (i % 15) * 62, GROUND - (i // 15) * 40, 70, dir=1, bow=15, layer='ink' if i // 15 == 0 else 'mid')
    if ph >= 3:
        sitter(A, 860, 1240, 150, dir=-1, bow=30, layer='ink')
        xz(A, 640, 1240, 160, dir=1, kneel=True, bow=40, arm=110, staff=False)
    A.flush(cv)
    stamp(cv, seal('那烂陀', 50), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img(f'僧众 {n * 330} 人' if ph < 3 else '拜戒贤为师 · 学瑜伽论', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph >= 4:
        paste(cv, text_img('一住五年', SERIF, 48, ZHU, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((ph - 4) / 0.3))

def art_x_wander(A, cv, t, u):
    pts = [(lerp(140, 940, f), 1100 + 160 * math.sin(f * 9)) for f in np.linspace(0, 1, 40)]
    A.d['kasaya'].line(pts, fill=220, width=6)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    xz(A, pts[i][0], pts[i][1], 90, dir=1, ph=t * 4, pack=True)
    for k in range(6):
        x, y = pts[k * 7]
        A.d['ink'].chord((x - 20, y - 50, x + 20, y - 10), 180, 360, fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('游学五印度 · 遍访高僧', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_robbers(A, cv, t, u):
    river(A, 1220, t, rows=3, amp=6, speed=1.8)
    boat(A, 540, 1260, 160, t, sail=False)
    xz(A, 480, 1230, 150, dir=1, kneel=True, bow=0, arm=-8, staff=False)
    for k in range(3):
        person(A, 600 + k * 50, 1230, 140, dir=-1, robe=False, hat='knot', sword=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), arm=120, layer='ink')
    if u > 2 * P:
        for k in range(40):
            q = (t * 1.6 + k / 40) % 1
            A.d['dune'].line((lerp(-100, 1200, q), 700 + (k * 37) % 500, lerp(-100, 1200, q) + 60, 700 + (k * 37) % 500), fill=200, width=4)
    A.flush(cv)
    stamp(cv, seal('遇盗', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('欲杀他祭神 · 忽起狂风', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_kanyakubja(A, cv, t, u):
    """8-beat set piece: 曲女城大会 — kings, thousands of monks; his treatise hangs at the gate; eighteen days, nobody
    rebuts it; he is carried on an elephant as 大乘天."""
    ph = u / P
    A.d['sutra'].rectangle((360, 900, 720, 1120), fill=200)
    A.d['kasaya'].polygon([(330, 900), (750, 900), (540, 820)], fill=255)
    ground(A, GROUND)
    for i in range(24):
        sitter(A, 100 + (i % 12) * 80, GROUND - (i // 12) * 40, 70, dir=1 if (i % 12) < 6 else -1, bow=15, layer='ink' if i // 12 == 0 else 'mid')
    if ph < 6:
        xz(A, 540, 1120, 160, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2)), staff=False)
    else:
        q = ease_out((ph - 6) / 1.5)
        ex = lerp(800, 540, q)
        A.d['mid'].ellipse((ex - 120, 1040, ex + 120, 1160), fill=230)
        A.d['mid'].rectangle((ex - 100, 1140, ex - 70, 1250), fill=230); A.d['mid'].rectangle((ex + 60, 1140, ex + 90, 1250), fill=230)
        A.d['mid'].line((ex - 120, 1080, ex - 170, 1220), fill=230, width=24)
        xz(A, ex, 1040, 120, dir=-1, arm=60, staff=False)
    A.flush(cv)
    stamp(cv, seal('戒日王', 46), 860, 880, t, t - u + 0.4, rot=6)
    days = min(18, int(lerp(1, 18, clamp((ph - 1) / 4.5))))
    paste(cv, text_img(f'辩经第{cn_num(days)}天 · 无人能难' if ph < 6 else '大乘天 · 解脱天', SERIF, 46, KASAYA if ph < 6 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

# ================================================================ 第四回 东归
def art_x_farewell(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    xz(A, lerp(500, 200, ease_out((u - P) / (2 * P))), GROUND, 210, dir=-1, ph=t * 3 if u > P else None, pack=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('婉拒挽留 · 决意东归', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_lost(A, cv, t, u):
    river(A, 1200, t, rows=4, amp=9, speed=2.4)
    boat(A, 540, 1240, 170, t * 2, sail=False)
    xz(A, 480, 1210, 150, dir=1, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 5)), staff=False)
    for k in range(5):
        q = clamp((u - P - k * 0.15 * P) / P)
        A.d['sutra'].ellipse((600 + k * 60 + 60 * q - 14, 1180 + 80 * q - 14, 600 + k * 60 + 60 * q + 14, 1180 + 80 * q + 14), fill=int(255 * (1 - q)))
    A.flush(cv)
    stamp(cv, seal('印度河', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('渡河时 失经五十夹', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_khotan(A, cv, t, u):
    yurt(A, 760, GROUND, 340, 280, layer='sutra')
    ground(A, GROUND)
    xz(A, 380, GROUND, 210, dir=1, kneel=True, bow=20, arm=100, staff=False)
    scroll(A, 560, GROUND - 160, 140, 50, u / 0.5)
    rider(A, lerp(600, 1200, ease_out((u - 1.5 * P) / (2 * P))), GROUND, 120, 1, t * 11, layer='mid')
    A.flush(cv)
    stamp(cv, seal('于阗', 54), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('上表请罪 · 等候回音', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_return(A, cv, t, u):
    """6-beat set piece: 回到长安 — the city gate; crowds line both sides for miles; carts of sutras roll in."""
    ph = u / P
    city_wall(A, 60, 1020, 1060, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    n = int(clamp(ph / 3) * 24)
    for i in range(n):
        x = 100 + (i % 12) * 80 if i < 12 else 100 + (i % 12) * 80
        y = GROUND - (0 if i < 12 else 60)
        if 380 < x < 700 and i < 12: continue
        person(A, x, y, 100, dir=1 if x < 540 else -1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + i)), layer='mid')
    for k in range(4):
        camel(A, lerp(1200, 600 + k * 110, ease_out((ph - k * 0.3) / 3)), GROUND, 90, -1, t * 5 + k, layer='ink')
    A.flush(cv)
    paste(cv, text_img('满城出迎 · 道俗奔赴', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(ph / 0.4))
    if ph >= 3:
        paste(cv, text_img('带回经书六百五十七部', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3) / 0.3))

def art_x_taizong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='sutra')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    xz(A, 360, GROUND, 220, dir=1, arm=40, staff=False)
    A.flush(cv)
    stamp(cv, seal('唐太宗', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('劝其还俗为官 · 婉拒', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_record(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='kasaya')
    sitter(A, 300, GROUND, 200, dir=1, bow=10)
    sitter(A, 780, GROUND, 180, dir=-1, bow=25, layer='mid')
    for k in range(int(clamp(u / (2 * P)) * 12)):
        bundle(A, 420 + (k % 6) * 40, GROUND - 74 - (k // 6) * 30, 30, layer='sutra')
    A.flush(cv)
    ink_in(cv, text_img('大唐西域记', SERIF, 50, KASAYA, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, dur=0.3)
    paste(cv, text_img('记一百一十国 · 弟子辩机执笔', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_x_preface(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    scroll(A, 540, 1000, 420, 160, u / 0.6, layer='yellow')
    A.flush(cv)
    if u > 0.6:
        ink_in(cv, text_img('大唐三藏圣教序', SERIF, 42, INK, 'Black', bleed=False, spacing=4), 540, 1000, t, t - u + 0.6, dur=0.3)
    stamp(cv, seal('太宗亲撰', 44), 860, 1180, t, t - u + 1.5 * P, rot=6)

# ================================================================ 第五回 译经
def art_x_translate(A, cv, t, u):
    """6-beat set piece: 译经 — translation hall: he reads the Sanskrit, scribes write, scrolls pile up; counter to 一千三百三十五卷."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='kasaya')
    xz(A, 540, GROUND - 60, 160, dir=1, kneel=True, bow=10, arm=100, staff=False)
    for k in range(4):
        sitter(A, 160 + k * 70 if k < 2 else 840 + (k - 2) * 70, GROUND, 110, dir=1 if k < 2 else -1, bow=25, layer='mid')
    n = int(clamp(ph / 5) * 40)
    for i in range(n):
        x = 130 + (i % 20) * 42; y = 900 + (i // 20) * 46
        A.d['sutra'].ellipse((x - 16, y - 16, x + 16, y + 16), fill=255)
    lamp(A, 360, GROUND - 70, 30, t, glow=0.6)
    A.flush(cv)
    vols = int(lerp(1, 1335, clamp(ph / 5)))
    paste(cv, text_img(f'译出 {vols} 卷' if vols < 1335 else '七十五部 · 一千三百三十五卷', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_x_pagoda(A, cv, t, u):
    p = ease_out(u / (2.5 * P))
    n = max(1, int(p * 5))
    base = GROUND
    for k in range(n):
        w = 300 - k * 40; h = 90
        A.d['sutra'].rectangle((540 - w / 2, base - h, 540 + w / 2, base), fill=230)
        A.d['ink'].rectangle((540 - w / 2 - 20, base - h - 10, 540 + w / 2 + 20, base - h), fill=255)
        A.d['ink'].rectangle((530, base - h + 20, 550, base - 20), fill=255)
        base -= h + 10
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('大雁塔', 54), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('为保存经像 · 亲自负土', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_yuhua(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 380), (x + 150, GROUND)], fill=200)
    palace(A, 540, GROUND, 380, layer='sutra')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('玉华宫', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('译完大般若经六百卷', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_nirvana(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xz(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, staff=False)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('圆寂 · 年六十二', SERIF, 50, KASAYA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_funeral(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 40)
    for i in range(n):
        person(A, 100 + (i % 20) * 46, GROUND - (i // 20) * 50, 90, dir=1, robe=True, hat='knot', bow=20, ph=t * 2 + i, arm=-8, layer='ink' if i // 20 == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img('五百里内 送葬者百余万', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_xiyouji(A, cv, t, u):
    ground(A, GROUND)
    horse(A, 700, GROUND, 160, dir=-1, ph=t * 3, layer='wash')
    xz(A, 700, GROUND - 120, 140, dir=-1, arm=40, staff=False)
    for k in range(3):
        person(A, 860 + k * 60, GROUND, 120, dir=-1, robe=False, hat='knot', ph=t * 4 + k, arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('明代西游记 · 唐僧取经', SERIF, 46, KASAYA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_legacy(A, cv, t, u):
    backpack(A, 860, 1440, 200, 12, lit=1.0, t=t)

def art_x_title(A, cv, t, u):
    backpack(A, 820, 1300, 260, 12)
    xz(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年出家'), 48: ('第二回', '冒禁西行'), 80: ('第三回', '那烂陀寺'),
            112: ('第四回', '万里东归'), 144: ('第五回', '译经十九年')}

CARDS = [
    C(0, 2, 'fate', 'num', num='五万里', line='一个人走到印度', art=art_x_hook_road),
    C(2, 4, 'works', 'num', num='十七年', line='才回到长安', art=art_x_hook_17),
    C(4, 6, 'empire', 'num', num='一千三百卷', line='译了十九年', art=art_x_hook_scrolls),
    C(6, 8, 'life', 'num', num='唐僧', line='真实的他没有徒弟', art=art_x_hook_monkey),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年出家
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=602, main='生于缑氏', sub='洛州缑氏县', note='生年 一说六〇〇年', art=art_x_birth),
    C(22, 26, 'death', 'card', year=610, main='幼年丧父', sub='随二哥长捷法师', art=art_x_father),
    C(26, 30, 'works', 'card', year=612, main='洛阳出家', sub='少年破格剃度', art=art_x_ordain),
    C(30, 34, 'war', 'card', year=618, main='避乱入蜀', sub='隋末天下大乱', art=art_x_shu),
    C(34, 38, 'life', 'card', year=622, main='受具足戒', sub='成都大慈寺', art=art_x_vow),
    C(38, 42, 'works', 'card', year=624, main='遍访名师', sub='疑惑反而更多', art=art_x_masters),
    C(42, 46, 'night', 'card', year=626, main='立志西行', sub='去天竺求取原典', art=art_x_resolve),
    C(46, 48, 'court', 'card', year=627, main='上表被拒', sub='朝廷禁止出关', art=art_x_denied),
    # ---- 第二回 冒禁西行
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'night', 'card', year=627, main='偷渡出关', sub='孤身出发', art=art_x_sneak),
    C(54, 58, 'war', 'card', year=627, main='凉州追捕', sub='有人通风 有人放行', art=art_x_liangzhou),
    C(58, 62, 'war', 'card', year=627, main='五烽', sub='夜里偷偷取水', art=art_x_beacons),
    C(62, 68, 'death', 'card', year=627, main='莫贺延碛', sub='八百里流沙', note='上无飞鸟 下无走兽', art=art_x_desert),
    C(68, 72, 'empire', 'card', year=628, main='高昌国', sub='国王麴文泰', art=art_x_gaochang),
    C(72, 80, 'fate', 'westward', year=628),
    # ---- 第三回 那烂陀寺
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'life', 'card', year=630, main='抵达天竺', sub='终于踏上佛国', art=art_x_arrive),
    C(86, 90, 'night', 'card', year=631, main='菩提树下', sub='佛陀成道之地', art=art_x_bodhi),
    C(90, 96, 'works', 'card', year=631, main='那烂陀寺', sub='当时世界最大的佛学院', art=art_x_nalanda),
    C(96, 100, 'fate', 'card', year=636, main='游学五印', sub='走遍印度', art=art_x_wander),
    C(100, 104, 'war', 'card', year=637, main='遇盗', sub='恒河上被劫', note='大慈恩寺三藏法师传所记', art=art_x_robbers),
    C(104, 112, 'empire', 'card', year=642, main='曲女城大会', sub='十八国王 · 数千僧众', art=art_x_kanyakubja),
    # ---- 第四回 万里东归
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'life', 'card', year=643, main='辞别戒日王', sub='满载经像东归', art=art_x_farewell),
    C(118, 122, 'death', 'card', year=644, main='渡河失经', sub='损失惨重', art=art_x_lost),
    C(122, 126, 'court', 'card', year=644, main='于阗上表', sub='为当年偷渡请罪', art=art_x_khotan),
    C(126, 132, 'empire', 'card', year=645, main='回到长安', sub='离开十七年', art=art_x_return),
    C(132, 136, 'court', 'card', year=645, main='太宗召见', sub='洛阳宫中长谈', art=art_x_taizong),
    C(136, 140, 'works', 'card', year=646, main='西域记', sub='奉诏撰写', art=art_x_record),
    C(140, 144, 'empire', 'card', year=648, main='圣教序', sub='皇帝为译经作序', art=art_x_preface),
    # ---- 第五回 译经十九年
    C(144, 146, 'works', 'chapter'),
    C(146, 152, 'works', 'card', year=650, main='译经', sub='日夜不辍', note='创立唯识宗', art=art_x_translate),
    C(152, 156, 'empire', 'card', year=652, main='大雁塔', sub='慈恩寺内', art=art_x_pagoda),
    C(156, 160, 'life', 'card', year=663, main='大般若经', sub='最后的巨作', art=art_x_yuhua),
    C(160, 164, 'death', 'card', year=664, main='圆寂', sub='玉华寺', art=art_x_nirvana),
    C(164, 168, 'fate', 'card', year=664, main='百万送葬', sub='葬于白鹿原', art=art_x_funeral),
    C(168, 170, 'end', 'card', year=1592, main='西游记', sub='真实的取经更难', art=art_x_xiyouji),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾玖', col=KASAYA, acc=SUTRA, born=602, died=664,
    hook_q='没有孙悟空 · 他一个人怎么走到印度？',
    name_line='玄奘 · 俗名陈祎', name='玄奘', seal='三藏', title_art=art_x_title,
    q1='求法圣僧？', q2='偷渡者？',
    end_art=art_x_legacy, end_big='宁向西死', end_seal='三藏',
    end_l1='他没有徒弟 没有神通', end_l2='只有一匹老马和一个愿',
    end_brush='宁可就西而死', end_ask='你有过非做不可的事吗？评论区聊聊', next='郭子仪'),
    scenes=dict(chapter=scene_chapter, westward=scene_westward))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
