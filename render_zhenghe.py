# 千古人物志 · 第拾柒集 · 郑和 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：宝船远洋 —— 深海碧绿 · 罗盘章回卡（每回多一圈刻度、指针转向新方位）· 牵星板边角
#          · 八拍「宝船出海」 · 七下西洋航线七印回顾 · 八拍「麒麟入京」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_qijiguang as Qj       # engine + helpers (ink layers drawn last)
import render_wentianxiang as Wx
import render_yuefei as Yf
import render_zhuge as Zg
import render_caocao as Cc
import render_liubang as Lb
import render_genghis as Gh
import render_qianlong as Q
import render_yongzheng as Y
import render_kangxi as K
import render_mingtaizu as M
import render_songtaizu as St
import render_wuzetian as Z
import render_taizong as Tz
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
from render_kangxi import rect, lantern
from render_wudi import camel
from render_qianlong import dome, palm
from render_songtaizu import tent
from render_yuefei import cn_year

F.RIPPLE = False

BORN, DIED = 1371, 1433
END_BEAT = 170
OCEAN = (24, 104, 104)              # 深海碧
GILD = (196, 150, 56)               # 宝船金
S.LAYERS.append(('ocean', OCEAN, 0.80, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='和', life='马', court='燕', night='夜', war='戰', empire='明', works='洋', fate='航', death='归', end='和')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (GILD, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (GILD, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (OCEAN, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (30, 46, 52), 'death': (56, 60, 62), 'war': (96, 60, 44), 'works': (40, 90, 96)}
def draw_background(t, theme):
    """远洋: low teal swells instead of tall ranges."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 182, 180), (96, 146, 146), MTN_COL.get(theme, (50, 108, 108))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 8 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.4))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """牵星板: stacked star-sighting boards with a small star at each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = OCEAN + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=3); d.line((x, y, x, y + sy * 160), fill=col, width=3)
        for k in range(4):
            s_ = 34 - k * 7
            bx, by = x + sx * (30 + k * 10), y + sy * (30 + k * 10)
            d.rectangle((min(bx, bx + sx * s_), min(by, by + sy * s_), max(bx, bx + sx * s_), max(by, by + sy * s_)), outline=col, width=2)
        sx_, sy_ = x + sx * 110, y + sy * 30
        for a in range(5):
            ang = -math.pi / 2 + a * 2 * math.pi / 5
            d.line((sx_, sy_, sx_ + 9 * math.cos(ang), sy_ + 9 * math.sin(ang)), fill=GILD + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def treasure_ship(A, x, y, s, t, layer='ink', sails=9, bob=True):
    """宝船: long high-sterned hull, multiple masts with batten sails."""
    b = 6 * math.sin(t * 1.6 + x * 0.01) if bob else 0
    A.d[layer].polygon([(x - s, y - 70 + b), (x - 0.8 * s, y - 30 + b), (x + 0.8 * s, y - 30 + b), (x + s, y - 90 + b),
                        (x + 0.9 * s, y + 20 + b), (x - 0.85 * s, y + 20 + b)], fill=255)
    A.d['red'].rectangle((x - 0.6 * s, y - 40 + b, x + 0.6 * s, y - 28 + b), fill=255)
    n = min(sails, 9)
    for i in range(n):
        mx = x - 0.7 * s + i * (1.4 * s / max(1, n - 1))
        h = s * (0.9 + 0.5 * math.sin(math.pi * (i + 0.5) / n))
        A.d[layer].line((mx, y - 30 + b, mx, y - 30 - h + b), fill=255, width=max(3, int(s * 0.02)))
        sw = s * 0.11
        A.d['gold'].polygon([(mx - sw, y - 30 - h + b), (mx + sw, y - 30 - h + b), (mx + sw * 1.1, y - 60 + b), (mx - sw * 0.9, y - 60 + b)], fill=220)
        for j in range(4):
            yy = lerp(y - 30 - h + b, y - 60 + b, (j + 1) / 5)
            A.d[layer].line((mx - sw, yy, mx + sw, yy), fill=180, width=2)

def zhenghe(A, x, y, h, dir=1, layer='ink', **kw):
    """郑和: tall official robe and cap with side wings."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    A.d[layer].rectangle((x - 0.07 * h, y - 1.06 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
    A.d[layer].line((x - 0.18 * h, y - 0.98 * h, x + 0.18 * h, y - 0.98 * h), fill=255, width=max(2, int(0.025 * h)))
    return hand

def giraffe(A, x, y, s, dir=1, ph=0.0, layer='ink'):
    d = A.d[layer]
    def T(u_, v): return (x + dir * u_ * s, y - v * s)
    d.polygon([T(*p_) for p_ in ellipse_pts(0, 0.9, 0.35, 0.16)], fill=255)
    d.polygon([T(0.22, 0.98), T(0.32, 0.9), T(0.62, 1.9), T(0.52, 1.95)], fill=255)
    d.polygon([T(*p_) for p_ in ellipse_pts(0.64, 1.96, 0.12, 0.06)], fill=255)
    for hu, off in ((0.22, 0), (0.12, 1.6), (-0.2, 3.1), (-0.28, 4.7)):
        a = 0.25 * math.sin(ph + off)
        d.line([T(hu, 0.8), T(hu + 0.1 * math.sin(a), 0)], fill=255, width=max(3, int(0.05 * s)))
    for k in range(6):
        px, py = T(-0.2 + k * 0.08, 0.92 + 0.04 * (k % 2))
        A.d['gold'].ellipse((px - 6, py - 6, px + 6, py + 6), fill=255)

def compass(A, cx, cy, r, ticks, ang, p=1.0, layer='ink'):
    q = ease_out(p)
    rr = r * q
    if rr < 4: return
    A.d['mid'].ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=200)
    A.d[layer].ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=255, width=6)
    for ring in range(min(ticks, 4)):
        r2 = rr * (0.9 - ring * 0.14)
        A.d[layer].ellipse((cx - r2, cy - r2, cx + r2, cy + r2), outline=180, width=2)
        n = 8 * (ring + 1)
        for k in range(n):
            a = k * 2 * math.pi / n
            A.d[layer].line((cx + r2 * math.cos(a), cy + r2 * math.sin(a), cx + (r2 - 12) * math.cos(a), cy + (r2 - 12) * math.sin(a)), fill=255, width=2)
    tip = (cx + rr * 0.6 * math.cos(ang), cy + rr * 0.6 * math.sin(ang))
    tail = (cx - rr * 0.6 * math.cos(ang), cy - rr * 0.6 * math.sin(ang))
    pa = ang + math.pi / 2
    A.d['red'].polygon([tip, (cx + 14 * math.cos(pa), cy + 14 * math.sin(pa)), (cx - 14 * math.cos(pa), cy - 14 * math.sin(pa))], fill=255)
    A.d[layer].polygon([tail, (cx + 14 * math.cos(pa), cy + 14 * math.sin(pa)), (cx - 14 * math.cos(pa), cy - 14 * math.sin(pa))], fill=255)
    A.d[layer].ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=255)

def sea(A, y0, t, rows=4, amp=10, speed=2.0):
    A.d['ocean'].rectangle((60, y0, W - 60, 1420), fill=130)
    waves(A, y0 + 10, t, rows=rows, amp=amp, speed=speed)

# ================================================================ chapter card
CH = {16: (1, -2.4), 48: (2, -1.6), 80: (3, -0.6), 112: (4, 0.3), 144: (4, 1.2)}
def art_compass_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    rings, a = CH.get(kb, (2, -1.6))
    compass(A, 540, 920, 300, rings, a + 0.1 * math.sin(t * 2) + (1 - ease_out(clamp(u / 0.8))) * 3, p=u / 0.5)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_compass_chapter)
    ink_in(cv, text_img(no, SERIF, 56, OCEAN, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_seven(A, cv, t, u):
    sea(A, 1200, t)
    n = int(clamp(u / (1.6 * P)) * 7) + 1
    for i in range(n):
        treasure_ship(A, 120 + i * 140, 1230 + (i % 2) * 30, 60, t + i, sails=5, layer='ink' if i % 2 else 'mid')

def art_z_hook_ship(A, cv, t, u):
    sea(A, 1200, t)
    treasure_ship(A, 540, 1240, lerp(200, 380, ease_out(u / (1.6 * P))), t, sails=9)

def art_z_hook_world(A, cv, t, u):
    A.d['ocean'].ellipse((260, 820, 820, 1380), fill=120)
    A.d['ink'].ellipse((260, 820, 820, 1380), outline=255, width=6)
    pts = [(540 + 280 * math.cos(a) * 0.9, 1100 + 280 * math.sin(a) * 0.5) for a in np.linspace(math.pi * 1.2, math.pi * 1.2 + 4 * ease_out(u / (1.6 * P)), 40)]
    A.d['red'].line(pts, fill=255, width=6)

def art_z_hook_eunuch(A, cv, t, u):
    palace(A, 540, GROUND, 640, layer='mid')
    ground(A, GROUND)
    zhenghe(A, 540, GROUND, 240, dir=1, bow=lerp(30, 0, ease_out(u / (1.6 * P))), arm=lerp(20, 60, ease_out(u / (1.6 * P))), layer='ink')

# ================================================================ 第一回 马三保
def art_z_birth(A, cv, t, u):
    A.d['ocean'].ellipse((160, 1180, 920, 1340), fill=150)
    for k, x in enumerate((180, 820)):
        A.d['mid'].polygon([(x - 200, 1260), (x, 960 - k * 40), (x + 200, 1260)], fill=220)
    dome(A, 540, 1250, 160, 150, layer='ink')
    A.flush(cv)
    stamp(cv, seal('昆阳', 56), 860, 940, t, t - u + P)

def art_z_hajj(A, cv, t, u):
    for k, (y0, amp) in enumerate(((1300, 50), (1360, 40))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + k)) for x in range(60, W - 59, 10)]
        A.d['wash' if k == 0 else 'mid'].polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=200)
    x = lerp(900, 360, ease_out(u / (4 * P)))
    camel(A, x, 1340, 160, -1, t * 5, layer='ink')
    person(A, x + 180, 1340, 180, dir=-1, robe=True, hat='knot', ph=t * 5, arm=40, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('祖父与父亲 · 都曾远赴麦加朝圣', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.5)

def art_z_captured(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    ground(A, GROUND)
    for k in range(3):
        rider(A, lerp(-150, 500, ease_out(u / (2 * P))) - k * 160, GROUND, 160, 1, t * 12 + k, layer='mid', spear=True)
    person(A, 760, GROUND, 140, dir=-1, robe=False, hat='knot', bow=40, arm=120, layer='ink')
    A.flush(cv)
    stamp(cv, seal('明军平云南', 40, INK), 300, 940, t, t - u + P, rot=-5)

def art_z_palace_boy(A, cv, t, u):
    palace(A, 620, GROUND, 600, layer='mid')
    ground(A, GROUND)
    x = walk_x(120, 420, u, 3 * P)
    person(A, x, GROUND, 160, dir=1, robe=True, hat='knot', bow=25, ph=t * 4, arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('燕王府', 50, INK), 300, 940, t, t - u + P)

def art_z_prince(A, cv, t, u):
    ground(A, GROUND)
    person(A, 720, GROUND, 290, dir=-1, robe=True, hat='crown', arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    zhenghe(A, 380, GROUND, 220, dir=1, kneel=True, bow=30, arm=70, layer='ink')
    A.flush(cv)
    stamp(cv, seal('朱棣', 50, INK), 720, 940, t, t - u + 0.3)

def art_z_jingnan(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        rider(A, lerp(-200, 500, ease_out(u / (2 * P))) - k * 130, GROUND - (k % 2) * 12, 150, 1, t * 13 + k, layer='ink' if k == 0 else 'mid', spear=True)
    for k in range(4):
        person(A, 760 + k * 70, GROUND, 150, dir=-1, robe=False, hat='helmet', spear=True, fall=-70 * ease_out((u - 2 * P - k * 0.1) / 0.3) if u > 2 * P else 0, layer='mid')
    A.flush(cv)
    stamp(cv, seal('郑村坝', 50), 860, 900, t, t - u + 2 * P, rot=5)

def art_z_surname(A, cv, t, u):
    p = ease_out(u / 0.5)
    A.d['yellow'].rectangle((540 - 260 * p, 860, 540 + 260 * p, 1180), fill=255)
    A.d['ink'].rectangle((540 - 272 * p, 850, 540 - 260 * p, 1190), fill=255); A.d['ink'].rectangle((540 + 260 * p, 850, 540 + 272 * p, 1190), fill=255)
    ground(A, GROUND)
    zhenghe(A, 540, GROUND, 200, dir=1, kneel=True, bow=45, arm=80, layer='ink')
    A.flush(cv)
    if p > 0.8:
        ink_in(cv, text_img('马', BRUSH, 150, (150, 140, 130)), 420, 1020, t, t - u + 0.5, dur=0.3)
        ink_in(cv, text_img('郑', BRUSH, 170, ZHU), 660, 1020, t, t - u + 1.5 * P, dur=0.3, settle=1.3)

def art_z_eunuch_chief(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, robe=True, hat='crown', arm=60, layer='mid')
    zhenghe(A, 380, GROUND, 260, dir=1, arm=70, layer='ink')
    A.flush(cv)
    stamp(cv, seal('内官监太监', 38), 380, 940, t, t - u + P, rot=-5)

# ================================================================ 第二回 宝船
def art_z_shipyard(A, cv, t, u):
    q = ease_out(u / (3 * P))
    treasure_ship(A, 560, 1260, 340, t, sails=int(1 + 8 * q), bob=False)
    for k in range(10):
        x = 260 + k * 60
        A.d['mid'].line((x, GROUND, x + 40, 1060), fill=200, width=4)
    ground(A, GROUND)
    for k in range(4):
        person(A, (t * 70 + k * 280) % (W + 200) - 100, GROUND, 120, dir=1, robe=False, load=True, ph=t * 6 + k, arm=160, layer='mid')
    A.flush(cv)
    stamp(cv, seal('龙江船厂', 46, INK), 860, 860, t, t - u + P, rot=5)

def art_z_size(A, cv, t, u):
    sea(A, 1220, t, rows=3, amp=6)
    treasure_ship(A, 640, 1250, 380, t, sails=9)
    boat(A, 140, 1260, 70, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('长四十四丈', SERIF, 60, GILD, 'Black', bleed=False, spacing=4), W / 2, 1460, 1, clamp((u - P) / 0.3))

def art_z_crew(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 60)
    for k in range(n):
        x = 100 + (k % 15) * 60; y = GROUND - (k // 15) * 50
        person(A, x, y, 70, dir=1, robe=k % 4 == 0, hat='helmet' if k % 3 else 'knot', arm=30, layer='ink' if k // 15 == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'{int(clamp(u / (2.5 * P)) * 27800)}人', SERIF, 64, OCEAN, 'Black', bleed=False), W / 2, 900, 1, 1)

def art_z_launch(A, cv, t, u):
    """8-beat set piece: fleet leaves 太仓刘家港 — ships fill the sea one after another, the sun rises."""
    ph = u / P
    sun(cv, 540, lerp(1240, 900, ease_out(u / (8 * P))), 220, GILD, 140)
    sea(A, 1160, t, rows=5, amp=10, speed=1.6)
    n = min(12, int(u / (0.6 * P)) + 1)
    for i in range(n):
        row = i % 3
        x = lerp(-200, 120 + (i // 3) * 240 + row * 60, ease_out((u - i * 0.6 * P) / (1.5 * P)))
        treasure_ship(A, x, 1200 + row * 60, 90 - row * 14, t + i, sails=6, layer='ink' if row == 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'宝船{n * 5 + 2}艘', SERIF, 56, GILD, 'Black', bleed=False), W / 2, 1460, 1, 1)
    if ph >= 6.5:
        stamp(cv, seal('刘家港', 50), 860, 860, t, t - u + 6.5 * P, rot=6)

def art_z_stars(A, cv, t, u):
    r = random.Random(5)
    for k in range(40):
        x = r.uniform(80, 1000); y = r.uniform(620, 1060)
        tw = 3 + 2 * math.sin(t * 3 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    sea(A, 1220, t, rows=3, amp=6)
    zhenghe(A, 360, 1220, 200, dir=1, arm=150, layer='ink')
    A.d['ink'].rectangle((420, 1220 - 330, 470, 1220 - 280), outline=255, width=4)
    A.d['ink'].line((440, 1220 - 300, 760, 900), fill=180, width=2)
    A.d['gold'].ellipse((750, 890, 770, 910), fill=255)
    A.flush(cv)
    stamp(cv, seal('牵星过洋', 44), 800, 1080, t, t - u + P, rot=5)

def art_z_compass_ship(A, cv, t, u):
    sea(A, 1260, t, rows=3, amp=6)
    A.d['mid'].rectangle((200, 1100, 880, 1260), fill=200)
    zhenghe(A, 280, 1100, 140, dir=1, arm=60, layer='ink')
    compass(A, 600, 1040, 140, 3, -1.2 + 0.4 * math.sin(t * 1.5), p=1.0)

def art_z_calicut(A, cv, t, u):
    for x in (120, 960):
        palm(A, x, 980, t)
    sea(A, 1270, t, rows=2, amp=5)
    for k in range(3):
        dome(A, 360 + k * 180, 1260, 120, 120, layer='mid')
    treasure_ship(A, lerp(1200, 800, ease_out(u / (3 * P))), 1290, 120, t, sails=5)
    A.flush(cv)
    stamp(cv, seal('古里', 54), 300, 940, t, t - u + P)

def art_z_stele(A, cv, t, u):
    for x in (160, 920):
        palm(A, x, 1000, t)
    ground(A, GROUND)
    rise = ease_out(u / (1.5 * P))
    A.d['mid'].rounded_rectangle((440, GROUND - 400 * rise, 640, GROUND), radius=30, fill=255)
    A.d['ink'].rounded_rectangle((440, GROUND - 400 * rise, 640, GROUND), radius=30, outline=255, width=6)
    A.flush(cv)
    if rise > 0.9:
        type_in(cv, text_img('其国去中国十万余里', SERIF, 36, INK, 'Black', bleed=False, vertical=True), 540, GROUND - 200, t, t - u + 1.5 * P, 0.6)

# ================================================================ 第三回 七下西洋
VOY = [('一下', 1405, (720, 1180)), ('二下', 1407, (660, 1080)), ('三下', 1409, (560, 1140)), ('四下', 1413, (400, 1020)),
       ('五下', 1417, (300, 1160)), ('六下', 1421, (220, 1060)), ('七下', 1431, (160, 960))]
def scene_voyages(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 7)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    A.d['ocean'].rectangle((80, 820, 1000, 1400), fill=90)
    A.d['mid'].polygon([(820, 820), (1000, 820), (1000, 1400), (900, 1300), (860, 1100)], fill=220)
    A.d['mid'].polygon([(380, 1240), (460, 1180), (480, 1300), (420, 1380)], fill=220)
    A.d['mid'].polygon([(80, 820), (300, 820), (220, 1000), (80, 1100)], fill=220)
    A.d['mid'].polygon([(80, 1200), (180, 1180), (200, 1400), (80, 1400)], fill=220)
    sx, sy = 880, 1080
    for i, (nm, yr, (x, y)) in enumerate(VOY):
        p = ease_out((t - bt(c[0] + i)) / 0.4)
        if p > 0:
            pts = [(lerp(sx, x, f), lerp(sy, y, f) + 40 * math.sin(math.pi * f) * (1 if i % 2 else -1)) for f in np.linspace(0, p, 20)]
            A.d['red' if i == 6 else 'ink'].line(pts, fill=230 if i == 6 else 160, width=5)
    A.flush(cv)
    stamp(cv, seal('南京', 40, INK), sx, sy, t, s0)
    for i, (nm, yr, (x, y)) in enumerate(VOY):
        if t >= bt(c[0] + i) + 0.3:
            stamp(cv, seal(nm, 38, ZHU if i == 6 else OCEAN), x, y, t, bt(c[0] + i) + 0.3)
    if 0 <= idx < 7 and not gather:
        nm, yr, _ = VOY[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · 第{cn_num(idx + 1)}次下西洋', SERIF, 46, OCEAN, 'Black', bleed=False, spacing=4), W / 2, 1470, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '七下西洋', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '二十八年', BRUSH, 160, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
    fx.flush(cv)
    if gather:
        paste(cv, text_img('三十余国 · 最远到达东非', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1470, 1, clamp((t - gather_t) / 0.3))

def art_z_pirate(A, cv, t, u):
    sea(A, 1200, t, rows=4, amp=8)
    for k in range(3):
        boat(A, 760 + k * 100, 1250 + (k % 2) * 20, 70, t + k, sail=True)
    treasure_ship(A, lerp(-100, 380, ease_out(u / (2 * P))), 1240, 180, t, sails=6)
    if u > 2 * P:
        for k in range(3):
            flames(A, 760 + k * 100, 1230, 60, 80, t + k, n=2, seed=50 + k, smoke=True)
    A.flush(cv)
    stamp(cv, seal('陈祖义', 46, INK), 860, 960, t, t - u + P, rot=5)

def art_z_ceylon(A, cv, t, u):
    city_wall(A, 520, W - 60, 1120, gate_x=780, label=None, open_=ease_out((u - P) / 0.5))
    for x in (440, 980):
        palm(A, x, 980, t)
    ground(A, GROUND)
    for k in range(5):
        person(A, lerp(-100, 520, ease_out(u / (2 * P))) - k * 90, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, ph=t * 9 + k, layer='ink')
    A.flush(cv)
    stamp(cv, seal('锡兰山', 50), 780, 900, t, t - u + P, rot=5)

def art_z_trade(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((160, 1200, 920, 1230), fill=255)
    goods = [('red', 'ell'), ('gold', 'rect'), ('ocean', 'ell'), ('mid', 'rect')]
    for k in range(int(clamp(u / (2 * P)) * 8)):
        lay, sh = goods[k % 4]
        x = 220 + k * 90
        if sh == 'ell':
            A.d[lay].ellipse((x - 30, 1140, x + 30, 1200), fill=255)
        else:
            A.d[lay].rectangle((x - 30, 1150, x + 30, 1200), fill=255)
    zhenghe(A, 120, GROUND, 200, dir=1, arm=60, layer='ink')
    person(A, 980, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('丝绸 瓷器 换回 香料 宝石', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.5)

def art_z_ambassadors(A, cv, t, u):
    palace(A, 540, 1180, 520, layer='mid')
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 8) + 1
    for k in range(n):
        side = -1 if k % 2 else 1
        x = 540 + side * (140 + (k // 2) * 100)
        person(A, x, GROUND, 140, dir=-side, robe=True, hat=['knot', 'helmet', 'crown'][k % 3], kneel=True, bow=40, arm=70, layer='ink' if k % 2 else 'mid')
    A.flush(cv)
    stamp(cv, seal('万国来朝', 46), 860, 900, t, t - u + P, rot=6)

def art_z_giraffe(A, cv, t, u):
    """8-beat set piece: the 'qilin' (a giraffe from East Africa) is led into the capital; officials bow."""
    ph = u / P
    city_wall(A, 520, W - 60, 1060, gate_x=760, label='北京', open_=1.0)
    ground(A, GROUND)
    x = walk_x(80, 520, u, 5 * P)
    giraffe(A, x, GROUND, 260, dir=1, ph=t * 4 if ph < 5 else 0, layer='ink')
    person(A, x + 130, GROUND, 170, dir=1, robe=True, hat='knot', ph=t * 4 if ph < 5 else None, arm=-10, layer='ink')
    if ph >= 5:
        for k in range(4):
            person(A, 680 + k * 80, GROUND, 140, dir=-1, robe=True, hat='crown', kneel=True, bow=lerp(0, 50, ease_out((u - 5 * P - k * 0.1) / 0.4)), arm=70, layer='mid')
    A.flush(cv)
    if ph >= 2:
        type_in(cv, text_img('麒麟', BRUSH, 120, GILD), 300, 900, t, t - u + 2 * P, 0.4)
    if ph >= 6.5:
        stamp(cv, seal('祥瑞', 54), 860, 860, t, t - u + 6.5 * P, rot=6)

def art_z_africa(A, cv, t, u):
    for k, (y0, amp) in enumerate(((1300, 50), (1360, 40))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + k)) for x in range(60, W - 59, 10)]
        A.d['gold' if k == 0 else 'mid'].polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=170)
    for x in (200, 820):
        A.d['ink'].line((x, GROUND - 40, x, 1080), fill=255, width=12)
        A.d['ink'].chord((x - 160, 1000, x + 160, 1120), 180, 360, fill=255)
    sea(A, 1380, t, rows=1, amp=4)
    treasure_ship(A, lerp(1200, 620, ease_out(u / (3 * P))), 1400, 100, t, sails=5)
    A.flush(cv)
    stamp(cv, seal('麻林', 50), 540, 940, t, t - u + P)

def art_z_mecca(A, cv, t, u):
    for k, (y0, amp) in enumerate(((1300, 50), (1360, 40))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + k)) for x in range(60, W - 59, 10)]
        A.d['wash' if k == 0 else 'mid'].polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=200)
    A.d['ink'].rectangle((440, 1080, 640, 1300), fill=255)
    A.d['gold'].rectangle((440, 1130, 640, 1150), fill=255)
    for k in range(6):
        a = k * math.pi / 3 + t * 0.4
        person(A, 540 + 240 * math.cos(a), 1320 + 30 * math.sin(a), 90, dir=1, robe=True, hat='knot', arm=20, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('随行者远赴天方', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.5)

# ================================================================ 第四回 风波
def art_z_yongle_dies(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    tent(A, 540, GROUND - 10, 520, 420, layer='mid')
    lt = clamp(1 - (u - P) / 0.6)
    lantern(A, 540, 1100, t, 0, size=int(22 * lt) + 2)
    A.flush(cv)
    stamp(cv, seal('永乐崩', 50, INK), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_z_halt(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out((u - 0.5) / 0.4)), layer='mid')
    for k in range(3):
        person(A, 180 + k * 110, GROUND, 190, dir=1, robe=True, hat='crown', bow=30, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('罢西洋', 50, INK), 540, 940, t, t - u + P)

def art_z_nanjing(A, cv, t, u):
    city_wall(A, 60, W - 60, 1120, gate_x=540, label='南京', layer='mid')
    ground(A, GROUND)
    zhenghe(A, 540, GROUND, 230, dir=1, arm=-10, layer='ink')
    A.flush(cv)
    stamp(cv, seal('南京守备', 46), 860, 900, t, t - u + P, rot=5)

def art_z_baoen(A, cv, t, u):
    rise = ease_out(u / (3 * P))
    for k in range(9):
        y = GROUND - k * 70
        if k > rise * 9: break
        w = 180 - k * 14
        A.d['ink'].rectangle((540 - w / 2, y - 60, 540 + w / 2, y), fill=255)
        A.d['ink'].polygon([(540 - w / 2 - 30, y - 60), (540 + w / 2 + 30, y - 60), (540 + w / 2, y - 76), (540 - w / 2, y - 76)], fill=255)
        A.d['gold'].rectangle((540 - 10, y - 50, 540 + 10, y - 20), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('大报恩寺', 46), 860, 900, t, t - u + P, rot=5)

def art_z_xuande(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((u - 0.5) / 0.4)), layer='mid')
    zhenghe(A, 380, GROUND, 250, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('再下西洋', 46), 380, 920, t, t - u + P, rot=-5)

def art_z_old(A, cv, t, u):
    sea(A, 1260, t, rows=3, amp=6)
    A.d['mid'].rectangle((200, 1120, 880, 1260), fill=200)
    zhenghe(A, 540, 1120, 200, dir=-1, bow=20, arm=20, layer='ink')
    A.flush(cv)
    paste(cv, text_img('年过六旬', SERIF, 50, OCEAN, 'Black', bleed=False, spacing=6), W / 2, 900, 1, clamp(u / 0.3))

# ================================================================ 第五回 归途
def art_z_seventh(A, cv, t, u):
    sun(cv, 540, lerp(980, 1180, ease_out(u / (4 * P))), 180, GILD, 110)
    sea(A, 1200, t, rows=4, amp=8)
    for k in range(5):
        treasure_ship(A, 160 + k * 200, 1230 + (k % 2) * 30, 70, t + k, sails=5, layer='mid')

def art_z_storm(A, cv, t, u):
    for k in range(50):
        q = (t * 1.4 + k / 50) % 1
        x = 80 + (k * 19) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 14, y + 40), fill=200, width=2)
    sea(A, 1160, t, rows=5, amp=26, speed=4)
    treasure_ship(A, 540, 1220, 220, t * 2, sails=6)
    if int(t * 2) % 3 == 0:
        A.d['wash'].line((700, 620, 760, 760, 720, 780, 800, 960), fill=255, width=10)

def art_z_death(A, cv, t, u):
    r = random.Random(9)
    for k in range(40):
        x = r.uniform(80, 1000); y = r.uniform(620, 1060)
        tw = 3 + 2 * math.sin(t * 3 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)
    sea(A, 1220, t, rows=3, amp=4, speed=0.8)
    treasure_ship(A, 540, 1250, 220, t, sails=7)
    lt = clamp(1 - (u - 1.5 * P) / 0.6)
    if lt > 0:
        lantern(A, 540, 1040, t, 0, size=int(20 * lt) + 2)
    A.flush(cv)
    stamp(cv, seal('古里', 50, INK), 860, 900, t, t - u + P, rot=6)

def art_z_tomb(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (420, 1000), (660, 1000), (960, GROUND)], fill=200)
    A.d['ink'].chord((420, 1180, 660, GROUND + 80), 180, 360, fill=255)
    for k in range(28):
        A.d['ink'].rectangle((300 + k * 18, GROUND - 40 - (k % 4) * 0, 310 + k * 18, GROUND), fill=255) if k % 4 == 0 else None
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('牛首山', 50), 540, 900, t, t - u + P)
    type_in(cv, text_img('衣冠冢', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1460, t, t - u + 1.5 * P, 0.4)

def art_z_burned(A, cv, t, u):
    for k in range(int(clamp(u / (1.5 * P)) * 10)):
        A.d['mid'].rectangle((360, GROUND - 20 - k * 22, 720, GROUND - 4 - k * 22), fill=255)
    flames(A, 540, GROUND, 400, 300 * ease_out((u - 1.5 * P) / 0.6), t, n=7, seed=21, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('航海档案', 46, INK), 860, 900, t, t - u + P, rot=6)

def art_z_age(A, cv, t, u):
    sea(A, 1200, t, rows=4, amp=6)
    treasure_ship(A, 360, 1240, 200, t, sails=7)
    for k in range(3):
        x = lerp(1200, 820, ease_out(u / (3 * P))) + k * 70
        A.d['wash'].polygon([(x - 50, 1230), (x + 50, 1230), (x + 40, 1250), (x - 40, 1250)], fill=255)
        A.d['wash'].line((x, 1230, x, 1130), fill=255, width=3)
    A.flush(cv)
    type_in(cv, text_img('早于哥伦布八十七年', SERIF, 50, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.5)

def art_z_legacy(A, cv, t, u):
    sea(A, 1160, t, rows=5, amp=10, speed=1.5)
    fo = font(BRUSH, 380)
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength('海') / 2, 720), '海', font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)

# ================================================================ script
CHAPTERS = {16: ('第一回', '马三保'), 48: ('第二回', '宝船出海'), 80: ('第三回', '七下西洋'),
            112: ('第四回', '盛世远航'), 144: ('第五回', '魂归大海')}

CARDS = [
    C(0, 2, 'hook', 'num', num='七下西洋', line='二十八年', art=art_z_hook_seven),
    C(2, 4, 'hook', 'num', num='宝船', line='世界最大木帆船', art=art_z_hook_ship),
    C(4, 6, 'hook', 'num', num='三十余国', line='最远到达东非', art=art_z_hook_world),
    C(6, 8, 'hook', 'num', num='宦官', line='却成了航海家', art=art_z_hook_eunuch),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 马三保
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1371, main='生于昆阳', sub='云南回族 · 本姓马 小名三保', note='世为云南昆阳州人', art=art_z_birth),
    C(22, 26, 'works', 'card', year=1378, main='祖父朝圣', sub='家族远行万里 · 见识天下', note='祖父与父亲 皆尝朝天方', art=art_z_hajj),
    C(26, 30, 'night', 'card', year=1381, main='家破被俘', sub='明军平云南 · 十岁被俘', note='父战死 子没入宫', art=art_z_captured),
    C(30, 34, 'court', 'card', year=1385, main='燕王府', sub='入燕王朱棣府中为侍从', note='燕王见而奇之', art=art_z_palace_boy),
    C(34, 38, 'court', 'card', year=1390, main='深得信任', sub='随燕王征战北疆', note='有智略 知兵习战', art=art_z_prince),
    C(38, 42, 'war', 'card', year=1399, main='靖难之役', sub='郑村坝之战 · 屡立战功', note='燕王起兵 南下夺位', art=art_z_jingnan),
    C(42, 46, 'empire', 'card', year=1404, main='御赐郑姓', sub='马和改名郑和', note='以郑村坝之功 赐姓郑', art=art_z_surname),
    C(46, 48, 'court', 'card', year=1404, main='内官监太监', sub='四品 · 宦官之首', art=art_z_eunuch_chief),
    # ---- 第二回 宝船出海
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'works', 'card', year=1405, main='龙江造船', sub='南京造宝船 · 举国之力', note='宝船厂', art=art_z_shipyard),
    C(54, 58, 'works', 'card', year=1405, main='宝船', sub='九桅十二帆 · 世界第一', note='大者长四十四丈 阔十八丈', art=art_z_size),
    C(58, 62, 'empire', 'card', year=1405, main='两万七千人', sub='官兵 水手 医官 翻译', note='将士卒二万七千八百余人', art=art_z_crew),
    C(62, 70, 'works', 'card', year=1405, main='刘家港启航', sub='首次下西洋 · 浩浩荡荡', note='自苏州刘家河泛海', art=art_z_launch),
    C(70, 74, 'night', 'card', year=1405, main='牵星过洋', sub='夜观星辰 · 测定方位', note='观星斗高低 度量远近', art=art_z_stars),
    C(74, 78, 'works', 'card', year=1405, main='针路', sub='罗盘定向 · 绘成航海图', note='郑和航海图', art=art_z_compass_ship),
    C(78, 80, 'works', 'card', year=1406, main='抵达古里', sub='印度西南海岸', art=art_z_calicut),
    # ---- 第三回 七下西洋
    C(80, 82, 'empire', 'chapter'),
    C(82, 90, 'works', 'voyages'),
    C(90, 94, 'war', 'card', year=1407, main='生擒海盗', sub='旧港海盗陈祖义 · 被擒解京', note='杀贼党五千余人', art=art_z_pirate),
    C(94, 98, 'war', 'card', year=1411, main='锡兰山之战', sub='国王劫船 · 郑和反攻其城', note='生擒其王', art=art_z_ceylon),
    C(98, 102, 'life', 'card', year=1413, main='互通有无', sub='赏赐与贸易并行', note='以中国之物 易彼之宝', art=art_z_trade),
    C(102, 106, 'empire', 'card', year=1416, main='使节来朝', sub='十余国使者 · 随船入明', note='诸番使臣 络绎不绝', art=art_z_ambassadors),
    C(106, 112, 'works', 'card', year=1424, main='碑立古里', sub='在古里立碑记事', note='其国去中国十万余里', art=art_z_stele),
    # ---- 第四回 盛世远航
    C(112, 114, 'empire', 'chapter'),
    C(114, 122, 'empire', 'card', year=1414, main='麒麟入京', sub='东非长颈鹿 · 被视为麒麟', note='群臣稽首称贺', art=art_z_giraffe),
    C(122, 126, 'works', 'card', year=1418, main='远达非洲', sub='麻林 木骨都束 · 东非海岸', note='最远抵达今肯尼亚', art=art_z_africa),
    C(126, 130, 'life', 'card', year=1432, main='天方', sub='随行者到达麦加', note='马欢 瀛涯胜览', art=art_z_mecca),
    C(130, 134, 'death', 'card', year=1424, main='永乐驾崩', sub='最大的支持者离去', note='北征途中 崩于榆木川', art=art_z_yongle_dies),
    C(134, 138, 'court', 'card', year=1424, main='停罢下西洋', sub='群臣以耗费巨大为由反对', note='劳民伤财', art=art_z_halt),
    C(138, 142, 'court', 'card', year=1425, main='南京守备', sub='留守南京 · 修大报恩寺', note='督造九层琉璃塔', art=art_z_baoen),
    C(142, 144, 'empire', 'card', year=1430, main='宣德再启', sub='皇帝命其再下西洋', art=art_z_xuande),
    # ---- 第五回 魂归大海
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=1431, main='第七次远航', sub='年过六旬 · 再度出海', note='最后一次', art=art_z_old),
    C(150, 154, 'night', 'card', year=1432, main='风暴', sub='惊涛骇浪 · 舟师无恙', note='天妃护佑', art=art_z_storm),
    C(154, 158, 'death', 'card', year=1433, main='卒于古里', sub='归途中病逝 · 年六十二', note='一说海葬 一说归葬', art=art_z_death),
    C(158, 162, 'death', 'card', year=1433, main='牛首山', sub='南京牛首山 · 衣冠冢', note='至今尚存', art=art_z_tomb),
    C(162, 166, 'fate', 'card', year=1477, main='档案焚毁', sub='后世官员焚毁航海档案', note='旧案虽有 亦当毁之', art=art_z_burned),
    C(166, 170, 'end', 'card', year=1492, main='早于哥伦布', sub='大航海时代之前 · 中国已航行万里', note='比哥伦布早八十七年', art=art_z_age),
    C(170, 999, 'end', 'end'),
]
# art_z_seventh / art_z_legacy kept in the episode library (ending backdrop uses art_z_legacy)

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
ALL = (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg, Yf, Wx, Qj)
for mod in ALL:
    mod.CHAPTERS = CHAPTERS
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
for mod in (G,) + ALL:
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=OCEAN + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, GILD, 120)
        sea(A, 1300, t_, rows=3, amp=6)
        zhenghe(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('郑和 · 本姓马', SERIF, 46, OCEAN, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '郑和', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('三保', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1371 — 1433', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '伟大航海？', BRUSH, 120, OCEAN, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '劳民伤财？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    art_z_legacy(A, cv, t, u)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.25)
    fx = Art()
    chars_in(cv, fx, '扬帆万里', BRUSH, 220, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('三保', 60), W / 2 + 380, 540, t, END + 0.45, rot=6)
    type_in(cv, text_img('中国本可以率先走向海洋', SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('却在他之后 关上了大门', SERIF, 52, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '若坚持远航', BRUSH, 100, OCEAN, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('世界会不同吗？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=OCEAN + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 245, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=GILD + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 王阳明', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, voyages=scene_voyages, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾柒集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('比哥伦布早八十七年 · 他航行到了哪里？', SERIF, 36, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 340, 335, W / 2 + 340, 335), fill=OCEAN + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, OCEAN, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=OCEAN + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=GILD + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(max(1, int(round(yr - BORN)))) + '岁' if yr <= DIED + 0.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=OCEAN + (255,))
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
    if ff.returncode != 0: sys.exit(1)
    print('done', out)
