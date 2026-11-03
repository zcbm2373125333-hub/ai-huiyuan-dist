"""千古人物志 · 第肆拾伍集 · 林则徐 (1785–1850)
Look: 海防蓝 + 烟土褐, 炮台 corner borders, a 虎门 chapter card: the sea fort's guns grow from none to a full battery,
then the flag falls in the last chapter.
Set pieces: 6-beat 治水, custom 8-beat scene 'humen' (虎门销烟: 23 days, 237万斤), 6-beat 收缴烟土,
8-beat 鸦片战争, 6-beat 伊犁, 6-beat 苟利国家.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_suiyangdi as Sy       # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_quyuan import river
from render_kongzi import bundle
from render_zhangqian import yurt

F.RIPPLE = False
HAIFANG = (38, 76, 120)             # 海防蓝
YANTU = (110, 72, 44)               # 烟土褐
S.LAYERS.append(('haifang', HAIFANG, 0.88, 1.0))
S.LAYERS.append(('yantu', YANTU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='禁', life='林', court='清', night='夜', war='战', empire='清', works='销', fate='戍', death='国', end='国')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (HAIFANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HAIFANG, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

SEA = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SEA)
for _k in range(5):
    _y = 1430 + _k * 14
    _d.line((60, _y, W - 60, _y), fill=HAIFANG + (40 - _k * 6,), width=3)
for _x, _y in ((150, 1360), (930, 1350)):
    _d.polygon([(_x - 40, _y), (_x + 40, _y), (_x + 30, _y + 20), (_x - 30, _y + 20)], fill=(60, 60, 70, 60))
    _d.line((_x, _y, _x, _y - 70), fill=(60, 60, 70, 60), width=3)
    _d.polygon([(_x, _y - 70), (_x + 30, _y - 30), (_x, _y - 20)], fill=(240, 240, 240, 60))
MTN_COL = {'night': (32, 36, 46), 'death': (60, 60, 64), 'war': (104, 60, 50), 'fate': (90, 96, 110)}
def draw_background(t, theme):
    """珠江口: low headlands, sea lines and distant sails at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(182, 188, 196), (138, 152, 170), MTN_COL.get(theme, (96, 114, 140))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(SEA)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """炮台: a small cannon in an embrasure in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=HAIFANG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=HAIFANG + (220,), width=3)
        d.rectangle((min(x + sx * 14, x + sx * 90), min(y + sy * 14, y + sy * 54), max(x + sx * 14, x + sx * 90), max(y + sy * 14, y + sy * 54)), fill=YANTU + (200,))
        cx, cy = x + sx * 52, y + sy * 34
        d.line((cx, cy, cx + sx * 60, cy + sy * 30), fill=(40, 40, 46, 240), width=10)
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(40, 40, 46, 240))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def lin(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """林则徐: Qing official — 顶戴 hat with a knob and peacock feather, queue, mandarin square, moustache."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.1 * h, y - 1.02 * h, x + 0.1 * h, y - 0.86 * h), 180, 360, fill=255)
        d.rectangle((x - 0.11 * h, y - 0.95 * h, x + 0.11 * h, y - 0.93 * h), fill=255)
        A.d['red'].ellipse((x - 0.025 * h, y - 1.06 * h, x + 0.025 * h, y - 1.01 * h), fill=255)
        A.d['haifang'].line((x - dir * 0.02 * h, y - 1.0 * h, x - dir * 0.2 * h, y - 0.9 * h), fill=255, width=max(2, int(0.02 * h)))
        d.line((x - dir * 0.05 * h, y - 0.88 * h, x - dir * 0.08 * h, y - 0.55 * h), fill=255, width=max(2, int(0.015 * h)))
        A.d['haifang'].rectangle((x - 0.07 * h, y - 0.72 * h, x + 0.07 * h, y - 0.6 * h), fill=255)
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.0, y - 0.86 * h, x + dir * 0.06 * h, y - 0.82 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def foreigner(A, x, y, h, dir=1, layer='mid', **kw):
    hand = person(A, x, y, h, dir=dir, robe=False, hat='none', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d[layer].rectangle((x - 0.08 * h, y - 1.1 * h, x + 0.08 * h, y - 0.96 * h), fill=255)
        A.d[layer].rectangle((x - 0.14 * h, y - 0.97 * h, x + 0.14 * h, y - 0.94 * h), fill=255)
    return hand

def fort(A, cx, base, w, guns, t, fallen=0.0):
    A.d['yantu'].polygon([(cx - w / 2, base), (cx - w / 2 + 30, base - 140), (cx + w / 2 - 30, base - 140), (cx + w / 2, base)], fill=230)
    for k in range(int(w / 70)):
        A.d['yantu'].rectangle((cx - w / 2 + 40 + k * 70, base - 170, cx - w / 2 + 70 + k * 70, base - 140), fill=230)
    n = min(guns, 6)
    for i in range(n):
        gx = cx - w / 2 + 70 + i * (w - 140) / max(1, 5)
        A.d['ink'].line((gx, base - 110, gx + 80, base - 130), fill=255, width=14)
        A.d['ink'].ellipse((gx - 18, base - 128, gx + 18, base - 92), fill=255)
    fx = cx + w / 2 - 60
    ang = fallen * 1.4
    A.d['ink'].line((fx, base - 170, fx + 200 * math.sin(ang), base - 170 - 200 * math.cos(ang)), fill=255, width=5)
    if fallen < 0.9:
        A.d['yellow'].polygon([(fx + 200 * math.sin(ang), base - 170 - 200 * math.cos(ang)), (fx + 200 * math.sin(ang) + 80, base - 150 - 200 * math.cos(ang)),
                               (fx + 200 * math.sin(ang), base - 120 - 200 * math.cos(ang))], fill=255)

def warship(A, x, y, s, t, smoke=True, fire=0.0):
    A.d['ink'].polygon([(x - s, y - 0.2 * s), (x + 1.1 * s, y - 0.2 * s), (x + 0.9 * s, y + 0.1 * s), (x - 0.9 * s, y + 0.1 * s)], fill=255)
    for k in range(3):
        mx = x - 0.5 * s + k * 0.5 * s
        A.d['ink'].line((mx, y - 0.2 * s, mx, y - 1.1 * s), fill=255, width=4)
        A.d['wash'].polygon([(mx - 0.2 * s, y - 1.0 * s), (mx + 0.2 * s, y - 1.0 * s), (mx + 0.22 * s, y - 0.5 * s), (mx - 0.22 * s, y - 0.5 * s)], fill=230)
    for k in range(5):
        A.d['wash'].ellipse((x - 0.7 * s + k * 0.35 * s - 6, y - 0.12 * s - 6, x - 0.7 * s + k * 0.35 * s + 6, y - 0.12 * s + 6), fill=255)
    if fire > 0:
        for k in range(3):
            r = 30 * fire
            A.d['red'].ellipse((x - 0.9 * s - r - k * 20, y - 0.15 * s - r, x - 0.9 * s + r - k * 20, y - 0.15 * s + r), fill=int(220 * fire))

def opium_ball(A, x, y, s):
    A.d['yantu'].ellipse((x - s, y - s, x + s, y + s), fill=255)
    A.d['ink'].arc((x - s, y - s, x + s, y + s), 200, 320, fill=120, width=3)

# ================================================================ chapter card
CH = {16: (0, 0.0), 48: (2, 0.0), 80: (4, 0.0), 112: (6, 0.0), 144: (6, 1.0)}
def art_fort_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, fallen = CH.get(kb, (2, 0.0))
    prev = {48: 0, 80: 2, 112: 4, 144: 6}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    A.d['haifang'].rectangle((60, 1160, W - 60, 1240), fill=150)
    waves(A, 1170, t, rows=2, amp=4)
    fort(A, 540, 1160, 640, int(lerp(prev, g, q)), t, fallen=fallen * q)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_fort_chapter)
    ink_in(cv, text_img(no, SERIF, 56, HAIFANG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_smoke(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1220, W - 60, GROUND), fill=150)
    for k in range(10):
        q = (t * 0.4 + k / 10) % 1
        A.d['mid'].ellipse((200 + (k * 71) % 680 - 40 - 30 * q, lerp(1200, 760, q) - 30, 200 + (k * 71) % 680 + 40 + 30 * q, lerp(1200, 760, q) + 30), fill=int(180 * (1 - q)))
    for k in range(3):
        A.d['yantu'].rectangle((200 + k * 260, 1180, 380 + k * 260, 1240), fill=255)

def art_l_hook_237(A, cv, t, u):
    ground(A, GROUND)
    n = min(237, int(clamp(u / (1.6 * P)) * 237) + 1)
    for i in range(n):
        x = 100 + (i % 30) * 30; y = GROUND - 12 - (i // 30) * 28
        opium_ball(A, x, y, 11)

def art_l_hook_eye(A, cv, t, u):
    ground(A, GROUND)
    lin(A, 380, GROUND, 260, dir=1, arm=lerp(40, 130, ease_out(u / P)))
    for k in range(int(clamp(u / (1.6 * P)) * 8)):
        bundle(A, 640 + (k % 4) * 70, GROUND - (k // 4) * 60, 60, layer='haifang')

def art_l_hook_exile(A, cv, t, u):
    for k in range(50):
        q = (t * 0.5 + k / 50) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    ground(A, GROUND)
    lin(A, lerp(100, 700, ease_out(u / (1.6 * P))), GROUND, 210, dir=1, ph=t * 3, old=0.6, arm=-8)

# ================================================================ 第一回 福州少年
def art_l_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('福州侯官', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('父亲林宾日 · 塾师清贫', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_juren(A, cv, t, u):
    for r in range(3):
        for c2 in range(6):
            x = 200 + c2 * 140; y = 960 + r * 120
            A.d['mid'].rectangle((x - 50, y, x + 50, y + 90), fill=220)
            A.d['ink'].rectangle((x - 50, y, x + 50, y + 90), outline=255, width=4)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('中举', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('二十岁 乡试中举', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_jinshi(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='haifang')
    ground(A, GROUND)
    lin(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / 0.6)))
    A.d['yellow'].rectangle((240, 860, 840, 920), fill=255)
    A.flush(cv)
    stamp(cv, seal('进士', 56), 860, 980, t, t - u + P, rot=6)

def art_l_hanlin(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='haifang')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        bundle(A, 440 + (k % 4) * 50, GROUND - 74 - (k // 4) * 30, 40, layer='yantu')
    A.flush(cv)
    stamp(cv, seal('翰林院', 50), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('七年 · 博览经世之书', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_motto(A, cv, t, u):
    A.d['wash'].rectangle((340, 860, 740, 1260), fill=255)
    A.d['ink'].rectangle((340, 860, 740, 1260), outline=255, width=6)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('制怒', BRUSH, 150, ZHU), W / 2, 1060, t, t - u + 0.5, 0.5)
    paste(cv, text_img('书于堂上 · 自戒急躁', SERIF, 44, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('传说', 44, INK), 860, 1300, t, t - u + P, rot=6)

def art_l_jiangsu(A, cv, t, u):
    """6-beat: 治水 — river breaches; he walks the dykes; workers fill the gaps; the river is tamed."""
    ph = u / P
    lvl = lerp(1240, 1300, ease_out((ph - 3) / 2))
    A.d['yellow'].rectangle((60, lvl, W - 60, GROUND + 40), fill=180)
    waves(A, lvl + 6, t, rows=3, amp=int(lerp(10, 3, ease_out((ph - 3) / 2))), speed=2)
    A.d['mid'].polygon([(60, lvl - 10), (W - 60, lvl - 30), (W - 60, lvl + 10), (60, lvl + 20)], fill=230)
    for k in range(6):
        x = (t * 80 + k * 170) % (W + 200) - 100
        person(A, x, lvl - 20, 80, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + k, arm=160, layer='ink')
    lin(A, 860, lvl - 25, 170, dir=-1, arm=60)
    A.flush(cv)
    stamp(cv, seal('江苏巡抚', 44), 260, 1020, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('兴修水利 · 赈济灾民', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_huguang(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='武昌', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['yantu'].ellipse((160 + k * 100 - 20, GROUND - 40, 160 + k * 100 + 20, GROUND), fill=255)
    lin(A, 540, GROUND, 210, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('湖广总督', 44), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('在湖广试行禁烟', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第二回 钦差禁烟
def art_l_opium(A, cv, t, u):
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=180)
    ground(A, GROUND)
    for k in range(5):
        x = 260 + k * 130
        person(A, x, GROUND - 20, 140, dir=1, robe=True, hat='knot', fall=-75, arm=60, layer='ink')
        A.d['yantu'].line((x + 40, GROUND - 100, x + 100, GROUND - 120), fill=255, width=6)
        lamp(A, x + 100, GROUND - 20, 20, t, glow=0.3)
    A.flush(cv)
    paste(cv, text_img('烟毒泛滥 · 白银外流', SERIF, 48, YANTU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_memorial(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='haifang')
    lin(A, 300, GROUND, 220, dir=1, kneel=True, bow=15, arm=90)
    scroll(A, 600, GROUND - 120, 260, 70, u / 0.6)
    A.flush(cv)
    type_in(cv, text_img('数十年后 中原几无可以御敌之兵', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + P, 0.6)
    type_in(cv, text_img('且无可以充饷之银', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 2 * P, 0.5)

def art_l_qinchai(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='yantu')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.6)), layer='ink')
    lin(A, 360, GROUND, 220, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('钦差大臣', 46), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('道光帝八次召见', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_south(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300), (x + 150, GROUND)], fill=200)
    pts = [(x, GROUND - 120 - 60 * math.sin(x / 150)) for x in range(80, W - 79, 20)]
    A.d['wash'].line(pts, fill=255, width=10)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    carriage(A, pts[i][0], pts[i][1], 70, dir=1, wheel=t * 6, ph=t * 8, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('若鸦片一日未绝 本大臣一日不回', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.6)

def art_l_collect(A, cv, t, u):
    """6-beat set piece: 收缴 — the foreign factories are surrounded; servants withdrawn; chests are carried out and stacked."""
    ph = u / P
    for k in range(3):
        A.d['wash'].rectangle((160 + k * 260, 960, 380 + k * 260, 1220), fill=230)
        A.d['ink'].rectangle((160 + k * 260, 960, 380 + k * 260, 1220), outline=255, width=4)
        flag(A, 270 + k * 260, 960, 100, t, w=50, layer='mid')
    ground(A, GROUND)
    for k in range(6):
        person(A, 100 + k * 170, GROUND, 120, dir=1 if k % 2 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='haifang')
    n = int(clamp((ph - 1.5) / 3.5) * 20)
    for i in range(n):
        A.d['yantu'].rectangle((240 + (i % 10) * 60, GROUND - 40 - (i // 10) * 36, 290 + (i % 10) * 60, GROUND - 8 - (i // 10) * 36), fill=255)
    A.flush(cv)
    stamp(cv, seal('十三行', 50), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img(f'收缴烟箱 {n * 1000}' if n < 20 else '收缴鸦片二万余箱', SERIF, 46, YANTU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_l_tablet(A, cv, t, u):
    A.d['wash'].rectangle((280, 860, 800, 1220), fill=255)
    A.d['ink'].rectangle((280, 860, 800, 1220), outline=255, width=6)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('海纳百川 有容乃大', SERIF, 46, HAIFANG, 'Black', bleed=False, vertical=True, spacing=4), 620, 1040, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('壁立千仞 无欲则刚', SERIF, 46, ZHU, 'Black', bleed=False, vertical=True, spacing=4), 460, 1040, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第三回 虎门销烟
def scene_humen(cv, t, c, k):
    """8-beat custom scene: 虎门销烟 — two pools on the beach; opium broken in with salt and lime; water churns and smokes;
    the outflow goes to sea on the ebb tide; the counter climbs to 二百三十七万斤 over 23 days."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['haifang'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=3, amp=4, speed=1.2)
    for i, cx in enumerate((320, 760)):
        A.d['mid'].rectangle((cx - 180, 1040, cx + 180, 1190), fill=200)
        A.d['ink'].rectangle((cx - 180, 1040, cx + 180, 1190), outline=255, width=6)
        churn = clamp((ph - 1 - i * 0.5) / 1)
        if churn > 0:
            for j in range(8):
                q = (t * 0.8 + j / 8) % 1
                A.d['wash'].ellipse((cx - 150 + (j * 41) % 300 - 20 - 20 * q, lerp(1040, 760, q) - 20, cx - 150 + (j * 41) % 300 + 20 + 20 * q, lerp(1040, 760, q) + 20), fill=int(200 * (1 - q) * churn))
            A.d['yantu'].rectangle((cx - 170, 1080, cx + 170, 1180), fill=int(200 * churn))
    for j in range(5):
        x = (t * 70 + j * 200) % (W + 200) - 100
        person(A, x, 1040, 70, dir=1, robe=False, hat='knot', load=True, ph=t * 6 + j, arm=160, layer='ink')
    lin(A, 540, 1040, 110, dir=1, arm=60)
    A.flush(cv)
    days = min(23, int(ph * 23 / 7.5) + 1)
    jin = int(lerp(0, 2376254, clamp(ph / 7.5)))
    fx = Art()
    chars_in(cv, fx, '虎门销烟', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=39)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(days)}天 · {jin} 斤', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('海水浸化 · 盐卤石灰 · 退潮入海', SERIF, 42, HAIFANG, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 0.5) / 0.4))

def art_l_forts(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1220, W - 60, GROUND), fill=150)
    waves(A, 1230, t, rows=2, amp=4)
    fort(A, 540, 1220, 600, int(clamp(u / (2 * P)) * 6), t)
    A.d['ink'].line((60, 1250, W - 60, 1270), fill=255, width=4)
    A.flush(cv)
    stamp(cv, seal('整饬海防', 44), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('购炮 拦江铁链 · 组织团练', SERIF, 44, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_translate(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='haifang')
    lin(A, 300, GROUND, 210, dir=1, kneel=True, bow=15, arm=90)
    sitter(A, 780, GROUND, 170, dir=-1, bow=25, layer='mid')
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['wash'].rectangle((420 + (k % 4) * 60, GROUND - 90 - (k // 4) * 16, 470 + (k % 4) * 60, GROUND - 76 - (k // 4) * 16), fill=255)
    A.flush(cv)
    stamp(cv, seal('四洲志', 50), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('组织翻译西书 · 了解世界', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_eye(A, cv, t, u):
    A.d['ocean'].ellipse((300, 820, 780, 1300), fill=130)
    A.d['ink'].ellipse((300, 820, 780, 1300), outline=255, width=6)
    for k in range(6):
        A.d['grass'].ellipse((380 + (k * 67) % 300, 900 + (k * 53) % 300, 460 + (k * 67) % 300, 960 + (k * 53) % 300), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('开眼看世界第一人', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('后人誉之', 40, INK), 860, 1360, t, t - u + P, rot=6)

def art_l_kowloon(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1180, W - 60, GROUND), fill=150)
    waves(A, 1190, t, rows=3, amp=6, speed=2)
    warship(A, 760, 1240, 120, t, fire=ease_out((u - P) / 0.6) * (0.5 + 0.5 * math.sin(t * 6)))
    for k in range(3):
        boat(A, 240 + k * 120, 1240, 60, t + k, sail=True)
    A.flush(cv)
    stamp(cv, seal('九龙海战', 44), 260, 1020, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('英舰挑衅 · 清军还击', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第四回 鸦片战争
def art_l_war(A, cv, t, u):
    """8-beat set piece: 鸦片战争 — warships arrive; Guangzhou is well defended, so they sail north; 定海 falls;
    the fleet reaches 天津 大沽口; the court panics."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    coast = [(700, 1380), (760, 1240), (800, 1100), (780, 960), (720, 840)]
    A.d['grass'].polygon([(110, 760), (720, 760)] + coast[::-1] + [(700, 1420), (110, 1420)], fill=120)
    A.d['ink'].line(coast, fill=255, width=6)
    ports = [('广州', 640, 1360), ('定海', 860, 1200), ('大沽', 760, 860)]
    route = [(900, 1400), (860, 1240), (880, 1060), (820, 880)]
    f = clamp(ph / 6)
    n = len(route) - 1
    m = f * n
    for i in range(n):
        ff = clamp(m - i)
        if ff <= 0: break
        (x0, y0), (x1, y1) = route[i], route[i + 1]
        A.d['red'].line((x0, y0, lerp(x0, x1, ff), lerp(y0, y1, ff)), fill=255, width=6)
    i = min(n - 1, int(m)); ff = clamp(m - i)
    sx, sy = lerp(route[i][0], route[i + 1][0], ff), lerp(route[i][1], route[i + 1][1], ff)
    warship(A, sx, sy, 40, t)
    A.flush(cv)
    for j, (nm, x, y) in enumerate(ports):
        stamp(cv, seal(nm, 30, ZHU if (j == 1 and ph >= 2.5) else HAIFANG), x - 100, y, t, t - u + 0.3 + j * 0.3)
    lab = '广州防守严密 · 英舰北上' if ph < 2.5 else ('攻陷定海' if ph < 5 else '直逼天津 · 京师震动')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2.5 else HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 760 - 0, 1, 1)

def art_l_dismissed(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='yantu')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 150, ease_out(u / 0.6)), layer='ink')
    lin(A, 360, GROUND, 220, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('革职', 60, INK), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('替罪羊 · 琦善接任', SERIF, 46, YANTU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_l_humen_falls(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1220, W - 60, GROUND), fill=150)
    waves(A, 1230, t, rows=2, amp=5)
    fort(A, 340, 1220, 420, 4, t, fallen=ease_out((u - 1.5 * P) / P))
    flames(A, 340, 1100, 300, 200 * ease_out((u - P) / 0.8), t, n=5, seed=11, smoke=True)
    warship(A, 800, 1250, 100, t, fire=0.5 + 0.5 * math.sin(t * 6))
    A.flush(cv)
    stamp(cv, seal('关天培', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('虎门陷落 · 关天培战死', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_l_zhenhai(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='镇海', layer='mid', open_=1.0)
    ground(A, GROUND)
    lin(A, 540, GROUND, 210, dir=1, arm=60, old=0.3)
    A.flush(cv)
    stamp(cv, seal('协防浙江', 44), 860, 1020, t, t - u + 0.4, rot=6)
    paste(cv, text_img('戴罪立功 · 又被追究', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_treaty(A, cv, t, u):
    boat(A, 540, 1100, 200, t, sail=False)
    warship(A, 540, 1200, 220, t)
    A.d['haifang'].rectangle((60, 1240, W - 60, GROUND), fill=150)
    waves(A, 1250, t, rows=2, amp=3)
    A.flush(cv)
    stamp(cv, seal('南京条约', 50, INK), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('割香港 · 赔银二千一百万元', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_xi(A, cv, t, u):
    """6-beat set piece: 发配伊犁 — farewell at 西安; he writes the couplet to his wife; the cart heads into the snowy west."""
    ph = u / P
    if ph < 3:
        ground(A, GROUND)
        lin(A, 380, GROUND, 220, dir=1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t)), old=0.5)
        person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, bow=20, arm=60, layer='ink')
    else:
        for k in range(60):
            q = (t * 0.5 + k / 60) % 1
            A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
        for k in range(5):
            x = 140 + k * 200
            A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 360), (x + 150, GROUND)], fill=200)
        ground(A, GROUND)
        carriage(A, lerp(300, 1000, ease_out((ph - 3) / 2.5)), GROUND, 100, dir=1, wheel=t * 4, ph=t * 5, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('苟利国家生死以', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('岂因祸福避趋之', SERIF, 50, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第五回 苟利国家
def art_l_ili(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 130, GROUND), (x, GROUND - 400), (x + 130, GROUND)], fill=200)
        A.d['wash'].polygon([(x - 40, GROUND - 280), (x, GROUND - 400), (x + 40, GROUND - 280)], fill=255)
    yurt(A, 760, GROUND, 260, 200, layer='yantu')
    ground(A, GROUND)
    lin(A, 400, GROUND, 200, dir=1, arm=60, old=0.7)
    A.flush(cv)
    stamp(cv, seal('伊犁', 54), 860, 1020, t, t - u + 0.4, rot=6)

def art_l_irrigate(A, cv, t, u):
    A.d['dune'].rectangle((60, 1200, W - 60, GROUND), fill=150)
    p = ease_out(u / (2.5 * P))
    A.d['ocean'].line((100, 1280, 100 + 880 * p, 1300), fill=200, width=16)
    for k in range(int(p * 10)):
        x = 140 + k * 86
        A.d['grass'].polygon([(x - 30, 1270), (x, 1200), (x + 30, 1270)], fill=220)
    lin(A, 880, 1200, 160, dir=-1, arm=60, old=0.7)
    A.flush(cv)
    paste(cv, text_img('勘垦屯田 · 兴修水利', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('坎儿井', 44), 260, 1040, t, t - u + P, rot=-5)

def art_l_russia(A, cv, t, u):
    A.d['wash'].rounded_rectangle((160, 820, 920, 1300), radius=20, fill=170)
    A.d['red'].line((400, 840, 380, 1000, 520, 1120, 480, 1280), fill=255, width=6)
    ground(A, GROUND)
    lin(A, 860, GROUND, 200, dir=-1, arm=lerp(40, 140, ease_out(u / P)), old=0.7)
    A.flush(cv)
    type_in(cv, text_img('终为中国患者 其俄罗斯乎', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + P, 0.5)

def art_l_recall(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    lin(A, lerp(-80, 540, ease_out(u / (2.5 * P))), GROUND, 200, dir=1, ph=t * 3, arm=-8, old=0.7)
    A.flush(cv)
    stamp(cv, seal('赐还', 54), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('历任陕甘 陕西 云贵', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    lin(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('普宁', 54), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('奉命镇压起义 · 途中病逝', SERIF, 44, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_l_wenzhong(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('文忠', BRUSH, 140, ZHU), W / 2, 960, t, t - u + 0.5, dur=0.3, settle=1.2)
    paste(cv, text_img('追赠太子太傅', SERIF, 44, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_haiguo(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='haifang')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    for i in range(int(clamp(u / (2 * P)) * 6) + 1):
        bundle(A, 440 + i * 50, GROUND - 74, 40, layer='yantu')
    A.flush(cv)
    ink_in(cv, text_img('海国图志', SERIF, 50, HAIFANG, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, dur=0.3)
    paste(cv, text_img('魏源据他所托 · 师夷长技以制夷', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_l_june3(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1200, W - 60, GROUND), fill=150)
    for k in range(6):
        q = (t * 0.3 + k / 6) % 1
        A.d['mid'].ellipse((300 + k * 80 - 30, lerp(1200, 800, q) - 20, 300 + k * 80 + 30, lerp(1200, 800, q) + 20), fill=int(160 * (1 - q)))
    ground(A, 1200)
    A.flush(cv)
    paste(cv, text_img('六月二十六日 · 国际禁毒日', SERIF, 46, HAIFANG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('销烟次日', 40, INK), 860, 1060, t, t - u + P, rot=6)

def art_l_legacy(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1380, W - 60, 1440), fill=150)
    fort(A, 860, 1380, 220, 2, t)

def art_l_title(A, cv, t, u):
    A.d['haifang'].rectangle((60, 1380, W - 60, 1460), fill=150)
    fort(A, 820, 1380, 300, 3, t)
    lin(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '福州少年'), 48: ('第二回', '钦差禁烟'), 80: ('第三回', '虎门销烟'),
            112: ('第四回', '鸦片战争'), 144: ('第五回', '苟利国家')}

CARDS = [
    C(0, 2, 'works', 'num', num='二十三天', line='销毁鸦片', art=art_l_hook_smoke),
    C(2, 4, 'empire', 'num', num='二百三十七万斤', line='全部入海', art=art_l_hook_237),
    C(4, 6, 'life', 'num', num='开眼看世界', line='第一人', art=art_l_hook_eye),
    C(6, 8, 'death', 'num', num='发配新疆', line='他没有怨言', art=art_l_hook_exile),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 福州少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1785, main='生于福州', sub='书香寒门', art=art_l_birth),
    C(22, 26, 'works', 'card', year=1804, main='中举', sub='少年得志', art=art_l_juren),
    C(26, 30, 'empire', 'card', year=1811, main='进士', sub='入翰林院', art=art_l_jinshi),
    C(30, 34, 'works', 'card', year=1814, main='翰林七年', sub='留心经世之学', art=art_l_hanlin),
    C(34, 38, 'night', 'card', year=1820, main='制怒', sub='性急 以此自警', art=art_l_motto),
    C(38, 44, 'works', 'card', year=1832, main='江苏巡抚', sub='林青天', art=art_l_jiangsu),
    C(44, 48, 'court', 'card', year=1837, main='湖广总督', sub='率先禁烟', art=art_l_huguang),
    # ---- 第二回 钦差禁烟
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'death', 'card', year=1838, main='烟毒', sub='吸食者数百万', art=art_l_opium),
    C(54, 58, 'works', 'card', year=1838, main='上书', sub='力陈鸦片之害', art=art_l_memorial),
    C(58, 62, 'empire', 'card', year=1838, main='钦差大臣', sub='节制广东水师', art=art_l_qinchai),
    C(62, 66, 'fate', 'card', year=1839, main='南下广州', sub='立下誓言', art=art_l_south),
    C(66, 72, 'war', 'card', year=1839, main='收缴鸦片', sub='包围商馆 · 断其供应', art=art_l_collect),
    C(72, 80, 'life', 'card', year=1839, main='无欲则刚', sub='他的自题联', note='一说 作于两广总督任上', art=art_l_tablet),
    # ---- 第三回 虎门销烟
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'works', 'humen', year=1839),
    C(90, 94, 'war', 'card', year=1839, main='整饬海防', sub='严阵以待', art=art_l_forts),
    C(94, 98, 'works', 'card', year=1839, main='译西书', sub='四洲志', art=art_l_translate),
    C(98, 104, 'empire', 'card', year=1839, main='开眼看世界', sub='主张了解西方', art=art_l_eye),
    C(104, 112, 'war', 'card', year=1839, main='九龙海战', sub='第一次交火', art=art_l_kowloon),
    # ---- 第四回 鸦片战争
    C(112, 114, 'war', 'chapter'),
    C(114, 122, 'war', 'card', year=1840, main='鸦片战争', sub='英军舰队北上', art=art_l_war),
    C(122, 126, 'night', 'card', year=1840, main='革职', sub='道光帝迁怒', art=art_l_dismissed),
    C(126, 130, 'death', 'card', year=1841, main='虎门失守', sub='将士殉国', art=art_l_humen_falls),
    C(130, 134, 'court', 'card', year=1841, main='镇海协防', sub='仍被问罪', art=art_l_zhenhai),
    C(134, 138, 'death', 'card', year=1842, main='南京条约', sub='第一个不平等条约', art=art_l_treaty),
    C(138, 144, 'fate', 'card', year=1842, main='发配伊犁', sub='赴戍登程口占示家人', art=art_l_xi),
    # ---- 第五回 苟利国家
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=1843, main='戍边伊犁', sub='万里之外', art=art_l_ili),
    C(150, 154, 'works', 'card', year=1845, main='屯田', sub='南疆勘垦', art=art_l_irrigate),
    C(154, 158, 'night', 'card', year=1845, main='忧俄', sub='最早的警告', note='一说 晚年所言', art=art_l_russia),
    C(158, 162, 'court', 'card', year=1845, main='赐还', sub='重新起用', art=art_l_recall),
    C(162, 166, 'death', 'card', year=1850, main='病逝', sub='年六十五', art=art_l_death),
    C(166, 168, 'empire', 'card', year=1850, main='谥文忠', sub='身后哀荣', art=art_l_wenzhong),
    C(168, 170, 'end', 'card', year=1852, main='海国图志', sub='他的遗志', art=art_l_haiguo),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾伍', col=HAIFANG, acc=YANTU, born=1785, died=1850, age0=1785.6,
    hook_q='他赢了禁烟 · 为什么输了战争？',
    name_line='林则徐 · 字元抚', name='林则徐', seal='文忠', title_art=art_l_title,
    q1='民族英雄？', q2='惹祸之臣？',
    end_art=art_l_legacy, end_big='苟利国家', end_seal='文忠',
    end_l1='他销毁的是鸦片', end_l2='点燃的是一个民族的觉醒',
    end_brush='岂因祸福避趋之', end_ask='你记得虎门销烟的日子吗？评论区聊聊', next='敬请期待'),
    scenes=dict(chapter=scene_chapter, humen=scene_humen))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
