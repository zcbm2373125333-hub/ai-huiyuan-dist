# 千古人物志 · 第陆集 · 明太祖朱元璋 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈）。本集原则：每一幕画面都是新画的、不重复。
# 本集特色：青花瓷配色 · 「五件物」章回卡（破碗 红巾 战船 玉玺 荆杖）· 缠枝纹边角 · 八拍「鄱阳湖火攻」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_songtaizu as St      # engine + helpers from earlier episodes
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
from render_songtaizu import tent, campfire

F.RIPPLE = False

BORN, DIED = 1328, 1398
END_BEAT = 170
COBALT = (38, 72, 150)              # 青花
S.LAYERS.append(('cobalt', COBALT, 0.80, 1.3))

DIG = '〇一二三四五六七八九'
def cn_year(y): return ''.join(DIG[int(ch)] for ch in str(y))

# ================================================================ episode look
WM = dict(hook='明', life='璋', court='谋', night='饥', war='戰', empire='洪', works='武', fate='孤', death='陵', end='明')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'fate', 'empire'):
    G.THEMES[k]['part'] = 'cobalt'
for k in ('night', 'death'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['empire']['sun'] = (ZHU, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (COBALT, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (COBALT, 200, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.98, 0.99, 1.02)
G.base_bg.cache_clear()

MTN_COL = {'night': (52, 52, 64), 'death': (60, 60, 66), 'war': (96, 56, 50)}
def draw_background(t, theme):
    """青花: distant ranges painted in cobalt washes like blue-and-white porcelain."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(132, 150, 196), (86, 108, 168), MTN_COL.get(theme, (50, 66, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'cobalt':
        return St.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(56, 90, 170), (96, 126, 196), (40, 66, 140)][q]
    d.ellipse((11, 15, 29, 26), fill=col + (215,))
    d.line((13, 20, 27, 21), fill=(250, 250, 255, 160), width=1)
    return im.filter(ImageFilter.GaussianBlur(0.6))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """青花缠枝: cobalt scroll-vine corner ornaments."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = COBALT + (200,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 150, y), fill=col, width=3); d.line((x, y, x, y + sy * 150), fill=col, width=3)
        pts = []
        for i in range(30):
            a = i * 0.32
            r = 26 - i * 0.7
            pts.append((x + sx * (40 + r * math.cos(a)), y + sy * (40 + r * math.sin(a))))
        d.line(pts, fill=col, width=3)
        for k in range(3):
            lx, ly = x + sx * (70 + k * 26), y + sy * (12 + (k % 2) * 8)
            d.ellipse((lx - 6, ly - 4, lx + 6, ly + 4), fill=col)
G.draw_frame_border = draw_frame_border

# ================================================================ 五件物 chapter cards
def obj_bowl(A, t, p):
    cx, cy = 540, 900
    w = 330 * ease_out(p)
    A.d['ink'].chord((cx - w, cy - 160, cx + w, cy + 220), 0, 180, fill=255)
    A.d['cobalt'].chord((cx - w * 0.92, cy - 140, cx + w * 0.92, cy + 200), 0, 180, fill=150)
    A.d['ink'].rectangle((cx - 90, cy + 210, cx + 90, cy + 240), fill=255)
    if p > 0.6:
        cr = ease_out((p - 0.6) / 0.4)
        A.d['wash'].line([(cx + 60, cy + 30), (cx + 90, cy + 90), (cx + 70, cy + 140), (cx + 100, cy + 30 + 170 * cr)], fill=255, width=6)
    for k in range(3):
        a = t * 0.8 + k * 2
        A.d['wash'].arc((cx - 60 + k * 40, cy - 120 - 30 * math.sin(a), cx + k * 40, cy - 60 - 30 * math.sin(a)), 200, 340, fill=255, width=5)

def obj_scarf(A, t, p):
    cx, cy = 540, 900
    n = int(16 * ease_out(p)) + 2
    top = [(cx - 360 + i * 45, cy - 60 + 30 * math.sin(t * 4 + i * 0.6)) for i in range(n)]
    bot = [(x, y + 120 + 10 * math.sin(t * 3 + i)) for i, (x, y) in enumerate(top)][::-1]
    A.d['red'].polygon(top + bot, fill=255)
    for k in range(2):
        tx = cx - 360 - 10
        A.d['red'].polygon([(tx, cy), (tx - 80, cy + 160 + 30 * math.sin(t * 3 + k)), (tx - 40 + k * 30, cy + 170)], fill=255)

def obj_ship(A, t, p):
    cx, cy = 540, 1000
    bob = 10 * math.sin(t * 2)
    w = 380 * ease_out(p)
    A.d['ink'].polygon([(cx - w, cy - 40 + bob), (cx + w, cy - 60 + bob), (cx + w * 0.8, cy + 50 + bob), (cx - w * 0.8, cy + 50 + bob)], fill=255)
    for k in range(3):
        mx = cx - 200 + k * 200
        A.d['ink'].line((mx, cy - 40 + bob, mx, cy - 420 + bob + k * 40), fill=255, width=6)
        A.d['mid'].polygon([(mx + 6, cy - 400 + bob + k * 40), (mx + 120, cy - 380 + bob + k * 40 + 10 * math.sin(t * 3 + k)), (mx + 110, cy - 120 + bob), (mx + 6, cy - 110 + bob)], fill=255)
    waves(A, int(cy + 40), t, rows=3, amp=12, speed=2.5, x0=100, x1=W - 100)

def obj_seal(A, t, p):
    """传国玉玺: jade cube with a coiled-dragon knob, and its red 大明 impression."""
    cx, cy = 430, 920
    s = 170 * ease_out(p)
    if s < 4: return
    A.d['cobalt'].rectangle((cx - s, cy - s * 0.1, cx + s, cy + s * 1.1), fill=170)
    A.d['ink'].rectangle((cx - s, cy - s * 0.1, cx + s, cy + s * 1.1), outline=255, width=6)
    A.d['ink'].line((cx - s, cy + s * 0.25, cx + s, cy + s * 0.25), fill=200, width=3)
    pts = []
    for i in range(40):                       # coiled dragon knob
        a = i * 0.36
        r = s * (0.55 - i * 0.010)
        pts.append((cx + r * math.cos(a), cy - s * 0.35 + r * 0.45 * math.sin(a)))
    A.d['ink'].line(pts, fill=255, width=max(4, int(s * 0.12)))
    A.d['ink'].ellipse((cx + s * 0.40, cy - s * 0.62, cx + s * 0.62, cy - s * 0.42), fill=255)
    if p > 0.6:
        q = ease_out((p - 0.6) / 0.4)
        sx, sy, w = 780, 1000, 150 * q
        A.d['red'].rectangle((sx - w, sy - w, sx + w, sy + w), fill=255)
        fo = font(SERIF, max(8, int(110 * q)), 'Black')
        A.d['red'].text((sx - w * 0.75, sy - w * 0.95), '大', font=fo, fill=0)
        A.d['red'].text((sx - w * 0.75, sy - w * 0.05), '明', font=fo, fill=0)

def obj_staff(A, t, p):
    x0, y0, x1, y1 = 260, 1240, 820, 680
    q = ease_out(p)
    xe, ye = lerp(x0, x1, q), lerp(y0, y1, q)
    A.d['ink'].line((x0, y0, xe, ye), fill=255, width=22)
    for k in range(14):
        f = (k + 0.5) / 14
        if f > q: break
        px, py = lerp(x0, x1, f), lerp(y0, y1, f)
        side = 1 if k % 2 else -1
        A.d['ink'].polygon([(px - 8, py), (px + 8, py), (px + side * 34, py - side * 34 + (-20))], fill=255)

OBJ = {16: obj_bowl, 48: obj_scarf, 80: obj_ship, 112: obj_seal, 144: obj_staff}
def art_object_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    OBJ.get(kb, obj_bowl)(A, t, clamp(u / 0.6))
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_object_chapter)
    ink_in(cv, text_img(no, SERIF, 56, COBALT, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives for this episode
def hut(A, x, base, w, h, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - h * 0.55, x + w / 2, base), fill=255)
    A.d[layer].polygon([(x - w / 2 - 30, base - h * 0.55), (x, base - h), (x + w / 2 + 30, base - h * 0.55)], fill=255)
    A.d['wash'].rectangle((x - w * 0.12, base - h * 0.35, x + w * 0.12, base), fill=0)
    for k in range(6):
        xx = x - w / 2 - 20 + k * (w + 40) / 5
        A.d['ink'].line((xx, base - h * 0.55, xx + 10, base - h * 0.55 + 20), fill=200, width=3)

def buffalo(A, x, y, s, dir=1, ph=0.0, layer='ink'):
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    d.polygon([T(*p_) for p_ in ellipse_pts(0, 0.55, 0.50, 0.22)], fill=255)
    d.polygon([T(0.40, 0.70), T(0.70, 0.62), T(0.78, 0.42), T(0.52, 0.40)], fill=255)
    d.arc((T(0.55, 0.95)[0] - 0.25 * s, T(0.55, 0.95)[1] - 0.05 * s, T(0.55, 0.95)[0] + 0.25 * s, T(0.55, 0.95)[1] + 0.3 * s), 200, 340, fill=255, width=max(3, int(0.05 * s)))
    for hu, off in ((0.32, 0), (0.2, 1.6), (-0.25, 3.1), (-0.38, 4.7)):
        a = 0.15 * math.sin(ph + off)
        d.line([T(hu, 0.4), T(hu + 0.1 * math.sin(a), 0)], fill=255, width=max(4, int(0.08 * s)))
    d.line([T(-0.5, 0.6), T(-0.62, 0.3 + 0.05 * math.sin(ph))], fill=255, width=max(2, int(0.03 * s)))

def mound(A, x, base, w, h, layer='mid'):
    A.d[layer].chord((x - w / 2, base - h, x + w / 2, base + h), 180, 360, fill=255)

def big_ship(A, x, y, s, t, layer='ink', burn=0.0):
    bob = 6 * math.sin(t * 2 + x * 0.01)
    A.d[layer].polygon([(x - s, y - 30 + bob), (x + s, y - 40 + bob), (x + s * 0.8, y + 40 + bob), (x - s * 0.8, y + 40 + bob)], fill=255)
    A.d[layer].rectangle((x - s * 0.5, y - 150 + bob, x + s * 0.4, y - 30 + bob), fill=255)
    A.d[layer].polygon([(x - s * 0.6, y - 150 + bob), (x + s * 0.5, y - 150 + bob), (x + s * 0.3, y - 210 + bob), (x - s * 0.4, y - 210 + bob)], fill=255)
    if burn > 0:
        flames(A, x, y - 30 + bob, s * 1.6, 260 * burn, t + x * 0.01, n=6, seed=int(x), smoke=True)

# ================================================================ hook scenes
def art_cowherd(A, cv, t, u):
    sun(cv, 820, 900, 110, ZHU, 110)
    ground(A, GROUND)
    buffalo(A, 620, GROUND, 300, 1, t * 2, layer='ink')
    person(A, 330, GROUND, 170, dir=1, robe=False, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.d['ink'].line((350, GROUND - 120, 470, GROUND - 260), fill=255, width=4)

def art_beg_hook(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(160, 620, ease_out(u / (2 * P)))
    person(A, x, GROUND, 260, dir=1, robe=True, hat='knot', arm=70, ph=t * 4, layer='ink')
    A.d['ink'].chord((x + 50, GROUND - 200, x + 120, GROUND - 150), 0, 180, fill=255)
    A.d['ink'].line((x - 50, GROUND - 260, x - 70, GROUND), fill=255, width=5)
    for k in range(4):
        y = 860 + k * 70
        xx = (t * 50 + k * 300) % (W + 500) - 300
        A.d['wash'].line((xx, y, xx + 300, y), fill=255, width=16)

def art_hongwu_hook(A, cv, t, u):
    for k in range(3):
        palace(A, 200 + k * 340, 1300, 300 + (k == 1) * 160, layer='ink' if k == 1 else 'mid')
    A.d['wash'].rectangle((60, 1300, W - 60, GROUND + 20), fill=255)
    for k in range(6):
        x = 120 + k * 170
        flag(A, x, GROUND, 260, t + k, w=90)

def art_purge_hook(A, cv, t, u):
    ground(A, GROUND)
    for k in range(7):
        x = 120 + k * 140
        gone = ease_out((u - k * 0.12) / 0.3)
        person(A, x, GROUND, 230, dir=1, hat='knot', arm=20, fall=-80 * gone, layer='ink' if k % 2 else 'mid')
        if gone > 0.5:
            A.d['red'].line((x - 40, GROUND - 300, x + 40, GROUND - 220), fill=255, width=6)

# ================================================================ 第一回 scenes
def art_hut_birth(A, cv, t, u):
    sun(cv, 560, 1000, lerp(60, 200, ease_out(u / (2 * P))), ZHU, 130)
    ground(A, GROUND)
    hut(A, 540, GROUND, 420, 380)
    for k in range(5):
        x = 120 + k * 70
        A.d['ink'].line((x, GROUND, x + 6, GROUND - 60), fill=255, width=3)
    person(A, 860, GROUND, 230, dir=-1, robe=False, arm=lerp(20, 120, ease_out((u - P) / 0.4)), layer='ink')

def art_calf_feast(A, cv, t, u):
    A.d['mid'].polygon([(700, GROUND), (760, 1000), (900, 940), (1020, GROUND)], fill=255)
    A.d['ink'].line((780, 1060, 820, 1120), fill=255, width=5)
    ground(A, GROUND)
    campfire(A, 420, GROUND, t, size=80)
    for k, x in enumerate((240, 330, 520, 600)):
        person(A, x, GROUND, 150, dir=1 if x < 420 else -1, robe=False, kneel=True, bow=20 + 6 * math.sin(t * 3 + k), arm=80, layer='ink')
    A.d['ink'].line((420, GROUND - 160, 420, GROUND - 60), fill=255, width=4)
    A.d['red'].ellipse((400, GROUND - 190, 440, GROUND - 150), fill=255)

def art_famine(A, cv, t, u):
    A.d['mid'].polygon([(x, 1300 - 30 * math.sin(x * 0.01)) for x in range(60, W - 59, 10)] + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=150)
    for k in range(60):
        q = (t * 0.6 + k / 60) % 1
        x = (k * 53 + t * 140) % (W - 120) + 60
        y = 700 + 260 * math.sin(k * 1.7 + t) + q * 40
        A.d['ink'].ellipse((x - 4, y - 3, x + 4, y + 3), fill=255)
    for i in range(3):
        if u > (1 + i * 0.8) * P:
            mound(A, 300 + i * 220, GROUND, 160, 70 * ease_out((u - (1 + i * 0.8) * P) / 0.3))
    person(A, 900, GROUND, 200, dir=-1, robe=False, kneel=True, bow=55, arm=80, layer='ink')

def art_burial(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 10, y + 40), fill=200, width=2)
    ground(A, GROUND)
    x = lerp(140, 480, ease_out(u / (2.5 * P)))
    person(A, x, GROUND, 230, dir=1, robe=False, bow=30, arm=70, ph=t * 3, layer='ink')
    A.d['mid'].rounded_rectangle((x - 140, GROUND - 200, x + 40, GROUND - 150), radius=20, fill=255)
    mound(A, 760, GROUND, 220, 90 * ease_out((u - 2.5 * P) / 0.4) if u > 2.5 * P else 0)

def art_sweep_monk(A, cv, t, u):
    palace(A, 620, GROUND, 600, layer='mid')
    A.d['wash'].rectangle((60, 1250, W - 60, GROUND + 20), fill=255)
    x = 300 + 60 * math.sin(t * 1.2)
    person(A, x, GROUND, 230, dir=1, hat='knot', bow=30, arm=110, layer='ink')
    a = math.sin(t * 6) * 0.4
    hx, hy = x + 60, GROUND - 150
    A.d['ink'].line((hx, hy, hx + 120 * math.sin(a + 0.5), GROUND - 10), fill=255, width=5)
    for k in range(8):
        lx = x + 120 + (k * 23 + t * 80) % 160
        A.d['gold'].ellipse((lx - 6, GROUND - 14, lx + 6, GROUND - 6), fill=200)

def art_begging_road(A, cv, t, u):
    pr = clamp(u / (4 * P))
    sun(cv, lerp(200, 880, pr), 900 - 160 * math.sin(math.pi * pr), 100, ZHU if pr < 0.8 else (140, 130, 120), 120)
    pts = [(x, 1300 + 60 * math.sin(x * 0.006 + 1)) for x in range(60, W - 59, 12)]
    A.d['mid'].line(pts, fill=255, width=26)
    ground(A, GROUND)
    x = lerp(120, 880, pr)
    y = 1300 + 60 * math.sin(x * 0.006 + 1)
    person(A, x, y, 180, dir=1, hat='knot', arm=70, ph=t * 5, layer='ink')
    A.d['ink'].chord((x + 34, y - 140, x + 90, y - 100), 0, 180, fill=255)
    for k in range(3):
        crow(A, 300 + k * 180 + 30 * math.sin(t + k), 820 + 20 * math.cos(t * 1.3 + k), 18, t * 10 + k)

def art_stone_man(A, cv, t, u):
    ground(A, GROUND)
    rise = ease_out(u / (1.5 * P))
    y = lerp(GROUND + 300, GROUND, rise)
    A.d['mid'].rectangle((470, y - 300, 610, y), fill=255)
    A.d['mid'].ellipse((480, y - 400, 600, y - 290), fill=255)
    A.d['wash'].ellipse((550, y - 360, 576, y - 340), fill=0)
    for k in range(3):
        person(A, 200 + k * 80, GROUND, 190, dir=1, robe=False, bow=30, arm=120, layer='ink')
    if u > 2 * P:
        v = u - 2 * P
        for k in range(6):
            p = ease_out((v - k * 0.06) / 0.3)
            flag(A, 680 + k * 60, lerp(GROUND, GROUND - 40, p), 260 * p, t + k, w=70)

def art_join_guo(A, cv, t, u):
    city_wall(A, 520, W - 60, 1140, gate_x=780, label='濠州', open_=0.4)
    ground(A, GROUND)
    for k in range(2):
        x = 640 + k * 300
        person(A, x, GROUND, 230, dir=-1, robe=False, hat='helmet', spear=True, layer='ink')
        A.d['red'].rectangle((x - 20, GROUND - 230, x + 20, GROUND - 215), fill=255)
    person(A, 380, GROUND, 230, dir=1, hat='knot', kneel=u > 0.5, bow=40, arm=80, layer='ink')

# ================================================================ 第二回 scenes
def art_wedding(A, cv, t, u):
    for k in range(4):
        x = 180 + k * 240
        sw = 8 * math.sin(t * 2 + k)
        A.d['ink'].line((x, 700, x + sw, 760), fill=255, width=2)
        A.d['red'].ellipse((x + sw - 26, 760, x + sw + 26, 830), fill=255)
    A.d['red'].rectangle((470, 880, 610, 1020), fill=255)
    A.d['red'].text((490, 890), '囍', font=font(SERIF, 100, 'Black'), fill=0)
    ground(A, GROUND)
    b = 45 * (0.5 + 0.5 * math.sin(t * math.pi / P))
    person(A, 440, GROUND, 250, dir=1, hat='knot', bow=b, arm=60, layer='ink')
    person(A, 640, GROUND, 230, dir=-1, female=True, bow=b, arm=60, layer='ink')
    A.d['red'].rectangle((610, GROUND - 230, 670, GROUND - 200), fill=255)

def art_hot_cake(A, cv, t, u):
    for k in range(6):
        A.d['ink'].line((640 + k * 50, 900, 640 + k * 50, GROUND), fill=255, width=8)
    A.d['ink'].rectangle((620, 880, 920, 900), fill=255)
    person(A, 780, GROUND, 220, dir=-1, kneel=True, bow=30, arm=60, layer='mid')
    ground(A, GROUND)
    x = lerp(120, 480, ease_out(u / (2.5 * P)))
    person(A, x, GROUND, 240, dir=1, female=True, ph=t * 8, robe=False, arm=80, layer='ink')
    glow = 18 + 4 * math.sin(t * 10)
    A.d['red'].ellipse((x + 20 - glow, GROUND - 175 - glow * 0.6, x + 20 + glow, GROUND - 175 + glow * 0.6), fill=255)
    for k in range(3):
        a = t * 3 + k * 2
        A.d['wash'].arc((x + 10 + k * 14, GROUND - 260 - 20 * math.sin(a), x + 40 + k * 14, GROUND - 210), 200, 340, fill=255, width=4)

def art_recruits(A, cv, t, u):
    hut(A, 180, GROUND - 40, 200, 180)
    hut(A, 360, GROUND - 60, 160, 150)
    ground(A, GROUND)
    flag(A, 900, GROUND, 520, t, w=130)
    for k in range(8):
        x = walk_x(120 - k * 90, 820 - k * 70, u, 3 * P)
        person(A, x, GROUND - (k % 3) * 8, 170 - (k % 3) * 10, dir=1, robe=False, ph=t * 6 + k, arm=20, layer='ink' if k % 2 else 'mid')
        A.d['red'].rectangle((x - 14, GROUND - 170 - (k % 3) * 8, x + 14, GROUND - 160 - (k % 3) * 8), fill=255)

def art_yingtian(A, cv, t, u):
    city_wall(A, 60, W - 60, 1100, gate_x=540, label=None, open_=1.0)
    ground(A, GROUND)
    flip = ease_out((u - 1.5 * P) / 0.3)
    A.d['ink'].rectangle((470, 1010, 610, 1080), fill=255)
    lab = '集庆' if flip < 0.5 else '应天'
    sq = abs(1 - 2 * flip) if 0 < flip < 1 else 1
    A.d['ink'].text((488, 1020 + (1 - sq) * 20), lab, font=font(SERIF, 40, 'Black'), fill=0)
    for k in range(5):
        x = walk_x(-100 - k * 110, 400 - k * 80, u, 2 * P)
        person(A, x, GROUND, 190, dir=1, robe=False, hat='helmet', spear=True, ph=t * 7 + k, layer='ink')

def art_nine_words(A, cv, t, u):
    ground(A, GROUND)
    ph = u / P
    h = 300 * ease_out(ph / 1.0)
    A.d['mid'].rectangle((90, GROUND - h, 380, GROUND), fill=255)
    for x in range(90, 380, 40):
        A.d['mid'].rectangle((x, GROUND - h - 26, x + 24, GROUND - h), fill=255)
    if ph > 1:
        g = ease_out((ph - 1) / 1.0)
        for k in range(int(g * 9)):
            gx = 470 + (k % 3) * 70; gy = GROUND - 30 - (k // 3) * 60
            A.d['gold'].ellipse((gx - 32, gy - 30, gx + 32, gy + 30), fill=255)
            A.d['ink'].ellipse((gx - 32, gy - 30, gx + 32, gy + 30), outline=255, width=3)
    if ph > 2:
        c_ = ease_out((ph - 2) / 0.8)
        cx = lerp(880, 820, c_); cy = lerp(1100, GROUND - 40, c_)
        A.d['ink'].polygon([(cx - 60, cy), (cx + 60, cy), (cx + 50, cy - 50), (cx + 25, cy - 20), (cx, cy - 60), (cx - 25, cy - 20), (cx - 50, cy - 50)], fill=255)
    A.flush(cv)
    for i, (txt, x) in enumerate((('高筑墙', 235), ('广积粮', 540), ('缓称王', 830))):
        if ph >= i:
            stamp(cv, seal(txt, 40, ZHU if i != 2 else COBALT), x, 960, t, t - u + i * P, rot=(i - 1) * 4)

def art_scholars_invite(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].polygon([(600, GROUND), (640, 1100), (760, 1060), (900, 1120), (1000, GROUND)], fill=200)
    for k, x in enumerate((640, 760, 880)):
        person(A, x, GROUND, 220, dir=-1, hat='knot', arm=60 if k else 110, layer='ink')
    A.d['ink'].pieslice((620, GROUND - 260, 700, GROUND - 180), 180, 300, fill=255)
    person(A, 320, GROUND, 250, dir=1, hat='knot', bow=lerp(0, 50, ease_out((u - P) / 0.4)), arm=70, layer='ink')

RIVALS = [('陈', (220, 1040), 110), ('朱', (540, 1080), 80), ('张', (860, 1040), 90)]
def art_rivals_map(A, cv, t, u):
    pts = []
    for j in range(44):
        a = 2 * math.pi * j / 44
        r = 400 + 30 * math.sin(a * 3) + 20 * math.sin(a * 5)
        pts.append((540 + r * math.cos(a), 1060 + r * math.sin(a) * 0.6))
    A.d['cobalt'].polygon(pts, fill=90); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.d['wash'].line([(x, 1060 + 40 * math.sin(x * 0.01)) for x in range(160, 930, 10)], fill=255, width=14)
    p = 0.5 + 0.5 * math.sin(t * 3)
    A.d['red'].line((330, 1050, lerp(330, 460, p), 1065), fill=255, width=8)
    A.d['red'].line((760, 1050, lerp(760, 620, p), 1065), fill=255, width=8)
    A.flush(cv)
    for i, (ch, (x, y), sz) in enumerate(RIVALS):
        stamp(cv, seal(ch, sz, ZHU if ch == '朱' else INK), x, y, t, t - u + i * 0.2)

# ================================================================ 第三回 scenes
def art_longwan(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1330), fill=170)
    waves(A, 1160, t, rows=3, amp=8, speed=2)
    for k in range(3):
        x = lerp(W + 200, 640, ease_out(u / (2 * P))) + k * 170
        big_ship(A, x, 1200, 90, t, layer='mid')
    ground(A, GROUND)
    pop = ease_out((u - 2 * P) / 0.3) if u > 2 * P else 0
    for k in range(6):
        x = 100 + k * 90
        person(A, x, lerp(GROUND + 200, GROUND, pop), 190, dir=1, robe=False, hat='helmet', spear=True, layer='ink')
    A.d['mid'].polygon([(60, GROUND), (60, 1180), (300, 1220), (620, GROUND)], fill=150)

def art_hongdu(A, cv, t, u):
    city_wall(A, 60, 620, 1060, gate_x=340, label='洪都')
    A.d['wash'].rectangle((620, 1180, W - 60, 1330), fill=170)
    waves(A, 1190, t, rows=3, amp=8, speed=2, x0=620)
    for k in range(3):
        big_ship(A, 760 + k * 110, 1220 - k * 20, 70, t + k, layer='mid')
    days = int(clamp(u / (4 * P)) * 85)
    for k in range(5):
        person(A, 120 + k * 100, 1060, 120, dir=1, robe=False, hat='helmet', spear=True, layer='ink')
    A.d['ink'].text((420, 1180), f'{days}', font=font(SERIF, 90, 'Black'), fill=0)

def art_poyang(A, cv, t, u):
    """8-beat set piece: chained giant ships → wind rises → fire boats → the fleet burns."""
    ph = u / P
    A.d['wash'].rectangle((60, 1100, W - 60, 1380), fill=170)
    waves(A, 1110, t, rows=5, amp=10, speed=2.5)
    burn = ease_out((u - 4.5 * P) / (2 * P)) if ph > 4.5 else 0
    xs = [300, 540, 780]
    for i, x in enumerate(xs):
        big_ship(A, x, 1150, 120, t, layer='ink', burn=clamp(burn * 1.2 - i * 0.15))
    for a_, b_ in zip(xs, xs[1:]):
        A.d['ink'].line((a_ + 120, 1140, b_ - 120, 1140), fill=255, width=5)
        for k in range(5):
            cx = lerp(a_ + 120, b_ - 120, (k + 0.5) / 5)
            A.d['ink'].ellipse((cx - 8, 1132, cx + 8, 1148), outline=255, width=3)
    if ph >= 2:
        w = ease_out((u - 2 * P) / 0.6)
        for k in range(8):
            y = 760 + k * 40
            x = (t * 600 + k * 170) % (W + 400) - 200
            A.d['wash'].line((x, y, x + 200 * w, y - 20), fill=255, width=6)
        A.flush(cv)
        stamp(cv, seal('东北风起', 44, COBALT), 860, 820, t, t - u + 2 * P, rot=6)
    if ph >= 3:
        for k in range(4):
            fx = lerp(1000 + k * 60, 360 + k * 140, ease_out((u - 3 * P - k * 0.08) / (1.6 * P)))
            fy = 1290 + (k % 2) * 30
            A.d['mid'].polygon([(fx - 50, fy - 10), (fx + 50, fy - 10), (fx + 40, fy + 20), (fx - 40, fy + 20)], fill=255)
            flames(A, fx, fy - 10, 90, 110, t + k, n=3, seed=40 + k, smoke=False)
    if ph >= 6.5:
        A.flush(cv)
        stamp(cv, seal('火烧连营', 50), 220, 820, t, t - u + 6.5 * P, rot=-6)

def art_one_arrow(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1330), fill=170)
    waves(A, 1160, t, rows=3, amp=8, speed=2)
    big_ship(A, 800, 1200, 160, t, layer='mid')
    person(A, 800, 1050, 160, dir=-1, hat='crown', arm=30, fall=0 if u < 0.6 else -60 * ease_out((u - 0.6) / 0.3), layer='ink')
    q = clamp(u / 0.6)
    arrow(A, lerp(120, 760, q), lerp(1000, 960, q), 0, 110)

def art_pingjiang(A, cv, t, u):
    city_wall(A, 60, W - 60, 1100, gate_x=540, label='平江', open_=ease_out((u - 0.3) / 0.5))
    ground(A, GROUND)
    for k in range(8):
        x = walk_x(-100 - k * 90, 400 - k * 50, u, 1.8 * P)
        person(A, x, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, ph=t * 9 + k, layer='ink' if k % 2 else 'mid')
    A.d['red'].line((420, 1060, 660, 1080), fill=255, width=8)

def art_proclaim(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 720 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 840, x1, 1240), fill=150)
    A.d['ink'].rectangle((x0 - 20, 820, x0, 1260), fill=255); A.d['ink'].rectangle((x1, 820, x1 + 20, 1260), fill=255)
    fo = font(BRUSH, 64)
    for j, col in enumerate(('驱逐胡虏', '恢复中华')):
        for i, ch in enumerate(col):
            x = 600 - j * 110
            if x0 + 20 < x < x1 - 40 and u > 0.25 + (j * 4 + i) * 0.06:
                A.d['ink'].text((x, 880 + i * 80), ch, font=fo, fill=255)

UNIFY = [('陈友谅', 1363, (230, 1000)), ('张士诚', 1367, (850, 1010)), ('方国珍', 1367, (880, 1250)),
         ('元大都', 1368, (560, 760)), ('四川', 1371, (200, 1200)), ('云南', 1382, (420, 1320))]
def scene_unify_ming(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 360 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((560 + r * math.cos(a), 1050 + r * math.sin(a) * 0.82))
    A.d['cobalt'].polygon(pts, fill=110); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    for i, (name, yr, (x, y)) in enumerate(UNIFY):
        p = ease_out((t - bt(c[0] + i)) / 0.3)
        if p > 0:
            A.d['red'].line((560, 1040, lerp(560, x, p), lerp(1040, y, p)), fill=255, width=8)
    A.flush(cv)
    stamp(cv, seal('明', 100 if not gather else 230), 560, 1040, t, s0 if not gather else gather_t)
    for i, (name, yr, (x, y)) in enumerate(UNIFY):
        if t >= bt(c[0] + i) and not gather:
            stamp(cv, seal(name, 36 if len(name) == 3 else 44, INK if i == 3 else ZHU), x, y, t, bt(c[0] + i) + 0.12)
    idx = int(k - c[0])
    if 0 <= idx < 6:
        nm, yr, _ = UNIFY[idx]
        ink_in(cv, text_img(f'公元{cn_year(yr)}年 · 平{nm}', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1460, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '扫平群雄', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '布衣天子', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '一统山河', BRUSH, 150, COBALT, W / 2, 1460, t, bt(c[0] + 7), stagger=0.08, seed=111)
    fx.flush(cv)

# ================================================================ 第四回 scenes
def art_nanjing_throne(A, cv, t, u):
    sun(cv, 540, 900, 260, ZHU, 120)
    A.d['ink'].polygon([(200, GROUND), (880, GROUND), (820, 1250), (260, 1250)], fill=255)
    for k in range(5):
        y = GROUND - k * 34
        A.d['wash'].line((260 + k * 12, y, 820 - k * 12, y), fill=0, width=3)
    A.d['gold'].polygon([(460, 1250), (620, 1250), (620, 1080), (590, 1030), (490, 1030), (460, 1080)], fill=255)
    person(A, 540, 1250, 200, dir=1, hat='crown', arm=50, layer='ink')
    for k in range(4):
        for side in (-1, 1):
            person(A, 540 + side * (380 + k * 40), GROUND, 130, dir=-side, kneel=True, bow=50, arm=60, layer='mid')

def art_dadu(A, cv, t, u):
    city_wall(A, 60, 520, 1120, gate_x=290, label='大都', open_=1.0)
    ground(A, GROUND)
    for k in range(4):
        x = lerp(600, W + 300, ease_out(u / (3 * P))) + k * 90
        rider(A, x, GROUND - k * 8, 120, 1, t * 13 + k, layer='mid')
    for k in range(3):
        x = lerp(200, 700, ease_out(u / (3 * P))) - k * 160
        rider(A, x, GROUND, 190, 1, t * 13 + k, layer='ink', spear=True)
    flag(A, 290, 1020, 220, t, w=90)

def art_fishscale(A, cv, t, u):
    pts = []
    for j in range(40):
        a = 2 * math.pi * j / 40
        r = 360 + 30 * math.sin(a * 4)
        pts.append((540 + r * math.cos(a), 1060 + r * math.sin(a) * 0.75))
    A.d['wash'].polygon(pts, fill=150); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    p = ease_out(u / 0.8)
    r = random.Random(5)
    for k in range(int(36 * p)):
        x = 260 + (k % 9) * 64 + r.uniform(-10, 10); y = 900 + (k // 9) * 80 + r.uniform(-10, 10)
        A.d['ink'].arc((x - 40, y - 30, x + 40, y + 40), 200, 340, fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('鱼鳞', 50), 860, 900, t, t - u + 0.6)

def art_yellow_book(A, cv, t, u):
    n = int(clamp(u / 0.8) * 8)
    for k in range(n):
        x = 220 + k * 85
        A.d['gold'].rectangle((x, 1180 - k % 2 * 10, x + 70, GROUND), fill=255)
        A.d['ink'].rectangle((x, 1180 - k % 2 * 10, x + 70, GROUND), outline=255, width=3)
        A.d['ink'].line((x + 10, 1220, x + 60, 1220), fill=255, width=3)
    for k in range(3):
        person(A, 140, GROUND, 180, dir=1, arm=80, layer='mid') if k == 0 else None
    ground(A, GROUND)

def art_plough(A, cv, t, u):
    sun(cv, 820, 880, 110, ZHU, 110)
    for r in range(4):
        y = 1230 + r * 50
        A.d['mid'].line((60, y, W - 60, y), fill=255, width=3)
    x = lerp(200, 640, ease_out(u / (1.6 * P)))
    buffalo(A, x + 160, GROUND, 200, 1, t * 4, layer='ink')
    A.d['ink'].line((x + 40, GROUND - 80, x + 120, GROUND - 120), fill=255, width=6)
    person(A, x, GROUND, 200, dir=1, robe=False, bow=25, arm=60, ph=t * 4, layer='ink')

def art_law_book(A, cv, t, u):
    A.d['ink'].rectangle((360, 960, 720, 1260), fill=255)
    A.d['wash'].rectangle((380, 980, 700, 1240), fill=0)
    fo = font(SERIF, 66, 'Black')
    for i, ch in enumerate('大明律'):
        if u > 0.2 + i * 0.12:
            A.d['ink'].text((508, 990 + i * 78), ch, font=fo, fill=255)
    ground(A, GROUND)
    a = math.radians(lerp(-60, 0, ease_expo((u - 0.6) / 0.2)))
    hx, hy = 820, 1150
    A.d['ink'].line((hx, hy, hx + 160 * math.cos(a), hy + 160 * math.sin(a)), fill=255, width=10)
    A.d['ink'].rectangle((hx + 150 * math.cos(a) - 30, hy + 150 * math.sin(a) - 20, hx + 150 * math.cos(a) + 30, hy + 150 * math.sin(a) + 20), fill=255)

def art_empty_chair(A, cv, t, u):
    A.d['mid'].polygon([(300, GROUND), (780, GROUND), (740, 1270), (340, 1270)], fill=255)
    person(A, 540, 1270, 200, dir=1, hat='crown', arm=80, layer='ink')
    tip = ease_out((u - P) / 0.4)
    cx, cy = 860, GROUND
    pts = [(-50, 0), (50, 0), (50, -110), (40, -200), (-40, -200), (-50, -110)]
    A.d['ink'].polygon([rotp((cx + a, cy + b), (cx + 50, cy), tip * 1.3) for a, b in pts], fill=255)
    if tip > 0.6:
        A.flush(cv)
        stamp(cv, seal('废相', 54), 860, 950, t, t - u + P + 0.3, rot=6)

def art_jinyiwei(A, cv, t, u):
    A.d['wash'].ellipse((780, 650, 880, 750), fill=255)
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].rectangle((x, 900, x + 40, GROUND), fill=255)
    ground(A, GROUND)
    for k in range(3):
        x = (t * 90 + k * 330) % (W + 300) - 150
        person(A, x, GROUND, 220, dir=1, robe=False, hat='helmet', ph=t * 6 + k, arm=30, layer='ink')
        A.d['ink'].line((x - 10, GROUND - 120, x - 80, GROUND - 40), fill=255, width=6)
        A.d['red'].rectangle((x - 14, GROUND - 175, x + 14, GROUND - 120), fill=200)
    ey = 860
    A.d['ink'].ellipse((470, ey - 30, 610, ey + 30), outline=255, width=5)
    A.d['ink'].ellipse((525, ey - 16, 555, ey + 16), fill=255)

def art_straw_man(A, cv, t, u):
    city_wall(A, 520, W - 60, 1140, gate_x=780, label='衙门', open_=0.0)
    ground(A, GROUND)
    sway = 0.06 * math.sin(t * 2)
    cx = 360
    A.d['ink'].line((cx, GROUND, cx, 900), fill=255, width=8)
    A.d['ink'].line((cx - 120, 960, cx + 120, 960), fill=255, width=8)
    body = [(-70, 960), (70, 960), (60, 1200), (-60, 1200)]
    A.d['gold'].polygon([rotp((cx + a, b), (cx, 900), sway) for a, b in body], fill=255)
    A.d['gold'].ellipse((cx - 40, 880, cx + 40, 960), fill=255)
    for k in range(10):
        a_ = -0.6 + k * 0.13
        A.d['ink'].line((cx + 60 * math.sin(a_), 1200, cx + 80 * math.sin(a_) + 6, 1240), fill=200, width=3)
    for k in range(3):
        person(A, 620 + k * 70, GROUND, 180, dir=-1, bow=35, arm=60, hat='knot', layer='mid')
    A.flush(cv)
    stamp(cv, seal('六十两', 46), 360, 820, t, t - u + P)

def art_lost_empress(A, cv, t, u):
    A.d['mid'].rectangle((300, 1150, 780, 1180), fill=255)
    A.d['ink'].rectangle((470, 1180, 610, GROUND), outline=255, width=6)
    A.d['ink'].rectangle((620, 1120, 640, 1150), fill=255)
    gut = clamp(1 - (u - 0.5) / 0.6)
    if gut > 0:
        A.d['red'].polygon([(622, 1120), (638, 1120), (632, 1120 - 40 * gut), (628, 1120 - 40 * gut)], fill=255)
    ground(A, GROUND)
    person(A, 330, GROUND, 250, dir=1, hat='crown', kneel=True, bow=55, arm=70, layer='ink')

# ================================================================ 第五回 scenes
def art_thorn_staff(A, cv, t, u):
    ground(A, GROUND)
    person(A, 280, GROUND, 270, dir=1, hat='crown', arm=80, layer='ink')
    person(A, 820, GROUND, 250, dir=-1, hat='crown', arm=lerp(20, 80, ease_out((u - 3 * P) / 0.4)), layer='ink')
    x0, y0, x1, y1 = 380, 1150, 700, 1150
    hand_off = ease_out((u - 3 * P) / 0.6) * 120 if u > 3 * P else 0
    A.d['ink'].line((x0 + hand_off, y0, x1 + hand_off, y1), fill=255, width=16)
    left = int(clamp(1 - u / (2.6 * P)) * 12)
    for k in range(left):
        px = lerp(x0, x1, (k + 0.5) / 12) + hand_off
        side = 1 if k % 2 else -1
        A.d['ink'].polygon([(px - 6, y0), (px + 6, y0), (px + 10, y0 - side * 36)], fill=255)
    for k in range(12 - left):
        q = clamp(u / (2.6 * P) * 12 - (12 - k - 1))
        A.d['mid'].polygon([(400 + k * 26, GROUND - 6), (412 + k * 26, GROUND - 6), (414 + k * 26, GROUND - 30)], fill=255)

def art_son_coffin(A, cv, t, u):
    A.d['wash'].rectangle((60, 700, W - 60, GROUND), fill=60)
    A.d['ink'].rounded_rectangle((520, 1250, 960, 1360), radius=26, fill=255)
    A.d['wash'].rectangle((540, 1260, 940, 1270), fill=0)
    for k in range(10):
        q = (t * 0.4 + k / 10) % 1
        x = 160 + k * 90; y = lerp(700, 1400, q)
        A.d['wash'].rectangle((x - 3, y - 12, x + 3, y + 12), fill=255)
    ground(A, GROUND)
    person(A, 330, GROUND, 250, dir=1, hat='crown', kneel=True, bow=lerp(30, 60, 0.5 + 0.5 * math.sin(t * 1.5)), arm=90, layer='ink')

def art_lanyu(A, cv, t, u):
    ground(A, GROUND)
    for k in range(9):
        x = 110 + k * 108
        gone = ease_out((u - 0.2 - k * 0.22) / 0.25)
        y = GROUND - 30
        A.d['ink'].line((x, y, x, lerp(y - 380, y - 40, gone)), fill=255, width=5)
        if gone < 0.95:
            fy = lerp(y - 380, y - 40, gone)
            A.d['mid' if k % 2 else 'red'].polygon([(x, fy), (x + 70, fy + 10), (x + 70, fy + 90), (x, fy + 80)], fill=255)
    A.flush(cv)
    if u > 2.5 * P:
        stamp(cv, seal('一万五千', 46, INK), 540, 920, t, t - u + 2.5 * P, rot=5)

def art_rain_palace(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    for k in range(50):
        q = (t * 1.2 + k / 50) % 1
        x = 80 + (k * 19) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 40), fill=200, width=2)
    sw = 10 * math.sin(t * 2)
    A.d['ink'].line((850, 1040, 850 + sw, 1100), fill=255, width=2)
    A.d['red'].ellipse((850 + sw - 22, 1100, 850 + sw + 22, 1160), fill=int(255 * clamp(1 - (u - 2 * P) / 1.0)))

def art_spirit_way(A, cv, t, u):
    for k in range(3):
        y = 1200 + k * 60
        A.d['wash'].line((60, y, W - 60, y - 40 + k * 20), fill=255, width=3)
    ground(A, GROUND)
    for k in range(4):
        p = ease_out((u - k * 0.25) / 0.4)
        if p <= 0.15: continue
        for side, x in ((-1, 160 + k * 90), (1, 920 - k * 90)):
            s = (120 - k * 18) * p
            y = GROUND - k * 30
            A.d['mid'].rectangle((x - s * 0.8, y - 10, x + s * 0.8, y), fill=255)
            A.d['ink'].polygon([q for q in ellipse_pts(x, y - s * 0.55, s * 0.7, s * 0.4)], fill=255)
            A.d['ink'].line((x - side * s * 0.6, y - s * 0.55, x - side * s * 0.85, y - 6), fill=255, width=max(3, int(s * 0.12)))
            for lx in (x - s * 0.4, x + s * 0.4):
                A.d['ink'].rectangle((lx - s * 0.1, min(y - s * 0.3, y - 10), lx + s * 0.1, y - 10), fill=255)
    A.flush(cv)
    stamp(cv, seal('孝陵', 54), 540, 900, t, t - u + P)

def art_ming_legacy(A, cv, t, u):
    p = ease_out(u / (1.5 * P))
    sun(cv, lerp(140, 400, p), 1000, 120, ZHU, 160)
    A.d['mid'].ellipse((lerp(940, 690, p) - 110, 890, lerp(940, 690, p) + 110, 1110), fill=255)
    A.d['mid'].ellipse((lerp(940, 690, p) - 70, 870, lerp(940, 690, p) + 150, 1090), fill=0)
    if u > 1.5 * P:
        A.flush(cv)
        ink_in(cv, text_img('明', BRUSH, 420, INK), 540, 1080, t, t - u + 1.5 * P, dur=0.4, settle=1.15)
    ground(A, GROUND)

def art_question_ming(A, cv, t, u):
    L.art_judge(A, cv, t, u)

# ================================================================ script
CHAPTERS = {16: ('第一回', '布衣乞丐'), 48: ('第二回', '红巾崛起'), 80: ('第三回', '鄱阳决战'),
            112: ('第四回', '洪武开国'), 144: ('第五回', '孤家寡人')}

CARDS = [
    C(0, 2, 'hook', 'num', num='放牛娃', line='连饭都吃不饱', art=art_cowherd),
    C(2, 4, 'hook', 'num', num='讨饭僧', line='托钵流浪三年', art=art_beg_hook),
    C(4, 6, 'hook', 'num', num='洪武大帝', line='开创大明二百七十六年', art=art_hongwu_hook),
    C(6, 8, 'hook', 'num', num='屠戮功臣', line='胡蓝之狱 株连数万', art=art_purge_hook),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=art_question_ming),
    # ---- 第一回 布衣乞丐
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1328, main='生于濠州', sub='佃户之家 · 排行第四 名唤重八', note='生时红光满室', art=art_hut_birth),
    C(22, 26, 'life', 'card', year=1338, main='放牛娃', sub='替地主放牛 · 偷宰牛犊分给伙伴', note='牛尾插入山缝 谎称牛钻进了山里', art=art_calf_feast),
    C(26, 30, 'night', 'card', year=1344, main='家破人亡', sub='旱灾 蝗灾 瘟疫 · 半月之内父母兄长相继饿死', note='田主德不我顾 呼叱昂昂', art=art_famine),
    C(30, 34, 'night', 'card', year=1344, main='无地葬亲', sub='求地不得 · 邻人赐一抔黄土', note='殡无棺椁 被体恶裳', art=art_burial),
    C(34, 38, 'life', 'card', year=1344, main='皇觉寺', sub='十七岁 · 剃度为僧 扫地上香', note='寺中扫洒 打钟击鼓', art=art_sweep_monk),
    C(38, 42, 'life', 'card', year=1345, main='托钵乞讨', sub='寺庙断粮 · 游方乞食三年', note='突朝烟而急进 暮投古寺以趋跄', art=art_begging_road),
    C(42, 46, 'war', 'card', year=1351, main='石人一只眼', sub='红巾军起 · 天下烽火', note='莫道石人一只眼 挑动黄河天下反', art=art_stone_man),
    C(46, 48, 'war', 'card', year=1352, main='投军濠州', sub='二十五岁 · 投奔郭子兴', art=art_join_guo),
    # ---- 第二回 红巾崛起
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'court', 'card', year=1352, main='迎娶马氏', sub='郭子兴将养女许配 · 后来的马皇后', note='大脚马皇后 一生相伴', art=art_wedding),
    C(54, 58, 'night', 'card', year=1353, main='怀饼救夫', sub='朱元璋被囚 · 马氏怀揣热饼送去', note='饼热灼伤胸前肌肤', art=art_hot_cake),
    C(58, 62, 'life', 'card', year=1353, main='回乡招兵', sub='带回七百子弟 · 徐达 汤和在其中', note='淮西二十四将 自此相随', art=art_recruits),
    C(62, 66, 'war', 'card', year=1356, main='攻占集庆', sub='改名应天 · 立下根基', note='金陵 自古帝王州', art=art_yingtian),
    C(66, 70, 'court', 'card', year=1357, main='九字国策', sub='朱升献策 · 一拍一字落地', note='高筑墙 广积粮 缓称王', art=art_nine_words),
    C(70, 74, 'court', 'card', year=1360, main='礼贤下士', sub='刘基 宋濂 · 请入幕府', note='吾为天下屈四先生', art=art_scholars_invite),
    C(74, 80, 'court', 'card', year=1360, main='群雄环伺', sub='西有陈友谅 · 东有张士诚', note='友谅志骄 士诚器小', art=art_rivals_map),
    # ---- 第三回 鄱阳决战
    C(80, 82, 'works', 'chapter'),
    C(82, 86, 'war', 'card', year=1360, main='龙湾之战', sub='诱敌深入 · 伏兵尽出', note='康茂才诈降 引友谅入伏', art=art_longwan),
    C(86, 90, 'war', 'card', year=1363, main='死守洪都', sub='朱文正坚守八十五天', note='城坏复修 屹然不动', art=art_hongdu),
    C(90, 98, 'works', 'card', year=1363, main='鄱阳湖火攻', sub='巨舰连锁 · 东北风起 火烧连营', note='友谅联巨舟为阵 太祖以火攻之', art=art_poyang),
    C(98, 100, 'war', 'card', year=1363, main='一箭毙命', sub='陈友谅中流矢身亡', art=art_one_arrow),
    C(100, 102, 'war', 'card', year=1367, main='平定吴地', sub='平江城破 · 张士诚被俘', art=art_pingjiang),
    C(102, 104, 'court', 'card', year=1367, main='北伐檄文', sub='驱逐胡虏 · 恢复中华', art=art_proclaim),
    C(104, 112, 'works', 'unify'),
    # ---- 第四回 洪武开国
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=1368, main='应天称帝', sub='国号大明 · 年号洪武', seal='洪武', note='自乞丐至天子 前无古人', art=art_nanjing_throne),
    C(118, 122, 'war', 'card', year=1368, main='攻克大都', sub='徐达北伐 · 元顺帝北逃', note='元朝在中原的统治 宣告结束', art=art_dadu),
    C(122, 130, 'empire', 'list', year=1381, items=['鱼鳞图册', '黄册户籍', '休养生息', '大明律']),
    C(130, 134, 'court', 'card', year=1380, main='废除丞相', sub='胡惟庸案 · 千年相权就此终结', note='以后嗣君 毋得议置丞相', art=art_empty_chair),
    C(134, 138, 'night', 'card', year=1382, main='锦衣卫', sub='直属皇帝 · 监察百官', note='掌直驾侍卫 巡查缉捕', art=art_jinyiwei),
    C(138, 142, 'court', 'card', year=1385, main='剥皮实草', sub='贪污六十两以上 · 一律处死', note='郭桓案 牵连数万人', art=art_straw_man),
    C(142, 144, 'death', 'card', year=1382, main='马皇后崩', sub='帝恸哭 · 终身不再立后', art=art_lost_empress),
    # ---- 第五回 孤家寡人
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=1390, main='荆杖去刺', sub='我杀人 · 是替你拔去荆棘', note='汝弗能执欤 吾为汝去刺', art=art_thorn_staff),
    C(150, 154, 'death', 'card', year=1392, main='太子早逝', sub='朱标病逝 · 白发人送黑发人', note='帝恸哭 群臣皆哀', art=art_son_coffin),
    C(154, 158, 'death', 'card', year=1393, main='蓝玉案', sub='大将蓝玉被诛 · 株连一万五千人', note='胡蓝之狱 功臣宿将几尽', art=art_lanyu),
    C(158, 162, 'death', 'card', year=1398, main='崩于应天', sub='在位三十一年 · 享年七十一岁', note='闰五月乙酉 崩于西宫', art=art_rain_palace),
    C(162, 166, 'fate', 'card', year=1398, main='葬于孝陵', sub='石象路上 · 石兽相对', note='孝陵神道 千年守望', art=art_spirit_way),
    C(166, 170, 'end', 'card', year=1398, main='治隆唐宋', sub='得国之正 · 莫如大明', note='日月为明 大明二百七十六年', art=art_ming_legacy),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St):
    mod.CHAPTERS = CHAPTERS
G.CHAPTER_BEATS = [0, 16, 48, 80, 112, 144, END_BEAT]
L.CUTS = sorted({c[0] for c in CARDS if c[0] not in G.CHAPTER_BEATS} | {124, 126, 128})

def year_at(t):
    pts = sorted((bt(c[0]), c[4]['year']) for c in CARDS if 'year' in c[4])
    if t <= pts[0][0]: return pts[0][1]
    prev = pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1: return lerp(prev, y0, ease_out((t - t0) / 0.4))
        prev = y0
    return lerp(prev, pts[-1][1], ease_out((t - pts[-1][0]) / 0.4))
for mod in (G, L, Wd, Tz, Z, St):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=COBALT + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('朱 元 璋', SERIF, 50, COBALT, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '明太祖', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('洪武', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1328 — 1398', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '嗜杀暴君？', BRUSH, 120, ZHU, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '布衣天子？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

LIST_ART = [art_fishscale, art_yellow_book, art_plough, art_law_book]
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
            stamp(cv, seal('壹贰叁肆'[j], 36, COBALT), x, 575, t, bt(c[0] + 2 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=COBALT + (110,), width=2)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    obj_bowl(A, t, clamp(u / 0.8))
    A.flush(cv, alpha=clamp(u / 0.6) * 0.35)
    fx = Art()
    chars_in(cv, fx, '布衣天子', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('洪武', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('从一只破碗起步', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('打下一个二百七十六年的王朝', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '若你是他', BRUSH, 110, COBALT, W / 2, 1190, t, END + 1.15, stagger=0.07, drop=30, splash=False)
    type_in(cv, text_img('会杀功臣吗？评论区说说', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=COBALT + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 255, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=ZHU + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 康熙大帝', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, list=scene_list,
                unify=scene_unify_ming, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第陆集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('从乞丐到皇帝 · 他是怎么做到的？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=COBALT + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, COBALT, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=COBALT + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=COBALT + (255,))
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
