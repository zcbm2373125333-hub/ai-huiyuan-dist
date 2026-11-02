"""千古人物志 · 第叁拾壹集 · 李白 (701–762)
Look: 青莲蓝紫 + 月白, 新月 corner borders, a moon chapter card that waxes chapter by chapter (new → crescent → half →
full) and ends as a moon reflected in water.
Set pieces: 8-beat 仗剑去国 (down the 三峡 under the 峨眉 moon), custom 8-beat scene 'jiangjin' (将进酒 lines pour out
with the wine), 6-beat 奉诏入京, 8-beat 力士脱靴 (legend), 6-beat 赐金放还, 6-beat 洛阳相遇, 8-beat 早发白帝.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_cailun as Cl          # engine + helpers (previous episode)
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
from render_wangyangming import desk, scroll, lamp, sitter
from render_quyuan import river
from render_simaqian import brush, bars
from render_wudi import camel

F.RIPPLE = False
LOTUS = (78, 92, 166)               # 青莲
MOON = (236, 220, 160)              # 月白
S.LAYERS.append(('lotus', LOTUS, 0.88, 1.0))
S.LAYERS.append(('moon', MOON, 0.92, 1.4))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='白', life='莲', court='唐', night='月', war='乱', empire='唐', works='诗', fate='酒', death='月', end='白')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court'):
    G.THEMES[k]['part'] = 'petal'
for k in ('empire',):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (MOON, 230, (W * 0.5, 820))
G.THEMES['fate']['sun'] = (MOON, 200, (W * 0.72, 760))
G.THEMES['night']['sun'] = (MOON, 200, (W * 0.72, 720))
G.THEMES['end']['sun'] = (LOTUS, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

PEAKS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PEAKS)
for _x, _h, _w in ((120, 420, 90), (220, 300, 70), (880, 380, 80), (990, 460, 90)):
    _d.polygon([(_x - _w, 1500), (_x - _w * 0.3, 1500 - _h), (_x + _w * 0.2, 1500 - _h * 0.92), (_x + _w, 1500)], fill=LOTUS + (34,))
MTN_COL = {'night': (32, 34, 52), 'death': (56, 58, 66), 'war': (98, 58, 50), 'fate': (70, 72, 110)}
def draw_background(t, theme):
    """蜀山: misty ranges with steep 三峡 cliffs at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 188, 200), (140, 146, 172), MTN_COL.get(theme, (100, 106, 140))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(PEAKS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """新月: a crescent moon and two small stars in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = LOTUS + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        cx, cy = x + sx * 52, y + sy * 52
        d.arc((cx - 26, cy - 26, cx + 26, cy + 26), 90 if sx > 0 else 270, 270 if sx > 0 else 90, fill=MOON + (240,), width=10)
        for (u, v) in ((110, 22), (22, 110)):
            d.ellipse((x + sx * u - 4, y + sy * v - 4, x + sx * u + 4, y + sy * v + 4), fill=MOON + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def li(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, cup=False, sword_on=True, **kw):
    """李白: loose robe, 幞头 with long soft tails flying, a sword on the back, often a wine cup."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.07 * h, y - 1.04 * h, x + 0.07 * h, y - 0.9 * h), 180, 360, fill=255)
        for k in range(2):
            d.line((x - dir * 0.05 * h, y - 0.97 * h, x - dir * (0.22 + 0.04 * k) * h, y - (0.88 - 0.08 * k) * h + 0.02 * h * math.sin(h + k)), fill=255, width=max(2, int(0.014 * h)))
        if sword_on:
            d.line((x - dir * 0.14 * h, y - 0.85 * h, x + dir * 0.1 * h, y - 0.35 * h), fill=255, width=max(2, int(0.016 * h)))
    if cup:
        hx, hy = hand
        A.d['moon'].chord((hx - 0.05 * h, hy - 0.06 * h, hx + 0.05 * h, hy + 0.02 * h), 0, 180, fill=255)
    return hand

def moon_phase(A, cx, cy, r, phase):
    """phase 0 = new, 0.5 = half, 1 = full."""
    if phase <= 0.02:
        A.d['moon'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=200, width=3)
        return
    A.d['moon'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    if phase < 1:
        off = 2 * r * phase
        A.d['moon'].ellipse((cx - r - off, cy - r - 2, cx + r - off, cy + r + 2), fill=0)

def wine_jar(A, x, base, s, layer='ink'):
    A.d[layer].ellipse((x - 0.5 * s, base - 1.1 * s, x + 0.5 * s, base), fill=255)
    A.d[layer].rectangle((x - 0.2 * s, base - 1.3 * s, x + 0.2 * s, base - 1.0 * s), fill=255)
    A.d['red'].rectangle((x - 0.24 * s, base - 1.38 * s, x + 0.24 * s, base - 1.28 * s), fill=255)

def cliff(A, x, top, base, w, side=1, layer='mid'):
    A.d[layer].polygon([(x, base), (x, top), (x + side * w * 0.6, top + 80), (x + side * w, base)], fill=230)

# ================================================================ chapter card
CH = {16: 0.12, 48: 0.3, 80: 0.6, 112: 1.0, 144: -1}
def art_moon_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    ph = CH.get(kb, 0.25)
    q = ease_out(u / (1.2 * P))
    if ph >= 0:
        moon_phase(A, 540, 960, 200, ph * q + (0.02 if ph == 0 else 0))
    else:
        river(A, 1120, t, rows=3, amp=4, speed=0.8)
        moon_phase(A, 540, 820, 120, 1.0)
        A.d['moon'].ellipse((540 - 120, 1180 - 30 + 4 * math.sin(t * 2), 540 + 120, 1180 + 30 + 4 * math.sin(t * 2)), fill=150)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_moon_chapter)
    ink_in(cv, text_img(no, SERIF, 56, LOTUS, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_poems(A, cv, t, u):
    ground(A, GROUND)
    n = min(90, int(clamp(u / (1.6 * P)) * 90) + 1)
    for i in range(n):
        x = 110 + (i % 18) * 50; y = GROUND - 30 - (i // 18) * 70
        A.d['lotus' if i % 9 else 'moon'].rectangle((x - 16, y - 50, x + 16, y), fill=255)

def art_l_hook_wine(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        wine_jar(A, 700 + k * 110, GROUND, 80)
    li(A, 380, GROUND, 270, dir=1, cup=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)))

def art_l_hook_gold(A, cv, t, u):
    palace(A, 760, GROUND, 400, layer='mid')
    ground(A, GROUND)
    li(A, lerp(560, 200, ease_out(u / (1.6 * P))), GROUND, 250, dir=-1, ph=t * 5, arm=40)
    for k in range(3):
        A.d['gold'].ellipse((lerp(520, 160, ease_out(u / (1.6 * P))) + k * 20, GROUND - 110, lerp(560, 200, ease_out(u / (1.6 * P))) + k * 20, GROUND - 90), fill=255)

def art_l_hook_moon(A, cv, t, u):
    river(A, 1200, t, rows=3, amp=4, speed=0.8)
    A.d['moon'].ellipse((440, 1230, 640, 1290), fill=180)
    boat(A, 760, 1240, 110, t, sail=False)
    li(A, 760, 1210, 150, dir=-1, arm=lerp(40, 150, ease_out(u / (1.4 * P))), cup=True)

# ================================================================ 第一回 青莲少年
def art_l_suiye(A, cv, t, u):
    A.d['dune'].polygon([(60, 1300), (W - 60, 1260), (W - 60, GROUND), (60, GROUND)], fill=120)
    city_wall(A, 360, 760, 1160, gate_x=560, label='碎叶', layer='mid')
    ground(A, GROUND)
    camel(A, 900, GROUND, 110, -1, t * 4, layer='ink')
    A.flush(cv)
    stamp(cv, seal('一说', 44, INK), 860, 880, t, t - u + P, rot=6)

def art_l_qinglian(A, cv, t, u):
    A.d['ocean'].ellipse((200, 1240, 880, 1380), fill=140)
    for k in range(6):
        x = 260 + k * 110
        A.d['lotus'].ellipse((x - 40, 1270, x + 40, 1300), fill=230)
        A.d['moon'].polygon([(x, 1250), (x - 16, 1280), (x + 16, 1280)], fill=230)
    ground(A, GROUND, x0=60, x1=200)
    person(A, 140, 1240, 110, dir=1, robe=True, hat='knot', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('青莲乡', 50), 860, 880, t, t - u + P, rot=6)

def art_l_needle(A, cv, t, u):
    river(A, 1300, t, rows=2, amp=4, speed=0.8)
    ground(A, 1300, x0=60, x1=W - 60)
    A.d['ink'].rectangle((560, 1240, 600, 1290), fill=255)
    person(A, 680, 1300, 190, dir=-1, robe=True, hat='knot', female=True, bow=50, arm=lerp(100, 140, 0.5 + 0.5 * math.sin(t * 6)), layer='ink')
    w = lerp(26, 4, ease_out(u / (3 * P)))
    A.d['ink'].rectangle((470, 1270 - w / 2, 640, 1270 + w / 2), fill=255)
    person(A, 320, 1300, 140, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('只要功夫深 铁杵磨成针', SERIF, 46, LOTUS, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)

def art_l_sword(A, cv, t, u):
    ground(A, GROUND)
    a = t * 3
    li(A, 540, GROUND, 260, dir=1 if math.cos(a) > 0 else -1, sword_on=False, sword=lerp(40, 170, 0.5 + 0.5 * math.sin(a)), arm=lerp(40, 170, 0.5 + 0.5 * math.sin(a)), arm2=lerp(-60, -120, 0.5 + 0.5 * math.cos(a)))
    for k in range(12):
        q = (t * 0.7 + k / 12) % 1
        ang = q * 2 * math.pi
        A.d['moon'].ellipse((540 + 240 * math.cos(ang) - 5, GROUND - 160 + 80 * math.sin(ang) - 5, 540 + 240 * math.cos(ang) + 5, GROUND - 160 + 80 * math.sin(ang) + 5), fill=int(220 * (1 - q)))
    A.flush(cv)
    stamp(cv, seal('剑术', 54), 860, 880, t, t - u + P, rot=6)

def art_l_kuangshan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 380 - 80 * (k % 2)), (x + 200, GROUND)], fill=170)
    A.d['ink'].polygon([(460, 1240), (620, 1240), (540, 1180)], fill=255)
    A.d['mid'].rectangle((470, 1240, 610, 1300), fill=230)
    ground(A, GROUND)
    sitter(A, 720, GROUND, 140, dir=-1, bow=15)
    for k in range(3):
        crow(A, 260 + k * 60, 860 + (k % 2) * 30, 24, t * 5 + k)
    A.flush(cv)
    stamp(cv, seal('大匡山', 50), 860, 880, t, t - u + P, rot=6)

def art_l_leave_shu(A, cv, t, u):
    """8-beat set piece: 仗剑去国 — a half moon over 峨眉; his boat runs down between the 三峡 cliffs; cliffs stream past."""
    ph = u / P
    moon_phase(A, 760, 820, 90, 0.5)
    A.d['moon'].ellipse((660, 1240, 860, 1280), fill=110)
    river(A, 1220, t, rows=4, amp=7, speed=2.6)
    off = (ph * 220) % 600
    for k in range(4):
        x = (k * 300 - off) % 1200 - 100
        cliff(A, x, 820 + (k % 2) * 60, 1220, 220, side=1 if k % 2 else -1, layer='mid' if k % 2 else 'lotus')
    boat(A, 480, 1260, 120, t, sail=True)
    li(A, 470, 1230, 140, dir=1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    lines = ['峨眉山月半轮秋', '影入平羌江水流', '夜发清溪向三峡', '思君不见下渝州']
    for i, ln in enumerate(lines):
        st = 0.4 + i * 1.6
        if ph >= st:
            type_in(cv, text_img(ln, SERIF, 40, LOTUS if i % 2 else INK, 'Black', bleed=False, vertical=True, spacing=2), 300 - i * 56, 960, t, t - u + st * P, 0.5)

def art_l_jingyesi(A, cv, t, u):
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=190)
    A.d['wash'].rectangle((620, 960, 820, 1160), fill=255)
    moon_phase(A, 720, 1060, 60, 1.0)
    A.d['moon'].polygon([(620, 1160), (820, 1160), (700, GROUND - 20), (420, GROUND - 20)], fill=110)
    ground(A, GROUND)
    li(A, 380, GROUND, 220, dir=1, arm=-8, bow=0)
    A.flush(cv)
    for i, ln in enumerate(('床前明月光', '疑是地上霜', '举头望明月', '低头思故乡')):
        type_in(cv, text_img(ln, SERIF, 36, INK, 'Black', bleed=False, vertical=True, spacing=2), 980 - i * 46 - 600, 760, t, t - u + 0.3 + i * 0.4 * P, 0.4)

# ================================================================ 第二回 酒隐安陆
def art_l_marriage(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='lotus')
    ground(A, GROUND)
    li(A, 420, GROUND, 230, dir=1, arm=lerp(20, 60, ease_out(u / P)))
    person(A, 660, GROUND, 210, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 60, ease_out(u / P)), layer='ink')
    A.d['red'].line((480, GROUND - 160, 600, GROUND - 160), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('许氏', 54), 860, 880, t, t - u + P, rot=6)

def art_l_changan1(A, cv, t, u):
    city_wall(A, 60, 1020, 1100, gate_x=760, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    x = lerp(760, 240, ease_out((u - P) / (2.5 * P)))
    li(A, x, GROUND, 220, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, bow=0, arm=-8)
    A.flush(cv)
    stamp(cv, seal('求仕无门', 44, INK), 860, 860, t, t - u + P, rot=6)

def art_l_farewell(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5, speed=1.2)
    A.d['lotus'].rectangle((140, 1000, 320, 1240), fill=230)
    A.d['ink'].polygon([(110, 1000), (350, 1000), (300, 940), (160, 940)], fill=255)
    A.d['ink'].polygon([(130, 940), (330, 940), (230, 880)], fill=255)
    li(A, 240, 1000, 150, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t)))
    x = lerp(500, 1000, ease_out(u / (3.5 * P)))
    boat(A, x, 1260, lerp(100, 40, ease_out(u / (3.5 * P))), t, sail=True)
    A.flush(cv)
    type_in(cv, text_img('孤帆远影碧空尽 唯见长江天际流', SERIF, 40, LOTUS, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.6)

def art_l_hard_road(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 420 - 80 * (k % 2)), (x + 200, GROUND)], fill=200)
    ground(A, GROUND)
    li(A, 540, GROUND, 260, dir=1, sword_on=False, sword=lerp(40, 170, ease_out(u / P)), arm=lerp(40, 170, ease_out(u / P)))
    A.flush(cv)
    type_in(cv, text_img('拔剑四顾心茫然', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('长风破浪会有时', SERIF, 48, LOTUS, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

JJJ = ['君不见黄河之水天上来', '奔流到海不复回', '人生得意须尽欢', '莫使金樽空对月', '天生我材必有用', '千金散尽还复来', '与尔同销万古愁']
def scene_jiangjin(cv, t, c, k):
    """8-beat custom scene: 将进酒 — the 黄河 pours from the sky at the left; each beat a line flows out with the wine
    from his raised cup; the last line lands in red."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for j in range(6):
        x = 120 + j * 22
        A.d['ocean'].line((x, 640, x + 30 * math.sin(t * 2 + j), 1200), fill=160, width=14)
    for j in range(12):
        q = (t * 1.6 + j / 12) % 1
        A.d['wash'].ellipse((130 + (j * 13) % 110 - 6, lerp(640, 1200, q) - 6, 130 + (j * 13) % 110 + 6, lerp(640, 1200, q) + 6), fill=200)
    river(A, 1200, t, rows=3, amp=8, speed=3)
    ground(A, GROUND, x0=400, x1=W - 60)
    for j in range(3):
        wine_jar(A, 880 + j * 60, GROUND, 50)
    li(A, 640, GROUND, 250, dir=-1, cup=True, arm=lerp(120, 170, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    n = min(len(JJJ), int(ph / 1.1) + 1)
    for i in range(n):
        x = 900 - i * 66
        type_in(cv, text_img(JJJ[i], SERIF, 38, ZHU if i == 4 else (LOTUS if i % 2 else INK), 'Black', bleed=False, vertical=True, spacing=2),
                x, 1000, t, s0 + i * 1.1 * P, 0.5)
    fx = Art()
    chars_in(cv, fx, '将进酒', BRUSH, 160, INK, W / 2, 440, t, s0, stagger=0.08, seed=74)
    fx.flush(cv)
    paste(cv, text_img('与友人岑勋 元丹丘共饮', SERIF, 42, LOTUS, 'Black', bleed=False, spacing=4), W / 2, 570, 1, clamp(ph / 0.4))
    paste(cv, text_img('作年不详 一说七五二年', SERIF, 38, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 1) / 0.4))

def art_l_summons(A, cv, t, u):
    """6-beat: 奉诏入京 — an imperial envoy arrives; he laughs to the sky, packs, and strides off."""
    ph = u / P
    A.d['mid'].rectangle((620, 1060, 960, GROUND), fill=200)
    A.d['ink'].polygon([(600, 1060), (980, 1060), (790, 960)], fill=255)
    ground(A, GROUND)
    for k in range(3):
        person(A, 700 + k * 60, GROUND, 110 - k * 10, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 6 + k)), layer='mid')
    rider(A, lerp(-150, 200, ease_out(ph / 1.5)), GROUND, 130, 1, t * 10, layer='ink', moving=ph < 1.5)
    x = 500 if ph < 3.5 else lerp(500, 1100, ease_out((ph - 3.5) / 2))
    li(A, x, GROUND, 240, dir=1, ph=t * 6 if ph >= 3.5 else None, arm=lerp(40, 170, ease_out((ph - 1.5) / 0.6)))
    A.flush(cv)
    type_in(cv, text_img('仰天大笑出门去', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)
    type_in(cv, text_img('我辈岂是蓬蒿人', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 3 * P, 0.5)

# ================================================================ 第三回 翰林供奉
def art_l_zhexian(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 340, layer='lotus')
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(30, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    li(A, 330, GROUND, 230, dir=1, cup=True, arm=100)
    A.d['gold'].ellipse((600, GROUND - 110, 650, GROUND - 80), fill=255)
    A.flush(cv)
    stamp(cv, seal('贺知章', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    ink_in(cv, text_img('谪仙人', BRUSH, 110, LOTUS), W / 2, 980, t, t - u + 1.5 * P, dur=0.3, settle=1.2)

def art_l_welcome(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='lotus')
    ground(A, GROUND)
    x = lerp(800, 600, ease_out(u / (1.5 * P)))
    person(A, x, GROUND, 230, dir=-1, robe=True, hat='crown', ph=t * 4 if u < 1.5 * P else None, arm=lerp(20, 100, ease_out((u - P) / 0.5)), layer='ink')
    li(A, 340, GROUND, 230, dir=1, arm=40)
    A.d['gold'].rectangle((400, GROUND - 60, 520, GROUND - 40), fill=255)
    A.flush(cv)
    stamp(cv, seal('降辇步迎', 44), 860, 880, t, t - u + P, rot=6)

def art_l_boots(A, cv, t, u):
    """8-beat set piece: 力士脱靴 (legend) — drunk on the palace steps; the emperor wants a poem; he sticks out a foot;
    the eunuch kneels and pulls off the boot; the brush flies."""
    ph = u / P
    palace(A, 540, 1100, 560, layer='lotus')
    for k in range(4):
        A.d['mid'].rectangle((200 + k * 40, GROUND - 40 - k * 30, 880 - k * 40, GROUND - k * 30), fill=230)
    ground(A, GROUND)
    li(A, 420, GROUND - 120, 220, dir=1, bow=lerp(-10, 10, 0.5 + 0.5 * math.sin(t * 1.5)) if ph < 3 else 0, cup=ph < 3, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 2)))
    if ph >= 2:
        x = lerp(900, 560, ease_out((ph - 2) / 1.2))
        person(A, x, GROUND - 60, 180, dir=-1, robe=True, hat='none', kneel=ph > 3.2, bow=50 if ph > 3.2 else 0, arm=lerp(40, 130, ease_out((ph - 3.2) / 0.6)), layer='mid')
    if ph >= 4.2:
        bx = lerp(520, 700, ease_out((ph - 4.2) / 0.8)); by = lerp(GROUND - 130, GROUND - 240, ease_out((ph - 4.2) / 0.8))
        A.d['ink'].polygon([(bx - 26, by), (bx + 26, by), (bx + 34, by + 30), (bx - 20, by + 30)], fill=255)
    if ph >= 5.5:
        brush(A, 360, 920, 120, ang=-0.6 + 0.3 * math.sin(t * 6))
    A.flush(cv)
    stamp(cv, seal('传说', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    if ph >= 3.2:
        stamp(cv, seal('高力士', 44), 600, 980, t, t - u + 3.2 * P, rot=-5)

def art_l_qingping(A, cv, t, u):
    ground(A, GROUND)
    for k in range(9):
        x = 160 + k * 95
        A.d['apricot'].ellipse((x - 40, 1160 + 20 * math.sin(k), x + 40, 1240 + 20 * math.sin(k)), fill=220)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='knot', female=True, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    li(A, 320, GROUND, 230, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    type_in(cv, text_img('云想衣裳花想容', SERIF, 50, LOTUS, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('杨贵妃', 44, INK), 860, 1060, t, t - u + 1.6 * P, rot=6)

def art_l_slander(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    for k in range(3):
        person(A, 860 + k * 50, GROUND, 160, dir=-1, robe=True, hat='none', bow=30, arm=100, layer='mid')
    li(A, 240, GROUND, 210, dir=1, cup=True, arm=60)
    A.flush(cv)
    for k in range(int(clamp((u - P) / P) * 3)):
        paste(cv, text_img('谗', BRUSH, 70, ZHU), 860 + k * 50, 1060 - k * 30, 1, 0.9)

def art_l_dismissed(A, cv, t, u):
    """6-beat: 赐金放还 — a tray of gold, a polite bow; he walks out of the palace gate laughing, the gold slung over a shoulder."""
    ph = u / P
    city_wall(A, 600, 1020, 1060, gate_x=810, label='长安', layer='lotus', open_=1.0)
    ground(A, GROUND)
    for k in range(5):
        A.d['gold'].ellipse((640 + k * 22, GROUND - 120, 680 + k * 22, GROUND - 100), fill=255 if ph < 2 else 0)
    x = 760 if ph < 2 else lerp(760, 180, ease_out((ph - 2) / 3.5))
    li(A, x, GROUND, 230, dir=-1, ph=t * 5 if ph >= 2 else None, cup=ph >= 2, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    if ph >= 2:
        A.d['gold'].ellipse((x + 30, GROUND - 230, x + 80, GROUND - 190), fill=255)
    A.flush(cv)
    stamp(cv, seal('赐金放还', 44), 300, 880, t, t - u + 0.4, rot=-5)

# ================================================================ 第四回 李杜相逢
def art_l_meet_du(A, cv, t, u):
    """6-beat: 洛阳相遇 — two figures approach from left and right, bow, and sit to drink; the age labels pop up."""
    ph = u / P
    ground(A, GROUND)
    p = ease_out(ph / 2.5)
    li(A, lerp(120, 420, p), GROUND, 240, dir=1, ph=t * 5 if ph < 2.5 else None, cup=ph > 3, arm=lerp(20, 90, ease_out((ph - 2.5) / 0.6)))
    person(A, lerp(980, 660, p), GROUND, 220, dir=-1, robe=True, hat='none', ph=t * 5 if ph < 2.5 else None, bow=20 if ph > 2.5 else 0, arm=60, layer='mid')
    if ph >= 3:
        wine_jar(A, 540, GROUND, 60)
    A.flush(cv)
    if ph >= 2.5:
        paste(cv, text_img('李白四十三', SERIF, 42, LOTUS, 'Black', bleed=False, spacing=4), 340, 830, 1, clamp((ph - 2.5) / 0.3))
        paste(cv, text_img('杜甫三十二', SERIF, 42, INK, 'Black', bleed=False, spacing=4), 740, 830, 1, clamp((ph - 2.8) / 0.3))

def art_l_qilu(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=200)
    ground(A, GROUND)
    x = lerp(100, 700, (u / (4 * P)))
    li(A, x, GROUND, 200, dir=1, ph=t * 4, arm=-8)
    person(A, x - 120, GROUND, 190, dir=1, robe=True, hat='none', ph=t * 4 + 1, arm=60, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('醉眠秋共被 携手日同行', SERIF, 46, LOTUS, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

def art_l_parting(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out((u - 0.5 * P) / (2.5 * P))
    li(A, lerp(480, 140, p), GROUND, 220, dir=-1, ph=t * 4, arm=-8)
    person(A, lerp(600, 940, p), GROUND, 210, dir=1, robe=True, hat='none', ph=t * 4, arm=-8, layer='mid')
    for k in range(20):
        q = (t * 0.4 + k / 20) % 1
        x = 80 + (k * 47) % 920
        A.d['wash'].ellipse((x - 3, lerp(620, 1420, q) - 3, x + 3, lerp(620, 1420, q) + 3), fill=200)
    A.flush(cv)
    paste(cv, text_img('此后再未相见', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_l_taohua(A, cv, t, u):
    river(A, 1220, t, rows=3, amp=5, speed=1.2)
    for k in range(6):
        x = 120 + k * 40
        A.d['apricot'].ellipse((x - 24, 1120 + (k % 2) * 30, x + 24, 1160 + (k % 2) * 30), fill=230)
    ground(A, 1220, x0=60, x1=420)
    for k in range(5):
        person(A, 160 + k * 50, 1220, 120, dir=1, robe=False, hat='knot', arm=lerp(20, 160, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    x = lerp(560, 900, ease_out(u / (3 * P)))
    boat(A, x, 1260, 110, t, sail=False)
    li(A, x, 1230, 130, dir=-1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    type_in(cv, text_img('桃花潭水深千尺 不及汪伦送我情', SERIF, 40, LOTUS, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.6)

def art_l_yongwang(A, cv, t, u):
    for k in range(6):
        boat(A, 140 + k * 160, 1260 + (k % 2) * 30, 80, t + k, sail=True)
    river(A, 1240, t, rows=2, amp=6, speed=2)
    li(A, 540, 1220, 160, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('永王幕府', 44), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('安史之乱', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_l_prison(A, cv, t, u):
    A.d['mid'].rectangle((240, 900, 840, GROUND), fill=190)
    li(A, 540, GROUND, 210, dir=1, sword_on=False, bow=0, arm=-8)
    bars(A, 260, 820, 920, GROUND, n=10)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('浔阳狱', 50, INK), 860, 860, t, t - u + P, rot=6)

def art_l_yelang(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 130, GROUND), (x, GROUND - 440 - 80 * (k % 2)), (x + 130, GROUND)], fill=200)
    pts = [(x, GROUND - 150 - 60 * math.sin(x / 140)) for x in range(80, W - 79, 20)]
    A.d['wash'].line(pts, fill=255, width=12)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    li(A, pts[i][0], pts[i][1], 110, dir=1, ph=t * 3, sword_on=False, arm=-8)
    A.flush(cv)
    stamp(cv, seal('夜郎', 56, INK), 860, 880, t, t - u + P, rot=6)

# ================================================================ 第五回 月下归去
def art_l_baidi(A, cv, t, u):
    """8-beat set piece: 早发白帝 — pardon at 白帝城; the boat shoots downstream at dawn; monkeys call from the cliffs;
    the counter flies to 千里."""
    ph = u / P
    sun(cv, 880, lerp(1240, 860, ease_out(ph / 4)), 100, ZHU, 140)
    river(A, 1220, t, rows=4, amp=8, speed=6)
    off = (t * 600) % 1200
    for k in range(5):
        x = (k * 280 - off) % 1400 - 200
        cliff(A, x, 820 + (k % 2) * 80, 1220, 220, side=1 if k % 2 else -1, layer='mid' if k % 2 else 'lotus')
        A.d['ink'].ellipse((x + 30, 900 + (k % 2) * 80, x + 54, 924 + (k % 2) * 80), fill=255)
    boat(A, 480, 1260, 130, t * 3, sail=True)
    li(A, 470, 1230, 150, dir=1, arm=lerp(100, 170, 0.5 + 0.5 * math.sin(t * 3)))
    for k in range(10):
        q = (t * 3 + k / 10) % 1
        A.d['wash'].line((480 - 200 * q, 1270 + 8 * k % 30, 520 - 200 * q, 1270 + 8 * k % 30), fill=int(200 * (1 - q)), width=3)
    A.flush(cv)
    li_ = int(lerp(0, 1000, clamp((ph - 1) / 5)))
    paste(cv, text_img(f'{li_}里' if li_ < 1000 else '千里江陵一日还', SERIF, 50, ZHU if li_ >= 1000 else LOTUS, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph < 1.5:
        stamp(cv, seal('遇赦', 56), 300, 960, t, t - u + 0.3, rot=-5)

def art_l_yangbing(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((560, 1060, 940, GROUND), fill=200)
    A.d['ink'].polygon([(540, 1060), (960, 1060), (750, 960)], fill=255)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='none', arm=lerp(20, 120, ease_out((u - P) / 0.5)), layer='ink')
    li(A, lerp(100, 420, ease_out(u / (2 * P))), GROUND, 200, dir=1, ph=t * 3, sword_on=False, arm=-8)
    A.flush(cv)
    stamp(cv, seal('李阳冰', 46), 300, 880, t, t - u + 0.5, rot=-5)

def art_l_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    li(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    person(A, 860, GROUND, 200, dir=-1, robe=True, hat='none', bow=30, arm=110, layer='ink')
    scroll(A, 760, GROUND - 160, 120, 50, u / 0.6)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('当涂', 56), 300, 880, t, t - u + P, rot=-5)

def art_l_catch_moon(A, cv, t, u):
    """legend: 醉中捉月 — he leans from the boat for the moon in the water; ripples close over it."""
    river(A, 1160, t, rows=3, amp=3, speed=0.6)
    moon_phase(A, 760, 820, 80, 1.0)
    rp = ease_out((u - 2 * P) / (1.5 * P))
    A.d['moon'].ellipse((560 - 90, 1230 - 22, 560 + 90, 1230 + 22), fill=int(200 * (1 - rp)))
    boat(A, 380, 1220, 110, t, sail=False)
    li(A, 400, 1190, 150, dir=1, bow=lerp(0, 70, ease_out((u - P) / P)), arm=lerp(60, 160, ease_out((u - P) / P)), cup=False)
    for k in range(4):
        r = 30 + 200 * rp + k * 30
        A.d['wash'].ellipse((560 - r, 1230 - r * 0.2, 560 + r, 1230 + r * 0.2), outline=int(200 * (1 - rp)), width=3)
    A.flush(cv)
    stamp(cv, seal('传说', 46, INK), 860, 1040, t, t - u + 0.4, rot=6)

def art_l_immortal(A, cv, t, u):
    for k in range(12):
        x = 140 + (k % 6) * 160; y = 980 + (k // 6) * 160
        A.d['lotus' if k % 2 else 'moon'].rectangle((x - 50, y - 60, x + 50, y + 60), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('九百余首 · 流传至今', SERIF, 48, LOTUS, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_legacy(A, cv, t, u):
    river(A, 1200, t, rows=3, amp=3, speed=0.6)
    moon_phase(A, 540, 900, 120, 1.0)
    A.d['moon'].ellipse((420, 1230, 660, 1280), fill=150)

def art_l_title(A, cv, t, u):
    moon_phase(A, 800, 820, 110, 1.0)
    li(A, 400, 1460, 680, dir=1, cup=True, arm=lerp(40, 130, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '青莲少年'), 48: ('第二回', '酒隐安陆'), 80: ('第三回', '翰林供奉'),
            112: ('第四回', '李杜相逢'), 144: ('第五回', '月下归去')}

CARDS = [
    C(0, 2, 'works', 'num', num='九百余首', line='诗仙', art=art_l_hook_poems),
    C(2, 4, 'fate', 'num', num='斗酒诗百篇', line='杜甫这样写他', art=art_l_hook_wine),
    C(4, 6, 'court', 'num', num='赐金放还', line='被皇帝客气地送走', art=art_l_hook_gold),
    C(6, 8, 'night', 'num', num='醉中捉月', line='传说他这样离开', art=art_l_hook_moon),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 青莲少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=701, main='生于碎叶', sub='一说生于蜀中', note='其先隋末流寓西域', art=art_l_suiye),
    C(22, 26, 'works', 'card', year=705, main='移居青莲', sub='随父迁居绵州昌隆', note='自号青莲居士', art=art_l_qinglian),
    C(26, 30, 'life', 'card', year=711, main='铁杵磨针', sub='遇老妇磨杵 · 发奋读书', note='传说', art=art_l_needle),
    C(30, 34, 'war', 'card', year=716, main='好剑术', sub='十五好剑术 · 遍干诸侯', art=art_l_sword),
    C(34, 38, 'works', 'card', year=720, main='大匡山', sub='隐居读书', art=art_l_kuangshan),
    C(38, 46, 'night', 'card', year=725, main='仗剑去国', sub='辞亲远游 · 出三峡', note='峨眉山月歌', art=art_l_leave_shu),
    C(46, 48, 'night', 'card', year=726, main='静夜思', sub='客居扬州', note='一说', art=art_l_jingyesi),
    # ---- 第二回 酒隐安陆
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'life', 'card', year=727, main='入赘许家', sub='娶故相许圉师孙女', art=art_l_marriage),
    C(54, 58, 'court', 'card', year=730, main='一入长安', sub='求仕无门 · 失意而归', art=art_l_changan1),
    C(58, 62, 'works', 'card', year=730, main='送孟浩然', sub='故人西辞黄鹤楼', note='烟花三月下扬州', art=art_l_farewell),
    C(62, 66, 'fate', 'card', year=731, main='行路难', sub='直挂云帆济沧海', note='作年 一说', art=art_l_hard_road),
    C(66, 74, 'fate', 'jiangjin', year=736),
    C(74, 80, 'empire', 'card', year=742, main='奉诏入京', sub='四十一岁 · 终于等到', art=art_l_summons),
    # ---- 第三回 翰林供奉
    C(80, 82, 'court', 'chapter'),
    C(82, 86, 'fate', 'card', year=742, main='谪仙人', sub='贺知章初见 · 金龟换酒', art=art_l_zhexian),
    C(86, 90, 'empire', 'card', year=742, main='降辇步迎', sub='玄宗亲迎 · 御手调羹', note='七宝床赐食', art=art_l_welcome),
    C(90, 98, 'court', 'card', year=743, main='力士脱靴', sub='醉中令高力士脱靴', note='传说 未见正史', art=art_l_boots),
    C(98, 102, 'life', 'card', year=743, main='清平调', sub='为杨贵妃赋诗', art=art_l_qingping),
    C(102, 106, 'night', 'card', year=744, main='谗言', sub='权贵侧目', art=art_l_slander),
    C(106, 112, 'fate', 'card', year=744, main='赐金放还', sub='天子客气地请他离开', art=art_l_dismissed),
    # ---- 第四回 李杜相逢
    C(112, 114, 'life', 'chapter'),
    C(114, 120, 'life', 'card', year=744, main='洛阳相遇', sub='诗仙遇见诗圣', art=art_l_meet_du),
    C(120, 124, 'works', 'card', year=745, main='同游齐鲁', sub='杜甫记下了那段日子', art=art_l_qilu),
    C(124, 128, 'night', 'card', year=745, main='一别永诀', sub='石门分手', art=art_l_parting),
    C(128, 132, 'life', 'card', year=754, main='桃花潭', sub='汪伦踏歌相送', note='一说七五五年', art=art_l_taohua),
    C(132, 136, 'war', 'card', year=756, main='永王幕府', sub='入永王李璘幕', art=art_l_yongwang),
    C(136, 140, 'night', 'card', year=757, main='下狱浔阳', sub='永王兵败 · 牵连入狱', art=art_l_prison),
    C(140, 144, 'death', 'card', year=758, main='流放夜郎', sub='长流夜郎', art=art_l_yelang),
    # ---- 第五回 月下归去
    C(144, 146, 'death', 'chapter'),
    C(146, 154, 'works', 'card', year=759, main='早发白帝', sub='流放途中遇赦', note='两岸猿声啼不住 轻舟已过万重山', art=art_l_baidi),
    C(154, 158, 'fate', 'card', year=761, main='投奔族叔', sub='往当涂依李阳冰', art=art_l_yangbing),
    C(158, 162, 'death', 'card', year=762, main='病逝当涂', sub='临终将诗稿托付李阳冰', art=art_l_death),
    C(162, 166, 'night', 'card', year=762, main='醉中捉月', sub='后人不愿他病死', note='传说 醉后入水捉月', art=art_l_catch_moon),
    C(166, 170, 'end', 'card', year=2026, main='诗仙', sub='至今仍在背诵', art=art_l_immortal),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾壹', col=LOTUS, acc=MOON, born=701, died=762,
    hook_q='天子呼来不上船 · 他到底有多狂？',
    name_line='李白 · 字太白', name='李白', seal='青莲', title_art=art_l_title,
    q1='诗仙？', q2='酒鬼？',
    end_art=art_l_legacy, end_big='诗仙', end_seal='青莲',
    end_l1='他没当成想当的官', end_l2='却成了中国人心里的月亮',
    end_brush='天生我材必有用', end_ask='你最爱他哪一句？评论区聊聊', next='杜甫'),
    scenes=dict(chapter=scene_chapter, jiangjin=scene_jiangjin))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
