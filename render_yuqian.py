"""千古人物志 · 第贰拾集 · 于谦 (1398–1457)
Look: 铁青 + 烽火橙, 城垛 (battlement) corner borders, a 石灰 (limestone) chapter card: each chapter the block is
hammered further, then burned white.
Set pieces: 6-beat 石灰吟, 8-beat 土木堡 (camp on a dry hill, encircled), custom 8-beat scene 'defense'
(北京保卫战: nine gates, 德胜门 ambush with cannon, 瓦剌 pull back in five days).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zhangjuzheng as Jz     # engine + helpers (previous episode)
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
from render_zhangjuzheng import official, ingot

F.RIPPLE = False
STEEL = (54, 72, 98)                # 铁青
EMBER = (206, 98, 40)               # 烽火橙
S.LAYERS.append(('steel', STEEL, 0.85, 1.0))
S.LAYERS.append(('ember', EMBER, 0.85, 1.6))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='谦', life='白', court='清', night='夜', war='戰', empire='京', works='石', fate='忠', death='冤', end='谦')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'snow'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'war', 'fate'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (EMBER, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = None
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (STEEL, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

BEACONS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(BEACONS)
for _x in (150, 420, 760, 960):
    _d.rectangle((_x - 14, 1150, _x + 14, 1230), fill=STEEL + (34,))
    _d.polygon([(_x - 22, 1150), (_x + 22, 1150), (_x, 1128)], fill=STEEL + (34,))
MTN_COL = {'night': (34, 40, 52), 'death': (60, 62, 66), 'war': (104, 60, 42), 'works': (90, 96, 104), 'empire': (74, 80, 96)}
def draw_background(t, theme):
    """北方关山: hard blue-grey ranges, distant beacon towers with drifting smoke in war themes."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(180, 184, 190), (130, 140, 154), MTN_COL.get(theme, (88, 100, 118))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn']))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(BEACONS)
    if theme in ('war', 'night'):
        sm = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sm)
        for k, x in enumerate((150, 420, 760, 960)):
            for j in range(5):
                q = (t * 0.4 + j / 5 + k * 0.13) % 1
                r = 10 + 30 * q
                d.ellipse((x - r + 40 * q, 1120 - 260 * q - r, x + r + 40 * q, 1120 - 260 * q + r), fill=(60, 60, 64, int(50 * (1 - q))))
        canvas.alpha_composite(sm)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """城垛: a crenellated parapet strip on each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = STEEL + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.rectangle((min(x, x + sx * 180), min(y, y + sy * 8), max(x, x + sx * 180), max(y, y + sy * 8)), fill=col)
        d.rectangle((min(x, x + sx * 8), min(y, y + sy * 180), max(x, x + sx * 8), max(y, y + sy * 180)), fill=col)
        for k in range(4):
            a = 20 + k * 42
            d.rectangle((min(x + sx * a, x + sx * (a + 22)), min(y + sy * 8, y + sy * 26), max(x + sx * a, x + sx * (a + 22)), max(y + sy * 8, y + sy * 26)), fill=col)
            d.rectangle((min(x + sx * 8, x + sx * 26), min(y + sy * a, y + sy * (a + 22)), max(x + sx * 8, x + sx * 26), max(y + sy * a, y + sy * (a + 22))), fill=col)
        d.ellipse((x + sx * 40 - 6, y + sy * 40 - 6, x + sx * 40 + 6, y + sy * 40 + 6), fill=EMBER + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, sash=True, **kw):
    """于谦: robe with a red sash and a 展脚幞头 (very long straight wings)."""
    capped = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if capped else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if capped:
        d = A.d[layer]
        d.rectangle((x - 0.06 * h, y - 1.05 * h, x + 0.06 * h, y - 0.94 * h), fill=255)
        d.rectangle((x - 0.36 * h, y - 0.995 * h, x + 0.36 * h, y - 0.98 * h), fill=255)
    if sash and not kneel and not kw.get('fall'):
        A.d['red'].rectangle((x - 0.1 * h, y - 0.56 * h, x + 0.1 * h, y - 0.5 * h), fill=255)
    return hand

def stone_block(A, cx, base, w, h, cut=0.0, burn=0.0):
    """limestone: a rough block; `cut` shaves facets and chips, `burn` whitens it."""
    r = random.Random(3)
    pts = []
    for i in range(14):
        a = math.pi + i * math.pi / 13
        rr = 1 - cut * 0.35 * (0.5 + 0.5 * math.sin(i * 2.3))
        pts.append((cx + w / 2 * rr * math.cos(a), base + h * rr * math.sin(a) * 1.0))
    pts += [(cx + w / 2, base), (cx - w / 2, base)]
    A.d['mid' if burn < 0.5 else 'wash'].polygon(pts, fill=int(lerp(230, 255, burn)))
    A.d['ink'].line(pts[:14], fill=int(lerp(220, 60, burn)), width=6)
    for k in range(int(cut * 12)):
        x = cx + r.uniform(-w / 2, w / 2); y = base - r.uniform(0, h * 0.8)
        A.d['ink'].line((x, y, x + r.uniform(-30, 30), y + r.uniform(10, 40)), fill=int(150 * (1 - burn)), width=3)

def cannon(A, x, y, s, dir=1, fire=0.0, layer='ink'):
    A.d[layer].polygon([(x - dir * 0.6 * s, y - 0.32 * s), (x + dir * 0.7 * s, y - 0.42 * s), (x + dir * 0.7 * s, y - 0.22 * s), (x - dir * 0.6 * s, y - 0.12 * s)], fill=255)
    A.d[layer].ellipse((x - 0.22 * s, y - 0.22 * s, x + 0.22 * s, y + 0.22 * s), outline=255, width=max(3, int(s * 0.06)))
    if fire > 0:
        mx = x + dir * 0.7 * s
        r = 0.5 * s * fire
        A.d['ember'].ellipse((mx + dir * r * 0.6 - r, y - 0.32 * s - r, mx + dir * r * 0.6 + r, y - 0.32 * s + r), fill=int(230 * fire))

def gate_tower(A, x, base, s, label=None, layer='steel'):
    A.d[layer].rectangle((x - 0.9 * s, base - 0.7 * s, x + 0.9 * s, base), fill=255)
    A.d['wash'].chord((x - 0.3 * s, base - 0.5 * s, x + 0.3 * s, base + 0.3 * s), 180, 360, fill=255)
    A.d['ink'].polygon([(x - 0.8 * s, base - 0.7 * s), (x + 0.8 * s, base - 0.7 * s), (x + 0.6 * s, base - 1.05 * s), (x - 0.6 * s, base - 1.05 * s)], fill=255)
    A.d['ink'].polygon([(x - 1.0 * s, base - 1.05 * s), (x + 1.0 * s, base - 1.05 * s), (x + 0.5 * s, base - 1.25 * s), (x - 0.5 * s, base - 1.25 * s)], fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.0), 48: (0.35, 0.0), 80: (0.7, 0.0), 112: (1.0, 0.3), 144: (1.0, 1.0)}
def art_lime_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    cut, burn = CH.get(kb, (0.35, 0.0))
    stone_block(A, 540, 1200, 460, 340, cut=cut, burn=burn)
    sw = math.sin(t * 9)
    hx, hy = 760, 860 + 40 * sw
    A.d['ink'].line((hx, hy, hx - 120, hy + 120), fill=255, width=10)
    A.d['ink'].rectangle((hx - 150, hy + 100, hx - 100, hy + 150), fill=255)
    if burn > 0:
        flames(A, 540, 1220, 520, 180 * burn, t, n=6, seed=5, smoke=True)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_lime_chapter)
    ink_in(cv, text_img(no, SERIF, 56, STEEL, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160 if len(title) <= 4 else 140, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_q_hook_one(A, cv, t, u):
    city_wall(A, 60, W - 60, 1180, label=None, layer='steel')
    yu(A, 540, 1180, 200, dir=-1, arm=lerp(-8, 70, ease_out(u / 0.6)))
    for k in range(9):
        rider(A, 120 + k * 100, GROUND + 10, 90, 1, t * 8 + k, layer='mid', spear=True, moving=False)

def art_q_hook_five(A, cv, t, u):
    ground(A, GROUND)
    p = ease_out(u / (1.6 * P))
    for k in range(6):
        x = lerp(500, 1100, p) + (k % 3) * 70; y = 1100 + (k // 3) * 120
        rider(A, x, y + 200, 100, 1, t * 12 + k, layer='mid')
    for k in range(5):
        ax = lerp(400, 900, (t * 0.8 + k * 0.2) % 1)
        arrow(A, ax, 1000 + k * 40, 0.0, 80)

def art_q_hook_empty(A, cv, t, u):
    A.d['mid'].rectangle((240, 820, 840, GROUND), fill=200)
    A.d['ink'].rectangle((240, 820, 840, GROUND), outline=255, width=8)
    A.d['wash'].rectangle((300, 880, 780, GROUND - 40), fill=255)
    for k in range(3):
        A.d['ink'].rectangle((340 + k * 150, 960, 440 + k * 150, 990), fill=200)
    q = (t * 0.6) % 1
    A.d['mid'].ellipse((560 + 200 * q, 1300, 580 + 200 * q, 1310), fill=int(200 * (1 - q)))

def art_q_hook_yiyu(A, cv, t, u):
    scroll(A, 540, 1040, 560, 300, u / 0.4, layer='wash')
    A.flush(cv)
    if u > 0.4:
        ink_in(cv, text_img('意欲', BRUSH, 170, ZHU), W / 2, 1040, t, t - u + 0.4, dur=0.3, settle=1.3)

# ================================================================ 第一回 清白少年
def art_q_birth(A, cv, t, u):
    A.d['ocean'].ellipse((140, 1160, 940, 1360), fill=110)
    A.d['ink'].arc((140, 1160, 940, 1360), 200, 340, fill=200, width=4)
    A.d['mid'].polygon([(120, 1200), (300, 1000), (480, 1200)], fill=200)
    A.d['ink'].rectangle((680, 1020, 700, 1200), fill=255)
    for k in range(5):
        y = 1020 + k * 34
        A.d['ink'].polygon([(650 - k * 4, y), (730 + k * 4, y), (690, y - 26)], fill=255)
    boat(A, lerp(300, 520, (t * 0.05) % 1), 1270, 70, t, sail=False)
    A.flush(cv)
    stamp(cv, seal('钱塘', 56), 860, 900, t, t - u + P, rot=6)

def art_q_portrait(A, cv, t, u):
    A.d['wash'].rectangle((560, 820, 820, 1220), fill=255)
    A.d['ink'].rectangle((560, 820, 820, 1220), outline=255, width=6)
    person(A, 690, 1190, 300, dir=-1, robe=True, hat='crown', arm=20, layer='mid')
    ground(A, GROUND)
    person(A, 380, GROUND, 160, dir=1, robe=True, hat='knot', bow=25, arm=70, layer='ink')
    A.flush(cv)
    stamp(cv, seal('文天祥', 46), 690, 760, t, t - u + P, rot=0)

def art_q_limestone(A, cv, t, u):
    """6-beat set piece: 石灰吟 — chisel strikes, kiln fire, white lime; one line per stage."""
    ph = u / P
    cut = clamp(ph / 2)
    burn = clamp((ph - 2.5) / 1.5)
    stone_block(A, 540, 1260, 420, 300, cut=cut, burn=burn)
    if ph < 2.5:
        hit = abs(math.sin(t * 7))
        hx, hy = 700, 900 + 80 * hit
        A.d['ink'].line((hx, hy, hx - 120, hy + 140), fill=255, width=10)
        A.d['ink'].rectangle((hx - 150, hy + 120, hx - 96, hy + 170), fill=255)
        if hit > 0.95:
            for j in range(6):
                a = -math.pi / 2 + (j - 2.5) * 0.4
                A.d['ink'].line((560, 1000, 560 + 70 * math.cos(a), 1000 + 70 * math.sin(a)), fill=200, width=4)
    if 2.5 <= ph < 4.5:
        flames(A, 540, 1270, 480, 240 * clamp((ph - 2.5) / 0.5), t, n=6, seed=12, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    lines = ['千锤万凿出深山', '烈火焚烧若等闲', '粉骨碎身浑不怕', '要留清白在人间']
    for i, ln in enumerate(lines):
        st = [0.2, 2.5, 3.6, 4.6][i]
        if ph >= st:
            type_in(cv, text_img(ln, SERIF, 44, ZHU if i == 3 else INK, 'Black', bleed=False, vertical=True, spacing=4),
                    880 - i * 64, 950, t, t - u + st * P, 0.5)

def art_q_jinshi(A, cv, t, u):
    palace(A, 540, GROUND, 540, layer='steel')
    ground(A, GROUND)
    yu(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 30, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('进士', 56), 860, 940, t, t - u + P, rot=6)

def art_q_rebuke(A, cv, t, u):
    ground(A, GROUND)
    yu(A, 340, GROUND, 260, dir=1, arm=lerp(30, 110, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 720, GROUND, 230, dir=-1, robe=True, hat='crown', kneel=True, bow=lerp(0, 60, ease_out((u - P) / 0.6)), arm=110, layer='ink')
    A.flush(cv)
    stamp(cv, seal('汉王朱高煦', 38, INK), 820, 920, t, t - u + 0.4, rot=6)

def art_q_governor(A, cv, t, u):
    pts = [(lerp(140, 940, f), 1000 + 160 * math.sin(f * 3.2)) for f in np.linspace(0, 1, 40)]
    A.d['yellow'].line(pts, fill=200, width=26)
    ground(A, GROUND)
    x = lerp(160, 760, ease_out(u / (3 * P)))
    horse(A, x, GROUND, 140, dir=1, ph=t * 8, moving=u < 3 * P, layer='ink')
    yu(A, x - 10, GROUND - 110, 140, dir=1, arm=20, sash=False)
    A.flush(cv)
    stamp(cv, seal('河南', 46), 300, 860, t, t - u + 0.5, rot=-5)
    stamp(cv, seal('山西', 46), 760, 820, t, t - u + P, rot=5)

def art_q_relief(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        A.d['steel'].rectangle((160 + k * 80, GROUND - 160, 220 + k * 80, GROUND), fill=255)
        A.d['steel'].polygon([(150 + k * 80, GROUND - 160), (190 + k * 80, GROUND - 200), (230 + k * 80, GROUND - 160)], fill=255)
    for k in range(5):
        x = lerp(1000, 520 + k * 90, ease_out((u - k * 0.2) / (2 * P)))
        person(A, x, GROUND, 130, dir=-1, robe=False, hat='knot', bow=20, arm=110, ph=t * 5 + k, layer='mid')
    yu(A, 470, GROUND, 200, dir=1, arm=80)
    A.flush(cv)
    stamp(cv, seal('平准仓', 50), 300, 1000, t, t - u + P, rot=-5)

# ================================================================ 第二回 两袖清风
def art_q_sleeves(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        official(A, 160 + k * 110, GROUND, 170, dir=1, layer='mid', arm=60)
        A.d['yellow'].rectangle((200 + k * 110, GROUND - 120, 250 + k * 110, GROUND - 80), fill=255)
    yu(A, 720, GROUND, 250, dir=-1, arm=lerp(-8, 130, 0.5 + 0.5 * math.sin(t * 2)), arm2=lerp(-8, -130, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(10):
        q = (t * 0.7 + k / 10) % 1
        A.d['wash'].line((620 + 200 * q, 1000 + 30 * math.sin(k + q * 6), 660 + 200 * q, 1000 + 30 * math.sin(k + q * 6)), fill=int(220 * (1 - q)), width=4)
    A.flush(cv)
    stamp(cv, seal('清风', 56), 860, 880, t, t - u + P, rot=6)

def art_q_wangzhen(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(20, 100, ease_out(u / 0.6)), layer='ink')
    yu(A, 300, GROUND, 200, dir=1, kneel=True, bow=10, arm=-10)
    for k in range(5):
        A.d['ink'].rectangle((220 + k * 34, 1180, 228 + k * 34, GROUND), fill=255)
    A.d['ink'].rectangle((210, 1172, 370, 1182), fill=255)
    A.flush(cv)
    stamp(cv, seal('王振', 54, INK), 760, 900, t, t - u + 0.4, rot=6)

def art_q_petition(A, cv, t, u):
    city_wall(A, 520, 1020, 1060, gate_x=770, label='京师', layer='mid')
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 24) + 1
    for i in range(n):
        x = 120 + (i % 8) * 50; y = GROUND - (i // 8) * 36
        person(A, x, y, 90, dir=1, robe=False, hat='knot', kneel=True, bow=40, arm=120, layer='ink' if i // 8 == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'请愿者 {n * 400} 人' if n < 25 else '请愿者以万计', SERIF, 46, STEEL, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_q_restored(A, cv, t, u):
    for k in range(5):
        x = 160 + k * 190
        A.d['grass'].rectangle((x - 70, GROUND - 60 - 40 * ease_out((u - k * 0.15) / (1.5 * P)), x + 70, GROUND), fill=200)
    ground(A, GROUND)
    x = lerp(-100, 540, ease_out(u / (2 * P)))
    yu(A, x, GROUND, 200, dir=1, ph=t * 5, arm=20)
    for k in range(4):
        person(A, 900 - k * 70, GROUND, 120, dir=-1, robe=False, hat='knot', arm=lerp(20, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')

def art_q_war_ministry(A, cv, t, u):
    A.d['steel'].rectangle((300, 900, 780, 1240), fill=255)
    A.d['wash'].rectangle((360, 960, 720, 1200), fill=255)
    for k in range(6):
        A.d['ink'].line((380, 990 + k * 34, 700, 990 + k * 34), fill=100, width=3)
    for k in range(int(clamp(u / (2 * P)) * 6)):
        A.d['red'].polygon([(400 + k * 50, 1000 + (k * 37) % 150), (420 + k * 50, 1000 + (k * 37) % 150), (410 + k * 50, 970 + (k * 37) % 150)], fill=255)
    ground(A, GROUND)
    yu(A, 860, GROUND, 220, dir=-1, arm=60)
    A.flush(cv)
    stamp(cv, seal('兵部', 56), 220, 900, t, t - u + P, rot=-5)

def art_q_esen(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 14) + 2
    for k in range(n):
        x = 980 - (k % 7) * 130 - (k // 7) * 60 - 40 * ((t * 0.5) % 1)
        rider(A, x, GROUND - (k // 7) * 60, 110 - (k // 7) * 18, -1, t * 10 + k, layer='ink' if k // 7 == 0 else 'mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('瓦剌', 56, INK), 860, 860, t, t - u + 0.4, rot=6)
    stamp(cv, seal('也先', 50), 260, 900, t, t - u + P, rot=-5)

def art_q_remonstrate(A, cv, t, u):
    palace(A, 540, 1140, 500, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((u - P) / 0.5)), layer='ink')
    person(A, 720, GROUND, 180, dir=-1, robe=True, hat='none', bow=20, arm=60, layer='mid')
    yu(A, 280, GROUND, 190, dir=1, kneel=True, bow=45, arm=90)
    A.flush(cv)
    stamp(cv, seal('力谏不从', 44), 280, 920, t, t - u + 1.5 * P, rot=-5)

# ================================================================ 第三回 土木之变
def art_q_tumu(A, cv, t, u):
    """8-beat set piece: 土木堡 — the army camps on a dry hill, wells come up empty,
    瓦剌 horsemen close a ring, the camp collapses, the emperor's banner falls."""
    ph = u / P
    A.d['mid'].polygon([(200, GROUND), (420, 1060), (660, 1060), (880, GROUND)], fill=220)
    for k in range(5):
        x = 420 + k * 60
        A.d['wash'].polygon([(x - 26, 1060), (x, 1020), (x + 26, 1060)], fill=255)
    for k in range(6):
        x = 450 + k * 36
        person(A, x, 1060, 70, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='steel')
    banner_fall = ease_out((ph - 6.5) / 0.6)
    A.d['ink'].line((540, 1060, 540 + 120 * banner_fall, 1060 - 200 * (1 - banner_fall) - 10), fill=255, width=6)
    A.d['yellow'].polygon([(540 + 120 * banner_fall, 1050 - 200 * (1 - banner_fall)), (540 + 120 * banner_fall + 80, 1070 - 200 * (1 - banner_fall)),
                           (540 + 120 * banner_fall, 1110 - 200 * (1 - banner_fall))], fill=255)
    if 1 <= ph < 3:
        for k in range(3):
            A.d['ink'].ellipse((300 + k * 220, 1300, 360 + k * 220, 1320), outline=255, width=4)
    ring = ease_out((ph - 2.5) / 2.5)
    if ring > 0:
        n = int(ring * 18)
        for k in range(n):
            a = math.pi + k * math.pi / 17
            rx = 540 + 460 * math.cos(a) * (1.1 - 0.25 * clamp((ph - 5) / 1.5))
            ry = GROUND - 10 + 60 * math.sin(a) * 0.3
            rider(A, rx, ry, 80, 1 if rx < 540 else -1, t * 9 + k, layer='ink', spear=True)
    if ph >= 5:
        for k in range(8):
            ang = -2.6 + k * 0.18
            ax = 540 + 360 * math.cos(ang) * (1 - clamp((ph - 5) / 1.2) * 0.6)
            ay = 1060 + 200 * math.sin(ang) * (1 - clamp((ph - 5) / 1.2) * 0.6)
            arrow(A, ax, ay, ang + math.pi, 70)
    A.flush(cv)
    if 1 <= ph < 3:
        paste(cv, text_img('掘井二丈 不得水', SERIF, 46, STEEL, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 1) / 0.3))
    if ph >= 6.5:
        stamp(cv, seal('英宗被俘', 50), 540, 860, t, t - u + 6.5 * P, rot=-6)

def art_q_south(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        official(A, 160 + k * 90, GROUND, 160, dir=1, layer='mid', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 3 + k)))
    yu(A, 700, GROUND, 260, dir=-1, arm=lerp(20, 150, ease_out((u - P) / 0.4)), sword=None)
    A.flush(cv)
    stamp(cv, seal('徐有贞', 44, INK), 250, 900, t, t - u + 0.4, rot=-5)
    if u > 1.5 * P:
        ink_in(cv, text_img('可斩', BRUSH, 120, ZHU), 760, 920, t, t - u + 1.5 * P, dur=0.25, settle=1.3)

def art_q_minister(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((470, 880, 610, 1020), fill=255)
    A.d['wash'].rectangle((500, 910, 580, 990), fill=255)
    yu(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 160, ease_out(u / (1.5 * P))))
    A.flush(cv)
    stamp(cv, seal('兵部尚书', 46), 840, 960, t, t - u + 1.5 * P, rot=6)

def art_q_new_emperor(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='steel')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    for k in range(4):
        x = 160 + k * 70 if k < 2 else 780 + (k - 2) * 70
        person(A, x, GROUND, 140, dir=1 if x < 540 else -1, robe=True, hat='none', kneel=True, bow=50, arm=100, layer='mid')
    yu(A, 330, GROUND, 170, dir=1, kneel=True, bow=50, arm=100)
    A.flush(cv)
    stamp(cv, seal('景泰', 56), 860, 880, t, t - u + P, rot=6)

def art_q_grain(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1300, W - 60, GROUND), fill=110)
    ground(A, 1300)
    n = 8
    for k in range(n):
        x = ((t * 120 + k * 150) % (W + 200)) - 100
        person(A, x, 1300, 110, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 6 + k, layer='ink' if k % 2 else 'mid')
    city_wall(A, 700, 1020, 1000, gate_x=860, label='通州', layer='mid', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('自取粮 免被敌所用', SERIF, 44, STEEL, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_q_nine_gates(A, cv, t, u):
    """6-beat: nine gates shut one by one, troops ranked outside."""
    city_wall(A, 60, W - 60, 1060, label=None, layer='steel')
    n = min(9, int(u / (0.5 * P)) + 1)
    for i in range(9):
        x = 110 + i * 107
        A.d['wash' if i >= n else 'ink'].rectangle((x - 30, 1150, x + 30, 1240), fill=255)
    ground(A, GROUND)
    for k in range(int(clamp(u / (4 * P)) * 22)):
        person(A, 100 + (k % 11) * 88, GROUND - (k // 11) * 50, 80, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='ink' if k // 11 == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'关闭城门 {n}/9', SERIF, 44, STEEL, 'Black', bleed=False, spacing=4), W / 2, 960, 1, 1)
    if u > 4.5 * P:
        paste(cv, text_img('二十二万 背城列阵', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 4.5 * P) / 0.3))

# ================================================================ 第四回 北京保卫战
DEF_DAYS = [(0, '十月十一', '瓦剌兵临城下'), (2, '十月十三', '德胜门 伏兵火器齐发'), (4, '十月十四', '西直门 彰义门 连战'), (6, '十月十五', '也先夜遁')]
def scene_defense(cv, t, c, k):
    """8-beat custom scene: Beijing from above — the square city with nine gates; 瓦剌 arrows from the NW,
    德胜门 ambush flashes, attacks broken at other gates, the arrows reverse and leave."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    cx, cy, R = 540, 1060, 260
    A.d['steel'].rectangle((cx - R, cy - R, cx + R, cy + R), outline=255, width=16)
    A.d['mid'].rectangle((cx - 80, cy - 80, cx + 80, cy + 80), fill=200)
    gates = {'德胜门': (cx - 120, cy - R), '安定门': (cx + 120, cy - R), '西直门': (cx - R, cy - 120), '彰义门': (cx - R, cy + 160)}
    for nm, (gx, gy) in gates.items():
        A.d['ink'].rectangle((gx - 22, gy - 22, gx + 22, gy + 22), fill=255)
    retreat = ease_out((ph - 6) / 1.5)
    tgt = [gates['德胜门'], gates['西直门'], gates['彰义门']]
    for i, (gx, gy) in enumerate(tgt):
        arrive = ease_out((ph - i * 0.6) / 1.5)
        sx, sy = 120 + i * 20, 680 + i * 80
        ex = lerp(sx, gx - 40, arrive * (1 - retreat)); ey = lerp(sy, gy - 30, arrive * (1 - retreat))
        A.d['ink'].line((sx - 60 * retreat, sy - 60 * retreat, ex, ey), fill=255, width=14)
        ang = math.atan2(ey - sy, ex - sx) + (math.pi if retreat > 0.5 else 0)
        A.d['ink'].polygon([(ex + 30 * math.cos(ang), ey + 30 * math.sin(ang)), (ex + 18 * math.cos(ang + 2.3), ey + 18 * math.sin(ang + 2.3)),
                            (ex + 18 * math.cos(ang - 2.3), ey + 18 * math.sin(ang - 2.3))], fill=255)
    for i, (b, (gx, gy)) in enumerate(((2, gates['德胜门']), (4, gates['西直门']), (4.6, gates['彰义门']))):
        f = clamp((ph - b) / 0.8)
        if 0 < f < 1:
            r = 40 + 120 * f
            A.d['ember'].ellipse((gx - 40 - r, gy - 30 - r, gx - 40 + r, gy - 30 + r), fill=int(220 * (1 - f)))
    A.flush(cv)
    for nm, (gx, gy) in gates.items():
        if nm in ('德胜门', '西直门', '彰义门'):
            paste(cv, text_img(nm, SERIF, 32, INK, 'Black', bleed=False), gx + (120 if nm != '德胜门' else 0), gy + (0 if nm != '德胜门' else -50), 1, 0.9)
    stamp(cv, seal('京师', 44), cx, cy, t, s0)
    i = max(j for j, (b, *_) in enumerate(DEF_DAYS) if ph >= b)
    b, dd, txt = DEF_DAYS[i]
    ink_in(cv, text_img(f'{dd} · {txt}', SERIF, 44, STEEL, 'Black', bleed=False, spacing=4), W / 2, 1448, t, s0 + b * P, dur=0.2, settle=1.0)
    days = min(5, int(ph / 1.5) + 1)
    fx = Art()
    chars_in(cv, fx, '北京保卫战', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=130)
    fx.flush(cv)
    paste(cv, text_img(f'第{cn_num(days)}天', SERIF, 52, ZHU, 'Black', bleed=False, spacing=4), W / 2, 570, 1, 1)
    if ph >= 6.5:
        stamp(cv, seal('击退', 64), 860, 820, t, s0 + 6.5 * P, rot=8)

def art_q_esen_flees(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = lerp(500, -300, ease_out(u / (3 * P))) + (k % 5) * 130 + (k // 5) * 60
        rider(A, x, GROUND - (k // 5) * 40, 110, -1, t * 12 + k, layer='mid' if k // 5 else 'ink')
    yu(A, 860, 1180, 200, dir=-1, arm=60)
    A.d['steel'].rectangle((720, 1180, W - 60, GROUND), fill=255)
    for k in range(4):
        A.d['steel'].rectangle((730 + k * 80, 1150, 770 + k * 80, 1180), fill=255)
    A.flush(cv)
    stamp(cv, seal('挟上皇北去', 40, INK), 300, 900, t, t - u + P, rot=-5)

def art_q_return(A, cv, t, u):
    palace(A, 700, GROUND, 400, layer='mid')
    A.d['ink'].rectangle((480, 1100, 920, 1120), fill=255)
    for k in range(9):
        A.d['ink'].rectangle((490 + k * 50, 1120, 500 + k * 50, GROUND), fill=255)
    ground(A, GROUND)
    x = lerp(-120, 300, ease_out(u / (2.5 * P)))
    carriage(A, x, GROUND, 130, dir=1, wheel=u * 5, ph=t * 7, moving=u < 2.5 * P, layer='ink')
    A.flush(cv)
    stamp(cv, seal('南宫', 56), 700, 900, t, t - u + 2 * P, rot=6)

def art_q_tuanying(A, cv, t, u):
    ground(A, GROUND)
    groups = min(10, int(clamp(u / (2 * P)) * 10) + 1)
    for g in range(groups):
        gx = 140 + (g % 5) * 200; gy = GROUND - (g // 5) * 140
        for j in range(4):
            person(A, gx - 45 + j * 30, gy, 80, dir=1, robe=False, hat='helmet', spear=True, arm=30, ph=t * 6 if u < 2 * P else None,
                   layer='ink' if g // 5 == 0 else 'mid')
        flag(A, gx + 70, gy, 160, t, w=40)
    A.flush(cv)
    paste(cv, text_img(f'十团营 · 第{cn_num(groups)}营', SERIF, 44, STEEL, 'Black', bleed=False, spacing=4), W / 2, 900, 1, 1)

def art_q_frugal(A, cv, t, u):
    A.d['mid'].polygon([(300, 1160), (540, 1000), (780, 1160)], fill=200)
    A.d['mid'].rectangle((340, 1160, 740, GROUND), fill=200)
    A.d['wash'].rectangle((480, 1240, 600, GROUND), fill=255)
    for k in range(int((t * 2) % 6)):
        A.d['wash'].line((360 + k * 60, 1100 + k * 10, 380 + k * 60, 1130 + k * 10), fill=255, width=3)
    ground(A, GROUND)
    sitter(A, 540, GROUND, 140, dir=1)
    lamp(A, 640, GROUND, 40, t, glow=0.4)
    A.flush(cv)
    stamp(cv, seal('辞第不受', 44), 860, 940, t, t - u + P, rot=6)

def art_q_ill_emperor(A, cv, t, u):
    A.d['mid'].rectangle((280, 1180, 800, 1240), fill=230)
    A.d['ink'].rectangle((260, 1240, 820, 1270), fill=255)
    person(A, 540, 1180, 200, dir=1, robe=True, hat='crown', fall=-88, layer='ink')
    for k in range(30):
        q = (t * 0.2 + k / 30) % 1
        x = 100 + (k * 31) % 880
        A.d['mid'].ellipse((x - 3, lerp(640, 1100, q) - 3, x + 3, lerp(640, 1100, q) + 3), fill=int(200 * (1 - q)))
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('储位未定', 44, INK), 860, 900, t, t - u + P, rot=6)

def art_q_coup(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    gate_tower(A, 540, GROUND, 260)
    p = ease_out((u - P) / 0.8)
    A.d['ink'].rectangle((540 - 78, GROUND - 130, 540 - 78 + 70 * (1 - p), GROUND), fill=255)
    A.d['ink'].rectangle((540 + 8 + 70 * p, GROUND - 130, 540 + 78, GROUND), fill=255)
    ground(A, GROUND)
    for k in range(5):
        x = lerp(-50, 480, ease_out((u - 0.2 * k) / (2.5 * P))) - k * 70
        person(A, x, GROUND, 140, dir=1, robe=False, hat='helmet', spear=True, ph=t * 8 + k, arm=40, layer='ink')
        A.d['ember'].ellipse((x + 30, GROUND - 210, x + 60, GROUND - 180), fill=230)
    A.flush(cv)
    stamp(cv, seal('石亨', 44, INK), 220, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('复辟', 56), 860, 880, t, t - u + 2 * P, rot=6)

# ================================================================ 第五回 要留清白
def art_q_prison(A, cv, t, u):
    A.d['mid'].rectangle((240, 860, 840, GROUND), fill=200)
    yu(A, 540, GROUND, 230, dir=1, sash=False, arm=-8)
    for k in range(9):
        A.d['ink'].rectangle((280 + k * 66, 860, 292 + k * 66, GROUND), fill=255)
    A.d['ink'].rectangle((240, 860, 840, 880), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('谋逆', 56), 860, 820, t, t - u + P, rot=8)

def art_q_two_words(A, cv, t, u):
    A.d['wash'].rectangle((240, 860, 840, 1300), fill=255)
    A.d['ink'].rectangle((240, 860, 840, 1300), outline=255, width=6)
    for k in range(7):
        A.d['ink'].line((280, 900 + k * 50, 800, 900 + k * 50), fill=60, width=2)
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('意', BRUSH, 220, ZHU), 420, 1080, t, t - u + 0.3, dur=0.3, settle=1.4)
    ink_in(cv, text_img('欲', BRUSH, 220, ZHU), 660, 1080, t, t - u + P, dur=0.3, settle=1.4)

def art_q_execution(A, cv, t, u):
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        x = 80 + (k * 17) % 920
        A.d['wash'].ellipse((x - 5, lerp(620, 1420, q) - 5, x + 5, lerp(620, 1420, q) + 5), fill=230)
    gate_tower(A, 760, GROUND, 180, layer='mid')
    ground(A, GROUND)
    yu(A, 360, GROUND, 230, dir=1, sash=False, arm=-8)
    for k in range(6):
        person(A, 120 + k * 50, GROUND, 110, dir=1, robe=False, hat='knot', bow=40, arm=120, layer='mid')
    A.flush(cv)
    stamp(cv, seal('崇文门', 50, INK), 760, 900, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('阴霾四合 天下冤之', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 1.5 * P, 0.5)

def art_q_no_wealth(A, cv, t, u):
    A.d['mid'].rectangle((200, 880, 880, GROUND), fill=170)
    p = ease_out(u / (1.2 * P))
    A.d['wash'].rectangle((540 - 300 * p, 940, 540 + 300 * p, GROUND - 40), fill=255)
    if p > 0.8:
        for k in range(6):
            A.d['ink'].rectangle((300 + k * 40, 1100, 330 + k * 40, 1240), fill=200)
        A.d['yellow'].polygon([(620, 1240), (760, 1240), (740, 1120), (640, 1120)], fill=255)
        A.d['ink'].line((800, 1000, 840, 1240), fill=255, width=8)
    ground(A, GROUND)
    for k in range(2):
        person(A, 120 + k * 60, GROUND, 160, dir=1, robe=False, hat='helmet', arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('御赐蟒衣', 44), 700, 1020, t, t - u + 1.6 * P, rot=6)
    paste(cv, text_img('家无余资', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 820, 1, clamp((u - 2.2 * P) / 0.3))

def art_q_rehab(A, cv, t, u):
    scroll(A, 540, 980, 560, 260, u / 0.6, layer='yellow')
    ground(A, GROUND)
    A.flush(cv)
    if u > 0.5:
        ink_in(cv, text_img('复其官', BRUSH, 110, ZHU), W / 2, 980, t, t - u + 0.5, dur=0.3, settle=1.2)
    stamp(cv, seal('成化', 50, INK), 860, 1200, t, t - u + 1.5 * P, rot=6)

def art_q_west_lake(A, cv, t, u):
    A.d['ocean'].polygon([(60, 1200), (W - 60, 1180), (W - 60, GROUND), (60, GROUND)], fill=120)
    waves(A, 1210, t, rows=3, amp=4, speed=0.8)
    A.d['mid'].polygon([(560, 1180), (760, 960), (980, 1180)], fill=200)
    A.d['ink'].rectangle((800, 1060, 812, 1180), fill=255)
    for k in range(4):
        y = 1060 + k * 26
        A.d['ink'].polygon([(780 - k * 3, y), (832 + k * 3, y), (806, y - 22)], fill=255)
    for i, x in enumerate((220, 400)):
        A.d['mid'].chord((x - 70, 1110, x + 70, 1230), 180, 360, fill=230)
        A.d['ink'].rectangle((x - 10, 1080, x + 10, 1160), fill=255)
    A.flush(cv)
    stamp(cv, seal('岳飞', 44), 220, 1000, t, t - u + 0.4)
    stamp(cv, seal('于谦', 44), 400, 1000, t, t - u + P)

def art_q_legacy(A, cv, t, u):
    stone_block(A, 540, 1260, 460, 300, cut=1.0, burn=1.0)
    ground(A, GROUND)

def art_q_title(A, cv, t, u):
    city_wall(A, 60, W - 60, 1300, label=None, layer='steel')
    yu(A, 440, 1300, 640, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))))
    flag(A, 820, 1300, 520, t, w=120)

# ================================================================ script
CHAPTERS = {16: ('第一回', '清白少年'), 48: ('第二回', '两袖清风'), 80: ('第三回', '土木之变'),
            112: ('第四回', '北京保卫战'), 144: ('第五回', '要留清白')}

CARDS = [
    C(0, 2, 'war', 'num', num='一人', line='撑住了将倾的大明', art=art_q_hook_one),
    C(2, 4, 'war', 'num', num='五天', line='击退瓦剌大军', art=art_q_hook_five),
    C(4, 6, 'life', 'num', num='两袖清风', line='抄家时家无余财', art=art_q_hook_empty),
    C(6, 8, 'death', 'num', num='意欲', line='两个字要了他的命', art=art_q_hook_yiyu),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 清白少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1398, main='生于钱塘', sub='浙江杭州 · 自幼聪颖', note='传说 有僧奇之 曰救时宰相也', art=art_q_birth),
    C(22, 26, 'court', 'card', year=1405, main='敬文天祥', sub='在座旁悬挂文天祥像', note='终身奉为楷模', art=art_q_portrait),
    C(26, 32, 'works', 'card', year=1414, main='石灰吟', sub='借石灰明志', note='一说 少年时作', art=art_q_limestone),
    C(32, 36, 'empire', 'card', year=1421, main='进士及第', sub='二十二岁 · 入仕', art=art_q_jinshi),
    C(36, 40, 'war', 'card', year=1426, main='痛斥汉王', sub='随宣宗平叛 · 当面数其罪', note='高煦伏地战栗', art=art_q_rebuke),
    C(40, 44, 'works', 'card', year=1430, main='巡抚河南', sub='兼领山西 · 一任十九年', art=art_q_governor),
    C(44, 48, 'life', 'card', year=1436, main='赈灾救荒', sub='设平准仓 · 修堤种树', note='百姓称颂', art=art_q_relief),
    # ---- 第二回 两袖清风
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'court', 'card', year=1440, main='两袖清风', sub='入京奏事 · 不带一份礼物', note='清风两袖朝天去', art=art_q_sleeves),
    C(54, 58, 'night', 'card', year=1441, main='王振陷害', sub='宦官记恨 · 下狱论死', art=art_q_wangzhen),
    C(58, 62, 'life', 'card', year=1441, main='万民请愿', sub='河南山西百姓 · 伏阙上书', note='吏民伏阙上书 请留于谦', art=art_q_petition),
    C(62, 66, 'works', 'card', year=1441, main='官复原职', sub='重回巡抚任上', art=art_q_restored),
    C(66, 70, 'court', 'card', year=1448, main='兵部侍郎', sub='奉召回京', art=art_q_war_ministry),
    C(70, 74, 'war', 'card', year=1449, main='也先南侵', sub='瓦剌大军压境', art=art_q_esen),
    C(74, 80, 'night', 'card', year=1449, main='御驾亲征', sub='王振怂恿 · 英宗执意出征', note='于谦等力谏 不听', art=art_q_remonstrate),
    # ---- 第三回 土木之变
    C(80, 82, 'war', 'chapter'),
    C(82, 90, 'war', 'card', year=1449, main='土木堡', sub='大军覆没 · 皇帝被俘', note='死伤数十万', art=art_q_tumu),
    C(90, 94, 'night', 'card', year=1449, main='南迁之议', sub='有人主张迁都南京', note='言南迁者 可斩也', art=art_q_south),
    C(94, 98, 'court', 'card', year=1449, main='临危受命', sub='升任兵部尚书', note='以身任天下之重', art=art_q_minister),
    C(98, 102, 'empire', 'card', year=1449, main='拥立新君', sub='郕王即位 · 是为景泰帝', note='社稷为重 君为轻', art=art_q_new_emperor),
    C(102, 106, 'works', 'card', year=1449, main='调兵运粮', sub='征调各地兵马 · 抢运通州粮', art=art_q_grain),
    C(106, 112, 'war', 'card', year=1449, main='九门列阵', sub='城门尽闭 · 有进无退', note='将不顾军先退者 斩其将', art=art_q_nine_gates),
    # ---- 第四回 北京保卫战
    C(112, 114, 'war', 'chapter'),
    C(114, 122, 'war', 'defense', year=1449),
    C(122, 126, 'empire', 'card', year=1449, main='也先败退', sub='挟英宗北逃', art=art_q_esen_flees),
    C(126, 130, 'court', 'card', year=1450, main='迎回上皇', sub='英宗归来 · 幽居南宫', art=art_q_return),
    C(130, 134, 'works', 'card', year=1451, main='创立团营', sub='整顿京营 · 强兵固边', art=art_q_tuanying),
    C(134, 138, 'life', 'card', year=1452, main='布衣蔬食', sub='居所仅蔽风雨', note='帝赐第 固辞不受', art=art_q_frugal),
    C(138, 142, 'night', 'card', year=1456, main='景泰病重', sub='储位未定 · 暗流涌动', art=art_q_ill_emperor),
    C(142, 144, 'night', 'card', year=1457, main='夺门之变', sub='英宗复辟', art=art_q_coup),
    # ---- 第五回 要留清白
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1457, main='下狱', sub='以谋逆罪下狱', art=art_q_prison),
    C(150, 154, 'fate', 'card', year=1457, main='意欲', sub='罪名只有两个字', note='意欲二字 何以服天下', art=art_q_two_words),
    C(154, 158, 'death', 'card', year=1457, main='崇文门外', sub='含冤被害', art=art_q_execution),
    C(158, 162, 'life', 'card', year=1457, main='家无余资', sub='抄家所见 · 唯有御赐之物', note='萧然仅书籍耳', art=art_q_no_wealth),
    C(162, 166, 'court', 'card', year=1466, main='平反昭雪', sub='成化帝恢复其官职', art=art_q_rehab),
    C(166, 170, 'end', 'card', year=1489, main='西湖之畔', sub='与岳飞一同长眠西湖', note='谥肃愍 后改忠肃', art=art_q_west_lake),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾', col=STEEL, acc=EMBER, born=1398, died=1457, age0=1398.6,
    hook_q='没有他 · 大明可能早就亡了？',
    name_line='于谦 · 字廷益', name='于谦', seal='节庵', title_art=art_q_title,
    q1='千古忠臣？', q2='咎由自取？',
    end_art=art_q_legacy, end_big='要留清白', end_seal='忠肃',
    end_l1='他救了大明 大明却杀了他', end_l2='西湖边的香火 至今未断',
    end_brush='清白在人间', end_ask='这样的结局 公平吗？评论区聊聊', next='孔子'),
    scenes=dict(chapter=scene_chapter, defense=scene_defense))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
