# 千古人物志 · 第拾陆集 · 戚继光 —— 长版（93.75 秒，五回章回体）
# 沿用系列引擎（同一音乐网格与动效，无跳动圆圈，墨色最后绘制）。每一幕画面均为本集新画，不重复。
# 本集特色：海防 —— 海蓝铁锈 · 鸳鸯阵章回卡（每回阵中多站一人）· 锚链边角
#          · 八拍「鸳鸯阵」 · 台州九战九捷九印回顾 · 八拍「空心敌台」
import math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import render_wentianxiang as Wx     # engine + helpers (ink layers drawn last)
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
from render_kangxi import rect, lantern, cannon
from render_songtaizu import tent
from render_mingtaizu import big_ship
from render_yuefei import cn_year

F.RIPPLE = False

BORN, DIED = 1528, 1588
END_BEAT = 170
SEA = (34, 86, 120)                 # 海蓝
RUST = (150, 76, 40)                # 铁锈
S.LAYERS.append(('sea', SEA, 0.80, 1.3))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

# ================================================================ episode look
WM = dict(hook='戚', life='光', court='兵', night='夜', war='戰', empire='明', works='海', fate='平', death='归', end='戚')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'court', 'end', 'empire', 'works'):
    G.THEMES[k]['part'] = 'ash'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['empire']['sun'] = (RUST, 250, (W * 0.5, 820))
G.THEMES['works']['sun'] = (SEA, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHU, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (36, 46, 58), 'death': (58, 60, 64), 'war': (100, 60, 44), 'works': (50, 80, 104)}
def draw_background(t, theme):
    """海防: sea-blue ranges over a misty coast."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(150, 170, 186), (98, 128, 150), MTN_COL.get(theme, (60, 92, 118))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 1.5))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """锚链: a chain of links ending in a small anchor at each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = SEA + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        for k in range(6):
            cx = x + sx * (14 + k * 22)
            d.ellipse((cx - 10, y - 6, cx + 10, y + 6), outline=col, width=3)
            cy = y + sy * (14 + k * 22)
            d.ellipse((x - 6, cy - 10, x + 6, cy + 10), outline=col, width=3)
        ax, ay = x + sx * 40, y + sy * 40
        d.line((ax, ay - 14, ax, ay + 14), fill=RUST + (230,), width=4)
        d.arc((ax - 14, ay - 4, ax + 14, ay + 20), 0, 180, fill=RUST + (230,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def ming_soldier(A, x, y, h, dir=1, layer='ink', weapon='spear', **kw):
    """明军: helmet with knob; weapon spear / langxian (狼筅) / shield."""
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, spear=(weapon == 'spear'), **kw)
    if weapon == 'langxian' and hand:
        hx, hy = hand
        tip = (hx + dir * 0.9 * h, hy - 0.5 * h)
        A.d[layer].line((hx - dir * 0.2 * h, hy + 0.1 * h, tip[0], tip[1]), fill=255, width=max(3, int(0.03 * h)))
        for j in range(6):
            f = 0.55 + j * 0.08
            bx, by = lerp(hx, tip[0], f), lerp(hy, tip[1], f)
            A.d[layer].line((bx, by, bx + dir * 0.08 * h, by - 0.12 * h), fill=255, width=2)
            A.d[layer].line((bx, by, bx - dir * 0.02 * h, by - 0.14 * h), fill=255, width=2)
    if weapon == 'shield' and hand:
        hx, hy = hand
        A.d['mid'].ellipse((hx - 0.12 * h, hy - 0.16 * h, hx + 0.12 * h, hy + 0.16 * h), fill=255)
        A.d[layer].ellipse((hx - 0.12 * h, hy - 0.16 * h, hx + 0.12 * h, hy + 0.16 * h), outline=255, width=3)
    return hand

def wokou(A, x, y, h, dir=-1, layer='mid', **kw):
    """倭寇: bare-headed, long curved blade."""
    hand = person(A, x, y, h, dir=dir, robe=False, hat='knot', layer=layer, **kw)
    if hand:
        hx, hy = hand
        pts = [(hx + dir * f * 0.5 * h, hy - f * 0.45 * h + 0.06 * h * math.sin(f * 3)) for f in np.linspace(0, 1, 8)]
        A.d[layer].line(pts, fill=255, width=max(3, int(0.025 * h)))
    return hand

def qi(A, x, y, h, dir=1, layer='ink', **kw):
    """戚继光: helmet with red tassel, sword at side."""
    hand = person(A, x, y, h, dir=dir, robe=kw.pop('robe', False), hat='helmet', layer=layer, **kw)
    A.d['red'].line((x, y - 0.99 * h, x - dir * 0.1 * h, y - 1.1 * h), fill=255, width=max(3, int(0.03 * h)))
    return hand

def wo_ship(A, x, y, s, t, layer='mid', burn=0.0):
    bob = 6 * math.sin(t * 2 + x * 0.01)
    A.d[layer].polygon([(x - s, y - 20 + bob), (x + s, y - 30 + bob), (x + s * 0.8, y + 30 + bob), (x - s * 0.8, y + 30 + bob)], fill=255)
    A.d[layer].line((x, y - 20 + bob, x, y - 2.4 * s + bob), fill=255, width=5)
    A.d['wash'].polygon([(x + 4, y - 2.3 * s + bob), (x + 0.9 * s, y - 2.1 * s + bob), (x + 0.8 * s, y - 0.6 * s + bob), (x + 4, y - 0.5 * s + bob)], fill=255)
    for k in range(4):
        yy = y - 2.1 * s + k * 0.4 * s + bob
        A.d[layer].line((x + 4, yy, x + 0.85 * s, yy + 6), fill=200, width=2)
    if burn > 0:
        flames(A, x, y - 20 + bob, s * 1.6, 220 * burn, t + x * 0.01, n=5, seed=int(x), smoke=True)

def watchtower(A, x, base, w, h, layer='ink', rise=1.0):
    top = base - h * rise
    A.d[layer].rectangle((x - w / 2, top, x + w / 2, base), fill=255)
    for k in range(int(w // 36)):
        A.d[layer].rectangle((x - w / 2 + k * 36, top - 24, x - w / 2 + k * 36 + 22, top), fill=255)
    if rise > 0.6:
        for j in range(2):
            for k in range(3):
                wx = x - w / 2 + 18 + k * (w - 36) / 2
                A.d['wash'].rectangle((wx - 10, top + 40 + j * 70, wx + 10, top + 76 + j * 70), fill=0)
    return top

YUANYANG = [('牌', 'shield'), ('牌', 'shield'), ('筅', 'langxian'), ('筅', 'langxian'), ('枪', 'spear'), ('枪', 'spear'),
            ('枪', 'spear'), ('枪', 'spear'), ('叉', 'spear'), ('叉', 'spear'), ('长', 'spear'), ('火', 'spear')]
def formation(A, cx, base, n, t, s=110, layer='ink'):
    """鸳鸯阵: a captain in front, then two columns of soldiers (shield, langxian, spear, trident)."""
    qi(A, cx, base - 3 * 0.7 * s, s * 0.9, dir=1, arm=60, layer=layer)
    for i in range(min(n, 10)):
        col = i % 2; row = i // 2
        x = cx - 120 + col * 240 - row * 12
        y = base - row * 0.55 * s
        w = ['shield', 'langxian', 'spear', 'spear', 'spear'][row]
        ming_soldier(A, x, y, s * (1 - row * 0.06), dir=1, weapon=w, arm=60, layer=layer if row < 2 else 'mid')

# ================================================================ chapter card
CH_N = {16: 2, 48: 4, 80: 6, 112: 8, 144: 10}
def art_formation_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = int(CH_N.get(kb, 4) * ease_out(clamp(u / 0.6))) + 1
    formation(A, 540, 1160, n, t, s=120)
    for k in range(3):
        y = 1330 + k * 46
        x = (t * 90 * (1 + 0.3 * k) + k * 330) % (W + 600) - 400
        A.d['wash'].line((x, y, x + 360, y), fill=255, width=20)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_formation_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SEA, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_formation(A, cv, t, u):
    ground(A, GROUND)
    formation(A, 380, GROUND, 10, t, s=110)
    for k in range(3):
        wokou(A, lerp(1100, 820, ease_out(u / P)) + k * 80, GROUND, 170, dir=-1, ph=t * 10 + k, arm=100, layer='mid')

def art_q_hook_nine(A, cv, t, u):
    A.flush(cv)
    for i in range(int(clamp(u / (1.6 * P)) * 9) + 1):
        x = 200 + (i % 3) * 340; y = 860 + (i // 3) * 170
        stamp(cv, seal('捷', 50), x, y, t, t - u + i * 0.1, rot=(i % 3 - 1) * 5)

def art_q_hook_wall(A, cv, t, u):
    pts = [(x, 1200 - 160 * math.sin(x * 0.006 + 1)) for x in range(60, W - 59, 10)]
    A.d['mid'].polygon(pts + [(W - 60, GROUND), (60, GROUND)], fill=200)
    A.d['ink'].line(pts, fill=255, width=12)
    for i in range(int(clamp(u / (1.6 * P)) * 6) + 1):
        x = 140 + i * 160
        watchtower(A, x, int(1200 - 160 * math.sin(x * 0.006 + 1)), 60, 100, layer='ink')

def art_q_hook_poor(A, cv, t, u):
    for k in range(30):
        q = (t * 0.3 + k / 30) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    A.d['mid'].rectangle((600, 1150, 900, GROUND), fill=255)
    A.d['mid'].polygon([(570, 1150), (930, 1150), (750, 1060)], fill=255)
    qi(A, 360, GROUND, 240, dir=1, robe=True, bow=30, arm=20, layer='ink')
    ground(A, GROUND)

# ================================================================ 第一回 将门之子
def art_q_birth(A, cv, t, u):
    A.d['sea'].rectangle((60, 1250, W - 60, 1380), fill=150)
    waves(A, 1260, t, rows=3, amp=8, speed=1.5)
    city_wall(A, 120, 760, 1180, gate_x=440, label='登州', layer='mid')
    A.flush(cv)
    stamp(cv, seal('将门', 54), 860, 960, t, t - u + P)

def art_q_father(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 290, dir=-1, robe=True, hat='helmet', arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 380, GROUND, 180, dir=1, robe=False, hat='knot', kneel=True, bow=20, arm=70, layer='ink')
    A.d['ink'].rectangle((470, GROUND - 120, 530, GROUND - 90), fill=255)
    A.flush(cv)
    type_in(cv, text_img('将门之子 不可忘本', BRUSH, 60, INK), W / 2, 880, t, t - u + P, 0.5)

def art_q_shoes(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 290, dir=-1, robe=True, hat='helmet', arm=lerp(30, 120, ease_out((u - P) / 0.3)), layer='ink')
    person(A, 400, GROUND, 190, dir=1, robe=False, hat='knot', bow=30, arm=20, layer='ink')
    sx = 420
    A.d['sea'].polygon([(sx - 30, GROUND - 6), (sx + 40, GROUND - 6), (sx + 50, GROUND - 24), (sx - 20, GROUND - 28)], fill=255)
    A.flush(cv)
    if u > P:
        stamp(cv, seal('丝履', 50, INK), 420, 960, t, t - u + P)

def art_q_succeed(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, robe=True, hat='crown', arm=60, layer='mid')
    qi(A, 380, GROUND, 250, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('指挥佥事', 44), 380, 940, t, t - u + P, rot=-5)

def art_q_poem(A, cv, t, u):
    A.d['sea'].rectangle((60, 1250, W - 60, 1380), fill=150)
    waves(A, 1260, t, rows=3, amp=10, speed=2)
    A.d['mid'].polygon([(60, 1250), (60, 1100), (360, 1130), (440, 1250)], fill=220)
    qi(A, 260, 1110, 170, dir=1, robe=True, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('封侯非我意', BRUSH, 80, INK, vertical=True), 760, 1000, t, t - u + 0.5 * P, 0.6)
    type_in(cv, text_img('但愿海波平', BRUSH, 80, ZHU, vertical=True), 640, 1000, t, t - u + 2 * P, 0.6)

def art_q_wokou(A, cv, t, u):
    A.d['sea'].rectangle((60, 1220, W - 60, 1380), fill=150)
    waves(A, 1230, t, rows=3, amp=10, speed=2)
    for k, x in enumerate((780, 960)):
        wo_ship(A, x, 1250, 70, t, layer='mid')
    for k in range(4):
        x = lerp(820, 420, ease_out((u - 0.3 * k) / (2 * P))) - k * 50
        wokou(A, x, 1220, 150, dir=-1, ph=t * 10 + k, arm=110, layer='ink')
    A.d['mid'].rectangle((120, 1100, 300, 1220), fill=255)
    A.d['mid'].polygon([(100, 1100), (320, 1100), (210, 1040)], fill=255)
    if u > 2 * P:
        flames(A, 210, 1100, 160, 140 * ease_out((u - 2 * P) / 0.4), t, n=4, seed=3, smoke=True)

def art_q_shandong(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        watchtower(A, x, GROUND - 40, 120, 220, layer='mid')
        A.flush(cv) if False else None
    ground(A, GROUND)
    qi(A, 540, GROUND, 240, dir=1, arm=lerp(40, 150, ease_out(u / P)), layer='ink')
    for k in range(3):
        flames(A, 220 + k * 320, GROUND - 290, 40, 60 * clamp((u - k * 0.3) / 0.4), t + k, n=2, seed=10 + k, smoke=True)

def art_q_zhejiang(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(-100, 600, ease_out(u / (3 * P)))
    rider(A, x, GROUND, 230, 1, t * 8, layer='ink')
    for k in range(3):
        ming_soldier(A, x - 260 - k * 100, GROUND, 150, dir=1, weapon='spear', ph=t * 7 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('调任浙江', 46), 860, 940, t, t - u + P, rot=5)

# ================================================================ 第二回 戚家军
def art_q_old_army(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        ming_soldier(A, 200 + k * 140, GROUND, 170, dir=-1 if u > P else 1, weapon='spear', ph=t * 10 + k if u > P else None,
                     arm=120, layer='mid')
    for k in range(2):
        wokou(A, lerp(1100, 860, ease_out(u / P)) + k * 80, GROUND, 170, dir=-1, ph=t * 10 + k, arm=110, layer='ink')
    A.flush(cv)
    if u > 1.5 * P:
        stamp(cv, seal('一触即溃', 44, INK), 540, 940, t, t - u + 1.5 * P)

def art_q_yiwu(A, cv, t, u):
    for k, (x, h) in enumerate(((200, 460), (540, 560), (880, 480))):
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - h), (x + 260, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(6):
        x = walk_x(1100 + k * 90, 300 + k * 110, u, 3 * P)
        person(A, x, GROUND, 170, dir=-1, robe=False, hat='knot', ph=t * 6 + k, arm=150 if k % 2 else 20, layer='ink' if k % 2 else 'mid')
    A.flush(cv)
    stamp(cv, seal('义乌矿工', 44), 300, 940, t, t - u + P, rot=-5)

def art_q_brawl(A, cv, t, u):
    ground(A, GROUND)
    for i in range(3):
        for j, side in enumerate((-1, 1)):
            x = 280 + i * 260 + side * 50
            person(A, x, GROUND, 180, dir=-side, robe=False, hat='knot', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 8 + i + j)), layer='ink' if j else 'mid')
    for k in range(6):
        q = ((t * 0.7 + k / 6) % 1)
        A.d['wash'].ellipse((200 + k * 130 - 30, GROUND - 40 - q * 60, 200 + k * 130 + 30, GROUND - q * 60), fill=int(160 * (1 - q)))
    A.flush(cv)
    type_in(cv, text_img('械斗数万人 · 敢死不退', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.4)

def art_q_yuanyang(A, cv, t, u):
    """8-beat set piece: the 12-man duck formation assembles soldier by soldier, then breaks a wokou charge."""
    ph = u / P
    ground(A, GROUND)
    n = int(clamp(u / (4 * P)) * 10) + 1
    formation(A, 360, GROUND, n, t, s=120)
    if ph >= 4:
        v = u - 4 * P
        for k in range(4):
            x = lerp(1150, 640, ease_out(v / (1.5 * P))) + k * 90
            fall = 80 * ease_out((v - 1.5 * P - k * 0.1) / 0.3) if v > 1.5 * P else 0
            wokou(A, x, GROUND, 160, dir=-1, ph=t * 10 + k if fall == 0 else None, fall=-fall, arm=110, layer='mid')
    A.flush(cv)
    labels = [('牌', 240, 1250), ('筅', 480, 1180), ('枪', 240, 1120), ('叉', 480, 1060)]
    for i, (ch, x, y) in enumerate(labels):
        if u > (0.5 + i) * P:
            stamp(cv, seal(ch, 40, ZHU if i % 2 == 0 else INK), x, y - 260, t, t - u + (0.5 + i) * P)
    if ph >= 6.5:
        stamp(cv, seal('鸳鸯阵', 50), 860, 900, t, t - u + 6.5 * P, rot=6)

def art_q_langxian(A, cv, t, u):
    ground(A, GROUND)
    ming_soldier(A, 360, GROUND, 300, dir=1, weapon='langxian', arm=lerp(30, 70, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    wokou(A, 820, GROUND, 230, dir=-1, arm=lerp(110, 70, 0.5 + 0.5 * math.sin(t * 4)), bow=lerp(0, 20, clamp(u / (2 * P))), layer='mid')
    A.flush(cv)
    stamp(cv, seal('狼筅', 54), 300, 920, t, t - u + P, rot=-5)

def art_q_book(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    qi(A, 540, GROUND, 230, dir=1, robe=True, kneel=True, bow=20, arm=lerp(80, 105, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    for k in range(int(clamp(u / (2 * P)) * 6)):
        A.d['sea'].rectangle((640, 1236 - k * 20, 760, 1252 - k * 20), fill=255)
    A.flush(cv)
    type_in(cv, text_img('纪效新书', BRUSH, 90, SEA), W / 2, 900, t, t - u + P, 0.4)

def art_q_drill(A, cv, t, u):
    ground(A, GROUND)
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.15)
    for r_ in range(3):
        for k in range(7):
            x = 160 + k * 120 + (r_ % 2) * 50; y = GROUND - r_ * 60
            ming_soldier(A, x, y, 130 - r_ * 12, dir=1, weapon='spear', arm=lerp(30, 90, hit), bow=10 * hit, layer='ink' if r_ == 0 else 'mid')
    flag(A, 980, GROUND, 400, t, w=110)

def art_q_army_name(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        flag(A, 90 + k * 130, GROUND, 300 * ease_out((u - k * 0.08) / 0.4), t + k, w=80)
    A.flush(cv)
    stamp(cv, seal('戚', 120), 540, 960, t, t - u + 0.5)

# ================================================================ 第三回 九战九捷
NINE = ['新河', '花街', '上峰岭', '长沙', '藤岭', '大田', '上峰', '仙居', '海门']
def scene_nine(cv, t, c, k):
    s0 = bt(c[0]); gather_t = bt(c[0] + 6)
    gather = t >= gather_t
    A = Art(); beat_fx(A, t)
    pts = []
    for j in range(48):
        a = 2 * math.pi * j / 48
        r = 360 + 40 * math.sin(a * 3 + 1) + 22 * math.sin(a * 7)
        pts.append((540 + r * math.cos(a), 1040 + r * math.sin(a) * 0.72))
    A.d['sea'].polygon(pts, fill=70); A.d['ink'].line(pts + [pts[0]], fill=255, width=4)
    A.flush(cv)
    n = min(9, int((t - s0) / (6 * P / 9)) + 1) if not gather else 9
    for i in range(n):
        a = -math.pi / 2 + i * 2 * math.pi / 9
        x, y = 540 + 270 * math.cos(a), 1040 + 200 * math.sin(a)
        stamp(cv, seal(NINE[i], 34 if len(NINE[i]) > 2 else 42, ZHU), x, y, t, s0 + i * 6 * P / 9)
    if not gather:
        paste(cv, text_img(f'第{cn_num(n)}捷', SERIF, 60, ZHU, 'Black', bleed=False), W / 2, 1470, 1, 1)
    else:
        stamp(cv, seal('台州', 80), 540, 1040, t, gather_t)
    fx = Art()
    if not gather:
        chars_in(cv, fx, '台州大捷', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=104)
    else:
        chars_in(cv, fx, '九战九捷', BRUSH, 170, ZHU, W / 2, 440, t, gather_t, stagger=0.08, seed=110)
        chars_in(cv, fx, '歼倭寇五千余', BRUSH, 110, INK, W / 2, 1470, t, bt(c[0] + 7), stagger=0.06, seed=111)
    fx.flush(cv)

def art_q_xinhe(A, cv, t, u):
    city_wall(A, 560, W - 60, 1140, gate_x=800, label='新河', open_=0.0)
    for k in range(5):
        person(A, 620 + k * 70, 1130, 80, dir=-1, female=k % 2 == 0, robe=True, hat='knot', arm=lerp(30, 150, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    ground(A, GROUND)
    for k in range(3):
        wokou(A, 200 + k * 100, GROUND, 160, dir=1, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('妇孺守城', 44), 800, 860, t, t - u + P, rot=5)

def art_q_march(A, cv, t, u):
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    ground(A, GROUND)
    for k in range(7):
        x = (t * 160 + k * 160) % (W + 300) - 150
        ming_soldier(A, x, GROUND - (k % 2) * 10, 160, dir=1, weapon='spear' if k % 3 else 'langxian', ph=t * 10 + k, arm=40, layer='ink' if k % 2 else 'mid')
    A.flush(cv)
    stamp(cv, seal('日夜兼程', 44, INK), 860, 940, t, t - u + P, rot=5)

def art_q_victory(A, cv, t, u):
    city_wall(A, 60, W - 60, 1140, gate_x=540, label='台州', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 140, dir=1 if k < 3 else -1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    qi(A, 540, GROUND, 240, dir=1, arm=60, layer='ink')

# ================================================================ 第四回 援闽
def art_q_hengyu(A, cv, t, u):
    A.d['mid'].rectangle((60, 1200, W - 60, GROUND + 20), fill=180)
    for k in range(6):
        pts = [(x, 1220 + k * 30 + 6 * math.sin(x * 0.02 + k)) for x in range(60, W - 59, 14)]
        A.d['ink'].line(pts, fill=120, width=3)
    A.d['mid'].polygon([(760, 1200), (860, 1060), (1020, 1200)], fill=255)
    for k in range(5):
        x = lerp(80, 620, ease_out(u / (3 * P))) - k * 90
        ming_soldier(A, x, 1230 + (k % 2) * 20, 140, dir=1, weapon='spear', ph=t * 4 + k, arm=40, layer='ink')
        A.d['gold'].polygon([(x - 50, 1240 + (k % 2) * 20), (x + 50, 1240 + (k % 2) * 20), (x + 40, 1256 + (k % 2) * 20), (x - 40, 1256 + (k % 2) * 20)], fill=255)
    A.flush(cv)
    stamp(cv, seal('铺草过滩', 44), 300, 940, t, t - u + P, rot=-5)

def art_q_pinghai(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='平海', open_=ease_out((u - 1.5 * P) / 0.5))
    ground(A, GROUND)
    for k in range(5):
        ming_soldier(A, lerp(-100, 520, ease_out(u / (2 * P))) - k * 90, GROUND, 160, dir=1, weapon='spear', ph=t * 9 + k, layer='ink')
    for k in range(4):
        flames(A, 440 + k * 140, 1110, 60, 70, t + k, n=2, seed=40 + k, smoke=True)

def art_q_fujian_people(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        person(A, 120 + k * 80, GROUND, 150, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 2 + k)), layer='mid')
    qi(A, 760, GROUND, 250, dir=-1, arm=60, layer='ink')
    A.d['red'].rectangle((610, GROUND - 180, 660, GROUND - 130), fill=255)
    A.flush(cv)
    type_in(cv, text_img('光饼', BRUSH, 80, ZHU), 620, 900, t, t - u + P, 0.4)

def art_q_xianyou(A, cv, t, u):
    city_wall(A, 360, W - 60, 1120, gate_x=700, label='仙游')
    ground(A, GROUND)
    for k in range(8):
        a = math.pi * (k / 7)
        x = 700 - 380 * math.cos(a)
        wokou(A, x, GROUND, 120, dir=1 if x < 700 else -1, arm=100, fall=-80 * ease_out((u - P - k * 0.08) / 0.3) if u > P else 0, layer='mid')
    for k in range(3):
        ming_soldier(A, lerp(-100, 220, ease_out(u / P)) - k * 80, GROUND, 170, dir=1, weapon='spear', ph=t * 10 + k, layer='ink')

def art_q_peace(A, cv, t, u):
    A.d['sea'].rectangle((60, 1200, W - 60, 1380), fill=140)
    waves(A, 1210, t, rows=3, amp=4, speed=0.8)
    sun(cv, 540, lerp(1250, 960, ease_out(u / (3 * P))), 200, ZHU, 140)
    for k in range(3):
        boat(A, 240 + k * 300, 1240 + (k % 2) * 20, 100, t + k, sail=True)
    A.flush(cv)
    type_in(cv, text_img('海波平', BRUSH, 110, INK), W / 2, 880, t, t - u + 1.5 * P, 0.5)

def art_q_hu(A, cv, t, u):
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 760, GROUND, 250, dir=-1, robe=True, hat='crown', kneel=True, bow=10, arm=60, layer='ink')
    qi(A, 320, GROUND, 250, dir=1, kneel=True, bow=20, arm=80, layer='ink')
    A.flush(cv)
    stamp(cv, seal('胡宗宪', 46, INK), 760, 940, t, t - u + 0.3)

# ================================================================ 第五回 北守蓟镇
def art_q_jizhen(A, cv, t, u):
    for k in range(34):
        q = (t * 0.3 + k / 34) % 1
        x = 80 + (k * 37) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
    ground(A, GROUND)
    x = lerp(100, 700, ease_out(u / (3 * P)))
    rider(A, x, GROUND, 220, 1, t * 6, layer='ink')
    for k in range(4):
        ming_soldier(A, x - 240 - k * 100, GROUND, 150, dir=1, weapon='spear', ph=t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('北调蓟镇', 44), 860, 900, t, t - u + P, rot=5)

def art_q_towers(A, cv, t, u):
    """8-beat set piece: hollow watchtowers rise one after another along the ridge."""
    ph = u / P
    pts = [(x, 1180 - 180 * math.sin(x * 0.005 + 0.6) - 40 * math.sin(x * 0.02)) for x in range(60, W - 59, 8)]
    A.d['mid'].polygon(pts + [(W - 60, GROUND), (60, GROUND)], fill=200)
    A.d['ink'].line(pts, fill=255, width=14)
    for i in range(6):
        x = 120 + i * 168
        y = 1180 - 180 * math.sin(x * 0.005 + 0.6) - 40 * math.sin(x * 0.02)
        rise = ease_out((u - i * 1.1 * P) / 0.6)
        if rise > 0:
            watchtower(A, x, y + 10, 90, 150, layer='ink', rise=rise)
    A.flush(cv)
    n = min(1200, int(clamp(u / (6.5 * P)) * 1200))
    paste(cv, text_img(f'{n}座', SERIF, 60, SEA, 'Black', bleed=False), W / 2, 1460, 1, 1)
    if ph >= 7:
        stamp(cv, seal('空心敌台', 46), 860, 860, t, t - u + 7 * P, rot=6)

def art_q_cannon(A, cv, t, u):
    watchtower(A, 540, GROUND, 340, 360, layer='ink')
    kk = (t - G.B0) / P
    for i, x in enumerate((420, 660)):
        f = ((kk + i * 0.5) % 1)
        cannon(A, x, GROUND - 330, 70, -1 if i == 0 else 1, fire=f if f < 0.6 else 0)
    ground(A, GROUND)
    for k in range(4):
        rider(A, (t * 200 + k * 260) % (W + 300) - 150, GROUND, 100, 1, t * 12 + k, layer='wash')

def art_q_mongol(A, cv, t, u):
    ground(A, GROUND)
    watchtower(A, 220, GROUND, 160, 300, layer='ink')
    for k in range(5):
        rider(A, lerp(600, 1200, ease_out((u - P) / (2 * P))) + k * 90, GROUND - (k % 2) * 10, 110, 1, t * 12 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('十六年', 54), 760, 900, t, t - u + P)
    type_in(cv, text_img('边境无战事', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 1460, t, t - u + 2 * P, 0.4)

def art_q_zhang(A, cv, t, u):
    A.d['wash'].ellipse((760, 640, 880, 760), fill=255)
    A.d['ink'].rectangle((300, 1250, 780, 1280), fill=255)
    for lx in (320, 740): A.d['ink'].rectangle((lx, 1280, lx + 18, GROUND), fill=255)
    person(A, 760, GROUND, 250, dir=-1, robe=True, hat='crown', kneel=True, bow=10, arm=60, layer='ink')
    qi(A, 320, GROUND, 250, dir=1, robe=True, kneel=True, bow=20, arm=80, layer='ink')
    lantern(A, 540, 1100, t, 0, size=20)
    A.flush(cv)
    stamp(cv, seal('张居正', 46, INK), 760, 940, t, t - u + 0.3)

def art_q_zhang_dies(A, cv, t, u):
    palace(A, 540, GROUND, 680, layer='mid')
    for k in range(40):
        q = (t * 1.0 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['mid'].line((x, y, x - 8, y + 36), fill=200, width=2)
    lt = clamp(1 - (u - P) / 0.6)
    A.d['wash'].rectangle((470, 1180, 610, 1280), fill=0)
    if lt > 0:
        A.d['yellow'].rectangle((470, 1180, 610, 1280), fill=int(160 * lt))
    A.flush(cv)
    stamp(cv, seal('靠山倒', 50, INK), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_q_guangdong(A, cv, t, u):
    for x in (160, 920):
        A.d['ink'].line((x, GROUND, x + 20, 1000), fill=255, width=10)
        for kk in range(6):
            a = math.radians(-160 + kk * 25)
            A.d['ink'].line((x + 20, 1000, x + 20 + 110 * math.cos(a), 1000 + 110 * math.sin(a) + 30), fill=255, width=5)
    ground(A, GROUND)
    x = lerp(800, 360, ease_out(u / (3 * P)))
    rider(A, x, GROUND, 200, -1, t * 4, layer='ink')
    A.flush(cv)
    stamp(cv, seal('调任广东', 44, INK), 300, 900, t, t - u + P, rot=-5)

def art_q_dismiss(A, cv, t, u):
    A.d['ink'].polygon([(560, GROUND), (980, GROUND), (940, 1260), (600, 1260)], fill=255)
    person(A, 770, 1260, 150, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out((u - 0.5) / 0.4)), layer='mid')
    qi(A, 380, GROUND, 250, dir=1, kneel=True, bow=40, arm=80, layer='ink')
    q = ease_out((u - P) / 0.5)
    A.d['ink'].chord((lerp(440, 300, q) - 40, lerp(GROUND - 270, GROUND - 40, q) - 20, lerp(440, 300, q) + 40, lerp(GROUND - 270, GROUND - 40, q) + 20), 180, 360, fill=255)
    A.flush(cv)
    stamp(cv, seal('罢官', 54, INK), 380, 940, t, t - u + 1.5 * P, rot=-5)

def art_q_home(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['mid'].rectangle((560, 1150, 900, GROUND), fill=255)
    A.d['mid'].polygon([(520, 1150), (940, 1150), (730, 1050)], fill=255)
    rect(A, 'wash', 680, 1220, 780, GROUND, fill=0)
    qi(A, 360, GROUND, 240, dir=1, robe=True, kneel=True, bow=30, arm=60, layer='ink')
    A.d['ink'].rectangle((440, GROUND - 40, 500, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('老妻弃 子不顾 · 贫病交加', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + P, 0.5)

def art_q_death(A, cv, t, u):
    for k in range(40):
        q = (t * 0.25 + k / 40) % 1
        x = 80 + (k * 23) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
    A.d['mid'].rectangle((300, 1160, 780, 1200), fill=255)
    lt = clamp(1 - (u - 1.5 * P) / 0.6)
    if lt > 0:
        lantern(A, 540, 1060, t, 0, size=int(20 * lt) + 2)
    for k in range(3):
        A.d['ink'].line((360 + k * 120, 1160, 360 + k * 120, GROUND), fill=255, width=8)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('寒冬腊月 · 年六十', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 1460, 1, clamp((u - P) / 0.3))

def art_q_temple(A, cv, t, u):
    palace(A, 540, 1240, 640, layer='mid')
    A.d['ink'].rectangle((400, 1000, 680, 1070), fill=255)
    A.d['ink'].text((420, 1008), '戚公祠', font=font(SERIF, 52, 'Black'), fill=0)
    A.d['wash'].rectangle((60, 1240, W - 60, GROUND + 20), fill=255)
    for k in range(4):
        person(A, 280 + k * 160, GROUND, 130, dir=1 if k < 2 else -1, kneel=True, bow=45, arm=60, female=k % 2 == 1, layer='ink')

def art_q_sea_legacy(A, cv, t, u):
    A.d['sea'].rectangle((60, 1150, W - 60, 1380), fill=150)
    waves(A, 1160, t, rows=5, amp=10, speed=1.5)
    fo = font(BRUSH, 380)
    p = ease_out(u / (1.5 * P))
    tmp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(tmp).text((540 - fo.getlength('平') / 2, 720), '平', font=fo, fill=255)
    fld = G.transition_field()
    a = np.asarray(tmp, np.float32) * np.clip((p * 1.3 - fld) / 0.08, 0, 1)
    m = Image.fromarray(a.astype(np.uint8))
    A.im['ink'].paste(m, (0, 0), m)

# ================================================================ list: 练兵四法
def art_q_l_select(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        ok = k % 2 == 0
        x = 160 + k * 150
        person(A, x, GROUND - (0 if ok else 0), 170, dir=1, robe=False, hat='knot', arm=40, layer='ink' if ok else 'wash')
    A.flush(cv)
    for k in range(3):
        stamp(cv, seal('选', 40), 160 + k * 300, 960, t, t - u + k * 0.2)

def art_q_l_drum(A, cv, t, u):
    kk = (t - G.B0) / P
    hit = math.exp(-((kk % 1) * P) / 0.12)
    A.d['red'].ellipse((380, 980, 700, 1200), fill=255)
    A.d['ink'].ellipse((380, 980, 700, 1200), outline=255, width=8)
    A.d['ink'].rectangle((380, 1090, 700, 1300), outline=255, width=6)
    for sx in (-1, 1):
        A.d['ink'].line((540 + sx * 60, 940 - 60 * hit, 540 + sx * 160, 860 - 40 * hit), fill=255, width=10)
    ground(A, GROUND)
    A.flush(cv)
    for k in range(4):
        r = 180 + 80 * hit + k * 40
        ImageDraw.Draw(cv).arc((540 - r, 1090 - r * 0.6, 540 + r, 1090 + r * 0.6), 200, 340, fill=INK + (int(120 * hit),), width=3)

def art_q_l_reward(A, cv, t, u):
    ground(A, GROUND)
    qi(A, 720, GROUND, 250, dir=-1, arm=lerp(30, 100, ease_out(u / P)), layer='ink')
    ming_soldier(A, 400, GROUND, 220, dir=1, weapon='spear', kneel=True, bow=30, arm=80, layer='ink')
    for k in range(int(clamp(u / P) * 5)):
        A.d['gold'].ellipse((560 + k * 30 - 14, GROUND - 160, 560 + k * 30 + 14, GROUND - 140), fill=255)
    A.flush(cv)
    stamp(cv, seal('赏罚分明', 44), 400, 900, t, t - u + P, rot=-5)

def art_q_l_rule(A, cv, t, u):
    p = ease_out(u / 0.6)
    A.d['mid'].rectangle((540 - 300 * p, 860, 540 + 300 * p, 1260), fill=200)
    A.d['ink'].rectangle((540 - 300 * p, 860, 540 + 300 * p, 1260), outline=255, width=6)
    A.flush(cv)
    for i, ln in enumerate(('临阵退缩者斩', '扰民者斩', '一人退 全队斩')):
        if u > 0.4 + i * 0.6:
            type_in(cv, text_img(ln, SERIF, 50, INK if i < 2 else ZHU, 'Black', bleed=False, spacing=4), 540, 940 + i * 100, t, t - u + 0.4 + i * 0.6, 0.4)

# ================================================================ script
CHAPTERS = {16: ('第一回', '将门之子'), 48: ('第二回', '戚家军'), 80: ('第三回', '九战九捷'),
            112: ('第四回', '援闽平倭'), 144: ('第五回', '北守蓟镇')}

CARDS = [
    C(0, 2, 'hook', 'num', num='鸳鸯阵', line='十二人一队', art=art_q_hook_formation),
    C(2, 4, 'hook', 'num', num='九战九捷', line='倭寇闻风丧胆', art=art_q_hook_nine),
    C(4, 6, 'hook', 'num', num='一千二百座', line='空心敌台', art=art_q_hook_wall),
    C(6, 8, 'hook', 'num', num='晚景凄凉', line='贫病而终', art=art_q_hook_poor),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1528, main='将门之后', sub='世袭登州卫 · 父戚景通', note='戚氏世袭登州卫指挥佥事', art=art_q_birth),
    C(22, 26, 'court', 'card', year=1538, main='严父教子', sub='父亲以兵法家训相授', note='将门之子 不可忘本', art=art_q_father),
    C(26, 30, 'life', 'card', year=1540, main='一双丝履', sub='穿了一双好鞋 · 被父亲痛斥', note='汝今衣丝履 他日必克扣军饷', art=art_q_shoes),
    C(30, 34, 'court', 'card', year=1544, main='十七袭职', sub='父亲病逝 · 承袭指挥佥事', note='年十七 嗣职', art=art_q_succeed),
    C(34, 38, 'works', 'card', year=1546, main='但愿海波平', sub='少年立志 · 题诗明心', note='韬钤深处', art=art_q_poem),
    C(38, 42, 'night', 'card', year=1553, main='倭寇横行', sub='东南沿海 · 烧杀抢掠', note='嘉靖大倭寇', art=art_q_wokou),
    C(42, 46, 'war', 'card', year=1553, main='山东备倭', sub='二十六岁 · 总督山东海防', note='管登州 文登 即墨三营', art=art_q_shandong),
    C(46, 48, 'war', 'card', year=1555, main='调任浙江', sub='倭患最烈之地', art=art_q_zhejiang),
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'death', 'card', year=1558, main='旧军不堪', sub='官兵见倭即溃', note='岑港之战 久攻不下', art=art_q_old_army),
    C(54, 58, 'war', 'card', year=1558, main='义乌械斗', sub='为争矿山 · 数万人相搏', note='他由此看中义乌人', art=art_q_brawl),
    C(58, 62, 'life', 'card', year=1559, main='招募义乌兵', sub='矿工农夫 · 朴实敢战', note='义乌之人 剽悍敢战', art=art_q_yiwu),
    C(62, 70, 'works', 'card', year=1559, main='鸳鸯阵', sub='十二人一队 · 长短相配 攻守兼备', note='牌筅枪叉 互为依托', art=art_q_yuanyang),
    C(70, 74, 'war', 'card', year=1559, main='狼筅', sub='毛竹留枝 · 专克倭刀', note='倭刀虽利 难近其身', art=art_q_langxian),
    C(74, 78, 'court', 'card', year=1560, main='纪效新书', sub='把练兵之法 · 写成兵书', note='纪其实效 法无陈迹', art=art_q_book),
    C(78, 80, 'empire', 'card', year=1560, main='戚家军', sub='四千精兵 · 名震东南', art=art_q_army_name),
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'night', 'card', year=1561, main='新河告急', sub='城中妇孺披甲守城', note='夫人王氏 率众登城', art=art_q_xinhe),
    C(86, 90, 'war', 'card', year=1561, main='疾行驰援', sub='一日一夜 · 奔袭百余里', note='倍道兼行', art=art_q_march),
    C(90, 98, 'works', 'nine'),
    C(98, 104, 'works', 'list', year=1561, items=['选兵', '号令', '赏罚', '军纪']),
    C(104, 112, 'empire', 'card', year=1561, main='台州大捷', sub='百姓夹道 · 迎戚家军', note='浙江倭患 自此渐平', art=art_q_victory),
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'war', 'card', year=1562, main='横屿', sub='倭巢四面泥滩 · 铺草而过', note='人持草一束 填壕而进', art=art_q_hengyu),
    C(118, 122, 'war', 'card', year=1563, main='平海卫', sub='收复平海 · 斩倭二千余', note='平海卫大捷', art=art_q_pinghai),
    C(122, 126, 'life', 'card', year=1563, main='光饼', sub='中间穿孔 · 串绳挂身当干粮', note='福建百姓 至今仍做', art=art_q_fujian_people),
    C(126, 130, 'war', 'card', year=1564, main='仙游之战', sub='解仙游之围 · 歼倭万余', note='闽中倭患 大体平定', art=art_q_xianyou),
    C(130, 134, 'court', 'card', year=1564, main='知遇之恩', sub='胡宗宪 谭纶 · 力荐重用', note='得遇明主 方显其才', art=art_q_hu),
    C(134, 144, 'works', 'card', year=1565, main='海波平', sub='东南倭患 · 基本平息', note='封侯非我意 但愿海波平', art=art_q_peace),
    C(144, 146, 'fate', 'chapter'),
    C(146, 148, 'war', 'card', year=1568, main='北调蓟镇', sub='镇守京师门户', art=art_q_jizhen),
    C(148, 156, 'works', 'card', year=1569, main='空心敌台', sub='沿长城修建敌台 · 驻兵储炮', note='三年 筑台一千二百余座', art=art_q_towers),
    C(156, 158, 'war', 'card', year=1571, main='火器守边', sub='台上设炮 · 骑兵难近', art=art_q_cannon),
    C(158, 160, 'empire', 'card', year=1580, main='十六年无战事', sub='蒙古骑兵 · 不敢犯边', art=art_q_mongol),
    C(160, 162, 'court', 'card', year=1580, main='张居正', sub='朝中首辅 · 一力支持', art=art_q_zhang),
    C(162, 164, 'death', 'card', year=1582, main='靠山倒下', sub='张居正病逝 · 遭清算', art=art_q_zhang_dies),
    C(164, 166, 'fate', 'card', year=1585, main='罢官归乡', sub='被劾罢职 · 回到登州', art=art_q_dismiss),
    C(166, 168, 'death', 'card', year=1588, main='病逝', sub='贫病交加 · 医药不备', art=art_q_death),
    C(168, 170, 'end', 'card', year=1588, main='戚公祠', sub='东南百姓 · 立祠纪念', art=art_q_temple),
    C(170, 999, 'end', 'end'),
]
# art_q_guangdong / art_q_home / art_q_sea_legacy are kept in the episode library

LIST_ART = [art_q_l_select, art_q_l_drum, art_q_l_reward, art_q_l_rule]
def scene_list(cv, t, c, k):
    i = min(3, int((k - c[0]) / 1.5))
    st = bt(c[0] + 1.5 * i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    L.year_line(cv, t, c[4]['year'], bt(c[0]))
    it = c[4]['items'][i]
    fx = Art()
    chars_in(cv, fx, '练兵' + it, BRUSH, 130, INK, W / 2, 440, t, st, stagger=0.05, seed=50 + i)
    fx.flush(cv)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            stamp(cv, seal('壹贰叁肆'[j], 36, SEA), x, 575, t, bt(c[0] + 1.5 * j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=SEA + (110,), width=2)

# ---------------------------------------------------------------- wire into the engine
L.CARDS = CARDS; G.CARDS = CARDS
ALL = (L, Wd, Tz, Z, St, M, K, Y, Q, Gh, Lb, Cc, Zg, Yf, Wx)
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
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=SEA + (220,), width=3)
L.year_line = year_line

def scene_title(cv, t, c, k):
    s0 = bt(c[0])
    def art(A, cv_, t_, u_):
        sun(cv_, 600, 1000, 250, SEA, 110)
        ground(A, 1440)
        qi(A, 470, 1440, 700, dir=1, arm=lerp(-5, 55, ease_out(u_ / (2 * P))), layer='ink')
    stage(cv, t, c, art)
    fx = Art()
    ink_in(cv, text_img('戚继光 · 字元敬', SERIF, 46, SEA, 'Black', bleed=False, spacing=8), W / 2, 300, t, s0)
    chars_in(cv, fx, '戚继光', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('武毅', 66), 880, 640, t, bt(c[0] + 2), rot=-5)
    type_in(cv, text_img('公元1528 — 1588', SERIF, 38, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 590, t, bt(c[0] + 2), 0.4)

def scene_question(cv, t, c, k):
    s0 = bt(c[0])
    stage(cv, t, c, c[4]['art'])
    fx = Art()
    chars_in(cv, fx, '明朝第一名将？', BRUSH, 110, SEA, W / 2, 420, t, s0, stagger=0.06, seed=5)
    chars_in(cv, fx, '依附权臣？', BRUSH, 120, INK, W / 2, 565, t, bt(c[0] + 1), stagger=0.07, seed=6)
    fx.flush(cv)
    type_in(cv, text_img('看完他的一生 · 你来评判', SERIF, 42, DIM, 'Bold', bleed=False, spacing=4), W / 2, 690, t, bt(c[0] + 2), 0.45)

END = bt(END_BEAT)
def scene_end(cv, t, c, k):
    u = t - END
    A = Art()
    art_q_sea_legacy(A, cv, t, u)
    A.flush(cv, alpha=clamp(u / 0.6) * 0.25)
    fx = Art()
    chars_in(cv, fx, '但愿海波平', BRUSH, 190, INK, W / 2, 760, t, END, stagger=0.09, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('元敬', 60), W / 2 + 380, 540, t, END + 0.45, rot=6)
    type_in(cv, text_img('平定倭患 守边十六年', SERIF, 48, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 960, t, END + 0.6, 0.4)
    type_in(cv, text_img('最后却在贫病中离开人世', SERIF, 52, INK, 'Bold', bleed=False, spacing=4), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '名将的结局', BRUSH, 100, SEA, W / 2, 1190, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('为何总是如此？评论区说说', SERIF, 42, DIM, 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh = 400 * pulse, 92 * pulse
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=SEA + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(250, 250, 255, a))
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=RUST + (230,), width=5)
        cv.alpha_composite(btn, (0, 1330))
        paste(cv, text_img('下集预告 · 郑和', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(title=scene_title, question=scene_question, chapter=scene_chapter, nine=scene_nine, list=scene_list, end=scene_end)

def draw_hud(canvas, t):
    paste(canvas, seal('千古', 34), 330, 170, 1, 1)
    paste(canvas, text_img('人物志 · 第拾陆集', SERIF, 40, INK, 'Bold', bleed=False, spacing=6), 570, 170, 1, 1)
    if t < bt(8):
        q = text_img('打得倭寇闻风丧胆 · 结局为何如此凄凉？', SERIF, 36, INK, 'Black', bleed=False, spacing=2)
        paste(canvas, q, W / 2, 290, 1, 1)
        ImageDraw.Draw(canvas).line((W / 2 - 340, 335, W / 2 + 340, 335), fill=SEA + (220,), width=3)
    cur = None
    for b, ch in CHAPTERS.items():
        if bt(b) <= t < bt(END_BEAT): cur = ch
    if cur:
        paste(canvas, text_img(f'{cur[0]} · {cur[1]}', SERIF, 30, SEA, 'Bold', bleed=False, spacing=4), W / 2, 228, 1, 0.95)
    if bt(16) - 0.15 <= t < bt(END_BEAT):
        a = clamp((t - (bt(16) - 0.15)) / 0.25)
        y = 1560; x0, x1 = 170, W - 170
        yr = year_at(t)
        p = clamp((yr - BORN) / (DIED - BORN))
        ov = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.line((x0, 80, x1, 80), fill=INK + (60,), width=3)
        xp = lerp(x0, x1, p)
        d.line((x0, 80, xp, 80), fill=SEA + (230,), width=6)
        d.ellipse((xp - 12, 68, xp + 12, 92), fill=ZHU + (255,))
        f = font(SERIF, 30, 'Medium')
        d.text((x0, 102), f'{BORN}年', font=f, fill=INK + (170,))
        d.text((x1 - f.getlength(f'{DIED}年'), 102), f'{DIED}年', font=f, fill=INK + (170,))
        lab = cn_num(max(1, int(round(yr - BORN)))) + '岁'
        fb = font(SERIF, 38, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 12), lab, font=fb, fill=SEA + (255,))
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
