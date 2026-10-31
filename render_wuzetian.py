# 千古人物志 · 第肆集 · 武则天 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效），本集特色：
#   紫金远山 · 凤凰章回卡 · 紫瓣金屑 · 驯狮子骢 · 日月当空造「曌」 · 请君入瓮 · 八拍「无字碑」长镜
#   并按要求去掉每拍的墨韵涟漪圆圈。
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_taizong as Tz        # engine + helpers from earlier episodes
import render_wudi as Wd
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, rotp, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P

F.RIPPLE = False                    # 去掉跳动的涟漪圆圈

BORN, DIED = 624, 705
END_BEAT = 170
GOLD = (190, 140, 50)
ZI = (112, 62, 118)                 # 紫
S.LAYERS.append(('gold', GOLD, 0.85, 1.2))
S.LAYERS.append(('purple', ZI, 0.80, 1.5))

# ================================================================ episode look
WM = dict(hook='曌', life='媚', court='帘', night='尼', war='变', empire='周', works='神', fate='碑', death='陵', end='天')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end'):
    G.THEMES[k]['part'] = 'lilac'
for k in ('empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
G.THEMES['hook']['tint'] = (1.0, 0.96, 0.98)
G.THEMES['empire']['tint'] = (1.02, 0.95, 0.92)
G.THEMES['empire']['sun'] = (GOLD, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = (ZI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZI, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (54, 44, 70), 'death': (62, 58, 66), 'war': (92, 44, 50)}
def draw_background(t, theme):
    """紫金远山: distant ranges in purple-grey with a gilded nearest ridge."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], SERIF if th['wm'] == '曌' else WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(126, 100, 140), (96, 70, 112), MTN_COL.get(theme, (70, 50, 80))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

_orig_sprite = Tz._orig_sprite
@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'lilac':
        return _orig_sprite(kind, q)
    s = 44
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(150, 96, 160), (186, 140, 196), (120, 70, 136)][q]
    d.ellipse((10, 16, 34, 30), fill=col + (220,))
    d.ellipse((15, 19, 29, 27), fill=tuple(min(255, c + 30) for c in col) + (220,))
    return im.filter(ImageFilter.GaussianBlur(0.7))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """Purple frame with gilded phoenix-feather corners."""
    d = ImageDraw.Draw(canvas)
    m = 46
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 130, y), fill=ZI + (190,), width=3); d.line((x, y, x, y + sy * 130), fill=ZI + (190,), width=3)
        for k in range(3):
            a = math.radians(45 + (k - 1) * 22)
            tx, ty = x + sx * 70 * math.cos(a), y + sy * 70 * math.sin(a)
            d.line((x + sx * 10, y + sy * 10, tx, ty), fill=GOLD + (200,), width=2)
            d.ellipse((tx - 7, ty - 7, tx + 7, ty + 7), outline=GOLD + (220,), width=2)
            d.ellipse((tx - 2, ty - 2, tx + 2, ty + 2), fill=ZI + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ phoenix chapter card
def phoenix(A, cx, cy, s, p, t):
    """Stylised phoenix: crested head, spread wings of feathers, long sweeping tail."""
    if p <= 0: return
    q = ease_out(p)
    hx, hy = cx + 0.30 * s, cy - 0.55 * s
    bx, by = cx, cy - 0.15 * s
    A.d['purple'].ellipse((bx - 0.16 * s, by - 0.10 * s, bx + 0.16 * s, by + 0.12 * s), fill=255)
    neck = [(bx + 0.10 * s, by - 0.05 * s), (bx + 0.25 * s, by - 0.25 * s), (hx, hy + 0.05 * s)]
    A.d['purple'].line(neck, fill=255, width=int(0.07 * s))
    A.d['purple'].ellipse((hx - 0.06 * s, hy - 0.06 * s, hx + 0.06 * s, hy + 0.06 * s), fill=255)
    A.d['gold'].polygon([(hx + 0.05 * s, hy), (hx + 0.16 * s, hy + 0.03 * s), (hx + 0.05 * s, hy + 0.04 * s)], fill=255)
    for k in range(3):
        a = math.radians(-120 + k * 18)
        A.d['gold'].line((hx, hy - 0.04 * s, hx + 0.15 * s * math.cos(a), hy - 0.04 * s + 0.15 * s * math.sin(a)), fill=255, width=4)
    flap = 0.08 * math.sin(t * 2.4)
    for side in (-1, 1):
        for j in range(7):
            a = math.radians(-90 + side * (25 + j * 13)) + side * flap
            L_ = 0.78 * s * q * (1 - 0.05 * j)
            ex, ey = bx + L_ * math.cos(a), by + L_ * math.sin(a)
            pa = a + math.pi / 2
            w = 0.05 * s
            pts = [(bx, by), (bx + 0.5 * L_ * math.cos(a) + w * math.cos(pa), by + 0.5 * L_ * math.sin(a) + w * math.sin(pa)),
                   (ex, ey), (bx + 0.5 * L_ * math.cos(a) - w * math.cos(pa), by + 0.5 * L_ * math.sin(a) - w * math.sin(pa))]
            A.d['purple' if j % 2 else 'mid'].polygon(pts, fill=255)
            A.d['gold'].ellipse((ex - 0.022 * s, ey - 0.022 * s, ex + 0.022 * s, ey + 0.022 * s), fill=255)
    for j in range(6):             # sweeping tail plumes, curling out to the side and down
        pts = []
        n = int(36 * q) + 2
        spread = (j - 2.5) * 0.10
        for i in range(n):
            f = i / 36
            x = bx - 0.05 * s - 0.95 * s * f + 0.10 * s * math.sin(f * 3.0 + t * 1.4 + j * 0.6) * f
            y = by + 0.10 * s + 0.55 * s * math.sin(f * math.pi * 0.75) + spread * s * f * 1.4
            pts.append((x, y))
        A.d['gold' if j % 2 == 0 else 'purple'].line(pts, fill=255, width=max(3, int(0.03 * s * (1.2 - j * 0.08))))
        for i in range(12, len(pts), 8):    # feather eyes along each plume
            ex, ey = pts[i]
            rr = 0.022 * s * (0.6 + i / 36)
            A.d['gold'].ellipse((ex - rr * 1.4, ey - rr, ex + rr * 1.4, ey + rr), outline=255, width=2)
            A.d['purple'].ellipse((ex - rr * 0.5, ey - rr * 0.4, ex + rr * 0.5, ey + rr * 0.4), fill=255)

def art_phoenix_chapter(A, cv, t, u):
    phoenix(A, 620, 760, 460, u / 0.6, t)
    for k in range(4):
        y = 1280 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)
L.art_chapter = art_phoenix_chapter

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_phoenix_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ZI, 'Black', bleed=False, spacing=12), W / 2, 1180, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 170, INK, W / 2, 1360, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ scenes
def empress(A, x, y, h, dir=1, **kw):
    return person(A, x, y, h, dir=dir, female=True, **kw)

def art_enter_palace(A, cv, t, u):
    palace(A, 540, 1300, 640, layer='mid')
    A.d['wash'].rectangle((60, 1300, W - 60, GROUND + 20), fill=255)
    x = walk_x(120, 470, u, 3.5 * P)
    empress(A, x, GROUND, 190, dir=1, arm=10, layer='ink')
    for k in range(2):
        person(A, 760 + k * 120, GROUND, 200, dir=-1, robe=False, hat='helmet', spear=True, layer='ink')

def art_lion_horse(A, cv, t, u):
    ground(A, GROUND)
    rear = 0.35 * math.sin(t * 6)
    tmp = Art()
    horse(tmp, 620, GROUND, 330, -1, t * 16, layer='ink')
    rot = Image.new('L', (W, H), 0)
    m = tmp.im['ink'].rotate(-math.degrees(0.20 + 0.10 * math.sin(t * 6)), center=(730, GROUND), resample=Image.BILINEAR)
    A.im['ink'].paste(m, (0, 0), m)
    for k in range(5):
        x = 760 + k * 40 + 20 * math.sin(t * 7 + k)
        A.d['wash'].ellipse((x - 40, GROUND - 40, x + 40, GROUND + 10), fill=255)
    empress(A, 260, GROUND, 230, dir=1, arm=lerp(30, 130, ease_out((u - 2 * P) / 0.3)), sword=None, layer='ink')
    if u > 2 * P:
        A.flush(cv)
        for i, ch in enumerate(('铁鞭', '铁挝', '匕首')):
            stamp(cv, seal(ch, 44, ZI if i != 1 else ZHU), 220 + i * 140, 960, t, t - u + 2 * P + i * 0.18, rot=(i - 1) * 6)

def art_temple(A, cv, t, u):
    palace(A, 540, 1240, 520, layer='mid')
    A.d['wash'].rectangle((60, 1240, W - 60, GROUND + 20), fill=255)
    sw = 0.25 * math.sin(t * 3)
    bx, by = 820, 820
    A.d['ink'].line((bx - 80, by, bx + 80, by), fill=255, width=8)
    A.d['ink'].line((bx, by, bx + 140 * math.sin(sw), by + 140 * math.cos(sw)), fill=255, width=4)
    cx, cy = bx + 140 * math.sin(sw), by + 140 * math.cos(sw)
    A.d['ink'].pieslice((cx - 50, cy - 40, cx + 50, cy + 60), 180, 360, fill=255)
    A.d['ink'].rectangle((cx - 50, cy + 8, cx + 50, cy + 22), fill=255)
    empress(A, 420, GROUND, 230, dir=1, kneel=True, bow=30 + 6 * math.sin(t * 2), arm=80, layer='ink')
    A.d['ink'].rectangle((600, 1300, 616, GROUND), fill=255)
    fh = 36 + 6 * math.sin(t * 16)
    A.d['red'].polygon([(598, 1300), (618, 1300), (611, 1300 - fh), (606, 1300 - fh)], fill=255)

def art_return_changan(A, cv, t, u):
    sun(cv, 820, 1060, 150, ZI, 110)
    city_wall(A, 640, W - 60, 1180, gate_x=860, label='长安')
    ground(A, GROUND)
    x = lerp(-80, 420, ease_out(u / (3.5 * P)))
    carriage(A, x, GROUND, 190, dir=1, wheel=t * 5, ph=t * 10)

def art_harem(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(380, GROUND), (700, GROUND), (670, 1300), (410, 1300)], fill=255)
    person(A, 540, 1300, 220, dir=1, hat='crown', arm=30, layer='ink')
    lean = 15 + 6 * math.sin(t * 3)
    empress(A, 780, GROUND, 240, dir=-1, bow=lean, arm=50, hat='crown', layer='mid')
    empress(A, 900, GROUND, 230, dir=-1, bow=lean, arm=50, layer='mid')
    empress(A, 220, GROUND, 250, dir=1, arm=lerp(-10, 60, ease_out((u - P) / 0.4)), layer='ink')
    for k in range(6):
        q = (u * 0.5 + k / 6) % 1
        x = 180 + k * 140 + 30 * math.sin(t + k); y = lerp(700, 1350, q)
        A.d['purple'].ellipse((x - 9, y - 6, x + 9, y + 6), fill=int(230 * (1 - q)))

def art_crowned(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(380, GROUND), (700, GROUND), (660, 1290), (420, 1290)], fill=255)
    A.d['ink'].polygon([(470, 1290), (610, 1290), (600, 1200), (480, 1200)], fill=255)
    empress(A, 540, 1200, 230, dir=1, hat='crown', arm=50, layer='ink')
    for fx_ in (330, 760):
        flag(A, fx_, 1290, 330, t + fx_, w=110, layer='purple')
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.12)
    b = 35 + 30 * hit
    for i, xx in enumerate((110, 220)):
        person(A, xx, GROUND, 190, dir=1, kneel=True, bow=b, arm=60, layer='ink' if i else 'mid')
    for i, xx in enumerate((970, 860)):
        person(A, xx, GROUND, 190, dir=-1, kneel=True, bow=b, arm=60, layer='ink' if i else 'mid')

def art_curtain(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(260, GROUND), (820, GROUND), (790, 1300), (290, 1300)], fill=255)
    person(A, 400, 1300, 210, dir=1, hat='crown', arm=20, bow=8, layer='ink')
    empress(A, 680, 1300, 230, dir=-1, hat='crown', arm=60, layer='mid')
    drop = ease_out(u / (1.5 * P))
    for k in range(14):
        x = 560 + k * 18
        sw = 4 * math.sin(t * 2 + k * 0.5)
        A.d['gold'].line((x, 760, x + sw, lerp(760, 1290, drop)), fill=255, width=3)
    A.d['gold'].rectangle((550, 750, 820, 766), fill=255)
    for k in range(3):
        person(A, 120 + k * 90, GROUND, 170, dir=1, kneel=True, bow=40, arm=70, layer='ink')

def art_two_sages(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(260, GROUND), (820, GROUND), (790, 1290), (290, 1290)], fill=255)
    person(A, 420, 1290, 220, dir=1, hat='crown', arm=40, layer='ink')
    empress(A, 660, 1290, 220, dir=-1, hat='crown', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('天皇', 50), 420, 930, t, t - u + P)
    stamp(cv, seal('天后', 50, ZI), 660, 930, t, t - u + P + 0.15)

def art_proclamation(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 760 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 840, x1, 1240), fill=150)
    A.d['ink'].rectangle((x0 - 20, 820, x0, 1260), fill=255)
    A.d['ink'].rectangle((x1, 820, x1 + 20, 1260), fill=255)
    fo = font(BRUSH, 60)
    lines = ['请看今日之域中', '竟是谁家之天下']
    for j, ln in enumerate(lines):
        for i, ch in enumerate(ln):
            x = 900 - j * 110 - 0; y = 870 + i * 52
            if x0 < x < x1 and u > 0.3 + (j * 7 + i) * 0.05:
                A.d['ink'].text((540 + 60 - j * 120 - 30, 860 + i * 52), ch, font=fo, fill=255)
    for k in range(4):
        person(A, 140 + k * 80, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='mid')

def art_urn(A, cv, t, u):
    ground(A, GROUND)
    if u < 3 * P:
        A.d['ink'].rectangle((420, 1060, 660, 1300), fill=255)
        A.d['ink'].rectangle((400, 1040, 680, 1070), fill=255)
        A.d['ink'].rectangle((500, 1050, 580, 1060), fill=0)
        A.d['ink'].rectangle((440, 1300, 470, GROUND), fill=255); A.d['ink'].rectangle((610, 1300, 640, GROUND), fill=255)
        for k in range(6):
            q = (u * 1.2 + k / 6) % 1
            x = 540 + 20 * math.sin(k); y = lerp(760, 1040, q)
            A.d['mid'].rectangle((x - 12, y - 30, x + 12, y + 30), fill=255)
        for k in range(3):
            x = walk_x(-100 - k * 110, 300 - k * 110, u, 2 * P)
            person(A, x, GROUND, 170, dir=1, ph=t * 6 + k, robe=False, layer='mid')
        A.flush(cv)
        stamp(cv, seal('铜匦', 54), 540, 1180, t, t - u + 0.2)
    else:
        v = u - 3 * P
        A.d['ink'].chord((380, 1020, 700, 1360), 0, 360, fill=255)
        A.d['ink'].rectangle((420, 1010, 660, 1050), fill=255)
        flames(A, 540, GROUND, 360, 160 * ease_out(v / 0.3), t, n=7, seed=5, smoke=True)
        person(A, 840, GROUND, 250, dir=-1, kneel=True, bow=50, arm=70, layer='ink')
        person(A, 240, GROUND, 260, dir=1, arm=80, layer='ink')

def art_zhao(A, cv, t, u):
    p = ease_out(u / (2 * P))
    sun(cv, lerp(140, 470, p), lerp(1300, 860, p), 110, ZHU, 170)
    mx, my = lerp(940, 610, p), lerp(1300, 860, p)
    A.d['mid'].ellipse((mx - 110, my - 110, mx + 110, my + 110), fill=255)
    A.d['mid'].ellipse((mx - 70, my - 130, mx + 150, my + 90), fill=0)
    ground(A, GROUND)
    if u > 2 * P:
        A.flush(cv)
        im = text_img('曌', SERIF, 360, INK, 'Black')
        ink_in(cv, im, 540, 1110, t, t - u + 2 * P, dur=0.4, settle=1.15)
        type_in(cv, text_img('日 月 当 空', SERIF, 44, ZI, 'Bold', bleed=False, spacing=10), 540, 1360, t, t - u + 2.5 * P, 0.35)

def art_wuju(A, cv, t, u):
    ground(A, GROUND)
    tx, ty = 880, 1180
    for r, lay in ((110, 'ink'), (80, 'gold'), (50, 'ink'), (22, 'red')):
        A.d[lay].ellipse((tx - r, ty - r, tx + r, ty + r), fill=255 if lay != 'ink' else 255)
        if lay == 'ink' and r == 110:
            A.d['ink'].ellipse((tx - 96, ty - 96, tx + 96, ty + 96), fill=0)
    A.d['ink'].rectangle((tx - 6, ty + 110, tx + 6, GROUND), fill=255)
    rider(A, lerp(-150, 420, ease_out(u / (1.5 * P))), GROUND, 210, 1, t * 13, layer='ink')
    for k in range(3):
        q = clamp((u - 0.3 - k * 0.15) / 0.35)
        if 0 < q < 1:
            arrow(A, lerp(420, tx - 90, q), lerp(1150, ty, q), 0, 80)
        elif q >= 1:
            arrow(A, tx - 90 - k * 6, ty - 10 + k * 14, 0, 80)

def art_wan_er(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((360, 1290, 720, 1320), fill=255)
    empress(A, 540, GROUND, 220, dir=1, kneel=True, bow=20, arm=95, layer='ink')
    n = int(clamp(u / (1.5 * P)) * 9)
    for k in range(n):
        A.d['mid'].rectangle((620 + k * 14, 1220, 630 + k * 14, 1288), fill=255)
    A.flush(cv)
    stamp(cv, seal('称量天下', 44, ZI), 820, 1000, t, t - u + P)

def art_di(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(600, GROUND), (980, GROUND), (950, 1300), (630, 1300)], fill=255)
    empress(A, 800, 1300, 220, dir=-1, hat='crown', arm=50, layer='ink')
    person(A, 400, GROUND, 260, dir=1, kneel=True, bow=30, arm=85, layer='ink')
    for k in range(3):
        x = walk_x(-100 - k * 120, 200 - k * 100, u, 2 * P)
        person(A, x, GROUND, 170, dir=1, arm=20, layer='mid')
    A.flush(cv)
    stamp(cv, seal('国老', 52, ZI), 400, 1000, t, t - u + P)

SEALS6 = [('首创殿试', ZHU), ('开设武举', ZI), ('劝农桑', ZHU), ('造曌字', ZI), ('立神都', ZHU), ('举贤才', ZI)]
SEAL_POS = [(250, 860), (540, 860), (830, 860), (250, 1150), (540, 1150), (830, 1150)]
def scene_seals(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t); A.flush(cv)
    gu = ease_expo((t - gather_t) / 0.4) if gather else 0
    for i, ((name, col), (x, y)) in enumerate(zip(SEALS6, SEAL_POS)):
        st = bt(c[0] + i)
        if t < st: continue
        px, py = lerp(x, 540, gu * 0.35), lerp(y, 1010, gu * 0.35)
        stamp(cv, seal(name, 50 if len(name) <= 3 else 44, col), px, py, t, st, rot=(i % 3 - 1) * 5)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '女皇新政', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '政启开元', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '治宏贞观', BRUSH, 150, ZI, W / 2, 1420, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

def art_heir(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(400, GROUND), (680, GROUND), (650, 1270), (430, 1270)], fill=255)
    empress(A, 540, 1270, 220, dir=1 if math.sin(t * 2) > 0 else -1, hat='crown', arm=40, layer='ink')
    person(A, 190, GROUND, 230, dir=1, arm=40, layer='ink')
    person(A, 890, GROUND, 230, dir=-1, arm=40, hat='crown', layer='ink')
    A.flush(cv)
    stamp(cv, seal('侄', 50, INK), 190, 1000, t, t - u + 0.2)
    stamp(cv, seal('子', 50, ZHU), 890, 1000, t, t - u + P)

def art_return_heir(A, cv, t, u):
    city_wall(A, 640, W - 60, 1180, gate_x=860, label='神都')
    ground(A, GROUND)
    x = lerp(-80, 420, ease_out(u / (3.5 * P)))
    carriage(A, x, GROUND, 190, dir=1, wheel=t * 5, ph=t * 10)
    for k in range(4):
        flag(A, 680 + k * 110, 1150, 150, t + k, w=60, layer='purple')

def art_favorites(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(560, GROUND), (980, GROUND), (950, 1300), (590, 1300)], fill=255)
    empress(A, 780, 1300, 220, dir=-1, hat='crown', arm=30, layer='ink')
    for k in range(2):
        person(A, 380 + k * 120, GROUND, 230, dir=1, bow=15 + 8 * math.sin(t * 3 + k), arm=70, layer='ink')
    for k in range(5):
        x = 100 + k * 220
        sw = 8 * math.sin(t * 2 + k)
        A.d['ink'].line((x, 700, x + sw, 760), fill=255, width=2)
        A.d['purple'].ellipse((x + sw - 22, 760, x + sw + 22, 820), fill=255)

def art_shenlong(A, cv, t, u):
    sun(cv, 540, 1000, 220, ZHU, 100)
    city_wall(A, 60, W - 60, 1080, gate_x=540, label='玄武', open_=ease_out(u / (1.5 * P)))
    ground(A, GROUND)
    for k in range(6):
        x = walk_x(-120 - k * 110, 400 - k * 70, u, 3 * P)
        person(A, x, GROUND, 200, dir=1, robe=False, hat='helmet', spear=True, ph=t * 9 + k, layer='ink' if k % 2 == 0 else 'mid')
    for k in range(6):
        p = ease_out((u - 0.3 - k * 0.06) / 0.3)
        px = 150 + k * 150
        A.d['red'].line((px, 1080, px, lerp(1080, 1000, p)), fill=255, width=5)
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('神龙元年', 50), 860, 900, t, t - u + 2 * P, rot=6)

def art_shangyang(A, cv, t, u):
    palace(A, 540, GROUND, 640, layer='mid')
    A.d['wash'].rectangle((420, 1060, 660, 1200), fill=0)
    empress(A, 540, 1200, 140, dir=1, hat='crown', bow=20, arm=20, layer='ink')
    for k in range(10):
        q = (u * 0.4 + k / 10) % 1
        x = 100 + k * 95 + 40 * math.sin(t * 2 + k); y = lerp(650, 1400, q)
        a = t * 3 + k
        A.d['gold'].polygon([rotp(p, (x, y), a) for p in ((x - 14, y), (x, y - 6), (x + 14, y), (x, y + 6))], fill=255)
    for k in range(3):
        a = t * 1.3 + k * 2.1
        crow(A, 540 + 320 * math.cos(a), 760 + 60 * math.sin(a), 22, t * 11 + k)

def art_will(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 700 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 860, x1, 1220), fill=150)
    A.d['ink'].rectangle((x0 - 20, 840, x0, 1240), fill=255); A.d['ink'].rectangle((x1, 840, x1 + 20, 1240), fill=255)
    fo = font(SERIF, 64, 'Black')
    txt = '去帝号'
    if p > 0.7:
        for i, ch in enumerate(txt):
            A.d['ink'].text((540 - 100 + i * 70 - 32, 990), ch, font=fo, fill=255)
    ground(A, GROUND)
    if u > 2 * P:
        q = ease_out((u - 2 * P) / 0.4)
        A.d['red'].line((540 - 120, 1030, 540 - 120 + 240 * q, 1030), fill=255, width=8)
        A.flush(cv)
        stamp(cv, seal('则天大圣皇后', 40, ZI), 800, 1180, t, t - u + 2.4 * P, rot=5)

def stele(A, cx, base, h, w, rise=1.0, layer='mid'):
    top = base - h * rise
    A.d[layer].rounded_rectangle((cx - w / 2, top, cx + w / 2, base), radius=int(w * 0.35), fill=255)
    A.d['ink'].rounded_rectangle((cx - w / 2, top, cx + w / 2, base), radius=int(w * 0.35), outline=255, width=6)
    A.d['ink'].rectangle((cx - w / 2 - 50, base, cx + w / 2 + 50, base + 40), fill=255)
    if rise > 0.6:
        for k in range(3):
            A.d['ink'].arc((cx - w / 2 + 20 + k * (w - 40) / 3, top + 20, cx - w / 2 + 20 + (k + 1) * (w - 40) / 3, top + 110), 180, 360, fill=255, width=4)
        A.d['wash'].rectangle((cx - w / 2 + 30, top + 140, cx + w / 2 - 30, base - 30), fill=0)

def art_qianling(A, cv, t, u):
    A.d['mid'].polygon([(120, 1320), (360, 900), (440, 960), (540, 820), (640, 960), (720, 900), (960, 1320)], fill=255)
    ground(A, GROUND)
    stele(A, 540, 1360, 300, 110, rise=ease_out(u / (1.5 * P)), layer='ink')

def art_wordless(A, cv, t, u):
    """8-beat set piece: the wordless stele through the seasons; merits & faults flicker and fade."""
    A.d['mid'].polygon([(60, 1340), (300, 1080), (420, 1160), (540, 1020), (660, 1160), (780, 1080), (1020, 1340)], fill=170)
    ground(A, GROUND)
    rise = ease_out(u / (1.5 * P))
    stele(A, 540, 1360, 620, 250, rise=rise)
    season = u / P
    if season < 2:
        kind, col = 'lilac', 'purple'
    elif season < 4:
        kind, col = 'rain', 'mid'
    elif season < 6:
        kind, col = 'leaf', 'gold'
    else:
        kind, col = 'snow', 'wash'
    for k in range(26):
        q = (t * (0.9 if kind == 'rain' else 0.35) + k / 26) % 1
        x = 80 + (k * 37) % 920 + 30 * math.sin(t + k); y = lerp(620, 1420, q)
        if kind == 'rain':
            A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
        elif kind == 'snow':
            A.d['ink'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=90)
        else:
            A.d[col].ellipse((x - 9, y - 6, x + 9, y + 6), fill=230)
    A.flush(cv)
    if rise > 0.95:
        for i, ch in enumerate('功过是非'):
            st = t - u + (2 + i * 1.3) * P
            v = t - st
            if 0 <= v < 1.1:
                a = clamp(v / 0.2) * clamp((1.1 - v) / 0.4)
                im = text_img(ch, BRUSH, 150, ZHU if i % 2 == 0 else INK)
                paste(cv, im, 540, 1000 + (i % 2) * 140 - 40, 1, a * 0.85, reveal=clamp(v / 0.3))

def art_two_voices(A, cv, t, u):
    ground(A, GROUND)
    person(A, 230, GROUND, 260, dir=1, arm=lerp(30, 120, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    person(A, 850, GROUND, 260, dir=-1, kneel=True, bow=35, arm=80, layer='ink')
    stele(A, 540, 1360, 300, 110, layer='mid')
    A.flush(cv)
    stamp(cv, seal('骂', 54, INK), 230, 960, t, t - u + 0.2)
    stamp(cv, seal('敬', 54, ZHU), 850, 960, t, t - u + P)

def art_kaiyuan(A, cv, t, u):
    Tz.art_market(A, cv, t, u)
    if u > P:
        A.flush(cv)
        stamp(cv, seal('开元盛世', 50, ZI), 540, 900, t, t - u + P)

def art_zhao_legacy(A, cv, t, u):
    sun(cv, 540, 1050, 260, ZI, 120)
    fo = font(SERIF, 480, 'Black')
    ch = '曌'
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength(ch) / 2, 760), ch, font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)
    ground(A, GROUND)
    for k in range(6):
        empress(A, 140 + k * 160, GROUND, 150 + (k % 2) * 20, dir=1 if k < 3 else -1, arm=40, layer='mid')

def art_stele_dawn(A, cv, t, u):
    sun(cv, 540, lerp(1250, 900, ease_out(u / (4 * P))), 230, ZHU, 120)
    A.d['mid'].polygon([(60, 1340), (300, 1080), (420, 1160), (540, 1020), (660, 1160), (780, 1080), (1020, 1340)], fill=170)
    ground(A, GROUND)
    stele(A, 540, 1360, 620, 250, rise=1.0)

def art_hook_stele(A, cv, t, u):
    ground(A, GROUND)
    stele(A, 540, 1360, 520, 220, rise=ease_out(u / 0.5))
    for k in range(3):
        a = t * 1.3 + k * 2.1
        crow(A, 540 + 300 * math.cos(a), 760 + 60 * math.sin(a), 22, t * 11 + k)

# ================================================================ script
CHAPTERS = {16: ('第一回', '才人武媚'), 48: ('第二回', '二圣临朝'), 80: ('第三回', '女皇登基'),
            112: ('第四回', '晚年风云'), 144: ('第五回', '无字丰碑')}

CARDS = [
    C(0, 2, 'hook', 'num', num='十四岁', line='入宫为才人', art=art_enter_palace),
    C(2, 4, 'hook', 'num', num='感业寺', line='削发为尼', art=art_temple),
    C(4, 6, 'hook', 'num', num='六十七岁', line='登基称帝', art=art_crowned),
    C(6, 8, 'hook', 'num', num='无字碑', line='功过任人评', art=art_hook_stele),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 才人武媚
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=624, main='生于利州', sub='木材商人之女 · 自幼聪慧', note='袁天罡相之 曰 若是女 当为天下主', art=Tz.art_birth),
    C(22, 26, 'life', 'card', year=637, main='十四入宫', sub='太宗召为才人 · 赐号武媚', note='太宗闻其美 召入宫', art=art_enter_palace),
    C(26, 30, 'life', 'card', year=638, main='驯狮子骢', sub='烈马无人能驯 · 她说只需三物', note='铁鞭击之 不服 则以挝挝其首 又不服 则以匕首断其喉', art=art_lion_horse),
    C(30, 34, 'night', 'card', year=649, main='感业寺', sub='太宗驾崩 · 削发为尼', note='青灯古佛 心有不甘', art=art_temple),
    C(34, 38, 'life', 'card', year=651, main='重回宫闱', sub='高宗旧情难忘 · 召回宫中', note='上见之而泣 武氏亦泣', art=art_return_changan),
    C(38, 42, 'court', 'card', year=654, main='后宫之争', sub='王皇后 萧淑妃 · 步步为营', note='卑辞屈体以事后', art=art_harem),
    C(42, 46, 'court', 'card', year=655, main='立为皇后', sub='废王立武 · 三十二岁母仪天下', note='百官朝皇后于肃义门', art=art_crowned),
    C(46, 48, 'night', 'card', year=655, main='宫闱血影', sub='王后 萧妃 · 惨死冷宫', art=Wd.art_dusk_palace),
    # ---- 第二回 二圣临朝
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=660, main='垂帘听政', sub='高宗风疾 · 皇后代批奏章', note='上每视朝 天后垂帘于御座后', art=art_curtain),
    C(54, 58, 'court', 'card', year=674, main='二圣临朝', sub='天皇天后 · 并称二圣', note='政无大小 皆预闻之', art=art_two_sages),
    C(58, 62, 'life', 'card', year=674, main='建言十二', sub='劝农桑 薄赋徭 · 息兵戈', note='天后上表 建言十二事', art=Tz.art_farm),
    C(62, 66, 'night', 'card', year=683, main='高宗驾崩', sub='临朝称制 · 大权独揽', note='军国大事 有不决者 取天后处分', art=Wd.art_dusk_palace),
    C(66, 70, 'court', 'card', year=684, main='废立皇帝', sub='一年之内 · 连废中宗', note='废中宗为庐陵王 立睿宗', art=Tz.art_depose),
    C(70, 74, 'war', 'card', year=684, main='讨武檄文', sub='徐敬业扬州起兵 · 骆宾王作檄', note='宰相安得失此人', art=art_proclamation),
    C(74, 80, 'night', 'card', year=691, main='请君入瓮', sub='设铜匦 任酷吏 · 以其人之道还治其身', note='周兴 来俊臣 罗织罪名', art=art_urn),
    # ---- 第三回 女皇登基
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'empire', 'card', year=689, main='日月当空', sub='为自己造字 · 武曌', note='曌 读作照 取日月当空之意', art=art_zhao),
    C(86, 90, 'empire', 'card', year=690, main='改唐为周', sub='六十七岁 · 登基称帝', seal='大周', note='中国历史上唯一的女皇帝', art=art_crowned),
    C(90, 96, 'works', 'card', year=690, main='神都洛阳', sub='迁都洛阳 · 号为神都', note='明堂 天堂 高耸入云', art=L.art_palace_build),
    C(96, 98, 'empire', 'card', year=690, main='首创殿试', sub='天子亲自策问贡士', art=Tz.art_exam),
    C(98, 100, 'war', 'card', year=702, main='开设武举', sub='骑射选拔将才', art=art_wuju),
    C(100, 102, 'court', 'card', year=698, main='上官婉儿', sub='女官掌诏命 · 称量天下', art=art_wan_er),
    C(102, 104, 'court', 'card', year=697, main='国老狄公', sub='狄仁杰拜相 · 举贤满朝', art=art_di),
    C(104, 112, 'empire', 'seals'),
    # ---- 第四回 晚年风云
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'court', 'card', year=698, main='立储之难', sub='传侄武三思 · 还是子李显？', note='姑侄之与母子孰亲', art=art_heir),
    C(118, 122, 'works', 'card', year=698, main='还政李唐', sub='召回庐陵王 · 复立为太子', note='天下归心 复归李氏', art=art_return_heir),
    C(122, 126, 'night', 'card', year=700, main='二张专宠', sub='张易之 张昌宗 · 恃宠弄权', note='朝臣侧目', art=art_favorites),
    C(126, 130, 'war', 'card', year=705, main='神龙政变', sub='张柬之率羽林军 · 斩二张 逼退位', note='神龙元年正月 兵入玄武门', art=art_shenlong),
    C(130, 134, 'death', 'card', year=705, main='退居上阳', sub='被迫传位 · 移居上阳宫', note='自是 不复栉颒', art=art_shangyang),
    C(134, 138, 'death', 'card', year=705, main='崩于上阳宫', sub='享年八十二岁', note='十一月壬寅 崩于上阳宫', art=Wd.art_dusk_palace),
    C(138, 142, 'death', 'card', year=705, main='遗诏', sub='去帝号 · 称则天大圣皇后', note='祔庙 归陵 令去帝号', art=art_will),
    C(142, 144, 'fate', 'card', year=706, main='合葬乾陵', sub='与高宗同穴', art=art_qianling),
    # ---- 第五回 无字丰碑
    C(144, 146, 'fate', 'chapter'),
    C(146, 154, 'fate', 'card', year=706, main='无字碑', sub='千年风雨 · 碑上一字未刻', note='己之功过 留待后人评说', art=art_wordless),
    C(154, 158, 'fate', 'card', year=706, main='毁誉千年', sub='骆宾王骂她 · 狄仁杰敬她', note='一千个人眼中 有一千个武则天', art=art_two_voices),
    C(158, 162, 'empire', 'card', year=706, main='政启开元', sub='为开元盛世铺路', note='政启开元 治宏贞观', art=art_kaiyuan),
    C(162, 166, 'end', 'card', year=706, main='唯一女皇', sub='中国历史上 · 唯一正统女皇帝', note='日月当空 照临下土', art=art_zhao_legacy),
    C(166, 170, 'end', 'card', year=706, main='一字未留', sub='功过 · 留与后人评', note='无字 胜有字', art=art_stele_dawn),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS; L.CHAPTERS = CHAPTERS; Wd.CHAPTERS = CHAPTERS; Tz.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
G.year_at = year_at; L.year_at = year_at; Wd.year_at = year_at; Tz.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    s = '公元' + cn_num(yr) + '年'
    im = text_img(s, SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=ZI + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, lambda A, cv_, t_, u_: (sun(cv_, 600, 1000, 250, ZI, 130), empress(A, 470, 1440, 700, dir=1, hat='crown', arm=lerp(-5, 55, ease_out(u_ / (2 * P)))), ground(A, 1440)))
    fx = Art()
    ink_in(cv, text_img('武 曌', SERIF, 50, ZI, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '武则天', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('日月当空', 58, ZI), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元624 — 705', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '篡唐妖后？', BRUSH, 120, ZI, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '千古女帝？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完她的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    phoenix(A, 620, 560, 340, u / 0.8, t)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.7)
    fx = Art()
    chars_in(cv, fx, '千古女帝', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('则天', 64, ZI), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('从才人到女皇 · 走了整整五十三年', SERIF, 46, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('她只留下一块无字碑', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '你会写下什么？', BRUSH, 110, ZI, W / 2, 1200, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区替她刻一个字', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=ZI + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=GOLD + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 宋太祖赵匡胤', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, seals=scene_seals, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第肆集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('从尼姑到女皇 · 她到底有多狠？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=ZI + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, ZI, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.9)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=ZI + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=GOLD + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁' if yr < DIED + 0.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=ZI + (255,))
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 80))
G.draw_hud = draw_hud

render = L.render

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', L.MUSIC,
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 300 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
