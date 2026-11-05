"""千古人物志 · 第伍拾玖集 · 华佗 (约145–208)
Look: 药草绿 + 葫芦褐, 药葫芦 corner borders, a 药箱 chapter card: one herb drawer slides out per chapter (0→4)
and in the last chapter the book 青囊书 burns in a brazier.
Set pieces: 6-beat 采药, custom 8-beat scene 'mafei' (麻沸散 · 刳破腹背), 6-beat 五禽戏, 6-beat 刮骨疗毒 (演义),
6-beat 青囊之焚.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhangheng as Zh       # engine + helpers (previous episode)
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
from render_kongzi import slips, bundle
from render_songtaizu import tent
from render_quyuan import river

F.RIPPLE = False
YAOCAO = (84, 128, 72)              # 药草绿
HULU = (146, 98, 52)                # 葫芦褐
S.LAYERS.append(('yaocao', YAOCAO, 0.9, 1.0))
S.LAYERS.append(('hulu', HULU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='医', life='谯', court='魏', night='夜', war='刀', empire='医', works='药', fate='囊', death='囚', end='医')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (YAOCAO, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HULU, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

HERBS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(HERBS)
for _x in list(range(80, 300, 36)) + list(range(790, 1010, 36)):     # herb plants at the margins
    _h = 50 + (_x * 13) % 40
    _d.line((_x, 1460, _x, 1460 - _h), fill=(80, 110, 70, 60), width=3)
    for _k in range(3):
        _y = 1460 - _h + _k * 14
        _d.ellipse((_x - 12, _y - 5, _x, _y + 5), fill=(90, 130, 80, 50))
        _d.ellipse((_x, _y - 5, _x + 12, _y + 5), fill=(90, 130, 80, 50))
for _k in range(3):
    _d.line((60, 1475 + _k * 16, W - 60, 1475 + _k * 16), fill=HULU + (34,), width=2)
MTN_COL = {'night': (30, 36, 34), 'death': (62, 60, 58), 'war': (110, 64, 50), 'fate': (92, 100, 90)}
def draw_background(t, theme):
    """谯郡: green hills and medicinal herbs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 192, 180), (150, 166, 146), MTN_COL.get(theme, (102, 128, 98))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(HERBS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """药葫芦: a gourd tied with a red cord in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YAOCAO + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YAOCAO + (220,), width=3)
        cx, cy = x + sx * 54, y + sy * 58
        d.ellipse((cx - 16, cy - 30, cx + 16, cy + 2), fill=HULU + (230,))
        d.ellipse((cx - 26, cy - 4, cx + 26, cy + 44), fill=HULU + (230,))
        d.line((cx - 16, cy, cx + 16, cy), fill=ZHU + (230,), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def hua(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, gourd=True, **kw):
    """华佗: a wandering physician — simple cloth cap, long white-streaked beard, a gourd at the hip, a herb basket."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        A.d['yaocao'].chord((x - 0.08 * h, y - 1.04 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.6 * h)], fill=255)
        A.d['wash'].line((x + dir * 0.06 * h, y - 0.82 * h, x + dir * 0.07 * h, y - 0.64 * h), fill=255, width=max(2, int(0.01 * h)))
        if gourd:
            gx, gy = x - dir * 0.1 * h, y - 0.42 * h
            A.d['hulu'].ellipse((gx - 0.03 * h, gy - 0.07 * h, gx + 0.03 * h, gy - 0.01 * h), fill=255)
            A.d['hulu'].ellipse((gx - 0.045 * h, gy - 0.02 * h, gx + 0.045 * h, gy + 0.07 * h), fill=255)
    return hand

def caocao(A, x, y, h, dir=-1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)
    return hand

def patient(A, x, y, h, layer='mid', lying=True, **kw):
    if lying:
        A.d['mid'].rectangle((x - 0.6 * h, y - 0.06 * h, x + 0.6 * h, y + 0.06 * h), fill=230)
        return person(A, x, y - 0.06 * h, h, dir=1, robe=True, hat='knot', fall=-88, layer=layer, arm=-8, **kw)
    return person(A, x, y, h, dir=1, robe=True, hat='knot', layer=layer, **kw)

def herb_chest(A, cx, base, w, drawers_out, layer='hulu'):
    A.d[layer].rectangle((cx - w / 2, base - 0.9 * w, cx + w / 2, base), fill=255)
    rows, cols = 4, 4
    dw, dh = w / cols, 0.9 * w / rows
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            x0 = cx - w / 2 + c * dw; y0 = base - 0.9 * w + r * dh
            out = (i in drawers_out) * 0.35 * dw
            A.d['mid'].rectangle((x0 + 4, y0 + 4 + 0, x0 + dw - 4, y0 + dh - 4), fill=200)
            if out:
                A.d['yaocao'].rectangle((x0 + 4, y0 + dh * 0.55, x0 + dw - 4, y0 + dh * 0.55 + out * 0.6), fill=255)
            A.d['ink'].ellipse((x0 + dw / 2 - 4, y0 + dh / 2 - 4, x0 + dw / 2 + 4, y0 + dh / 2 + 4), fill=255)

def animal(A, kind, x, y, s, t):
    d = A.d['yaocao' if kind in ('鹿', '鸟') else 'hulu' if kind in ('虎', '熊') else 'ink']
    if kind == '虎':
        d.ellipse((x - s, y - 0.5 * s, x + s, y), fill=255); d.ellipse((x + 0.7 * s, y - 0.75 * s, x + 1.2 * s, y - 0.25 * s), fill=255)
        for k in range(4):
            A.d['ink'].line((x - 0.6 * s + k * 0.35 * s, y - 0.48 * s, x - 0.5 * s + k * 0.35 * s, y - 0.1 * s), fill=255, width=3)
    elif kind == '鹿':
        d.ellipse((x - s, y - 0.5 * s, x + s, y - 0.1 * s), fill=255); d.line((x + 0.8 * s, y - 0.4 * s, x + 1.1 * s, y - 1.0 * s), fill=255, width=6)
        d.line((x + 1.1 * s, y - 1.0 * s, x + 1.3 * s, y - 1.3 * s), fill=255, width=3); d.line((x + 1.1 * s, y - 1.0 * s, x + 0.9 * s, y - 1.3 * s), fill=255, width=3)
    elif kind == '熊':
        d.ellipse((x - s, y - 0.8 * s, x + s, y), fill=255); d.ellipse((x + 0.6 * s, y - 1.0 * s, x + 1.1 * s, y - 0.5 * s), fill=255)
    elif kind == '猿':
        d.ellipse((x - 0.4 * s, y - 1.2 * s, x + 0.4 * s, y - 0.4 * s), fill=255); d.ellipse((x - 0.25 * s, y - 1.5 * s, x + 0.25 * s, y - 1.1 * s), fill=255)
        d.line((x + 0.3 * s, y - 1.0 * s, x + 0.9 * s, y - 1.6 * s + 0.2 * s * math.sin(t * 5)), fill=255, width=6)
    else:
        d.ellipse((x - 0.5 * s, y - 0.3 * s, x + 0.5 * s, y + 0.1 * s), fill=255)
        f = math.sin(t * 8)
        d.polygon([(x - 0.2 * s, y - 0.1 * s), (x + 0.2 * s, y - 0.1 * s), (x, y - 0.9 * s * f - 0.2 * s)], fill=255)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
DRAWERS = [5, 10, 3, 14]
def art_chest_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    n = b if q > 0.5 else a
    if kb == 144:
        herb_chest(A, 380, 1220, 260, DRAWERS)
        A.d['ink'].polygon([(640, 1220), (840, 1220), (810, 1140), (670, 1140)], fill=255)
        flames(A, 740, 1140, 180, 180 * q, t, n=4, seed=208, smoke=True)
    else:
        herb_chest(A, 540, 1220, 320, DRAWERS[:n])

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_chest_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YAOCAO, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_t_hook_knife(A, cv, t, u):
    ground(A, GROUND)
    patient(A, 540, GROUND - 120, 220)
    A.d['wash'].line((440, GROUND - 260, 520, GROUND - 200), fill=255, width=6)

def art_t_hook_animals(A, cv, t, u):
    ground(A, GROUND)
    ks = ['虎', '鹿', '熊', '猿', '鸟']
    n = min(5, int(clamp(u / (1.4 * P)) * 5) + 1)
    for i in range(n):
        animal(A, ks[i], 160 + i * 190, GROUND, 60, t)

def art_t_hook_cao(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 540, GROUND, 220, dir=1, arm=lerp(20, 150, ease_out(u / P)))

def art_t_hook_fire(A, cv, t, u):
    ground(A, GROUND)
    bundle(A, 540, GROUND, 120, layer='hulu')
    flames(A, 540, GROUND, 260, 240 * ease_out(u / P), t, n=5, seed=59, smoke=True)

# ================================================================ 第一回 谯郡布衣
def art_t_birth(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    A.d['mid'].rectangle((380, 1100, 700, 1240), fill=220)
    A.d['ink'].polygon([(340, 1100), (740, 1100), (540, 1000)], fill=255)
    A.flush(cv)
    paste(cv, text_img('沛国谯县 · 与曹操同乡', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('谯县', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='yaocao')
    hua(A, 300, GROUND, 170, dir=1, kneel=True, bow=20, arm=90, gourd=False)
    slips(A, 440, GROUND - 74, int(clamp(u / (2 * P)) * 8) + 1, 90, layer='hulu')
    A.flush(cv)
    paste(cv, text_img('游学徐土 · 兼通数经', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_refuse(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(20, 120, ease_out(u / 0.5)), layer='ink')
    hua(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('举孝廉 辟太尉 皆不就', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_herbs(A, cv, t, u):
    """6-beat set piece: 采药 — climbing mountains with a basket; picking, drying on racks, grinding."""
    ph = u / P
    if ph < 3:
        for k in range(3):
            x = 240 + k * 300
            A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - 440), (x + 260, GROUND)], fill=180)
        ground(A, GROUND)
        x = lerp(160, 520, clamp(ph / 3))
        hua(A, x, GROUND - 300 * clamp(ph / 3), 150, dir=1, ph=t * 3, arm=150, bow=30)
        for j in range(5):
            A.d['yaocao'].ellipse((300 + j * 90 - 16, GROUND - 120 - j * 50 - 16, 300 + j * 90 + 16, GROUND - 120 - j * 50 + 16), fill=220)
        lab = '入山采药'
    else:
        ground(A, GROUND)
        for r in range(3):
            A.d['ink'].line((200, GROUND - 120 - r * 70, 880, GROUND - 120 - r * 70), fill=255, width=4)
            for j in range(8):
                A.d['yaocao' if (r + j) % 2 else 'hulu'].ellipse((230 + j * 82 - 20, GROUND - 130 - r * 70, 230 + j * 82 + 20, GROUND - 110 - r * 70), fill=230)
        hua(A, 120, GROUND, 160, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
        lab = '晾晒 · 研磨 · 识百草'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, YAOCAO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph % 3) / 0.4))

def art_t_wander(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    hua(A, lerp(120, 840, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('行医于徐州 豫州 青州 兖州', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_twins(A, cv, t, u):
    ground(A, GROUND)
    hua(A, 540, GROUND, 190, dir=1, arm=60)
    for i in range(2):
        person(A, 300 + i * 480, GROUND, 160, dir=1 if i == 0 else -1, robe=True, hat='knot', bow=25, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='mid' if i else 'hulu')
    A.flush(cv)
    paste(cv, text_img('二人同患头痛身热 · 一下之 一发汗', SERIF, 42, YAOCAO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('同病异治', 44), 860, 1020, t, t - u + P, rot=6)

def art_t_snake(A, cv, t, u):
    ground(A, GROUND)
    person(A, 400, GROUND, 180, dir=1, robe=True, hat='knot', bow=40, arm=lerp(-8, 80, ease_out(u / 0.6)), layer='mid')
    q = ease_out((u - P) / P)
    pts = [(460 + k * 20, GROUND - 40 + 12 * math.sin(k * 0.8 + t * 4)) for k in range(int(12 * q) + 2)]
    A.d['ink'].line(pts, fill=255, width=8)
    hua(A, 760, GROUND, 180, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('以蒜齑大酢三升饮之 · 吐出一虫', SERIF, 44, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见三国志方技传 当为寄生虫', t, t - u + P)

# ================================================================ 第二回 麻沸散
def art_t_wine(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='hulu')
    for i in range(3):
        A.d['hulu'].ellipse((420 + i * 90 - 30, GROUND - 160, 420 + i * 90 + 30, GROUND - 80), fill=255)
        A.d['hulu'].rectangle((420 + i * 90 - 10, GROUND - 180, 420 + i * 90 + 10, GROUND - 150), fill=255)
    hua(A, 220, GROUND, 180, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('以酒服麻沸散 · 既醉无所觉', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('麻醉', 56), 860, 1020, t, t - u + P, rot=6)

def scene_mafei(cv, t, c, k):
    """8-beat custom scene: 麻沸散 — the patient drinks; slowly falls asleep; the incision; the illness is cut out; stitched;
    a salve applied; four or five days, then the patient sits up."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    lamp(A, 940, GROUND, 60, t, glow=0.8)
    if ph < 2:
        patient(A, 520, GROUND, 180, lying=False, kneel=True, arm=lerp(60, 120, clamp(ph / 0.6)))
        A.d['hulu'].ellipse((600, GROUND - 160, 640, GROUND - 120), fill=255)
        hua(A, 280, GROUND, 190, dir=1, arm=60)
        lab = '先令以酒服麻沸散'
    elif ph < 6:
        patient(A, 560, GROUND - 120, 220)
        A.d['mid'].rectangle((300, GROUND - 120, 820, GROUND), fill=150)
        hua(A, 260, GROUND, 190, dir=1, bow=30, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 6)))
        cut = clamp((ph - 2.5) / 1)
        A.d['red'].line((500, GROUND - 140, 500 + 120 * cut, GROUND - 140), fill=255, width=4)
        if ph > 4.5:
            for kk in range(5):
                A.d['ink'].line((510 + kk * 22, GROUND - 150, 510 + kk * 22, GROUND - 130), fill=255, width=3)
        lab = '醉无所觉 · 因刳破腹背' if ph < 4.5 else '既而缝合 · 傅以神膏'
    else:
        patient(A, 540, GROUND, 190, lying=False, arm=lerp(-8, 120, clamp((ph - 6.5) / 0.4)))
        hua(A, 280, GROUND, 190, dir=1, arm=40)
        lab = '四五日差 · 一月之间皆平复'
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '麻沸散', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=59)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2 <= ph < 6 else YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('比西方麻醉术早一千六百余年', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 6.5) / 0.4))
    note_in(cv, '麻沸散方已失传', t, s0 + 3 * P)

def art_t_chenden(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='crown', bow=lerp(0, 40, ease_out(u / P)), arm=lerp(-8, 100, ease_out(u / P)), layer='mid')
    A.d['red'].ellipse((600, GROUND - 60, 680, GROUND - 20), fill=200)
    hua(A, 820, GROUND, 180, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('广陵太守陈登 · 好食生鱼脍', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('陈登', 56), 260, 1020, t, t - u + P, rot=-5)

def art_t_threeyears(A, cv, t, u):
    for k in range(3):
        A.d['wash'].rectangle((240 + k * 230, 940, 420 + k * 230, 1200), fill=230)
        A.d['ink'].rectangle((240 + k * 230, 940, 420 + k * 230, 1200), outline=255, width=4)
    ground(A, GROUND)
    A.flush(cv)
    n = min(3, int(u / P) + 1)
    for i in range(n):
        paste(cv, text_img(f'第{cn_num(i + 1)}年', SERIF, 40, ZHU if i == 2 else INK, 'Black', bleed=False, spacing=4), 330 + i * 230, 1070, 1, clamp((u - i * P) / 0.3))
    paste(cv, text_img('此病后三期当发 · 遇良医乃可济救', SERIF, 42, YAOCAO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_t_dengdies(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 220, dir=1, robe=True, hat='crown', fall=-88, arm=-8, layer='mid')
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('三年果发 · 时佗不在 如言而死', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_pregnant(A, cv, t, u):
    ground(A, GROUND)
    person(A, 400, GROUND, 180, dir=1, robe=True, hat='knot', female=True, bow=20, arm=40, layer='hulu')
    hua(A, 680, GROUND, 190, dir=-1, arm=lerp(40, 100, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('诊脉 · 知腹中死胎在左', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('切脉', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_acupuncture(A, cv, t, u):
    ground(A, GROUND)
    patient(A, 560, GROUND - 120, 220)
    A.d['mid'].rectangle((300, GROUND - 120, 820, GROUND), fill=150)
    n = min(6, int(clamp(u / (2 * P)) * 6) + 1)
    for i in range(n):
        x = 460 + i * 40
        A.d['wash'].line((x, GROUND - 200, x, GROUND - 150), fill=255, width=3)
    hua(A, 220, GROUND, 190, dir=1, bow=20, arm=100)
    A.flush(cv)
    paste(cv, text_img('针灸不过一两处 · 下针言当引某许', SERIF, 42, YAOCAO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 五禽戏
def art_t_wuqin(A, cv, t, u):
    """6-beat set piece: 五禽戏 — the physician mimics tiger, deer, bear, ape, bird in turn; each animal appears beside him."""
    ph = u / P
    ks = [('虎', 0), ('鹿', 1), ('熊', 2), ('猿', 3), ('鸟', 4)]
    k = min(4, int(ph / 1.15))
    ground(A, GROUND)
    nm, _ = ks[k]
    poses = [dict(kneel=True, bow=40, arm=150), dict(bow=-10, arm=170), dict(bow=30, arm=60), dict(arm=170), dict(arm=lerp(90, 170, 0.5 + 0.5 * math.sin(t * 6)))]
    hua(A, 360, GROUND, 200, dir=1, gourd=False, **poses[k])
    animal(A, nm, 720, GROUND, 80, t)
    A.flush(cv)
    stamp(cv, seal(nm, 60, ZHU), 860, 1020, t, t - u + k * 1.15 * P)
    paste(cv, text_img(f'五禽之戏 · 一曰{nm}', SERIF, 48, YAOCAO, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp((ph - k * 1.15) / 0.3))
    paste(cv, text_img('人体欲得劳动 但不当使极尔', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((ph - 1) / 0.4))

def art_t_wupu(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='knot', arm=lerp(40, 170, 0.5 + 0.5 * math.sin(t * 2)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('弟子吴普行之 · 年九十余 耳目聪明', SERIF, 42, YAOCAO, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('吴普', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_fanah(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='yaocao')
    sitter(A, 300, GROUND, 170, dir=1, bow=20, layer='mid')
    for i in range(int(clamp(u / (2 * P)) * 6) + 1):
        A.d['yaocao'].ellipse((440 + i * 40 - 16, GROUND - 100, 440 + i * 40 + 16, GROUND - 74), fill=255)
    A.flush(cv)
    paste(cv, text_img('弟子樊阿 · 善针术 背入一二寸', SERIF, 44, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('樊阿', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_kitchen(A, cv, t, u):
    ground(A, GROUND)
    for i in range(3):
        A.d['hulu'].ellipse((300 + i * 160 - 50, GROUND - 120, 300 + i * 160 + 50, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('漆叶青黏散 · 久服去三虫 利五脏', SERIF, 44, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_guanyu(A, cv, t, u):
    """6-beat set piece: 刮骨疗毒 — the general plays weiqi and drinks while the bone is scraped; this story is from the novel."""
    ph = u / P
    tent(A, 540, GROUND, 720, 420, layer='mid')
    ground(A, GROUND)
    desk(A, 640, GROUND, 260, layer='ink')
    for i in range(9):
        A.d['wash' if i % 2 else 'ink'].ellipse((560 + (i % 3) * 30 - 10, GROUND - 90 - (i // 3) * 12, 560 + (i % 3) * 30 + 10, GROUND - 78 - (i // 3) * 12), fill=255)
    person(A, 460, GROUND, 230, dir=1, robe=False, hat='helmet', kneel=True, arm=110, layer='red')
    hua(A, 280, GROUND, 180, dir=1, bow=20, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 8)))
    A.flush(cv)
    lab = '刮骨去毒 · 悉悉有声' if ph < 3 else '公饮酒食肉 谈笑弈棋 全无痛苦之色'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 3 else YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '三国演义情节 史载刮骨者为他医 非华佗', t, t - u + 0.5 * P)

def art_t_physician(A, cv, t, u):
    for k in range(3):
        A.d['yaocao'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    hua(A, 540, GROUND - 180, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('精于方药 · 处齐不过数种', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 头风
def art_t_cao_ill(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 540, GROUND, 220, dir=1, bow=lerp(0, 25, 0.5 + 0.5 * math.sin(t * 3)), arm=170)
    A.flush(cv)
    paste(cv, text_img('曹操苦头风 · 每发 心乱目眩', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_needle(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 600, GROUND, 200, dir=1, kneel=True, arm=40)
    A.d['wash'].line((640, GROUND - 200, 680, GROUND - 240), fill=255, width=3)
    hua(A, 360, GROUND, 190, dir=1, arm=100)
    A.flush(cv)
    paste(cv, text_img('佗针鬲 随手而差', SERIF, 48, YAOCAO, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('侍医', 56), 860, 1020, t, t - u + P, rot=6)

def art_t_wife(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    hua(A, lerp(540, 900, ease_out(u / (2.5 * P))), GROUND, 180, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('以妻病为由 · 告假还乡 数期不反', SERIF, 44, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_beans(A, cv, t, u):
    A.d['mid'].rectangle((620, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(600, GROUND - 200), (920, GROUND - 200), (760, GROUND - 280)], fill=255)
    ground(A, GROUND)
    person(A, 400, GROUND, 180, dir=1, robe=False, hat='helmet', arm=lerp(40, 120, ease_out(u / 0.5)), layer='ink')
    for i in range(int(clamp(u / (2 * P)) * 8)):
        A.d['hulu'].ellipse((480 + (i % 4) * 26 - 10, GROUND - 20 - (i // 4) * 20, 480 + (i % 4) * 26 + 10, GROUND - (i // 4) * 20), fill=255)
    A.flush(cv)
    paste(cv, text_img('曹操遣人往检 · 妻果诈疾', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '赐小豆四十斛 宽假限日 若虚诈 便收送之', t, t - u + P)

def art_t_jail(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    hua(A, 540, GROUND, 180, dir=1, kneel=True, bow=30, arm=-8, gourd=False, old=0.6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('传付许狱 · 考验首服', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('许昌', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_t_xunyu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    caocao(A, 760, GROUND - 30, 200, dir=-1, arm=lerp(20, 160, ease_out((u - P) / 0.4)))
    person(A, 400, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=110, layer='hulu')
    A.flush(cv)
    type_in(cv, text_img('佗术实工 人命所县 宜含宥之', SERIF, 44, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('不忧 天下当无此鼠辈耶', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('荀令君', 50, INK), 260, 1020, t, t - u + 0.4, rot=-5)

def art_t_qingnang(A, cv, t, u):
    """6-beat set piece: 青囊之焚 — in the cell he hands the book to the jailer; the jailer dare not take it; he burns it himself."""
    ph = u / P
    A.d['ink'].rectangle((200, 880, 880, GROUND), outline=255, width=8)
    for k in range(13):
        A.d['ink'].line((200 + k * 56, 880, 200 + k * 56, GROUND), fill=150, width=3)
    ground(A, GROUND)
    hua(A, 380, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 120, clamp(ph / 0.6)), gourd=False, old=0.8)
    person(A, 720, GROUND, 180, dir=-1, robe=False, hat='helmet', arm=lerp(60, -8, clamp((ph - 2) / 0.6)), bow=20 if ph > 2 else 0, layer='mid')
    bx = 520
    if ph < 3.4:
        bundle(A, bx, GROUND - 40, 70, layer='yaocao')
    else:
        bundle(A, bx, GROUND - 10, 70, layer='yaocao')
        flames(A, bx, GROUND, 180, 200 * ease_out((ph - 3.4) / 0.8), t, n=4, seed=591, smoke=True)
    A.flush(cv)
    lab = '出一卷书与狱吏 · 此可以活人' if ph < 2 else ('吏畏法不受' if ph < 3.4 else '佗亦不强 · 索火烧之')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.4 else YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '青囊书之名出自三国演义', t, t - u + 3.4 * P)

# ================================================================ 第五回 医者
def art_t_death(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    ground(A, GROUND)
    lamp(A, 540, GROUND, 60, t, glow=clamp(1 - u / (1.5 * P)))
    A.flush(cv)
    paste(cv, text_img('华佗死于狱中', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年一说二〇八年 一说二〇七年', t, t - u + P)

def art_t_cangshu(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    person(A, 540, 1200, 160, dir=1, robe=True, hat='knot', fall=-88, arm=-8, layer='hulu')
    caocao(A, 860, GROUND, 200, dir=-1, kneel=True, bow=40, arm=100)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('吾悔杀华佗 令此儿强死也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('曹冲', 56, INK), 260, 1020, t, t - u + P, rot=-5)

def art_t_wuqin_today(A, cv, t, u):
    ground(A, GROUND)
    for j in range(6):
        person(A, 160 + j * 150, GROUND, 140, dir=1, robe=True, hat='knot', arm=lerp(90, 170, 0.5 + 0.5 * math.sin(t * 2 + j)), kneel=(int(t) + j) % 3 == 0, layer='yaocao' if j % 2 else 'ink')
    A.flush(cv)
    paste(cv, text_img('五禽戏 · 至今仍在练习', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_waike(A, cv, t, u):
    for k in range(3):
        A.d['hulu'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    hua(A, 540, GROUND - 180, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('外科鼻祖', SERIF, 52, YAOCAO, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_t_plaque(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='yaocao')
    ground(A, GROUND)
    A.d['hulu'].rectangle((400, 1120, 680, 1170), fill=255)
    A.flush(cv)
    paste(cv, text_img('华佗再世 · 民间赠医的最高赞誉', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_bozhou(A, cv, t, u):
    for j in range(12):
        x = 120 + j * 76
        A.d['yaocao'].ellipse((x - 26, GROUND - 60, x + 26, GROUND - 10), fill=220)
        A.d['ink'].line((x, GROUND - 10, x, GROUND), fill=200, width=3)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('故乡亳州 · 今为中华药都', SERIF, 46, YAOCAO, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_t_heal(A, cv, t, u):
    ground(A, GROUND)
    hua(A, 420, GROUND, 200, dir=1, arm=60)
    person(A, 660, GROUND, 180, dir=-1, robe=True, hat='knot', arm=lerp(-8, 120, ease_out(u / 0.6)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('此可以活人', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_t_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    herb_chest(A, 860, 1380, 110, [2, 7])

def art_t_title(A, cv, t, u):
    herb_chest(A, 820, 1460, 260, [5, 10])
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    hua(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '谯郡布衣'), 48: ('第二回', '麻沸散'), 80: ('第三回', '五禽戏'),
            112: ('第四回', '头风'), 144: ('第五回', '医者')}

CARDS = [
    C(0, 2, 'war', 'num', num='一千六百年前', line='他就开腹手术', art=art_t_hook_knife),
    C(2, 4, 'life', 'num', num='五种动物', line='一套健身操', art=art_t_hook_animals),
    C(4, 6, 'death', 'num', num='曹操的头痛', line='要了他的命', art=art_t_hook_cao),
    C(6, 8, 'night', 'num', num='一卷医书', line='付之一炬', art=art_t_hook_fire),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 谯郡布衣
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=145, main='生于谯县', sub='曹操同乡', note='生年约在一四五年', art=art_t_birth),
    C(22, 26, 'works', 'card', year=160, main='游学徐土', sub='通数经', art=art_t_study),
    C(26, 30, 'fate', 'card', year=168, main='辟举不就', sub='不愿做官', art=art_t_refuse),
    C(30, 36, 'works', 'card', year=170, main='采药', sub='识百草', art=art_t_herbs),
    C(36, 40, 'fate', 'card', year=175, main='行医四方', sub='游走民间', art=art_t_wander),
    C(40, 44, 'court', 'card', year=180, main='同病异治', sub='辨证施治', art=art_t_twins),
    C(44, 48, 'night', 'card', year=182, main='吐虫', sub='奇症', art=art_t_snake),
    # ---- 第二回 麻沸散
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'works', 'card', year=185, main='酒服麻药', sub='世界最早的麻醉', art=art_t_wine),
    C(54, 62, 'war', 'mafei', year=186),
    C(62, 66, 'court', 'card', year=196, main='陈登之病', sub='生鱼脍', art=art_t_chenden),
    C(66, 70, 'night', 'card', year=196, main='三年之期', sub='一语成谶', art=art_t_threeyears),
    C(70, 74, 'death', 'card', year=199, main='陈登病逝', sub='果如其言', art=art_t_dengdies),
    C(74, 78, 'life', 'card', year=199, main='切脉', sub='神乎其技', art=art_t_pregnant),
    C(78, 80, 'works', 'card', year=200, main='针灸', sub='一两处', art=art_t_acupuncture),
    # ---- 第三回 五禽戏
    C(80, 82, 'life', 'chapter'),
    C(82, 88, 'life', 'card', year=200, main='五禽戏', sub='虎鹿熊猿鸟', art=art_t_wuqin),
    C(88, 92, 'empire', 'card', year=200, main='弟子吴普', sub='九十耳目聪明', art=art_t_wupu),
    C(92, 96, 'works', 'card', year=201, main='弟子樊阿', sub='善针', art=art_t_fanah),
    C(96, 100, 'court', 'card', year=201, main='漆叶青黏', sub='养生方', art=art_t_kitchen),
    C(100, 106, 'war', 'card', year=202, main='刮骨疗毒', sub='小说家言', art=art_t_guanyu),
    C(106, 112, 'empire', 'card', year=203, main='精于方药', sub='用药精简', art=art_t_physician),
    # ---- 第四回 头风
    C(112, 114, 'death', 'chapter'),
    C(114, 118, 'night', 'card', year=204, main='曹操头风', sub='心乱目眩', art=art_t_cao_ill),
    C(118, 122, 'court', 'card', year=204, main='针到病除', sub='被留为侍医', art=art_t_needle),
    C(122, 126, 'fate', 'card', year=206, main='告假还乡', sub='不愿侍奉', art=art_t_wife),
    C(126, 130, 'death', 'card', year=207, main='诈病被查', sub='欺君之罪', art=art_t_beans),
    C(130, 134, 'night', 'card', year=207, main='下狱', sub='许昌', art=art_t_jail),
    C(134, 138, 'court', 'card', year=208, main='重臣求情', sub='曹操不许', art=art_t_xunyu),
    C(138, 144, 'fate', 'card', year=208, main='焚书', sub='医术失传', art=art_t_qingnang),
    # ---- 第五回 医者
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=208, main='死于狱中', sub='一代神医', art=art_t_death),
    C(150, 154, 'night', 'card', year=208, main='曹冲之死', sub='悔之晚矣', art=art_t_cangshu),
    C(154, 158, 'life', 'card', year=2011, main='五禽戏', sub='非遗', art=art_t_wuqin_today),
    C(158, 162, 'empire', 'card', year=2011, main='外科鼻祖', sub='后世尊称', art=art_t_waike),
    C(162, 166, 'court', 'card', year=2011, main='华佗再世', sub='一句赞誉', art=art_t_plaque),
    C(166, 168, 'works', 'card', year=2011, main='亳州药都', sub='故乡', art=art_t_bozhou),
    C(168, 170, 'end', 'card', year=2011, main='医者仁心', sub='活人之术', art=art_t_heal),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾玖', col=YAOCAO, acc=HULU, born=145, died=208, age0=145,
    born_lab='约145年', died_lab='208年', years_txt='约公元145 — 208',
    hook_q='他能治好曹操的头痛 · 为什么却被曹操杀了？',
    name_line='华佗 · 字元化', name='华佗', seal='神医', title_art=art_t_title,
    q1='一代神医？', q2='恃才傲物？',
    end_art=art_t_legacy, end_big='医者仁心', end_seal='神医',
    end_l1='他治好了无数人的病', end_l2='却没能逃过一个人的猜忌',
    end_brush='此可以活人', end_ask='如果青囊书没被烧 中医会怎样？评论区聊聊', next='关羽'),
    scenes=dict(chapter=scene_chapter, mafei=scene_mafei))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
