# 千古人物志 · 第拾叁集 · 诸葛亮 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：靛蓝月白星象 —— 羽扇章回卡（每回多展开几根羽毛）· 星象边角
#          · 八拍「草船借箭」 · 六出祁山回顾 · 八拍「空城计」 · 五丈原星落
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_caocao as Cc          # engine + helpers (ink layers drawn last)
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
from render_songtaizu import tent, campfire
from render_mingtaizu import big_ship
from render_liubang import low_table
from render_caocao import lord, general

F.RIPPLE = False

BORN, DIED = 181, 234
END_BEAT = 170
INDIGO = (40, 62, 120)
S.LAYERS.append(('indigo', INDIGO, 0.80, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='亮', life='龙', court='相', night='星', war='戰', empire='蜀', works='谋', fate='忠', death='星', end='明')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'feather'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (INDIGO, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = ((170, 180, 200), 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (INDIGO, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (0.97, 0.99, 1.03)
G.base_bg.cache_clear()

MTN_COL = {'night': (34, 40, 62), 'death': (52, 56, 70), 'war': (92, 62, 54), 'works': (70, 80, 100)}
def draw_background(t, theme):
    """靛蓝: indigo-washed ranges like blue-dyed silk."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 160, 190), (96, 110, 150), MTN_COL.get(theme, (54, 70, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'feather':
        return Cc.particle_sprite(kind, q)
    s = 44
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [(250, 250, 255), (200, 210, 235), (230, 230, 240)][q]
    d.ellipse((14, 6, 30, 38), fill=col + (220,))
    d.line((22, 6, 22, 40), fill=(120, 130, 160, 200), width=1)
    return im.rotate(30 * q, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.5))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """星象: a small constellation linked by fine lines at each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = INDIGO + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 160, y), fill=col, width=2); d.line((x, y, x, y + sy * 160), fill=col, width=2)
        pts = [(x + sx * 24, y + sy * 30), (x + sx * 56, y + sy * 22), (x + sx * 82, y + sy * 46), (x + sx * 50, y + sy * 70), (x + sx * 26, y + sy * 96)]
        d.line(pts, fill=col, width=2)
        for i, (px, py) in enumerate(pts):
            r = 6 if i == 2 else 4
            d.ellipse((px - r, py - r, px + r, py + r), fill=(ZHU if i == 2 else INDIGO) + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ 羽扇 chapter card
CH_FEATHERS = {16: 5, 48: 7, 80: 9, 112: 11, 144: 13}
def feather_fan(A, cx, cy, s, n, p=1.0, t=0.0, layer='wash'):
    """羽扇: n feathers fanned from a handle; spreads as p goes 0→1."""
    q = ease_out(p)
    A.d['ink'].line((cx, cy, cx, cy + s * 0.42), fill=255, width=max(6, int(s * 0.05)))
    A.d['ink'].ellipse((cx - s * 0.06, cy + s * 0.40, cx + s * 0.06, cy + s * 0.50), fill=255)
    spread = math.radians(110) * q
    for i in range(n):
        f = (i / (n - 1) - 0.5) if n > 1 else 0
        a = -math.pi / 2 + f * spread + 0.02 * math.sin(t * 2 + i)
        L_ = s * (0.9 - 0.15 * abs(f) * 2)
        ex, ey = cx + L_ * math.cos(a), cy + L_ * math.sin(a)
        pa = a + math.pi / 2
        w = s * 0.07
        mx, my = cx + L_ * 0.55 * math.cos(a), cy + L_ * 0.55 * math.sin(a)
        A.d[layer].polygon([(cx, cy), (mx + w * math.cos(pa), my + w * math.sin(pa)), (ex, ey), (mx - w * math.cos(pa), my - w * math.sin(pa))], fill=255)
        A.d['ink'].line((cx, cy, ex, ey), fill=170, width=2)
    A.d['indigo'].ellipse((cx - s * 0.09, cy - s * 0.09, cx + s * 0.09, cy + s * 0.09), fill=255)

def art_fan_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    feather_fan(A, 540, 1010, 440, CH_FEATHERS.get(kb, 7), p=u / 0.5, t=t, layer='mid')
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_fan_chapter)
    ink_in(cv, text_img(no, SERIF, 56, INDIGO, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def kongming(A, x, y, h, dir=1, layer='ink', fan=True, **kw):
    """诸葛亮: robe, 纶巾 scarf cap, feather fan."""
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    A.d[layer].polygon([(x - 0.08 * h, y - 0.93 * h), (x + 0.08 * h, y - 0.93 * h), (x + 0.05 * h, y - 1.04 * h), (x - 0.05 * h, y - 1.04 * h)], fill=255)
    A.d[layer].line((x - dir * 0.06 * h, y - 0.98 * h, x - dir * 0.16 * h, y - 0.86 * h), fill=255, width=max(2, int(0.02 * h)))
    if fan and hand:
        hx, hy = hand
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.25
            A.d['wash'].polygon([(hx, hy), (hx + 0.18 * h * math.cos(a - 0.1), hy + 0.18 * h * math.sin(a - 0.1)), (hx + 0.2 * h * math.cos(a), hy + 0.2 * h * math.sin(a)), (hx + 0.18 * h * math.cos(a + 0.1), hy + 0.18 * h * math.sin(a + 0.1))], fill=255)

def starfield(A, t, n=30, seed=1, y0=620, y1=980):
    r = random.Random(seed)
    for k in range(n):
        x = r.uniform(80, 1000); y = r.uniform(y0, y1)
        tw = 3 + 2 * math.sin(t * 3 + k)
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)

def thatched(A, x, base, w, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - w * 0.5, x + w / 2, base), fill=255)
    A.d[layer].polygon([(x - w * 0.65, base - w * 0.5), (x, base - w * 0.95), (x + w * 0.65, base - w * 0.5)], fill=255)
    for k in range(8):
        xx = x - w * 0.6 + k * w * 0.17
        A.d['ink'].line((xx, base - w * 0.52, xx + 8, base - w * 0.42), fill=200, width=3)
    rect(A, 'wash', x - w * 0.1, base - w * 0.32, x + w * 0.1, base, fill=0)

def straw_boat(A, x, y, s, t, arrows_n=0, layer='ink'):
    bob = 6 * math.sin(t * 2 + x * 0.01)
    A.d[layer].polygon([(x - s, y - 20 + bob), (x + s, y - 30 + bob), (x + s * 0.8, y + 30 + bob), (x - s * 0.8, y + 30 + bob)], fill=255)
    for k in range(6):
        xx = x - s * 0.7 + k * s * 0.28
        A.d['gold'].polygon([(xx - 20, y - 20 + bob), (xx + 20, y - 20 + bob), (xx + 10, y - 140 + bob), (xx - 10, y - 140 + bob)], fill=230)
    r = random.Random(int(x))
    for k in range(arrows_n):
        ax = x + r.uniform(-s * 0.7, s * 0.7); ay = y - r.uniform(30, 130) + bob
        A.d['ink'].line((ax, ay, ax - 40, ay - 6), fill=255, width=2)

# ================================================================ hooks
def art_z_hook_cottage(A, cv, t, u):
    for k in range(18):
        q = (t * 0.3 + k / 18) % 1
        x = 80 + (k * 53) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    ground(A, GROUND)
    thatched(A, 760, GROUND - 10, 300)
    for i in range(3):
        if u > i * 0.5:
            person(A, 160 + i * 110, GROUND, 190, dir=1, robe=True, hat='crown' if i == 2 else 'knot', bow=25, arm=60, layer='ink' if i == 2 else 'mid')

def art_z_hook_arrows(A, cv, t, u):
    A.d['wash'].rectangle((60, 1180, W - 60, 1380), fill=150)
    waves(A, 1190, t, rows=4, amp=6, speed=1.5)
    straw_boat(A, 540, 1230, 200, t, arrows_n=int(clamp(u / (1.6 * P)) * 30))

def art_z_hook_empty(A, cv, t, u):
    city_wall(A, 60, W - 60, 1150, gate_x=540, label='西城', open_=1.0)
    kongming(A, 540, 1060, 120, dir=1, kneel=True, bow=0, arm=60, fan=False, layer='ink')
    A.d['ink'].rectangle((470, 1040, 610, 1056), fill=255)
    ground(A, GROUND)
    for k in range(3):
        person(A, 300 + k * 30, GROUND, 120, dir=1, robe=False, bow=50, arm=110, layer='mid')

def art_z_hook_star(A, cv, t, u):
    starfield(A, t, seed=3)
    q = clamp(u / (1.6 * P))
    sx, sy = lerp(820, 520, q), lerp(700, 1150, q * q)
    A.d['red'].ellipse((sx - 18, sy - 18, sx + 18, sy + 18), fill=255)
    for k in range(8):
        A.d['wash'].line((sx + k * 16, sy - k * 22, sx + k * 16 + 10, sy - k * 22 - 14), fill=int(200 * (1 - k / 8)), width=4)
    ground(A, GROUND)
    tent(A, 540, GROUND - 10, 360, 300, layer='mid')

# ================================================================ 第一回 卧龙
def art_z_birth(A, cv, t, u):
    A.d['mid'].polygon([(560, GROUND), (720, 1100), (900, 1060), (1020, GROUND)], fill=200)
    ground(A, GROUND)
    A.d['mid'].rectangle((220, 1100, 520, GROUND), fill=255)
    A.d['ink'].polygon([(180, 1110), (560, 1110), (480, 1030), (260, 1030)], fill=255)
    rect(A, 'wash', 330, 1170, 410, GROUND, fill=0)
    A.flush(cv)
    stamp(cv, seal('琅琊', 56), 540, 900, t, t - u + P)

def art_z_orphan(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].chord((620, GROUND - 90, 860, GROUND + 90), 180, 360, fill=255)
    person(A, 400, GROUND, 160, dir=1, robe=True, hat='knot', kneel=True, bow=50, arm=70, layer='ink')
    person(A, 260, GROUND, 280, dir=1, robe=True, hat='knot', arm=lerp(20, 60, ease_out((u - P) / 0.4)), layer='ink')
    for k in range(10):
        q = ((t * 0.4 + k / 10) % 1)
        A.d['mid'].ellipse((140 + k * 80 - 6, lerp(700, 1400, q) - 4, 140 + k * 80 + 6, lerp(700, 1400, q) + 4), fill=255)

def art_z_plough(A, cv, t, u):
    sun(cv, 820, 880, 110, (190, 150, 70), 110)
    for r_ in range(4):
        y = 1230 + r_ * 50
        A.d['mid'].line((60, y, W - 60, y), fill=255, width=3)
        for x in range(90, W - 60, 60):
            A.d['grass'].line((x, y, x + 4 * math.sin(t * 2 + x), y - 24 - r_ * 4), fill=255, width=3)
    kongming(A, 420, 1260, 230, dir=1, bow=lerp(30, 50, 0.5 + 0.5 * math.sin(t * 3)), arm=120, fan=False, layer='ink')
    A.d['ink'].line((470, 1110, 540, 1260), fill=255, width=6)
    A.flush(cv)
    type_in(cv, text_img('躬耕陇亩 好为梁父吟', BRUSH, 60, INK), W / 2, 880, t, t - u + P, 0.5)

def art_z_guanyue(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    kongming(A, 540, GROUND, 230, dir=1, kneel=True, bow=20, arm=100, fan=False, layer='ink')
    A.flush(cv)
    stamp(cv, seal('管仲', 52, INK), 300, 960, t, t - u + 0.3)
    stamp(cv, seal('乐毅', 52, INK), 780, 960, t, t - u + P)
    if u > 2 * P:
        stamp(cv, seal('自比', 50), 540, 860, t, t - u + 2 * P)

def art_z_dragon_phoenix(A, cv, t, u):
    starfield(A, t, seed=4)
    for i, (x, ch) in enumerate(((320, '卧龙'), (760, '凤雏'))):
        q = ease_out((u - i * P) / 0.6)
        pts = [(x - 160 * q + f * 320 * q, 940 + 60 * math.sin(f * 7 + t * 2 + i)) for f in np.linspace(0, 1, 24)]
        if len(pts) > 1 and q > 0.02:
            A.d['indigo' if i == 0 else 'red'].line(pts, fill=255, width=14)
    ground(A, GROUND)
    person(A, 540, GROUND, 260, dir=1, robe=True, hat='knot', arm=lerp(20, 100, ease_out(u / P)), layer='ink')
    A.flush(cv)
    for i, (x, ch) in enumerate(((320, '卧龙'), (760, '凤雏'))):
        if u > i * P + 0.4:
            stamp(cv, seal(ch, 50, INDIGO if i == 0 else ZHU), x, 1060, t, t - u + i * P + 0.4)

def art_z_three_visits(A, cv, t, u):
    """three beats of snow → the third visit, Liu Bei bows before the thatched door."""
    for k in range(int(10 + 20 * clamp(u / (3 * P)))):
        q = (t * 0.3 + k / 30) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    ground(A, GROUND)
    thatched(A, 780, GROUND - 10, 320)
    n = min(3, int(u / P) + 1)
    for i in range(3):
        person(A, 200 + i * 110, GROUND, 200, dir=1, robe=i == 0, hat='crown' if i == 0 else 'helmet', bow=35 if i == 0 else 0, arm=60 if i == 0 else 30, layer='ink' if i == 0 else 'mid')
    A.flush(cv)
    for i in range(n):
        stamp(cv, seal(['一顾', '二顾', '三顾'][i], 44, INK if i < 2 else ZHU), 260 + i * 140, 920, t, t - u + i * P)

def art_z_longzhong(A, cv, t, u):
    """隆中对: a map split into three on the beat."""
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 360 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.72))
    A.d['indigo'].polygon(pts, fill=70); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    q1 = ease_out((u - 0.5 * P) / 0.4); q2 = ease_out((u - 1.5 * P) / 0.4)
    if q1 > 0:
        A.d['red'].line((540, 1040, lerp(540, 540, q1), lerp(1040, 760, q1)), fill=255, width=8)
    if q2 > 0:
        A.d['red'].line((540, 1040, lerp(540, 200, q2), lerp(1040, 1240, q2)), fill=255, width=8)
        A.d['red'].line((540, 1040, lerp(540, 900, q2), lerp(1040, 1240, q2)), fill=255, width=8)
    A.flush(cv)
    for i, (nm, x, y) in enumerate((('魏', 540, 900), ('蜀', 330, 1150), ('吴', 760, 1150))):
        if u > (2 + i * 0.3) * P:
            stamp(cv, seal(nm, 70, INK if nm != '蜀' else ZHU), x, y, t, t - u + (2 + i * 0.3) * P)

def art_z_leave(A, cv, t, u):
    sun(cv, 800, 920, 120, ZHU, 110)
    ground(A, GROUND)
    thatched(A, 860, GROUND - 10, 220)
    x = walk_x(700, 300, u, 1.8 * P)
    kongming(A, x, GROUND, 250, dir=-1, ph=t * 5, arm=60, layer='ink')
    person(A, x - 140, GROUND, 250, dir=-1, robe=True, hat='crown', arm=60, ph=t * 5, layer='ink')

# ================================================================ 第二回 赤壁
def art_z_debate(A, cv, t, u):
    for k in range(5):
        A.d['mid'].rectangle((140 + k * 210, 900, 176 + k * 210, GROUND), fill=255)
    A.d['mid'].rectangle((60, 870, W - 60, 900), fill=255)
    ground(A, GROUND)
    kongming(A, 540, GROUND, 260, dir=1, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    for i in range(3):
        for side in (-1, 1):
            x = 540 + side * (220 + i * 110)
            b = 0 if u < 2 * P else 40 * ease_out((u - 2 * P - i * 0.1) / 0.3)
            person(A, x, GROUND, 180, dir=-side, robe=True, hat='knot', bow=b, arm=40, layer='mid')

def art_z_boats(A, cv, t, u):
    """8-beat set piece: fog → twenty straw boats → drums and arrows → boats laden → 十万支."""
    ph = u / P
    A.d['wash'].rectangle((60, 1160, W - 60, 1380), fill=150)
    waves(A, 1170, t, rows=4, amp=6, speed=1.5)
    for k in range(6):
        y = 760 + k * 70
        x = (t * 40 + k * 260) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 520, y), fill=230, width=60)
    xs = [220, 520, 820]
    for i, x in enumerate(xs):
        n = 0 if ph < 2 else int(clamp((u - 2 * P - i * 0.1) / (4 * P)) * 40)
        straw_boat(A, x + (0 if ph < 6 else -120 * ease_out((u - 6 * P) / (2 * P))), 1220, 130, t, arrows_n=n)
    if 2 <= ph < 6:
        for k in range(10):
            q = ((u * 1.6 + k * 0.1) % 1)
            arrow(A, lerp(1060, 300 + k * 60, q), 900 + k * 18 - 100 * math.sin(math.pi * q), math.pi + 0.15, 70)
    kongming(A, 520, 1080, 110, dir=-1, kneel=True, bow=0, arm=40, layer='ink')
    A.flush(cv)
    if ph >= 1:
        stamp(cv, seal('大雾', 50, INK), 860, 820, t, t - u + P, rot=6)
    if ph >= 6.5:
        paste(cv, text_img('十万支', SERIF, 70, ZHU, 'Black', bleed=False), W / 2, 1460, 1, clamp((u - 6.5 * P) / 0.3))

def art_z_altar(A, cv, t, u):
    for k in range(10):
        y = 720 + k * 60
        x = (t * 600 + k * 190) % (W + 400) - 200
        A.d['wash'].line((x, y, x + 260 * ease_out((u - P) / 0.6), y - 30), fill=255, width=6)
    ground(A, GROUND)
    for r_ in range(3):
        w = 300 - r_ * 70
        A.d['ink'].rectangle((540 - w, GROUND - (r_ + 1) * 60, 540 + w, GROUND - r_ * 60), fill=255)
    kongming(A, 540, GROUND - 180, 200, dir=1, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    for k in range(8):
        a = math.pi + k * math.pi / 7
        flag(A, 540 + 330 * math.cos(a), GROUND - 10, 160, t * 1.5 + k, w=60, layer='indigo' if k % 2 else 'red')

def art_z_three_kingdoms(A, cv, t, u):
    for i, (nm, x) in enumerate((('魏', 230), ('蜀', 540), ('吴', 850))):
        p = ease_out((u - i * P) / 0.4)
        if p > 0:
            A.d['ink' if nm != '蜀' else 'red'].polygon([(x - 120, GROUND), (x, GROUND - 360 * p), (x + 120, GROUND)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    for i, (nm, x) in enumerate((('魏', 230), ('蜀', 540), ('吴', 850))):
        if u > i * P + 0.3:
            stamp(cv, seal(nm, 70, ZHU if nm == '蜀' else INK), x, 980, t, t - u + i * P + 0.3)

def art_z_shu(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 560), (520, 640), (860, 540))):
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - h), (x + 260, GROUND)], fill=200)
    city_wall(A, 300, 780, 1180, gate_x=540, label='成都', open_=ease_out((u - P) / 0.5))
    ground(A, GROUND)
    for k in range(4):
        general(A, walk_x(-100 - k * 90, 260 - k * 70, u, 2 * P), GROUND, 160, dir=1, spear=True, ph=t * 8 + k, layer='ink')

def art_z_baidi(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    A.d['mid'].rectangle((200, 1250, 640, 1290), fill=255)
    person(A, 420, 1250, 180, dir=1, hat='crown', kneel=True, bow=-30, fall=-40, arm=lerp(30, 100, ease_out((u - P) / 0.4)), layer='ink')
    kongming(A, 760, GROUND, 250, dir=-1, kneel=True, bow=45, arm=80, fan=False, layer='ink')
    lantern(A, 180, 1000, t, 0, size=22)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('白帝城', 50, INK), 300, 940, t, t - u + 0.3)

def art_z_chancellor(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 130, dir=-1, hat='crown', arm=20, layer='mid')
    kongming(A, 380, GROUND, 290, dir=1, arm=lerp(30, 80, ease_out(u / P)), layer='ink')
    n = int(clamp(u / (3 * P)) * 10)
    for k in range(n):
        A.d['mid'].rectangle((120, GROUND - 20 - k * 22, 240, GROUND - 4 - k * 22), fill=255)
    A.flush(cv)
    stamp(cv, seal('丞相', 56), 380, 940, t, t - u + P)

# ================================================================ 第三回 南征北伐
def art_z_menghuo(A, cv, t, u):
    for x in (140, 900):
        A.d['ink'].line((x, GROUND, x + 20, 1000), fill=255, width=12)
        for k in range(6):
            a = math.radians(-160 + k * 30)
            A.d['ink'].line((x + 20, 1000, x + 20 + 120 * math.cos(a), 1000 + 120 * math.sin(a) + 40), fill=255, width=6)
    ground(A, GROUND)
    kongming(A, 760, GROUND, 250, dir=-1, arm=60, layer='ink')
    cnt = min(7, int(u / (0.5 * P)) + 1)
    tied = (cnt % 2 == 1)
    person(A, 400, GROUND, 250, dir=1, robe=False, hat='helmet', kneel=tied, bow=40 if tied else 0, arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img(f'第{cn_num(cnt)}擒', SERIF, 60, ZHU, 'Black', bleed=False), 400, 940, 1, 1)

def art_z_chushi(A, cv, t, u):
    p = ease_out(u / 0.6)
    w = 760 * p
    x0, x1 = 540 - w / 2, 540 + w / 2
    A.d['mid'].rectangle((x0, 840, x1, 1260), fill=150)
    A.d['ink'].rectangle((x0 - 20, 820, x0, 1280), fill=255); A.d['ink'].rectangle((x1, 820, x1 + 20, 1280), fill=255)
    fo = font(BRUSH, 62)
    for j, col in enumerate(('先帝创业未半', '而中道崩殂', '臣本布衣', '躬耕于南阳')):
        for i, ch in enumerate(col):
            x = 760 - j * 120
            if x0 + 20 < x < x1 - 40 and u > 0.3 + (j * 6 + i) * 0.05:
                A.d['ink'].text((x, 870 + i * 64), ch, font=fo, fill=255)

QISHAN = [('一出祁山', 228), ('二出散关', 228), ('三出武都', 229), ('四出祁山', 231), ('五出斜谷', 234), ('星落五丈原', 234)]
def scene_qishan(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    idx = int(k - c[0])
    A = Art(); beat_fx(A, t)
    for kk, (x, h) in enumerate(((220, 420), (420, 520), (640, 470), (860, 400))):
        A.d['mid'].polygon([(x - 200, 1360), (x, 1360 - h), (x + 200, 1360)], fill=150)
    pos = [(260, 1100), (420, 1000), (560, 1060), (700, 960), (820, 1040), (920, 900)]
    for i, (x, y) in enumerate(pos):
        if t >= bt(c[0] + i):
            px, py = pos[i - 1] if i else (160, 1300)
            q = ease_out((t - bt(c[0] + i)) / 0.3)
            A.d['red'].line((px, py, lerp(px, x, q), lerp(py, y, q)), fill=255, width=8)
    A.flush(cv)
    for i, ((nm, yr), (x, y)) in enumerate(zip(QISHAN, pos)):
        if t >= bt(c[0] + i):
            stamp(cv, seal(cn_num(i + 1), 50, ZHU if i < 5 else INK), x, y, t, bt(c[0] + i) + 0.1)
    if 0 <= idx < 6 and not gather:
        nm, yr = QISHAN[idx]
        ink_in(cv, text_img(f'公元{cn_num(yr)}年 · {nm}', SERIF, 50, INDIGO, 'Black', bleed=False, spacing=4), W / 2, 1470, t, bt(c[0] + idx), dur=0.2, settle=1.0)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '六出祁山', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '北伐未竟', BRUSH, 160, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '出师未捷身先死', BRUSH, 96, ZHU, W / 2, 1470, t, bt(c[0] + 7), stagger=0.05, seed=111)
    fx.flush(cv)

def art_z_jieting(A, cv, t, u):
    A.d['mid'].polygon([(380, GROUND), (540, 960), (700, GROUND)], fill=220)
    for k in range(4):
        general(A, 500 + k * 30, 1000 + k * 60, 90, dir=1, spear=True, layer='ink')
    ground(A, GROUND)
    for k in range(8):
        a = math.pi * (k / 7)
        x = 540 - 460 * math.cos(a)
        general(A, x, GROUND, 140, dir=1 if x < 540 else -1, spear=True, layer='mid')
    A.d['wash'].rectangle((60, 1330, 360, 1360), fill=170)
    A.d['ink'].line((200, 1345, 200 - 140 * ease_out((u - P) / 0.5), 1345), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('断水', 56, INK), 860, 940, t, t - u + P, rot=6)

def art_z_masu(A, cv, t, u):
    ground(A, GROUND)
    general(A, 360, GROUND, 250, dir=1, kneel=True, bow=50, arm=70, layer='ink')
    kongming(A, 760, GROUND, 270, dir=-1, arm=lerp(30, 100, ease_out((u - P) / 0.3)), fan=False, layer='ink')
    for k in range(5):
        q = ((t * 0.8 + k * 0.2) % 1)
        A.d['wash'].ellipse((735 + k * 4 - 4, GROUND - 240 + q * 40 - 4, 735 + k * 4 + 4, GROUND - 240 + q * 40 + 4), fill=255)
    A.flush(cv)
    stamp(cv, seal('挥泪', 56), 760, 960, t, t - u + 1.5 * P, rot=5)

# ================================================================ 第四回 空城计
def art_z_empty_city(A, cv, t, u):
    """8-beat set piece: Sima's host rolls up → gates wide open, old men sweep → Kongming plays the qin → retreat."""
    ph = u / P
    city_wall(A, 60, W - 60, 1100, gate_x=540, label='西城', open_=1.0)
    A.d['ink'].rectangle((450, 1020, 630, 1036), fill=255)
    kongming(A, 540, 1036, 120, dir=1, kneel=True, bow=0, arm=lerp(60, 90, 0.5 + 0.5 * math.sin(t * 9)), fan=False, layer='ink')
    lantern(A, 380, 940, t, 0, size=18); lantern(A, 700, 940, t, 1, size=18)
    ground(A, GROUND)
    for k in range(3):
        person(A, 440 + k * 70, GROUND, 120, dir=1, robe=False, bow=50, arm=lerp(90, 130, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
    if ph >= 1:
        n = 7
        retreat = ease_out((u - 6 * P) / (2 * P)) if ph >= 6 else 0
        for k in range(n):
            x = lerp(1200, 760 + k * 50, ease_out((u - P) / (2 * P))) + retreat * 600
            rider(A, x, GROUND - (k % 3) * 12, 100, -1 if retreat == 0 else 1, t * (0 if 3 <= ph < 6 else 10) + k, layer='mid', moving=not (3 <= ph < 6), spear=True)
    A.flush(cv)
    if ph >= 3:
        for i in range(int(clamp((u - 3 * P) / (3 * P)) * 5)):
            x = 540 + 80 * math.cos(t * 2 + i); y = 960 - i * 40
            paste(cv, text_img('♪' if False else '琴', SERIF, 30, INDIGO, 'Bold', bleed=False), x, y, 1, 0.6)
    if ph >= 3.2:
        stamp(cv, seal('司马懿', 44, INK), 880, 860, t, t - u + 3.2 * P, rot=6)
    if ph >= 6.5:
        stamp(cv, seal('退兵', 54), 200, 860, t, t - u + 6.5 * P, rot=-6)

def art_z_woodox(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 560), (520, 640), (860, 540))):
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - h), (x + 260, GROUND)], fill=180)
    ground(A, GROUND)
    for k in range(3):
        x = (t * 60 + k * 330) % (W + 200) - 100
        A.d['ink'].rectangle((x - 70, GROUND - 120, x + 70, GROUND - 50), fill=255)
        A.d['ink'].rectangle((x + 60, GROUND - 150, x + 100, GROUND - 100), fill=255)
        for lx in (x - 50, x + 40):
            a = 0.3 * math.sin(t * 6 + k + lx)
            A.d['ink'].line((lx, GROUND - 50, lx + 30 * math.sin(a), GROUND), fill=255, width=8)
        A.d['gold'].rectangle((x - 60, GROUND - 160, x + 50, GROUND - 120), fill=255)
    kongming(A, 160, GROUND, 230, dir=1, arm=60, layer='ink')

def art_z_crossbow(A, cv, t, u):
    ground(A, GROUND)
    general(A, 300, GROUND, 240, dir=1, arm=95, arm2=85, layer='ink')
    A.d['ink'].rectangle((360, GROUND - 210, 520, GROUND - 180), fill=255)
    A.d['ink'].arc((470, GROUND - 260, 530, GROUND - 130), 270, 90, fill=255, width=6)
    kk = (t - G.B0) / P
    for k in range(10):
        q = ((kk * 2 + k * 0.1) % 1)
        arrow(A, lerp(540, 1040, q), GROUND - 195 + (k % 3) * 8, 0, 70)
    A.flush(cv)
    stamp(cv, seal('十矢连发', 44), 820, 940, t, t - u + P, rot=5)

def art_z_lantern(A, cv, t, u):
    starfield(A, t, seed=6)
    city_wall(A, 60, W - 60, 1180, label='平阳', layer='mid')
    ground(A, GROUND)
    for k in range(5):
        q = clamp((u - k * 0.3) / (3 * P))
        x = 220 + k * 160 + 30 * math.sin(t + k); y = lerp(1160, 720, q)
        A.d['yellow'].rounded_rectangle((x - 30, y - 40, x + 30, y + 30), radius=10, fill=230)
        A.d['red'].ellipse((x - 8, y + 20, x + 8, y + 36), fill=255)

def art_z_baguatu(A, cv, t, u):
    cx, cy = 540, 1060
    r = 300
    A.d['ink'].ellipse((cx - 110, cy - 110, cx + 110, cy + 110), outline=255, width=6)
    A.d['ink'].pieslice((cx - 110, cy - 110, cx + 110, cy + 110), 90, 270, fill=255)
    A.d['wash'].ellipse((cx - 55, cy - 110, cx + 55, cy), fill=0)
    A.d['ink'].ellipse((cx - 55, cy, cx + 55, cy + 110), fill=255)
    trig = ['111', '000', '100', '011', '010', '101', '001', '110']
    for i, tg in enumerate(trig):
        if u < i * 0.2: continue
        a = i * math.pi / 4 + t * 0.2
        for j, b in enumerate(tg):
            rr = r - j * 34
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            pa = a + math.pi / 2
            if b == '1':
                A.d['ink'].line((x - 40 * math.cos(pa), y - 40 * math.sin(pa), x + 40 * math.cos(pa), y + 40 * math.sin(pa)), fill=255, width=12)
            else:
                for s_ in (-1, 1):
                    A.d['ink'].line((x + s_ * 8 * math.cos(pa), y + s_ * 8 * math.sin(pa), x + s_ * 40 * math.cos(pa), y + s_ * 40 * math.sin(pa)), fill=255, width=12)

def art_z_overwork(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    kongming(A, 540, GROUND, 230, dir=1, kneel=True, bow=30, arm=lerp(80, 105, 0.5 + 0.5 * math.sin(t * 7)), fan=False, layer='ink')
    for k in range(12):
        A.d['mid'].rectangle((640, 1236 - k * 14, 740, 1248 - k * 14), fill=255)
    A.d['ink'].rectangle((260, 1200, 280, 1250), fill=255)
    fh = 26 + 5 * math.sin(t * 15)
    A.d['red'].polygon([(258, 1200), (282, 1200), (274, 1200 - fh), (268, 1200 - fh)], fill=255)
    A.flush(cv)
    stamp(cv, seal('食少事烦', 44, INK), 820, 940, t, t - u + P, rot=5)

def art_z_dress(A, cv, t, u):
    tent(A, 760, GROUND - 10, 360, 300, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 250, dir=-1, robe=True, hat='crown', arm=lerp(30, 120, ease_out((u - P) / 0.4)), layer='ink')
    A.d['pink'].polygon([(560, GROUND - 210), (640, GROUND - 210), (660, GROUND - 80), (540, GROUND - 80)], fill=255) if 'pink' in A.d else \
        A.d['red'].polygon([(560, GROUND - 210), (640, GROUND - 210), (660, GROUND - 80), (540, GROUND - 80)], fill=200)
    general(A, 340, GROUND, 220, dir=1, kneel=True, bow=40, arm=90, layer='ink')
    A.flush(cv)
    stamp(cv, seal('巾帼', 54), 600, 940, t, t - u + 0.3)

# ================================================================ 第五回 星落五丈原
def art_z_wuzhang(A, cv, t, u):
    for k in range(20):
        q = (t * 0.4 + k / 20) % 1
        x = 80 + (k * 47) % 920 + 30 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['gold'].ellipse((x - 8, y - 5, x + 8, y + 5), fill=200)
    A.d['mid'].polygon([(120, GROUND), (360, 1060), (720, 1060), (960, GROUND)], fill=200)
    tent(A, 540, 1070, 300, 240, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('秋风五丈原', BRUSH, 80, INDIGO), W / 2, 880, t, t - u + P, 0.5)

def art_z_lamps(A, cv, t, u):
    starfield(A, t, seed=8, n=40)
    tent(A, 540, GROUND - 10, 900, 700, layer='wash')
    for k in range(7):
        a = math.pi + k * math.pi / 6
        x = 540 + 280 * math.cos(a); y = GROUND - 80 + 60 * math.sin(a)
        out = k == 3 and u > 2.5 * P
        A.d['ink'].rectangle((x - 6, y, x + 6, y + 40), fill=255)
        if not out:
            fh = 24 + 5 * math.sin(t * 13 + k)
            A.d['red'].polygon([(x - 6, y), (x + 6, y), (x + 2, y - fh), (x - 2, y - fh)], fill=255)
    kongming(A, 540, GROUND - 40, 160, dir=1, kneel=True, bow=40, arm=80, fan=False, layer='ink')
    if u > 2.5 * P:
        general(A, lerp(-100, 240, ease_out((u - 2.5 * P) / 0.4)), GROUND, 200, dir=1, ph=t * 10, arm=60, layer='ink')
        A.flush(cv)
        stamp(cv, seal('魏延', 50, INK), 220, 900, t, t - u + 2.7 * P)

def art_z_star_fall(A, cv, t, u):
    starfield(A, t, seed=9, n=40)
    q = clamp((u - P) / (2 * P))
    sx, sy = lerp(760, 560, q), lerp(760, 1120, q * q)
    rr = 22 * (1 - 0.6 * q)
    A.d['red'].ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=255)
    for k in range(10):
        A.d['wash'].line((sx + k * 14, sy - k * 22, sx + k * 14 + 8, sy - k * 22 - 14), fill=int(220 * (1 - k / 10)), width=4)
    tent(A, 540, GROUND - 10, 320, 260, layer='mid')
    ground(A, GROUND)

def art_z_puppet(A, cv, t, u):
    ground(A, GROUND)
    carriage(A, 300, GROUND, 180, dir=1, horses=False, moving=False, canopy=True)
    kongming(A, 300, GROUND - 120, 110, dir=1, kneel=True, bow=0, arm=60, layer='mid')
    for k in range(6):
        x = lerp(600, 1200, ease_out((u - P) / (2 * P))) + k * 70
        rider(A, x, GROUND - (k % 2) * 10, 120, 1, t * 14 + k, layer='ink', spear=True)
    A.flush(cv)
    type_in(cv, text_img('死诸葛走生仲达', BRUSH, 70, INDIGO), W / 2, 880, t, t - u + 1.5 * P, 0.5)

def art_z_dingjun(A, cv, t, u):
    A.d['mid'].polygon([(100, GROUND), (420, 1000), (660, 1000), (980, GROUND)], fill=200)
    for x in (220, 860):
        A.d['ink'].line((x, GROUND, x, 1060), fill=255, width=12)
        for j in range(4):
            A.d['mid'].ellipse((x - 80 + j * 10, 1040 + j * 70, x + 80 - j * 10, 1100 + j * 70), fill=255)
    A.d['ink'].chord((440, 1160, 640, GROUND + 60), 180, 360, fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('定军山', 50), 540, 940, t, t - u + P)

def art_z_wuhou(A, cv, t, u):
    palace(A, 540, GROUND, 760, layer='mid')
    A.d['ink'].rectangle((400, 1020, 680, 1090), fill=255)
    A.d['ink'].text((420, 1028), '武侯祠', font=font(SERIF, 54, 'Black'), fill=0)
    for x in (140, 940):
        A.d['ink'].line((x, GROUND, x + 6, 900), fill=255, width=14)
        for j in range(5):
            A.d['mid'].ellipse((x - 90, 860 + j * 60, x + 90, 920 + j * 60), fill=255)
    for k in range(4):
        person(A, 280 + k * 160, GROUND, 130, dir=1 if k < 2 else -1, kneel=True, bow=45, arm=60, female=k % 2 == 1, layer='ink')
    for k in range(3):
        q = (t * 0.4 + k / 3) % 1
        A.d['wash'].line((500 + k * 40, 1300 - q * 200, 510 + k * 40 + 10 * math.sin(t * 2 + k), 1260 - q * 200), fill=int(200 * (1 - q)), width=4)

def art_z_legacy(A, cv, t, u):
    feather_fan(A, 540, 1060, 440, 15, p=clamp(u / 0.8), t=t, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('鞠躬尽瘁 死而后已', BRUSH, 80, INK), W / 2, 1400, t, t - u + P, 0.5)

# ================================================================ script
CHAPTERS = {16: ('第一回', '卧龙出山'), 48: ('第二回', '三分天下'), 80: ('第三回', '南征北伐'),
            112: ('第四回', '空城奇谋'), 144: ('第五回', '星落秋风')}

CARDS = [
    C(0, 2, 'hook', 'num', num='三顾茅庐', line='请出一个农夫', art=art_z_hook_cottage),
    C(2, 4, 'hook', 'num', num='草船借箭', line='一夜得箭十万', art=art_z_hook_arrows),
    C(4, 6, 'hook', 'num', num='空城计', line='一张琴退十五万', art=art_z_hook_empty),
    C(6, 8, 'hook', 'num', num='五丈原', line='星落秋风', art=art_z_hook_star),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 卧龙出山
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=181, main='生于琅琊', sub='阳都诸葛氏 · 字孔明', note='琅琊阳都人也 汉司隶校尉诸葛丰后也', art=art_z_birth),
    C(22, 26, 'death', 'card', year=189, main='少年丧父', sub='随叔父诸葛玄 · 辗转南下', note='亮早孤', art=art_z_orphan),
    C(26, 30, 'life', 'card', year=197, main='躬耕南阳', sub='隆中草庐 · 耕读十年', note='躬耕陇亩 好为梁父吟', art=art_z_plough),
    C(30, 34, 'court', 'card', year=200, main='自比管乐', sub='时人莫之许也', note='每自比于管仲 乐毅', art=art_z_guanyue),
    C(34, 38, 'night', 'card', year=206, main='卧龙凤雏', sub='得一可安天下', note='伏龙 凤雏 两人得一 可安天下', art=art_z_dragon_phoenix),
    C(38, 42, 'life', 'card', year=207, main='三顾茅庐', sub='刘备风雪三访 · 方得一见', note='凡三往 乃见', art=art_z_three_visits),
    C(42, 46, 'court', 'card', year=207, main='隆中对', sub='未出茅庐 · 已知三分天下', note='将军欲成霸业 北让曹操占天时 南让孙权占地利', art=art_z_longzhong),
    C(46, 48, 'life', 'card', year=207, main='出山', sub='二十七岁 · 随刘备而去', art=art_z_leave),
    # ---- 第二回 三分天下
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=208, main='舌战群儒', sub='孤身入吴 · 说服孙权联刘抗曹', note='谈笑间 群儒默然', art=art_z_debate),
    C(54, 62, 'works', 'card', year=208, main='草船借箭', sub='大雾漫江 · 草船二十 · 满载而归', note='演义故事 流传千年', art=art_z_boats),
    C(62, 66, 'fate', 'card', year=208, main='借东风', sub='七星坛上 · 祭风三日', note='东风不与周郎便 铜雀春深锁二乔', art=art_z_altar),
    C(66, 70, 'empire', 'card', year=208, main='三分天下', sub='赤壁之后 · 三国鼎立之势成', note='魏 蜀 吴', art=art_z_three_kingdoms),
    C(70, 74, 'war', 'card', year=214, main='入川取蜀', sub='刘备入成都 · 据有益州', note='天府之国', art=art_z_shu),
    C(74, 78, 'death', 'card', year=223, main='白帝托孤', sub='刘备临终 · 托以后事', note='君才十倍曹丕 若嗣子可辅 辅之', art=art_z_baidi),
    C(78, 80, 'court', 'card', year=223, main='丞相治蜀', sub='事无巨细 · 咸决于亮', art=art_z_chancellor),
    # ---- 第三回 南征北伐
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=225, main='七擒孟获', sub='攻心为上 · 南中归心', note='公 天威也 南人不复反矣', art=art_z_menghuo),
    C(86, 90, 'court', 'card', year=227, main='出师表', sub='上表后主 · 誓师北伐', note='鞠躬尽瘁 死而后已', art=art_z_chushi),
    C(90, 98, 'war', 'qishan'),
    C(98, 102, 'war', 'card', year=228, main='街亭失守', sub='马谡违令 · 舍水上山', note='依阻南山 不下据城', art=art_z_jieting),
    C(102, 112, 'death', 'card', year=228, main='挥泪斩马谡', sub='军法如山 · 自贬三等', note='戮谡以谢众', art=art_z_masu),
    # ---- 第四回 空城奇谋
    C(112, 114, 'night', 'chapter'),
    C(114, 122, 'night', 'card', year=228, main='空城计', sub='城门大开 · 焚香抚琴 · 司马懿退兵', note='演义名篇 一曲退大军', art=art_z_empty_city),
    C(122, 126, 'works', 'card', year=231, main='木牛流马', sub='蜀道运粮 · 机巧之器', note='以木牛运', art=art_z_woodox),
    C(126, 130, 'war', 'card', year=231, main='诸葛连弩', sub='一弩十矢', note='损益连弩 谓之元戎', art=art_z_crossbow),
    C(130, 134, 'night', 'card', year=231, main='孔明灯', sub='被困平阳 · 天灯传信', note='相传为孔明所制', art=art_z_lantern),
    C(134, 138, 'works', 'card', year=231, main='八阵图', sub='推演兵法 · 作八阵图', note='功盖三分国 名成八阵图', art=art_z_baguatu),
    C(138, 142, 'fate', 'card', year=234, main='食少事烦', sub='罚二十以上 · 皆亲览焉', note='其能久乎', art=art_z_overwork),
    C(142, 144, 'court', 'card', year=234, main='赠送巾帼', sub='激司马懿出战 · 懿不为所动', art=art_z_dress),
    # ---- 第五回 星落秋风
    C(144, 146, 'fate', 'chapter'),
    C(146, 150, 'fate', 'card', year=234, main='屯兵五丈原', sub='最后一次北伐 · 与司马懿对峙', note='分兵屯田 为久驻之基', art=art_z_wuzhang),
    C(150, 154, 'night', 'card', year=234, main='禳星续命', sub='七星灯 · 魏延闯帐灯灭', note='演义故事', art=art_z_lamps),
    C(154, 158, 'death', 'card', year=234, main='星落五丈原', sub='八月 · 病逝军中 · 年五十四', note='其年八月 亮疾病 卒于军', art=art_z_star_fall),
    C(158, 162, 'war', 'card', year=234, main='死诸葛走生仲达', sub='木像坐车 · 司马懿惊退', note='吾能料生 不便料死', art=art_z_puppet),
    C(162, 166, 'death', 'card', year=234, main='葬定军山', sub='因山为坟 · 冢足容棺', note='敛以时服 不须器物', art=art_z_dingjun),
    C(166, 170, 'end', 'card', year=234, main='武侯祠', sub='千年香火 · 丞相祠堂何处寻', note='出师未捷身先死 长使英雄泪满襟', art=art_z_wuhou),
    C(170, 999, 'end', 'end'),
]
# art_z_legacy is used as the ending backdrop.

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_num(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=INDIGO + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, INDIGO, 110)
        ground(A, 1440)
        kongming(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('诸 葛 亮 · 字孔明', SERIF, 46, INDIGO, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '卧龙', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('武侯', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元181 — 234', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '千古忠臣？', BRUSH, 120, INDIGO, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '穷兵黩武？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    feather_fan(A, 540, 900, 330, 15, p=clamp(u / 0.8), t=t, layer='wash')
    A.flush(cv, alpha=clamp(u / 0.6) * 0.45)
    fx = Art()
    chars_in(cv, fx, '鞠躬尽瘁', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('孔明', 60), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('六出祁山 · 至死未能北定中原', SERIF, 46, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('却成了中国人心中的智慧化身', SERIF, 50, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '他若生在曹营', BRUSH, 100, INDIGO, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('三国会是谁的天下？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=INDIGO + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 255, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=ZHU + (220,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 岳飞', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, qishan=scene_qishan, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾叁集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('一个农夫 · 如何成了千古第一智者？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 320, 335, W / 2 + 320, 335), fill=INDIGO + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, INDIGO, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=INDIGO + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=INDIGO + (255,))
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
