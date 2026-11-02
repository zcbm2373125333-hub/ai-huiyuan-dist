"""千古人物志 · 第叁拾肆集 · 李清照 (1084–约1155)
Look: 海棠粉 + 黛青, 菊瓣 corner borders, a 海棠 chapter card: the crabapple branch in full bloom, then
"绿肥红瘦", bare, and finally a single yellow chrysanthemum (人比黄花瘦).
Set pieces: 6-beat 争渡 (lotus boat, startled egrets), 8-beat 赌书泼茶, custom 8-beat scene 'southward'
(金石南渡: the collection shrinks cart by cart), 6-beat 声声慢, 6-beat 金石录后序.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_sushi as Ss           # engine + helpers (previous episode)
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
from render_simaqian import brush
from render_libai import moon_phase, wine_jar
from render_kongzi import bundle
from render_qianlong import palm

F.RIPPLE = False
BEGONIA = (214, 112, 128)           # 海棠粉
DAI = (60, 70, 96)                  # 黛青
S.LAYERS.append(('begonia', BEGONIA, 0.88, 1.0))
S.LAYERS.append(('dai', DAI, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='清', life='照', court='宋', night='愁', war='渡', empire='宋', works='词', fate='瘦', death='寂', end='清')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (BEGONIA, 220, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['night']['sun'] = None
G.THEMES['end']['sun'] = (DAI, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

LATTICE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(LATTICE)
for _x0 in (70, W - 200):
    _d.rectangle((_x0, 1180, _x0 + 130, 1460), outline=DAI + (50,), width=4)
    for _k in range(1, 5):
        _d.line((_x0, 1180 + _k * 56, _x0 + 130, 1180 + _k * 56), fill=DAI + (36,), width=2)
    for _k in range(1, 3):
        _d.line((_x0 + _k * 43, 1180, _x0 + _k * 43, 1460), fill=DAI + (36,), width=2)
MTN_COL = {'night': (36, 36, 48), 'death': (60, 60, 66), 'war': (98, 64, 60), 'fate': (90, 80, 96)}
def draw_background(t, theme):
    """闺阁: soft far hills, lattice windows at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 186, 190), (156, 144, 158), MTN_COL.get(theme, (116, 104, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.8))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(LATTICE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """菊瓣: a small chrysanthemum (ring of petals) in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DAI + (200,), width=3); d.line((x, y, x, y + sy * 180), fill=DAI + (200,), width=3)
        cx, cy = x + sx * 52, y + sy * 52
        for k in range(12):
            a = k * math.pi / 6
            d.line((cx + 8 * math.cos(a), cy + 8 * math.sin(a), cx + 28 * math.cos(a), cy + 28 * math.sin(a)), fill=(214, 170, 60, 230), width=5)
        d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=BEGONIA + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def qz(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """李清照: slender woman, high bun with a hairpin; stoops when old."""
    b = bow + 16 * old
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, layer=layer, kneel=kneel, bow=b, **kw)
    if not kneel and abs(b) < 1 and not kw.get('fall'):
        A.d[layer].ellipse((x - 0.06 * h, y - 1.06 * h, x + 0.04 * h, y - 0.96 * h), fill=255)
        A.d['begonia' if old < 0.5 else 'dai'].line((x - 0.08 * h, y - 1.0 * h, x + 0.06 * h, y - 1.06 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def zhao(A, x, y, h, dir=1, layer='ink', **kw):
    """赵明诚: scholar in a 幞头."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall') and not kw.get('bow'):
        A.d[layer].rectangle((x - 0.06 * h, y - 1.03 * h, x + 0.06 * h, y - 0.94 * h), fill=255)
        A.d[layer].rectangle((x - 0.18 * h, y - 0.99 * h, x + 0.18 * h, y - 0.975 * h), fill=255)
    return hand

def begonia_branch(A, x, y, s, t, bloom=1.0, leaves=0.3):
    r = random.Random(7)
    A.d['ink'].line((x, y, x + 0.8 * s, y - 0.5 * s), fill=255, width=int(0.04 * s))
    for k in range(6):
        f = (k + 1) / 7
        bx, by = x + 0.8 * s * f, y - 0.5 * s * f
        a = -math.pi / 2 + r.uniform(-0.8, 0.8)
        ex, ey = bx + 0.25 * s * math.cos(a), by + 0.25 * s * math.sin(a)
        A.d['ink'].line((bx, by, ex, ey), fill=255, width=int(0.018 * s))
        for j in range(3):
            px, py = ex + r.uniform(-0.06, 0.06) * s, ey + r.uniform(-0.06, 0.06) * s
            if r.random() < leaves:
                Ss_leaf(A, px, py, r.uniform(0, 6.28), 0.12 * s)
            elif r.random() < bloom:
                rr = 0.035 * s * (1 + 0.1 * math.sin(t * 2 + j))
                A.d['begonia'].ellipse((px - rr, py - rr, px + rr, py + rr), fill=240)

def Ss_leaf(A, x, y, a, L_):
    from render_wangyangming import leaf
    leaf(A, 'grass', x, y, a, L_, L_ * 0.22, fill=230)

def chrysanthemum(A, x, y, r, t, layer='gold'):
    for k in range(16):
        a = k * math.pi / 8 + 0.05 * math.sin(t + k)
        A.d[layer].line((x + 0.2 * r * math.cos(a), y + 0.2 * r * math.sin(a), x + r * math.cos(a), y + r * math.sin(a)), fill=255, width=max(3, int(0.12 * r)))
    A.d['ink'].line((x, y + 0.3 * r, x + 0.2 * r, y + 3 * r), fill=255, width=max(2, int(0.06 * r)))

def bronze(A, x, base, s, kind=0):
    if kind == 0:
        A.d['bronze'].chord((x - s, base - 1.1 * s, x + s, base - 0.1 * s), 0, 180, fill=255)
        for lx in (-0.6, 0, 0.6):
            A.d['bronze'].rectangle((x + lx * s - 0.07 * s, base - 0.4 * s, x + lx * s + 0.07 * s, base), fill=255)
        for sx in (-1, 1):
            A.d['bronze'].rectangle((x + sx * 0.55 * s - 0.06 * s, base - 0.9 * s, x + sx * 0.55 * s + 0.06 * s, base - 0.6 * s), fill=255)
    else:
        A.d['bronze'].polygon([(x - 0.4 * s, base - 1.4 * s), (x + 0.4 * s, base - 1.4 * s), (x + 0.2 * s, base - 0.7 * s), (x + 0.4 * s, base), (x - 0.4 * s, base), (x - 0.2 * s, base - 0.7 * s)], fill=255)

# ================================================================ chapter card
CH = {16: (1.0, 0.1, 0), 48: (0.9, 0.3, 0), 80: (0.35, 0.8, 0), 112: (0.0, 0.2, 0), 144: (0.0, 0.0, 1)}
def art_begonia_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    bloom, leaves, chrys = CH.get(kb, (0.9, 0.3, 0))
    q = ease_out(u / P)
    if chrys:
        chrysanthemum(A, 540, 960, 90 * q + 4, t)
    else:
        begonia_branch(A, 220, 1200, 760, t, bloom=bloom * q, leaves=leaves)
    if kb == 112:
        for k in range(20):
            qq = (t * 0.4 + k / 20) % 1
            A.d['begonia'].ellipse((300 + (k * 41) % 500 - 6, lerp(900, 1300, qq) - 4, 300 + (k * 41) % 500 + 6, lerp(900, 1300, qq) + 4), fill=int(200 * (1 - qq)))
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_begonia_chapter)
    ink_in(cv, text_img(no, SERIF, 56, BEGONIA, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_queen(A, cv, t, u):
    ground(A, GROUND)
    qz(A, 540, GROUND, 300, dir=1, arm=lerp(-8, 60, ease_out(u / (1.2 * P))))
    for k in range(3):
        sitter(A, 160 + k * 60, GROUND, 110, dir=1, bow=20, layer='mid')
        sitter(A, 920 - k * 60, GROUND, 110, dir=-1, bow=20, layer='mid')

def art_q_hook_carts(A, cv, t, u):
    ground(A, GROUND)
    n = max(1, 15 - int(clamp(u / (1.6 * P)) * 14))
    for i in range(n):
        x = 120 + (i % 8) * 110; y = GROUND - (i // 8) * 90
        A.d['dai'].rectangle((x - 40, y - 60, x + 40, y - 20), fill=255)
        A.d['ink'].ellipse((x - 30, y - 30, x - 4, y - 4), outline=255, width=4)
        A.d['ink'].ellipse((x + 4, y - 30, x + 30, y - 4), outline=255, width=4)

def art_q_hook_thin(A, cv, t, u):
    chrysanthemum(A, 680, 980, 70, t)
    ground(A, GROUND)
    qz(A, 420, GROUND, 260, dir=1, arm=40, old=0.2)

def art_q_hook_divorce(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    qz(A, 300, GROUND, 230, dir=1, arm=-8)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    A.d['ink'].line((540, 960, 540, 1360), fill=int(255 * ease_out(u / (1.2 * P))), width=6)

# ================================================================ 第一回 少女词名
def art_q_jinan(A, cv, t, u):
    A.d['ocean'].ellipse((160, 1240, 920, 1380), fill=150)
    for k in range(5):
        x = 300 + k * 110
        for j in range(4):
            q = (t * 1.2 + j / 4 + k * 0.2) % 1
            A.d['wash'].ellipse((x - 6 - 10 * q, 1300 - 120 * q - 6, x + 6 + 10 * q, 1300 - 120 * q + 6), fill=int(220 * (1 - q)))
    ground(A, GROUND, x0=60, x1=160)
    A.flush(cv)
    stamp(cv, seal('济南', 56), 860, 880, t, t - u + P, rot=6)
    stamp(cv, seal('易安', 50), 260, 940, t, t - u + 1.5 * P, rot=-5)

def art_q_father(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='dai')
    zhao(A, 760, GROUND, 230, dir=-1, arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 2)))
    qz(A, 340, GROUND, 160, dir=1, arm=70)
    for k in range(int(clamp(u / (2 * P)) * 6)):
        bundle(A, 440 + k * 40, GROUND - 74, 30, layer='begonia')
    A.flush(cv)
    stamp(cv, seal('李格非', 46, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_q_zhengdu(A, cv, t, u):
    """6-beat: 如梦令 — dusk on the lotus pond; tipsy, she rows the wrong way; '争渡 争渡'; egrets burst up."""
    ph = u / P
    sun(cv, 860, 900, 70, ZHU, 120)
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND), fill=150)
    waves(A, 1170, t, rows=3, amp=4, speed=1.2)
    for k in range(18):
        x = 100 + (k * 53) % 880; y = 1160 + (k * 37) % 180
        A.d['grass'].ellipse((x - 40, y - 12, x + 40, y + 12), fill=220)
        if k % 3 == 0:
            A.d['begonia'].polygon([(x, y - 50), (x - 16, y - 14), (x + 16, y - 14)], fill=255)
    x = lerp(300, 700, ease_out(ph / 4))
    boat(A, x, 1260, 100, t * 2, sail=False)
    qz(A, x, 1230, 130, dir=1, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 5)))
    if ph >= 3:
        for k in range(8):
            q = clamp((ph - 3 - k * 0.08) / 1.5)
            crow_x = x + 60 + k * 30 + 200 * q; crow_y = 1180 - 400 * q - (k % 3) * 30
            A.d['wash'].polygon([(crow_x - 26, crow_y), (crow_x, crow_y - 14 * math.sin(t * 12 + k)), (crow_x + 26, crow_y), (crow_x, crow_y + 6)], fill=255)
    A.flush(cv)
    type_in(cv, text_img('争渡 争渡', SERIF, 56, BEGONIA, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 1.5 * P, 0.4)
    if ph >= 3:
        type_in(cv, text_img('惊起一滩鸥鹭', SERIF, 50, INK, 'Black', bleed=False, spacing=8), W / 2, 910, t, t - u + 3 * P, 0.4)

def art_q_haitang(A, cv, t, u):
    for k in range(50):
        q = (t * 0.8 + k / 50) % 1
        x = 80 + (k * 19) % 920
        A.d['wash'].line((x, lerp(620, 1420, q), x - 4, lerp(620, 1420, q) + 18), fill=180, width=2)
    begonia_branch(A, 560, 1260, 420, t, bloom=0.4, leaves=0.7)
    ground(A, GROUND)
    qz(A, 300, GROUND, 220, dir=1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    type_in(cv, text_img('知否 知否', SERIF, 52, INK, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 0.5, 0.4)
    type_in(cv, text_img('应是绿肥红瘦', SERIF, 52, BEGONIA, 'Black', bleed=False, spacing=8), W / 2, 900, t, t - u + 1.5 * P, 0.4)

def art_q_fame(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 140 + k * 160
        person(A, x, GROUND, 150, dir=1 if k % 2 else -1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
        A.d['wash'].rectangle((x + 30, GROUND - 130, x + 70, GROUND - 100), fill=255)
    A.flush(cv)
    paste(cv, text_img('文士莫不击节称赏', SERIF, 48, BEGONIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_marry(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='begonia')
    ground(A, GROUND)
    qz(A, 640, GROUND, 210, dir=-1, arm=lerp(20, 60, ease_out(u / P)))
    zhao(A, 420, GROUND, 230, dir=1, arm=lerp(20, 60, ease_out(u / P)))
    A.d['red'].line((480, GROUND - 160, 600, GROUND - 160), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('赵明诚', 50), 860, 880, t, t - u + P, rot=6)

def art_q_pawn(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((140, 1060, 440, GROUND), fill=200)
    A.d['ink'].polygon([(120, 1060), (460, 1060), (290, 980)], fill=255)
    zhao(A, lerp(300, 700, ease_out(u / (2 * P))), GROUND, 210, dir=1, ph=t * 4, arm=60)
    A.d['wash'].rectangle((lerp(340, 740, ease_out(u / (2 * P))), GROUND - 160, lerp(380, 780, ease_out(u / (2 * P))), GROUND - 120), fill=255)
    qz(A, 860, GROUND, 190, dir=-1, arm=40)
    A.flush(cv)
    paste(cv, text_img('典衣买碑帖', SERIF, 50, DAI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_q_parted(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='mid')
    ground(A, GROUND)
    qz(A, lerp(540, 1000, ease_out(u / (2.5 * P))), GROUND, 200, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('党争', 54, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('元祐党人之女 被逐出京', SERIF, 46, DAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第二回 赌书泼茶
def art_q_qingzhou(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 280), (x + 200, GROUND)], fill=200)
    A.d['dai'].rectangle((360, 1060, 720, GROUND), fill=220)
    A.d['ink'].polygon([(330, 1060), (750, 1060), (540, 960)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('归来堂', 50), 540, 900, t, t - u + P)
    paste(cv, text_img('屏居青州 十年', SERIF, 48, BEGONIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_tea(A, cv, t, u):
    """8-beat set piece: 赌书泼茶 — two at a table piled with books; she names a passage, points to the volume and page;
    she wins, laughs, and spills the tea."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='dai')
    for k in range(10):
        bundle(A, 340 + k * 42, GROUND - 74 - (k % 3) * 18, 34, layer='begonia' if k % 3 else 'mid')
    zhao(A, 780, GROUND, 220, dir=-1, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)))
    qz(A, 300, GROUND, 210, dir=1, arm=lerp(40, 150, ease_out((ph - 1) / 0.6)))
    cx = 470; cy = GROUND - 90
    A.d['ink'].chord((cx - 22, cy - 20, cx + 22, cy + 10), 0, 180, fill=255)
    if ph >= 5:
        for k in range(10):
            q = clamp((ph - 5) / 1) * (0.5 + k / 20)
            A.d['gold'].ellipse((cx + 30 * q * k / 5 - 6, cy - 10 + 60 * q - 6, cx + 30 * q * k / 5 + 6, cy - 10 + 60 * q + 6), fill=200)
    A.flush(cv)
    if 1 <= ph < 4:
        paste(cv, text_img('某事在某书某卷 第几页 第几行', SERIF, 42, DAI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((ph - 1) / 0.3))
    if ph >= 4:
        paste(cv, text_img('举杯大笑 茶倾覆怀中', SERIF, 46, BEGONIA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 4) / 0.3))
    if ph >= 6:
        type_in(cv, text_img('赌书消得泼茶香', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 6 * P, 0.5)

def art_q_collect(A, cv, t, u):
    ground(A, GROUND)
    for r in range(3):
        for c2 in range(6):
            x = 200 + c2 * 136; y = 980 + r * 110
            A.d['dai'].rectangle((x - 50, y, x + 50, y + 90), outline=255, width=4)
            if r * 6 + c2 < int(clamp(u / (2.5 * P)) * 18):
                bronze(A, x, y + 86, 30, kind=(r + c2) % 2)
    A.flush(cv)
    paste(cv, text_img('金石书画 · 十余屋', SERIF, 48, BEGONIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_jinshilu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='dai')
    zhao(A, 300, GROUND, 220, dir=1, kneel=True, bow=20, arm=90)
    qz(A, 780, GROUND, 200, dir=-1, kneel=True, bow=20, arm=90)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['wash'].rectangle((420 + k * 30, GROUND - 90, 444 + k * 30, GROUND - 74), fill=255)
    A.flush(cv)
    ink_in(cv, text_img('金石录', BRUSH, 110, DAI), W / 2, 930, t, t - u + P, dur=0.3, settle=1.2)

def art_q_chongyang(A, cv, t, u):
    chrysanthemum(A, 760, 1000, 70, t)
    A.d['dai'].rectangle((200, 900, 560, GROUND), fill=150)
    for k in range(6):
        A.d['ink'].line((220 + k * 60, 900, 220 + k * 60, GROUND), fill=150, width=3)
    qz(A, 600, GROUND, 220, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t)))
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('莫道不销魂 帘卷西风', SERIF, 44, DAI, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('人比黄花瘦', SERIF, 56, BEGONIA, 'Black', bleed=False, spacing=10), W / 2, 905, t, t - u + 1.6 * P, 0.5)

def art_q_fifty(A, cv, t, u):
    ground(A, GROUND)
    zhao(A, 540, GROUND, 230, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(int(clamp(u / (2 * P)) * 50)):
        x = 120 + (k % 10) * 30; y = 900 + (k // 10) * 50
        A.d['wash'].rectangle((x, y, x + 22, y + 36), fill=255)
        A.d['ink'].rectangle((x, y, x + 22, y + 36), outline=120, width=1)
    A.flush(cv)
    stamp(cv, seal('相传', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('他闭门三日写五十首 · 终不及她三句', SERIF, 40, DAI, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_q_laixiang(A, cv, t, u):
    city_wall(A, 420, 980, 1100, gate_x=700, label='莱州', layer='mid', open_=1.0)
    ground(A, GROUND)
    qz(A, lerp(-80, 560, ease_out(u / (2.5 * P))), GROUND, 200, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('赴莱州', 50), 260, 880, t, t - u + P, rot=-5)

# ================================================================ 第三回 金石南渡
def art_q_jingkang(A, cv, t, u):
    palace(A, 540, GROUND, 620, collapse=ease_out((u - P) / (2 * P)), layer='mid')
    flames(A, 540, GROUND, 800, 280 * ease_out((u - 0.5 * P) / 0.8), t, n=8, seed=13, smoke=True)
    ground(A, GROUND)
    for k in range(5):
        rider(A, lerp(-200, 300, ease_out(u / (2 * P))) - k * 100, GROUND, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('靖康之变', 46, INK), 860, 860, t, t - u + 0.4, rot=6)

def scene_southward(cv, t, c, k):
    """8-beat custom scene: 金石南渡 — fifteen carts of the collection set out; at each stop the column shrinks
    (青州 burned, 江宁, 洪州 lost, 越州 stolen); she walks on with a single bundle."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    n = int(lerp(15, 1, clamp(ph / 7)))
    for i in range(n):
        x = 980 - i * 60 - 40 * ((t * 0.5) % 1)
        A.d['dai'].rectangle((x - 26, GROUND - 60, x + 26, GROUND - 24), fill=255)
        A.d['ink'].ellipse((x - 24, GROUND - 30, x - 4, GROUND - 10), outline=255, width=3)
        A.d['ink'].ellipse((x + 4, GROUND - 30, x + 24, GROUND - 10), outline=255, width=3)
    if ph < 2.5:
        flames(A, 160, GROUND, 200, 160, t, n=4, seed=3, smoke=True)
    qz(A, 980 - n * 60 - 40, GROUND, 160, dir=-1, ph=t * 3, arm=60)
    A.flush(cv)
    stops = [(0, '青州 · 故居十余屋 尽毁于兵火'), (2, '江宁'), (3.5, '洪州 · 书画尽失'), (5, '越州 · 被盗五簏'), (6.5, '所存 十去其九')]
    j = max(i for i, (b, _) in enumerate(stops) if ph >= b)
    fx = Art()
    chars_in(cv, fx, '金石南渡', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=97)
    fx.flush(cv)
    paste(cv, text_img(stops[j][1], SERIF, 44, BEGONIA if j < 4 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img(f'载书十五车 · 余 {n} 车', SERIF, 46, DAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    paste(cv, text_img('公元一一二七年起', SERIF, 40, DAI, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_q_wujiang(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=6, speed=1.6)
    ground(A, 1240, x0=60, x1=500)
    qz(A, 340, 1240, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    for i, ln in enumerate(('生当作人杰', '死亦为鬼雄', '至今思项羽', '不肯过江东')):
        type_in(cv, text_img(ln, SERIF, 40, BEGONIA if i == 3 else INK, 'Black', bleed=False, vertical=True, spacing=4), 900 - i * 62, 960, t, t - u + 0.3 + i * 0.4 * P, 0.4)

def art_q_zhao_dies(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zhao(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    qz(A, 860, GROUND, 200, dir=-1, kneel=True, bow=40, arm=100)
    lamp(A, 200, GROUND, 50, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('建康', 54, INK), 300, 880, t, t - u + P, rot=-5)

def art_q_flee(A, cv, t, u):
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    river(A, 1260, t, rows=2, amp=5, speed=1.6)
    x = lerp(200, 800, ease_out(u / (3 * P)))
    boat(A, x, 1290, 100, t, sail=True)
    qz(A, x, 1260, 120, dir=1, arm=40, old=0.2)
    A.flush(cv)
    paste(cv, text_img('追随帝踪 · 颠沛流离', SERIF, 46, DAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_q_stolen(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['mid'].rectangle((200, 1000, 560, GROUND), fill=200)
    A.d['wash'].rectangle((300, 1100, 460, GROUND), fill=255)
    ground(A, GROUND)
    for k in range(2):
        person(A, lerp(380, 1000, ease_out(u / (2 * P))) + k * 70, GROUND, 150, dir=1, robe=False, hat='knot', load=True, ph=t * 8 + k, arm=160, layer='ink')
    A.flush(cv)
    stamp(cv, seal('越州', 54, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('一夜被盗五簏', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第四回 晚年飘零
def art_q_second(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    qz(A, 360, GROUND, 220, dir=1, arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), old=0.3)
    person(A, 720, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 150, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('张汝舟', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('觊觎所余文物 婚后屡施拳脚', SERIF, 42, DAI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_q_court(A, cv, t, u):
    """6-beat: 告夫 — she reports his fraud to the court knowing the law will jail her too; the verdict; nine days later released."""
    ph = u / P
    palace(A, 540, 1140, 560, layer='dai')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 220, dir=1, robe=True, hat='crown', arm=lerp(20, 130, ease_out((ph - 2) / 0.6)), layer='ink')
    qz(A, 300, GROUND, 200, dir=1, kneel=True, bow=20, arm=100, old=0.3)
    person(A, 800, GROUND, 200, dir=-1, robe=True, hat='none', kneel=ph > 2.5, bow=40 if ph > 2.5 else 0, arm=60, layer='mid')
    A.flush(cv)
    if ph >= 1:
        paste(cv, text_img('宁可坐牢 也要离婚', SERIF, 50, BEGONIA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 1) / 0.3))
    if ph >= 3.5:
        paste(cv, text_img('入狱九日 · 友人营救获释', SERIF, 44, DAI, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3.5) / 0.3))

def art_q_jinhua(A, cv, t, u):
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=26)
    boat(A, 760, 1330, 70, t, sail=False)
    ground(A, GROUND)
    qz(A, 360, GROUND, 210, dir=1, arm=-8, old=0.5)
    A.flush(cv)
    type_in(cv, text_img('只恐双溪舴艋舟 载不动许多愁', SERIF, 40, DAI, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.6)

def art_q_houxu(A, cv, t, u):
    """6-beat: 金石录后序 — by lamplight the old woman edits his manuscript; the last surviving pieces sit beside her."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 560, GROUND, 400, layer='dai')
    qz(A, 300, GROUND, 210, dir=1, kneel=True, bow=25, arm=90, old=0.7)
    lamp(A, 800, GROUND - 70, 50, t, glow=0.8)
    n = int(clamp(ph / 4) * 30)
    for k in range(n):
        A.d['wash'].rectangle((400 + (k % 10) * 26, GROUND - 90 - (k // 10) * 8, 420 + (k % 10) * 26, GROUND - 84 - (k // 10) * 8), fill=255)
    bronze(A, 920, GROUND, 40, kind=1)
    A.flush(cv)
    ink_in(cv, text_img('金石录后序', SERIF, 50, DAI, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, dur=0.3)
    if ph >= 3:
        paste(cv, text_img('一份清单 一段婚姻 一个时代', SERIF, 42, BEGONIA, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 3) / 0.4))

def art_q_present(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, ease_out(u / P)), layer='ink')
    qz(A, 360, GROUND, 190, dir=1, kneel=True, bow=30, arm=100, old=0.7)
    scroll(A, 540, GROUND - 120, 160, 50, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('表上金石录', 40), 260, 880, t, t - u + P, rot=-5)

def art_q_cizhuan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='begonia')
    qz(A, 300, GROUND, 200, dir=1, kneel=True, bow=20, arm=90, old=0.5)
    A.flush(cv)
    ink_in(cv, text_img('词别是一家', BRUSH, 100, BEGONIA), W / 2, 960, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('词论 · 点评北宋名家', SERIF, 44, DAI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 寻寻觅觅
def art_q_shengsheng(A, cv, t, u):
    """6-beat: 声声慢 — autumn dusk; wild geese pass; rain on the 梧桐; the fourteen reduplicated characters fall one pair at a time."""
    ph = u / P
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        x = 80 + (k * 19) % 920
        A.d['wash'].line((x, lerp(620, 1420, q), x - 4, lerp(620, 1420, q) + 18), fill=170, width=2)
    A.d['ink'].line((820, GROUND, 840, 900), fill=255, width=20)
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.5
        A.d['ink'].line((840, 960, 840 + 160 * math.cos(a), 960 + 100 * math.sin(a)), fill=255, width=6)
    for k in range(5):
        crow(A, 200 + k * 70 + 30 * ((t * 0.4) % 1), 760 + abs(k - 2) * 26, 26, t * 5 + k)
    qz(A, 400, GROUND, 220, dir=1, old=0.8, arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    pairs = ['寻寻', '觅觅', '冷冷', '清清', '凄凄', '惨惨', '戚戚']
    n = min(7, int(ph / 0.75) + 1)
    for i in range(n):
        type_in(cv, text_img(pairs[i], SERIF, 46, BEGONIA if i >= 4 else INK, 'Black', bleed=False, vertical=True, spacing=4), 620 - i * 62, 920, t, t - u + i * 0.75 * P, 0.3)

def art_q_alone(A, cv, t, u):
    A.d['dai'].rectangle((200, 900, 880, GROUND), fill=150)
    A.d['wash'].rectangle((600, 960, 800, 1160), fill=255)
    for k in range(4):
        A.d['ink'].line((600 + k * 66, 960, 600 + k * 66, 1160), fill=180, width=3)
    lamp(A, 400, GROUND, 50, t, glow=0.4)
    qz(A, 500, GROUND, 200, dir=1, old=1.0, kneel=True, bow=20, arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('晚年无子 · 孤独终老', SERIF, 48, DAI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_disciple(A, cv, t, u):
    ground(A, GROUND)
    qz(A, 360, GROUND, 210, dir=1, old=1.0, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
    person(A, 700, GROUND, 150, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('孙氏女', 50), 860, 880, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('才藻非女子事也', SERIF, 48, DAI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_q_unknown(A, cv, t, u):
    for k in range(40):
        q = (t * 0.2 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 30, lerp(1300, 700, q) - 8, x + 30, lerp(1300, 700, q) + 8), fill=int(140 * math.sin(math.pi * q)))
    chrysanthemum(A, 540, 1100, 60, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒年不详 · 约七十余岁', SERIF, 48, DAI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_q_shuyu(A, cv, t, u):
    ground(A, GROUND)
    for i in range(int(clamp(u / (2 * P)) * 3) + 1):
        bundle(A, 380 + i * 160, GROUND - 40, 120, layer='begonia')
    A.flush(cv)
    ink_in(cv, text_img('漱玉词', BRUSH, 120, BEGONIA), W / 2, 920, t, t - u + 0.5, dur=0.3, settle=1.2)

def art_q_queen(A, cv, t, u):
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.2
        A.d['begonia'].ellipse((540 + 260 * math.cos(a) - 20, 1060 + 160 * math.sin(a) - 20, 540 + 260 * math.cos(a) + 20, 1060 + 160 * math.sin(a) + 20), fill=220)
    qz(A, 540, 1260, 260, dir=1, arm=40)
    ground(A, 1260)
    A.flush(cv)
    paste(cv, text_img('千古第一才女', SERIF, 52, BEGONIA, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_q_legacy(A, cv, t, u):
    chrysanthemum(A, 540, 1100, 110, t)
    ground(A, GROUND)

def art_q_title(A, cv, t, u):
    begonia_branch(A, 640, 1200, 420, t, bloom=1.0, leaves=0.2)
    qz(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '少女词名'), 48: ('第二回', '赌书泼茶'), 80: ('第三回', '金石南渡'),
            112: ('第四回', '晚年飘零'), 144: ('第五回', '寻寻觅觅')}

CARDS = [
    C(0, 2, 'works', 'num', num='千古第一才女', line='宋词婉约之宗', art=art_q_hook_queen),
    C(2, 4, 'war', 'num', num='十五车', line='金石南渡 十去其九', art=art_q_hook_carts),
    C(4, 6, 'fate', 'num', num='人比黄花瘦', line='一句惊倒满朝文人', art=art_q_hook_thin),
    C(6, 8, 'night', 'num', num='宁愿坐牢', line='也要离婚', art=art_q_hook_divorce),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少女词名
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1084, main='生于济南', sub='号易安居士', art=art_q_jinan),
    C(22, 26, 'works', 'card', year=1090, main='书香门第', sub='父亲李格非 · 苏轼门生', art=art_q_father),
    C(26, 32, 'life', 'card', year=1100, main='争渡', sub='如梦令', note='作年不详', art=art_q_zhengdu),
    C(32, 36, 'night', 'card', year=1100, main='绿肥红瘦', sub='昨夜雨疏风骤', art=art_q_haitang),
    C(36, 40, 'court', 'card', year=1100, main='词名满京', sub='少女之作 · 传遍汴京', art=art_q_fame),
    C(40, 44, 'empire', 'card', year=1101, main='嫁赵明诚', sub='太学生 · 金石同好', art=art_q_marry),
    C(44, 46, 'life', 'card', year=1101, main='典衣买碑', sub='每朔望谒告出 质衣取钱', art=art_q_pawn),
    C(46, 48, 'death', 'card', year=1103, main='党争牵连', sub='被迫与夫分离', art=art_q_parted),
    # ---- 第二回 赌书泼茶
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'life', 'card', year=1107, main='屏居青州', sub='远离朝堂 · 夫妇相守', art=art_q_qingzhou),
    C(54, 62, 'works', 'card', year=1110, main='赌书泼茶', sub='比谁记得某事在某页', note='金石录后序 所记', art=art_q_tea),
    C(62, 66, 'empire', 'card', year=1115, main='金石满屋', sub='倾尽家财 · 收集古物', art=art_q_collect),
    C(66, 70, 'works', 'card', year=1117, main='金石录', sub='夫妇合力编撰', art=art_q_jinshilu),
    C(70, 74, 'fate', 'card', year=1120, main='醉花阴', sub='重阳寄夫', art=art_q_chongyang),
    C(74, 78, 'court', 'card', year=1121, main='五十首', sub='赵明诚欲胜之', art=art_q_fifty),
    C(78, 80, 'life', 'card', year=1121, main='赴莱州', sub='随夫赴任', art=art_q_laixiang),
    # ---- 第三回 金石南渡
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=1127, main='靖康之变', sub='金兵攻破汴京 · 北宋亡', art=art_q_jingkang),
    C(86, 94, 'war', 'southward', year=1127),
    C(94, 98, 'night', 'card', year=1129, main='夏日绝句', sub='过乌江 · 讽南宋苟安', art=art_q_wujiang),
    C(98, 102, 'death', 'card', year=1129, main='明诚病逝', sub='建康途中 · 染疾而亡', art=art_q_zhao_dies),
    C(102, 106, 'fate', 'card', year=1130, main='孤身追驾', sub='带着残存文物 · 一路逃难', art=art_q_flee),
    C(106, 112, 'night', 'card', year=1131, main='越州失盗', sub='卧榻之下 · 尽被窃去', art=art_q_stolen),
    # ---- 第四回 晚年飘零
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'night', 'card', year=1132, main='再嫁', sub='病中误嫁张汝舟', note='一说 再嫁之事存疑', art=art_q_second),
    C(118, 124, 'court', 'card', year=1132, main='告夫离婚', sub='告发其妄增举数', note='宋律 妻告夫 虽实亦徒二年', art=art_q_court),
    C(124, 128, 'life', 'card', year=1134, main='避难金华', sub='物是人非事事休', art=art_q_jinhua),
    C(128, 134, 'works', 'card', year=1134, main='金石录后序', sub='为亡夫遗作写后记', art=art_q_houxu),
    C(134, 138, 'empire', 'card', year=1150, main='表上金石录', sub='献书朝廷', note='一说', art=art_q_present),
    C(138, 144, 'works', 'card', year=1150, main='词别是一家', sub='她的词论', note='作年不详', art=art_q_cizhuan),
    # ---- 第五回 寻寻觅觅
    C(144, 146, 'night', 'chapter'),
    C(146, 152, 'night', 'card', year=1150, main='声声慢', sub='乍暖还寒时候 最难将息', note='作年不详', art=art_q_shengsheng),
    C(152, 156, 'death', 'card', year=1152, main='独居临安', sub='暮年孤苦', art=art_q_alone),
    C(156, 160, 'life', 'card', year=1153, main='欲传其学', sub='孙氏女辞谢', note='陆游所记', art=art_q_disciple),
    C(160, 164, 'death', 'card', year=1155, main='不知所终', sub='卒年不详', art=art_q_unknown),
    C(164, 168, 'works', 'card', year=1200, main='漱玉词', sub='后人辑录 · 存词四十余首', art=art_q_shuyu),
    C(168, 170, 'end', 'card', year=2026, main='才女', sub='千年一人', art=art_q_queen),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾肆', col=BEGONIA, acc=DAI, born=1084, died=1155,
    born_lab='1084年', died_lab='约1155年',
    hook_q='千古第一才女 · 晚年为何孤苦无依？',
    name_line='李清照 · 号易安居士', name='李清照', seal='易安', title_art=art_q_title,
    q1='一代词宗？', q2='红颜薄命？',
    end_art=art_q_legacy, end_big='人比黄花瘦', end_seal='易安',
    end_l1='她失去了丈夫 家园和收藏', end_l2='却留下了宋词最美的句子',
    end_brush='寻寻觅觅', end_ask='你最喜欢她哪一首？评论区聊聊', next='辛弃疾'),
    scenes=dict(chapter=scene_chapter, southward=scene_southward))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
