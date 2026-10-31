# 秦始皇 · 千古一帝 —— 古风水墨「故事动画」版
# 在古风版基础上：每段文字下方加一幕水墨剪影动画，把故事演出来。
# 卡点只作用在画面元素上（人物动作、印章、墨迹），整屏不缩放、不震动。
import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_gufeng as G
from render_gufeng import (W, H, FPS, P, bt, INK, ZHU, ZHE, BRUSH, SERIF, font, clamp, lerp,
                           ease_out, ease_expo, cn_num, text_img, paste, ink_in, seal, stamp, smooth_noise)

HERE = os.path.dirname(os.path.abspath(__file__))
GROUND = 1420
for th in G.THEMES.values():
    th['mtn'] *= 0.55          # 远山淡一些，让人物剪影更清楚

# ================================================================ ink layers
DRY_FULL = smooth_noise((H, W), 5, 88)
LAYERS = [  # name, colour, opacity, blur
    ('wash', INK, 0.28, 5.0),
    ('mid', INK, 0.50, 1.2),
    ('ink', INK, 0.94, 0.9),
    ('red', ZHU, 0.88, 2.2),
]

class Art:
    def __init__(s):
        s.im = {n: Image.new('L', (W, H), 0) for n, *_ in LAYERS}
        s.d = {n: ImageDraw.Draw(i) for n, i in s.im.items()}

    def flush(s, canvas, reveal=None, alpha=1.0):
        fld = G.transition_field() if reveal is not None and reveal < 1 else None
        for n, col, op, blur in LAYERS:
            im = s.im[n]
            bb = im.getbbox()
            if not bb: continue
            pad = int(blur * 3) + 2
            x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad)
            x1, y1 = min(W, bb[2] + pad), min(H, bb[3] + pad)
            crop = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
            a = np.asarray(crop, np.float32) / 255 * op * alpha
            if n in ('ink', 'mid'):
                a *= 0.84 + 0.16 * DRY_FULL[y0:y1, x0:x1]
            if fld is not None:
                if reveal <= 0: return
                a *= np.clip((reveal * 1.3 - fld[y0:y1, x0:x1]) / 0.08, 0, 1)
            lay = Image.new('RGBA', (x1 - x0, y1 - y0), col + (0,))
            lay.putalpha(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))
            canvas.alpha_composite(lay, (x0, y0))
        s.__init__()

def rotp(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca)

def ellipse_pts(cx, cy, rx, ry, n=24):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]

# ================================================================ figures
def person(A, x, y, h, dir=1, ph=None, bow=0, arm=-8, robe=True, hat='knot', spear=False, sword=None,
           fall=0, kneel=False, baby=False, load=False, female=False, layer='ink', arm2=None):
    """Side-view silhouette. Local units: u forward, v up, height = h."""
    d = A.d[layer]
    hipv = 0.5
    bowr = math.radians(bow); fallr = math.radians(fall)
    def T(u, v):
        if kneel:
            if v >= 0.5: v -= 0.24
            else: v *= 0.52; u -= 0.10 * (1 - v)
        hv = hipv - (0.24 if kneel else 0)
        if bowr and v > hv:
            du, dv = u, v - hv
            u = du * math.cos(bowr) + dv * math.sin(bowr)
            v = hv - du * math.sin(bowr) + dv * math.cos(bowr)
        if fallr:
            u, v = (u * math.cos(fallr) - v * math.sin(fallr), u * math.sin(fallr) + v * math.cos(fallr))
        return (x + dir * u * h, y - v * h)
    def poly(pts): d.polygon([T(*p) for p in pts], fill=255)
    def line(a, b, w): d.line([T(*a), T(*b)], fill=255, width=max(1, int(w * h)))
    def circ(c, r):
        cx, cy = T(*c); d.ellipse((cx - r * h, cy - r * h, cx + r * h, cy + r * h), fill=255)

    if robe:
        poly([(-0.085, 0.80), (0.085, 0.80), (0.10, 0.55), (0.19, 0.0), (-0.22, 0.0), (-0.11, 0.55)])
    else:
        poly([(-0.08, 0.80), (0.08, 0.80), (0.07, 0.50), (-0.07, 0.50)])
        poly([(-0.09, 0.53), (0.09, 0.53), (0.12, 0.38), (-0.12, 0.38)])
        sw = 0.45 * math.sin(ph) if ph is not None else 0.12
        for sgn in (1, -1):
            a = sgn * sw
            knee = (0.0 + 0.24 * math.sin(a), 0.45 - 0.24 * math.cos(a))
            b = a - 0.35 * max(0, math.sin((ph or 0) + (0 if sgn > 0 else math.pi) + 1.2))
            foot = (knee[0] + 0.24 * math.sin(b), knee[1] - 0.24 * math.cos(b))
            line((0, 0.45), knee, 0.06); line(knee, foot, 0.055)
            line(foot, (foot[0] + 0.07, foot[1]), 0.04)
    circ((0.0, 0.895), 0.068)
    if hat == 'knot': circ((-0.035, 0.965), 0.032)
    elif hat == 'crown':
        poly([(-0.12, 0.965), (0.14, 0.975), (0.14, 0.995), (-0.12, 0.99)])
        poly([(-0.02, 0.96), (0.03, 0.96), (0.03, 0.975), (-0.02, 0.975)])
        for uu in (0.13, -0.11):
            for k in range(3):
                line((uu, 0.975), (uu + 0.002 * k, 0.90 - 0.01 * k), 0.008)
    elif hat == 'helmet':
        poly([(-0.08, 0.90), (-0.07, 0.97), (0.0, 0.995), (0.07, 0.97), (0.08, 0.90)])
        line((0.0, 0.99), (-0.05, 1.08), 0.02)
    if female:
        circ((-0.075, 0.935), 0.05); line((-0.13, 0.96), (-0.02, 0.98), 0.012)
    # arms
    def arm_shape(angle):
        sh = (0.02, 0.77)
        ar = math.radians(angle)
        end = (sh[0] + 0.32 * math.sin(ar), sh[1] - 0.32 * math.cos(ar))
        if robe:
            nx, ny = math.cos(ar), math.sin(ar)
            poly([(sh[0] - 0.045 * nx, sh[1] - 0.045 * ny), (sh[0] + 0.045 * nx, sh[1] + 0.045 * ny),
                  (end[0] + 0.075 * nx, end[1] + 0.075 * ny), (end[0] - 0.06 * nx, end[1] - 0.06 * ny)])
        else:
            line(sh, end, 0.05)
        return end
    hand = arm_shape(70 if baby else arm)
    if arm2 is not None: arm_shape(arm2)
    if baby:
        poly(ellipse_pts(0.13, 0.70, 0.075, 0.05, 14)); circ((0.19, 0.74), 0.035)
    if load:
        poly([(-0.13, 1.0), (0.10, 1.0), (0.12, 1.12), (-0.11, 1.13)])
    if spear:
        a = math.radians(12)
        p0 = (hand[0] - 0.45 * math.sin(a), hand[1] - 0.45 * math.cos(a))
        p1 = (hand[0] + 0.95 * math.sin(a), hand[1] + 0.95 * math.cos(a))
        line(p0, p1, 0.016)
        tip = (p1[0] + 0.12 * math.sin(a), p1[1] + 0.12 * math.cos(a))
        poly([(p1[0] - 0.025, p1[1]), (p1[0] + 0.025, p1[1]), tip])
    if sword is not None:
        ar = math.radians(sword)
        tip = (hand[0] + 0.55 * math.sin(ar), hand[1] - 0.55 * math.cos(ar))
        line(hand, tip, 0.02)
        line((hand[0] - 0.05 * math.cos(ar), hand[1] - 0.05 * math.sin(ar)),
             (hand[0] + 0.05 * math.cos(ar), hand[1] + 0.05 * math.sin(ar)), 0.02)
    return T(*hand)

def horse(A, x, y, s, dir=1, ph=0.0, head_down=0, layer='ink', moving=True):
    d = A.d[layer]
    hd = math.radians(head_down)
    def T(u, v, neck=False):
        if neck and hd: u, v = rotp((u, v), (0.32, 0.66), -hd)
        return (x + dir * u * s, y - v * s)
    def poly(pts, neck=False): d.polygon([T(u, v, neck) for u, v in pts], fill=255)
    def line(a, b, w): d.line([T(*a), T(*b)], fill=255, width=max(1, int(w * s)))
    poly(ellipse_pts(0.0, 0.62, 0.42, 0.15))
    poly([(0.26, 0.72), (0.40, 0.52), (0.60, 0.92), (0.50, 1.00)], True)
    poly([(0.48, 1.0), (0.58, 1.04), (0.82, 0.84), (0.77, 0.78), (0.62, 0.82), (0.56, 0.90)], True)
    poly([(0.52, 1.01), (0.55, 1.10), (0.58, 1.02)], True)
    for k in range(4):
        line((0.40 - 0.05 * k, 0.92 - 0.08 * k), (0.33 - 0.07 * k, 0.98 - 0.09 * k), 0.03)
    sw = math.sin(ph * 1.3) * 0.06
    poly([(-0.40, 0.70), (-0.56, 0.66 + sw), (-0.66, 0.40 + sw), (-0.50, 0.56)])
    for hipu, off in ((0.28, 0.0), (0.22, 0.6), (-0.30, 2.2), (-0.36, 2.8)):
        a = 0.55 * math.sin(ph + off) if moving else 0.05
        knee = (hipu + 0.25 * math.sin(a), 0.55 - 0.25 * math.cos(a))
        b = a + (0.6 * max(0, math.sin(ph + off + 1.4)) if moving else 0) * (1 if hipu > 0 else -1)
        hoof = (knee[0] + 0.24 * math.sin(b), knee[1] - 0.24 * math.cos(b))
        line((hipu, 0.58), knee, 0.06); line(knee, hoof, 0.045)

def carriage(A, x, y, s, dir=1, wheel=0.0, ph=0.0, moving=True, horses=True, layer='ink', canopy=True):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    def poly(pts): d.polygon([T(*p) for p in pts], fill=255)
    def line(a, b, w): d.line([T(*a), T(*b)], fill=255, width=max(1, int(w * s)))
    wc = (-0.12, 0.32); r = 0.32
    cx, cy = T(*wc)
    d.ellipse((cx - r * s, cy - r * s, cx + r * s, cy + r * s), outline=255, width=max(2, int(0.04 * s)))
    for k in range(8):
        a = wheel + k * math.pi / 8 * 2
        d.line((cx, cy, cx + r * s * math.cos(a), cy + r * s * math.sin(a)), fill=255, width=max(1, int(0.018 * s)))
    poly([(-0.48, 0.42), (0.24, 0.42), (0.24, 0.74), (-0.48, 0.74)])
    if canopy:
        line((-0.12, 0.74), (-0.12, 1.12), 0.025)
        arc = [(-0.62 + 1.0 * i / 16, 1.04 + 0.16 * math.sin(math.pi * i / 16)) for i in range(17)]
        poly(arc + [(0.38, 1.02), (-0.62, 1.02)])
    line((0.24, 0.50), (0.95, 0.66), 0.03)
    person(A, x + dir * 0.10 * s, y - 0.62 * s, 0.42 * s, dir=dir, arm=60, layer=layer)
    if horses:
        horse(A, x + dir * 1.12 * s, y, 0.86 * s, dir, ph, layer=layer, moving=moving)
        horse(A, x + dir * 1.30 * s, y, 0.86 * s, dir, ph + 0.9, layer='mid' if layer == 'ink' else 'wash', moving=moving)

def palace(A, x, y, s, collapse=0.0, layer='ink'):
    d = A.d[layer]; dm = A.d['mid']
    def T(u, v): return (x + u * s, y - v * s)
    def poly(pts, dd=None, rot=0, c=(0, 0), drop=0):
        q = [rotp(p, c, rot) for p in pts]
        (dd or d).polygon([T(u, v - drop) for u, v in q], fill=255)
    poly([(-0.72, 0), (0.72, 0), (0.62, 0.10), (-0.62, 0.10)])
    poly([(-0.56, 0.10), (0.56, 0.10), (0.50, 0.20), (-0.50, 0.20)])
    poly([(-0.12, 0.0), (0.12, 0.0), (0.09, 0.20), (-0.09, 0.20)], dm)
    poly([(-0.42, 0.20), (0.42, 0.20), (0.42, 0.50), (-0.42, 0.50)], dm)
    for i in range(9):
        u = -0.40 + i * 0.1
        poly([(u, 0.20), (u + 0.035, 0.20), (u + 0.035, 0.50), (u, 0.50)])
    rot1 = collapse * 0.25; drop1 = collapse * 0.12
    poly([(-0.70, 0.56), (-0.64, 0.52), (-0.50, 0.50), (0.50, 0.50), (0.64, 0.52), (0.70, 0.56),
          (0.44, 0.66), (-0.44, 0.66)], rot=-rot1 * 0.3, c=(0, 0.5), drop=drop1 * 0.3)
    poly([(-0.26, 0.66), (0.26, 0.66), (0.26, 0.76), (-0.26, 0.76)], dm, rot=rot1 * 0.5, c=(0, 0.66), drop=drop1)
    poly([(-0.48, 0.80), (-0.42, 0.77), (-0.30, 0.76), (0.30, 0.76), (0.42, 0.77), (0.48, 0.80),
          (0.26, 0.90), (-0.26, 0.90)], rot=rot1, c=(0, 0.76), drop=drop1 * 2)
    poly([(-0.27, 0.90), (-0.22, 0.93), (0.22, 0.93), (0.27, 0.90)], rot=rot1, c=(0, 0.76), drop=drop1 * 2)

def flames(A, x, y, w, h, t, n=7, seed=0, smoke=True):
    r = random.Random(seed)
    d = A.d['red']
    def tongue(fx, fw, fh, sway, fill):
        left, right = [], []
        for j in range(13):
            sv = j / 12
            half = fw / 2 * (1 - sv) ** 0.6 * (1 + 0.35 * math.sin(sv * math.pi))
            cx = fx + sway * sv ** 1.3 + fw * 0.12 * math.sin(sv * 4.5 + t * 9 + fx)
            left.append((cx - half, y - fh * sv)); right.append((cx + half, y - fh * sv))
        d.polygon(left + right[::-1], fill=fill)
    for i in range(n):
        fx = x - w / 2 + w * (i + 0.5) / n + r.uniform(-12, 12)
        fh = h * r.uniform(0.45, 1.0) * (0.8 + 0.2 * math.sin(t * 11 + i * 2.1))
        fw = w / n * 2.5
        sway = 40 * math.sin(t * 6 + i * 1.3) * fh / max(1, h)
        tongue(fx, fw, fh, sway, 255)
    for i in range(n):  # inner cut-outs give layered flame shapes
        fx = x - w / 2 + w * (i + 0.5) / n + r.uniform(-8, 8)
        fh = h * r.uniform(0.25, 0.5) * (0.8 + 0.2 * math.sin(t * 13 + i))
        tongue(fx, w / n * 0.7, fh, 25 * math.sin(t * 8 + i), 90)
    # sparks
    for k in range(10):
        q = (t * 0.8 + k * 0.1) % 1
        sx = x + (r.uniform(-0.5, 0.5)) * w + 30 * math.sin(t * 3 + k)
        sy = y - h * 0.6 - q * h * 0.9
        d.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=int(255 * (1 - q)))
    if smoke:
        dw = A.d['wash']
        for j in range(6):
            k = (t * 90 + j * 55) % 330
            sx = x + 40 * math.sin(j * 1.7 + t) + k * 0.25
            sy = y - h * 0.8 - k
            rr = 30 + k * 0.25
            dw.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=255)

def waves(A, y0, t, rows=4, amp=12, x0=0, x1=W, speed=2.0):
    for r in range(rows):
        lay = 'ink' if r == rows - 1 else ('mid' if r >= rows - 2 else 'wash')
        d = A.d[lay]
        yb = y0 + r * 34
        ph = t * speed * (1 + 0.25 * r) + r * 1.3
        pts = [(x, yb + amp * math.sin(x * 0.018 + ph)) for x in range(x0, x1 + 8, 8)]
        d.line(pts, fill=255, width=4 if lay == 'ink' else 6)
        for cx in range(x0 + int((ph * 55) % 150), x1, 150):
            cy = yb + amp * math.sin(cx * 0.018 + ph)
            d.arc((cx - 16, cy - 22, cx + 16, cy + 6), 180, 340, fill=255, width=4)

def boat(A, x, y, s, t, sail=True):
    d = A.d['ink']
    bob = math.sin(t * 3) * 0.03
    def T(u, v): return (x + u * s, y - (v + bob) * s)
    d.polygon([T(-0.55, 0.18), T(0.55, 0.20), T(0.42, 0.0), T(-0.40, 0.0)], fill=255)
    d.line([T(0, 0.18), T(0, 1.05)], fill=255, width=max(2, int(0.025 * s)))
    if sail:
        bil = 0.05 * math.sin(t * 2)
        A.d['mid'].polygon([T(0.03, 1.0), T(0.03, 0.30), T(0.40 + bil, 0.34), T(0.38 + bil, 0.95)], fill=255)
        for k in range(5):
            yy = 0.36 + k * 0.13
            d.line([T(0.03, yy), T(0.39 + bil, yy + 0.01)], fill=255, width=2)
    person(A, x - 0.25 * s, y - (0.18 + bob) * s, 0.42 * s, arm=40, layer='ink')

def crow(A, x, y, s, flap):
    d = A.d['ink']
    f = math.sin(flap)
    d.ellipse((x - s * 0.25, y - s * 0.1, x + s * 0.25, y + s * 0.1), fill=255)
    d.line([(x - s, y - s * 0.5 * f), (x - s * 0.4, y - s * 0.2 * f - s * 0.1), (x, y)], fill=255, width=max(2, int(s * 0.12)))
    d.line([(x + s, y - s * 0.5 * f), (x + s * 0.4, y - s * 0.2 * f - s * 0.1), (x, y)], fill=255, width=max(2, int(s * 0.12)))

def arrow(A, x, y, ang, L=90):
    d = A.d['ink']
    ex, ey = x + L * math.cos(ang), y + L * math.sin(ang)
    d.line((x, y, ex, ey), fill=255, width=3)
    hx, hy = math.cos(ang), math.sin(ang)
    d.polygon([(ex + hx * 16, ey + hy * 16), (ex - hy * 6, ey + hx * 6), (ex + hy * 6, ey - hx * 6)], fill=255)
    for k in (0, 8):
        d.line((x + hx * k, y + hy * k, x + hx * k - hy * 10 - hx * 8, y + hy * k + hx * 10 - hy * 8), fill=255, width=2)

def flag(A, x, y, h, t, w=90, layer='red', pole='ink'):
    A.d[pole].line((x, y, x, y - h), fill=255, width=6)
    pts_top = [(x + i * w / 10, y - h + 6 * math.sin(t * 6 + i * 0.7)) for i in range(11)]
    pts_bot = [(x + i * w / 10, y - h + w * 0.6 + 6 * math.sin(t * 6 + i * 0.7)) for i in range(10, -1, -1)]
    A.d[layer].polygon(pts_top + pts_bot, fill=255)

def ground(A, y, x0=60, x1=W - 60, seed=1):
    r = random.Random(seed)
    d = A.d['wash']
    d.rectangle((x0, y - 6, x1, y + 26), fill=255)
    for _ in range(18):
        gx = r.uniform(x0, x1)
        d.line((gx, y + r.uniform(0, 20), gx + r.uniform(40, 160), y + r.uniform(0, 20)), fill=255, width=4)

def sun(canvas, cx, cy, r, col=ZHU, alpha=150):
    s = Image.new('RGBA', (int(r * 2 + 20), int(r * 2 + 20)), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((10, 10, 10 + 2 * r, 10 + 2 * r), fill=col + (alpha,))
    s = s.filter(ImageFilter.GaussianBlur(4))
    canvas.alpha_composite(s, (int(cx - r - 10), int(cy - r - 10)))

def walk_x(x0, x1, u, dur): return lerp(x0, x1, clamp(u / dur))

# ================================================================ story scenes (u = time since scene start)
def art_child_king(A, cv, t, u):
    ground(A, GROUND)
    d = A.d['mid']
    d.polygon([(330, GROUND), (750, GROUND), (720, 1340), (360, 1340)], fill=255)
    A.d['ink'].polygon([(470, 1340), (610, 1340), (610, 1210), (590, 1110), (490, 1110), (470, 1210)], fill=255)
    A.d['ink'].rectangle((430, 1180, 650, 1200), fill=255)
    bx = walk_x(400, 540, u, 0.5)
    person(A, bx, 1340, 175, dir=1, hat='crown', ph=None, arm=20 if u < 0.5 else 70, layer='ink')
    b = 55 * ease_out((u - P) / 0.25)
    for i, xx in enumerate((150, 255)):
        person(A, xx, GROUND, 230, dir=1, bow=b, arm=40, layer='ink' if i else 'mid')
    for i, xx in enumerate((930, 825)):
        person(A, xx, GROUND, 230, dir=-1, bow=b, arm=40, layer='ink' if i else 'mid')

def art_army(A, cv, t, u):
    ground(A, GROUND)
    for row, (yy, hh, lay, sp, gap) in enumerate([(1250, 100, 'wash', 60, 85), (1330, 140, 'mid', 95, 115), (GROUND, 190, 'ink', 140, 160)]):
        off = (t * sp) % gap
        for i in range(-1, W // gap + 2):
            x = i * gap + off - 40
            person(A, x, yy, hh, dir=1, robe=False, hat='helmet', ph=t * 7 + i * 0.9 + row, spear=True, arm=30, layer=lay)
        if lay != 'wash':
            for i in range(0, W // gap + 2, 3):
                fx = i * gap + off + 10
                flag(A, fx, yy - hh * 0.95, hh * 0.6, t + i, w=hh * 0.45, layer='red' if lay == 'ink' else 'mid')
    if u > P:
        v = ease_out((u - P) / 0.3)
        flag(A, 820, lerp(1500, GROUND, v), 520, t, w=240)

def art_last_journey(A, cv, t, u):
    sun(cv, 790, 820, 120, (110, 100, 95), 110)
    ground(A, GROUND)
    stop = clamp((u - P) / 0.3)
    speed = 1 - ease_out(stop)
    x = 260 + 260 * ease_out(u / (2 * P)) if True else 0
    carriage(A, x, GROUND, 230, dir=1, wheel=t * 4 * speed, ph=t * 9 * speed, moving=speed > 0.3)
    for k in range(9):
        A.d['wash'].line((80 + k * 110 - (t * 120 * speed) % 110, GROUND + 40, 140 + k * 110 - (t * 120 * speed) % 110, GROUND + 40), fill=255, width=4)
    if u > P:
        for k in range(3):
            a = t * 1.8 + k * 2.1
            crow(A, 560 + 200 * math.cos(a), 900 + 60 * math.sin(a), 26, t * 12 + k)

def art_emperor(A, cv, t, u):
    sun(cv, 600, 1000, 250, ZHU, 140)
    ground(A, 1440)
    arm = lerp(-5, 55, ease_out(u / (2 * P)))
    person(A, 470, 1440, 700, dir=1, hat='crown', arm=arm, layer='ink')
    for k in range(3):
        y = 820 + k * 70
        x = (t * 70 + k * 300) % (W + 400) - 200
        A.d['wash'].line((x, y, x + 260, y), fill=255, width=14)

def art_handan(A, cv, t, u):
    d = A.d['mid']
    d.rectangle((60, 1150, W - 60, GROUND), fill=255)
    for x in range(60, W - 60, 46): d.rectangle((x, 1122, x + 26, 1150), fill=255)
    A.d['ink'].polygon([(340, 1160), (740, 1160), (690, 1050), (390, 1050)], fill=255)
    A.d['ink'].polygon([(300, 1060), (780, 1060), (720, 1000), (360, 1000)], fill=255)
    A.d['ink'].polygon([(400, 1000), (680, 1000), (640, 960), (440, 960)], fill=255)
    d.rectangle((470, 1250, 610, GROUND), fill=0)
    d.pieslice((470, 1180, 610, 1320), 180, 360, fill=0)
    A.d['ink'].rectangle((485, 1068, 595, 1140), fill=255)
    f = font(SERIF, 40, 'Black')
    A.d['ink'].text((497, 1080), '邯郸', font=f, fill=0)
    A.d['wash'].ellipse((800, 700, 920, 820), fill=255); A.d['wash'].ellipse((830, 690, 950, 810), fill=0)
    mx = walk_x(860, 700, u, 2 * P)
    person(A, mx, GROUND, 250, dir=-1, female=True, baby=True, layer='ink')
    if u > P:
        for k in range(3):
            gx = 150 + k * 90
            person(A, gx, GROUND, 210, dir=1, robe=False, hat='helmet', spear=True, arm=25, layer='mid', ph=None)

def art_escape(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        gx = (k * 130 - t * 520) % (W + 200) - 100
        A.d['mid'].line((gx, GROUND + 4, gx + 60, GROUND + 4), fill=255, width=5)
        A.d['wash'].line((gx + 40, GROUND - 30, gx + 55, GROUND - 2), fill=255, width=3)
    mx = 720 + 20 * math.sin(t * 3)
    person(A, mx, GROUND - abs(math.sin(t * 12)) * 12, 240, dir=1, female=True, baby=True, robe=False, ph=t * 12, layer='ink')
    for k in range(3):
        sx = 160 + k * 120 + 30 * math.sin(t * 2 + k)
        person(A, sx, GROUND - abs(math.sin(t * 11 + k)) * 10, 230 - k * 10, dir=1, robe=False, hat='helmet',
               spear=True, arm=45, ph=t * 11 + k, layer='ink' if k == 2 else 'mid')
    n = 4 if u < P else 9
    for k in range(n):
        q = (u * 1.4 + k * 0.17) % 1.0
        x = lerp(80, 980, q); y = 900 - 260 * math.sin(math.pi * q) + k * 22
        ang = math.atan2(-260 * math.pi * math.cos(math.pi * q), 900)
        arrow(A, x, y, ang)

def art_throne(A, cv, t, u):
    palace(A, 540, 1330, 640, layer='mid')
    A.d['wash'].rectangle((60, 1330, W - 60, GROUND + 20), fill=255)
    by = lerp(GROUND, 1330, ease_out(u / (1.6 * P)))
    person(A, 540, by, 150, dir=-1, hat='crown', ph=t * 6, robe=True, layer='ink')
    for i, xx in enumerate((150, 280)):
        person(A, xx, GROUND, 200, dir=1, kneel=True, bow=40 + 15 * ease_out((u - P) / 0.25), arm=60, layer='ink')
    for i, xx in enumerate((930, 800)):
        person(A, xx, GROUND, 200, dir=-1, kneel=True, bow=40 + 15 * ease_out((u - P) / 0.25), arm=60, layer='ink')

def art_purge(A, cv, t, u):
    ground(A, GROUND)
    swing = ease_expo((u - P) / 0.18)
    sw_ang = lerp(160, 70, swing)
    person(A, 300, GROUND, 330, dir=1, hat='crown', arm=sw_ang, sword=sw_ang, layer='ink')
    if u > P:
        v = u - P
        al = clamp(1 - (v - 0.15) / 0.4)
        if al > 0:
            pts = [(330 + 520 * math.cos(math.radians(a)), 1180 - 360 * math.sin(math.radians(a))) for a in range(60, -25, -5)]
            inner = [(330 + 470 * math.cos(math.radians(a)), 1180 - 320 * math.sin(math.radians(a))) for a in range(-20, 65, 5)]
            A.d['red'].polygon(pts + inner, fill=int(255 * al))
    for k in range(3):
        rx = 640 + k * 130
        fall = -75 * ease_out((u - P - 0.06 * k) / 0.3) if u > P else 0
        person(A, rx, GROUND, 240, dir=-1, robe=False, hat='helmet', spear=True, arm=30, fall=fall, layer='ink' if k == 0 else 'mid')

def art_enthrone(A, cv, t, u):
    d = A.d['mid']
    d.polygon([(380, GROUND), (700, GROUND), (660, 1290), (420, 1290)], fill=255)
    A.d['ink'].polygon([(470, 1290), (610, 1290), (600, 1200), (480, 1200)], fill=255)
    person(A, 540, 1200, 230, dir=1, hat='crown', arm=50, layer='ink')
    flag(A, 330, 1290, 330, t, w=110); flag(A, 760, 1290, 330, t + 1, w=110)
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.12)
    b = 35 + 30 * hit
    for i, xx in enumerate((110, 220)):
        person(A, xx, GROUND, 190, dir=1, kneel=True, bow=b, arm=60, layer='ink' if i else 'mid')
    for i, xx in enumerate((970, 860)):
        person(A, xx, GROUND, 190, dir=-1, kneel=True, bow=b, arm=60, layer='ink' if i else 'mid')

def art_slips(A, cv, t, u):
    n = 13
    p = ease_out(u / 0.45)
    f = font(BRUSH, 52)
    chars = '书同文字车同轨行同伦'
    for i in range(int(n * p) + 1):
        if i >= n: break
        x = 860 - i * 50
        A.d['mid'].rectangle((x - 20, 820, x + 20, 1330), fill=255)
        if i < len(chars):
            for j in range(1):
                A.d['ink'].text((x - 26, 880 + (i % 3) * 120), chars[i], font=f, fill=255)
    if p > 0.05:
        x_end = 860 - int(n * p) * 50
        A.d['ink'].line((x_end - 20, 900, 880, 900), fill=255, width=4)
        A.d['ink'].line((x_end - 20, 1250, 880, 1250), fill=255, width=4)
        A.d['ink'].ellipse((x_end - 60, 820, x_end + 10, 1330), fill=255)

def art_ruts(A, cv, t, u):
    for yy in (GROUND + 8, GROUND + 34):
        A.d['ink'].line((60, yy, W - 60, yy), fill=255, width=5)
    x = lerp(880, 300, ease_out(u / 0.55))
    carriage(A, x, GROUND, 200, dir=-1, wheel=-t * 6, ph=t * 10)
    for k in range(4):
        px = x + 160 + k * 50; rr = 20 + k * 12
        A.d['wash'].ellipse((px - rr, GROUND - rr - 10, px + rr, GROUND + rr - 10), fill=255)
    f = font(SERIF, 34, 'Bold')
    A.d['red'].text((470, GROUND + 48), '轨宽六尺', font=f, fill=255)

def art_scale(A, cv, t, u):
    cx, top = 540, 900
    d = A.d['ink']
    d.polygon([(470, GROUND), (610, GROUND), (560, GROUND - 40), (520, GROUND - 40)], fill=255)
    d.line((cx, GROUND - 40, cx, top), fill=255, width=12)
    ang = math.radians(22 * math.exp(-u * 5) * math.cos(u * 18))
    L = 320
    lx, ly = cx - L * math.cos(ang), top - L * math.sin(ang) * -1
    rx, ry = cx + L * math.cos(ang), top - L * math.sin(ang)
    d.line((lx, ly, rx, ry), fill=255, width=10)
    d.ellipse((cx - 14, top - 14, cx + 14, top + 14), fill=255)
    for (px, py), load in (((lx, ly), 'w'), ((rx, ry), 'g')):
        by = py + 220
        d.line((px, py, px - 70, by), fill=255, width=3); d.line((px, py, px + 70, by), fill=255, width=3)
        d.chord((px - 95, by - 40, px + 95, by + 40), 0, 180, fill=255)
        if load == 'w':
            A.d['mid'].rectangle((px - 35, by - 60, px + 35, by), fill=255)
        else:
            A.d['mid'].pieslice((px - 70, by - 50, px + 70, by + 50), 180, 360, fill=255)

def art_tree(A, cv, t, u):
    d = A.d['ink']
    p = ease_out(u / 0.4)
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
    stamp(cv, seal('皇', 70), top[0], top[1], t, bt(29))
    for m in mids: stamp(cv, seal('郡', 52), m[0], m[1], t, bt(29) + 0.12)
    for l in lows: stamp(cv, seal('县', 40), l[0], l[1], t, bt(29) + 0.25)

def art_taishan(A, cv, t, u):
    rise = ease_out(u / (2 * P))
    sun(cv, 540, lerp(1250, 960, rise), 210, ZHU, 150)
    d = A.d['ink']
    d.polygon([(120, GROUND), (420, 1150), (500, 1170), (560, 1080), (640, 1140), (960, GROUND)], fill=255)
    A.d['mid'].polygon([(0, GROUND), (200, 1250), (330, 1300), (300, GROUND)], fill=255)
    A.d['mid'].polygon([(760, GROUND), (900, 1240), (1080, 1300), (1080, GROUND)], fill=255)
    person(A, 560, 1085, 110, dir=1, hat='crown', arm=150, arm2=150, layer='ink')
    for k in range(4):
        y = 1180 + k * 55
        x = (t * 60 * (1 + k * 0.3) + k * 270) % (W + 500) - 300
        A.d['wash'].line((x, y, x + 320, y), fill=255, width=22)

def art_wall(A, cv, t, u):
    ground(A, GROUND + 40)
    for k in range(4):
        x = (t * 70 + k * 270) % (W + 200) - 100
        person(A, x, GROUND + 40, 170, dir=1, robe=False, ph=t * 6 + k, load=True, arm=160, layer='ink' if k % 2 else 'mid')
    for k in range(3):
        hx = 820 + k * 70 + t * 160 * (1 if u > P else 0.3)
        horse(A, hx % (W + 300), 1200 - k * 18, 70, dir=1, ph=t * 12 + k, layer='wash')

def art_road_canal(A, cv, t, u):
    A.d['wash'].rectangle((60, 1205, W - 60, 1222), fill=255)
    x = lerp(-200, 760, ease_out(u / (2 * P)))
    carriage(A, x, 1205, 150, dir=1, wheel=t * 9, ph=t * 14)
    for k in range(4):
        px = x - 120 - k * 45; rr = 16 + k * 10
        A.d['wash'].ellipse((px - rr, 1190 - rr, px + rr, 1190 + rr), fill=255)
    waves(A, 1290, t, rows=4, amp=10, speed=3)
    boat(A, lerp(850, 420, ease_out(u / (2 * P))), 1330, 130, t)

def art_burn(A, cv, t, u):
    ground(A, GROUND)
    d = A.d['mid']
    for row, n in enumerate((6, 5, 4)):
        for i in range(n):
            x = 540 - (n - 1) * 52 + i * 104
            y = GROUND - 30 - row * 56
            d.rounded_rectangle((x - 50, y - 26, x + 50, y + 26), radius=24, fill=255)
            A.d['ink'].ellipse((x + 30, y - 26, x + 54, y + 26), outline=255, width=4)
    grow = 0.55 + 0.45 * ease_out((u - P) / 0.3) if u > P else ease_out(u / 0.4) * 0.55
    flames(A, 540, GROUND - 40, 560, 520 * grow, t, n=9, seed=4)
    for k in range(6):
        q = (u * 0.9 + k * 0.17) % 1
        sx = 540 + (k - 2.5) * 70 + q * 120 * math.sin(k)
        sy = GROUND - 250 - q * 520
        a = q * 6 + k
        pts = [rotp(p, (sx, sy), a) for p in ((sx - 8, sy - 30), (sx + 8, sy - 30), (sx + 8, sy + 30), (sx - 8, sy + 30))]
        A.d['ink'].polygon(pts, fill=255)
    person(A, 150, GROUND, 200, dir=1, kneel=True, bow=55, arm=70, layer='ink')
    person(A, 930, GROUND, 200, dir=-1, kneel=True, bow=55, arm=70, layer='ink')

def art_sea(A, cv, t, u):
    A.d['wash'].ellipse((760, 720, 900, 860), fill=255)
    A.d['mid'].polygon([(700, 1260), (790, 1100), (840, 1150), (900, 1050), (1000, 1180), (1080, 1260)], fill=255)
    for k in range(3):
        y = 1150 + k * 30
        x = (t * 40 + k * 200) % 600 + 600
        A.d['wash'].line((x, y, x + 260, y), fill=255, width=18)
    x = lerp(220, 520, ease_out(u / (2 * P)))
    boat(A, x, 1300, 260, t)
    waves(A, 1300, t, rows=4, amp=14, speed=2.5)

def art_shaqiu(A, cv, t, u):
    d = A.d['mid']
    for k, (y0, amp, ph) in enumerate(((1300, 60, 0.4), (1370, 40, 2.0))):
        pts = [(x, y0 - amp * math.sin(x * 0.006 + ph)) for x in range(60, W - 59, 10)]
        (A.d['wash'] if k == 0 else d).polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=255)
    carriage(A, 430, 1360, 220, dir=1, wheel=0.3, moving=False)
    for k in range(5):
        a = t * 1.5 + k * 1.26
        crow(A, 540 + 260 * math.cos(a), 880 + 80 * math.sin(a), 24, t * 11 + k)
    if u > P:
        f = font(SERIF, 34, 'Bold')
        A.d['mid'].text((700, 1100), '“祖龙死”', font=f, fill=255)

def art_fall(A, cv, t, u):
    palace(A, 540, GROUND, 760, collapse=ease_out((u - P) / 0.4) if u > P else 0)
    big = 0.5 + 0.5 * ease_out((u - P) / 0.3) if u > P else 0.35 + 0.15 * ease_out(u / 0.4)
    flames(A, 540, GROUND - 60, 820, 560 * big, t, n=11, seed=9)

def art_end(A, cv, t, u):
    person(A, 230, 1700, 760, dir=1, hat='crown', arm=20, layer='wash')

# ================================================================ text layouts (top band; stage below)
def year_line(cv, t, year, start):
    s = '公元前' + cn_num(year) + '年'
    im = text_img(s, SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=ZHU + (220,), width=3)

def stage(cv, t, c, fn, extra_reveal=True):
    A = Art()
    u = t - bt(c[0])
    fn(A, cv, t, u)
    A.flush(cv, reveal=ease_out(u / 0.35) if extra_reveal else None)

ART = {}

def scene_num(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    stage(cv, t, c, ART[c[0]])
    d = c[4]
    ink_in(cv, text_img(d['num'], BRUSH, 150, G.INK), W / 2, 470, t, s0)
    ink_in(cv, text_img(d['line'], BRUSH, 92, ZHU), W / 2, 600, t, s1, dur=0.25)

def scene_title(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    stage(cv, t, c, art_emperor)
    ink_in(cv, text_img('嬴 政', SERIF, 50, ZHE, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    ink_in(cv, text_img('秦始皇', BRUSH, 200, G.INK), W / 2, 450, t, s0, dur=0.35)
    stamp(cv, seal('千古一帝', 58), 880, 640, t, s1, rot=-5)

def scene_card(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    stage(cv, t, c, ART[c[0]])
    year_line(cv, t, d['year'], s0)
    main = d['main'].replace('\n', ' ')
    ink_in(cv, text_img(main, BRUSH, 150 if len(main) <= 5 else 120, G.INK), W / 2, 435, t, s0)
    if t >= s1:
        sub = text_img(d['sub'], SERIF, 40, (70, 50, 30), 'SemiBold', bleed=False, spacing=3)
        v = t - s1
        paste(cv, sub, W / 2, lerp(565, 550, ease_out(v / 0.3)), 1, clamp(v / 0.15))
        if 'seal' in d:
            stamp(cv, seal(d['seal'], 60), W / 2 + 330, 420, t, s1, rot=6)

LIST_ART = [art_slips, art_ruts, art_scale, art_tree]
def scene_list(cv, t, c, k):
    i = min(3, int(k - c[0]))
    st = bt(c[0] + i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    year_line(cv, t, 221, bt(24))
    it = c[4]['items'][i]
    ink_in(cv, text_img(it, BRUSH, 140 if len(it) <= 5 else 120, G.INK), W / 2, 440, t, st, dur=0.22)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            paste(cv, seal('壹贰叁肆'[j], 36), x, 575, 1, 1)
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=ZHU + (110,), width=2)

def scene_end(cv, t, c, k):
    A = Art(); art_end(A, cv, t, t - bt(44)); A.flush(cv, alpha=clamp((t - bt(44)) / 0.6))
    G.scene_end_orig(cv, t, c, k)

G.scene_end_orig = G.scene_end
_orig_wall = G.draw_wall
G.draw_wall = lambda cv, t, off: _orig_wall(cv, t, off) if t < bt(34) else None
G.SCENES.update(num=scene_num, title=scene_title, card=scene_card, list=scene_list, end=scene_end)
ART.update({0: art_child_king, 2: art_army, 4: art_last_journey, 8: art_handan, 10: art_escape, 12: art_throne,
            14: art_purge, 24: art_enthrone, 30: art_taishan, 32: art_wall, 34: art_road_canal, 36: art_burn,
            38: art_sea, 40: art_shaqiu, 42: art_fall})

# hook question higher up so the stage below stays clear
def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第壹集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(6):
        q = text_img('史上第一位皇帝 · 一生到底有多狠？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=ZHU + (220,), width=3)
    G_draw_timeline(canvas, t)

_orig_hud = G.draw_hud
def G_draw_timeline(canvas, t):
    # reuse original timeline part only (skip its title/question drawing) by masking time window
    if bt(8) - 0.15 <= t < bt(44):
        tmp = Image.new('RGBA', (W, 200), (0, 0, 0, 0))
        big = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        _orig_hud(big, t)
        canvas.alpha_composite(big.crop((0, 1440, W, 1640)), (0, 1440))
G.draw_hud = draw_hud

# cover frame (first 0.4s): finished title shot, then ink-wipe into the story on beat 0
_orig_compose = G.compose
G.compose = lambda t: _orig_compose(bt(8) - 0.2 if t < G.B0 else t)
G.CHAPTER_BEATS.insert(0, 0)

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    render = G.render
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(G.DUR * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', os.path.join(HERE, 'music_clean.wav'),
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 120 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
