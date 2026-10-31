# 千古人物志 · 第贰集 · 汉武帝刘彻 —— 长版（93.75 秒，五回章回体）
# 复用第壹集（秦始皇长版）的引擎、音乐网格与全部动效，只换故事、插画与字幕。
import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw
import render_long as L            # sets up beat grid / music / effects
import render_gufeng as G
import render_story as S
import render_full as F
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, rotp, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx, year_line
from render_long import C, rider, city_wall, enso, note_in, stage, DIM, P

BORN, DIED = 156, 87
END_BEAT = 170

# per-episode watermarks
for k, wm in dict(hook='汉', life='彻', court='儒', night='夜', war='戰', empire='盛', works='远',
                  fate='悔', death='逝', end='武').items():
    G.THEMES[k]['wm'] = wm
G.THEMES['works']['sun'] = ((200, 150, 60), 220, (W * 0.5, 820))
G.draw_wall = lambda *a: None
G.base_bg.cache_clear()

# ================================================================ new figures
def camel(A, x, y, s, dir=1, ph=0.0, layer='ink', load=True):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    d.polygon([T(*p) for p in ellipse_pts(0, 0.66, 0.40, 0.14)], fill=255)
    for hu in (-0.16, 0.12):
        d.polygon([T(*p) for p in ellipse_pts(hu, 0.80, 0.11, 0.12)], fill=255)
    d.polygon([T(0.34, 0.70), T(0.44, 0.62), T(0.62, 0.96), T(0.54, 1.00)], fill=255)
    d.polygon([T(0.52, 1.0), T(0.76, 0.98), T(0.76, 0.92), T(0.56, 0.93)], fill=255)
    for hu, off in ((0.26, 0.0), (0.18, 1.6), (-0.24, 3.1), (-0.32, 4.7)):
        a = 0.35 * math.sin(ph + off)
        knee = (hu + 0.28 * math.sin(a), 0.58 - 0.28)
        foot = (knee[0] + 0.28 * math.sin(a * 0.5), 0.02)
        d.line([T(hu, 0.58), T(*knee)], fill=255, width=max(2, int(0.05 * s)))
        d.line([T(*knee), T(*foot)], fill=255, width=max(2, int(0.04 * s)))
    if load:
        A.d['mid'].rectangle((min(T(-0.3, 0.9)[0], T(0.25, 0.9)[0]), y - 1.02 * s,
                              max(T(-0.3, 0.9)[0], T(0.25, 0.9)[0]), y - 0.86 * s), fill=255)

def coin(A, x, y, r, rot=0.0, layer='ink'):
    rx = max(2, abs(r * math.cos(rot)))
    A.d[layer].ellipse((x - rx, y - r, x + rx, y + r), fill=255)
    h = r * 0.32
    A.d[layer].rectangle((x - h * rx / r, y - h, x + h * rx / r, y + h), fill=0)

# ================================================================ new scenes
def art_dream_sun(A, cv, t, u):
    cy = lerp(700, 1150, ease_out(u / (3 * P)))
    sun(cv, 540, cy, lerp(170, 90, ease_out(u / (3 * P))), ZHU, 160)
    for k in range(12):
        a = t * 0.6 + k * math.pi / 6
        A.d['wash'].line((540 + 120 * math.cos(a), cy + 120 * math.sin(a), 540 + 260 * math.cos(a), cy + 260 * math.sin(a)), fill=255, width=8)
    ground(A, GROUND)
    A.d['mid'].rectangle((300, 1260, 780, 1300), fill=255)
    person(A, 560, 1260, 220, dir=-1, female=True, kneel=True, bow=10, arm=60, layer='ink')
    for k in range(4):
        y = 820 + k * 70
        x = (t * 60 + k * 300) % (W + 500) - 300
        A.d['wash'].line((x, y, x + 300, y), fill=255, width=18)

def art_golden_house(A, cv, t, u):
    sun(cv, 540, 980, 260, (210, 160, 60), 120)
    palace(A, 540, 1290, 520, layer='mid')
    A.d['wash'].rectangle((60, 1290, W - 60, GROUND + 20), fill=255)
    person(A, 440, GROUND, 150, dir=1, hat='knot', arm=lerp(10, 60, ease_out((u - P) / 0.3)), layer='ink')
    person(A, 640, GROUND, 140, dir=-1, female=True, arm=20, layer='ink')
    for k in range(14):
        q = (u * 0.5 + k / 14) % 1
        x = 160 + k * 55 + 20 * math.sin(t + k); y = lerp(720, 1350, q)
        A.d['red'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=int(200 * (1 - q)))

def art_scroll(text):
    def f(A, cv, t, u):
        p = ease_out(u / 0.6)
        w = 760 * p
        x0 = 540 - w / 2; x1 = 540 + w / 2
        A.d['mid'].rectangle((x0, 860, x1, 1300), fill=150)
        A.d['ink'].rectangle((x0 - 20, 840, x0, 1320), fill=255)
        A.d['ink'].rectangle((x1, 840, x1 + 20, 1320), fill=255)
        fo = font(BRUSH, 190)
        tw = fo.getlength(text)
        A.d['ink'].text((540 - tw / 2, 960), text, font=fo, fill=255)
        A.d['ink'].rectangle((0, 0, x0, H), fill=0); A.d['ink'].rectangle((x1, 0, W, H), fill=0)
        A.d['ink'].rectangle((x0 - 20, 840, x0, 1320), fill=255)
        A.d['ink'].rectangle((x1, 840, x1 + 20, 1320), fill=255)
        if p > 0.9:
            A.flush(cv)
            stamp(cv, seal('建元', 50), 540 + 300, 1230, t, t - u + 0.6)
    return f

def art_grandma(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(560, GROUND), (980, GROUND), (950, 1310), (590, 1310)], fill=255)
    person(A, 790, 1310, 180, dir=-1, hat='crown', arm=30, layer='ink')
    grow = ease_out(u / (2 * P))
    big = lerp(380, 540, grow)
    person(A, 330, GROUND, big * 1.22, dir=1, female=True, arm=lerp(20, 75, grow), layer='wash')
    person(A, 300, GROUND, big, dir=1, female=True, arm=lerp(10, 70, grow), layer='ink')
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('黄老', 50), 800, 980, t, t - u + 2 * P)

def art_zhangqian(A, cv, t, u):
    sun(cv, 820, 860, 110, (200, 150, 60), 120)
    d = A.d['mid']
    for k, (y0, amp, ph) in enumerate(((1300, 60, 0.4), (1370, 40, 2.0))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + ph + t * 0.05)) for x in range(60, W - 59, 10)]
        (A.d['wash'] if k == 0 else d).polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=255)
    x = lerp(160, 620, ease_out(u / (4 * P)))
    horse(A, x, 1360, 200, 1, t * 5, layer='ink')
    person(A, x - 10, 1360 - 0.66 * 200, 120, dir=1, arm=150, layer='ink')
    A.d['ink'].line((x + 20, 1180, x + 50, 900), fill=255, width=6)
    for k in range(3):
        A.d['red'].ellipse((x + 40 - 10, 920 + k * 26, x + 60 - 10, 940 + k * 26), fill=255)
    camel(A, x - 260, 1360, 170, 1, t * 5, layer='mid')

def art_ambush(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].polygon([(60, GROUND), (200, 1150), (420, 1180), (560, GROUND)], fill=255)
    for k in range(5):
        hx = 130 + k * 80
        peek = 1170 + 12 * math.sin(t * 3 + k)
        A.d['ink'].ellipse((hx - 16, peek - 16, hx + 16, peek + 16), fill=255)
        A.d['ink'].line((hx + 10, peek, hx + 30, peek - 120), fill=255, width=4)
    turn = u > 2 * P
    v = u - 2 * P
    for k in range(3):
        if not turn:
            x = lerp(W + 100, 700, ease_out(u / (2 * P))) + k * 120
            rider(A, x, GROUND - k * 20, 170, -1, t * 12 + k, layer='ink' if k == 0 else 'mid')
        else:
            x = lerp(700, W + 300, ease_out(v / (2 * P))) + k * 120
            rider(A, x, GROUND - k * 20, 170, 1, t * 14 + k, layer='ink' if k == 0 else 'mid')
    if turn:
        A.flush(cv)
        stamp(cv, seal('计泄', 50), 820, 900, t, t - u + 2 * P)

def art_split(top_ch, mid_ch, low_ch):
    def f(A, cv, t, u):
        d = A.d['ink']; st = t - u
        p = ease_out(u / 0.35)
        top = (540, 820)
        mids = [(250, 1030), (540, 1030), (830, 1030)]
        lows = [(x + dx, 1250) for x, _ in mids for dx in (-80, 80)]
        for m in mids:
            d.line((top[0], top[1], lerp(top[0], m[0], p), lerp(top[1], m[1], p)), fill=255, width=5)
        q = ease_out((u - 0.3) / 0.4)
        for i, l in enumerate(lows):
            m = mids[i // 2]
            if q > 0: d.line((m[0], m[1], lerp(m[0], l[0], q), lerp(m[1], l[1], q)), fill=255, width=4)
        A.flush(cv)
        stamp(cv, seal(top_ch, 90), top[0], top[1], t, st)
        for m in mids: stamp(cv, seal(mid_ch, 56), m[0], m[1], t, st + P)
        for l in lows: stamp(cv, seal(low_ch, 40), l[0], l[1], t, st + 2 * P)
    return f

def art_furnace(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].polygon([(380, 1150), (700, 1150), (660, 1330), (420, 1330)], fill=255)
    A.d['ink'].rectangle((360, 1130, 720, 1160), fill=255)
    for lx in (420, 640):
        A.d['ink'].rectangle((lx, 1330, lx + 24, GROUND), fill=255)
    flames(A, 540, GROUND - 4, 260, 110, t, n=6, seed=2, smoke=False)
    for k in range(5):
        kk = (t * 60 + k * 50) % 260
        A.d['wash'].ellipse((480 + k * 25 - 20, 1100 - kk - 20, 480 + k * 25 + 20, 1100 - kk + 20), fill=255)
    for k in range(3):
        x = (t * 80 + k * 360) % (W + 200) - 100
        person(A, x, GROUND, 170, dir=1, robe=False, ph=t * 7 + k, load=True, arm=160, layer='mid')
    person(A, 820, GROUND, 220, dir=-1, robe=False, arm=lerp(120, 60, abs(math.sin(t * 4))), layer='ink')

def art_coins(A, cv, t, u):
    ground(A, GROUND)
    for k in range(18):
        q = (u * 0.7 + k / 18) % 1
        x = 120 + (k * 53) % 840; y = lerp(650, GROUND - 30, q ** 1.4)
        coin(A, x, y, 30, rot=t * 5 + k, layer='ink' if k % 3 else 'mid')
    for k in range(int(clamp(u / (4 * P)) * 10)):
        coin(A, 300 + (k % 5) * 110, GROUND - 26 - (k // 5) * 20, 34, layer='ink')
    A.flush(cv)
    if u > P:
        stamp(cv, seal('五铢', 64), 800, 1000, t, t - u + P)

def art_school(A, cv, t, u):
    ground(A, GROUND)
    palace(A, 540, 1180, 420, layer='mid')
    person(A, 540, GROUND, 240, dir=-1, arm=lerp(30, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    for k in range(3):
        for side in (-1, 1):
            x = 540 + side * (170 + k * 120)
            person(A, x, GROUND, 170 - k * 10, dir=-side, kneel=True, bow=20 + 15 * math.sin(t * 2 + k), arm=80,
                   layer='ink' if k == 0 else 'mid')

def art_huo(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = (k * 120 - t * 900) % (W + 200) - 100
        A.d['wash'].line((x, 1050 + k * 30, x + 180, 1050 + k * 30), fill=255, width=4)
    lead = lerp(-200, 640, ease_out(u / (2 * P)))
    rider(A, lead, GROUND, 250, 1, t * 15, layer='ink', spear=True)
    for k in range(4):
        rider(A, lead - 260 - k * 180, 1340 - k * 10, 150, 1, t * 14 + k, layer='mid', spear=True)
    if u > 4 * P:
        v = u - 4 * P
        flag(A, 860, lerp(1500, GROUND, ease_out(v / 0.3)), 460, t, w=200)

def art_four(A, cv, t, u):
    d = A.d['mid']
    pts = [(160, 1200), (300, 1120), (480, 1090), (680, 1050), (900, 980), (950, 1040), (700, 1140), (480, 1190), (300, 1250), (160, 1280)]
    d.polygon(pts, fill=150)
    A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.flush(cv)
    for i, (name, (x, y)) in enumerate(zip(('武威', '张掖', '酒泉', '敦煌'), ((830, 1030), (620, 1100), (420, 1150), (230, 1220)))):
        stamp(cv, seal(name, 44), x, y - 70, t, t - u + i * 0.22)

def art_flee(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = lerp(560, 1100, ease_out(u / (2 * P))) + k * 70
        rider(A, x, 1320 - k * 10, 110 - k * 8, 1, t * 12 + k, layer='mid')
    for k in range(6):
        rr = 30 + k * 12
        x = lerp(500, 980, ease_out(u / (2 * P))) - k * 50
        A.d['wash'].ellipse((x - rr, 1300 - rr, x + rr, 1300 + rr), fill=255)
    rider(A, 320, GROUND, 230, 1, 0, layer='ink', spear=True, moving=False)
    flag(A, 200, GROUND, 380, t, w=150)

DIRS = [('北', '匈奴', (540, 820)), ('西', '西域', (200, 1040)), ('南', '南越', (560, 1340)),
        ('东', '朝鲜', (900, 960)), ('西南', '夷', (320, 1290))]
def scene_expand(cv, t, c, k):
    s0 = bt(c[0])
    A = Art(); beat_fx(A, t)
    grow = 1 + 0.35 * ease_out((t - s0) / (5 * P))
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 230 * grow + 30 * math.sin(a * 3 + 1) + 18 * math.sin(a * 7)
        pts.append((560 + r * math.cos(a), 1060 + r * math.sin(a) * 0.8))
    A.d['wash'].polygon(pts, fill=200); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    for i, (dname, place, (x, y)) in enumerate(DIRS):
        p = ease_out((t - bt(c[0] + i)) / 0.3)
        if p > 0:
            A.d['red'].line((560, 1060, lerp(560, x, p), lerp(1060, y, p)), fill=255, width=9)
    A.flush(cv)
    gather = t >= bt(c[0] + 6)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '开疆拓土', BRUSH, 150, INK, W / 2, 420, t, s0, stagger=0.06, seed=104)
    stamp(cv, seal('汉', 110 if not gather else 240), 560, 1060, t, s0 if not gather else bt(c[0] + 6))
    for i, (dname, place, (x, y)) in enumerate(DIRS):
        if t >= bt(c[0] + i) and not gather:
            stamp(cv, seal(place, 44, INK), x, y, t, bt(c[0] + i) + 0.15)
    idx = int(k - c[0])
    if 0 <= idx < 5:
        lab = text_img(f'{DIRS[idx][0]} · {DIRS[idx][1]}', SERIF, 60, ZHU, 'Black', bleed=False, spacing=6)
        ink_in(cv, lab, W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    if gather:
        chars_in(cv, fx, '奠定', BRUSH, 170, INK, W / 2, 450, t, bt(c[0] + 6), stagger=0.08, seed=110)
        chars_in(cv, fx, '中华版图', BRUSH, 170, ZHU, W / 2, 1420, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

def art_fleet(A, cv, t, u):
    for k in range(3):
        x = lerp(-200 - k * 220, 760 - k * 260, ease_out(u / (4 * P)))
        boat(A, x, 1290 + k * 22, 220 - k * 30, t + k)
    waves(A, 1300, t, rows=4, amp=14, speed=3)
    flag(A, 900, 1150, 260, t, w=110)

def art_west(A, cv, t, u):
    sun(cv, 860, 900, 110, (200, 150, 60), 120)
    A.d['wash'].polygon([(x, 1320 - 50 * math.sin(x * 0.007 + 1)) for x in range(60, W - 59, 10)] + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=255)
    for k in range(4):
        x = (t * 70 + k * 240) % (W + 300) - 200
        camel(A, x, 1380 - k % 2 * 10, 150, 1, t * 5 + k, layer='ink' if k % 2 else 'mid')
    person(A, (t * 70 + 120) % (W + 300) - 200, 1380, 170, dir=1, arm=40, layer='ink')

def art_silk(A, cv, t, u):
    for k in range(3):
        y = 900 + k * 70
        pts = [(x, y + 30 * math.sin(x * 0.012 + t * 2 + k)) for x in range(60, W - 59, 12)]
        A.d['red' if k == 1 else 'mid'].line(pts, fill=255, width=26 - k * 6)
    ground(A, GROUND)
    for k in range(3):
        x = (t * 90 + k * 330) % (W + 300) - 200
        camel(A, x, GROUND, 160, 1, t * 5 + k, layer='ink')

def art_steed(A, cv, t, u):
    ground(A, GROUND)
    for k in range(12):
        x = (k * 97 - t * 1100) % (W + 200) - 100
        A.d['wash'].line((x, 1000 + k * 28, x + 200, 1000 + k * 28), fill=255, width=4)
    horse(A, lerp(250, 560, ease_out(u / 0.6)), GROUND, 420, 1, t * 15, layer='ink')
    for k in range(6):
        q = (t * 1.5 + k / 6) % 1
        A.d['red'].ellipse((420 - q * 260 - 6, 1180 + k * 8 - 6, 420 - q * 260 + 6, 1180 + k * 8 + 6), fill=int(230 * (1 - q)))

def art_calendar(A, cv, t, u):
    cx, cy = 540, 1060
    for r, w in ((300, 8), (230, 5), (150, 5)):
        A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=w)
    for j in range(24):
        a = j * math.pi / 12 + t * 0.4
        A.d['ink'].line((cx + 230 * math.cos(a), cy + 230 * math.sin(a), cx + 300 * math.cos(a), cy + 300 * math.sin(a)), fill=255, width=3)
    a = t * 1.3
    A.d['red'].ellipse((cx + 190 * math.cos(a) - 26, cy + 190 * math.sin(a) - 26, cx + 190 * math.cos(a) + 26, cy + 190 * math.sin(a) + 26), fill=255)
    b = -t * 2.2
    A.d['mid'].ellipse((cx + 120 * math.cos(b) - 18, cy + 120 * math.sin(b) - 18, cx + 120 * math.cos(b) + 18, cy + 120 * math.sin(b) + 18), fill=255)
    A.d['ink'].ellipse((cx - 20, cy - 20, cx + 20, cy + 20), fill=255)

def art_surround(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        x = 440 + k * 60
        person(A, x, GROUND, 190, dir=1 if k % 2 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    for k in range(6):
        a = t * 1.6 + k * math.pi / 3
        x = 540 + 380 * math.cos(a); y = GROUND - 30 + 70 * math.sin(a)
        rider(A, x, y, 150, -1 if math.sin(a) > 0 else 1, t * 13 + k, layer='ink' if math.sin(a) > 0 else 'mid')
    for k in range(6):
        q = (u * 1.3 + k * 0.17) % 1
        arrow(A, lerp(980, 560, q), 900 - 180 * math.sin(math.pi * q), math.atan2(-180 * math.pi * math.cos(math.pi * q), -420), 70)

def art_sima(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].ellipse((220, 980, 560, 1320), fill=200)
    A.d['ink'].rectangle((360, 1260, 380, GROUND), fill=255)
    fh = 44 + 8 * math.sin(t * 17)
    A.d['red'].polygon([(358, 1260), (382, 1260), (374 + 4 * math.sin(t * 9), 1260 - fh), (370, 1260 - fh)], fill=255)
    person(A, 560, GROUND, 240, dir=-1, kneel=True, bow=25, arm=95, layer='ink')
    n = int(clamp(u / (2 * P)) * 7) + 2
    for k in range(n):
        A.d['mid'].rounded_rectangle((680, GROUND - 30 - k * 32, 900, GROUND - 4 - k * 32), radius=12, fill=255)
        A.d['ink'].ellipse((880, GROUND - 30 - k * 32, 904, GROUND - 4 - k * 32), outline=255, width=3)
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('史记', 60), 790, GROUND - 120 - n * 32, t, t - u + 2 * P)

def art_chenglu(A, cv, t, u):
    ground(A, GROUND)
    rise = ease_out(u / (2 * P))
    top = lerp(GROUND, 760, rise)
    A.d['ink'].rectangle((515, min(top + 90, GROUND), 565, GROUND), fill=255)
    person(A, 540, top + 90, 150, dir=1, arm=170, arm2=160, layer='ink')
    A.d['ink'].chord((450, top - 40, 630, top + 20), 0, 180, fill=255)
    for k in range(5):
        q = (t * 0.8 + k / 5) % 1
        y = lerp(560, top - 20, q)
        A.d['mid'].ellipse((540 + (k - 2) * 25 - 6, y - 9, 540 + (k - 2) * 25 + 6, y + 9), fill=255)
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    for k in range(3):
        y = 1000 + k * 70
        x = (t * 60 + k * 330) % (W + 500) - 300
        A.d['wash'].line((x, y, x + 300, y), fill=255, width=20)

def art_wugu(A, cv, t, u):
    palace(A, 540, 1210, 520, layer='mid')
    ground(A, GROUND)
    for k in range(5):
        rise = ease_out((u - k * 0.15) / 0.4)
        if rise <= 0: continue
        x = 180 + k * 180
        y = lerp(GROUND + 120, GROUND - 10, rise)
        A.d['ink'].ellipse((x - 18, y - 120, x + 18, y - 84), fill=255)
        A.d['ink'].rectangle((x - 22, y - 86, x + 22, y), fill=255)
        A.d['ink'].line((x - 50, y - 70, x + 50, y - 70), fill=255, width=10)
        A.d['red'].line((x - 30, y - 40, x + 30, y - 46), fill=255, width=6)
    if u > 2 * P:
        flames(A, 540, 1210, 520, 260 * ease_out((u - 2 * P) / 0.4), t, n=8, seed=11)

def art_luntai(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((300, 1260, 320, GROUND), fill=255)
    fh = 40 + 8 * math.sin(t * 15)
    A.d['red'].polygon([(298, 1260), (322, 1260), (314 + 4 * math.sin(t * 9), 1260 - fh), (310, 1260 - fh)], fill=255)
    person(A, 560, GROUND, 290, dir=-1, hat='crown', kneel=True, bow=lerp(10, 45, ease_out(u / (2 * P))), arm=85, layer='ink')
    p = ease_out((u - P) / 0.6)
    if p > 0:
        A.d['mid'].rectangle((660, 1300, 660 + 260 * p, 1360), fill=255)
        fo = font(BRUSH, 44)
        A.d['ink'].text((680, 1306), '罪己诏'[:max(0, int(p * 3.2))], font=fo, fill=255)

def art_tuogu(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(640, GROUND), (1000, GROUND), (970, 1310), (670, 1310)], fill=255)
    person(A, 830, 1310, 200, dir=-1, hat='crown', kneel=True, bow=10, arm=70, layer='ink')
    x = walk_x(160, 440, u, 2 * P)
    person(A, x, GROUND, 300, dir=1, bow=22, arm=-30, layer='ink')
    person(A, x - 70, GROUND - 230, 110, dir=1, arm=60, layer='ink')
    if u > 2 * P:
        A.flush(cv)
        stamp(cv, seal('托孤', 56), 560, 900, t, t - u + 2 * P, rot=-5)

def art_dusk_palace(A, cv, t, u):
    sun(cv, 540, lerp(1050, 1250, ease_out(u / (4 * P))), 180, (120, 115, 110), 130)
    palace(A, 540, GROUND, 640, layer='ink')
    for k in range(6):
        a = t * 1.4 + k * 1.05
        crow(A, 540 + 330 * math.cos(a), 780 + 70 * math.sin(a), 24, t * 11 + k)

def art_legacy(A, cv, t, u):
    sun(cv, 540, 1050, 260, ZHU, 130)
    fo = font(BRUSH, 520)
    ch = '汉'
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength(ch) / 2, 760), ch, font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    A.im['ink'].paste(Image.fromarray(a.astype(np.uint8)), (0, 0), Image.fromarray(a.astype(np.uint8)))
    ground(A, GROUND)
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 150 + (k % 2) * 20, dir=1 if k < 3 else -1, arm=40, layer='mid')

def art_famine(A, cv, t, u):
    d = A.d['mid']
    for k, (y0, amp, ph) in enumerate(((1300, 50, 0.4), (1370, 30, 2.0))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + ph)) for x in range(60, W - 59, 10)]
        (A.d['wash'] if k == 0 else d).polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=255)
    for k in range(9):   # withered stalks
        x = 120 + k * 105
        A.d['ink'].line((x, GROUND - 40, x + 18, GROUND - 150), fill=255, width=4)
        A.d['ink'].line((x + 18, GROUND - 150, x + 46, GROUND - 120), fill=255, width=3)
    for k in range(3):
        x = walk_x(820 - k * 140, 420 - k * 140, u, 4 * P)
        person(A, x, GROUND, 210 - k * 15, dir=-1, bow=30, arm=20, ph=None, layer='ink' if k == 0 else 'mid')
    for k in range(5):
        a = t * 1.3 + k * 1.26
        crow(A, 540 + 280 * math.cos(a), 860 + 70 * math.sin(a), 22, t * 11 + k)
    if u > P:
        A.flush(cv)
        stamp(cv, seal('户口减半', 48), 820, 950, t, t - u + P, rot=5)

# ================================================================ script
CHAPTERS = {16: ('第一回', '金屋太子'), 48: ('第二回', '独尊儒术'), 80: ('第三回', '北击匈奴'),
            112: ('第四回', '盛世雄主'), 144: ('第五回', '晚年悔悟')}

CARDS = [
    C(0, 2, 'hook', 'num', num='十六岁', line='登基为帝', art=S.art_child_king),
    C(2, 4, 'hook', 'num', num='五十四年', line='雄踞帝位', art=S.art_enthrone),
    C(4, 6, 'hook', 'num', num='封狼居胥', line='匈奴远遁', art=L.art_cavalry),
    C(6, 8, 'hook', 'num', num='罪己诏', line='晚年悔过', art=art_luntai),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 金屋太子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=156, main='梦日入怀', sub='母亲王娡 · 梦见太阳入怀而生', note='王夫人梦日入其怀', art=art_dream_sun),
    C(22, 26, 'life', 'card', year=152, main='金屋藏娇', sub='若得阿娇作妇 · 当作金屋贮之', note='长公主大悦 乃苦要帝 遂成婚焉', art=art_golden_house),
    C(26, 30, 'life', 'card', year=150, main='立为太子', sub='七岁 · 被立为皇太子', note='景帝废栗太子 立胶东王为太子', art=S.art_throne),
    C(30, 34, 'life', 'card', year=141, main='少年天子', sub='十六岁 · 继位为帝', note='景帝崩 太子即皇帝位', art=S.art_enthrone),
    C(34, 38, 'life', 'card', year=140, main='首创年号', sub='建元元年 · 中国第一个年号', note='年号纪年 自此而始', art=art_scroll('建元')),
    C(38, 42, 'court', 'card', year=139, main='祖母掣肘', sub='窦太皇太后好黄老 · 新政夭折', note='赵绾 王臧 皆下狱自杀', art=art_grandma),
    C(42, 46, 'court', 'card', year=138, main='张骞出塞', sub='出使西域 · 一去十三年', note='持汉节不失', art=art_zhangqian),
    C(46, 48, 'night', 'card', year=137, main='隐忍待时', sub='韬光养晦 · 静待亲政', art=L.art_candle),
    # ---- 第二回 独尊儒术
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=135, main='亲掌大权', sub='窦太后崩 · 二十二岁乾纲独断', note='自此 政由己出', art=L.art_capping),
    C(54, 58, 'court', 'card', year=134, main='独尊儒术', sub='采纳董仲舒 · 罢黜百家', note='诸不在六艺之科 孔子之术者 皆绝其道', art=L.art_lisi),
    C(58, 62, 'court', 'card', year=133, main='马邑之谋', sub='伏兵三十万 · 诱敌深入', note='单于觉之 引兵还', art=art_ambush),
    C(62, 66, 'court', 'card', year=127, main='推恩令', sub='诸侯分封子弟 · 不削而弱', note='主父偃献策 藩国自析', art=art_split('王', '侯', '侯')),
    C(66, 70, 'court', 'card', year=124, main='兴太学', sub='置五经博士 · 天下学子归心', note='天下学士 靡然乡风', art=art_school),
    C(70, 74, 'court', 'card', year=119, main='盐铁官营', sub='盐铁收归国有 · 充实国库', note='笼天下盐铁之利', art=art_furnace),
    C(74, 80, 'court', 'card', year=118, main='五铢钱', sub='统一铸币 · 行用七百余年', note='自是钱法始定', art=art_coins),
    # ---- 第三回 北击匈奴
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=129, main='龙城飞将', sub='卫青直捣龙城 · 首战告捷', note='但使龙城飞将在 不教胡马度阴山', art=L.art_cavalry),
    C(86, 90, 'war', 'card', year=127, main='收复河套', sub='卫青收河南地 · 置朔方郡', note='筑朔方城 复缮故秦时蒙恬所为塞', art=lambda A, cv, t, u: L.art_siege(A, cv, t, u, label='朔方')),
    C(90, 96, 'war', 'card', year=121, main='少年霍去病', sub='十七岁封冠军侯 · 千里奔袭河西', note='匈奴未灭 何以家为', art=art_huo),
    C(96, 98, 'war', 'card', year=121, main='河西四郡', sub='武威 张掖 酒泉 敦煌', art=art_four),
    C(98, 100, 'war', 'card', year=119, main='漠北决战', sub='卫青 霍去病 各率五万骑', art=L.art_cavalry),
    C(100, 102, 'war', 'card', year=119, main='封狼居胥', sub='霍去病 · 祭天于狼居胥山', art=S.art_taishan),
    C(102, 104, 'war', 'card', year=119, main='漠南无王庭', sub='匈奴远遁', art=art_flee),
    C(104, 112, 'war', 'expand', year=119),
    # ---- 第四回 盛世雄主
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=111, main='平定南越', sub='楼船十万 · 置南海九郡', note='汉之疆域 南抵南海', art=art_fleet),
    C(118, 126, 'works', 'list', year=104, items=['凿空西域', '丝绸之路', '汗血宝马', '太初历']),
    C(126, 130, 'empire', 'card', year=110, main='泰山封禅', sub='登封泰山 · 告成于天', note='天子至泰山 封禅', art=S.art_taishan),
    C(130, 134, 'empire', 'card', year=108, main='东定朝鲜', sub='置乐浪等四郡', note='遂定朝鲜 为四郡', art=lambda A, cv, t, u: L.art_surrender(A, cv, t, u, label='王险')),
    C(134, 138, 'fate', 'card', year=104, main='求仙问道', sub='建章宫立承露金人 · 求长生', note='作承露盘 高二十丈', art=art_chenglu),
    C(138, 142, 'war', 'card', year=99, main='李陵之祸', sub='五千步卒力战 · 兵败降匈奴', note='转斗千里 矢尽道穷', art=art_surround),
    C(142, 144, 'night', 'card', year=98, main='司马迁', sub='为李陵辩护 · 惨遭宫刑', art=art_sima),
    # ---- 第五回 晚年悔悟
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=95, main='国力空虚', sub='连年征战 · 海内虚耗 户口减半', note='天下虚耗 人复相食', art=art_famine),
    C(150, 154, 'death', 'card', year=91, main='巫蛊之祸', sub='江充构陷 · 太子刘据兵败自尽', note='死者数万人', art=art_wugu),
    C(154, 158, 'death', 'card', year=89, main='轮台罪己', sub='下诏深陈既往之悔', note='朕即位以来 所为狂悖 使天下愁苦', art=art_luntai),
    C(158, 162, 'death', 'card', year=88, main='托孤霍光', sub='立幼子刘弗陵 · 霍光辅政', note='赐周公负成王图', art=art_tuogu),
    C(162, 166, 'death', 'card', year=87, main='崩于五柞宫', sub='在位五十四年 · 享年七十岁', note='后元二年二月丁卯 崩于五柞宫', art=art_dusk_palace),
    C(166, 170, 'end', 'card', year=87, main='秦皇汉武', sub='一个朝代 · 成了一个民族的名字', note='汉人 汉字 汉族 由此得名', art=art_legacy),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS; L.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, 150, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS} | {120, 122, 124})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
G.year_at = year_at; L.year_at = year_at

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('刘 彻', SERIF, 50, ZHE, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '汉武帝', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('雄才大略', 58), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('前156 — 前87', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '穷兵黩武？', BRUSH, 120, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '雄才大略？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

LIST_ART = [art_west, art_silk, art_steed, art_calendar]
def scene_list(cv, t, c, k):
    i = min(3, int((k - c[0]) / 2))
    st = bt(c[0] + 2 * i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    year_line(cv, t, c[4]['year'], bt(c[0]))
    it = c[4]['items'][i]
    fx = Art()
    chars_in(cv, fx, it, BRUSH, 140, INK, W / 2, 440, t, st, stagger=0.05, seed=50 + i)
    fx.flush(cv)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            stamp(cv, seal('壹贰叁肆'[j], 36), x, 575, t, bt(c[0] + 2 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=ZHU + (110,), width=2)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    rise = ease_out(u / 1.6)
    person(A, 230, lerp(1820, 1700, rise), 760, dir=1, hat='crown', arm=lerp(10, 40, rise), layer='wash')
    for i in range(4):
        cx = lerp(-80, W + 120, clamp((u - 0.2 * i) / 2.4)) + i * 40
        crow(A, cx, 470 + 40 * math.sin(u * 2 + i) + i * 28, 20, t * 11 + i)
    beat_fx(A, t)
    A.flush(cv, alpha=clamp(u / 0.6))
    fx = Art()
    chars_in(cv, fx, '雄才大略', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('汉武大帝', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('北逐匈奴 · 西通西域', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('他让“汉”成了一个民族的名字', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '功大？过大？', BRUSH, 120, ZHU, W / 2, 1200, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区留下你的看法', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=ZHU + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=INK + (200,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 唐太宗李世民', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, list=scene_list, expand=scene_expand, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第贰集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('秦皇汉武 · 他凭什么与秦始皇齐名？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 320, 335, W / 2 + 320, 335), fill=ZHU + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, ZHU, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.9)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((BORN - yr) / (BORN - DIED))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=INK + (220,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'前{BORN}', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'前{DIED}'), 102), f'前{DIED}', font=f, fill=INK + (170,))
        lab = cn_num(int(round(BORN + 1 - yr))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=ZHU + (255,))
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
