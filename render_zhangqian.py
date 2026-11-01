"""千古人物志 · 第贰拾伍集 · 张骞 (约前164–前114)
Look: 沙丘金 + 绿松石, 驼铃 corner borders, dunes with a far caravan; a 汉节 chapter card: the staff's yak-tail tufts
thin out through the captive years and are renewed for the second mission.
Set pieces: 8-beat 匈奴十年 (seasons turn; wife, child; the staff kept), custom 8-beat scene 'route'
(万里西行 map with year counter), 6-beat 再被扣留, 6-beat 归来二人, 8-beat 再使乌孙 caravan.
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_hanxin as Hx          # engine + helpers (previous episode)
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
from render_wudi import camel
from render_quyuan import river

F.RIPPLE = False
DUNE = (176, 124, 58)               # 沙丘金
TURQ = (34, 146, 146)               # 绿松石
S.LAYERS.append(('dune', DUNE, 0.85, 1.4))
S.LAYERS.append(('turq2', TURQ, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='骞', life='汉', court='汉', night='囚', war='胡', empire='汉', works='西', fate='节', death='归', end='路')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'empire', 'court'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = (DUNE, 240, (W * 0.5, 800))
G.THEMES['empire']['sun'] = (DUNE, 230, (W * 0.5, 820))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (TURQ, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

DUNES = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(DUNES)
_pts = [(x, 1440 - 40 * math.sin(x / 130) - 20 * math.sin(x / 47)) for x in range(60, W - 59, 10)]
_d.polygon(_pts + [(W - 60, 1500), (60, 1500)], fill=DUNE + (40,))
for _k in range(5):
    _x = 640 + _k * 46
    _d.ellipse((_x - 14, 1338, _x + 14, 1352), fill=(90, 70, 50, 46))
    _d.line((_x + 10, 1342, _x + 18, 1330), fill=(90, 70, 50, 46), width=3)
    _d.line((_x - 8, 1350, _x - 8, 1366), fill=(90, 70, 50, 46), width=2); _d.line((_x + 6, 1350, _x + 6, 1366), fill=(90, 70, 50, 46), width=2)
MTN_COL = {'night': (40, 38, 40), 'death': (62, 60, 58), 'war': (104, 70, 44), 'works': (130, 100, 60), 'fate': (90, 80, 70)}
def draw_background(t, theme):
    """大漠: low dune ridges and a tiny camel train on the horizon."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(206, 188, 160), (180, 150, 110), MTN_COL.get(theme, (140, 108, 70))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(DUNES)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """驼铃: a hanging camel bell on a cord in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = DUNE + (230,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 170, y), fill=col, width=4); d.line((x, y, x, y + sy * 170), fill=col, width=4)
        bx, by = x + sx * 60, y + sy * 18
        d.line((bx, by, bx, by + sy * 34), fill=col, width=3)
        cy = by + sy * 34
        d.polygon([(bx - 12, cy), (bx + 12, cy), (bx + 18, cy + sy * 30), (bx - 18, cy + sy * 30)], fill=TURQ + (230,))
        d.ellipse((bx - 4, cy + sy * 30 - 4, bx + 4, cy + sy * 30 + 4), fill=col)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def qian(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, jie=True, tufts=3, **kw):
    """张骞: travelling robe, fur-rimmed hat, holding the 汉节 (staff with red yak-tail tufts)."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
        d.rectangle((x - 0.09 * h, y - 0.98 * h, x + 0.09 * h, y - 0.95 * h), fill=255)
    if jie:
        hx, hy = hand
        jie_staff(A, hx, hy + 0.3 * h, 1.15 * h, tufts, layer=layer)
    return hand

def jie_staff(A, x, base, h, tufts, layer='ink', t=0.0):
    A.d[layer].line((x, base, x, base - h), fill=255, width=max(3, int(0.022 * h)))
    for k in range(3):
        ty = base - h + 0.06 * h + k * 0.13 * h
        A.d[layer].ellipse((x - 0.025 * h, ty - 0.012 * h, x + 0.025 * h, ty + 0.012 * h), fill=255)
        if k < tufts:
            sw = 0.02 * h * math.sin(t * 3 + k)
            A.d['red'].polygon([(x - 0.03 * h, ty), (x + 0.03 * h, ty), (x + 0.045 * h + sw, ty + 0.11 * h), (x - 0.045 * h + sw, ty + 0.11 * h)], fill=255)

def yurt(A, x, base, w, h, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - 0.55 * h, x + w / 2, base), fill=230)
    A.d[layer].chord((x - w / 2, base - 1.1 * h, x + w / 2, base), 180, 360, fill=230)
    A.d['ink'].rectangle((x - 0.1 * w, base - 0.4 * h, x + 0.1 * w, base), fill=255)
    for k in range(4):
        A.d['ink'].line((x - w / 2 + k * w / 3, base - 0.55 * h, x - w / 2 + k * w / 3 + 10, base), fill=90, width=3)

def grapes(A, x, y, s, layer='turq2'):
    for r in range(4):
        for c in range(4 - r):
            gx = x + (c - (3 - r) / 2) * 0.24 * s; gy = y + r * 0.22 * s
            A.d[layer].ellipse((gx - 0.12 * s, gy - 0.12 * s, gx + 0.12 * s, gy + 0.12 * s), fill=255)
    A.d['ink'].line((x, y - 0.15 * s, x + 0.1 * s, y - 0.4 * s), fill=255, width=4)
    leaf(A, 'grass', x + 0.1 * s, y - 0.3 * s, -0.4, 0.5 * s, 0.14 * s)

def sheep(A, x, y, s, layer='mid'):
    A.d[layer].ellipse((x - 0.5 * s, y - 0.7 * s, x + 0.5 * s, y - 0.25 * s), fill=230)
    A.d[layer].ellipse((x + 0.4 * s, y - 0.75 * s, x + 0.65 * s, y - 0.5 * s), fill=230)
    for lx in (-0.3, 0.3):
        A.d[layer].line((x + lx * s, y - 0.3 * s, x + lx * s, y), fill=230, width=max(2, int(0.08 * s)))

# ================================================================ chapter card
CH = {16: 3, 48: 1, 80: 0, 112: 3, 144: 3}
def art_jie_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    tf = CH.get(kb, 2)
    q = ease_out(u / 0.6)
    jie_staff(A, 540, 1240, 520 * q + 10, tf, layer='ink', t=t)
    if kb == 144:
        A.d['dune'].polygon([(380, 1240), (540, 1200), (700, 1240)], fill=255)
    for k in range(3):
        y = 1260 + k * 30
        x = (t * 60 * (1 + 0.4 * k) + k * 300) % (W + 400) - 200
        A.d['dune'].line((x, y, x + 260, y), fill=160, width=10)
    ground(A, 1240)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_jie_chapter)
    ink_in(cv, text_img(no, SERIF, 56, DUNE, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_13(A, cv, t, u):
    ground(A, GROUND)
    n = max(2, 100 - int(clamp(u / (1.6 * P)) * 98))
    for i in range(100):
        x = 120 + (i % 20) * 44; y = GROUND - 40 - (i // 20) * 44
        if i < n or i in (0, 1):
            A.d['ink' if i in (0, 1) else 'mid'].ellipse((x - 12, y - 12, x + 12, y + 12), fill=255)

def art_q_hook_staff(A, cv, t, u):
    yurt(A, 760, GROUND, 300, 260, layer='mid')
    ground(A, GROUND)
    for k in range(40):
        q = (t * 0.5 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    qian(A, 380, GROUND, 280, dir=1, tufts=1, arm=60)

def art_q_hook_drill(A, cv, t, u):
    p = ease_out(u / (1.6 * P))
    A.d['mid'].rectangle((60, 860, W - 60, 1300), fill=200)
    A.d['wash'].polygon([(60, 1080 - 40 * p), (60 + (W - 120) * p, 1060), (60 + (W - 120) * p, 1100), (60, 1080 + 40 * p)], fill=255)
    camel(A, 60 + (W - 120) * p - 60, 1100, 80, 1, t * 5, layer='ink')

def art_q_hook_silk(A, cv, t, u):
    p = ease_out(u / (1.6 * P))
    pts = [(lerp(980, 100, f), 1100 + 120 * math.sin(f * 6)) for f in np.linspace(0, p, 30)]
    if len(pts) > 1:
        A.d['turq2'].line(pts, fill=230, width=22)
        A.d['wash'].line(pts, fill=200, width=6)
    qian(A, 980, 1300, 220, dir=-1, tufts=3, arm=60)
    ground(A, 1300, x0=820, x1=W - 60)

# ================================================================ 第一回 应募出使
def art_q_hometown(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 300 - 60 * (k % 2)), (x + 200, GROUND)], fill=170)
    A.d['ocean'].line([(60, 1340), (500, 1300), (1020, 1330)], fill=150, width=24)
    ground(A, GROUND)
    person(A, 540, GROUND, 180, dir=1, robe=False, hat='knot', arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('城固', 56), 860, 880, t, t - u + P, rot=6)

def art_q_lang(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    for k in range(2):
        person(A, 300 + k * 480, GROUND, 190, dir=1 if k == 0 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('郎', 60), 860, 880, t, t - u + P, rot=6)

def art_q_volunteer(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 220, dir=1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.5)), layer='ink')
    scroll(A, 540, 900, 300, 100, u / 0.6, layer='yellow')
    x = lerp(100, 330, ease_out((u - P) / P))
    qian(A, x, GROUND, 220, dir=1, jie=False, kneel=u > 2.2 * P, bow=40 if u > 2.2 * P else 0, arm=90)
    A.flush(cv)
    if u > 0.6:
        ink_in(cv, text_img('募能使者', SERIF, 44, INK, 'Black', bleed=False, spacing=6), 540, 900, t, t - u + 0.6, dur=0.3)

def art_q_ganfu(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.2 * P))
    person(A, 640, GROUND, 230, dir=-1, robe=False, hat='helmet', arm=lerp(40, 150, p), arm2=lerp(-20, -60, p), layer='ink')
    A.d['ink'].arc((520, 900, 640, 1100), 100, 260, fill=255, width=6)
    for k in range(int(clamp((u - P) / P) * 3)):
        crow(A, 300 - k * 60, 820 + k * 40, 30, t * 6 + k)
    qian(A, 300, GROUND, 220, dir=1, tufts=3, arm=60)
    A.flush(cv)
    stamp(cv, seal('甘父', 54), 860, 880, t, t - u + 0.4, rot=6)

def art_q_depart(A, cv, t, u):
    city_wall(A, 60, 420, 1140, gate_x=240, label='陇西', layer='mid', open_=1.0)
    ground(A, GROUND)
    n = min(14, int(clamp(u / (2.5 * P)) * 14) + 1)
    for k in range(n):
        x = lerp(240, 980 - k * 52, ease_out((u - k * 0.1) / (3 * P)))
        if k == 0:
            qian(A, x, GROUND, 170, dir=1, tufts=3, ph=t * 4, arm=60)
        elif k % 4 == 0:
            camel(A, x, GROUND, 80, 1, t * 5 + k, layer='ink')
        else:
            person(A, x, GROUND, 110, dir=1, robe=False, hat='knot', ph=t * 5 + k, arm=20, layer='mid')
    A.flush(cv)
    paste(cv, text_img('一百余人', SERIF, 52, DUNE, 'Black', bleed=False, spacing=8), W / 2, 880, 1, clamp((u - P) / 0.3))

def art_q_captive(A, cv, t, u):
    """8-beat set piece: 匈奴十年 — the seasons cycle (snow / grass) over a yurt; a wife appears, then a child;
    tufts wear off the staff, but he never lets it go; the year counter climbs to 十."""
    ph = u / P
    yr = min(10, int(ph * 10 / 7.5) + 1)
    season = (ph * 2) % 2
    yurt(A, 700, GROUND, 340, 280)
    ground(A, GROUND)
    if season < 1:
        for k in range(50):
            q = (t * 0.5 + k / 50) % 1
            x = 80 + (k * 19) % 920
            A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    else:
        for k in range(14):
            x = 100 + k * 66
            A.d['grass'].polygon([(x - 20, GROUND), (x, GROUND - 40 - 10 * (k % 3)), (x + 20, GROUND)], fill=200)
        for k in range(3):
            sheep(A, 160 + k * 90 + 10 * math.sin(t + k), GROUND, 60)
    tufts = 3 if yr < 4 else (2 if yr < 7 else 1)
    qian(A, 360, GROUND, 250, dir=1, tufts=tufts, arm=60)
    if ph >= 2:
        person(A, 520, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, arm=20, layer='mid')
    if ph >= 4:
        person(A, 460, GROUND, 90, dir=-1, robe=False, hat='knot', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    for k in range(2):
        rider(A, 880 + k * 70, GROUND, 100, -1, t * 3 + k, layer='ink', spear=True, moving=False)
    A.flush(cv)
    paste(cv, text_img(f'被扣第{cn_num(yr)}年', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph >= 6:
        type_in(cv, text_img('持汉节不失', SERIF, 48, DUNE, 'Black', bleed=False, spacing=8), W / 2, 1448, t, t - u + 6 * P, 0.5)

def art_q_slip_away(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['wash'].ellipse((160, 680, 240, 760), fill=255)
    yurt(A, 220, GROUND, 260, 220)
    ground(A, GROUND)
    x = lerp(300, 1000, ease_out(u / (2 * P)))
    qian(A, x, GROUND, 180, dir=1, tufts=1, ph=t * 6, arm=60)
    person(A, x - 120, GROUND, 170, dir=1, robe=False, hat='helmet', ph=t * 6 + 1, arm=30, layer='ink')

# ================================================================ 第二回 西域见闻
ROUTE = [('长安', 920, 1240, -139), ('陇西', 820, 1180, -139), ('匈奴', 700, 860, -139), ('大宛', 420, 980, -129),
         ('康居', 300, 860, -128), ('大月氏', 250, 1100, -128), ('大夏', 330, 1250, -128), ('羌中', 640, 1300, -127), ('长安', 920, 1240, -126)]
def scene_route(cv, t, c, k):
    """8-beat custom scene: 万里西行 — a parchment map; each beat the route reaches the next stop; the year counter runs
    from 前139 to 前126; captive legs are drawn dashed."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['dune'].rounded_rectangle((100, 760, 980, 1420), radius=26, fill=120)
    for k2 in range(5):
        x = 150 + k2 * 180
        A.d['mid'].polygon([(x - 60, 1000 + (k2 % 2) * 120), (x, 940 + (k2 % 2) * 120), (x + 60, 1000 + (k2 % 2) * 120)], fill=200)
    stops = min(len(ROUTE), int(ph) + 2)
    for i in range(1, stops):
        (_, x0, y0, _), (_, x1, y1, _) = ROUTE[i - 1], ROUTE[i]
        f = clamp(ph - (i - 1)) if i == stops - 1 else 1
        ex, ey = lerp(x0, x1, f), lerp(y0, y1, f)
        dashed = ROUTE[i][0] in ('匈奴', '羌中')
        if dashed:
            for g in range(8):
                a, b = g / 8, (g + 0.5) / 8
                if a < f:
                    A.d['red'].line((lerp(x0, x1, a), lerp(y0, y1, a), lerp(x0, x1, min(b, f)), lerp(y0, y1, min(b, f))), fill=255, width=7)
        else:
            A.d['turq2'].line((x0, y0, ex, ey), fill=255, width=8)
        if i == stops - 1:
            camel(A, ex, ey + 20, 50, 1 if x1 > x0 else -1, t * 6, layer='ink')
    A.flush(cv)
    for i in range(stops):
        nm, x, y, yr = ROUTE[i]
        if i == len(ROUTE) - 1 and stops < len(ROUTE): continue
        stamp(cv, seal(nm, 34, ZHU if nm in ('长安', '匈奴') else DUNE), x, y - 46, t, s0 + max(0, i - 1) * P + 0.2)
    yr = int(round(lerp(-139, -126, clamp(ph / 7.6))))
    fx = Art()
    chars_in(cv, fx, '万里西行', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=50)
    fx.flush(cv)
    paste(cv, text_img(f'公元前{cn_num(-yr)}年', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('出发百余人 · 往返十三年', SERIF, 44, DUNE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6) / 0.4))

def art_q_dayuan(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(1100, 560, ease_out(u / (1.5 * P)))
    horse(A, x, GROUND, 230, dir=-1, ph=t * 8, moving=u < 1.5 * P, layer='ink')
    for k in range(3):
        q = (t * 0.6 + k / 3) % 1
        A.d['red'].ellipse((x + 40 + 60 * q, GROUND - 180 + 30 * q, x + 54 + 60 * q, GROUND - 166 + 30 * q), fill=int(220 * (1 - q)))
    grapes(A, 220, 940, 140)
    A.flush(cv)
    stamp(cv, seal('汗血马', 48), 860, 880, t, t - u + P, rot=6)

def art_q_kangju(A, cv, t, u):
    ground(A, GROUND)
    yurt(A, 760, GROUND, 320, 280, layer='turq2')
    person(A, 640, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out((u - P) / 0.5)), layer='ink')
    qian(A, 360, GROUND, 230, dir=1, tufts=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('康居', 56), 300, 880, t, t - u + 0.4, rot=-5)

def art_q_yuezhi(A, cv, t, u):
    for k in range(10):
        x = 100 + k * 92
        A.d['grass'].rectangle((x, GROUND - 70 - 20 * (k % 3), x + 70, GROUND), fill=200)
    river(A, 1330, t, rows=2, amp=4)
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    A.d['red'].line((560, 1080, 620, 1140), fill=255, width=8); A.d['red'].line((620, 1080, 560, 1140), fill=255, width=8)
    qian(A, 340, GROUND, 230, dir=1, tufts=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('大月氏', 48), 860, 880, t, t - u + 0.4, rot=6)

def art_q_daxia(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((300, 1160, 780, GROUND), fill=200)
    for k in range(4):
        A.d['dune'].rectangle((330 + k * 110, 1100, 410 + k * 110, 1160), fill=230)
    A.d['ink'].line((420, 1000, 460, 1160), fill=255, width=10)
    for k in range(3):
        A.d['ink'].line((418 + k * 13, 1010 + k * 50, 432 + k * 13, 1010 + k * 50), fill=255, width=4)
    qian(A, 880, GROUND, 230, dir=-1, tufts=1, arm=lerp(30, 110, ease_out((u - P) / 0.5)))
    A.flush(cv)
    stamp(cv, seal('蜀布', 48), 300, 900, t, t - u + 0.5, rot=-5)
    stamp(cv, seal('邛竹杖', 44), 540, 900, t, t - u + P, rot=4)
    if u > 2 * P:
        paste(cv, text_img('从身毒国买来', SERIF, 46, TURQ, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_q_recaptured(A, cv, t, u):
    """6-beat: 再被扣留 — taking the 羌中 road home, riders close in again; a year passes in snow."""
    ph = u / P
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 400 - 80 * (k % 2)), (x + 160, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(100, 480, ease_out(ph / 2))
    qian(A, x, GROUND, 190, dir=1, tufts=1, ph=t * 4 if ph < 2 else None, arm=60)
    for k in range(6):
        side = -1 if k % 2 else 1
        rx = lerp(540 + side * 700, 540 + side * (140 + (k // 2) * 90), ease_out((ph - 1.5) / 1.5))
        rider(A, rx, GROUND, 110, -side, t * 10 + k, layer='ink', spear=True, moving=ph < 3)
    if ph >= 3.5:
        for k in range(40):
            q = (t * 0.5 + k / 40) % 1
            x2 = 80 + (k * 23) % 920
            A.d['wash'].ellipse((x2 - 4, lerp(620, 1420, q) - 4, x2 + 4, lerp(620, 1420, q) + 4), fill=220)
    A.flush(cv)
    stamp(cv, seal('羌中', 54), 860, 860, t, t - u + 0.4, rot=6)
    if ph >= 3.5:
        paste(cv, text_img('又被扣留一年多', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 3.5) / 0.3))

# ================================================================ 第三回 十三年归
def art_q_return_two(A, cv, t, u):
    """6-beat set piece: 归来 — two figures (and a wife) walk up to the 长安 gate; a ghost column of a hundred fades."""
    ph = u / P
    city_wall(A, 640, 1020, 1100, gate_x=830, label='长安', layer='mid', open_=ease_out((ph - 3.5) / 1))
    ground(A, GROUND)
    fade = 1 - clamp(ph / 3)
    for i in range(100):
        if fade <= 0: break
        x = 100 + (i % 20) * 26; y = 1240 - (i // 20) * 26
        A.d['mid'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=int(200 * fade))
    x = lerp(100, 600, ease_out(ph / 5))
    qian(A, x, GROUND, 200, dir=1, tufts=1, ph=t * 4, arm=60)
    person(A, x - 120, GROUND, 180, dir=1, robe=False, hat='helmet', ph=t * 4 + 1, arm=20, layer='ink')
    person(A, x - 220, GROUND, 170, dir=1, robe=True, hat='knot', female=True, ph=t * 4 + 2, arm=20, layer='mid')
    A.flush(cv)
    paste(cv, text_img('去时百余人' if ph < 3 else '归来仅二人', SERIF, 56, DUNE if ph < 3 else ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, 1)

def art_q_report(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    qian(A, 340, GROUND, 230, dir=1, tufts=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    for i, nm in enumerate(('大宛', '乌孙', '康居', '奄蔡', '大月氏', '安息', '条枝', '大夏')):
        if u > 0.3 + i * 0.25 * P:
            stamp(cv, seal(nm, 30, DUNE if i % 2 else TURQ), 190 + (i % 4) * 230, 830 + (i // 4) * 90, t, t - u + 0.3 + i * 0.25 * P)

def art_q_official(A, cv, t, u):
    ground(A, GROUND)
    A.d['yellow'].rectangle((360, 900, 720, 1000), fill=255)
    qian(A, 540, GROUND, 240, dir=1, tufts=3, kneel=True, bow=40, arm=90, jie=False)
    A.flush(cv)
    ink_in(cv, text_img('太中大夫', SERIF, 48, INK, 'Black', bleed=False, spacing=6), 540, 950, t, t - u + 0.5, dur=0.3)

def art_q_north(A, cv, t, u):
    for k in range(10):
        x = 100 + k * 92
        A.d['grass'].polygon([(x - 30, GROUND), (x, GROUND - 60 - 20 * (k % 3)), (x + 30, GROUND)], fill=180)
    A.d['ocean'].ellipse((700, 1300, 960, 1380), fill=150)
    ground(A, GROUND)
    x = lerp(-200, 500, ease_out(u / (2.5 * P)))
    for k in range(5):
        rider(A, x - k * 110, GROUND, 120, 1, t * 11 + k, layer='ink' if k else 'dune', spear=True, moving=u < 2.5 * P)
    A.flush(cv)
    stamp(cv, seal('卫青', 50, INK), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('水草', 50), 830, 1220, t, t - u + 1.6 * P, rot=6)

def art_q_bowang(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.5 * P))
    A.d['dune'].polygon([(540, GROUND), (540 - 360 * p, 900), (540 + 360 * p, 900)], fill=120)
    qian(A, 540, GROUND, 260, dir=1, tufts=3, arm=lerp(60, 160, p))
    A.flush(cv)
    stamp(cv, seal('博望侯', 54), 860, 880, t, t - u + 1.5 * P, rot=6)
    paste(cv, text_img('广博瞻望', SERIF, 50, DUNE, 'Black', bleed=False, spacing=10), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_q_southwest(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['grass'].polygon([(x - 130, GROUND), (x, GROUND - 440 - 80 * (k % 2)), (x + 130, GROUND)], fill=200)
    ground(A, GROUND)
    for i in range(4):
        x = lerp(80, 780, ease_out((u - i * 0.15) / (2.5 * P)))
        person(A, x - i * 60, GROUND, 110, dir=1, robe=False, hat='knot', ph=t * 5 + i, arm=20, layer='ink')
    A.d['red'].line((820, 1100, 920, GROUND - 20), fill=255, width=12); A.d['red'].line((920, 1100, 820, GROUND - 20), fill=255, width=12)
    A.flush(cv)
    stamp(cv, seal('昆明', 54, INK), 870, 900, t, t - u + 2 * P, rot=6)

def art_q_late(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        rider(A, 600 + k * 70, GROUND, 100, -1, t * 3 + k, layer='mid', spear=True, moving=False)
    qian(A, 300, GROUND, 230, dir=1, tufts=3, kneel=True, bow=40, arm=90, jie=False)
    sun(cv, 860, lerp(900, 1200, ease_out(u / (2 * P))), 70, ZHU, 150)
    A.flush(cv)
    stamp(cv, seal('失期', 56, INK), 860, 880, t, t - u + 0.6, rot=6)
    paste(cv, text_img('赎为庶人', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - 1.6 * P) / 0.3))

# ================================================================ 第四回 再使乌孙
def art_q_wusun_caravan(A, cv, t, u):
    """8-beat set piece: 再使乌孙 — a long caravan: banners, three hundred men, ten thousand head of cattle and sheep,
    gold and silk; counters climb as it passes."""
    ph = u / P
    ground(A, GROUND)
    off = t * 90
    for k in range(18):
        x = (k * 110 - off) % (W + 400) - 200
        kind = k % 6
        if kind == 0:
            camel(A, x, GROUND, 90, -1, t * 6 + k, layer='ink')
        elif kind == 3:
            rider(A, x, GROUND, 100, -1, t * 9 + k, layer='ink')
        else:
            sheep(A, x, GROUND, 50 + 6 * (k % 2), layer='mid')
    qian(A, 760, 1200, 170, dir=-1, tufts=3, arm=60)
    A.d['dune'].rectangle((660, 1200, 860, 1214), fill=220)
    A.flush(cv)
    men = min(300, int(lerp(10, 300, clamp(ph / 3))))
    heads = min(10000, int(lerp(0, 10000, clamp((ph - 2) / 4))))
    paste(cv, text_img(f'随员 {men} 人', SERIF, 46, DUNE, 'Black', bleed=False, spacing=4), 320, 830, 1, 1)
    paste(cv, text_img(f'牛羊 {heads} 头', SERIF, 46, TURQ, 'Black', bleed=False, spacing=4), 760, 830, 1, clamp((ph - 2) / 0.3))
    if ph >= 6:
        paste(cv, text_img('金币丝帛 数以千巨万', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6) / 0.3))

def art_q_envoys(A, cv, t, u):
    cx, cy = 540, 1300
    names = ['大宛', '康居', '大月氏', '大夏', '安息', '身毒']
    for i, nm in enumerate(names):
        a = math.pi + (i + 0.5) * math.pi / 6
        p = ease_out((u - i * 0.2 * P) / P)
        ex, ey = cx + 440 * math.cos(a) * p, cy + 440 * math.sin(a) * p
        A.d['turq2'].line((cx, cy, ex, ey), fill=220, width=6)
        if p > 0.2: camel(A, ex, ey + 20, 40, 1 if math.cos(a) > 0 else -1, t * 6 + i, layer='ink')
    yurt(A, cx, cy + 60, 160, 120, layer='turq2')
    A.flush(cv)
    for i, nm in enumerate(names):
        a = math.pi + (i + 0.5) * math.pi / 6
        if u > i * 0.2 * P + P:
            stamp(cv, seal(nm, 30, DUNE), cx + 470 * math.cos(a), cy + 470 * math.sin(a) - 50, t, t - u + i * 0.2 * P + P)

def art_q_wusun_hesitate(A, cv, t, u):
    yurt(A, 700, GROUND, 340, 280, layer='turq2')
    ground(A, GROUND)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='crown', bow=lerp(0, 20, 0.5 + 0.5 * math.sin(t * 1.5)), arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    qian(A, 330, GROUND, 230, dir=1, tufts=3, arm=lerp(50, 110, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('乌孙王', 48, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('汉之大小 未可知', SERIF, 46, DUNE, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_q_wusun_envoy(A, cv, t, u):
    city_wall(A, 600, 1020, 1080, gate_x=810, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(4):
        x = lerp(-100, 560 - k * 110, ease_out((u - k * 0.1) / (2.5 * P)))
        if k == 0:
            qian(A, x, GROUND, 180, dir=1, tufts=3, ph=t * 4, arm=60)
        else:
            horse(A, x, GROUND, 110, dir=1, ph=t * 7 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('乌孙使者', 44), 300, 880, t, t - u + P, rot=-5)

def art_q_daxing(A, cv, t, u):
    palace(A, 540, 1140, 540, layer='mid')
    ground(A, GROUND)
    for k in range(4):
        x = 180 + k * 80 if k < 2 else 760 + (k - 2) * 90
        person(A, x, GROUND, 140, dir=1 if x < 540 else -1, robe=True, hat='knot', kneel=True, bow=40, arm=90, layer='mid')
    qian(A, 540, GROUND, 230, dir=1, tufts=3, arm=40)
    A.flush(cv)
    stamp(cv, seal('大行', 56), 860, 880, t, t - u + P, rot=6)

def art_q_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    jie_staff(A, 860, GROUND, 460, 1, layer='ink', t=t)
    ground(A, GROUND)
    lamp(A, 200, GROUND, 50, t, glow=clamp(1 - (u - P) / 0.8))
    A.flush(cv)
    stamp(cv, seal('卒', 64, INK), 540, 960, t, t - u + 1.5 * P)

def art_q_envoys_return(A, cv, t, u):
    city_wall(A, 60, 420, 1100, gate_x=240, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(10):
        x = lerp(1100, 480 + (k % 5) * 110, ease_out((u - k * 0.1) / (2.5 * P)))
        y = GROUND - (k // 5) * 40
        if k % 2:
            camel(A, x, y, 90, -1, t * 6 + k, layer='ink')
        else:
            horse(A, x, y, 100, dir=-1, ph=t * 6 + k, layer='mid')
    A.flush(cv)
    paste(cv, text_img('西北诸国始通于汉', SERIF, 48, TURQ, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第五回 丝路长存
def art_q_horses(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        x = lerp(1100, 200 + k * 200, ease_out((u - k * 0.15) / (2 * P)))
        horse(A, x, GROUND - (k % 2) * 30, 150, dir=-1, ph=t * 9 + k, layer='ink' if k % 2 else 'dune')
    A.flush(cv)
    stamp(cv, seal('天马', 56), 860, 880, t, t - u + P, rot=6)

def art_q_grapes(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['ink'].line((200 + k * 300, GROUND, 200 + k * 300, 980), fill=255, width=8)
    A.d['ink'].line((180, 980, 820, 980), fill=255, width=6)
    for k in range(int(clamp(u / (2 * P)) * 6) + 1):
        grapes(A, 260 + k * 100, 1000, 80)
    for k in range(12):
        x = 140 + k * 70
        A.d['grass'].ellipse((x - 20, GROUND - 40, x + 20, GROUND), fill=220)
    A.flush(cv)
    stamp(cv, seal('一说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_q_zaokong(A, cv, t, u):
    A.d['mid'].rectangle((60, 860, W - 60, 1340), fill=210)
    p = ease_out(u / (2.5 * P))
    A.d['wash'].rectangle((60, 1060, 60 + (W - 120) * p, 1140), fill=255)
    for k in range(int(p * 12)):
        A.d['ink'].line((60 + k * 80, 1060, 60 + k * 80 + 20, 1140), fill=120, width=3)
    A.flush(cv)
    ink_in(cv, text_img('凿空', BRUSH, 150, ZHU), W / 2, 960, t, t - u + 1.5 * P, dur=0.3, settle=1.3)
    stamp(cv, seal('司马迁', 46, INK), 860, 1260, t, t - u + 0.4, rot=6)

def art_q_duhu(A, cv, t, u):
    city_wall(A, 220, 860, 1120, gate_x=540, label='乌垒', layer='dune', open_=0.0)
    ground(A, GROUND)
    flag(A, 540, 1120, 220, t, w=80, layer='red')
    for k in range(4):
        person(A, 300 + k * 160, GROUND, 130, dir=1 if k < 2 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('西域都护', 44), 860, 880, t, t - u + P, rot=6)

def art_q_name(A, cv, t, u):
    A.d['wash'].rectangle((240, 860, 840, 1280), fill=255)
    A.d['ink'].rectangle((240, 860, 840, 1280), outline=255, width=6)
    p = ease_out(u / (2 * P))
    pts = [(lerp(800, 280, f), 1070 + 80 * math.sin(f * 7)) for f in np.linspace(0, p, 30)]
    if len(pts) > 1: A.d['turq2'].line(pts, fill=255, width=10)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('Seidenstraße', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 920, 1, clamp((u - P) / 0.3))
    stamp(cv, seal('李希霍芬', 42, INK), 760, 1220, t, t - u + 1.5 * P, rot=6)

def art_q_heritage(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = (t * 70 + k * 190) % (W + 300) - 150
        camel(A, x, GROUND, 100, 1, t * 5 + k, layer='ink' if k % 2 else 'dune')
    p = ease_out(u / (1.5 * P))
    A.d['turq2'].ellipse((540 - 160 * p, 960 - 160 * p, 540 + 160 * p, 960 + 160 * p), outline=255, width=10)
    A.flush(cv)
    if p > 0.8:
        ink_in(cv, text_img('世界遗产', SERIF, 48, TURQ, 'Black', bleed=False, spacing=6), 540, 960, t, t - u + 1.5 * P, dur=0.3)

def art_q_legacy(A, cv, t, u):
    jie_staff(A, 540, 1300, 520, 3, layer='ink', t=t)
    ground(A, 1300)

def art_q_title(A, cv, t, u):
    for k in range(3):
        camel(A, 760 + k * 110, 1460, 110, 1, t * 4 + k, layer='mid')
    qian(A, 380, 1460, 640, dir=1, tufts=3, arm=lerp(30, 60, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '应募出使'), 48: ('第二回', '西域见闻'), 80: ('第三回', '十三年归'),
            112: ('第四回', '再使乌孙'), 144: ('第五回', '丝路长存')}

CARDS = [
    C(0, 2, 'works', 'num', num='十三年', line='去时百余人 回来两个', art=art_q_hook_13),
    C(2, 4, 'night', 'num', num='十年囚禁', line='汉节始终不丢', art=art_q_hook_staff),
    C(4, 6, 'fate', 'num', num='凿空', line='打通西域', art=art_q_hook_drill),
    C(6, 8, 'empire', 'num', num='丝绸之路', line='从他脚下开始', art=art_q_hook_silk),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 应募出使
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-164, main='汉中少年', sub='汉中城固人', note='生年不详 一说约前一六四年', art=art_q_hometown),
    C(22, 26, 'court', 'card', year=-140, main='宫中为郎', sub='侍卫在汉武帝身边', art=art_q_lang),
    C(26, 30, 'empire', 'card', year=-139, main='应募出使', sub='联络大月氏 · 夹击匈奴', note='匈奴破月氏王 以其头为饮器', art=art_q_volunteer),
    C(30, 34, 'works', 'card', year=-139, main='堂邑父', sub='胡人向导 · 善射', note='穷急 射禽兽给食', art=art_q_ganfu),
    C(34, 38, 'life', 'card', year=-139, main='出陇西', sub='持节西行', art=art_q_depart),
    C(38, 46, 'night', 'card', year=-139, main='匈奴扣留', sub='一扣就是十年 · 娶妻生子', note='然骞持汉节不失', art=art_q_captive),
    C(46, 48, 'fate', 'card', year=-129, main='伺机西逃', sub='与部属向西出逃', art=art_q_slip_away),
    # ---- 第二回 西域见闻
    C(48, 50, 'works', 'chapter'),
    C(50, 58, 'works', 'route', year=-129),
    C(58, 62, 'empire', 'card', year=-129, main='大宛', sub='汗血宝马 · 葡萄美酒', note='多善马 马汗血', art=art_q_dayuan),
    C(62, 66, 'court', 'card', year=-128, main='康居', sub='大宛派人护送 · 转至大月氏', art=art_q_kangju),
    C(66, 70, 'life', 'card', year=-128, main='大月氏', sub='土地肥饶 · 已无复仇之心', note='殊无报胡之心', art=art_q_yuezhi),
    C(70, 74, 'works', 'card', year=-128, main='大夏', sub='见到蜀布与邛竹杖', note='可从蜀地通身毒', art=art_q_daxia),
    C(74, 80, 'night', 'card', year=-127, main='再被扣留', sub='取道羌中 · 又落匈奴之手', note='留岁余', art=art_q_recaptured),
    # ---- 第三回 十三年归
    C(80, 82, 'death', 'chapter'),
    C(82, 88, 'death', 'card', year=-126, main='归来', sub='匈奴内乱 · 携胡妻与甘父逃回', note='去十三岁 唯二人得还', art=art_q_return_two),
    C(88, 92, 'court', 'card', year=-126, main='面见武帝', sub='讲述西域诸国', art=art_q_report),
    C(92, 96, 'empire', 'card', year=-126, main='太中大夫', sub='武帝授官', art=art_q_official),
    C(96, 100, 'war', 'card', year=-123, main='随军北征', sub='随卫青出塞', note='知水草处 军得以不乏', art=art_q_north),
    C(100, 104, 'empire', 'card', year=-123, main='博望侯', sub='以军功封侯', art=art_q_bowang),
    C(104, 108, 'works', 'card', year=-122, main='寻路身毒', sub='从西南探路 · 受阻昆明', art=art_q_southwest),
    C(108, 112, 'night', 'card', year=-121, main='失期当斩', sub='随李广出击 · 误了军期', art=art_q_late),
    # ---- 第四回 再使乌孙
    C(112, 114, 'fate', 'chapter'),
    C(114, 122, 'fate', 'card', year=-119, main='再使乌孙', sub='三百人 · 牛羊万头', note='赍金币帛直数千巨万', art=art_q_wusun_caravan),
    C(122, 126, 'works', 'card', year=-119, main='分遣副使', sub='分赴大宛 康居 大夏 安息 身毒', art=art_q_envoys),
    C(126, 130, 'court', 'card', year=-118, main='乌孙犹豫', sub='不知汉朝虚实', art=art_q_wusun_hesitate),
    C(130, 134, 'empire', 'card', year=-115, main='乌孙使者', sub='随张骞入汉 · 见汉人众富厚', art=art_q_wusun_envoy),
    C(134, 138, 'court', 'card', year=-115, main='拜为大行', sub='位列九卿', art=art_q_daxing),
    C(138, 142, 'death', 'card', year=-114, main='病逝', sub='归来一年余 · 卒', art=art_q_death),
    C(142, 144, 'empire', 'card', year=-114, main='副使归来', sub='各国使者随之而来', art=art_q_envoys_return),
    # ---- 第五回 丝路长存
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'war', 'card', year=-101, main='天马来', sub='汉朝得大宛良马', art=art_q_horses),
    C(150, 154, 'life', 'card', year=-100, main='葡萄苜蓿', sub='西域物产传入中原', note='一说 由张骞带回', art=art_q_grapes),
    C(154, 158, 'works', 'card', year=-91, main='凿空', sub='司马迁评张骞之功', note='张骞凿空', art=art_q_zaokong),
    C(158, 162, 'empire', 'card', year=-60, main='西域都护', sub='汉朝设西域都护府', art=art_q_duhu),
    C(162, 166, 'works', 'card', year=1877, main='丝绸之路', sub='德国学者李希霍芬命名', art=art_q_name),
    C(166, 170, 'end', 'card', year=2014, main='申遗成功', sub='长安天山廊道 · 列入世界遗产', art=art_q_heritage),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾伍', col=DUNE, acc=TURQ, born=-164, died=-114,
    born_lab='约前164年', died_lab='前114年', years_txt='约公元前164 — 前114',
    hook_q='一次出差十三年 · 他到底去了哪？',
    name_line='张骞 · 字子文', name='张骞', seal='博望', title_art=art_q_title,
    q1='凿空英雄？', q2='劳而无功？',
    end_art=art_q_legacy, end_big='凿空西域', end_seal='博望',
    end_l1='他没完成最初的任务', end_l2='却打开了一个世界',
    end_brush='持节不失', end_ask='你愿意用十三年走一条路吗？评论区聊聊', next='司马迁'),
    scenes=dict(chapter=scene_chapter, route=scene_route))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
