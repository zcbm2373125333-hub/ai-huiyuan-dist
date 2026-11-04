"""千古人物志 · 第肆拾柒集 · 孙武 (约前545–约前470)
Look: 吴钩青 + 战旗赤, 交戟 corner borders, a 竹简 chapter card: the thirteen slips of 兵法 are laid down
(3→6→9→13) and in the last chapter they roll up into a bundle.
Set pieces: 6-beat 十三篇, custom 8-beat scene 'jiaozhan' (吴宫教战), 6-beat 三师疲楚, 8-beat 柏举之战 map,
6-beat 秦越夹击, 6-beat 飞鸟尽.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_shangyang as Sy       # engine + helpers (previous episode)
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
from render_kongzi import slips, bundle
from render_quyuan import river

F.RIPPLE = False
WUGOU = (56, 92, 88)                # 吴钩青
ZHANQI = (164, 54, 40)              # 战旗赤
S.LAYERS.append(('wugou', WUGOU, 0.9, 1.0))
S.LAYERS.append(('zhanqi', ZHANQI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='兵', life='齐', court='吴', night='夜', war='战', empire='吴', works='谋', fate='隐', death='兵', end='圣')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHANQI, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (WUGOU, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (WUGOU, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

LAKE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(LAKE)
for _k in range(4):                 # 太湖 water lines
    _y = 1450 + _k * 18
    _d.line((60, _y, W - 60, _y), fill=WUGOU + (36 - _k * 6,), width=3)
for _x in list(range(80, 260, 22)) + list(range(840, 1010, 22)):   # reeds at the margins
    _h = 60 + (_x * 37) % 50
    _d.line((_x, 1440, _x + 8, 1440 - _h), fill=(70, 80, 60, 50), width=3)
    _d.ellipse((_x + 2, 1440 - _h - 16, _x + 14, 1440 - _h + 4), fill=(110, 90, 60, 50))
MTN_COL = {'night': (30, 36, 42), 'death': (58, 60, 60), 'war': (104, 58, 48), 'fate': (86, 98, 96)}
def draw_background(t, theme):
    """吴地: low hills, lake lines and reeds at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(180, 190, 184), (140, 160, 152), MTN_COL.get(theme, (94, 120, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(LAKE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """交戟: two crossed halberds in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=WUGOU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=WUGOU + (220,), width=3)
        for a, b in (((14, 90), (90, 14)), ((14, 14), (90, 90))):
            d.line((x + sx * a[0], y + sy * a[1], x + sx * b[0], y + sy * b[1]), fill=(60, 50, 40, 230), width=4)
        d.polygon([(x + sx * 90, y + sy * 14), (x + sx * 104, y + sy * 4), (x + sx * 98, y + sy * 22)], fill=ZHANQI + (230,))
        d.polygon([(x + sx * 90, y + sy * 90), (x + sx * 104, y + sy * 100), (x + sx * 98, y + sy * 82)], fill=ZHANQI + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def sun_wu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, armour=False, **kw):
    """孙武: Spring-and-Autumn strategist — 冠 with a jade pin, sword at the hip, scroll tucked in the belt."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='none' if up else ('helmet' if armour else 'knot'), layer=layer,
                  kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.05 * h, y - 1.06 * h, x + 0.05 * h, y - 0.94 * h), fill=255)
        A.d['wugou'].line((x - 0.1 * h, y - 1.0 * h, x + 0.1 * h, y - 1.0 * h), fill=255, width=max(2, int(0.018 * h)))
        A.d['wugou'].line((x - dir * 0.04 * h, y - 0.5 * h, x - dir * 0.26 * h, y - 0.34 * h), fill=255, width=max(3, int(0.02 * h)))
        A.d['zhanqi'].rectangle((x - 0.07 * h, y - 0.56 * h, x + 0.07 * h, y - 0.52 * h), fill=255)
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.06 * h, y - 0.82 * h, x + dir * 0.09 * h, y - 0.72 * h), fill=255, width=max(2, int(0.012 * h)))
    return hand

def king(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def drum(A, x, base, s, t, hit=0.0):
    A.d['ink'].line((x - 0.6 * s, base, x - 0.3 * s, base - 0.9 * s), fill=255, width=5)
    A.d['ink'].line((x + 0.6 * s, base, x + 0.3 * s, base - 0.9 * s), fill=255, width=5)
    A.d['zhanqi'].ellipse((x - 0.5 * s, base - 1.4 * s, x + 0.5 * s, base - 0.5 * s), fill=255)
    A.d['ink'].ellipse((x - 0.5 * s, base - 1.4 * s, x + 0.5 * s, base - 0.5 * s), outline=255, width=5)
    if hit > 0:
        r = 0.5 * s + 40 * hit
        A.d['wash'].ellipse((x - r, base - 0.95 * s - r, x + r, base - 0.95 * s + r), outline=int(200 * (1 - hit)), width=4)

def banner(A, x, base, h, t, layer='zhanqi', fallen=0.0):
    ang = fallen * 1.5
    tx, ty = x + h * math.sin(ang), base - h * math.cos(ang)
    A.d['ink'].line((x, base, tx, ty), fill=255, width=6)
    if fallen < 0.95:
        wv = 8 * math.sin(t * 4)
        A.d[layer].polygon([(tx, ty), (tx + 90 * math.cos(ang), ty + 90 * math.sin(ang) + wv), (tx + 80 * math.cos(ang) - 50 * math.sin(ang), ty + 80 * math.sin(ang) + 50 * math.cos(ang) + wv), (tx - 50 * math.sin(ang), ty + 50 * math.cos(ang))], fill=255)

def army(A, x0, y, n, dir=1, layer='ink', t=0.0, march=False, h=90, spear=True):
    for i in range(n):
        person(A, x0 + i * h * 0.45 * dir, y, h, dir=dir, ph=(t * 6 + i) if march else None, robe=False, hat='helmet', spear=spear, arm=40, layer=layer)

def slip_row(A, cx, base, n, h=300, layer='wugou'):
    slips(A, cx - n * 19 / 2, base, n, h, layer=layer)

# ================================================================ chapter card
CH = {16: (3, 0.0), 48: (6, 0.0), 80: (9, 0.0), 112: (13, 0.0), 144: (13, 1.0)}
def art_slips_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g, roll = CH.get(kb, (6, 0.0))
    prev = {16: 0, 48: 3, 80: 6, 112: 9, 144: 13}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    if roll > 0:
        n = int(lerp(13, 2, q * roll))
        slip_row(A, 540, 1180, n, 320)
        if q > 0.6:
            bundle(A, 540, 1180, 160 * (q - 0.6) / 0.4, layer='wugou')
    else:
        slip_row(A, 540, 1180, int(lerp(prev, g, q)), 320)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_slips_chapter)
    ink_in(cv, text_img(no, SERIF, 56, WUGOU, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_w_hook_13(A, cv, t, u):
    ground(A, GROUND)
    slip_row(A, 540, GROUND - 20, min(13, int(clamp(u / (1.4 * P)) * 13) + 1), 360)

def art_w_hook_30k(A, cv, t, u):
    ground(A, GROUND)
    army(A, 120, GROUND, 4, dir=1, layer='wugou', t=t, march=True, h=110)
    n = int(clamp(u / (1.4 * P)) * 20) + 1
    for i in range(n):
        person(A, 980 - (i % 10) * 40, GROUND - (i // 10) * 50, 70, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')

def art_w_hook_nofight(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 220, GROUND, 220, 180, layer='mid')
    banner(A, 820, GROUND, 360, t, fallen=0.0)
    for i in range(4):
        person(A, 560 + i * 60, GROUND, 120, dir=1, robe=False, hat='helmet', kneel=True, bow=40, arm=-8, layer='ink')

def art_w_hook_2500(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='wugou')
    for i in range(int(clamp(u / P) * 5) + 1):
        bundle(A, 380 + i * 80, GROUND - 74, 60, layer='zhanqi')

# ================================================================ 第一回 齐国将门
def art_w_birth(A, cv, t, u):
    palace(A, 540, 1160, 480, layer='mid')
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='knot', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('齐国乐安', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('陈氏之后 · 世代将门', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_sand(A, cv, t, u):
    ground(A, GROUND)
    A.d['dune'].rectangle((300, GROUND - 40, 860, GROUND), fill=220)
    for k in range(int(clamp(u / (2 * P)) * 8) + 1):
        A.d['zhanqi' if k % 2 else 'wugou'].polygon([(340 + k * 62, GROUND - 40), (360 + k * 62, GROUND - 90), (380 + k * 62, GROUND - 40)], fill=255)
    person(A, 220, GROUND, 160, dir=1, robe=True, hat='knot', kneel=True, bow=25, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('少年布石为阵', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('家学', 54), 860, 1020, t, t - u + P, rot=6)

def art_w_surname(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='wugou')
    ground(A, GROUND)
    king(A, 720, GROUND - 30, 220, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)))
    person(A, 380, GROUND, 220, dir=1, robe=False, hat='helmet', kneel=True, bow=30, arm=100, layer='ink')
    A.flush(cv)
    ink_in(cv, text_img('孙', BRUSH, 150, ZHU), W / 2, 1020, t, t - u + P, dur=0.3, settle=1.2)
    paste(cv, text_img('祖父伐莒有功 · 齐景公赐姓', SERIF, 44, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_turmoil(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='临淄', layer='mid', open_=1.0)
    flames(A, 540, 1060, 600, 220 * ease_out(u / P), t, n=7, seed=47, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('田鲍高国四族相争', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('内乱', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_south(A, cv, t, u):
    river(A, 1180, t, rows=3, amp=6)
    x = lerp(140, 900, ease_out(u / (3.5 * P)))
    boat(A, x, 1200, 120, t, sail=True)
    sun_wu(A, x - 20, 1180, 110, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('避祸南下 · 投奔吴国', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('奔吴', 56), 260, 1020, t, t - u + P, rot=-5)

PIANS = ['计', '作战', '谋攻', '形', '势', '虚实', '军争', '九变', '行军', '地形', '九地', '火攻', '用间']
def art_w_thirteen(A, cv, t, u):
    """6-beat set piece: 十三篇 — in a mountain hut he writes; the thirteen chapter titles appear one by one on the slips."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 360), (x + 200, GROUND)], fill=150)
    ground(A, GROUND)
    lamp(A, 940, GROUND, 60, t, glow=0.8)
    sitter(A, 170, GROUND, 190, dir=1, bow=20)
    n = min(13, int(clamp(ph / 5.2) * 13) + 1)
    for i in range(n):
        A.d['wash'].rectangle((300 + i * 46, 980, 336 + i * 46, GROUND - 10), fill=255)
        A.d['ink'].rectangle((300 + i * 46, 980, 336 + i * 46, GROUND - 10), outline=200, width=2)
    A.flush(cv)
    for i in range(n):
        im = text_img(PIANS[12 - i] if False else PIANS[i], SERIF, 28, ZHU if i == n - 1 else INK, 'Black', bleed=False, vertical=True)
        paste(cv, im, 318 + i * 46, 980 + 20 + im.height / 2, 1, clamp((ph - i * 0.4) / 0.3))
    paste(cv, text_img(f'兵法 第{cn_num(n)}篇', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('穹窿山', 46), 860, 1440, t, t - u + 0.4, rot=6)

def art_w_seven(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    king(A, 760, GROUND - 30, 220, dir=-1, arm=20)
    person(A, 420, GROUND, 210, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    n = min(7, int(u / (0.5 * P)) + 1)
    paste(cv, text_img(f'伍子胥 一日七荐 · 第{cn_num(n)}次', SERIF, 44, ZHU if n == 7 else WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    note_in(cv, '出自吴越春秋', t, t - u + P)

# ================================================================ 第二回 吴宫教战
def art_w_audience(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='wugou')
    ground(A, GROUND)
    king(A, 740, GROUND - 30, 220, dir=-1, arm=lerp(20, 90, ease_out(u / 0.6)))
    sun_wu(A, 360, GROUND, 220, dir=1, arm=60)
    scroll(A, 560, GROUND - 210, 220, 60, clamp(u / P), layer='wash')
    A.flush(cv)
    type_in(cv, text_img('子之十三篇 寡人尽观之矣', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('吴王阖闾', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_test(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='pink')
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 18) + 1
    for i in range(n):
        person(A, 140 + (i % 9) * 100, GROUND - (i // 9) * 60, 100, dir=1, robe=True, hat='knot', female=True, arm=30, layer='pink' if i % 2 else 'ink')
    A.flush(cv)
    type_in(cv, text_img('可以小试勒兵乎', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('一百八十人', 40), 860, 1020, t, t - u + P, rot=6)

def scene_jiaozhan(cv, t, c, k):
    """8-beat custom scene: 吴宫教战 — the palace women laugh at the drum; he repeats the orders; the two captains'
    banners fall; then both squads turn, kneel and rise in perfect step."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    beat = (t - s0) % P / P
    drum(A, 540, GROUND, 120, t, hit=beat if ph < 3.5 or ph > 5 else 0.0)
    for side, x0 in ((0, 120), (1, 680)):
        lead_fall = clamp((ph - 3.6) / 0.6)
        banner(A, x0 + 140, GROUND - 230, 160, t, layer='zhanqi' if side else 'wugou', fallen=lead_fall)
        for i in range(8):
            r, cidx = divmod(i, 4)
            x = x0 + cidx * 75
            y = GROUND - r * 70
            if ph < 3.5:
                arm = lerp(-8, 120, 0.5 + 0.5 * math.sin(t * 7 + i * 1.7))
                person(A, x + 6 * math.sin(t * 5 + i), y, 110, dir=1 if (i + int(t * 2)) % 2 else -1, robe=True, hat='knot', female=True, arm=arm, layer='pink')
            else:
                step = int((ph - 5) * 2) % 4 if ph >= 5 else 0
                kneel = step == 2
                dirn = -1 if step == 1 else 1
                person(A, x, y, 110, dir=dirn, robe=True, hat='knot', female=True, kneel=kneel, arm=40, layer='pink' if ph < 5 else 'ink')
    sun_wu(A, 540, GROUND - 260, 150, dir=1, arm=lerp(-8, 140, clamp((ph - 3.4) / 0.3)) if ph < 5 else 60)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '吴宫教战', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=47)
    fx.flush(cv)
    sub = '三令五申 · 宫女大笑' if ph < 3.5 else ('将在军 君命有所不受' if ph < 5 else '左右前后跪起 皆中规矩')
    paste(cv, text_img(sub, SERIF, 46, ZHU if 3.5 <= ph < 5 else WUGOU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('令行禁止 · 斩队长二人以徇', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3.6) / 0.4))

def art_w_general(A, cv, t, u):
    for k in range(3):
        A.d['wugou'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    sun_wu(A, 540, GROUND - 180, 200, dir=1, armour=False, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('拜将', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('吴王知孙子能用兵', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_shu(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='舒', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-80, 200, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='wugou', t=t, march=u < 2 * P, h=110)
    banner(A, 120, GROUND, 300, t, layer='wugou')
    A.flush(cv)
    stamp(cv, seal('初战', 56), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('拔舒 · 取钟吾', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_tire(A, cv, t, u):
    """6-beat set piece: 三师疲楚 — three Wu columns take turns striking the Chu border; Chu rushes out each time and comes back exhausted."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 860, 970, 1300), radius=20, fill=170)
    A.d['ink'].line((540, 880, 520, 1080, 560, 1280), fill=255, width=6)
    A.d['zhanqi'].rectangle((140, 900, 500, 1270), fill=40)
    k = int(ph) % 3
    for j in range(3):
        y = 960 + j * 120
        on = j == k
        x = lerp(820, 600, ease_out((ph % 1) / 0.5)) if on else 820
        A.d['wugou'].polygon([(x, y), (x + 120, y - 30), (x + 120, y + 30)], fill=255 if on else 120)
    cx = lerp(300, 470, 0.5 + 0.5 * math.sin(ph * math.pi))
    A.d['zhanqi'].ellipse((cx - 40, 1060 - 40, cx + 40, 1060 + 40), fill=int(lerp(255, 100, clamp(ph / 6))))
    A.flush(cv)
    paste(cv, text_img(f'三师轮番袭扰 · 楚军疲于奔命 第{cn_num(int(ph) + 1)}年', SERIF, 40, WUGOU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)
    for nm, x, y, col in (('吴', 900, 1240, WUGOU), ('楚', 200, 1240, ZHANQI)):
        stamp(cv, seal(nm, 44, col), x, y, t, t - u + 0.3)

# ================================================================ 第三回 柏举之战
def art_w_allies(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='wugou')
    ground(A, GROUND)
    for i, x in enumerate((300, 780)):
        person(A, x, GROUND, 200, dir=1 if i == 0 else -1, robe=True, hat='crown', bow=20, arm=90, layer='ink')
    A.flush(cv)
    paste(cv, text_img('唐蔡两国怨楚 · 愿为向导', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('联唐蔡', 50), 860, 1020, t, t - u + P, rot=6)

def art_w_land(A, cv, t, u):
    river(A, 1220, t, rows=2, amp=4)
    for i in range(3):
        boat(A, 760 + i * 90, 1240, 70, t + i, sail=False)
    army(A, lerp(700, 120, ease_out(u / (3 * P))), 1220, 6, dir=-1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('舍舟淮汭 · 疾趋楚境', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('奇袭', 56), 260, 1020, t, t - u + P, rot=-5)

def art_w_baiju(A, cv, t, u):
    """8-beat set piece: 柏举之战 — the route across the map: off the boats at 淮汭, through the three passes,
    the clash at 柏举, five victories, into 郢."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    A.d['ocean'].line([(980, 960), (760, 980), (560, 940), (380, 960)], fill=220, width=10)
    A.d['ocean'].line([(140, 1060), (260, 1180), (240, 1360)], fill=220, width=10)
    route = [(900, 970), (640, 1020), (500, 1120), (380, 1200), (220, 1300)]
    f = clamp(ph / 6.5)
    n = len(route) - 1
    m = f * n
    for i in range(n):
        ff = clamp(m - i)
        if ff <= 0: break
        (x0, y0), (x1, y1) = route[i], route[i + 1]
        A.d['wugou'].line((x0, y0, lerp(x0, x1, ff), lerp(y0, y1, ff)), fill=255, width=10)
    for j in range(3):
        A.d['mid'].polygon([(470 + j * 40, 1080), (490 + j * 40, 1030), (510 + j * 40, 1080)], fill=230)
    if ph > 4:
        r = 30 + 20 * math.sin(t * 8)
        A.d['zhanqi'].ellipse((380 - r, 1200 - r, 380 + r, 1200 + r), fill=200)
    A.flush(cv)
    for nm, x, y, col in (('淮汭', 900, 900, WUGOU), ('三关', 500, 1010, INK), ('柏举', 380, 1270, ZHANQI), ('郢', 220, 1370, ZHANQI)):
        stamp(cv, seal(nm, 30, col), x, y, t, t - u + 0.3)
    wins = min(5, max(0, int((ph - 4) / 0.6) + 1)) if ph > 4 else 0
    lab = '吴军三万 · 楚军二十万' if ph < 4 else (f'五战五胜 · 第{cn_num(wins)}战' if wins < 5 or ph < 7.2 else '十日之内 攻入郢都')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else WUGOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_w_ying(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='郢', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-100, 300, ease_out(u / (2 * P))), GROUND, 5, dir=1, layer='wugou', t=t, march=True, h=110)
    A.flush(cv)
    paste(cv, text_img('楚昭王弃城而逃', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('入郢', 60), 860, 1020, t, t - u + P, rot=6)

def art_w_baoxu(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 210, dir=1, robe=True, hat='knot', kneel=True, bow=lerp(20, 60, 0.5 + 0.5 * math.sin(t * 2)), arm=140, layer='ink')
    A.flush(cv)
    n = min(7, int(u / (0.5 * P)) + 1)
    paste(cv, text_img(f'申包胥哭秦庭 · 第{cn_num(n)}日', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('秦庭', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_pincer(A, cv, t, u):
    """6-beat set piece: 秦越夹击 — Qin chariots roll in from the west, Yue boats strike from the east; the Wu army pulls back."""
    ph = u / P
    river(A, 1260, t, rows=2, amp=4)
    ground(A, 1250, x0=60, x1=700)
    for j in range(3):
        carriage(A, lerp(-200, 160 + j * 150, ease_out(ph / 2.5)), 1250, 70, dir=1, wheel=t * 6, ph=t * 8 + j, layer='ink')
    for j in range(3):
        boat(A, lerp(1200, 820 + j * 70, ease_out((ph - 1.5) / 2)), 1290, 60, t + j, sail=True)
    army(A, lerp(560, 640, ease_out((ph - 3) / 2.5)), 1250, 3, dir=1 if ph > 3 else -1, layer='wugou', t=t, march=ph > 3, h=100)
    A.flush(cv)
    lab = '秦发兵车五百乘救楚' if ph < 1.5 else ('越王允常趁虚袭吴' if ph < 3 else '腹背受敌 · 吴军班师')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph < 3 else WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

# ================================================================ 第四回 吴越争霸
def art_w_helv(A, cv, t, u):
    tent(A, 540, GROUND, 360, 260, layer='mid')
    ground(A, GROUND)
    king(A, 540, GROUND - 10, 200, dir=1, fall=-80, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    A.flush(cv)
    paste(cv, text_img('伐越负伤 · 阖闾去世', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('夫差继位', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_fujiao(A, cv, t, u):
    river(A, 1180, t, rows=3, amp=6, speed=2)
    for j in range(4):
        boat(A, lerp(1100, 600 + j * 110, ease_out(u / (2 * P))), 1210, 70, t + j, sail=True)
    for j in range(3):
        boat(A, lerp(380 - j * 100, -200 - j * 100, ease_out((u - 2 * P) / (1.5 * P))), 1220, 60, t + j, sail=False)
    A.flush(cv)
    paste(cv, text_img('大败越军 · 勾践困守会稽', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('夫椒', 56), 260, 1020, t, t - u + P, rot=-5)

def art_w_peace(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='wugou')
    ground(A, GROUND)
    king(A, 760, GROUND - 30, 220, dir=-1, arm=lerp(20, 60, ease_out(u / 0.6)))
    person(A, 560, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, ease_out((u - P) / 0.4)), layer='ink')
    person(A, 330, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, bow=50, arm=100, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('今不灭越 后必悔之', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('子胥谏', 50, INK), 860, 1020, t, t - u + 0.4, rot=6)

def art_w_ailing(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        rider(A, lerp(-200, 300, ease_out(u / (2 * P))) + j * 120, GROUND, 120, dir=1, ph=t * 8 + j, layer='wugou', spear=True)
    for j in range(4):
        rider(A, lerp(720, 1200, ease_out((u - 1.5 * P) / (2 * P))) + j * 120, GROUND, 110, dir=1, ph=t * 8 + j, layer='mid')
    A.flush(cv)
    paste(cv, text_img('大破齐军 · 吴国称雄', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('艾陵', 56), 860, 1020, t, t - u + P, rot=6)

def art_w_zixu(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 210, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='ink')
    A.d['wugou'].line((620, GROUND - 220, 760, GROUND - 120), fill=255, width=8)
    A.flush(cv)
    type_in(cv, text_img('抉吾眼悬吴东门之上', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('属镂剑', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_vanish(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 360), (x + 150, GROUND)], fill=200)
    for k in range(6):
        q = (t * 0.1 + k / 6) % 1
        A.d['wash'].ellipse((lerp(-100, 1100, q) - 120, 900 + k * 40 - 30, lerp(-100, 1100, q) + 120, 900 + k * 40 + 30), fill=120)
    ground(A, GROUND)
    sun_wu(A, lerp(300, 820, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('辞官归隐 · 不知所终', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_birds(A, cv, t, u):
    """6-beat set piece: 飞鸟尽 — seasons pass over a lone hut; birds leave; a bow hangs on the wall; the slips are bundled."""
    ph = u / P
    season = int(ph / 1.5) % 4
    cols = ['grass', 'yellow', 'zhanqi', 'wash']
    for k in range(3):
        x = 260 + k * 280
        A.d['ink'].line((x, GROUND, x, GROUND - 260), fill=255, width=10)
        A.d[cols[season]].ellipse((x - 110, GROUND - 380, x + 110, GROUND - 220), fill=200 if season < 3 else 60)
    A.d['mid'].rectangle((620, GROUND - 200, 900, GROUND), fill=230)
    A.d['ink'].polygon([(600, GROUND - 200), (920, GROUND - 200), (760, GROUND - 300)], fill=255)
    A.d['ink'].arc((680, GROUND - 170, 760, GROUND - 60), 270, 90, fill=255, width=6)
    for j in range(5):
        q = clamp(ph / 6 + j * 0.05)
        crow(A, lerp(200 + j * 60, 1100, q), lerp(800 + j * 20, 640, q), 18, t * 8 + j)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('飞鸟尽 良弓藏', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('他比谁都懂得何时收兵', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 2 * P, 0.5)

# ================================================================ 第五回 兵圣
def art_w_wu_falls(A, cv, t, u):
    palace(A, 540, 1160, 560, collapse=ease_out(u / (2 * P)), layer='wugou')
    flames(A, 540, 1100, 600, 240 * ease_out(u / P), t, n=7, seed=473, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('越灭吴 · 夫差自尽', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('姑苏', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_tomb(A, cv, t, u):
    A.d['mid'].chord((340, 1080, 740, 1320), 180, 360, fill=230)
    A.d['ink'].rectangle((520, 1080, 560, 1200), fill=255)
    for k in range(3):
        A.d['pine'].polygon([(180 + k * 60, GROUND), (210 + k * 60, GROUND - 220), (240 + k * 60, GROUND)], fill=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('终老吴地', SERIF, 48, WUGOU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年葬地均无确载 一说葬于吴都郊外', t, t - u + P)

def art_w_europe(A, cv, t, u):
    river(A, 1220, t, rows=2, amp=4)
    boat(A, lerp(200, 860, ease_out(u / (3 * P))), 1220, 140, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('法国传教士钱德明译出', SERIF, 46, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('西传', 56), 260, 1020, t, t - u + P, rot=-5)

def art_w_yinque(A, cv, t, u):
    A.d['dune'].rectangle((200, 1000, 880, GROUND), fill=220)
    A.d['ink'].rectangle((300, 1060, 780, 1240), fill=200)
    q = ease_out((u - 0.5 * P) / P)
    slip_row(A, 540, 1220, int(q * 16), 140, layer='wugou')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('孙子兵法 孙膑兵法 同墓出土', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('银雀山', 50), 860, 1020, t, t - u + P, rot=6)

def art_w_knowself(A, cv, t, u):
    A.d['ink'].ellipse((300, 900, 520, 1120), outline=255, width=8)
    A.d['ink'].ellipse((560, 900, 780, 1120), outline=255, width=8)
    q = ease_out(u / P)
    A.d['wugou'].ellipse((410 - 110 * q, 1010 - 110 * q, 410 + 110 * q, 1010 + 110 * q), fill=150)
    A.d['zhanqi'].ellipse((670 - 110 * q, 1010 - 110 * q, 670 + 110 * q, 1010 + 110 * q), fill=150)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('知彼知己者 百战不殆', SERIF, 48, WUGOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_famou(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        person(A, 200 + i * 110, GROUND, 140, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid', bow=0)
    A.d['wash'].rectangle((140, GROUND - 160, 860 * ease_out(u / P) + 140 * (1 - ease_out(u / P)), GROUND - 150), fill=200)
    A.flush(cv)
    paste(cv, text_img('不战而屈人之兵 · 善之善者也', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_dashi(A, cv, t, u):
    drum(A, 540, GROUND, 180, t, hit=(u % P) / P)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('死生之地 存亡之道 不可不察也', SERIF, 42, WUGOU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_w_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    slip_row(A, 860, 1380, 6, 160)

def art_w_title(A, cv, t, u):
    banner(A, 820, 1460, 560, t, layer='zhanqi')
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    sun_wu(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '齐国将门'), 48: ('第二回', '吴宫教战'), 80: ('第三回', '柏举之战'),
            112: ('第四回', '吴越争霸'), 144: ('第五回', '兵家之圣')}

CARDS = [
    C(0, 2, 'works', 'num', num='十三篇', line='六千字', art=art_w_hook_13),
    C(2, 4, 'war', 'num', num='三万人', line='破楚二十万', art=art_w_hook_30k),
    C(4, 6, 'night', 'num', num='不战', line='而屈人之兵', art=art_w_hook_nofight),
    C(6, 8, 'empire', 'num', num='两千五百年', line='还在被人读', art=art_w_hook_2500),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 齐国将门
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-545, main='生于齐国', sub='将门之后', note='生年约在前五四五年', art=art_w_birth),
    C(22, 26, 'works', 'card', year=-532, main='少年论兵', sub='耳濡目染', art=art_w_sand),
    C(26, 30, 'court', 'card', year=-523, main='赐姓孙', sub='孙氏由来', art=art_w_surname),
    C(30, 34, 'death', 'card', year=-517, main='齐国内乱', sub='是非之地', art=art_w_turmoil),
    C(34, 38, 'fate', 'card', year=-517, main='南下奔吴', sub='另寻天地', art=art_w_south),
    C(38, 44, 'works', 'card', year=-515, main='著十三篇', sub='隐居著书', art=art_w_thirteen),
    C(44, 48, 'court', 'card', year=-512, main='七荐孙武', sub='伍子胥', art=art_w_seven),
    # ---- 第二回 吴宫教战
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'empire', 'card', year=-512, main='进见吴王', sub='献兵法', art=art_w_audience),
    C(54, 58, 'life', 'card', year=-512, main='以妇人试', sub='吴王的刁难', art=art_w_test),
    C(58, 66, 'works', 'jiaozhan', year=-512),
    C(66, 70, 'empire', 'card', year=-512, main='拜为将军', sub='军令如山', art=art_w_general),
    C(70, 74, 'war', 'card', year=-512, main='初试锋芒', sub='伐楚之始', art=art_w_shu),
    C(74, 80, 'works', 'card', year=-511, main='疲楚之计', sub='六年不停的骚扰', art=art_w_tire),
    # ---- 第三回 柏举之战
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'court', 'card', year=-506, main='联唐蔡', sub='借路伐楚', art=art_w_allies),
    C(86, 90, 'fate', 'card', year=-506, main='舍舟登陆', sub='出其不意', art=art_w_land),
    C(90, 98, 'war', 'card', year=-506, main='柏举之战', sub='以少胜多', art=art_w_baiju),
    C(98, 102, 'empire', 'card', year=-506, main='攻入郢都', sub='楚国几乎灭亡', art=art_w_ying),
    C(102, 106, 'night', 'card', year=-506, main='哭秦庭', sub='七日七夜', art=art_w_baoxu),
    C(106, 112, 'war', 'card', year=-505, main='秦越夹击', sub='见好就收', art=art_w_pincer),
    # ---- 第四回 吴越争霸
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'death', 'card', year=-496, main='阖闾之死', sub='伐越负伤', art=art_w_helv),
    C(118, 122, 'war', 'card', year=-494, main='夫椒之战', sub='一雪前耻', art=art_w_fujiao),
    C(122, 126, 'court', 'card', year=-494, main='放虎归山', sub='夫差许越求和', art=art_w_peace),
    C(126, 130, 'empire', 'card', year=-484, main='艾陵之战', sub='北上争霸', note='孙武是否参战 史无明载', art=art_w_ailing),
    C(130, 134, 'death', 'card', year=-484, main='子胥赐死', sub='忠臣之死', art=art_w_zixu),
    C(134, 138, 'fate', 'card', year=-484, main='功成身退', sub='归隐山林', note='去向众说纷纭 多为后人推测', art=art_w_vanish),
    C(138, 144, 'night', 'card', year=-482, main='良弓藏', sub='全身而退', art=art_w_birds),
    # ---- 第五回 兵家之圣
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=-473, main='吴国灭亡', sub='子胥一语成谶', art=art_w_wu_falls),
    C(150, 154, 'life', 'card', year=-470, main='长眠吴地', sub='卒年不详', art=art_w_tomb),
    C(154, 158, 'works', 'card', year=1772, main='传入欧洲', sub='第一个西文译本', art=art_w_europe),
    C(158, 162, 'empire', 'card', year=1972, main='银雀山竹简', sub='千年疑案终结', art=art_w_yinque),
    C(162, 166, 'court', 'card', year=1972, main='知己知彼', sub='最有名的八个字', art=art_w_knowself),
    C(166, 168, 'works', 'card', year=1972, main='上兵伐谋', sub='最高明的胜利', art=art_w_famou),
    C(168, 170, 'end', 'card', year=1972, main='兵者大事', sub='开篇第一句', art=art_w_dashi),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾柒', col=WUGOU, acc=ZHANQI, born=-545, died=-470, age0=-545,
    born_lab='约前545年', died_lab='约前470年', years_txt='约公元前545 — 约前470',
    hook_q='最会打仗的人 · 为什么劝人别打仗？',
    name_line='孙武 · 字长卿', name='孙武', seal='兵圣', title_art=art_w_title,
    q1='兵家至圣？', q2='查无此人？',
    end_art=art_w_legacy, end_big='不战而胜', end_seal='兵圣',
    end_l1='他写下了最懂打仗的书', end_l2='教人的却是最好别打仗',
    end_brush='知己知彼', end_ask='你用过哪一条孙子兵法？评论区聊聊', next='勾践'),
    scenes=dict(chapter=scene_chapter, jiaozhan=scene_jiaozhan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
