"""千古人物志 · 第拾玖集 · 张居正 (1525–1582)
Look: 紫檀 + 帑银, 方孔钱 corner borders, an 算盘 (abacus) chapter card that tallies higher each chapter.
Set pieces: 8-beat 考成法 (three ledgers, ticks and red strokes), 6-beat 清丈田亩 (land grid measured),
custom 8-beat scene 'whip' (一条鞭法: a dozen levies bundled into one silver ingot).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_wangyangming as Wy     # engine + helpers (previous episode)
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

F.RIPPLE = False
SANDAL = (98, 44, 46)               # 紫檀
SILVER = (150, 160, 172)            # 帑银
S.LAYERS.append(('sandal', SANDAL, 0.85, 1.0))
S.LAYERS.append(('silver', SILVER, 0.90, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='正', life='圭', court='阁', night='夜', war='戰', empire='明', works='法', fate='鞭', death='抄', end='正')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire', 'works', 'fate'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['empire']['sun'] = (SILVER, 240, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (SANDAL, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

ROOFS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(ROOFS)
for _x in range(120, W - 100, 230):
    _d.polygon([(_x - 70, 1250), (_x, 1222), (_x + 70, 1250)], fill=SANDAL + (40,))
    _d.rectangle((_x - 50, 1250, _x + 50, 1300), fill=SANDAL + (28,))
MTN_COL = {'night': (40, 34, 38), 'death': (62, 58, 58), 'war': (100, 56, 44), 'works': (92, 72, 70), 'fate': (88, 54, 56)}
def draw_background(t, theme):
    """宫城远景: plain ranges with a long low palace wall line in the distance."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 178, 176), (150, 128, 126), MTN_COL.get(theme, (110, 84, 82))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn']))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(ROOFS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """方孔钱: a short string of square-holed coins along each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = SANDAL + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 170, y), fill=col, width=3); d.line((x, y, x, y + sy * 170), fill=col, width=3)
        for k, (cx, cy) in enumerate(((x + sx * 30, y + sy * 30), (x + sx * 80, y + sy * 18), (x + sx * 18, y + sy * 80))):
            r = 20 if k == 0 else 13
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SILVER + (240,), width=4)
            d.rectangle((cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35), outline=col, width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """张居正: official robe, 乌纱帽 with two straight wings, long beard."""
    capped = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if capped else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if capped:
        d = A.d[layer]
        d.rounded_rectangle((x - 0.07 * h, y - 1.06 * h, x + 0.07 * h, y - 0.94 * h), radius=int(0.03 * h), fill=255)
        d.rectangle((x - dir * 0.05 * h, y - 1.10 * h, x + dir * 0.0 * h, y - 1.0 * h) if dir > 0 else
                    (x, y - 1.10 * h, x + 0.05 * h, y - 1.0 * h), fill=255)
        for s_ in (-1, 1):
            d.rectangle((min(x + s_ * 0.07 * h, x + s_ * 0.2 * h), y - 1.0 * h, max(x + s_ * 0.07 * h, x + s_ * 0.2 * h), y - 0.975 * h), fill=255)
        d.polygon([(x + dir * 0.02 * h, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.70 * h)], fill=255)
    return hand

def official(A, x, y, h, dir=1, layer='mid', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('bow') and not kw.get('fall'):
        A.d[layer].rectangle((x - 0.06 * h, y - 1.04 * h, x + 0.06 * h, y - 0.94 * h), fill=255)
        A.d[layer].rectangle((x - 0.16 * h, y - 0.99 * h, x + 0.16 * h, y - 0.975 * h), fill=255)
    return hand

def ingot(A, x, y, s, layer='silver'):
    """元宝: boat-shaped silver ingot with a domed centre."""
    A.d[layer].polygon([(x - s, y - 0.55 * s), (x - 0.55 * s, y - 0.25 * s), (x + 0.55 * s, y - 0.25 * s), (x + s, y - 0.55 * s),
                        (x + 0.7 * s, y), (x - 0.7 * s, y)], fill=255)
    A.d[layer].ellipse((x - 0.38 * s, y - 0.62 * s, x + 0.38 * s, y - 0.12 * s), fill=255)
    A.d['ink'].arc((x - 0.38 * s, y - 0.62 * s, x + 0.38 * s, y - 0.12 * s), 200, 340, fill=150, width=max(2, int(s * 0.05)))

def ledger(A, x, y, w, h, t, open_=1.0, ticks=0, red=0, layer='wash'):
    q = ease_out(open_)
    A.d[layer].rectangle((x - w / 2 * q, y - h / 2, x + w / 2 * q, y + h / 2), fill=255)
    A.d['sandal'].rectangle((x - w / 2 * q - 6, y - h / 2 - 6, x + w / 2 * q + 6, y + h / 2 + 6), outline=255, width=6)
    A.d['ink'].line((x, y - h / 2, x, y + h / 2), fill=200, width=3)
    rows = 6
    for i in range(rows):
        yy = y - h / 2 + 22 + i * (h - 40) / rows
        A.d['ink'].line((x - w / 2 * q + 16, yy, x - 18, yy), fill=120, width=3)
        A.d['ink'].line((x + 18, yy, x + w / 2 * q - 16, yy), fill=120, width=3)
        if i < ticks:
            A.d['ink'].line((x + w / 2 * q - 50, yy - 4, x + w / 2 * q - 38, yy + 6, x + w / 2 * q - 18, yy - 14), fill=255, width=5)
        if i < red:
            A.d['red'].line((x - w / 2 * q + 16, yy - 2, x - 18, yy + 2), fill=255, width=7)

def abacus(A, cx, cy, w, h, counts, t, p=1.0):
    q = ease_out(p)
    w2 = w * q / 2
    if w2 < 6: return
    A.d['sandal'].rectangle((cx - w2, cy - h / 2, cx + w2, cy + h / 2), outline=255, width=16)
    beam = cy - h / 2 + h * 0.3
    A.d['sandal'].rectangle((cx - w2, beam - 6, cx + w2, beam + 6), fill=255)
    n = len(counts)
    for i, cnt in enumerate(counts):
        x = cx - w2 + (i + 0.5) * (2 * w2 / n)
        A.d['ink'].line((x, cy - h / 2 + 8, x, cy + h / 2 - 8), fill=170, width=3)
        up = cnt >= 5; low = cnt % 5
        ty = beam - 22 if up else cy - h / 2 + 30
        A.d['ink'].ellipse((x - 26, ty - 13, x + 26, ty + 13), fill=255)
        for j in range(4):
            raised = j < low
            by = beam + 24 + j * 30 if raised else cy + h / 2 - 22 - (3 - j) * 30
            A.d['silver' if raised else 'ink'].ellipse((x - 26, by - 13, x + 26, by + 13), fill=255)

def sedan(A, x, y, s, t, bearers=4, layer='ink'):
    A.d['sandal'].rectangle((x - 0.5 * s, y - 1.3 * s, x + 0.5 * s, y - 0.45 * s), fill=255)
    A.d['sandal'].polygon([(x - 0.6 * s, y - 1.3 * s), (x, y - 1.6 * s), (x + 0.6 * s, y - 1.3 * s)], fill=255)
    A.d[layer].line((x - 1.4 * s, y - 0.62 * s, x + 1.4 * s, y - 0.62 * s), fill=255, width=max(4, int(s * 0.06)))
    for k in range(bearers):
        bx = x - 1.25 * s + k * (2.5 * s / max(1, bearers - 1))
        person(A, bx, y, 0.85 * s, dir=1, robe=False, hat='knot', ph=t * 7 + k * 1.3, arm=170, layer=layer)

# ================================================================ chapter card
CH = {16: [1, 0, 0, 0, 0], 48: [3, 1, 0, 0, 0], 80: [5, 3, 2, 0, 0], 112: [7, 5, 4, 3, 0], 144: [9, 9, 6, 6, 1]}
def art_abacus_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    tgt = CH.get(kb, [3, 1, 0, 0, 0])
    k = int(clamp(u / (1.2 * P)) * sum(tgt))
    cur = []
    for v in tgt:
        take = min(v, k); cur.append(take); k -= take
    abacus(A, 540, 960, 620, 400, cur, t, p=u / 0.45)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_abacus_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SANDAL, 'Black', bleed=False, spacing=12), W / 2, 1270, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1420, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_j_hook_treasury(A, cv, t, u):
    ground(A, GROUND)
    n = min(15, int(clamp(u / (1.6 * P)) * 15) + 1)
    for i in range(n):
        row = [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4][i]
        col = i - [0, 5, 9, 12, 14][row]
        x = 540 + (col - (4 - row) / 2) * 150; y = GROUND - row * 90
        ingot(A, x, y, 70)

def art_j_hook_boy(A, cv, t, u):
    ground(A, GROUND)
    zhang(A, 660, GROUND, 330, dir=-1, arm=lerp(20, 70, ease_out(u / 0.6)))
    person(A, 380, GROUND, 150, dir=1, robe=True, hat='crown', arm=20, layer='ink')
    desk(A, 380, GROUND, 220, layer='sandal')

def art_j_hook_seal(A, cv, t, u):
    ground(A, GROUND)
    A.d['sandal'].rectangle((300, 860, 780, GROUND), fill=255)
    A.d['ink'].rectangle((360, 940, 720, GROUND), fill=255)
    p = ease_out((u - 0.3) / 0.5)
    A.d['wash'].rectangle((420 + 60 * (1 - p), 1000, 660 - 60 * (1 - p), 1040), fill=255)
    A.d['wash'].rectangle((500 + 20 * (1 - p), 980, 580 - 20 * (1 - p), 1300), fill=255)

def art_j_hook_whip(A, cv, t, u):
    p = ease_out(u / (1.6 * P))
    pts = [(lerp(220, 860, f), 1100 + 120 * math.sin(f * 7 + t * 4) * (1 - f) * (1 - p * 0.7)) for f in np.linspace(0, 1, 30)]
    A.d['ink'].line(pts, fill=255, width=10)
    A.d['sandal'].rectangle((180, 1080, 240, 1220), fill=255)
    ingot(A, 540, GROUND, 140 * p + 10)
    ground(A, GROUND)

# ================================================================ 第一回 江陵神童
def art_j_turtle(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, 1420), fill=130)
    waves(A, 1210, t, rows=3, amp=6, speed=1.2)
    p = ease_out(u / (2 * P))
    tx, ty = 540, lerp(1320, 1180, p)
    A.d['wash'].ellipse((tx - 140, ty - 70, tx + 140, ty + 50), fill=255)
    A.d['ink'].ellipse((tx - 140, ty - 70, tx + 140, ty + 50), outline=200, width=5)
    for k in range(5):
        A.d['ink'].line((tx - 100 + k * 50, ty - 60, tx - 100 + k * 50, ty + 40), fill=120, width=3)
    A.d['wash'].ellipse((tx + 120, ty - 40, tx + 190, ty + 10), fill=255)
    A.flush(cv)
    stamp(cv, seal('白龟', 54), 860, 880, t, t - u + P, rot=6)

def art_j_rename(A, cv, t, u):
    ground(A, GROUND)
    official(A, 760, GROUND, 290, dir=-1, layer='ink', arm=lerp(20, 80, ease_out(u / 0.6)))
    person(A, 330, GROUND, 160, dir=1, robe=True, hat='knot', bow=20, arm=60, layer='ink')
    A.flush(cv)
    ink_in(cv, text_img('白圭', BRUSH, 110, (150, 140, 130)), 330, 1000, t, t - u + 0.3, dur=0.3)
    if u > 1.6 * P:
        ink_in(cv, text_img('居正', BRUSH, 120, ZHU), 560, 940, t, t - u + 1.6 * P, dur=0.3, settle=1.3)

def art_j_failed_on_purpose(A, cv, t, u):
    A.d['wash'].rectangle((360, 820, 720, 1200), fill=255)
    A.d['sandal'].rectangle((360, 820, 720, 1200), outline=255, width=8)
    for k in range(7):
        A.d['ink'].line((400 + k * 46, 860, 400 + k * 46, 1160), fill=140, width=4)
    p = ease_out((u - P) / 0.5)
    A.d['red'].line((380, 840, 380 + 320 * p, 840 + 340 * p), fill=255, width=14)
    ground(A, GROUND)
    person(A, 540, GROUND, 150, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('顾璘', 50, INK), 860, 900, t, t - u + 1.5 * P, rot=6)

def art_j_belt(A, cv, t, u):
    ground(A, GROUND)
    official(A, 720, GROUND, 300, dir=-1, layer='ink', arm=lerp(20, 95, ease_out(u / (1.5 * P))))
    zhang(A, 360, GROUND, 210, dir=1, bow=20, arm=60)
    p = ease_out(u / (1.5 * P))
    bx = lerp(700, 470, p)
    A.d['silver'].rounded_rectangle((bx - 90, 1110, bx + 90, 1140), radius=12, fill=255)
    for k in range(4):
        A.d['ink'].ellipse((bx - 72 + k * 46, 1116, bx - 56 + k * 46, 1134), fill=255)
    A.flush(cv)
    stamp(cv, seal('犀带', 54), 300, 900, t, t - u + 1.6 * P, rot=-6)

def art_j_jinshi(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='sandal')
    ground(A, GROUND)
    p = ease_out(u / (1.2 * P))
    A.d['yellow'].rectangle((540 - 300 * p, 860, 540 + 300 * p, 930), fill=255)
    zhang(A, 540, GROUND, 230, dir=1, arm=20)
    A.flush(cv)
    stamp(cv, seal('庶吉士', 48), 860, 1000, t, t - u + 1.5 * P, rot=6)

def art_j_memorial(A, cv, t, u):
    scroll(A, 540, 960, 600, 300, u / 0.6, layer='wash')
    ground(A, GROUND)
    zhang(A, 540, GROUND, 200, dir=1, kneel=True, bow=45, arm=80)
    A.flush(cv)
    for i, w in enumerate(['宗室骄恣', '庶官疾旷', '吏治因循', '边备未修', '财用大匮']):
        type_in(cv, text_img(w, SERIF, 30, INK, 'Black', bleed=False, vertical=True), 760 - i * 55, 960, t, t - u + 0.5 + i * 0.25, 0.3)
    if u > 2.5 * P:
        paste(cv, text_img('石沉大海', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 2.5 * P) / 0.3))

def art_j_home(A, cv, t, u):
    for k in range(8):
        x = 120 + k * 120
        A.d['grass'].polygon([(x - 50, GROUND), (x, GROUND - 120 - 30 * math.sin(k)), (x + 50, GROUND)], fill=180)
    ground(A, GROUND)
    for k in range(3):
        person(A, 240 + k * 140, GROUND, 140, dir=1, robe=False, hat='knot', bow=50, arm=150, ph=t * 2 + k, layer='ink')
    zhang(A, 820, GROUND, 200, dir=-1, arm=10)
    A.flush(cv)
    stamp(cv, seal('民间疾苦', 44), 860, 900, t, t - u + P, rot=6)

def art_j_back_capital(A, cv, t, u):
    city_wall(A, 120, 960, 1100, gate_x=540, label='京师', layer='mid', open_=ease_out(u / (2 * P)))
    ground(A, GROUND)
    zhang(A, walk_x(540, 540, u, 1), GROUND, 180, dir=1, arm=10)
    official(A, 700, GROUND, 230, dir=-1, layer='ink', arm=60)
    A.flush(cv)
    stamp(cv, seal('徐阶', 50, INK), 860, 960, t, t - u + P, rot=6)

# ================================================================ 第二回 隐忍入阁
def art_j_yansong(A, cv, t, u):
    palace(A, 540, GROUND, 560, layer='mid')
    ground(A, GROUND)
    official(A, 540, GROUND, 260, dir=1, layer='ink', fall=-80 * ease_out((u - 1.5 * P) / 0.5))
    A.flush(cv)
    stamp(cv, seal('严嵩', 54, INK), 300, 940, t, t - u + 0.4, rot=-5)
    if u > 1.5 * P:
        stamp(cv, seal('罢官', 54), 760, 940, t, t - u + 1.5 * P, rot=8)

def art_j_cabinet(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 180 + k * 180
        A.d['sandal'].rectangle((x - 70, GROUND - 100, x + 70, GROUND - 86), fill=255)
        if k == 2:
            zhang(A, x, GROUND, 240, dir=1, arm=40)
        else:
            official(A, x, GROUND, 210, dir=1 if k < 2 else -1, arm=30)
    A.flush(cv)
    stamp(cv, seal('内阁', 56), 540, 900, t, t - u + P)

def art_j_border(A, cv, t, u):
    pts = [(x, 1200 - 120 * math.sin(x / W * math.pi * 1.5) - 30 * math.sin(x * 0.03)) for x in range(60, W - 59, 20)]
    A.d['mid'].polygon(pts + [(W - 60, GROUND), (60, GROUND)], fill=180)
    A.d['ink'].line(pts, fill=255, width=12)
    for i in range(0, len(pts), 8):
        A.d['ink'].rectangle((pts[i][0] - 22, pts[i][1] - 80, pts[i][0] + 22, pts[i][1]), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    for i, (nm, x) in enumerate((('戚继光', 330), ('李成梁', 750))):
        if u > 0.6 + i * P:
            stamp(cv, seal(nm, 44, SANDAL if i else ZHU), x, 900, t, t - u + 0.6 + i * P, rot=-5 + 10 * i)

def art_j_horse_market(A, cv, t, u):
    ground(A, GROUND)
    A.d['sandal'].rectangle((520, 1060, 560, GROUND), fill=255)
    for k in range(3):
        horse(A, lerp(-100, 300, ease_out(u / (2 * P))) - k * 120, GROUND, 130, dir=1, ph=t * 6 + k, moving=u < 2 * P, layer='mid')
    for k in range(3):
        A.d['silver'].rectangle((640 + k * 90, GROUND - 60, 710 + k * 90, GROUND), fill=255)
        A.d['wash'].rectangle((640 + k * 90, GROUND - 120, 710 + k * 90, GROUND - 64), fill=255)
    A.flush(cv)
    stamp(cv, seal('互市', 56), 540, 920, t, t - u + P)

def art_j_longqing_dies(A, cv, t, u):
    A.d['mid'].rectangle((330, 1060, 750, GROUND - 60), fill=230)
    A.d['ink'].rectangle((300, GROUND - 60, 780, GROUND - 40), fill=255)
    for k in range(10):
        q = (t * 0.3 + k / 10) % 1
        x = 360 + (k * 41) % 360; y = lerp(1060, 700, q)
        A.d['wash'].ellipse((x - 10, y - 10, x + 10, y + 10), fill=int(150 * math.sin(math.pi * q)))
    ground(A, GROUND)
    person(A, 860, GROUND, 140, dir=-1, robe=True, hat='crown', arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('太子年幼', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), 860, 1100, 1, clamp((u - P) / 0.3))

def art_j_gaogong(A, cv, t, u):
    palace(A, 400, GROUND, 460, layer='mid')
    ground(A, GROUND)
    x = lerp(400, 1000, ease_out((u - P) / (2 * P)))
    carriage(A, x, GROUND, 120, dir=1, wheel=u * 5, ph=t * 8, moving=u > P, layer='mid')
    zhang(A, 260, GROUND, 230, dir=1, arm=20)
    person(A, 140, GROUND, 190, dir=1, robe=True, hat='none', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('高拱罢归', 44, INK), 760, 940, t, t - u + P, rot=6)
    stamp(cv, seal('冯保', 44), 160, 940, t, t - u + 2 * P, rot=-5)

def art_j_teacher(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((240, 820, 840, 1120), fill=255)
    A.d['sandal'].rectangle((240, 820, 840, 1120), outline=255, width=8)
    for k in range(4):
        x0 = 270 + k * 140
        A.d['mid'].rectangle((x0, 850, x0 + 120, 1000), fill=200)
        person(A, x0 + 60, 990, 100, dir=1, robe=True, hat='crown' if k % 2 else 'knot', arm=40 * (k % 2), layer='ink')
    person(A, 400, GROUND, 150, dir=1, robe=True, hat='crown', arm=10, layer='ink')
    zhang(A, 720, GROUND, 270, dir=-1, arm=lerp(40, 110, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('帝鉴图说', 44), 860, 1180, t, t - u + P, rot=6)

def art_j_power(A, cv, t, u):
    A.d['yellow'].rectangle((390, 860, 690, 1180), fill=200)
    A.d['red'].rectangle((470, 900, 610, 1040), fill=255)
    ground(A, GROUND)
    zhang(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    ink_in(cv, text_img('首辅', BRUSH, 80, (250, 245, 235)), 540, 970, t, t - u + 0.3, dur=0.3)

# ================================================================ 第三回 雷霆改革
def art_j_kaocheng(A, cv, t, u):
    """8-beat set piece: 考成法 — three ledgers open in turn (六部 · 六科 · 内阁), ticks run, laggards get red."""
    ph = u / P
    names = ['六部', '六科', '内阁']
    for i in range(3):
        op = clamp((ph - i * 1.4) / 0.6)
        if op <= 0: continue
        ticks = int(clamp((ph - i * 1.4 - 0.6) / 2.5) * 6)
        red = 2 if ph >= 6 and i == 0 else (1 if ph >= 6.6 and i == 1 else 0)
        ledger(A, 220 + i * 320, 1060, 260, 300, t, open_=op, ticks=ticks, red=red)
    if ph >= 1.4:
        A.d['sandal'].line((350, 1060, 410, 1060), fill=255, width=6)
    if ph >= 2.8:
        A.d['sandal'].line((670, 1060, 730, 1060), fill=255, width=6)
    ground(A, GROUND)
    if ph >= 6:
        for k in range(3):
            official(A, 300 + k * 90, GROUND, 140, dir=1, layer='ink', fall=-80 * ease_out((ph - 6 - k * 0.2) / 0.5))
    A.flush(cv)
    for i in range(3):
        if ph >= i * 1.4 + 0.3:
            stamp(cv, seal(names[i], 40, SANDAL if i < 2 else ZHU), 220 + i * 320, 870, t, t - u + (i * 1.4 + 0.3) * P)
    if ph >= 6.5:
        paste(cv, text_img('懒政者 罢黜', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 6.5) / 0.4))

def art_j_courier(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].rectangle((x - 50, 1260, x + 50, GROUND), fill=220)
        A.d['mid'].polygon([(x - 70, 1260), (x, 1210), (x + 70, 1260)], fill=220)
        if k < int(clamp(u / (2 * P)) * 4):
            A.d['red'].line((x - 60, 1220, x + 60, GROUND - 10), fill=255, width=10)
    ground(A, GROUND)
    rider(A, (t * 260) % (W + 300) - 150, GROUND, 130, 1, t * 12, layer='ink')
    A.flush(cv)
    stamp(cv, seal('驿递', 54), 540, 940, t, t - u + P)

def art_j_granary(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 160 + k * 190
        h = 220 * ease_out((u - k * 0.15) / (1.5 * P))
        A.d['sandal'].rectangle((x - 70, GROUND - h, x + 70, GROUND), fill=255)
        A.d['sandal'].polygon([(x - 90, GROUND - h), (x, GROUND - h - 70), (x + 90, GROUND - h)], fill=255)
        A.d['yellow'].rectangle((x - 50, GROUND - h + 30, x + 50, GROUND - 20), fill=200) if h > 60 else None
    A.flush(cv)
    paste(cv, text_img(f'可支{cn_num(max(1, int(clamp(u / (2.5 * P)) * 10)))}年', SERIF, 64, SANDAL, 'Black', bleed=False), W / 2, 960, 1, 1)

def art_j_duoqing(A, cv, t, u):
    palace(A, 540, 1150, 520, layer='mid')
    ground(A, GROUND)
    zhang(A, 540, GROUND, 230, dir=1, kneel=True, bow=30, arm=70)
    for k in range(4):
        official(A, 140 + k * 70, GROUND, 150, dir=1, layer='ink', bow=30, arm=100)
    A.d['wash'].rectangle((470, 1220, 610, GROUND - 40), fill=255)
    A.flush(cv)
    stamp(cv, seal('父丧', 52, INK), 860, 900, t, t - u + 0.4, rot=6)
    if u > 2 * P:
        stamp(cv, seal('夺情', 56), 540, 940, t, t - u + 2 * P)

def art_j_river(A, cv, t, u):
    A.d['yellow'].polygon([(60, 1240), (W - 60, 1180), (W - 60, 1320), (60, 1380)], fill=200)
    waves(A, 1250, t, rows=3, amp=6, speed=2.2)
    p = ease_out(u / (2.5 * P))
    for side in (0, 1):
        y0 = 1230 if side == 0 else 1370
        pts = [(x, y0 - (x - 60) * 0.06 + (side * 0)) for x in range(60, int(lerp(60, W - 60, p)), 20)]
        if len(pts) > 1: A.d['ink'].line(pts, fill=255, width=14)
    for k in range(int(p * 8)):
        person(A, 120 + k * 110, 1225 - k * 6, 90, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 6 + k, layer='mid')
    A.flush(cv)
    stamp(cv, seal('潘季驯', 46, INK), 860, 900, t, t - u + P, rot=6)
    type_in(cv, text_img('束水攻沙', SERIF, 50, SANDAL, 'Black', bleed=False, spacing=8), W / 2, 1448, t, t - u + 1.5 * P, 0.5)

def art_j_survey(A, cv, t, u):
    """6-beat set piece: 清丈田亩 — a field grid is paced out, hidden fields flip red, tally grows."""
    ph = u / P
    cols, rows = 7, 4
    x0, y0, cw, rh = 140, 960, 114, 90
    hidden = {(1, 2), (3, 1), (4, 3), (5, 0), (6, 2), (2, 3), (0, 1)}
    k = int(clamp(ph / 4.5) * cols * rows)
    for i in range(cols * rows):
        cx, cy = i % cols, i // cols
        x = x0 + cx * cw; y = y0 + cy * rh
        A.d['grass'].rectangle((x + 4, y + 4, x + cw - 4, y + rh - 4), fill=120)
        if i < k:
            A.d['ink'].rectangle((x + 4, y + 4, x + cw - 4, y + rh - 4), outline=220, width=3)
            if (cx, cy) in hidden:
                A.d['red'].rectangle((x + 10, y + 10, x + cw - 10, y + rh - 10), fill=200)
    j = min(k, cols * rows - 1)
    px = x0 + (j % cols) * cw + cw / 2; py = y0 + (j // cols) * rh + rh
    person(A, px, py, 110, dir=1, robe=False, hat='knot', ph=t * 6, arm=60, layer='ink')
    A.d['ink'].line((px + 20, py - 80, px + 60, py), fill=255, width=4)
    A.flush(cv)
    found = sum(1 for i in range(k) if (i % cols, i // cols) in hidden)
    paste(cv, text_img(f'清出隐田 {found * 40}万顷' if found < 7 else '清出隐田 二百八十余万顷', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4),
          W / 2, 1448, 1, clamp(ph / 0.5))

# ================================================================ 第四回 一条鞭法
LEVIES = ['田赋', '丁银', '力差', '银差', '均徭', '杂泛', '里甲', '贡纳', '物料', '马差', '漕粮', '盐钞']
def scene_whip(cv, t, c, k):
    """8-beat custom scene: 一条鞭法 — twelve levies drop in, a cord whips them together, they melt into one silver ingot."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    gather = ease_out((ph - 4) / 2)
    pos = []
    for i, nm in enumerate(LEVIES):
        a = i * 2 * math.pi / 12 - math.pi / 2
        r = lerp(330, 40, gather)
        pos.append((540 + r * math.cos(a), 1020 + r * 0.8 * math.sin(a)))
    if 3 <= ph < 6:
        q = clamp((ph - 3) / 1)
        loop = [(540 + lerp(380, 90, gather) * math.cos(a), 1020 + lerp(380, 90, gather) * 0.8 * math.sin(a))
                for a in np.linspace(-math.pi / 2, -math.pi / 2 + 2 * math.pi * q, 50)]
        A.d['sandal'].line(loop, fill=255, width=12)
    if ph >= 5.5:
        ingot(A, 540, 1120, lerp(20, 230, ease_out((ph - 5.5) / 0.8)))
        if ph >= 6.2:
            for i in range(12):
                a = i * math.pi / 6 + t
                r1, r2 = 260, 260 + 50 * (0.5 + 0.5 * math.sin(t * 6 + i))
                A.d['silver'].line((540 + r1 * math.cos(a), 1040 + r1 * 0.8 * math.sin(a), 540 + r2 * math.cos(a), 1040 + r2 * 0.8 * math.sin(a)), fill=200, width=6)
    A.flush(cv)
    if ph < 6:
        for i, nm in enumerate(LEVIES):
            st = s0 + i * 0.22 * P
            if t >= st:
                fade = 1 - clamp((ph - 5.5) / 0.5)
                paste(cv, seal(nm, 38, SANDAL if i % 2 else INK), pos[i][0], pos[i][1], lerp(1.0, 0.6, gather), fade)
    fx = Art()
    if ph < 6:
        chars_in(cv, fx, '一条鞭法', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=114)
    else:
        chars_in(cv, fx, '计亩征银', BRUSH, 150, SANDAL, W / 2, 440, t, s0 + 6 * P, stagger=0.08, seed=115)
    fx.flush(cv)
    sub = '赋役杂税 名目繁多' if ph < 3 else ('总为一条 合并征收' if ph < 6 else '一律折银 按田亩计')
    paste(cv, text_img(sub, SERIF, 46, DIM, 'Black', bleed=False, spacing=4), W / 2, 570, 1, 1)
    paste(cv, text_img('公元一五八一年 · 推行全国', SERIF, 42, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 0.5) / 0.4))

def art_j_zuiji(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 400, GROUND, 170, dir=1, robe=True, hat='crown', kneel=True, bow=45, arm=80, layer='ink')
    zhang(A, 720, GROUND, 250, dir=-1, arm=lerp(20, 70, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('罪己诏', 50), 540, 900, t, t - u + 1.5 * P, rot=4)
    type_in(cv, text_img('年少醉酒 太后震怒', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + P, 0.4)

def art_j_silver_age(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, 1420), fill=120)
    waves(A, 1250, t, rows=3, amp=6, speed=1.6)
    boat(A, lerp(-100, 300, ease_out(u / (2 * P))), 1270, 110, t, sail=True)
    ground(A, 1240, x0=540, x1=W - 60)
    for k in range(int(clamp(u / (2.5 * P)) * 6)):
        ingot(A, 640 + (k % 3) * 110, 1236 - (k // 3) * 60, 52)
    A.flush(cv)
    stamp(cv, seal('白银', 54), 300, 900, t, t - u + P, rot=-5)

def art_j_sedan(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(-300, 560, ease_out(u / (3 * P)))
    sedan(A, x, GROUND, 200, t, bearers=5)
    A.flush(cv)
    stamp(cv, seal('传说', 44, INK), 860, 900, t, t - u + P, rot=6)
    paste(cv, text_img('三十二人抬', SERIF, 50, SANDAL, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((u - 1.5 * P) / 0.3))

def art_j_overwork(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 400, layer='sandal')
    for k in range(int(clamp(u / (2.5 * P)) * 9)):
        A.d['wash'].rectangle((420 + (k % 3) * 100, GROUND - 90 - (k // 3) * 26, 500 + (k % 3) * 100, GROUND - 66 - (k // 3) * 26), fill=255)
        A.d['ink'].rectangle((420 + (k % 3) * 100, GROUND - 90 - (k // 3) * 26, 500 + (k % 3) * 100, GROUND - 66 - (k // 3) * 26), outline=180, width=2)
    sitter(A, 300, GROUND, 230, dir=1, bow=lerp(5, 30, 0.5 + 0.5 * math.sin(t * 0.8)))
    lamp(A, 780, GROUND - 70, 50, t, glow=0.6)
    A.flush(cv)
    stamp(cv, seal('病中批阅', 44, INK), 860, 900, t, t - u + P, rot=6)

def art_j_death(A, cv, t, u):
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        x = 80 + (k * 29) % 920; y = lerp(620, 1420, q)
        A.d['wash'].ellipse((x - 4, y - 4, x + 4, y + 4), fill=200)
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    for sx in (300, 760):
        A.d['ink'].rectangle((sx, 1290, sx + 20, GROUND), fill=255)
    ground(A, GROUND)
    lt = clamp(1 - (u - P) / 0.8)
    lamp(A, 860, GROUND, 60, t, glow=lt)
    A.flush(cv)
    stamp(cv, seal('文忠', 56), 540, 920, t, t - u + 1.5 * P)

def art_j_honors(A, cv, t, u):
    ground(A, GROUND)
    for k in range(int(clamp(u / P) * 12)):
        x = 120 + k * 75
        person(A, x, GROUND, 120, dir=1, robe=True, hat='none', ph=t * 4 + k, arm=20, layer='mid')
        A.d['wash'].rectangle((x - 12, GROUND - 200, x + 12, GROUND - 130), fill=255)
    A.flush(cv)
    stamp(cv, seal('上柱国', 50), 540, 940, t, t - u + 0.5)

# ================================================================ 第五回 身后清算
def art_j_undo(A, cv, t, u):
    abacus(A, 540, 1060, 560, 320, [int(lerp(9, 0, ease_out(u / (2.5 * P))))] * 5, t)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('新政尽废', 46, INK), 860, 860, t, t - u + 1.5 * P, rot=6)

def art_j_reckoning(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 130, ease_out(u / 0.5)), layer='ink')
    for k in range(5):
        official(A, 160 + k * 60, GROUND, 140, dir=1, layer='ink', bow=30, arm=100)
        official(A, 920 - k * 60, GROUND, 140, dir=-1, layer='ink', bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('削尽官秩', 46), 540, 880, t, t - u + P, rot=-4)

def art_j_raid(A, cv, t, u):
    A.d['sandal'].rectangle((280, 900, 800, GROUND), fill=255)
    A.d['ink'].rectangle((400, 1080, 680, GROUND), fill=255)
    p = ease_out((u - P) / 0.4)
    for sx in (-1, 1):
        A.d['wash'].rectangle((540 + sx * 40 - 30, 1100 - 40 * (1 - p), 540 + sx * 40 + 30, 1400), fill=int(255 * p))
    A.d['wash'].polygon([(470, 1180), (610, 1180), (600, 1220), (480, 1220)], fill=int(255 * p))
    ground(A, GROUND)
    for k in range(3):
        person(A, 160 + k * 60, GROUND, 160, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    if p > 0.5:
        ink_in(cv, text_img('封', BRUSH, 90, ZHU), 540, 1260, t, t - u + P + 0.2, dur=0.2, settle=1.3)
    paste(cv, text_img('饿死十余口', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 820, 1, clamp((u - 2 * P) / 0.3))

def art_j_son(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 41) % 920; y = 640 + (k * 47) % 360
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    A.d['ink'].line((200, 820, 880, 820), fill=255, width=16)
    A.d['ink'].line((540, 820, 540, 960), fill=200, width=4)
    A.d['mid'].rectangle((300, 1040, 780, GROUND), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('血书 · 绝命', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + P, 0.5)
    stamp(cv, seal('张敬修', 46, INK), 860, 1000, t, t - u + 0.4, rot=6)

def art_j_rehab(A, cv, t, u):
    scroll(A, 540, 980, 560, 280, u / 0.6, layer='yellow')
    ground(A, GROUND)
    A.flush(cv)
    if u > 0.5:
        ink_in(cv, text_img('复其官', BRUSH, 120, ZHU), W / 2, 980, t, t - u + 0.5, dur=0.3, settle=1.2)
    type_in(cv, text_img('死后四十年', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, t, t - u + 1.5 * P, 0.4)

def art_j_missing(A, cv, t, u):
    palace(A, 540, GROUND, 640, collapse=ease_out((u - P) / (2.5 * P)), layer='mid')
    flames(A, 540, GROUND, 600, 260 * ease_out((u - 1.5 * P) / 0.8), t, n=7, seed=81, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('甲申', 54, INK), 860, 880, t, t - u + P, rot=6)

def art_j_legacy(A, cv, t, u):
    abacus(A, 540, 1080, 640, 360, [9, 9, 9, 9, 9], t)
    ground(A, GROUND)

def art_j_title(A, cv, t, u):
    palace(A, 820, 1460, 520, layer='mid')
    zhang(A, 430, 1460, 720, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '江陵神童'), 48: ('第二回', '隐忍入阁'), 80: ('第三回', '雷霆改革'),
            112: ('第四回', '一条鞭法'), 144: ('第五回', '身后清算')}

CARDS = [
    C(0, 2, 'empire', 'num', num='十年', line='把大明从破产边缘拉回', art=art_j_hook_treasury),
    C(2, 4, 'court', 'num', num='少年天子', line='由他一手教大', art=art_j_hook_boy),
    C(4, 6, 'death', 'num', num='死后抄家', line='长子自尽', art=art_j_hook_seal),
    C(6, 8, 'fate', 'num', num='一条鞭法', line='影响明清两朝', art=art_j_hook_whip),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 江陵神童
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1525, main='白圭', sub='生于湖广江陵 · 初名张白圭', note='传说 曾祖梦白龟浮水', art=art_j_turtle),
    C(22, 26, 'life', 'card', year=1536, main='改名居正', sub='少年考中秀才 · 知府为他改名', note='荆州知府李士翱', art=art_j_rename),
    C(26, 30, 'night', 'card', year=1537, main='故意落榜', sub='巡抚顾璘 · 有意磨其心志', note='一说 恐其少年得志', art=art_j_failed_on_purpose),
    C(30, 34, 'court', 'card', year=1540, main='犀带相赠', sub='再考中举 · 顾璘解带相赠', note='他日当为帝王师', art=art_j_belt),
    C(34, 38, 'empire', 'card', year=1547, main='进士及第', sub='二十二岁 · 选为庶吉士', art=art_j_jinshi),
    C(38, 42, 'court', 'card', year=1549, main='论时政疏', sub='直陈五大积弊', note='朝廷不纳', art=art_j_memorial),
    C(42, 46, 'life', 'card', year=1554, main='告病归乡', sub='乡居三年 · 看清民间疾苦', art=art_j_home),
    C(46, 48, 'court', 'card', year=1557, main='重返京师', sub='依附恩师徐阶', art=art_j_back_capital),
    # ---- 第二回 隐忍入阁
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'night', 'card', year=1562, main='严嵩倒台', sub='徐阶扳倒二十年权相', note='隐忍多年 静待时机', art=art_j_yansong),
    C(54, 58, 'court', 'card', year=1567, main='入阁', sub='四十二岁 · 进入内阁', art=art_j_cabinet),
    C(58, 62, 'war', 'card', year=1568, main='整饬边防', sub='戚继光镇蓟州 · 李成梁守辽东', note='用人不疑', art=art_j_border),
    C(62, 66, 'works', 'card', year=1571, main='俺答封贡', sub='隆庆和议 · 开放互市', note='北边数十年少有大战', art=art_j_horse_market),
    C(66, 70, 'death', 'card', year=1572, main='隆庆驾崩', sub='托孤三位大臣', art=art_j_longqing_dies),
    C(70, 74, 'night', 'card', year=1572, main='驱逐高拱', sub='联手宦官冯保 · 出任首辅', note='权斗无情', art=art_j_gaogong),
    C(74, 78, 'court', 'card', year=1572, main='帝王之师', sub='亲编帝鉴图说 · 教小皇帝读史', art=art_j_teacher),
    C(78, 80, 'empire', 'card', year=1572, main='内阁首辅', sub='自此十年当国', art=art_j_power),
    # ---- 第三回 雷霆改革
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'works', 'card', year=1573, main='考成法', sub='立限考事 · 以实绩问责', note='以六科稽六部 以内阁稽六科', art=art_j_kaocheng),
    C(90, 94, 'court', 'card', year=1575, main='整顿驿递', sub='严禁滥用驿站 · 节省开支', art=art_j_courier),
    C(94, 98, 'empire', 'card', year=1577, main='太仓充盈', sub='国库存粮 · 足支十年', note='太仓之粟 可支十年', art=art_j_granary),
    C(98, 102, 'night', 'card', year=1577, main='夺情', sub='父丧不归 · 留任理政', note='言官上疏反对 遭廷杖', art=art_j_duoqing),
    C(102, 106, 'works', 'card', year=1578, main='治理黄河', sub='起用潘季驯', note='筑堤束水 以水攻沙', art=art_j_river),
    C(106, 112, 'works', 'card', year=1578, main='清丈田亩', sub='全国重新丈量土地', note='豪强隐田 无所遁形', art=art_j_survey),
    # ---- 第四回 一条鞭法
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'night', 'card', year=1580, main='皇帝罪己', sub='万历醉酒失仪 · 他代拟罪己诏', note='严师亦成心结', art=art_j_zuiji),
    C(118, 126, 'fate', 'whip', year=1581),
    C(126, 130, 'empire', 'card', year=1581, main='白银时代', sub='以银纳税 · 商品经济繁荣', note='海外白银源源流入', art=art_j_silver_age),
    C(130, 134, 'court', 'card', year=1581, main='权倾朝野', sub='排场之大 · 遭人非议', art=art_j_sedan),
    C(134, 138, 'fate', 'card', year=1582, main='积劳成疾', sub='病中仍批阅奏章', note='鞠躬尽瘁', art=art_j_overwork),
    C(138, 142, 'death', 'card', year=1582, main='病逝', sub='卒于任上 · 年五十七', note='赠上柱国 谥文忠', art=art_j_death),
    C(142, 144, 'empire', 'card', year=1582, main='哀荣极盛', sub='朝野送葬', art=art_j_honors),
    # ---- 第五回 身后清算
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=1583, main='人亡政息', sub='冯保被逐 · 新政渐废', art=art_j_undo),
    C(150, 154, 'court', 'card', year=1583, main='清算', sub='万历亲政 · 追夺官爵', note='昔日恩师 转眼成仇', art=art_j_reckoning),
    C(154, 158, 'night', 'card', year=1584, main='抄家', sub='家门被封 · 家人困死宅中', art=art_j_raid),
    C(158, 162, 'death', 'card', year=1584, main='长子自缢', sub='张敬修不堪拷问', note='留绝命书', art=art_j_son),
    C(162, 166, 'end', 'card', year=1622, main='平反', sub='天启年间 · 恢复名誉', art=art_j_rehab),
    C(166, 170, 'war', 'card', year=1644, main='大明落幕', sub='国势危亡 · 人们又想起了他', art=art_j_missing),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='拾玖', col=SANDAL, acc=SILVER, born=1525, died=1582,
    hook_q='他救了大明 · 死后却被抄家？',
    name_line='张居正 · 字叔大', name='张居正', seal='太岳', title_art=art_j_title,
    q1='救时宰相？', q2='专权之臣？',
    end_art=art_j_legacy, end_big='工于谋国', end_seal='太岳',
    end_l1='他替大明续了一口气', end_l2='却没能保住自己和家人',
    end_brush='拙于谋身', end_ask='改革者该不该如此强硬？评论区聊聊', next='于谦'),
    scenes=dict(chapter=scene_chapter, whip=scene_whip))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
