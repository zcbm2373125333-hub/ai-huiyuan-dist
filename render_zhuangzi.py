"""千古人物志 · 第伍拾壹集 · 庄子 (约前369–约前286)
Look: 天青 + 蝶黄, 蝴蝶 corner borders, a 鲲鹏 chapter card: a small fish grows into 鲲, turns into 鹏 and spreads
its wings, and in the last chapter it soars away.
Set pieces: 6-beat 衣弊履穿见魏王, 6-beat 曳尾涂中, 6-beat 濠梁之辩, 6-beat 庖丁解牛, custom 8-beat scene
'mengdie' (庄周梦蝶), 8-beat 逍遥游 鲲鹏, 6-beat 物化.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_mengzi as Mz          # engine + helpers (previous episode)
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
from render_quyuan import river

F.RIPPLE = False
TIANQING = (92, 136, 170)           # 天青
DIEHUANG = (206, 160, 58)           # 蝶黄
S.LAYERS.append(('tianqing', TIANQING, 0.88, 1.0))
S.LAYERS.append(('diehuang', DIEHUANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='游', life='庄', court='楚', night='梦', war='辩', empire='鹏', works='道', fate='贫', death='化', end='逍')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (DIEHUANG, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (TIANQING, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DIEHUANG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (34, 40, 56), 'death': (64, 66, 70), 'war': (110, 92, 60), 'fate': (96, 104, 112)}
def draw_background(t, theme):
    """濠水: misty hills, drifting cloud bands, and small fish in the water lines at the bottom."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 192, 196), (150, 166, 178), MTN_COL.get(theme, (104, 124, 140))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k in range(3):
        x = (t * 18 + k * 400) % (W + 600) - 300
        d.ellipse((x - 220, 1330 + k * 30 - 22, x + 220, 1330 + k * 30 + 22), fill=(240, 240, 236, 50))
    for k in range(3):
        d.line((60, 1470 + k * 18, W - 60, 1470 + k * 18), fill=TIANQING + (34,), width=2)
    for k in range(4):
        fx = (t * 40 * (1 if k % 2 else -1) + k * 300) % (W - 160) + 80
        fy = 1478 + (k % 2) * 18
        d.ellipse((fx - 12, fy - 5, fx + 12, fy + 5), fill=(60, 70, 80, 60))
    canvas.alpha_composite(ov)
    return canvas
G.draw_background = draw_background

def _wing(d, cx, cy, s, sx, sy, col, a):
    d.ellipse((cx, cy - sy * 0.9 * s if sy > 0 else cy, cx + sx * s, cy) if False else
              (min(cx, cx + sx * s), min(cy, cy - 0.9 * s), max(cx, cx + sx * s), max(cy, cy - 0.9 * s)), fill=col + (a,))

def draw_frame_border(canvas):
    """蝴蝶: a small butterfly resting in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=TIANQING + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=TIANQING + (220,), width=3)
        cx, cy = x + sx * 52, y + sy * 52
        for wx, wy, r in ((-1, -1, 22), (1, -1, 22), (-1, 1, 15), (1, 1, 15)):
            ex, ey = cx + wx * r * 0.9, cy + wy * r * 0.8
            d.ellipse((ex - r, ey - r * 0.8, ex + r, ey + r * 0.8), fill=DIEHUANG + (220,))
        d.line((cx, cy - 22, cx, cy + 22), fill=(40, 36, 30, 240), width=4)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhuang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """庄子: loose-haired recluse — a simple topknot with a stick through it, patched robe, sandals of straw."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        A.d['diehuang'].line((x - 0.08 * h, y - 1.02 * h, x + 0.08 * h, y - 0.96 * h), fill=255, width=max(2, int(0.016 * h)))
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.7 * h)], fill=255)
        A.d['tianqing'].rectangle((x - 0.1 * h, y - 0.36 * h, x - 0.02 * h, y - 0.28 * h), fill=255)
        A.d['tianqing'].rectangle((x + 0.02 * h, y - 0.22 * h, x + 0.09 * h, y - 0.15 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.04 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
    return hand

def king(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def butterfly(A, x, y, s, t, layer='diehuang', flap=None):
    f = abs(math.sin(t * 9)) if flap is None else flap
    w = s * (0.35 + 0.65 * f)
    for wx, wy, r in ((-1, -1, 1.0), (1, -1, 1.0), (-1, 0.8, 0.7), (1, 0.8, 0.7)):
        A.d[layer].ellipse((x + wx * w * r - w * r * 0.8, y + wy * s * 0.45 - s * r * 0.45, x + wx * w * r + w * r * 0.8, y + wy * s * 0.45 + s * r * 0.45), fill=255)
    A.d['ink'].line((x, y - 0.5 * s, x, y + 0.6 * s), fill=255, width=max(2, int(0.1 * s)))

def fish(A, x, y, s, dir=1, layer='tianqing', t=0.0):
    wag = 0.25 * math.sin(t * 6)
    A.d[layer].ellipse((x - s, y - 0.4 * s, x + s, y + 0.4 * s), fill=255)
    tx = x - dir * s
    A.d[layer].polygon([(tx, y), (tx - dir * 0.6 * s, y - 0.45 * s + wag * s), (tx - dir * 0.6 * s, y + 0.45 * s + wag * s)], fill=255)
    A.d['ink'].ellipse((x + dir * 0.6 * s - 0.08 * s, y - 0.12 * s, x + dir * 0.6 * s + 0.08 * s, y + 0.04 * s), fill=255)

def peng(A, x, y, s, t, layer='ink', spread=1.0):
    flap = 0.25 * math.sin(t * 2.4)
    A.d[layer].ellipse((x - 0.5 * s, y - 0.18 * s, x + 0.5 * s, y + 0.18 * s), fill=255)
    for sgn in (-1, 1):
        A.d[layer].polygon([(x + sgn * 0.2 * s, y - 0.05 * s), (x + sgn * (0.3 + 1.6 * spread) * s, y - (0.5 + flap) * s * spread),
                            (x + sgn * (0.2 + 1.4 * spread) * s, y + 0.05 * s), (x + sgn * 0.2 * s, y + 0.12 * s)], fill=255)
    A.d[layer].polygon([(x + 0.5 * s, y - 0.08 * s), (x + 0.8 * s, y - 0.02 * s), (x + 0.5 * s, y + 0.06 * s)], fill=255)
    A.d['diehuang'].polygon([(x - 0.5 * s, y), (x - 0.95 * s, y - 0.2 * s), (x - 0.95 * s, y + 0.2 * s)], fill=255)

def turtle(A, x, y, s, layer='ink'):
    A.d[layer].chord((x - s, y - 0.7 * s, x + s, y + 0.3 * s), 180, 360, fill=255)
    A.d[layer].ellipse((x + 0.8 * s, y - 0.45 * s, x + 1.25 * s, y - 0.1 * s), fill=255)
    for lx in (-0.6, 0.5):
        A.d[layer].ellipse((x + lx * s - 0.15 * s, y - 0.2 * s, x + lx * s + 0.15 * s, y + 0.05 * s), fill=255)

# ================================================================ chapter card
CH = {16: 0, 48: 1, 80: 2, 112: 3, 144: 4}
def art_kunpeng_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    st = CH.get(kb, 1)
    q = ease_out(u / (1.2 * P))
    A.d['tianqing'].rectangle((60, 1180, W - 60, 1260), fill=140)
    waves(A, 1190, t, rows=2, amp=5)
    if st == 0:
        fish(A, lerp(300, 540, q), 1220, lerp(20, 50, q), t=t)
    elif st == 1:
        fish(A, 540, 1220, lerp(50, 200, q), t=t, layer='ink')
    elif st == 2:
        fish(A, 540, lerp(1220, 1100, q), 200 * (1 - 0.5 * q), t=t, layer='ink')
        peng(A, 540, lerp(1220, 1060, q), 160 * q, t, spread=q)
    elif st == 3:
        peng(A, 540, 1040, 200, t, spread=lerp(0.4, 1.0, q))
    else:
        peng(A, lerp(540, 900, q), lerp(1040, 840, q), lerp(200, 70, q), t, spread=1.0)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_kunpeng_chapter)
    ink_in(cv, text_img(no, SERIF, 56, TIANQING, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_seal(A, cv, t, u):
    ground(A, GROUND)
    king(A, 760, GROUND, 200, dir=-1, arm=lerp(20, 110, ease_out(u / P)))
    zhuang(A, lerp(400, 160, ease_out((u - P) / 0.8)), GROUND, 190, dir=-1, ph=t * 3 if u > P else None, arm=-8)

def art_z_hook_drum(A, cv, t, u):
    ground(A, GROUND)
    zhuang(A, 480, GROUND, 190, dir=1, kneel=True, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 8)))
    A.d['tianqing'].chord((560, GROUND - 90, 720, GROUND + 10), 180, 360, fill=255)

def art_z_hook_dream(A, cv, t, u):
    ground(A, GROUND)
    zhuang(A, 540, GROUND - 40, 200, dir=1, fall=-86, arm=-8)
    butterfly(A, 540 + 120 * math.sin(t * 1.3), 1000 + 60 * math.cos(t * 1.7), 50, t)

def art_z_hook_peng(A, cv, t, u):
    q = ease_out(u / (1.6 * P))
    peng(A, lerp(200, 760, q), lerp(1200, 900, q), 160, t)
    A.d['tianqing'].rectangle((60, 1300, W - 60, GROUND), fill=140)

# ================================================================ 第一回 漆园小吏
def art_z_birth(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    A.d['mid'].rectangle((360, 1080, 720, 1240), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 980)], fill=255)
    butterfly(A, 820, 1000, 30, t)
    A.flush(cv)
    stamp(cv, seal('宋国蒙地', 46), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('名周 · 宋国蒙人', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='tianqing')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    n = int(clamp(u / (2 * P)) * 8) + 1
    for i in range(n):
        bundle(A, 420 + (i % 5) * 50, GROUND - 74 - (i // 5) * 36, 40, layer='diehuang')
    A.flush(cv)
    paste(cv, text_img('其学无所不窥', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('本归老子', 44), 860, 1020, t, t - u + P, rot=6)

def art_z_lacquer(A, cv, t, u):
    for k in range(5):
        x = 180 + k * 180
        A.d['ink'].line((x, GROUND, x + 10, GROUND - 300), fill=255, width=12)
        A.d['grass'].ellipse((x - 90, GROUND - 400, x + 100, GROUND - 260), fill=200)
    ground(A, GROUND)
    zhuang(A, lerp(120, 560, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('曾为蒙漆园吏', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('漆园', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_sandals(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    zhuang(A, 360, GROUND, 170, dir=1, kneel=True, bow=30, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 6)))
    n = int(clamp(u / (2 * P)) * 6)
    for i in range(n):
        A.d['diehuang'].ellipse((440 + i * 40, GROUND - 24, 470 + i * 40, GROUND - 4), fill=255)
    A.flush(cv)
    paste(cv, text_img('处穷闾厄巷 · 困窘织屦', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_borrow(A, cv, t, u):
    A.d['dune'].rectangle((240, GROUND - 40, 840, GROUND), fill=220)
    A.d['ink'].line((260, GROUND - 20, 820, GROUND - 26), fill=200, width=6)
    fish(A, 540, GROUND - 24, 24, t=t * 0.3)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('我且南游吴越 激西江之水而迎子', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('曾不如早索我于枯鱼之肆', SERIF, 44, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('涸辙之鲋', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_weiwang(A, cv, t, u):
    """6-beat set piece: 衣弊履穿 — in patched robe and tied-up sandals he meets the King of Wei: 贫也 非惫也."""
    ph = u / P
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    king(A, 780, GROUND - 30, 200, dir=-1, arm=lerp(20, 100, clamp((ph - 1) / 0.4)))
    zhuang(A, lerp(-80, 380, ease_out(ph / 1.2)), GROUND, 200, dir=1, ph=t * 3 if ph < 1.2 else None, arm=lerp(-8, 90, clamp((ph - 2.6) / 0.4)))
    A.flush(cv)
    lab = '衣大布而补之 正緳系履' if ph < 1.4 else ('何先生之惫邪' if ph < 2.6 else '贫也 非惫也')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2.6 else TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph > 3.6:
        paste(cv, text_img('士有道德不能行 惫也', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 3.6) / 0.4))
    stamp(cv, seal('魏王', 54, INK), 260, 1020, t, t - u + 0.4, rot=-5)

def art_z_rat(A, cv, t, u):
    for k in range(3):
        A.d['ink'].line((200 + k * 300, GROUND, 210 + k * 300, GROUND - 320), fill=255, width=10)
    q = ease_out(u / (2.5 * P))
    peng(A, lerp(120, 900, q), 860, 50, t, layer='diehuang')
    crow(A, 330, GROUND - 330, 40, t * 3)
    A.d['ink'].ellipse((350, GROUND - 320, 380, GROUND - 304), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('惠子相梁 · 恐庄子夺其位', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    type_in(cv, text_img('非梧桐不止 鸱得腐鼠', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第二回 曳尾涂中
def art_z_turtle(A, cv, t, u):
    """6-beat set piece: 曳尾涂中 — two Chu envoys come to the river with gold; he points at a turtle dragging its tail in the mud,
    and at a turtle shell kept in a silk box on the temple altar."""
    ph = u / P
    river(A, 1240, t, rows=2, amp=4)
    zhuang(A, 220, 1240, 180, dir=1, kneel=True, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 0.8)))
    A.d['ink'].line((280, 1150, 520, 1080), fill=255, width=4)
    for j in range(2):
        person(A, 760 + j * 90, 1240, 170, dir=-1, robe=True, hat='knot', bow=20, arm=90, layer='mid')
    if ph >= 2:
        if ph < 4:
            turtle(A, lerp(400, 600, (ph - 2) / 2), 1250, 50)
            A.d['dune'].rectangle((360, 1250, 700, 1270), fill=200)
        else:
            A.d['diehuang'].rectangle((440, 1000, 640, 1120), fill=255)
            A.d['ink'].rectangle((440, 1000, 640, 1120), outline=255, width=5)
            turtle(A, 540, 1100, 60, layer='mid')
    A.flush(cv)
    lab = '楚威王使人以千金聘之' if ph < 2 else ('宁其生而曳尾于涂中乎' if ph < 4 else '宁其死为留骨而贵乎')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph > 5:
        paste(cv, text_img('往矣 吾将曳尾于涂中', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 5) / 0.4))

def art_z_hao(A, cv, t, u):
    """6-beat set piece: 濠梁之辩 — two friends on a bridge above swimming fish; the famous exchange, line by line."""
    ph = u / P
    river(A, 1260, t, rows=3, amp=4)
    A.d['ink'].arc((200, 1100, 880, 1440), 200, 340, fill=255, width=14)
    for j in range(4):
        fish(A, (t * 60 + j * 240) % (W - 200) + 100, 1330 + (j % 2) * 30, 22, t=t + j)
    zhuang(A, 440, 1130, 170, dir=1, arm=lerp(-8, 70, clamp(ph / 0.4)))
    person(A, 640, 1130, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), layer='tianqing')
    A.flush(cv)
    lines = [('鯈鱼出游从容 是鱼之乐也', TIANQING), ('子非鱼 安知鱼之乐', INK), ('子非我 安知我不知鱼之乐', ZHU)]
    k = min(2, int(ph / 2))
    paste(cv, text_img(lines[k][0], SERIF, 44, lines[k][1], 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 2 * k) / 0.3))
    stamp(cv, seal('惠施', 50, INK), 860, 1020, t, t - u + 2 * P, rot=6)

def art_z_tree(A, cv, t, u):
    A.d['ink'].line((540, GROUND, 520, GROUND - 260), fill=255, width=40)
    for k in range(7):
        a = math.radians(200 + k * 24)
        A.d['ink'].line((520, GROUND - 240, 520 + 260 * math.cos(a), GROUND - 240 + 180 * math.sin(a)), fill=255, width=12)
        A.d['grass'].ellipse((520 + 260 * math.cos(a) - 90, GROUND - 240 + 180 * math.sin(a) - 60, 520 + 260 * math.cos(a) + 90, GROUND - 240 + 180 * math.sin(a) + 60), fill=200)
    ground(A, GROUND)
    zhuang(A, 820, GROUND, 170, dir=-1, fall=-80, arm=-8)
    A.flush(cv)
    paste(cv, text_img('不夭斤斧 物无害者 无所可用 安所困苦哉', SERIF, 38, TIANQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('大樗', 54), 260, 1020, t, t - u + P, rot=-5)

def art_z_well(A, cv, t, u):
    A.d['mid'].ellipse((380, GROUND - 60, 700, GROUND + 40), fill=230)
    A.d['ink'].ellipse((380, GROUND - 60, 700, GROUND + 40), outline=255, width=8)
    A.d['tianqing'].ellipse((410, GROUND - 40, 670, GROUND + 20), fill=200)
    A.d['grass'].ellipse((510, GROUND - 40, 570, GROUND - 4), fill=255)
    turtle(A, lerp(980, 820, ease_out(u / (2 * P))), GROUND - 10, 50, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('井鼃不可以语于海者 拘于虚也', SERIF, 42, TIANQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('秋水', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_monkeys(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    n = 6
    for i in range(n):
        x = 180 + i * 80
        A.d['mid'].ellipse((x - 26, GROUND - 70, x + 26, GROUND - 10), fill=255)
        A.d['mid'].ellipse((x - 16, GROUND - 100, x + 16, GROUND - 68), fill=255)
        A.d['mid'].line((x + 20, GROUND - 30, x + 40, GROUND - 60 - 20 * math.sin(t * 5 + i)), fill=255, width=4)
    A.flush(cv)
    lab = '朝三而暮四 众狙皆怒' if u < 2 * P else '朝四而暮三 众狙皆悦'
    paste(cv, text_img(lab, SERIF, 46, ZHU if u >= 2 * P else TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('狙公赋芧', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_ox(A, cv, t, u):
    """6-beat set piece: 庖丁解牛 — the cook's blade glides through the joints; the ox falls apart like earth; the blade is still new."""
    ph = u / P
    ground(A, GROUND)
    sep = ease_out((ph - 3) / 1.2) * 40
    parts = [(-160, -60, -40, 40), (-40, -60, 80, 40), (80, -60, 200, 40), (-180, -120, -60, -60), (180, -100, 260, -30)]
    for i, (x0, y0, x1, y1) in enumerate(parts):
        dx = (i - 2) * sep * 0.5; dy = sep * (0.3 if i % 2 else -0.2)
        A.d['mid'].rounded_rectangle((540 + x0 + dx, 1160 + y0 + dy, 540 + x1 + dx, 1160 + y1 + dy), radius=20, fill=230)
    for lx in (-140, -60, 100, 170):
        A.d['mid'].line((540 + lx, 1200, 540 + lx, GROUND), fill=230, width=16)
    if ph < 4:
        a = t * 3
        kx = 540 + 200 * math.sin(a)
        ky = 1130 + 40 * math.cos(a * 1.3)
        A.d['wash'].line((kx - 40, ky - 10, kx + 40, ky + 10), fill=255, width=8)
        A.d['tianqing'].line((kx - 40, ky - 10, kx + 40, ky + 10), fill=160, width=3)
    person(A, 200, GROUND, 190, dir=1, robe=False, hat='knot', arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    lab = '依乎天理 批大郤 导大窾' if ph < 3 else ('謋然已解 如土委地' if ph < 4.6 else '刀刃若新发于硎 · 游刃有余')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.6 else TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('十九年', 50), 860, 1020, t, t - u + 4.6 * P, rot=6)

# ================================================================ 第三回 庄周梦蝶
def scene_mengdie(cv, t, c, k):
    """8-beat custom scene: 庄周梦蝶 — he dozes under a tree; the scene dissolves into a meadow where a butterfly flies freely;
    he wakes; the butterfly and the sleeper overlap in a mirrored pair — which is dreaming which?"""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2 or ph >= 5:
        A.d['ink'].line((240, GROUND, 230, GROUND - 300), fill=255, width=24)
        A.d['grass'].ellipse((80, GROUND - 440, 400, GROUND - 240), fill=200)
        wake = ph >= 5
        zhuang(A, 420, GROUND - (0 if wake else 10), 200, dir=1, fall=0 if wake else -86, kneel=wake, arm=lerp(-8, 90, clamp((ph - 5.4) / 0.4)) if wake else -8)
        if wake:
            butterfly(A, lerp(700, 640, 0.5 + 0.5 * math.sin(t)), 1000 + 30 * math.sin(t * 1.4), 50, t)
    else:
        for j in range(12):
            A.d['diehuang' if j % 3 == 0 else 'grass'].ellipse((100 + j * 80 - 18, GROUND - 30 - (j % 3) * 12, 100 + j * 80 + 18, GROUND - (j % 3) * 12), fill=200)
        q = (ph - 2) / 3
        bx = lerp(140, 940, q); by = 1000 - 200 * math.sin(q * math.pi * 2) + 30 * math.sin(t * 3)
        butterfly(A, bx, by, 70, t)
        for j in range(3):
            butterfly(A, (bx + 300 + j * 230) % 880 + 100, 820 + j * 90 + 40 * math.sin(t * 2 + j), 26, t + j, layer='tianqing')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '庄周梦蝶', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=51)
    fx.flush(cv)
    lab = '昔者庄周梦为胡蝶' if ph < 2 else ('栩栩然胡蝶也 自喻适志与 不知周也' if ph < 5 else '俄然觉 则蘧蘧然周也')
    paste(cv, text_img(lab, SERIF, 44, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if ph > 6.3:
        paste(cv, text_img('不知周之梦为胡蝶与 胡蝶之梦为周与', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 6.3) / 0.4))

def art_z_basin(A, cv, t, u):
    A.d['mid'].rectangle((620, GROUND - 200, 920, GROUND), fill=200)
    A.d['ink'].polygon([(600, GROUND - 200), (940, GROUND - 200), (770, GROUND - 280)], fill=255)
    ground(A, GROUND)
    zhuang(A, 330, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 8)))
    A.d['tianqing'].chord((400, GROUND - 90, 560, GROUND + 10), 180, 360, fill=255)
    A.flush(cv)
    type_in(cv, text_img('箕踞鼓盆而歌', SERIF, 48, TIANQING, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.3, 0.4)
    type_in(cv, text_img('生死如春秋冬夏四时行也', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('妻死', 54, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_moisten(A, cv, t, u):
    A.d['dune'].rectangle((200, GROUND - 40, 880, GROUND), fill=220)
    q = clamp((u - 2 * P) / (1.5 * P))
    if q <= 0:
        fish(A, 500, GROUND - 30, 40, dir=1, t=t * 0.4)
        fish(A, 580, GROUND - 30, 40, dir=-1, t=t * 0.4)
        for k in range(4):
            yy = GROUND - 60 - ((t * 60 + k * 30) % 120)
            A.d['wash'].ellipse((540 - 10, yy - 10, 540 + 10, yy + 10), outline=200, width=3)
    else:
        A.d['tianqing'].rectangle((60, 1220, W - 60, GROUND), fill=150)
        waves(A, 1230, t, rows=2, amp=4)
        fish(A, lerp(500, 200, q), 1290, 40, dir=-1, t=t)
        fish(A, lerp(580, 880, q), 1310, 40, dir=1, t=t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('相呴以湿 相濡以沫', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('不如相忘于江湖', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((u - 2 * P) / 0.4))

def art_z_huizi(A, cv, t, u):
    A.d['mid'].chord((380, 1100, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    zhuang(A, 260, GROUND, 190, dir=1, bow=20, arm=-8, old=0.6)
    A.flush(cv)
    type_in(cv, text_img('自夫子之死也 吾无以为质矣', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('吾无与言之矣', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('运斤成风', 44), 860, 1020, t, t - u + P, rot=6)

def art_z_xiaoyao(A, cv, t, u):
    """8-beat set piece: 逍遥游 — a fish in the northern dark grows to 鲲, turns to 鹏, rises on the whirlwind
    ninety thousand li and flies south."""
    ph = u / P
    A.d['tianqing'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=3, amp=6, speed=1.4)
    if ph < 3:
        fish(A, 540, 1260, lerp(30, 220, ease_out(ph / 2.5)), t=t, layer='ink')
    else:
        q = clamp((ph - 3) / 4.5)
        peng(A, lerp(540, 860, q), lerp(1180, 760, ease_out(q)), lerp(220, 90, q), t, spread=clamp((ph - 3) / 0.8))
        for k in range(4):
            r = 60 + k * 50 + 30 * math.sin(t * 3 + k)
            A.d['wash'].arc((lerp(540, 860, q) - r, lerp(1260, 900, q) - r * 0.3, lerp(540, 860, q) + r, lerp(1260, 900, q) + r * 0.3), 0, 300, fill=150, width=4)
    A.flush(cv)
    li = int(lerp(0, 90000, clamp((ph - 3) / 4.5)))
    lab = '北冥有鱼 其名为鲲' if ph < 3 else ('化而为鸟 其名为鹏' if ph < 4.2 else f'抟扶摇而上者 {li}里')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.2 else TIANQING, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('逍遥游', 50), 260, 1020, t, t - u + 0.4, rot=-5)

def art_z_qiwu(A, cv, t, u):
    for k in range(9):
        a = t * 0.4 + k * 2 * math.pi / 9
        x, y = 540 + 280 * math.cos(a), 1060 + 160 * math.sin(a)
        if k % 3 == 0:
            butterfly(A, x, y, 24, t + k)
        elif k % 3 == 1:
            fish(A, x, y, 24, t=t + k)
        else:
            A.d['grass'].ellipse((x - 20, y - 20, x + 20, y + 20), fill=220)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('天地与我并生 而万物与我为一', SERIF, 44, TIANQING, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 逍遥
def art_z_write(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='tianqing')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    n = int(clamp(u / (2.5 * P)) * 10) + 1
    for i in range(n):
        bundle(A, 400 + (i % 5) * 56, GROUND - 74 - (i // 5) * 36, 42, layer='diehuang')
    A.flush(cv)
    paste(cv, text_img('著书十余万言 大抵率寓言也', SERIF, 44, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_life(A, cv, t, u):
    A.d['ink'].line((200, 1100, 520, 1100), fill=255, width=6)
    q = ease_out(u / (3 * P))
    A.d['tianqing'].line((200, 1180, 200 + 680 * q, 1180), fill=255, width=6)
    A.d['ink'].polygon([(520, 1086), (546, 1100), (520, 1114)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('吾生也有涯 而知也无涯', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('养生主', 50), 860, 1020, t, t - u + P, rot=6)

def art_z_wood(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300), (x + 150, GROUND)], fill=180)
    A.d['ink'].line((760, GROUND, 750, GROUND - 260), fill=255, width=26)
    A.d['grass'].ellipse((620, GROUND - 400, 880, GROUND - 220), fill=200)
    ground(A, GROUND)
    zhuang(A, 360, GROUND, 190, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)), old=0.6)
    sitter(A, 200, GROUND, 120, dir=1, bow=10, layer='mid')
    A.flush(cv)
    paste(cv, text_img('周将处乎材与不材之间', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('山木', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_calm(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=3, speed=0.6)
    boat(A, 540, 1250, 140, t, sail=False)
    zhuang(A, 540, 1240, 120, dir=1, kneel=True, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('安时而处顺 哀乐不能入也', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_coffin(A, cv, t, u):
    for k in range(40):
        a = k * 2 * math.pi / 40
        A.d['diehuang'].ellipse((540 + 380 * math.cos(a) - 6, 1060 + 260 * math.sin(a) - 6, 540 + 380 * math.cos(a) + 6, 1060 + 260 * math.sin(a) + 6), fill=200)
    ground(A, GROUND)
    zhuang(A, 540, GROUND - 20, 200, dir=1, fall=-86, arm=-8, old=0.8)
    A.flush(cv)
    type_in(cv, text_img('吾以天地为棺椁 以日月为连璧', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('吾葬具岂不备邪', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)

def art_z_death(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    lamp(A, 820, GROUND, 50, t, glow=clamp(1 - (u - P) / 1))
    A.flush(cv)
    paste(cv, text_img('卒年约八十余', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '生卒年均无确考', t, t - u + P)

def art_z_wuhua(A, cv, t, u):
    """6-beat set piece: 物化 — butterflies rise from the grass over the grave, more and more, and drift up into the sky."""
    ph = u / P
    A.d['mid'].chord((380, 1140, 700, 1320), 180, 360, fill=200)
    ground(A, GROUND)
    n = min(14, int(ph * 3) + 1)
    for j in range(n):
        q = ((t * 0.12 + j / 14) % 1)
        butterfly(A, 540 + 360 * math.sin(j * 1.7 + t * 0.5) * q, lerp(1180, 640, q), 30 + (j % 3) * 8, t + j, layer='diehuang' if j % 2 else 'tianqing')
    A.flush(cv)
    paste(cv, text_img('此之谓物化', SERIF, 48, TIANQING, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 1) / 0.4))

# ================================================================ 第五回 南华真经
def art_z_guoxiang(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='tianqing')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('郭象注庄 · 魏晋玄学大兴', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('三十三篇', 44), 860, 1020, t, t - u + P, rot=6)

def art_z_nanhua(A, cv, t, u):
    palace(A, 540, 1260, 400, layer='diehuang')
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('南华真人', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, dur=0.3)
    stamp(cv, seal('唐玄宗', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_z_jing(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 220, clamp(u / (1.5 * P)), layer='wash')
    A.flush(cv)
    im = text_img('南华真经', SERIF, 60, INK, 'Black', bleed=False, vertical=True, spacing=6)
    paste(cv, im, W / 2, 1100, 1, clamp((u - P) / 0.4))
    paste(cv, text_img('与道德经并列 道家经典', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_sushi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='tianqing')
    person(A, 320, GROUND, 200, dir=1, robe=True, hat='knot', kneel=True, arm=lerp(60, 140, ease_out((u - P) / 0.4)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('吾昔有见 口未能言 今见是书 得吾心矣', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.6)
    stamp(cv, seal('苏轼', 54), 860, 1020, t, t - u + P, rot=6)

def art_z_idioms(A, cv, t, u):
    ground(A, GROUND)
    words = ['庖丁解牛', '井底之蛙', '鹏程万里', '朝三暮四', '相濡以沫', '游刃有余']
    A.flush(cv)
    n = min(6, int(u / (0.5 * P)) + 1)
    for i in range(n):
        paste(cv, text_img(words[i], SERIF, 40, ZHU if i == n - 1 else INK, 'Black', bleed=False, spacing=4), 320 + (i % 2) * 440, 1000 + (i // 2) * 90, 1, clamp((u - i * 0.5 * P) / 0.3))
    paste(cv, text_img('一部书 半部成语词典', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_free(A, cv, t, u):
    q = ease_out(u / (1.8 * P))
    peng(A, lerp(300, 760, q), lerp(1200, 900, q), 110, t)
    for j in range(4):
        butterfly(A, 200 + j * 220, 1260 + 30 * math.sin(t * 2 + j), 26, t + j)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('乘天地之正 御六气之辩', SERIF, 46, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_spirit(A, cv, t, u):
    for k in range(5):
        q = (t * 0.25 + k / 5) % 1
        A.d['tianqing'].ellipse((540 - 300 * q, 1080 - 200 * q, 540 + 300 * q, 1080 + 200 * q), outline=int(200 * (1 - q)), width=5)
    butterfly(A, 540, 1080, 50, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('独与天地精神往来', SERIF, 48, TIANQING, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    A.d['tianqing'].rectangle((60, 1380, W - 60, 1440), fill=150)
    butterfly(A, 860, 1320, 40, t)

def art_z_title(A, cv, t, u):
    butterfly(A, 800 + 60 * math.sin(t * 1.3), 1000 + 40 * math.cos(t * 1.1), 70, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhuang(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '漆园小吏'), 48: ('第二回', '曳尾涂中'), 80: ('第三回', '庄周梦蝶'),
            112: ('第四回', '逍遥'), 144: ('第五回', '南华真经')}

CARDS = [
    C(0, 2, 'court', 'num', num='宰相之位', line='他不要', art=art_z_hook_seal),
    C(2, 4, 'death', 'num', num='妻子去世', line='他敲盆唱歌', art=art_z_hook_drum),
    C(4, 6, 'night', 'num', num='一个梦', line='想了两千年', art=art_z_hook_dream),
    C(6, 8, 'empire', 'num', num='九万里', line='扶摇直上', art=art_z_hook_peng),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 漆园小吏
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-369, main='生于宋国', sub='蒙人庄周', note='生卒年均为约数', art=art_z_birth),
    C(22, 26, 'works', 'card', year=-350, main='博览群书', sub='归于老子', art=art_z_study),
    C(26, 30, 'court', 'card', year=-340, main='漆园吏', sub='一个小官', art=art_z_lacquer),
    C(30, 34, 'fate', 'card', year=-335, main='织屦为生', sub='穷得揭不开锅', art=art_z_sandals),
    C(34, 38, 'night', 'card', year=-333, main='涸辙之鲋', sub='借粮被拒', art=art_z_borrow),
    C(38, 44, 'court', 'card', year=-331, main='贫而非惫', sub='破衣见魏王', art=art_z_weiwang),
    C(44, 48, 'war', 'card', year=-330, main='腐鼠之讥', sub='老友惠施', art=art_z_rat),
    # ---- 第二回 曳尾涂中
    C(48, 50, 'fate', 'chapter'),
    C(50, 56, 'court', 'card', year=-328, main='曳尾涂中', sub='楚王聘相', art=art_z_turtle),
    C(56, 62, 'war', 'card', year=-326, main='濠梁之辩', sub='子非鱼', art=art_z_hao),
    C(62, 66, 'life', 'card', year=-325, main='无用之用', sub='大树的智慧', art=art_z_tree),
    C(66, 70, 'works', 'card', year=-322, main='井底之蛙', sub='秋水篇', art=art_z_well),
    C(70, 74, 'night', 'card', year=-321, main='朝三暮四', sub='名实未亏', art=art_z_monkeys),
    C(74, 80, 'works', 'card', year=-320, main='庖丁解牛', sub='养生之道', art=art_z_ox),
    # ---- 第三回 庄周梦蝶
    C(80, 82, 'night', 'chapter'),
    C(82, 90, 'night', 'mengdie', year=-320),
    C(90, 94, 'death', 'card', year=-318, main='鼓盆而歌', sub='妻子去世', art=art_z_basin),
    C(94, 98, 'life', 'card', year=-315, main='相忘江湖', sub='相濡以沫之后', art=art_z_moisten),
    C(98, 102, 'fate', 'card', year=-310, main='惠子之死', sub='失去对手', art=art_z_huizi),
    C(102, 110, 'empire', 'card', year=-305, main='逍遥游', sub='鲲鹏之志', art=art_z_xiaoyao),
    C(110, 112, 'works', 'card', year=-305, main='齐物', sub='万物为一', art=art_z_qiwu),
    # ---- 第四回 逍遥
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'works', 'card', year=-300, main='著书', sub='寓言十九', art=art_z_write),
    C(118, 122, 'night', 'card', year=-295, main='生也有涯', sub='知也无涯', art=art_z_life),
    C(122, 126, 'life', 'card', year=-292, main='材与不材', sub='山木篇', art=art_z_wood),
    C(126, 130, 'fate', 'card', year=-290, main='安时处顺', sub='晚年', art=art_z_calm),
    C(130, 134, 'death', 'card', year=-286, main='天地为棺', sub='不要厚葬', art=art_z_coffin),
    C(134, 138, 'death', 'card', year=-286, main='庄周去世', sub='归于自然', art=art_z_death),
    C(138, 144, 'night', 'card', year=-286, main='物化', sub='蝶归何处', art=art_z_wuhua),
    # ---- 第五回 南华真经
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=300, main='郭象注庄', sub='魏晋风流', art=art_z_guoxiang),
    C(150, 154, 'court', 'card', year=742, main='南华真人', sub='唐玄宗追封', art=art_z_nanhua),
    C(154, 158, 'empire', 'card', year=742, main='南华真经', sub='道家经典', art=art_z_jing),
    C(158, 162, 'life', 'card', year=1080, main='苏轼读庄', sub='得吾心矣', art=art_z_sushi),
    C(162, 166, 'works', 'card', year=1080, main='成语宝库', sub='一本书的影响', art=art_z_idioms),
    C(166, 168, 'empire', 'card', year=1080, main='逍遥', sub='最自由的灵魂', art=art_z_free),
    C(168, 170, 'end', 'card', year=1080, main='物我两忘', sub='与天地往来', art=art_z_spirit),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾壹', col=TIANQING, acc=DIEHUANG, born=-369, died=-286, age0=-369,
    born_lab='约前369年', died_lab='约前286年', years_txt='约公元前369 — 约前286',
    hook_q='楚王请他当宰相 · 他为什么宁愿穷着？',
    name_line='庄周 · 字子休', name='庄子', seal='南华', title_art=art_z_title,
    q1='逍遥智者？', q2='消极避世？',
    end_art=art_z_legacy, end_big='逍遥游', end_seal='南华',
    end_l1='他一生贫穷 拒绝了宰相之位', end_l2='换来了两千年的自由',
    end_brush='天地与我并生', end_ask='你想当庄子 还是当宰相？评论区聊聊', next='李斯'),
    scenes=dict(chapter=scene_chapter, mengdie=scene_mengdie))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
