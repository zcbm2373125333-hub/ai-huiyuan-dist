"""千古人物志 · 第伍拾柒集 · 王昭君 (生卒年不详 · 前33年出塞)
Look: 胭脂红 + 胡天蓝, 琵琶 corner borders, a 琵琶 chapter card: one string is strung per chapter (1→4) and in the
last chapter the pipa lies on a green grave mound.
Set pieces: 6-beat 画工, 6-beat 辞行 (光明汉宫), custom 8-beat scene 'chusai' (出塞 · 落雁), 6-beat 塞外四季,
6-beat 边城晏闭.
Birth and death years are unknown: the HUD hides ages (no_age) and the life bar spans 前52–前19 only for scale.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_liuxiu as Lx          # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_quyuan import river
from render_zhangqian import yurt

F.RIPPLE = False
YANZHI = (186, 64, 86)              # 胭脂红
HUTIAN = (80, 112, 150)             # 胡天蓝
S.LAYERS.append(('yanzhi', YANZHI, 0.9, 1.0))
S.LAYERS.append(('hutian', HUTIAN, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='塞', life='嫱', court='汉', night='月', war='胡', empire='宁', works='琶', fate='雁', death='冢', end='塞')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (YANZHI, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (HUTIAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YANZHI, 180, (W * 0.5, 720))
G.base_bg.cache_clear()

STEPPE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STEPPE)
for _k in range(4):                 # 草原 grass lines
    _y = 1450 + _k * 20
    _d.line([(60 + i * 30, _y + 4 * math.sin(i * 0.9 + _k)) for i in range(34)], fill=(100, 130, 90, 44), width=3)
for _x in (130, 950):               # yurts at the margins
    _d.chord((_x - 50, 1360, _x + 50, 1440), 180, 360, fill=(170, 160, 140, 60))
    _d.rectangle((_x - 50, 1400, _x + 50, 1440), fill=(170, 160, 140, 60))
MTN_COL = {'night': (30, 34, 50), 'death': (62, 62, 66), 'war': (110, 70, 60), 'fate': (96, 104, 120)}
def draw_background(t, theme):
    """塞外: snow-capped ridges, grass lines and felt yurts at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 192, 196), (160, 168, 180), MTN_COL.get(theme, (112, 126, 146))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STEPPE)
    return canvas
G.draw_background = draw_background

def _pipa(d, cx, cy, s, sx, sy, col):
    d.ellipse((cx - 0.5 * s, cy - 0.45 * s, cx + 0.5 * s, cy + 0.55 * s), fill=col)
    d.line((cx, cy - 0.4 * s, cx + sx * 0.35 * s, cy - sy * 1.1 * s), fill=col, width=max(3, int(0.12 * s)))
    d.line((cx + sx * 0.32 * s, cy - sy * 1.1 * s, cx + sx * 0.5 * s, cy - sy * 1.2 * s), fill=col, width=max(3, int(0.1 * s)))

def draw_frame_border(canvas):
    """琵琶: a small pipa in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=HUTIAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=HUTIAN + (220,), width=3)
        _pipa(d, x + sx * 50, y + sy * 80, 46, sx, sy, YANZHI + (220,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhaojun(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, pipa=False, cloak=True, **kw):
    """王昭君: fur-trimmed 昭君套 hood, long red cloak, often holding a pipa."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', female=True, layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        A.d['yanzhi'].chord((x - 0.11 * h, y - 1.04 * h, x + 0.11 * h, y - 0.86 * h), 180, 360, fill=255)
        A.d['wash'].rectangle((x - 0.11 * h, y - 0.96 * h, x + 0.11 * h, y - 0.93 * h), fill=255)
        if cloak:
            A.d['yanzhi'].polygon([(x - dir * 0.06 * h, y - 0.82 * h), (x - dir * 0.3 * h, y - 0.02 * h), (x - dir * 0.04 * h, y - 0.06 * h)], fill=255)
        if pipa:
            px, py = x + dir * 0.12 * h, y - 0.56 * h
            A.d['hutian'].ellipse((px - 0.09 * h, py - 0.06 * h, px + 0.09 * h, py + 0.12 * h), fill=255)
            A.d['ink'].line((px, py - 0.04 * h, px + dir * 0.06 * h, py - 0.26 * h), fill=255, width=max(2, int(0.02 * h)))
    return hand

def emperor(A, x, y, h, dir=-1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d['ink'].rectangle((x - 0.14 * h, y - 1.06 * h, x + 0.14 * h, y - 1.02 * h), fill=255)
    return hand

def chanyu(A, x, y, h, dir=-1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=False, hat='none', layer=layer, **kw)
    if not kw.get('fall') and not kw.get('kneel'):
        A.d[layer].chord((x - 0.12 * h, y - 1.06 * h, x + 0.12 * h, y - 0.88 * h), 180, 360, fill=255)
        A.d['wash'].rectangle((x - 0.13 * h, y - 0.94 * h, x + 0.13 * h, y - 0.9 * h), fill=255)
    return hand

def pipa_big(A, cx, cy, s, strings=4, layer='hutian'):
    A.d[layer].ellipse((cx - 0.5 * s, cy - 0.45 * s, cx + 0.5 * s, cy + 0.6 * s), fill=255)
    A.d['ink'].line((cx, cy - 0.4 * s, cx, cy - 1.5 * s), fill=255, width=max(4, int(0.08 * s)))
    A.d['ink'].polygon([(cx - 0.08 * s, cy - 1.5 * s), (cx + 0.08 * s, cy - 1.5 * s), (cx + 0.14 * s, cy - 1.75 * s), (cx - 0.04 * s, cy - 1.75 * s)], fill=255)
    for k in range(4):
        A.d['ink'].line((cx - 0.06 * s, cy - 1.45 * s + k * 0.08 * s, cx - 0.16 * s, cy - 1.45 * s + k * 0.08 * s), fill=255, width=4)
    for k in range(strings):
        xx = cx - 0.09 * s + k * 0.06 * s
        A.d['wash'].line((xx, cy - 1.45 * s, xx, cy + 0.45 * s), fill=255, width=2)

def goose(A, x, y, s, t, fall=0.0):
    f = math.sin(t * 6) * (1 - fall)
    A.d['ink'].ellipse((x - s, y - 0.25 * s, x + s, y + 0.25 * s), fill=255)
    A.d['ink'].line((x + s, y, x + 1.5 * s, y - 0.2 * s), fill=255, width=max(2, int(0.15 * s)))
    A.d['ink'].polygon([(x - 0.3 * s, y), (x + 0.3 * s, y), (x - 0.1 * s, y - 1.3 * s * f - 0.2 * s)], fill=255)

# ================================================================ chapter card
CH = {16: 1, 48: 2, 80: 3, 112: 4, 144: 5}
def art_pipa_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    st = CH.get(kb, 2)
    q = ease_out(u / (1.2 * P))
    if st < 5:
        pipa_big(A, 540, 1120, 200, strings=st if q > 0.6 else st - 1)
    else:
        A.d['grass'].chord((300, 1080, 780, 1340), 180, 360, fill=230)
        A.d['hutian'].ellipse((480, 1110, 600, 1170), fill=int(255 * q))
        A.d['ink'].line((560, 1130, 680, 1090), fill=int(255 * q), width=6)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_pipa_chapter)
    ink_in(cv, text_img(no, SERIF, 56, HUTIAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_pipa(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(160, 620, ease_out(u / (1.6 * P)))
    horse(A, x, GROUND, 170, dir=1, ph=t * 4)
    zhaojun(A, x - 10, GROUND - 112, 130, dir=1, pipa=True, arm=60)

def art_z_hook_peace(A, cv, t, u):
    ground(A, GROUND)
    zhaojun(A, 540, GROUND, 220, dir=1, arm=-8)
    n = int(clamp(u / (1.4 * P)) * 12) + 1
    for i in range(n):
        A.d['grass'].ellipse((120 + i * 70 - 20, GROUND - 30, 120 + i * 70 + 20, GROUND), fill=220)

def art_z_hook_goose(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        q = clamp(u / (1.6 * P))
        goose(A, 300 + j * 140, lerp(900, 1100, q) + j * 20, 30, t + j, fall=q)

def art_z_hook_tomb(A, cv, t, u):
    A.d['grass'].chord((320, 1080, 760, 1340), 180, 360, fill=230)
    ground(A, GROUND)
    A.d['red'].ellipse((820, 820, 900, 900), fill=int(200 * ease_out(u / P)))

# ================================================================ 第一回 秭归女儿
def art_z_birth(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    A.d['mid'].rectangle((380, 1100, 700, 1240), fill=220)
    A.d['ink'].polygon([(340, 1100), (740, 1100), (540, 1000)], fill=255)
    for k in range(3):
        A.d['grass'].polygon([(120 + k * 60, 1240), (150 + k * 60, 1080), (180 + k * 60, 1240)], fill=200)
    A.flush(cv)
    paste(cv, text_img('南郡秭归 · 香溪之畔', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秭归', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_girl(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=3)
    zhaojun(A, 540, 1260, 180, dir=1, bow=30, arm=lerp(120, 160, 0.5 + 0.5 * math.sin(t * 3)), cloak=False)
    A.flush(cv)
    paste(cv, text_img('良家子 · 名嫱 字昭君', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_select(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='yanzhi')
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 8) + 1
    for i in range(n):
        person(A, 160 + i * 100, GROUND, 120, dir=1, robe=True, hat='knot', female=True, arm=30, layer='mid' if i != 3 else 'ink')
    A.flush(cv)
    paste(cv, text_img('元帝时 · 以良家子选入掖庭', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('掖庭', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_painter(A, cv, t, u):
    """6-beat set piece: 画工 — court ladies bribe the painter; she refuses; her portrait is spoiled with a mole."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='mid')
    person(A, 400, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    A.d['wash'].rectangle((490, GROUND - 260, 610, GROUND - 100), fill=255)
    A.d['ink'].rectangle((490, GROUND - 260, 610, GROUND - 100), outline=255, width=3)
    A.d['yanzhi'].ellipse((530, GROUND - 230, 570, GROUND - 190), fill=200)
    if ph < 2.5:
        person(A, 760, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, arm=90, layer='mid')
        A.d['gold'].ellipse((660, GROUND - 120, 690, GROUND - 90), fill=255)
    else:
        zhaojun(A, 760, GROUND, 170, dir=-1, arm=-8, cloak=False)
        if ph > 3.5:
            A.d['ink'].ellipse((555, GROUND - 205, 565, GROUND - 195), fill=255)
    A.flush(cv)
    lab = '宫人皆赂画工 · 求画得好' if ph < 2.5 else ('昭君独不肯' if ph < 3.5 else '画工丑图之 · 遂不得见')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '画工毛延寿之事出自西京杂记 属传说', t, t - u + P)

def art_z_lonely(A, cv, t, u):
    r = 60
    A.d['wash'].ellipse((800 - r, 840 - r, 800 + r, 840 + r), fill=255)
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    zhaojun(A, 300, GROUND, 170, dir=1, bow=20, arm=-8, cloak=False)
    A.flush(cv)
    paste(cv, text_img('入宫数岁 不得见御 · 积悲怨', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '语出后汉书南匈奴传', t, t - u + P)

def art_z_huhanye(A, cv, t, u):
    for k in range(3):
        yurt(A, 200 + k * 300, GROUND, 180, 140, layer='mid')
    ground(A, GROUND)
    for j in range(4):
        rider(A, lerp(-200, 600, ease_out(u / (2.5 * P))) - j * 120, GROUND, 110, dir=1, ph=t * 6 + j, layer='ink')
    A.flush(cv)
    paste(cv, text_img('呼韩邪单于附汉 · 三度入朝', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('南匈奴', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_ask(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='hutian')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 200, dir=-1, arm=lerp(20, 80, ease_out(u / 0.6)))
    chanyu(A, 380, GROUND, 210, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    type_in(cv, text_img('愿婿汉氏以自亲', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('求亲', 56), 260, 1020, t, t - u + P, rot=-5)

# ================================================================ 第二回 自请出塞
def art_z_request(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    zhaojun(A, 400, GROUND, 190, dir=1, kneel=True, bow=20, arm=lerp(60, 110, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('乃请掖庭令求行', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('自请', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_farewell(A, cv, t, u):
    """6-beat set piece: 辞行 — at the farewell audience she appears in full dress; the hall lights up; she turns and looks back; the court is stunned."""
    ph = u / P
    palace(A, 540, 1300, 340, layer='yanzhi')
    ground(A, GROUND)
    emperor(A, 820, GROUND - 30, 190, dir=-1, arm=lerp(20, 150, clamp((ph - 2.5) / 0.4)))
    chanyu(A, 640, GROUND, 180, dir=-1, arm=40)
    zhaojun(A, lerp(-60, 360, ease_out(ph / 1.6)), GROUND, 200, dir=1 if ph < 3.6 else -1, ph=t * 3 if ph < 1.6 else None, arm=-8)
    if ph > 1.6:
        r = 120 + 40 * math.sin(t * 3)
        A.d['gold'].ellipse((360 - r, GROUND - 120 - r, 360 + r, GROUND - 120 + r), fill=50)
    for i in range(4):
        person(A, 120 + i * 50 if i < 2 else 960 - (i - 2) * 50, GROUND, 130, dir=1 if i < 2 else -1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='mid')
    A.flush(cv)
    lab = '丰容靓饰 光明汉宫' if ph < 3.6 else '顾景裴回 竦动左右'
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3.6 else HUTIAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp((ph % 3.6) / 0.4))

def art_z_regret(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 220, dir=1, bow=lerp(0, 25, ease_out(u / (2 * P))), arm=lerp(120, 40, ease_out(u / P)))
    A.flush(cv)
    paste(cv, text_img('帝见大惊 意欲留之 · 而难于失信', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_jingning(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='hutian')
    scroll(A, 540, GROUND - 160, 300, 80, clamp(u / P), layer='wash')
    A.flush(cv)
    ink_in(cv, text_img('竟宁', BRUSH, 140, ZHU), W / 2, 1020, t, t - u + P, dur=0.3, settle=1.2)
    paste(cv, text_img('改元 · 边境安宁之意', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_ninghu(A, cv, t, u):
    for k in range(3):
        A.d['yanzhi'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    zhaojun(A, 540, GROUND - 180, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('号宁胡阏氏 · 胡人得之 国以安宁', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('阏氏', 56), 860, 1020, t, t - u + P, rot=6)

def scene_chusai(cv, t, c, k):
    """8-beat custom scene: 出塞 — she rides out through the frontier gate with the pipa; the land turns to desert and steppe;
    she plays; wild geese overhead forget their wings and drop."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 2.5:
        city_wall(A, 520, 1000, 1080, gate_x=760, label='雁门', layer='mid', open_=1.0)
        A.d['dune'].rectangle((60, GROUND - 20, W - 60, GROUND), fill=200)
    else:
        A.d['dune'].polygon([(60, GROUND), (260, GROUND - 160), (520, GROUND - 60), (800, GROUND - 200), (W - 60, GROUND)], fill=200)
        for k2 in range(30):
            q = (t * 0.8 + k2 / 30) % 1
            A.d['wash'].line((W - 60 - q * 900, 760 + (k2 * 37) % 600, W - 100 - q * 900, 760 + (k2 * 37) % 600), fill=140, width=2)
    ground(A, GROUND)
    x = lerp(860, 420, ease_out(clamp(ph / 2.5))) if ph < 2.5 else 420
    horse(A, x, GROUND, 170, dir=-1, ph=t * 4 if ph < 2.5 else 0, moving=ph < 2.5)
    zhaojun(A, x + 10, GROUND - 112, 130, dir=-1, pipa=True, arm=lerp(40, 90, 0.5 + 0.5 * math.sin(t * 8)) if ph > 3.5 else 40)
    if ph > 4:
        for j in range(5):
            fall = clamp((ph - 5 - j * 0.2) / 1.2)
            goose(A, 600 + j * 70 - 30 * fall, lerp(760 + j * 24, 1100 + j * 30, fall), 22, t + j, fall=fall)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '昭君出塞', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=57)
    fx.flush(cv)
    lab = '辞别长安 · 出雁门' if ph < 2.5 else ('北行大漠 · 马上弹琵琶' if ph < 5 else '大雁闻声 忘摆翅膀 跌落平沙')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 5 else HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph > 5:
        note_in(cv, '落雁之说出自后世民间传说', t, s0 + 5 * P)

# ================================================================ 第三回 塞外
def art_z_yurt(A, cv, t, u):
    yurt(A, 540, GROUND, 360, 260, layer='hutian')
    ground(A, GROUND)
    zhaojun(A, 820, GROUND, 180, dir=-1, arm=40)
    A.flush(cv)
    paste(cv, text_img('穹庐为室兮旃为墙 · 以肉为食兮酪为浆', SERIF, 40, HUTIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '诗句出自细君公主悲愁歌', t, t - u + P)

def art_z_seasons(A, cv, t, u):
    """6-beat set piece: 塞外四季 — the same steppe through spring grass, summer flocks, autumn wind and winter snow; she by the yurt."""
    ph = u / P
    season = min(3, int(ph / 1.5))
    cols = ['grass', 'grass', 'yellow', 'wash']
    A.d[cols[season]].rectangle((60, GROUND - 60, W - 60, GROUND), fill=170)
    if season == 1:
        for j in range(8):
            A.d['wash'].ellipse((200 + j * 80 - 22, GROUND - 90, 200 + j * 80 + 22, GROUND - 60), fill=255)
    if season == 3:
        for k2 in range(60):
            q = (t * 0.5 + k2 / 60) % 1
            A.d['wash'].ellipse((80 + (k2 * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k2 * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    yurt(A, 260, GROUND - 60, 220, 160, layer='mid')
    zhaojun(A, 520, GROUND - 60, 170, dir=1, pipa=season >= 2, arm=lerp(40, 90, 0.5 + 0.5 * math.sin(t * 6)) if season >= 2 else 40)
    ground(A, GROUND)
    A.flush(cv)
    lab = ['春草初生', '牛羊遍野', '秋风朔漠', '冬雪穹庐'][season]
    paste(cv, text_img(lab, SERIF, 48, HUTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - season * 1.5) / 0.3))

def art_z_son(A, cv, t, u):
    yurt(A, 540, GROUND, 360, 260, layer='hutian')
    ground(A, GROUND)
    zhaojun(A, 400, GROUND, 180, dir=1, arm=60)
    person(A, 470, GROUND, 70, dir=-1, robe=True, hat='knot', baby=True, arm=40, layer='ink')
    chanyu(A, 760, GROUND, 200, dir=-1, arm=40)
    A.flush(cv)
    paste(cv, text_img('生一男 · 伊屠智牙师', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_chanyu_dies(A, cv, t, u):
    yurt(A, 540, GROUND, 400, 280, layer='mid')
    ground(A, GROUND)
    chanyu(A, 540, GROUND - 10, 200, dir=1, fall=-86, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    A.flush(cv)
    paste(cv, text_img('呼韩邪单于去世', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_letter(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='hutian')
    zhaojun(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    rider(A, lerp(600, 1200, ease_out((u - 1.5 * P) / P)), GROUND, 110, dir=1, ph=t * 8)
    A.flush(cv)
    type_in(cv, text_img('上书求归 · 成帝敕令从胡俗', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

def art_z_remarry(A, cv, t, u):
    yurt(A, 540, GROUND, 360, 260, layer='yanzhi')
    ground(A, GROUND)
    zhaojun(A, 400, GROUND, 180, dir=1, bow=15, arm=-8)
    chanyu(A, 700, GROUND, 200, dir=-1, arm=60, layer='hutian')
    A.flush(cv)
    paste(cv, text_img('复为复株累单于阏氏', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('胡俗', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_daughters(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    zhaojun(A, 540, GROUND - 40, 190, dir=1, arm=60)
    for i in range(2):
        person(A, 380 + i * 340, GROUND - 40, 100, dir=-1 if i else 1, robe=True, hat='knot', female=True, arm=60, layer='yanzhi')
    A.flush(cv)
    paste(cv, text_img('生二女 · 须卜居次 当于居次', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第四回 六十年
def art_z_market(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='关市', layer='mid', open_=1.0)
    ground(A, GROUND)
    for j in range(3):
        horse(A, lerp(-100, 380, ease_out(u / (2 * P))) - j * 120, GROUND, 110, dir=1, ph=t * 4 + j, layer='hutian')
    carriage(A, lerp(1100, 720, ease_out(u / (2 * P))), GROUND, 80, dir=-1, wheel=t * 4, ph=t * 6, canopy=False, layer='yanzhi')
    A.flush(cv)
    paste(cv, text_img('胡汉通好 · 关市往来', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_beacon(A, cv, t, u):
    """6-beat set piece: 边城晏闭 — a row of beacon towers along the wall stays dark; farmers work right up to the wall; a year counter climbs."""
    ph = u / P
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 22, GROUND - 40), (x + 22, GROUND - 40), (x + 14, GROUND - 200), (x - 14, GROUND - 200)], fill=230)
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=170)
    for j in range(5):
        person(A, 200 + j * 170, GROUND - 40, 110, dir=1 if j % 2 else -1, robe=False, hat='knot', bow=40, arm=150, ph=t * 2 + j, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    yrs = int(lerp(1, 60, clamp(ph / 5)))
    paste(cv, text_img(f'边城晏闭 牛马布野 · {cn_num(yrs)}年', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    paste(cv, text_img('烽燧不举 · 三世无犬吠之警', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3.5) / 0.4))

def art_z_widow(A, cv, t, u):
    yurt(A, 540, GROUND, 400, 280, layer='mid')
    ground(A, GROUND)
    zhaojun(A, 820, GROUND, 180, dir=-1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('复株累单于去世 · 再度寡居', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_dies(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=150)
    ground(A, GROUND)
    pipa_big(A, 540, 1160, 120)
    A.flush(cv)
    paste(cv, text_img('终老塞外', SERIF, 48, HUTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年与葬地均无确考', t, t - u + P)

def art_z_qingzhong(A, cv, t, u):
    A.d['wash'].rectangle((60, GROUND - 60, W - 60, GROUND), fill=200)
    A.d['grass'].chord((320, 1080, 760, 1340), 180, 360, fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('塞草皆白 · 惟此冢独青', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '青冢之名出自传说', t, t - u + P)
    stamp(cv, seal('青冢', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_daughter_visit(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='yanzhi')
    ground(A, GROUND)
    person(A, 400, GROUND, 180, dir=1, robe=True, hat='knot', female=True, kneel=True, bow=30, arm=90, layer='hutian')
    person(A, 740, GROUND - 30, 190, dir=-1, robe=True, hat='knot', female=True, arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('女儿须卜居次入长安 · 侍太后', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_wangmang(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 22, GROUND), (x + 22, GROUND), (x + 14, GROUND - 180), (x - 14, GROUND - 180)], fill=230)
        flames(A, x, GROUND - 180, 60, 80 * ease_out((u - k * 0.3 * P) / P), t, n=2, seed=k, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('王莽篡汉 改单于印 · 和平终结', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 青冢黄昏
def art_z_hanshu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('边城晏闭 牛马布野 三世无犬吠之警', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('汉书', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_dufu(A, cv, t, u):
    r = 90
    A.d['red'].ellipse((800 - r, 900 - r, 800 + r, 900 + r), fill=180)
    A.d['grass'].chord((240, 1100, 600, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('一去紫台连朔漠 独留青冢向黄昏', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('杜甫', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_anshi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='hutian')
    A.d['wash'].rectangle((470, GROUND - 260, 610, GROUND - 90), fill=255)
    A.d['ink'].rectangle((470, GROUND - 260, 610, GROUND - 90), outline=255, width=3)
    person(A, 300, GROUND, 190, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('意态由来画不成 当时枉杀毛延寿', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('王安石', 50), 860, 1020, t, t - u + P, rot=6)

def art_z_hangongqiu(A, cv, t, u):
    for k in range(3):
        A.d['mid'].rectangle((240 + k * 80, GROUND - 60 - k * 40, 840 - k * 80, GROUND - k * 40), fill=230 - k * 20)
    ground(A, GROUND)
    zhaojun(A, 460, GROUND - 120, 170, dir=1, arm=60)
    emperor(A, 620, GROUND - 120, 170, dir=-1, arm=60)
    A.flush(cv)
    paste(cv, text_img('马致远杂剧 汉宫秋', SERIF, 46, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('元曲', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_luoyan(A, cv, t, u):
    for j in range(6):
        fall = clamp((u - j * 0.25 * P) / (1.5 * P))
        goose(A, 200 + j * 130, lerp(800, 1180, fall), 26, t + j, fall=fall)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('沉鱼 落雁 闭月 羞花', SERIF, 48, HUTIAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '四大美女之说成于后世', t, t - u + P)

def art_z_alone(A, cv, t, u):
    A.d['dune'].polygon([(60, GROUND), (300, GROUND - 120), (700, GROUND - 40), (W - 60, GROUND)], fill=200)
    ground(A, GROUND)
    zhaojun(A, lerp(300, 820, ease_out(u / (3 * P))), GROUND, 160, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('一个人的远嫁 · 一个时代的安宁', SERIF, 44, HUTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_wind(A, cv, t, u):
    for k2 in range(30):
        q = (t * 0.8 + k2 / 30) % 1
        A.d['wash'].line((W - 60 - q * 900, 760 + (k2 * 37) % 600, W - 100 - q * 900, 760 + (k2 * 37) % 600), fill=140, width=2)
    pipa_big(A, 540, 1160, 160)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('千载琵琶作胡语 分明怨恨曲中论', SERIF, 42, HUTIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    A.d['grass'].chord((720, 1320, 1000, 1460), 180, 360, fill=200)
    A.d['mid'].rectangle((60, 1400, W - 60, 1440), fill=150)

def art_z_title(A, cv, t, u):
    pipa_big(A, 820, 1400, 150)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhaojun(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '秭归女儿'), 48: ('第二回', '自请出塞'), 80: ('第三回', '穹庐'),
            112: ('第四回', '六十年'), 144: ('第五回', '青冢黄昏')}

CARDS = [
    C(0, 2, 'fate', 'num', num='一把琵琶', line='弹到塞外', art=art_z_hook_pipa),
    C(2, 4, 'empire', 'num', num='一个女子', line='换来六十年和平', art=art_z_hook_peace),
    C(4, 6, 'night', 'num', num='大雁', line='忘了扇动翅膀', art=art_z_hook_goose),
    C(6, 8, 'death', 'num', num='一座青冢', line='独向黄昏', art=art_z_hook_tomb),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 秭归女儿
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-52, main='生于秭归', sub='香溪之畔', note='生年不详 此为约数', art=art_z_birth),
    C(22, 26, 'works', 'card', year=-40, main='良家女子', sub='名嫱 字昭君', art=art_z_girl),
    C(26, 30, 'court', 'card', year=-36, main='入选掖庭', sub='待诏宫中', art=art_z_select),
    C(30, 36, 'night', 'card', year=-36, main='画工', sub='一个传说', art=art_z_painter),
    C(36, 40, 'night', 'card', year=-35, main='深宫寂寞', sub='不得见御', art=art_z_lonely),
    C(40, 44, 'war', 'card', year=-34, main='呼韩邪', sub='附汉的单于', art=art_z_huhanye),
    C(44, 48, 'court', 'card', year=-33, main='单于求亲', sub='愿婿汉氏', art=art_z_ask),
    # ---- 第二回 自请出塞
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'fate', 'card', year=-33, main='自请出塞', sub='一个决定', art=art_z_request),
    C(54, 60, 'empire', 'card', year=-33, main='光明汉宫', sub='临辞大会', art=art_z_farewell),
    C(60, 64, 'court', 'card', year=-33, main='帝悔', sub='难于失信', art=art_z_regret),
    C(64, 68, 'works', 'card', year=-33, main='改元竟宁', sub='边境安宁', art=art_z_jingning),
    C(68, 72, 'empire', 'card', year=-33, main='宁胡阏氏', sub='她的名号', art=art_z_ninghu),
    C(72, 80, 'fate', 'chusai', year=-33),
    # ---- 第三回 穹庐
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'life', 'card', year=-32, main='穹庐为室', sub='异乡', art=art_z_yurt),
    C(86, 92, 'works', 'card', year=-32, main='塞外四季', sub='春去秋来', art=art_z_seasons),
    C(92, 96, 'life', 'card', year=-32, main='生子', sub='伊屠智牙师', art=art_z_son),
    C(96, 100, 'death', 'card', year=-31, main='单于去世', sub='呼韩邪', art=art_z_chanyu_dies),
    C(100, 104, 'night', 'card', year=-31, main='上书求归', sub='回不去了', art=art_z_letter),
    C(104, 108, 'fate', 'card', year=-31, main='从胡俗', sub='再嫁', art=art_z_remarry),
    C(108, 112, 'life', 'card', year=-28, main='生二女', sub='两个女儿', art=art_z_daughters),
    # ---- 第四回 六十年
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'court', 'card', year=-25, main='胡汉通好', sub='关市', art=art_z_market),
    C(118, 124, 'empire', 'card', year=-22, main='烽燧不举', sub='六十年', art=art_z_beacon),
    C(124, 128, 'night', 'card', year=-20, main='再度寡居', sub='复株累去世', art=art_z_widow),
    C(128, 132, 'death', 'card', year=-19, main='终老塞外', sub='卒年不详', art=art_z_dies),
    C(132, 136, 'fate', 'card', year=-19, main='青冢', sub='草色独青', art=art_z_qingzhong),
    C(136, 140, 'court', 'card', year=2, main='女儿入汉', sub='须卜居次', art=art_z_daughter_visit),
    C(140, 144, 'war', 'card', year=9, main='王莽篡汉', sub='和平终结', art=art_z_wangmang),
    # ---- 第五回 青冢黄昏
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=82, main='汉书赞曰', sub='三世无警', art=art_z_hanshu),
    C(150, 154, 'night', 'card', year=767, main='独留青冢', sub='杜甫咏怀古迹', art=art_z_dufu),
    C(154, 158, 'court', 'card', year=1059, main='明妃曲', sub='王安石', art=art_z_anshi),
    C(158, 162, 'empire', 'card', year=1300, main='汉宫秋', sub='马致远', art=art_z_hangongqiu),
    C(162, 166, 'fate', 'card', year=1300, main='落雁', sub='四大美女', art=art_z_luoyan),
    C(166, 168, 'life', 'card', year=1300, main='远嫁', sub='她的选择', art=art_z_alone),
    C(168, 170, 'end', 'card', year=1300, main='琵琶胡语', sub='千载回响', art=art_z_wind),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾柒', col=HUTIAN, acc=YANZHI, born=-52, died=-19, no_age=True,
    born_lab='生年不详', died_lab='卒年不详', years_txt='生卒年不详 · 前33年出塞',
    hook_q='她本是一名宫女 · 为什么主动嫁去匈奴？',
    name_line='王嫱 · 字昭君', name='王昭君', seal='宁胡', title_art=art_z_title,
    q1='和亲牺牲品？', q2='和平使者？',
    end_art=art_z_legacy, end_big='昭君出塞', end_seal='宁胡',
    end_l1='她一个人走进了大漠', end_l2='身后的边塞安宁了六十年',
    end_brush='独留青冢向黄昏', end_ask='你觉得昭君是被迫还是自愿？评论区聊聊', next='张衡'),
    scenes=dict(chapter=scene_chapter, chusai=scene_chusai))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
