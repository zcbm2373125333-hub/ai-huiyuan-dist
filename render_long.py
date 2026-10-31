# 秦始皇 · 千古一帝 —— 长版（93.75 秒，五回章回体）
# 基于古风故事加强版：同样的水墨/宣纸画风与动效库，换新音乐（116.16 BPM），
# 内容扩充为 开篇 + 五回 + 结尾，约 45 幕，每幕一段水墨剪影动画。
import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw
import render_gufeng as G
import render_story as S
import render_full as F

# ---------------------------------------------------------------- new music grid
BPM = 116.16
P = 60 / BPM
for mod in (G, S, F):
    mod.P = P
G.B0 = 0.208
G.DUR = 93.75
MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm2', 'music2_clean.wav')

from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          sun, walk_x, rotp, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx, spatter, year_line

END_BEAT = 170
F.END = bt(END_BEAT)

G.THEMES['court'] = dict(tint=(0.97, 0.93, 0.86), mtn=0.30, wm='权', sun=None, part='petal')
G.THEMES['fate'] = dict(tint=(0.95, 0.94, 0.92), mtn=0.35, wm='仙', sun=None, part='gold')
G.THEMES['night'] = dict(tint=(0.90, 0.90, 0.93), mtn=0.40, wm='夜', sun=None, part='snow')
G.THEMES['war']['sun'] = (ZHU, 250, (W * 0.5, 430))

DIM = (70, 50, 30)

# ================================================================ new ink scenes
def art_judge(A, cv, t, u):
    """Balance of merit and fault, swinging on the beat."""
    cx, top = 540, 860
    d = A.d['ink']
    d.polygon([(470, GROUND), (610, GROUND), (560, GROUND - 40), (520, GROUND - 40)], fill=255)
    d.line((cx, GROUND - 40, cx, top), fill=255, width=12)
    kb = (t - G.B0) / P
    ang = math.radians(16 * math.sin(kb * math.pi / 2) * math.exp(-max(0, u - 1.5) * 0.4))
    L = 320
    lx, ly = cx - L * math.cos(ang), top + L * math.sin(ang)
    rx, ry = cx + L * math.cos(ang), top - L * math.sin(ang)
    d.line((lx, ly, rx, ry), fill=255, width=10)
    d.ellipse((cx - 14, top - 14, cx + 14, top + 14), fill=255)
    pans = []
    for px, py in ((lx, ly), (rx, ry)):
        by = py + 220
        d.line((px, py, px - 70, by), fill=255, width=3); d.line((px, py, px + 70, by), fill=255, width=3)
        d.chord((px - 95, by - 40, px + 95, by + 40), 0, 180, fill=255)
        pans.append((px, by - 55))
    A.flush(cv)
    stamp(cv, seal('功', 64), pans[0][0], pans[0][1], t, t - u + 0.1)
    stamp(cv, seal('过', 64, INK), pans[1][0], pans[1][1], t, t - u + 0.25)

def enso(A, cx, cy, r, p, layer='ink', w0=26):
    """Zen ink circle drawn with a brush — thick start, dry thin tail."""
    d = A.d[layer]
    n = 60
    a0 = math.radians(-110)
    sweep = math.radians(335) * p
    prev = None
    for j in range(n + 1):
        f = j / n
        a = a0 + sweep * f
        pt = (cx + r * math.cos(a), cy + r * math.sin(a) * 0.96)
        if prev:
            d.line((prev, pt), fill=int(255 * (1 - 0.4 * f)), width=max(2, int(w0 * (1 - 0.75 * f))))
        prev = pt

def art_chapter(A, cv, t, u):
    enso(A, 540, 960, 380, ease_out(u / 0.7))
    A.d['wash'].ellipse((780, 640, 880, 740), fill=255)
    for k in range(4):
        y = 1180 + k * 50
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)
    for k in range(3):
        a = t * 1.2 + k * 2.1
        crow(A, 540 + 380 * math.cos(a), 700 + 50 * math.sin(a), 18, t * 10 + k)

def rider(A, x, y, s, dir=1, ph=0.0, layer='ink', spear=False, moving=True):
    horse(A, x, y, s, dir, ph, layer=layer, moving=moving)
    person(A, x - dir * 0.05 * s, y - 0.66 * s - abs(math.sin(ph)) * 0.04 * s, 0.6 * s, dir=dir, arm=55,
           hat='helmet' if spear else 'knot', spear=spear, layer=layer)

def city_wall(A, x0, x1, top, gate_x=None, label=None, layer='mid', open_=0.0):
    d = A.d[layer]
    d.rectangle((x0, top, x1, GROUND), fill=255)
    for x in range(int(x0), int(x1), 46):
        d.rectangle((x, top - 28, x + 26, top), fill=255)
    if gate_x is not None:
        di = A.d['ink']
        di.polygon([(gate_x - 200, top + 10), (gate_x + 200, top + 10), (gate_x + 150, top - 100), (gate_x - 150, top - 100)], fill=255)
        di.polygon([(gate_x - 240, top - 90), (gate_x + 240, top - 90), (gate_x + 180, top - 150), (gate_x - 180, top - 150)], fill=255)
        di.polygon([(gate_x - 140, top - 150), (gate_x + 140, top - 150), (gate_x + 100, top - 190), (gate_x - 100, top - 190)], fill=255)
        gw = 70
        d.rectangle((gate_x - gw, top + 100, gate_x + gw, GROUND), fill=0)
        d.pieslice((gate_x - gw, top + 30, gate_x + gw, top + 170), 180, 360, fill=0)
        if open_ < 1:  # gate doors
            dw = gw * (1 - open_)
            di.rectangle((gate_x - gw, top + 100, gate_x - gw + dw, GROUND), fill=255)
            di.rectangle((gate_x + gw - dw, top + 100, gate_x + gw, GROUND), fill=255)
        if label:
            di.rectangle((gate_x - 55, top - 82, gate_x + 55, top - 12), fill=255)
            di.text((gate_x - 42, top - 72), label, font=font(SERIF, 40, 'Black'), fill=0)

def art_father_flees(A, cv, t, u):
    A.d['wash'].ellipse((760, 680, 880, 800), fill=255); A.d['wash'].ellipse((790, 670, 910, 790), fill=0)
    city_wall(A, 60, 520, 1150, gate_x=300, label='邯郸')
    q = ease_out(u / (4 * P))
    s = lerp(260, 110, q)
    rx = lerp(560, 960, q)
    rider(A, rx, lerp(GROUND, 1300, q), s, 1, t * 13, layer='ink' if q < 0.6 else 'mid')
    for k in range(5):
        px = rx - s * (0.8 + k * 0.35); rr = s * (0.1 + 0.05 * k)
        A.d['wash'].ellipse((px - rr, lerp(GROUND, 1300, q) - rr - 10, px + rr, lerp(GROUND, 1300, q) + rr - 10), fill=255)
    person(A, 470, GROUND, 230, dir=1, female=True, baby=True, kneel=u > 2 * P, bow=20 if u > 2 * P else 0, layer='ink')

def art_return(A, cv, t, u):
    sun(cv, 820, 1060, 150, ZHU, 120)
    city_wall(A, 640, W - 60, 1180, gate_x=860, label='咸阳')
    ground(A, GROUND)
    x = lerp(-80, 420, ease_out(u / (3.5 * P)))
    carriage(A, x, GROUND, 190, dir=1, wheel=t * 5, ph=t * 10)
    for k in range(4):
        fx = 680 + k * 110
        flag(A, fx, 1150, 150, t + k, w=60)

def art_regent(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(560, GROUND), (980, GROUND), (950, 1310), (590, 1310)], fill=255)
    person(A, 790, 1310, 170, dir=-1, hat='crown', arm=30, layer='ink')
    grow = ease_out(u / (2 * P))
    big = lerp(380, 560, grow)
    person(A, 330, GROUND, big * 1.25, dir=1, arm=lerp(20, 75, grow), layer='wash')       # looming shadow
    person(A, 300, GROUND, big, dir=1, arm=lerp(10, 70, grow), layer='ink')
    for k in range(6):
        q = (u * 0.7 + k / 6) % 1
        x = 120 + k * 150; y = lerp(1300, 700, q)
        A.d['red'].ellipse((x - 9, y - 9, x + 9, y + 9), fill=int(220 * (1 - q)))
        A.d['red'].rectangle((x - 3, y - 3, x + 3, y + 3), fill=0)

def art_candle(A, cv, t, u):
    d = A.d['mid']
    d.rectangle((640, 720, 940, 1020), outline=255, width=10)
    for k in range(1, 4):
        d.line((640 + k * 75, 720, 640 + k * 75, 1020), fill=255, width=4)
        d.line((640, 720 + k * 75, 940, 720 + k * 75), fill=255, width=4)
    mx = lerp(700, 880, ease_out(u / (2 * P)))
    A.d['wash'].ellipse((mx - 40, 790, mx + 40, 870), fill=255)
    ground(A, GROUND)
    A.d['wash'].ellipse((260, 1020, 560, 1320), fill=200)
    A.d['ink'].rectangle((400, 1260, 420, GROUND), fill=255)
    A.d['ink'].rectangle((385, GROUND - 10, 435, GROUND), fill=255)
    fh = 46 + 8 * math.sin(t * 17)
    A.d['red'].polygon([(398, 1260), (422, 1260), (415 + 4 * math.sin(t * 9), 1260 - fh), (410, 1260 - fh * 1.05)], fill=255)
    person(A, 560, GROUND, 230, dir=-1, hat='crown', kneel=True, bow=18, arm=75, layer='ink')
    A.d['mid'].rectangle((430, 1270, 500, 1300), fill=255)

def art_capping(A, cv, t, u):
    ground(A, GROUND)
    stand = u > 2 * P
    if not stand:
        person(A, 540, GROUND, 300, dir=1, kneel=True, bow=12, arm=40, layer='ink')
        cy = lerp(780, 1010, ease_out(u / (1.6 * P)))
        A.d['ink'].polygon([(470, cy), (630, cy + 4), (630, cy + 20), (470, cy + 16)], fill=255)
        person(A, 760, GROUND, 340, dir=-1, arm=150, layer='mid')
    else:
        v = u - 2 * P
        sw = lerp(40, 175, ease_expo(v / 0.3))
        person(A, 540, GROUND, 360, dir=1, hat='crown', arm=sw, sword=sw, layer='ink')
        for k in range(12):
            a = math.radians(-90 + (k - 5.5) * 13)
            r0, r1 = 120, lerp(150, 520, ease_out(v / 0.5))
            A.d['wash'].line((540 + r0 * math.cos(a), 960 + r0 * math.sin(a), 540 + r1 * math.cos(a), 960 + r1 * math.sin(a)), fill=255, width=10)
        person(A, 830, GROUND, 300, dir=-1, kneel=True, bow=50, arm=60, layer='mid')

def art_rebels(A, cv, t, u):
    sun(cv, 540, 980, 260, ZHU, 110)
    ground(A, GROUND)
    off = (t * 110) % 150
    for i in range(-1, 8):
        x = i * 150 + off - 60
        person(A, x, GROUND, 200, dir=1, robe=False, hat='helmet', ph=t * 7 + i, spear=True, arm=30, layer='ink')
        if i % 2 == 0:
            flames(A, x + 30, GROUND - 330, 40, 70, t + i, n=2, seed=i, smoke=False)
    rider(A, lerp(-200, 380, ease_out(u / (2 * P))), 1300, 200, 1, t * 12, layer='mid', spear=True)

def art_poison(A, cv, t, u):
    ground(A, GROUND)
    person(A, 420, GROUND, 300, dir=1, kneel=True, bow=lerp(20, 60, ease_out((u - P) / 0.4)), arm=70, layer='ink')
    tilt = ease_out((u - 2 * P) / 0.3)
    cx, cy = 640, GROUND - 40
    pts = [(-30, -50), (30, -50), (14, 0), (-14, 0)]
    pts = [rotp((cx + a, cy + b), (cx, cy), tilt * 1.6) for a, b in pts]
    A.d['ink'].polygon(pts, fill=255)
    if tilt > 0:
        for k in range(8):
            q = clamp((u - 2 * P - k * 0.04) / 0.5)
            A.d['ink'].ellipse((cx + 30 + q * 160 - 6, GROUND - 10 - 6, cx + 30 + q * 160 + 6, GROUND - 10 + 6), fill=int(255 * q))
    for k in range(10):
        q = (u * 0.45 + k * 0.1) % 1
        x = 120 + k * 90 + 40 * math.sin(t * 2 + k); y = 650 + q * 700
        a = t * 3 + k
        A.d['mid'].polygon([rotp(p, (x, y), a) for p in ((x - 14, y), (x, y - 6), (x + 14, y), (x, y + 6))], fill=255)
    if u > P:
        A.flush(cv)
        stamp(cv, seal('迁蜀', 54), 800, 980, t, t - u + P)

def art_lisi(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(700, GROUND), (1020, GROUND), (990, 1300), (730, 1300)], fill=255)
    person(A, 860, 1300, 200, dir=-1, hat='crown', arm=40, layer='ink')
    person(A, 560, GROUND, 230, dir=1, kneel=True, bow=25, arm=85, layer='ink')
    sl = ease_out((u - P) / 0.4)
    if sl > 0:
        for k in range(int(6 * sl)):
            A.d['ink'].rectangle((610 + k * 16, 1200, 622 + k * 16, 1290), fill=255)
    for k in range(5):
        x = walk_x(-150 - k * 120, 360 - k * 75, u, 3.5 * P)
        person(A, x, GROUND, 180 - k * 12, dir=1, arm=20, layer='mid' if k % 2 else 'ink')

QIN_POS = (230, 1040)
SIX_POS = [(560, 940, '韩'), (600, 760, '赵'), (640, 1110, '魏'), (720, 1300, '楚'), (860, 700, '燕'), (900, 960, '齐')]

def art_strategy(A, cv, t, u):
    d = A.d['wash']
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 420 + 60 * math.sin(a * 3 + 1) + 30 * math.sin(a * 7)
        pts.append((560 + r * math.cos(a) * 1.0, 1000 + r * math.sin(a) * 0.75))
    d.polygon(pts, fill=200)
    A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    for i, (x, y, ch) in enumerate(SIX_POS):
        p = ease_out((u - 0.25 - i * 0.22) / 0.3)
        if p > 0:
            x0, y0 = QIN_POS
            xe, ye = lerp(x0, x, p), lerp(y0, y, p)
            A.d['red'].line((x0 + 50, y0, xe, ye), fill=255, width=8)
            ang = math.atan2(ye - y0, xe - x0)
            A.d['red'].polygon([(xe + 26 * math.cos(ang), ye + 26 * math.sin(ang)),
                                (xe + 16 * math.cos(ang + 2.3), ye + 16 * math.sin(ang + 2.3)),
                                (xe + 16 * math.cos(ang - 2.3), ye + 16 * math.sin(ang - 2.3))], fill=255)
    A.flush(cv)
    stamp(cv, seal('秦', 80), QIN_POS[0], QIN_POS[1], t, t - u)
    for i, (x, y, ch) in enumerate(SIX_POS):
        stamp(cv, seal(ch, 44, INK), x, y, t, t - u + 0.1 + i * 0.05)

def art_cavalry(A, cv, t, u, snow=False):
    ground(A, GROUND)
    for row, (yy, s, lay, sp) in enumerate([(1280, 120, 'wash', 260), (1350, 170, 'mid', 360), (GROUND, 230, 'ink', 470)]):
        gap = s * 2.0
        off = (t * sp) % gap
        for i in range(-1, int(W / gap) + 2):
            x = i * gap + off - 80
            rider(A, x, yy, s, 1, t * 13 + i * 1.7 + row, layer=lay, spear=True)
    for k in range(14):
        x = (k * 97 - t * 900) % (W + 200) - 100
        A.d['wash'].line((x, 1100 + k * 22, x + 160, 1100 + k * 22), fill=255, width=4)

def art_siege(A, cv, t, u, label='邯郸'):
    city_wall(A, 200, W - 60, 1060, gate_x=640, label=label)
    flames(A, 470, 1050, 260, 170 * (0.5 + 0.5 * ease_out(u / (2 * P))), t, n=5, seed=3, smoke=True)
    flames(A, 860, 1050, 220, 150 * (0.5 + 0.5 * ease_out(u / (2 * P))), t + 1, n=4, seed=8, smoke=True)
    for k, lx in enumerate((300, 960)):
        A.d['ink'].line((lx - 90, GROUND, lx, 1050), fill=255, width=8)
        A.d['ink'].line((lx - 60, GROUND, lx + 30, 1050), fill=255, width=8)
        for r in range(7):
            yy = lerp(GROUND, 1050, r / 7)
            A.d['ink'].line((lerp(lx - 90, lx, r / 7), yy, lerp(lx - 60, lx + 30, r / 7), yy), fill=255, width=5)
        q = (u * 0.35 + k * 0.5) % 1
        person(A, lerp(lx - 70, lx + 10, q), lerp(GROUND, 1060, q), 120, dir=1, robe=False, hat='helmet', ph=t * 9, arm=150, layer='ink')
    for k in range(3):
        person(A, 90 + k * 60, GROUND, 180, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    for k in range(5):
        q = (u * 1.2 + k * 0.2) % 1
        arrow(A, lerp(120, 700, q), 950 - 200 * math.sin(math.pi * q), math.atan2(-200 * math.pi * math.cos(math.pi * q), 580), 70)

def art_jingke(A, cv, t, u):
    for px in (160, 920):
        A.d['ink'].rectangle((px - 40, 700, px + 40, GROUND), fill=255)
        A.d['ink'].rectangle((px - 60, 680, px + 60, 710), fill=255)
    A.d['mid'].rectangle((60, 640, W - 60, 680), fill=255)
    ground(A, GROUND)
    if u < 2 * P:
        person(A, 760, GROUND, 260, dir=-1, hat='crown', arm=20, layer='ink')
        person(A, 380, GROUND, 250, dir=1, kneel=True, bow=15, arm=80, layer='ink')
        p = ease_out(u / (1.6 * P))
        A.d['mid'].rectangle((460, 1250, 460 + 220 * p, 1300), fill=255)
        if p > 0.95:
            A.d['ink'].polygon([(680, 1265), (740, 1275), (680, 1285)], fill=255)
            A.d['red'].ellipse((730, 1262, 750, 1288), fill=255)
    elif u < 4 * P:
        v = u - 2 * P
        cx = 540; w = 2.6
        a = v * w
        kx = cx + 200 * math.cos(a); jx = cx + 200 * math.cos(a - 0.9)
        A.d['ink'].rectangle((cx - 45, 700, cx + 45, GROUND), fill=255)
        for x, a2, who in ((kx, a, 'k'), (jx, a - 0.9, 'j')):
            front = math.sin(a2) > 0
            dir_ = -1 if math.sin(a2) > 0 else 1
            lay = 'ink' if front else 'mid'
            if who == 'k':
                person(A, x, GROUND, 250, dir=dir_, hat='crown', robe=False, ph=t * 14, arm=30, layer=lay)
            else:
                person(A, x, GROUND, 240, dir=dir_, robe=False, ph=t * 14, arm=95, sword=95, layer=lay)
    else:
        v = u - 4 * P
        sw = lerp(170, 60, ease_expo(v / 0.2))
        person(A, 420, GROUND, 290, dir=1, hat='crown', robe=False, arm=sw, sword=sw, layer='ink')
        fall = -80 * ease_out((v - 0.12) / 0.35)
        person(A, 700, GROUND, 260, dir=-1, robe=False, arm=60, fall=fall, layer='ink')
        al = clamp(1 - (v - 0.2) / 0.4)
        if al > 0 and v > 0.05:
            pts = [(450 + 430 * math.cos(math.radians(a)), 1180 - 330 * math.sin(math.radians(a))) for a in range(70, -30, -5)]
            inner = [(450 + 390 * math.cos(math.radians(a)), 1180 - 290 * math.sin(math.radians(a))) for a in range(-25, 75, 5)]
            A.d['red'].polygon(pts + inner, fill=int(255 * al))

def art_flood(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='大梁')
    lvl = lerp(GROUND + 20, 1240, ease_out(u / (1.6 * P)))
    A.d['mid'].rectangle((60, lvl, W - 60, GROUND + 30), fill=255)
    waves(A, int(lvl) - 30, t, rows=3, amp=12, speed=4)
    for k in range(3):
        person(A, 90 + k * 70, lvl - 120, 150, dir=1, robe=False, hat='helmet', spear=True, layer='ink')
    A.d['mid'].polygon([(60, lvl - 110), (330, lvl - 110), (300, lvl - 80), (60, lvl - 80)], fill=255)

def art_surrender(A, cv, t, u, label='临淄'):
    op = ease_out((u - 0.1) / 0.5)
    city_wall(A, 60, W - 60, 1100, gate_x=540, label=label, open_=op)
    for k in range(3):
        person(A, 160 + k * 80, GROUND, 200, dir=1, robe=False, hat='helmet', spear=True, arm=35, layer='ink')
        person(A, 920 - k * 80, GROUND, 200, dir=-1, robe=False, hat='helmet', spear=True, arm=35, layer='ink')
    if op > 0.6:
        v = u - 0.4
        y = GROUND
        person(A, 540, y, 210, dir=1, kneel=v > P * 0.8, bow=50 if v > P * 0.8 else 0, arm=80, layer='ink')
        A.d['wash'].rectangle((560, 1180, 640, 1240), fill=255)

def art_jinren(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        x = 120 + i * 168
        rise = ease_out((u - i * 0.12) / 0.5)
        if rise <= 0: continue
        h = 420 if i % 2 else 470
        person(A, x, lerp(GROUND + h, GROUND, rise), h, dir=1 if i < 3 else -1, arm=10, hat='crown', layer='mid' if i % 2 else 'ink')
    flames(A, 540, GROUND - 10, 260, 150, t, n=6, seed=5, smoke=True)
    for k in range(6):
        q = (u * 0.9 + k / 6) % 1
        x = 460 + k * 30; y = lerp(700, GROUND - 60, q)
        A.d['ink'].line((x, y, x + 20, y + 60), fill=255, width=5)

def art_palace_build(A, cv, t, u):
    tmp = Art()
    palace(tmp, 540, GROUND, 760, layer='ink')
    lvl = lerp(GROUND, 600, ease_out(u / (1.8 * P)))
    for n, im in tmp.im.items():
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).rectangle((0, lvl, W, H), fill=255)
        A.im[n].paste(im, (0, 0), m)
    d = A.d['mid']
    for x in range(140, 960, 80):
        d.line((x, lvl, x, GROUND), fill=255, width=3)
    d.line((120, lvl, 960, lvl), fill=255, width=4)
    for k in range(3):
        x = (t * 80 + k * 300) % (W + 200) - 100
        person(A, x, GROUND, 150, dir=1, robe=False, ph=t * 7 + k, load=True, arm=160, layer='ink')

def art_procession(A, cv, t, u):
    A.d['ink'].rounded_rectangle((830, 860, 960, GROUND), radius=30, fill=255)
    A.d['ink'].rectangle((800, GROUND - 40, 990, GROUND), fill=255)
    f = font(SERIF, 40, 'Black')
    for j, ch in enumerate('皇帝临立'):
        if u > 0.3 + j * 0.2:
            A.d['ink'].text((875, 900 + j * 52), ch, font=f, fill=0)
    ground(A, GROUND)
    off = t * 120
    for k in range(4):
        x = (k * 300 + off) % (W + 600) - 500
        if k % 2 == 0:
            carriage(A, x, GROUND, 150, dir=1, wheel=t * 5, ph=t * 9, layer='mid' if k else 'ink')
        else:
            for j in range(3):
                person(A, x + j * 60, GROUND, 150, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + j, layer='ink')
            flag(A, x + 30, GROUND - 150, 200, t + k, w=70)

def art_plot(A, cv, t, u):
    A.d['wash'].ellipse((160, 650, 280, 770), fill=255)
    carriage(A, 170, GROUND, 170, dir=1, horses=False, moving=False, layer='wash')
    ground(A, GROUND)
    lean = 15 + 6 * math.sin(t * 3)
    person(A, 560, GROUND, 270, dir=1, bow=lean, arm=50, layer='ink')
    person(A, 820, GROUND, 280, dir=-1, bow=lean, arm=50, hat='knot', layer='ink')
    A.d['ink'].rectangle((680, 1300, 700, GROUND), fill=255)
    fh = 34 + 6 * math.sin(t * 15)
    A.d['red'].polygon([(682, 1300), (698, 1300), (692 + 3 * math.sin(t * 9), 1300 - fh), (688, 1300 - fh)], fill=255)
    p = ease_out((u - P) / 0.5)
    if p > 0:
        A.d['mid'].rectangle((620, lerp(1200, 900, p), 760, lerp(1240, 1060, p)), fill=255)
        A.flush(cv)
        if u > P + 0.4:
            stamp(cv, seal('诏', 46), 730, 1030, t, t - u + P + 0.4)

def art_tree(A, cv, t, u):
    d = A.d['ink']
    st = t - u
    p = ease_out(u / 0.35)
    top = (540, 820)
    mids = [(250, 1030), (540, 1030), (830, 1030)]
    lows = [(x + dx, 1250) for x, _ in mids for dx in (-80, 80)]
    for m in mids:
        d.line((top[0], top[1], lerp(top[0], m[0], p), lerp(top[1], m[1], p)), fill=255, width=5)
    q = ease_out((u - 0.15) / 0.35)
    for i, l in enumerate(lows):
        m = mids[i // 2]
        if q > 0: d.line((m[0], m[1], lerp(m[0], l[0], q), lerp(m[1], l[1], q)), fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('皇', 70), top[0], top[1], t, st)
    for m in mids: stamp(cv, seal('郡', 52), m[0], m[1], t, st + 0.12)
    for l in lows: stamp(cv, seal('县', 40), l[0], l[1], t, st + 0.25)

def art_snow_cavalry(A, cv, t, u): art_cavalry(A, cv, t, u, snow=True)

# ================================================================ script
def C(b0, b1, theme, kind, **d): return (b0, b1, theme, kind, d)

CHAPTERS = {16: ('第一回', '邯郸质子'), 48: ('第二回', '亲政夺权'), 80: ('第三回', '横扫六合'),
            112: ('第四回', '始皇称帝'), 144: ('第五回', '功过千秋')}

CARDS = [
    C(0, 2, 'hook', 'num', num='十三岁', line='继位为王', art=S.art_child_king),
    C(2, 4, 'hook', 'num', num='三十九岁', line='一统天下', art=S.art_army),
    C(4, 6, 'hook', 'num', num='五十岁', line='崩于东巡路上', art=S.art_last_journey),
    C(6, 8, 'hook', 'num', num='十五年', line='大秦二世而亡', art=S.art_fall),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=art_judge),
    # ---- 第一回
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=259, main='生于邯郸', sub='秦国质子之子 · 生在敌国赵都', note='秦昭王四十八年 正月生于邯郸', art=S.art_handan),
    C(22, 26, 'night', 'card', year=257, main='父逃母藏', sub='邯郸之战 · 父亲子楚弃城逃回秦国', note='子楚行金六百斤 予守者吏 得脱', art=art_father_flees),
    C(26, 30, 'night', 'card', year=257, main='九死一生', sub='赵人欲杀之 · 母子东躲西藏', note='赵欲杀子楚妻子 得匿 母子竟得活', art=S.art_escape),
    C(30, 34, 'life', 'card', year=251, main='归秦', sub='九岁 终于回到秦国', note='秦赵修好 赵乃奉其母子归秦', art=art_return),
    C(34, 38, 'life', 'card', year=250, main='父亲即位', sub='子楚继位 · 是为庄襄王', note='在位仅三年 即病逝', art=S.art_enthrone),
    C(38, 42, 'life', 'card', year=247, main='少年为王', sub='十三岁 · 继承秦王之位', note='年少 委国事大臣', art=S.art_throne),
    C(42, 46, 'court', 'card', year=247, main='仲父专权', sub='相国吕不韦 · 把持朝政', note='家僮万人 门客三千', art=art_regent),
    C(46, 48, 'court', 'card', year=243, main='隐忍九年', sub='韬光养晦 · 静待时机', art=art_candle),
    # ---- 第二回
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=238, main='加冠亲政', sub='二十二岁 · 雍城行冠礼 佩剑', note='己酉 王冠 带剑', art=art_capping),
    C(54, 58, 'court', 'card', year=238, main='长信侯叛乱', sub='嫪毐趁机 · 发兵攻蕲年宫', note='矫王御玺及太后玺 以发县卒', art=art_rebels),
    C(58, 62, 'court', 'card', year=238, main='雷霆平乱', sub='车裂嫪毐 · 夷其三族', note='战咸阳 斩首数百', art=S.art_purge),
    C(62, 66, 'court', 'card', year=235, main='罢黜仲父', sub='吕不韦被逐 · 饮鸩自尽', note='君何功于秦 秦封君河南', art=art_poison),
    C(66, 70, 'court', 'card', year=237, main='谏逐客书', sub='李斯上书 · 广纳天下贤才', note='泰山不让土壤 故能成其大', art=art_lisi),
    C(70, 74, 'court', 'card', year=236, main='远交近攻', sub='重金离间 · 各个击破', note='奋六世之余烈 振长策而御宇内', art=art_strategy),
    C(74, 80, 'war', 'card', year=231, main='剑指六国', sub='百万秦军 · 集结待发', note='带甲百万 车千乘 骑万匹', art=S.art_army),
    # ---- 第三回
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=230, main='灭韩', sub='内史腾攻韩 · 俘韩王安', note='六国之中 韩最先亡', art=art_cavalry),
    C(86, 90, 'war', 'card', year=228, main='破赵', sub='王翦攻破邯郸 · 俘赵王迁', note='重回出生之地 尽坑仇家', art=art_siege),
    C(90, 96, 'war', 'card', year=227, main='荆轲刺秦', sub='图穷匕见 · 秦王绕柱而走', note='风萧萧兮易水寒 壮士一去兮不复还', art=art_jingke),
    C(96, 98, 'war', 'card', year=225, main='水淹大梁', sub='王贲引河灌城 · 魏亡', art=art_flood),
    C(98, 100, 'war', 'card', year=223, main='灭楚', sub='王翦率六十万大军', art=S.art_army),
    C(100, 102, 'war', 'card', year=222, main='灭燕', sub='王贲远征辽东', art=art_cavalry),
    C(102, 104, 'war', 'card', year=221, main='齐降', sub='齐王建 · 不战而降', art=art_surrender),
    C(104, 112, 'war', 'six'),
    # ---- 第四回
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=221, main='始皇帝', sub='德兼三皇 · 功过五帝', seal='皇帝', note='朕为始皇帝 后世以计数', art=S.art_enthrone),
    C(118, 126, 'empire', 'list', year=221, items=['书同文', '车同轨', '统一度量衡', '废分封 立郡县']),
    C(126, 130, 'empire', 'card', year=221, main='铸十二金人', sub='收天下兵器 · 熔铸咸阳', note='收天下兵 聚之咸阳 销以为钟鐻', art=art_jinren),
    C(130, 134, 'empire', 'card', year=219, main='泰山封禅', sub='登临绝顶 · 刻石颂德', note='登兹泰山 周览东极', art=S.art_taishan),
    C(134, 138, 'works', 'card', year=215, main='北筑长城', sub='蒙恬率三十万大军 · 北击匈奴', note='起临洮 至辽东 延袤万余里', art=S.art_wall),
    C(138, 142, 'works', 'card', year=214, main='凿灵渠', sub='南征百越 · 沟通湘漓', note='车马通天下 水路连岭南', art=S.art_road_canal),
    C(142, 144, 'works', 'card', year=212, main='营建阿房宫', sub='覆压三百余里', art=art_palace_build),
    # ---- 第五回
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=213, main='焚书坑儒', sub='功过是非 · 争议两千年', note='非博士官所职 天下敢有藏诗书者 悉诣守尉杂烧之', art=S.art_burn),
    C(150, 154, 'fate', 'card', year=219, main='求仙问药', sub='遣徐福东渡 · 只为长生不老', note='发童男女数千人 入海求仙人', art=S.art_sea),
    C(154, 158, 'fate', 'card', year=211, main='五巡天下', sub='刻石颂功 · 威震四海', note='皇帝临位 作制明法', art=art_procession),
    C(158, 162, 'death', 'card', year=210, main='崩于沙丘', sub='第五次东巡途中 · 终年五十岁', note='七月丙寅 始皇崩于沙丘平台', art=S.art_shaqiu),
    C(162, 166, 'death', 'card', year=210, main='沙丘之谋', sub='赵高李斯 · 秘不发丧 伪造遗诏', note='赐公子扶苏死 立胡亥为太子', art=art_plot),
    C(166, 170, 'death', 'card', year=207, main='二世而亡', sub='大秦帝国 · 仅存十五年', note='一夫作难而七庙隳', art=S.art_fall),
    C(170, 999, 'end', 'end'),
]
G.CARDS = CARDS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, 158, END_BEAT]
SIX_BASE = 104

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
G.year_at = year_at

def draw_wall(canvas, t, off):
    s0 = bt(134)
    if not (s0 - 0.1 <= t < bt(138)): return
    prog = ease_out((t - s0) / (P * 3))
    ys = G.SMOOTH_FRONT
    d = ImageDraw.Draw(canvas)
    xmax = int(W * prog); col = (52, 50, 48, 235)
    pts = [(x, ys[x + off]) for x in range(0, xmax, 6)]
    if len(pts) > 1:
        d.line(pts, fill=col, width=9)
        for x in range(0, xmax, 26):
            d.rectangle((x, ys[x + off] - 16, x + 11, ys[x + off]), fill=col)
        for x in range(90, xmax, 260):
            y = ys[x + off]
            d.rectangle((x - 18, y - 56, x + 18, y), fill=col)
            d.polygon([(x - 28, y - 56), (x + 28, y - 56), (x, y - 80)], fill=col)
G.draw_wall = draw_wall

# ================================================================ scene layouts
def stage(cv, t, c, fn):
    A = Art()
    u = t - bt(c[0])
    fn(A, cv, t, u)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out(u / 0.35))

def type_down(cv, im, cx, cy, t, start, dur=0.5):
    u = t - start
    if u <= 0: return
    p = clamp(u / dur)
    if p < 1:
        a = np.asarray(im.getchannel('A'), np.float32)
        ys = np.arange(im.height, dtype=np.float32)[:, None]
        m = np.clip((p * im.height * 1.1 - ys) / 40, 0, 1)
        im = im.copy(); im.putalpha(Image.fromarray((a * m).astype(np.uint8)))
    paste(cv, im, cx, cy)

def note_in(cv, text, t, start):
    """Classical quote in vertical columns down the left margin (read right-to-left)."""
    cols = text.split(' ')
    n = len(cols)
    for j, col in enumerate(cols):
        im = text_img(col, SERIF, 36, DIM, 'SemiBold', bleed=False, vertical=True)
        x = 92 + (n - 1 - j) * 50
        type_down(cv, im, x, 650 + im.height / 2, t, start + j * 0.3, dur=0.45)
    u = t - start
    if u > 0:
        h = 30 + 40 * max(len(c) for c in cols) * ease_out(u / 0.5)
        ImageDraw.Draw(cv).line((92 + n * 50 - 20, 640, 92 + n * 50 - 20, 640 + h), fill=ZHU + (200,), width=3)

def scene_num(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    stage(cv, t, c, d['art'])
    fx = Art()
    chars_in(cv, fx, d['num'], BRUSH, 150, INK, W / 2, 470, t, s0, stagger=0.06, seed=c[0])
    chars_in(cv, fx, d['line'], BRUSH, 92, ZHU, W / 2, 600, t, s1, stagger=0.05, drop=30, splash=False)
    fx.flush(cv)

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('嬴 政', SERIF, 50, ZHE, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '秦始皇', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('千古一帝', 58), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('前259 — 前210', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '暴君？', BRUSH, 130, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '千古一帝？', BRUSH, 130, INK, W / 2, 570, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ZHU, 'Black', bleed=False, spacing=12), W / 2, 760, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 170, INK, W / 2, 970, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

def scene_card(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    stage(cv, t, c, d['art'])
    year_line(cv, t, d['year'], s0)
    main = d['main']
    fx = Art()
    chars_in(cv, fx, main, BRUSH, 150 if len(main) <= 5 else 125, INK, W / 2, 435, t, s0, seed=c[0])
    fx.flush(cv)
    type_in(cv, text_img(d['sub'], SERIF, 40, DIM, 'SemiBold', bleed=False, spacing=3), W / 2, 555, t, s1, dur=0.38)
    if 'seal' in d and t >= s1:
        stamp(cv, seal(d['seal'], 60), W / 2 + 330, 420, t, s1, rot=6)
    if 'note' in d:
        note_in(cv, d['note'], t, bt(c[0] + 2) if c[1] - c[0] >= 4 else s1 + 0.25)

LIST_ART = [S.art_slips, S.art_ruts, S.art_scale, art_tree]
def scene_list(cv, t, c, k):
    i = min(3, int((k - c[0]) / 2))
    st = bt(c[0] + 2 * i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    year_line(cv, t, 221, bt(114))
    it = c[4]['items'][i]
    fx = Art()
    chars_in(cv, fx, it, BRUSH, 140 if len(it) <= 5 else 120, INK, W / 2, 440, t, st, stagger=0.05, seed=50 + i)
    fx.flush(cv)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            stamp(cv, seal('壹贰叁肆'[j], 36), x, 575, t, bt(c[0] + 2 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=ZHU + (110,), width=2)

STATES = G.STATES; STATE_YEARS = G.STATE_YEARS; HEX_POS = G.HEX_POS
def scene_six(cv, t, c, k):
    s0 = bt(SIX_BASE)
    cx0, cy0, R = W / 2, 935, 190
    gather_t = bt(SIX_BASE + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t); A.flush(cv)
    if not gather:
        fx = Art()
        chars_in(cv, fx, '横扫六合', BRUSH, 150, INK, W / 2, 420, t, s0, stagger=0.06, seed=104)
        fx.flush(cv)
    idx = int(k - SIX_BASE)
    if 0 <= idx < 6:
        lab = text_img(f'公元前{cn_num(STATE_YEARS[idx])}年 · 灭{STATES[idx]}', SERIF, 56, ZHU, 'Black', bleed=False, spacing=4)
        ink_in(cv, lab, W / 2, 1410, t, bt(SIX_BASE + idx), dur=0.2, settle=1.0)
    gu = ease_expo((t - gather_t) / 0.4) if gather else 0
    stamp(cv, seal('秦', 110), cx0, cy0, t, s0)
    if gather:
        stamp(cv, seal('秦', 260), cx0, cy0, t, gather_t)
    for i, ch in enumerate(STATES):
        hx, hy = HEX_POS[ch]
        px = cx0 + hx * R * (0.95 if abs(hx) == 2 else 0.92); py = cy0 + hy * R * 1.55
        ka = bt(SIX_BASE + i)
        if gather:
            paste(cv, G.state_disc(ch, True), lerp(px, cx0, gu), lerp(py, cy0, gu), 1 - 0.7 * gu, 1 - gu)
            continue
        if t < ka:
            paste(cv, G.state_disc(ch, False), px, py); continue
        u = t - ka
        L = 150
        if u < 0.45:
            from PIL import ImageChops
            disc = G.state_disc(ch, False)
            a, b = G.half_masks(disc.width)
            sep = ease_out((u - 0.08) / 0.37) * 40 if u > 0.08 else 0
            for msk, sgn in ((a, -1), (b, 1)):
                part = disc.copy(); part.putalpha(ImageChops.multiply(disc.getchannel('A'), msk))
                paste(cv, part, px + sgn * sep, py + sgn * sep * 0.6, 1, 1 - clamp((u - 0.08) / 0.37))
            paste(cv, G.state_disc(ch, True), px, py, 1, clamp(u / 0.45))
        else:
            paste(cv, G.state_disc(ch, True), px, py)
        G.brush_slash(cv, px + L * 0.7, py - L * 0.7, px - L * 0.7, py + L * 0.7, ease_out(u / 0.1), 1.0)
    if gather:
        fx = Art()
        chars_in(cv, fx, '六王毕', BRUSH, 200, INK, W / 2, 450, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '四海一', BRUSH, 200, ZHU, W / 2, 1300, t, bt(SIX_BASE + 7), stagger=0.08, seed=111)
        fx.flush(cv)

G.SCENES.update(num=scene_num, title=scene_title, question=scene_question, chapter=scene_chapter,
                card=scene_card, list=scene_list, six=scene_six, end=F.scene_end)

# ================================================================ HUD
def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第壹集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('史上第一位皇帝 · 一生到底有多狠？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=ZHU + (220,), width=3)
    # current chapter tag
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, ZHU, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.9)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((259 - yr) / (259 - 210))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=INK + (220,), width=6)
        for b, ch in CHAPTERS.items():   # chapter ticks
            cy_ = [c for c in CARDS if c[0] > b and 'year' in c[4]]
            if cy_:
                xt = lerp(x0, x1, clamp((259 - cy_[0][4]['year']) / 49))
                d.line((xt, 72, xt, 88), fill=ZHU + (160,), width=3)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), '前259', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength('前210'), 102), '前210', font=f, fill=INK + (170,))
        lab = cn_num(int(round(260 - yr))) + '岁' if yr > 209.5 else '身后'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=ZHU + (255,))
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 80))
G.draw_hud = draw_hud

# cover: finished title shot, ink-wipe into the story on beat 0
G.compose = lambda t: S._orig_compose(bt(12) - 0.2 if t < G.B0 else t)

# dissolves for every in-chapter cut
CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS} | {120, 122, 124})
DISSOLVE = 0.22
def render(fi):
    t = fi / FPS
    cur = G.render(fi)
    for cb in CUTS:
        s = bt(cb)
        if s <= t < s + DISSOLVE:
            pa = np.frombuffer(G.render(math.ceil(s * FPS) - 1), np.uint8).astype(np.float32)
            a = ease_out((t - s) / DISSOLVE)
            return np.clip(pa * (1 - a) + np.frombuffer(cur, np.uint8).astype(np.float32) * a, 0, 255).astype(np.uint8).tobytes()
    return cur

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', MUSIC,
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 300 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
