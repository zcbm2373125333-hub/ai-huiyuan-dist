# 千古人物志 · 第玖集 · 乾隆弘历 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：粉彩 —— 松石绿远山 · 「盖章狂魔」章回卡（每回长卷上的御印越盖越多）· 彩瓣 · 彩珠边角
#          · 六拍「盖章狂魔」 · 十全武功十印回顾 · 八拍「马戛尔尼使团」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_yongzheng as Y        # engine + helpers (ink layers drawn last)
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
from render_mingtaizu import cn_year
from render_kangxi import qing_hat, official, throne, rect, lantern, cannon
from render_wudi import camel

F.RIPPLE = False

BORN, DIED = 1711, 1799
END_BEAT = 170
TURQ = (36, 138, 136)               # 松石绿
PINK = (214, 108, 138)              # 粉彩胭脂
GOLDC = (196, 146, 46)
S.LAYERS.append(('turq', TURQ, 0.80, 1.3))
S.LAYERS.append(('pink', PINK, 0.82, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='乾', life='历', court='盛', night='夜', war='戰', empire='隆', works='疆', fate='衰', death='寿', end='乾')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'fencai'
for k in ('night', 'death', 'fate'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (GOLDC, 260, (W * 0.5, 820))
G.THEMES['works']['sun'] = (TURQ, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (PINK, 210, (W * 0.5, 720))
G.THEMES['hook']['tint'] = (1.02, 1.0, 0.98)
G.base_bg.cache_clear()

MTN_COL = {'night': (54, 60, 66), 'death': (64, 64, 66), 'war': (98, 62, 50), 'fate': (80, 78, 74)}
def draw_background(t, theme):
    """松石绿: distant ranges in turquoise-green washes like famille-rose grounds."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 196, 188), (98, 160, 152), MTN_COL.get(theme, (54, 112, 106))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

@lru_cache(None)
def particle_sprite(kind, q):
    if kind != 'fencai':
        return Y.particle_sprite(kind, q)
    s = 40
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = [PINK, TURQ, GOLDC][q]
    d.ellipse((11, 15, 29, 27), fill=col + (220,))
    d.ellipse((16, 18, 24, 24), fill=(255, 245, 230, 200))
    return im.filter(ImageFilter.GaussianBlur(0.6))
G.particle_sprite = particle_sprite

def draw_frame_border(canvas):
    """彩珠: strings of pink / turquoise / gold beads along each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    cols = [PINK, TURQ, GOLDC]
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 150, y), fill=GOLDC + (180,), width=2); d.line((x, y, x, y + sy * 150), fill=GOLDC + (180,), width=2)
        for i in range(7):
            c = cols[i % 3] + (230,)
            bx, by = x + sx * (14 + i * 20), y + sy * 12
            d.ellipse((bx - 7, by - 7, bx + 7, by + 7), fill=c)
            bx, by = x + sx * 12, y + sy * (14 + i * 20)
            d.ellipse((bx - 7, by - 7, bx + 7, by + 7), fill=c)
G.draw_frame_border = draw_frame_border

# ================================================================ 盖章狂魔 chapter card
def landscape_scroll(A, x0, y0, w, h, p):
    ww = w * ease_out(p)
    A.d['wash'].rectangle((x0, y0, x0 + ww, y0 + h), fill=120)
    A.d['ink'].rectangle((x0 - 14, y0 - 10, x0, y0 + h + 10), fill=255)
    A.d['ink'].rectangle((x0 + ww, y0 - 10, x0 + ww + 14, y0 + h + 10), fill=255)
    pts = [(x, y0 + h * 0.75 - h * 0.45 * abs(math.sin(x * 0.012 + 1)) * (0.6 + 0.4 * math.sin(x * 0.031)))
           for x in range(int(x0), int(x0 + ww), 8)]
    if len(pts) > 2:
        A.d['mid'].polygon(pts + [(x0 + ww, y0 + h), (x0, y0 + h)], fill=200)
    return ww

ROYAL = ['乾隆御览之宝', '古稀天子', '三希堂精鉴玺', '八征耄念之宝', '太上皇帝', '乾隆鉴赏', '石渠宝笈', '宜子孙',
         '五福五代堂', '御书房鉴藏宝', '乾隆宸翰']
CH_SEALS = {16: 2, 48: 4, 80: 6, 112: 9, 144: 11}
def art_seal_chapter(A, cv, t, u):
    landscape_scroll(A, 140, 660, 800, 500, u / 0.5)
    A.flush(cv)
    kb = int(round((t - u - G.B0) / P))
    n = CH_SEALS.get(kb, 3)
    r = random.Random(kb)
    for i in range(n):
        x = r.uniform(220, 860); y = r.uniform(720, 1100)
        nm = ROYAL[i % len(ROYAL)]
        stamp(cv, seal(nm, 30 if len(nm) > 4 else 36, ZHU if i % 3 else (150, 30, 40)), x, y, t, t - u + 0.25 + i * 0.12, rot=r.uniform(-8, 8))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_seal_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TURQ, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ primitives
def crane(A, x, y, s, flap=0.0, layer='ink'):
    A.d['wash'].ellipse((x - s * 0.5, y - s * 0.2, x + s * 0.5, y + s * 0.2), fill=255)
    A.d[layer].line((x + s * 0.4, y - s * 0.1, x + s * 0.7, y - s * 0.7), fill=255, width=max(2, int(s * 0.06)))
    A.d['red'].ellipse((x + s * 0.64, y - s * 0.8, x + s * 0.76, y - s * 0.68), fill=255)
    A.d[layer].line((x - s * 0.1, y + s * 0.15, x - s * 0.05, y + s * 0.8), fill=255, width=3)
    A.d[layer].line((x + s * 0.1, y + s * 0.15, x + s * 0.12, y + s * 0.8), fill=255, width=3)
    f = math.sin(flap)
    A.d[layer].polygon([(x - s * 0.3, y - s * 0.1), (x + s * 0.2, y - s * 0.1), (x - s * 0.1, y - s * 0.1 - s * 0.6 * f)], fill=255)

def bear(A, x, y, s, dir=1, ph=0.0, layer='ink'):
    d = A.d[layer]
    def T(u_, v): return (x + dir * u_ * s, y - v * s)
    d.polygon([T(*p_) for p_ in ellipse_pts(0, 0.62, 0.55, 0.32)], fill=255)
    d.polygon([T(*p_) for p_ in ellipse_pts(0.55, 0.85, 0.22, 0.2)], fill=255)
    for ex in (0.48, 0.62):
        d.polygon([T(*p_) for p_ in ellipse_pts(ex, 1.04, 0.06, 0.06)], fill=255)
    for hu, off in ((0.35, 0), (0.2, 1.6), (-0.3, 3.1), (-0.42, 4.7)):
        a = 0.35 * math.sin(ph + off)
        d.line([T(hu, 0.4), T(hu + 0.15 * math.sin(a), 0)], fill=255, width=max(5, int(0.14 * s)))

def palm(A, x, top, t, layer='ink'):
    A.d[layer].line((x, GROUND, x + 20, top), fill=255, width=12)
    for k in range(7):
        a = math.radians(-160 + k * 25) + 0.08 * math.sin(t * 2 + k)
        pts = [(x + 20 + j * 22 * math.cos(a), top + j * 22 * math.sin(a) + j * j * 1.6) for j in range(8)]
        A.d[layer].line(pts, fill=255, width=6)

def dome(A, x, base, w, h, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - h * 0.55, x + w / 2, base), fill=255)
    A.d[layer].chord((x - w / 2, base - h * 1.1, x + w / 2, base - h * 0.1), 180, 360, fill=255)
    A.d['ink'].line((x, base - h * 1.1, x, base - h * 1.3), fill=255, width=4)
    A.d['ink'].ellipse((x - 10, base - h * 1.36, x + 10, base - h * 1.26), outline=255, width=3)

def yurt(A, x, base, w, layer='mid'):
    A.d[layer].rectangle((x - w / 2, base - w * 0.45, x + w / 2, base), fill=255)
    A.d[layer].chord((x - w / 2, base - w * 0.85, x + w / 2, base - w * 0.05), 180, 360, fill=255)
    A.d['wash'].rectangle((x - w * 0.1, base - w * 0.3, x + w * 0.1, base), fill=0)

def tall_ship(A, x, y, s, t, layer='ink'):
    bob = 8 * math.sin(t * 2)
    A.d[layer].polygon([(x - s, y - 40 + bob), (x + s * 1.1, y - 60 + bob), (x + s * 0.8, y + 30 + bob), (x - s * 0.8, y + 30 + bob)], fill=255)
    for k, mx in enumerate((x - s * 0.5, x, x + s * 0.5)):
        A.d[layer].line((mx, y - 40 + bob, mx, y - 420 + bob + k * 30), fill=255, width=6)
        for j in range(3):
            yy = y - 380 + bob + k * 30 + j * 110
            bil = 10 * math.sin(t * 2 + j + k)
            A.d['wash'].polygon([(mx - 70, yy), (mx + 70, yy), (mx + 76 + bil, yy + 90), (mx - 64 + bil, yy + 90)], fill=255)
    A.d['red'].polygon([(x + s * 0.5, y - 400 + bob + 60), (x + s * 0.5 + 60, y - 390 + bob + 60), (x + s * 0.5, y - 370 + bob + 60)], fill=255)

def peony(A, x, y, r, layer='pink'):
    for j in range(6):
        a = j * math.pi / 3
        A.d[layer].ellipse((x + r * 0.5 * math.cos(a) - r * 0.6, y + r * 0.5 * math.sin(a) - r * 0.6,
                            x + r * 0.5 * math.cos(a) + r * 0.6, y + r * 0.5 * math.sin(a) + r * 0.6), fill=255)
    A.d['gold'].ellipse((x - r * 0.25, y - r * 0.25, x + r * 0.25, y + r * 0.25), fill=255)

def opera_actor(A, x, y, h, t, layer='ink'):
    person(A, x, y, h, dir=1, robe=True, hat='crown', arm=lerp(30, 150, 0.5 + 0.5 * math.sin(t * 3)), layer=layer)
    sl = 0.5 + 0.5 * math.sin(t * 3)
    pts = [(x + 0.1 * h + j * 14, y - 0.75 * h - sl * 0.25 * h + 18 * math.sin(t * 5 + j * 0.6)) for j in range(10)]
    A.d['wash'].line(pts, fill=255, width=10)

# ================================================================ hooks
def art_q_hook_old(A, cv, t, u):
    A.d['ink'].line((760, GROUND, 800, 860), fill=255, width=16)
    for k in range(4):
        y = 860 + k * 80
        A.d['mid'].ellipse((640 - k * 10, y - 30, 980 + k * 10, y + 30), fill=255)
    ground(A, GROUND)
    person(A, 400, GROUND, 280, dir=1, hat='crown', bow=12, arm=60, layer='ink')
    A.d['ink'].line((470, GROUND - 160, 500, GROUND), fill=255, width=6)
    A.d['wash'].line((420, GROUND - 230, 430, GROUND - 170), fill=255, width=8)
    crane(A, lerp(980, 640, ease_out(u / (1.6 * P))), 1080, 90, t * 6)

def art_q_hook_two_thrones(A, cv, t, u):
    throne(A, 540, 1250, 1.6)
    person(A, 540, 1150, 190, dir=1, hat='crown', arm=50, layer='wash')
    throne(A, 540, GROUND, 0.9)
    q = ease_out(u / (1.2 * P))
    person(A, 540, GROUND - 60, 140, dir=1, hat='crown', arm=20, layer='ink')
    for k in range(4):
        official(A, 120 + k * 70 if k < 2 else 860 + (k - 2) * 70, GROUND, 140, dir=1 if k < 2 else -1, kneel=True, bow=45, arm=60, layer='mid')

def art_q_hook_poems(A, cv, t, u):
    for k in range(22):
        q = ((u * 0.8 + k / 22) % 1)
        x = 120 + (k * 47) % 840; y = lerp(640, GROUND - 40, q)
        A.d['mid'].polygon([rotp(p_, (x, y), q * 4 + k) for p_ in ((x - 30, y - 20), (x + 30, y - 20), (x + 30, y + 20), (x - 30, y + 20))], fill=200)
    n = int(clamp(u / (1.5 * P)) * 10)
    for k in range(n):
        A.d['mid'].rectangle((360, GROUND - 14 - k * 18, 720, GROUND - k * 18), fill=255)
        A.d['ink'].rectangle((360, GROUND - 14 - k * 18, 720, GROUND - k * 18), outline=200, width=2)
    ground(A, GROUND)

def art_q_hook_sun(A, cv, t, u):
    q = clamp(u / (2 * P))
    y = 860 - 160 * math.sin(math.pi * min(1, q * 1.4))
    if q > 0.7:
        y = lerp(860 - 160 * math.sin(math.pi * 0.98), 1220, (q - 0.7) / 0.3)
    sun(cv, 540, y, 170, GOLDC if q < 0.7 else ZHU, 150)
    palace(A, 540, GROUND, 720, layer='ink')

# ================================================================ 第一回 天选之孙
def art_q_moongate(A, cv, t, u):
    A.d['mid'].rectangle((140, 900, 940, GROUND), fill=200)
    A.d['wash'].ellipse((330, 960, 750, GROUND + 160), fill=0)
    A.d['ink'].ellipse((330, 960, 750, GROUND + 160), outline=255, width=10)
    A.d['wash'].ellipse((500, 1040, 620, 1160), fill=255)
    A.d['ink'].line((820, GROUND, 830, 980), fill=255, width=10)
    for k in range(18):
        a = k * 0.35
        A.d['gold'].ellipse((830 + 70 * math.cos(a) - 5, 960 + 50 * math.sin(a) - 5, 830 + 70 * math.cos(a) + 5, 960 + 50 * math.sin(a) + 5), fill=255)
    ground(A, GROUND)
    person(A, 540, GROUND, 220, dir=1, female=True, baby=True, layer='ink')

def art_q_peony(A, cv, t, u):
    for k in range(9):
        x = 100 + k * 110; y = 1230 + (k % 2) * 40
        A.d['turq'].line((x, GROUND, x + 10, y), fill=255, width=6)
        peony(A, x + 10, y - 10, 34 + 6 * math.sin(t * 2 + k))
    ground(A, GROUND)
    person(A, 760, GROUND, 300, dir=-1, hat='crown', bow=10, arm=lerp(20, 70, ease_out((u - P) / 0.4)), layer='ink')
    x = walk_x(160, 470, u, 1.5 * P)
    person(A, x, GROUND, 170, dir=1, hat='knot', bow=40 if u > 1.8 * P else 0, ph=t * 6 if u < 1.5 * P else None, arm=60, layer='ink')

def art_q_bear(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        A.d['mid'].polygon([(80 + k * 170, GROUND), (130 + k * 170, 900 + (k % 2) * 60), (180 + k * 170, GROUND)], fill=200)
    bx = lerp(980, 640, ease_out(u / (1.8 * P)))
    fall = u > 2.4 * P
    if not fall:
        bear(A, bx, GROUND, 260, -1, t * 10, layer='ink')
    else:
        A.d['ink'].polygon([q for q in ellipse_pts(bx, GROUND - 70, 170, 70)], fill=255)
    rider(A, 300, GROUND, 230, 1, 0.5, layer='ink', moving=False)
    q = clamp((u - 2 * P) / 0.3)
    if 0 < q < 1:
        arrow(A, lerp(120, bx - 100, q), lerp(1150, GROUND - 160, q), 0.2, 90)

def art_q_study(A, cv, t, u):
    A.d['ink'].rectangle((240, 1240, 840, 1270), fill=255)
    for lx in (260, 800): A.d['ink'].rectangle((lx, 1270, lx + 18, GROUND), fill=255)
    for k in range(3):
        person(A, 380 + k * 160, GROUND, 170, dir=1, hat='knot', kneel=True, bow=30, arm=90, layer='ink' if k == 1 else 'mid')
        A.d['mid'].rectangle((430 + k * 160, 1210, 500 + k * 160, 1236), fill=255)
    official(A, 900, GROUND, 250, dir=-1, arm=lerp(30, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    lantern(A, 180, 1000, t, 0, size=24)
    ground(A, GROUND)

def art_q_baoqin(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 290, dir=-1, hat='crown', arm=80, layer='ink')
    person(A, 400, GROUND, 230, dir=1, kneel=True, bow=30, arm=85, hat='knot', layer='ink')
    q = ease_out(u / (1.4 * P))
    x = lerp(660, 500, q)
    A.d['gold'].rectangle((x - 50, GROUND - 200, x + 50, GROUND - 130), fill=255)
    A.d['ink'].rectangle((x - 50, GROUND - 200, x + 50, GROUND - 130), outline=255, width=3)
    A.flush(cv)
    stamp(cv, seal('宝', 66), 400, 980, t, t - u + 1.6 * P, rot=-5)

def art_q_couple(A, cv, t, u):
    A.d['wash'].rectangle((60, 1250, W - 60, 1340), fill=170)
    waves(A, 1260, t, rows=2, amp=5, speed=1.2)
    for i, x in enumerate((600, 680)):
        xx = x + 20 * math.sin(t + i)
        A.d['pink' if i else 'turq'].ellipse((xx - 34, 1240, xx + 34, 1270), fill=255)
        A.d['ink'].ellipse((xx + 18, 1218, xx + 40, 1240), fill=255)
    A.d['mid'].rectangle((200, 980, 500, 1010), fill=255)
    A.d['ink'].polygon([(160, 990), (540, 990), (440, 900), (260, 900)], fill=255)
    for lx in (220, 470): A.d['ink'].rectangle((lx, 1010, lx + 14, GROUND), fill=255)
    person(A, 300, GROUND, 230, dir=1, hat='knot', arm=60, layer='ink')
    person(A, 410, GROUND, 210, dir=-1, female=True, arm=60, layer='ink')
    ground(A, GROUND)

def art_q_empty_robe(A, cv, t, u):
    for x in (200, 880):
        h = 80 + 10 * math.sin(t * 4 + x)
        A.d['ink'].rectangle((x - 10, GROUND - 260, x + 10, GROUND), fill=255)
        A.d['red'].polygon([(x - 8, GROUND - 260), (x + 8, GROUND - 260), (x, GROUND - 260 - h * 0.6)], fill=255)
    throne(A, 540, GROUND, 1.4)
    A.d['yellow'].polygon([(470, 1100), (610, 1100), (660, 1320), (420, 1320)], fill=255)
    for k in range(6):
        A.d['wash'].line((120 + k * 160, 700, 130 + k * 160 + 10 * math.sin(t + k), 900), fill=255, width=10)

def art_q_openbox(A, cv, t, u):
    A.d['ink'].rectangle((280, 760, 800, 880), fill=255)
    A.d['ink'].text((300, 772), '正大光明', font=font(SERIF, 96, 'Black'), fill=0)
    q = ease_out(u / (0.8 * P))
    A.d['gold'].rectangle((470, lerp(900, 1100, q), 610, lerp(980, 1180, q)), fill=255)
    A.flush(cv)
    if u > 0.8 * P:
        ink_in(cv, text_img('弘历', SERIF, 110, INK, 'Black', bleed=False), 540, 1320, t, t - u + 0.8 * P, dur=0.3, settle=1.1)

# ================================================================ 第二回 盛世天子
def art_q_plaza(A, cv, t, u):
    palace(A, 540, 1020, 560, layer='ink')
    for r_ in range(6):
        y = 1080 + r_ * 50
        n = 8 + r_
        for k in range(n):
            x = 540 + (k - (n - 1) / 2) * (680 / n)
            b = 45 * ease_out((u - 0.4 - r_ * 0.08) / 0.3)
            person(A, x, y + 40, 50 + r_ * 6, dir=1, kneel=True, bow=b, arm=60, layer='mid' if r_ < 3 else 'ink')
    A.d['red'].polygon([(510, 1040), (570, 1040), (600, GROUND), (480, GROUND)], fill=200)

def art_q_release(A, cv, t, u):
    for k in range(6):
        A.d['ink'].line((560 + k * 70, 900, 560 + k * 70, GROUND), fill=255, width=8)
    op = ease_out((u - 0.4) / 0.5)
    A.d['ink'].rectangle((540, 880, 960, 900), fill=255)
    for k in range(2):
        x = walk_x(800 - k * 80, 260 - k * 120, u - 0.6, 2 * P)
        person(A, x, GROUND, 220, dir=-1, robe=True, hat='crown', ph=t * 6 + k, arm=20, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('宽', 70), 300, 960, t, t - u + P)

def art_q_grief(A, cv, t, u):
    A.d['wash'].rectangle((60, 1200, W - 60, 1320), fill=160)
    waves(A, 1210, t, rows=3, amp=6, speed=1.2)
    A.d['ink'].polygon([(260, 1220), (820, 1210), (760, 1270), (320, 1270)], fill=255)
    A.d['mid'].rectangle((380, 1110, 700, 1210), fill=255)
    for k in range(14):
        q = ((t * 0.25 + k / 14) % 1)
        x = 120 + k * 64 + 20 * math.sin(t + k); y = lerp(700, 1300, q)
        A.d['wash'].ellipse((x - 9, y - 6, x + 9, y + 6), fill=255)
    person(A, 520, 1210, 130, dir=1, hat='crown', kneel=True, bow=55, arm=70, layer='ink')

def art_q_fountain(A, cv, t, u):
    A.d['mid'].rectangle((200, 980, 880, 1250), fill=200)
    for k in range(7):
        x = 240 + k * 100
        A.d['ink'].rectangle((x - 12, 1000, x + 12, 1250), fill=255)
    A.d['ink'].polygon([(180, 990), (900, 990), (820, 900), (260, 900)], fill=255)
    A.d['ink'].chord((420, 830, 660, 1000), 180, 360, fill=255)
    A.d['wash'].rectangle((160, 1300, 920, 1360), fill=180)
    for k in range(6):
        sx = 240 + k * 120
        pts = [(sx + f * 120, 1300 - 260 * f * (1 - f) * 4 * (0.8 + 0.2 * math.sin(t * 6 + k))) for f in np.linspace(0, 1, 16)]
        A.d['turq'].line(pts, fill=255, width=5)
    ground(A, GROUND)

def art_q_jiangnan(A, cv, t, u):
    A.d['wash'].rectangle((60, 1240, W - 60, 1350), fill=170)
    waves(A, 1250, t, rows=2, amp=5, speed=1.4)
    for i, x in enumerate((120, 300, 780, 940)):
        A.d['wash'].rectangle((x - 70, 1060, x + 70, 1240), fill=60)
        A.d['ink'].rectangle((x - 70, 1060, x + 70, 1240), outline=255, width=3)
        A.d['ink'].polygon([(x - 80, 1060), (x - 50, 1030), (x - 20, 1060), (x + 10, 1020), (x + 40, 1060), (x + 80, 1030), (x + 80, 1060)], fill=255)
    A.d['ink'].arc((360, 1110, 720, 1390), 180, 360, fill=255, width=14)
    person(A, 540, 1120, 130, dir=1, hat='crown', arm=50, layer='ink')
    x = (t * 60) % (W + 200) - 100
    A.d['ink'].polygon([(x - 70, 1270), (x + 70, 1270), (x + 50, 1300), (x - 50, 1300)], fill=255)

def art_q_poet(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 540, GROUND, 230, dir=1, hat='crown', kneel=True, bow=20, arm=lerp(80, 105, 0.5 + 0.5 * math.sin(t * 8)), layer='ink')
    n = int(clamp(u / (3 * P)) * 40)
    for k in range(n):
        x = 640 + (k % 4) * 40; y = 1236 - (k // 4) * 14
        A.d['mid'].rectangle((x, y, x + 36, y + 10), fill=255)
    A.flush(cv)
    cnt = int(clamp(u / (3 * P)) * 43000)
    paste(cv, text_img(f'{cnt:,}首', SERIF, 60, ZHU, 'Black', bleed=False), 540, 940, 1, 1)

def art_q_envoys_scroll(A, cv, t, u):
    p = ease_out(u / (2 * P))
    w = 820 * p
    A.d['wash'].rectangle((130, 880, 130 + w, 1300), fill=110)
    A.d['ink'].rectangle((116, 860, 130, 1320), fill=255); A.d['ink'].rectangle((130 + w, 860, 144 + w, 1320), fill=255)
    palace(A, 220, 1100, 160, layer='mid') if w > 200 else None
    for k in range(int(w / 70)):
        x = 330 + k * 70; y = 1260 - (k % 2) * 40
        hat = ['helmet', 'knot', 'crown'][k % 3]
        person(A, x, y, 90, dir=-1, robe=True, hat=hat, arm=40, layer='ink' if k % 2 else 'mid')
        if k % 3 == 0:
            camel(A, x + 30, y + 10, 60, -1, 0.0, layer='mid')

# ================================================================ 第三回 十全武功
def art_q_dzungar(A, cv, t, u):
    for i, x in enumerate((700, 860, 980)):
        yurt(A, x, GROUND - 30, 140)
        if u > 1.5 * P:
            flames(A, x, GROUND - 120, 100, 120 * ease_out((u - 1.5 * P) / 0.5), t + i, n=3, seed=80 + i, smoke=True)
    ground(A, GROUND)
    for k in range(4):
        x = lerp(-200 - k * 150, 500 - k * 150, ease_out(u / (2 * P)))
        rider(A, x, GROUND - (k % 2) * 14, 190, 1, t * 13 + k, layer='ink' if k % 2 == 0 else 'mid', spear=True)

def art_q_oasis(A, cv, t, u):
    for k, (x, y0) in enumerate(((60, 1300), (500, 1340))):
        pts = [(xx, y0 - 50 * math.sin((xx - x) * 0.006 + k)) for xx in range(60, W - 59, 10)]
        A.d['wash'].polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=200 if k == 0 else 255)
    dome(A, 640, 1250, 200, 200, layer='mid')
    dome(A, 860, 1260, 130, 140, layer='mid')
    for x in (520, 980):
        A.d['ink'].rectangle((x - 14, 960, x + 14, 1260), fill=255)
    palm(A, 220, 1000, t)
    for k in range(3):
        person(A, lerp(-100, 300, ease_out(u / (2 * P))) - k * 80, GROUND, 180, dir=1, robe=False, hat='helmet', spear=True, ph=t * 8 + k, layer='ink')

def art_q_xinjiang(A, cv, t, u):
    for k, (x, y0) in enumerate(((60, 1300), (500, 1360))):
        pts = [(xx, y0 - 40 * math.sin((xx - x) * 0.006 + k)) for xx in range(60, W - 59, 10)]
        A.d['wash'].polygon(pts + [(W - 60, GROUND + 30), (60, GROUND + 30)], fill=200 if k == 0 else 255)
    for k in range(4):
        x = (t * 60 + k * 240) % (W + 300) - 150
        camel(A, x, 1360, 120, 1, t * 5 + k, layer='ink')
    p = ease_out(u / (1.2 * P))
    A.d['yellow'].rectangle((540 - 260 * p, 840, 540 + 260 * p, 1000), fill=255)
    A.d['ink'].rectangle((540 - 274 * p, 830, 540 - 260 * p, 1010), fill=255); A.d['ink'].rectangle((540 + 260 * p, 830, 540 + 274 * p, 1010), fill=255)
    if p > 0.8:
        A.d['ink'].text((420, 850), '新疆', font=font(BRUSH, 120), fill=255)

def art_q_jinchuan(A, cv, t, u):
    A.d['mid'].polygon([(400, GROUND), (640, 860), (900, 960), (1020, GROUND)], fill=200)
    for i, (x, y) in enumerate(((640, 980), (820, 1080))):
        A.d['ink'].polygon([(x - 50, y + 220), (x + 50, y + 220), (x + 34, y), (x - 34, y)], fill=255)
        for j in range(4):
            A.d['wash'].rectangle((x - 8, y + 30 + j * 45, x + 8, y + 50 + j * 45), fill=0)
    ground(A, GROUND)
    kk = (t - G.B0) / P
    for i, x in enumerate((140, 300)):
        f = ((kk + i * 0.5) % 1)
        cannon(A, x, GROUND, 110, 1, fire=f if f < 0.6 else 0)

def art_q_burma(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    for x in (140, 360, 880):
        palm(A, x, 980 + (x % 3) * 30, t)
    ground(A, GROUND)
    for k in range(4):
        person(A, 480 + k * 90, GROUND, 170, dir=1, robe=False, hat='helmet', spear=True, bow=20, ph=t * 3 + k, layer='ink')

def art_q_annam(A, cv, t, u):
    A.d['wash'].rectangle((60, 1150, W - 60, 1380), fill=160)
    waves(A, 1160, t, rows=4, amp=8, speed=2)
    for k in range(5):
        x = lerp(-200, 700, ease_out(u / (2 * P))) - k * 150
        A.d['ink'].rectangle((x - 60, 1230 + (k % 2) * 30, x + 60, 1250 + (k % 2) * 30), fill=255)
        person(A, x, 1230 + (k % 2) * 30, 100, dir=1, robe=False, hat='helmet', spear=True, layer='ink')

def art_q_gurkha(A, cv, t, u):
    for k, (x, h) in enumerate(((240, 520), (560, 640), (860, 500))):
        A.d['mid'].polygon([(x - 300, GROUND), (x, GROUND - h), (x + 300, GROUND)], fill=200)
        A.d['wash'].polygon([(x - 90, GROUND - h + 150), (x, GROUND - h), (x + 90, GROUND - h + 150)], fill=0)
    q = clamp(u / (2 * P))
    for k in range(6):
        f = clamp(q - k * 0.06)
        x = lerp(120, 520, f); y = lerp(GROUND, GROUND - 520, f)
        person(A, x - k * 20, y + k * 30, 90, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, layer='ink')

def art_q_taiwan(A, cv, t, u):
    A.d['wash'].rectangle((60, 1200, W - 60, 1380), fill=160)
    waves(A, 1210, t, rows=3, amp=8, speed=2)
    A.d['ink'].rectangle((600, 1040, 960, 1200), fill=255)
    for x in range(600, 960, 40): A.d['ink'].rectangle((x, 1010, x + 24, 1040), fill=255)
    A.d['ink'].polygon([(560, 1200), (1000, 1200), (980, 1240), (580, 1240)], fill=255)
    for k in range(3):
        x = lerp(-150, 380, ease_out(u / (2 * P))) - k * 170
        boat(A, x, 1260, 140, t + k)
    if u > P:
        for k in range(3):
            rr = 40 + 30 * ((t * 2 + k) % 1)
            A.d['wash'].ellipse((700 + k * 100 - rr, 1080 - rr, 700 + k * 100 + rr, 1080 + rr), fill=200)

TEN = ['准噶尔', '准噶尔', '回部', '金川', '金川', '缅甸', '安南', '台湾', '廓尔喀', '廓尔喀']
def scene_ten(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    for i in range(10):
        x = 160 + (i % 5) * 190; y = 940 + (i // 5) * 260
        A.d['ink'].rectangle((x - 80, y - 100, x + 80, y + 100), outline=200, width=3)
    A.flush(cv)
    for i, nm in enumerate(TEN):
        st = bt(c[0] + i * 0.6)
        if t < st: continue
        x = 160 + (i % 5) * 190; y = 940 + (i // 5) * 260
        gx, gy = lerp(x, 540, ease_expo((t - gather_t) / 0.4) * 0.25 if gather else 0), lerp(y, 1060, ease_expo((t - gather_t) / 0.4) * 0.25 if gather else 0)
        stamp(cv, seal(nm, 44 if len(nm) <= 2 else 36, ZHU if i % 2 == 0 else INK), gx, gy, t, st, rot=(i % 3 - 1) * 5)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '十全武功', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
        n = min(10, int((t - s0) / (0.6 * P)) + 1)
        paste(cv, text_img(f'第{cn_num(n)}功', SERIF, 50, ZHU, 'Black', bleed=False), W / 2, 1460, 1, 1)
    else:
        chars_in(cv, fx, '十全老人', BRUSH, 170, INK, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '自诩武功十全', BRUSH, 110, ZHU, W / 2, 1460, t, bt(c[0] + 7), stagger=0.06, seed=111)
    fx.flush(cv)

# ================================================================ 第四回 文治与盖章
def art_q_siku(A, cv, t, u):
    for r_ in range(3):
        for k in range(6):
            x = 140 + k * 140; y = 760 + r_ * 130
            A.d['mid'].rectangle((x, y, x + 120, y + 110), outline=255, width=3)
            n = int(clamp(u / (2 * P) - r_ * 0.2 - k * 0.04) * 8)
            for j in range(n):
                A.d['pink' if (j + k) % 4 == 0 else ('turq' if (j + k) % 4 == 1 else 'ink')].rectangle((x + 6 + j * 14, y + 20, x + 16 + j * 14, y + 104), fill=255)
    for k in range(4):
        person(A, 200 + k * 220, GROUND, 150, dir=1, hat='knot', kneel=True, bow=30, arm=100, layer='ink')
    ground(A, GROUND)

def art_q_stamping(A, cv, t, u):
    """6-beat set piece: the Fuchun scroll fills up with imperial seals and inscriptions."""
    landscape_scroll(A, 120, 760, 840, 520, 1.0)
    fo = font(SERIF, 26, 'Bold')
    r = random.Random(5)
    n_ins = int(clamp(u / (6 * P)) * 26)
    for k in range(n_ins):
        x = r.uniform(150, 900); y = r.uniform(780, 1200)
        for j in range(r.randint(3, 6)):
            A.d['ink'].text((x, y + j * 26), '御题诗句'[j % 4], font=fo, fill=200)
    A.flush(cv)
    r2 = random.Random(11)
    n = int(clamp(u / (5.5 * P)) * 34) + 1
    for i in range(n):
        x = r2.uniform(170, 900); y = r2.uniform(800, 1240)
        nm = ROYAL[i % len(ROYAL)]
        stamp(cv, seal(nm, 26 if len(nm) > 4 else 32, ZHU), x, y, t, t - u + i * (5.5 * P / 34), rot=r2.uniform(-10, 10))
    paste(cv, text_img(f'御印 × {n}', SERIF, 46, ZHU, 'Black', bleed=False), W / 2, 1360, 1, 1)

def art_q_wenziyu(A, cv, t, u):
    A.d['mid'].rectangle((300, 820, 780, 1250), fill=150)
    fo = font(SERIF, 52, 'Bold')
    line = '一把心肠论浊清'
    for i, ch in enumerate(line):
        A.d['ink'].text((620, 840 + i * 56), ch, font=fo, fill=255)
    A.flush(cv)
    q = ease_out((u - P) / 0.4)
    if q > 0:
        d = ImageDraw.Draw(cv)
        y = 840 + 5 * 56 + 30
        d.ellipse((606, y - 34, 606 + 80 * q, y + 30), outline=ZHU + (240,), width=6)
    if u > 2 * P:
        stamp(cv, seal('斩', 70), 400, 1050, t, t - u + 2 * P, rot=-6)

def art_q_redact(A, cv, t, u):
    for p_i, x0 in enumerate((180, 560)):
        A.d['mid'].rectangle((x0, 820, x0 + 340, 1300), fill=150)
        for j in range(10):
            y = 850 + j * 44
            A.d['ink'].line((x0 + 30, y, x0 + 310, y), fill=150, width=6)
            if (j * 7 + p_i * 3) % 3 == 0 and u > (0.3 + j * 0.15) * 1.0:
                A.d['ink'].rectangle((x0 + 26, y - 10, x0 + 314, y + 10), fill=255)
    ground(A, GROUND)

def art_q_heshen(A, cv, t, u):
    person(A, 760, GROUND, 290, dir=-1, hat='crown', arm=lerp(30, 70, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    official(A, 420, GROUND, 250, dir=1, bow=20, arm=70, layer='ink')
    n = int(clamp(u / (3 * P)) * 15)
    for k in range(n):
        x = 160 + (k % 5) * 40; y = GROUND - 20 - (k // 5) * 30
        A.d['gold'].ellipse((x - 20, y - 14, x + 20, y + 14), fill=255)
    ground(A, GROUND)

def art_q_population(A, cv, t, u):
    for k in range(7):
        x = 120 + k * 140
        A.d['turq'].line((x, GROUND, x + 4, 1080), fill=255, width=6)
        A.d['gold'].polygon([(x - 6, 1100), (x + 14, 1100), (x + 10, 1180), (x - 2, 1180)], fill=255)
        for j in range(3):
            A.d['turq'].line((x + 2, 1150 + j * 50, x + 50 * (1 if j % 2 else -1), 1120 + j * 50), fill=255, width=5)
    n = int(clamp(u / (3 * P)) * 30) + 3
    for k in range(n):
        x = 80 + (k * 31) % 920; y = GROUND - (k % 3) * 20
        person(A, x, y, 70, dir=1 if k % 2 else -1, robe=False, arm=20, layer='mid')
    A.flush(cv)
    yi = '一' if u < P else ('二' if u < 2 * P else '三')
    paste(cv, text_img(f'{yi}亿', SERIF, 90, ZHU, 'Black', bleed=False), W / 2, 940, 1, 1)

def art_q_opera(A, cv, t, u):
    A.d['ink'].rectangle((200, 1250, 880, 1290), fill=255)
    for x in (230, 850): A.d['ink'].rectangle((x - 14, 860, x + 14, 1250), fill=255)
    A.d['ink'].polygon([(160, 870), (920, 870), (820, 780), (260, 780)], fill=255)
    A.d['red'].rectangle((240, 880, 840, 920), fill=255)
    for k in range(4):
        lantern(A, 300 + k * 160, 940, t, k, size=20)
    opera_actor(A, 540, 1250, 260, t, layer='ink')
    for k in range(6):
        person(A, 140 + k * 160, GROUND, 110, dir=1, kneel=True, bow=10, arm=40, layer='mid')

# ================================================================ 第五回 盛极而衰
def art_q_macartney(A, cv, t, u):
    """8-beat set piece: the British ship arrives → gifts → refused → 天朝物产丰盈 → ship sails → 1840."""
    ph = u / P
    A.d['wash'].rectangle((60, 1180, W - 60, 1380), fill=150)
    waves(A, 1190, t, rows=4, amp=8, speed=2)
    sx = lerp(1300, 760, ease_out(u / (2 * P))) if ph < 6 else lerp(760, 1400, ease_out((u - 6 * P) / (2 * P)))
    tall_ship(A, sx, 1240, 170, t, layer='mid')
    if 2 <= ph < 6:
        person(A, 600, 1180, 190, dir=-1, robe=False, hat='helmet', bow=25 if ph >= 3 else 0, arm=70, layer='ink')
        gx = [(420, 'scope'), (340, 'globe'), (260, 'clock')]
        for i, (x, kind) in enumerate(gx):
            if ph < 2 + i * 0.6: continue
            if kind == 'scope':
                A.d['ink'].line((x - 50, 1170, x + 40, 1120), fill=255, width=14); A.d['ink'].line((x, 1150, x - 20, 1180), fill=255, width=5)
            elif kind == 'globe':
                A.d['turq'].ellipse((x - 40, 1100, x + 40, 1180), fill=255); A.d['ink'].ellipse((x - 40, 1100, x + 40, 1180), outline=255, width=3)
            else:
                A.d['gold'].rectangle((x - 30, 1100, x + 30, 1180), fill=255); A.d['ink'].ellipse((x - 20, 1110, x + 20, 1150), outline=255, width=3)
        throne(A, 140, 1180, 0.6)
        person(A, 140, 1120, 110, dir=1, hat='crown', arm=lerp(30, 150, ease_out((u - 4 * P) / 0.3)) if ph >= 4 else 30, layer='ink')
    A.flush(cv)
    if ph >= 4.5:
        type_in(cv, text_img('天朝物产丰盈 无所不有', BRUSH, 66, INK), W / 2 + 20, 1450, t, t - u + 4.5 * P, 0.6)
    if ph >= 6.5:
        stamp(cv, seal('四十七年后', 44, INK), 300, 960, t, t - u + 6.5 * P, rot=-5)
        stamp(cv, seal('鸦片战争', 50), 780, 960, t, t - u + 7 * P, rot=5)

def art_q_abdicate(A, cv, t, u):
    ground(A, GROUND)
    person(A, 320, GROUND, 300, dir=1, hat='crown', bow=10, arm=lerp(40, 80, ease_out(u / P)), layer='ink')
    person(A, 720, GROUND, 260, dir=-1, hat='crown', arm=lerp(20, 80, ease_out(u / P)), layer='ink')
    pull = 0.5 + 0.5 * math.sin(t * 2.5) if u > 1.5 * P else 0
    x = lerp(470, 520, pull)
    A.d['gold'].rectangle((x - 40, GROUND - 230, x + 40, GROUND - 170), fill=255)
    A.d['ink'].ellipse((x - 26, GROUND - 270, x + 26, GROUND - 228), fill=255)
    A.flush(cv)
    if u > 2 * P:
        stamp(cv, seal('训政', 56), 320, 950, t, t - u + 2 * P, rot=-5)

def art_q_white_lotus(A, cv, t, u):
    ground(A, GROUND)
    off = (t * 120) % 150
    for i in range(-1, 8):
        x = i * 150 + off - 60
        person(A, x, GROUND, 190, dir=1, robe=False, ph=t * 7 + i, arm=150, layer='ink')
        A.d['wash'].rectangle((x - 20, GROUND - 200, x + 20, GROUND - 186), fill=255)
        flames(A, x + 30, GROUND - 330, 34, 60, t + i, n=2, seed=90 + i, smoke=False)

def art_q_snow_palace(A, cv, t, u):
    A.d['red'].rectangle((60, 1080, W - 60, 1300), fill=160)
    A.d['ink'].polygon([(30, 1090), (W - 30, 1090), (W - 90, 1020), (90, 1020)], fill=255)
    A.d['wash'].polygon([(90, 1020), (W - 90, 1020), (W - 100, 1008), (100, 1008)], fill=255)
    for k in range(40):
        q = (t * 0.2 + k / 40) % 1
        x = 80 + (k * 23) % 920 + 15 * math.sin(t + k); y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    crow(A, 300, 990, 24, 0.2)
    ground(A, GROUND)

def art_q_fall_he(A, cv, t, u):
    fall = ease_out((u - P) / 0.6) if u > P else 0
    for k in range(10):
        x = 300 + (k % 3) * 60 + fall * k * 30
        y = GROUND - 30 - (k // 3) * 60 + fall * (k // 3) * 60
        A.d['gold'].ellipse((x - 30, y - 20, x + 30, y + 20), fill=255)
    official(A, 420, GROUND, 230, dir=1, bow=lerp(10, 50, fall), arm=60, layer='ink') if fall < 0.5 else \
        person(A, 420, GROUND, 230, dir=1, kneel=True, bow=55, arm=70, hat='none', layer='ink')
    chest_x = 820
    A.d['ink'].rectangle((chest_x - 110, GROUND - 160, chest_x + 110, GROUND), outline=255, width=6)
    for k in range(int(fall * 8)):
        A.d['gold'].ellipse((chest_x - 80 + (k % 4) * 50 - 20, GROUND - 40 - (k // 4) * 40 - 14, chest_x - 80 + (k % 4) * 50 + 20, GROUND - 40 - (k // 4) * 40 + 14), fill=255)
    person(A, 960, GROUND, 250, dir=-1, hat='crown', arm=60, layer='ink')
    ground(A, GROUND)

# ================================================================ script
CHAPTERS = {16: ('第一回', '天选之孙'), 48: ('第二回', '盛世天子'), 80: ('第三回', '十全武功'),
            112: ('第四回', '文治盖章'), 144: ('第五回', '盛极而衰')}

CARDS = [
    C(0, 2, 'hook', 'num', num='八十九岁', line='最长寿的皇帝', art=art_q_hook_old),
    C(2, 4, 'hook', 'num', num='六十年', line='又当三年太上皇', art=art_q_hook_two_thrones),
    C(4, 6, 'hook', 'num', num='四万首诗', line='一首也没流传', art=art_q_hook_poems),
    C(6, 8, 'hook', 'num', num='盛世巅峰', line='也是衰落起点', art=art_q_hook_sun),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 天选之孙
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'night', 'card', year=1711, main='生于雍亲王府', sub='雍正第四子 · 名弘历', note='八月十三日 生于雍亲王府', art=art_q_moongate),
    C(22, 26, 'life', 'card', year=1722, main='牡丹台初见', sub='十二岁 · 被祖父康熙一眼看中', note='圆明园牡丹台 祖孙初见', art=art_q_peony),
    C(26, 30, 'war', 'card', year=1722, main='木兰遇熊', sub='猛熊扑来 · 少年镇定自若', note='是命贵重 福将过予', art=art_q_bear),
    C(30, 34, 'life', 'card', year=1723, main='上书房苦读', sub='名字已被父亲写进匾后', note='寅时入学 风雨无阻', art=art_q_study),
    C(34, 38, 'court', 'card', year=1733, main='封宝亲王', sub='二十三岁 · 晋封亲王', note='授和硕宝亲王', art=art_q_baoqin),
    C(38, 42, 'life', 'card', year=1727, main='结发富察氏', sub='少年夫妻 · 情深意笃', note='后性节俭 不喜华饰', art=art_q_couple),
    C(42, 46, 'death', 'card', year=1735, main='雍正驾崩', sub='一夜之间 · 龙椅空悬', note='八月二十三日 雍正崩', art=art_q_empty_robe),
    C(46, 48, 'court', 'card', year=1735, main='开匣宣诏', sub='正大光明匾后 · 写着弘历', art=art_q_openbox),
    # ---- 第二回 盛世天子
    C(48, 50, 'empire', 'chapter'),
    C(50, 54, 'empire', 'card', year=1735, main='二十五岁登基', sub='年号乾隆 · 天道昌隆', note='太和殿前 百官朝贺', art=art_q_plaza),
    C(54, 58, 'court', 'card', year=1736, main='宽严相济', sub='纠父之严 · 释放被囚宗室', note='治天下之道 贵得其中', art=art_q_release),
    C(58, 62, 'death', 'card', year=1748, main='孝贤皇后', sub='东巡途中 · 皇后病逝舟中', note='痛失贤后 作述悲赋', art=art_q_grief),
    C(62, 66, 'works', 'card', year=1747, main='圆明园西洋楼', sub='意大利画师设计 · 大水法喷泉', note='万园之园', art=art_q_fountain),
    C(66, 70, 'life', 'card', year=1751, main='六下江南', sub='粉墙黛瓦 · 小桥流水', note='六次南巡 耗费无数', art=art_q_jiangnan),
    C(70, 74, 'court', 'card', year=1760, main='御笔写诗', sub='一生写诗四万余首', note='几乎相当于全唐诗', art=art_q_poet),
    C(74, 80, 'empire', 'card', year=1761, main='万国来朝', sub='宫廷画师绘万国来朝图', note='四夷宾服 万邦来朝', art=art_q_envoys_scroll),
    # ---- 第三回 十全武功
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=1755, main='平定准噶尔', sub='百年边患 · 一朝荡平', note='天山北路 尽入版图', art=art_q_dzungar),
    C(86, 90, 'works', 'card', year=1759, main='平大小和卓', sub='平定回部 · 天山南路归一', note='兵至喀什噶尔', art=art_q_oasis),
    C(90, 94, 'works', 'card', year=1760, main='故土新归', sub='命名新疆 · 设伊犁将军', note='故土新归 是为新疆', art=art_q_xinjiang),
    C(94, 96, 'war', 'card', year=1776, main='两征金川', sub='碉楼林立 · 耗银七千万两', art=art_q_jinchuan),
    C(96, 98, 'war', 'card', year=1769, main='征缅', sub='瘴疠横行 · 四征而和', art=art_q_burma),
    C(98, 100, 'works', 'card', year=1789, main='出兵安南', sub='富良江上 · 得失参半', art=art_q_annam),
    C(100, 102, 'war', 'card', year=1792, main='远征廓尔喀', sub='翻越喜马拉雅', art=art_q_gurkha),
    C(102, 104, 'war', 'card', year=1788, main='平林爽文', sub='渡海平定台湾民变', art=art_q_taiwan),
    C(104, 112, 'war', 'ten'),
    # ---- 第四回 文治盖章
    C(112, 114, 'court', 'chapter'),
    C(114, 118, 'empire', 'card', year=1773, main='四库全书', sub='三千余种 · 七万九千余卷', note='开四库全书馆 历时十年', art=art_q_siku),
    C(118, 124, 'court', 'card', year=1746, main='盖章狂魔', sub='富春山居图 · 题跋盖章五十余处', note='每得名画 必题诗钤印', art=art_q_stamping),
    C(124, 128, 'night', 'card', year=1755, main='文字狱', sub='一字之差 · 满门获罪', note='一把心肠论浊清 加浊于国号之上', art=art_q_wenziyu),
    C(128, 132, 'fate', 'card', year=1774, main='禁毁书籍', sub='修书的同时 · 禁毁三千余种', note='寓禁于征', art=art_q_redact),
    C(132, 136, 'court', 'card', year=1776, main='宠信权臣', sub='和珅一路高升 · 富可敌国', note='和珅 二十余年 权倾朝野', art=art_q_heshen),
    C(136, 140, 'life', 'card', year=1790, main='人口三亿', sub='玉米番薯 · 人口暴增', note='乾隆末年 人口突破三亿', art=art_q_population),
    C(140, 144, 'empire', 'card', year=1790, main='八旬万寿', sub='徽班进京 · 京剧由此而生', note='四大徽班 入京祝寿', art=art_q_opera),
    # ---- 第五回 盛极而衰
    C(144, 146, 'fate', 'chapter'),
    C(146, 154, 'works', 'card', year=1793, main='马戛尔尼', sub='英国使团来华 · 带来了整个世界', note='天朝物产丰盈 无所不有 原不藉外夷货物以通有无', art=art_q_macartney),
    C(154, 158, 'court', 'card', year=1795, main='禅位嘉庆', sub='不敢超过祖父 · 却不肯交出大权', note='归政仍训政', art=art_q_abdicate),
    C(158, 162, 'war', 'card', year=1796, main='白莲教起义', sub='五省烽烟 · 盛世裂开缝隙', note='官逼民反', art=art_q_white_lotus),
    C(162, 166, 'death', 'card', year=1799, main='崩于养心殿', sub='享年八十九岁', note='正月初三 太上皇崩', art=art_q_snow_palace),
    C(166, 170, 'fate', 'card', year=1799, main='巨贪倒台', sub='和珅被赐死 · 抄家所得惊人', note='和珅跌倒 嘉庆吃饱', art=art_q_fall_he),
    C(170, 999, 'end', 'end'),
]

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
for mod in (L, Wd, Tz, Z, St, M, K, Y):
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
for mod in (G, L, Wd, Tz, Z, St, M, K, Y):
    mod.year_at = year_at

def year_line(cv, t, year, start):
    yr = int(round(year_at(t))) if t >= bt(16) else year
    im = text_img('公元' + cn_year(yr) + '年', SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=TURQ + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('爱新觉罗 · 弘历', SERIF, 46, TURQ, 'Bold', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '乾隆', BRUSH, 220, INK, W / 2, 450, t, s0, stagger=0.1, seed=77)
    fx.flush(cv)
    stamp(cv, seal('乾隆御览之宝', 40), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1711 — 1799', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '好大喜功？', BRUSH, 120, INK, W / 2, 420, t, s0, stagger=0.07, seed=5)
    chars_in(cv, fx, '十全盛世？', BRUSH, 120, TURQ, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    landscape_scroll(A, 140, 560, 800, 400, clamp(u / 0.6))
    A.flush(cv, alpha=clamp(u / 0.6) * 0.3)
    fx = Art()
    chars_in(cv, fx, '十全老人', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('古稀天子', 52), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('他把大清带到了巅峰', SERIF, 50, DIM, 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('也把危机留给了后人', SERIF, 52, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '若他接纳世界', BRUSH, 100, TURQ, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('历史会改写吗？评论区聊聊', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=TURQ + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 245, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=PINK + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 成吉思汗', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, ten=scene_ten, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第玖集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 560, 170, 1, 1)
    if t < bt(8):
        q = text_img('最长寿的皇帝 · 他的盛世有多盛？', SERIF, 40, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 300, 335, W / 2 + 300, 335), fill=TURQ + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, TURQ, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=TURQ + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=PINK + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(int(round(yr - BORN + 1))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=TURQ + (255,))
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
