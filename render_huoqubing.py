"""千古人物志 · 第贰拾柒集 · 霍去病 (前140–前117)
Look: 焉支胭脂 + 祁连雪蓝, 箭簇 corner borders, a galloping-horse chapter card that runs further each chapter (百里 → 两千里).
Set pieces: 8-beat 八百骑, custom 8-beat scene 'hexi' (河西两战 + 受降 map), 6-beat 驰入敌营, 6-beat 酒泉,
8-beat 封狼居胥, 6-beat 玄甲列阵.
Years are stored negative (BC); epkit prints 公元前.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_simaqian as Sm        # engine + helpers (previous episode)
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
from render_zhangqian import yurt

F.RIPPLE = False
ROUGE = (176, 46, 78)               # 焉支胭脂
QILIAN = (110, 160, 196)            # 祁连雪蓝
S.LAYERS.append(('rouge', ROUGE, 0.88, 1.0))
S.LAYERS.append(('qilian', QILIAN, 0.85, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='骠', life='霍', court='侯', night='夜', war='戰', empire='汉', works='骑', fate='狼', death='冢', end='骠')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['war']['sun'] = (ROUGE, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (QILIAN, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (ROUGE, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

PEAKS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PEAKS)
for _x, _h in ((140, 260), (330, 340), (560, 300), (780, 380), (960, 280)):
    _d.polygon([(_x - 170, 1330), (_x, 1330 - _h), (_x + 170, 1330)], fill=QILIAN + (34,))
    _d.polygon([(_x - 50, 1330 - _h + 70), (_x, 1330 - _h), (_x + 50, 1330 - _h + 70)], fill=(250, 250, 250, 70))
MTN_COL = {'night': (34, 36, 46), 'death': (60, 60, 66), 'war': (110, 54, 56), 'fate': (70, 86, 104)}
def draw_background(t, theme):
    """祁连: snow-capped peaks on the horizon above dry steppe ridges."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    canvas.alpha_composite(PEAKS)
    cols = [(196, 186, 176), (160, 140, 126), MTN_COL.get(theme, (116, 96, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 9 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """箭簇: three arrowheads fanning out of each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = ROUGE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        for k, a in enumerate((0.25, 0.78, 1.3)):
            ax, ay = x + sx * 70 * math.cos(a), y + sy * 70 * math.sin(a)
            d.line((x + sx * 10 * math.cos(a), y + sy * 10 * math.sin(a), ax, ay), fill=col, width=3)
            nx, ny = sx * math.cos(a), sy * math.sin(a)
            d.polygon([(ax + 18 * nx, ay + 18 * ny), (ax - 7 * ny, ay + 7 * nx), (ax + 7 * ny, ay - 7 * nx)], fill=QILIAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def huo(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, **kw):
    """霍去病: young general, light armour, a tall single red feather on the helmet, short cape."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        A.d['rouge'].line((x - dir * 0.02 * h, y - 1.05 * h, x - dir * 0.1 * h, y - 1.28 * h), fill=255, width=max(3, int(0.025 * h)))
        A.d['rouge'].polygon([(x - dir * 0.05 * h, y - 0.82 * h), (x - dir * 0.24 * h, y - 0.36 * h), (x - dir * 0.08 * h, y - 0.4 * h)], fill=255)
    return hand

def huo_rider(A, x, y, s, dir=1, ph=0.0, moving=True, layer='ink'):
    horse(A, x, y, s, dir=dir, ph=ph, moving=moving, layer=layer)
    huo(A, x - dir * 0.05 * s, y - 0.78 * s, 0.95 * s, dir=dir, arm=60, spear=True, layer=layer)

def golden_man(A, x, base, s, layer='gold'):
    d = A.d[layer]
    d.ellipse((x - 0.12 * s, base - 1.0 * s, x + 0.12 * s, base - 0.76 * s), fill=255)
    d.polygon([(x - 0.18 * s, base - 0.76 * s), (x + 0.18 * s, base - 0.76 * s), (x + 0.26 * s, base - 0.1 * s), (x - 0.26 * s, base - 0.1 * s)], fill=255)
    d.rectangle((x - 0.32 * s, base - 0.1 * s, x + 0.32 * s, base), fill=255)
    for sx in (-1, 1):
        d.line((x + sx * 0.16 * s, base - 0.7 * s, x + sx * 0.06 * s, base - 0.45 * s), fill=255, width=max(3, int(0.06 * s)))

# ================================================================ chapter card
CH = {16: (0.25, '百里'), 48: (0.45, '千里'), 80: (0.65, '一千五百里'), 112: (0.92, '两千余里'), 144: (0.0, '')}
def art_ride_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    reach, lab = CH.get(kb, (0.45, '千里'))
    ground(A, 1180)
    A.d['qilian'].line((120, 1190, 960, 1190), fill=160, width=4)
    for k in range(9):
        x = 120 + k * 105
        A.d['ink'].line((x, 1182, x, 1198), fill=200, width=3)
    if kb == 144:
        A.d['mid'].polygon([(380, 1180), (540, 960), (700, 1180)], fill=220)
        flag(A, 540, 960, 120, t, w=50, layer='rouge')
    else:
        x = lerp(120, 120 + 840 * reach, ease_out(u / (1.4 * P)))
        huo_rider(A, x, 1180, 150, dir=1, ph=t * 12)
        A.flush(cv)
        paste(cv, text_img(lab, SERIF, 46, ROUGE, 'Black', bleed=False, spacing=6), min(max(x, 200), 880), 900, 1, clamp(u / 0.4))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_ride_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ROUGE, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_g_hook_17(A, cv, t, u):
    ground(A, GROUND)
    huo(A, 540, GROUND, 300, dir=1, arm=lerp(20, 150, ease_out(u / (1.2 * P))), spear=True)
    A.d['gold'].rectangle((360, GROUND - 40, 720, GROUND), fill=200)

def art_g_hook_altar(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (540, 880), (880, GROUND)], fill=210)
    A.d['ink'].rectangle((500, 860, 580, 890), fill=255)
    p = ease_out(u / (1.4 * P))
    for k in range(5):
        q = (t * 0.5 + k / 5) % 1
        A.d['wash'].ellipse((540 + 30 * math.sin(k + t) - 12, lerp(860, 700, q) - 12, 540 + 30 * math.sin(k + t) + 12, lerp(860, 700, q) + 12), fill=int(200 * (1 - q) * p))
    flag(A, 540, 880, 160, t, w=60, layer='rouge')
    ground(A, GROUND)

def art_g_hook_house(A, cv, t, u):
    palace(A, 760, GROUND, 360, layer='mid')
    ground(A, GROUND)
    huo(A, lerp(560, 260, ease_out(u / (1.4 * P))), GROUND, 260, dir=-1, ph=t * 5, arm=40)

def art_g_hook_23(A, cv, t, u):
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    A.d['mid'].polygon([(300, GROUND), (540, 1080), (780, GROUND)], fill=220)
    ground(A, GROUND)

# ================================================================ 第一回 私生之子
def art_g_birth(A, cv, t, u):
    palace(A, 720, GROUND, 380, layer='mid')
    ground(A, GROUND)
    person(A, 380, GROUND, 230, dir=1, robe=True, hat='knot', female=True, baby=True, layer='ink')
    x = lerp(500, 1100, ease_out((u - P) / (2 * P)))
    person(A, x, GROUND, 220, dir=1, robe=True, hat='none', ph=t * 4, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('平阳', 56), 300, 880, t, t - u + 0.4, rot=-5)

def art_g_aunt(A, cv, t, u):
    palace(A, 540, 1140, 520, layer='rouge')
    ground(A, GROUND)
    person(A, 460, GROUND - 30, 230, dir=1, robe=True, hat='crown', arm=60, layer='ink')
    person(A, 640, GROUND - 30, 220, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('卫子夫', 50), 860, 880, t, t - u + P, rot=6)

def art_g_uncle(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        rider(A, lerp(-150, 640, ease_out(u / (2.5 * P))) - k * 110, GROUND - (k % 2) * 20, 130, 1, t * 12 + k, layer='ink' if k == 0 else 'mid', spear=True)
    flames(A, 900, GROUND, 160, 160 * ease_out((u - 2 * P) / 0.6), t, n=4, seed=3, smoke=True)
    A.flush(cv)
    stamp(cv, seal('卫青', 54), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('龙城', 50, INK), 860, 960, t, t - u + 2 * P, rot=6)

def art_g_archer(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(200, 700, 0.5 + 0.5 * math.sin(t * 0.8))
    horse(A, x, GROUND, 170, dir=1 if math.cos(t * 0.8) > 0 else -1, ph=t * 10, layer='ink')
    person(A, x, GROUND - 130, 150, dir=1, robe=False, hat='knot', arm=150, arm2=-120, layer='ink')
    for k in range(3):
        A.d['qilian'].ellipse((880 - 30 * k, 980 + 60 * k - 30, 940 - 30 * k + 30, 980 + 60 * k + 30), outline=255, width=5)
    arrow(A, lerp(x + 80, 900, (t * 2) % 1), 1000, 0.05, 70)
    A.flush(cv)
    paste(cv, text_img('善骑射', SERIF, 52, ROUGE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_g_shizhong(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    huo(A, 760, GROUND, 190, dir=-1, arm=40)
    A.flush(cv)
    stamp(cv, seal('侍中', 54), 280, 880, t, t - u + P, rot=-5)

def art_g_800(A, cv, t, u):
    """8-beat set piece: 八百骑 — the main army halts; 800 riders peel away, cross hundreds of li, fall on the camp at night."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        for k in range(10):
            person(A, 80 + k * 40, GROUND, 80, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
        n = int(clamp(ph / 1.2) * 8)
        for k in range(n):
            x = lerp(500, 1200, clamp((ph - k * 0.12) / 2.5)) - (k % 4) * 60
            huo_rider(A, x, GROUND - (k // 4) * 50, 110, dir=1, ph=t * 12 + k) if k == 0 else rider(A, x, GROUND - (k // 4) * 50, 110, 1, t * 12 + k, layer='ink', spear=True)
    else:
        for k2 in range(30):
            x2 = 80 + (k2 * 37) % 920; y2 = 640 + (k2 * 53) % 300
            A.d['wash'].ellipse((x2 - 2, y2 - 2, x2 + 2, y2 + 2), fill=255)
        for k in range(4):
            yurt(A, 600 + k * 110, GROUND, 100, 90)
        burn = ease_out((ph - 4.5) / 1)
        if burn > 0:
            flames(A, 760, GROUND, 460, 220 * burn, t, n=6, seed=7, smoke=True)
        for k in range(8):
            x = lerp(-200, 520, ease_out((ph - 3) / 1.5)) - (k % 4) * 90
            if k == 0:
                huo_rider(A, x, GROUND - (k // 4) * 40, 120, dir=1, ph=t * 12 + k)
            else:
                rider(A, x, GROUND - (k // 4) * 40, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    lab = '轻骑八百 · 弃大军而去' if ph < 3 else ('夜袭敌营' if ph < 6 else '斩捕二千余人')
    paste(cv, text_img(lab, SERIF, 48, ROUGE if ph >= 6 else INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_g_marquis(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='rouge')
    ground(A, GROUND)
    person(A, 700, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.5)), layer='ink')
    huo(A, 360, GROUND, 220, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    stamp(cv, seal('冠军侯', 56), 540, 880, t, t - u + P)

# ================================================================ 第二回 河西之战
def art_g_general(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        flag(A, 680 + k * 110, GROUND, 360, t, w=80, layer='rouge' if k == 1 else 'red')
    huo(A, 360, GROUND, 300, dir=1, arm=lerp(40, 160, ease_out(u / (1.2 * P))), spear=True)
    A.flush(cv)
    stamp(cv, seal('骠骑', 60), 790, 860, t, t - u + P, rot=6)

HEXI = [('陇西', 900, 1240), ('焉支山', 640, 1120), ('皋兰', 520, 1180), ('北地', 960, 1000), ('居延', 520, 860), ('祁连山', 300, 1120)]
def scene_hexi(cv, t, c, k):
    """8-beat custom scene: 河西 — the corridor between 祁连 and the desert; spring campaign through 焉支 (beats 0–3),
    summer campaign via 居延 to 祁连 (beats 3–6), then the 浑邪王 surrenders (6–8). Head count climbs."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=200)
    for kx in range(6):
        x = 200 + kx * 130
        A.d['qilian'].polygon([(x - 80, 1320), (x, 1220), (x + 80, 1320)], fill=200)
    A.d['dune'].polygon([(130, 780), (950, 780), (950, 900), (130, 960)], fill=110)
    p1 = clamp(ph / 3)
    seg1 = [HEXI[0][1:], HEXI[1][1:], HEXI[2][1:]]
    def draw_path(pts, q, layer):
        n = len(pts) - 1
        m = q * n
        for i in range(n):
            f = clamp(m - i)
            if f <= 0: break
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            A.d[layer].line((x0, y0, lerp(x0, x1, f), lerp(y0, y1, f)), fill=255, width=8)
        i = min(n - 1, int(m)); f = clamp(m - i)
        return (lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f))
    tip = draw_path(seg1, p1, 'rouge')
    if ph >= 3:
        seg2 = [HEXI[3][1:], HEXI[4][1:], HEXI[5][1:]]
        tip = draw_path(seg2, clamp((ph - 3) / 3), 'red')
    huo_rider(A, tip[0], tip[1] + 16, 70, dir=-1, ph=t * 12)
    A.flush(cv)
    for i, (nm, x, y) in enumerate(HEXI):
        st = [0, 1, 2, 3, 4.5, 5.6][i]
        if ph >= st:
            stamp(cv, seal(nm, 30, ROUGE if nm in ('焉支山', '祁连山') else INK), x, y - 44, t, s0 + st * P)
    heads = int(lerp(0, 8960, clamp(ph / 3))) + int(lerp(0, 30200, clamp((ph - 3) / 3)))
    fx = Art()
    chars_in(cv, fx, '河西之战', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=54)
    fx.flush(cv)
    lab = '春 · 出陇西 过焉支山千余里' if ph < 3 else ('夏 · 逾居延 至祁连山' if ph < 6 else '秋 · 浑邪王请降')
    paste(cv, text_img(lab, SERIF, 44, ROUGE, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img(f'斩首捕虏 {heads} 人' if ph < 6 else '河西尽归汉', SERIF, 44, QILIAN if ph < 6 else ROUGE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_g_golden(A, cv, t, u):
    ground(A, GROUND)
    golden_man(A, 540, GROUND - 20, 360)
    A.d['ink'].rectangle((380, GROUND - 20, 700, GROUND), fill=255)
    for k in range(2):
        person(A, 240 + k * 600, GROUND, 190, dir=1 if k == 0 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('休屠', 54, INK), 860, 880, t, t - u + P, rot=6)

def art_g_lament(A, cv, t, u):
    A.d['qilian'].polygon([(120, GROUND), (330, 960), (540, GROUND)], fill=220)
    A.d['rouge'].polygon([(540, GROUND), (760, 1000), (980, GROUND)], fill=180)
    ground(A, GROUND)
    for k in range(3):
        person(A, lerp(500, 1100, ease_out(u / (3 * P))) + k * 70, GROUND, 140, dir=1, robe=True, hat='knot', female=k == 1, ph=t * 3 + k, arm=-8, layer='mid')
    A.flush(cv)
    for i, ln in enumerate(('亡我祁连山 使我六畜不蕃息', '失我焉支山 使我妇女无颜色')):
        type_in(cv, text_img(ln, SERIF, 40, ROUGE if i else INK, 'Black', bleed=False, spacing=2), W / 2, 830 + i * 64, t, t - u + 0.4 + i * 1.2 * P, 0.5)

def art_g_hunye(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 24) + 1
    for i in range(n):
        x = 980 - (i % 12) * 60 - 40 * ease_out(u / (3 * P)); y = GROUND - (i // 12) * 40
        person(A, x, y, 90, dir=-1, robe=True, hat='knot', ph=t * 4 + i, arm=-8, layer='mid' if i // 12 else 'ink')
    huo(A, 180, GROUND, 230, dir=1, arm=60, spear=True)
    A.flush(cv)
    stamp(cv, seal('浑邪王', 50), 760, 880, t, t - u + 0.4, rot=6)

def art_g_mutiny(A, cv, t, u):
    """6-beat: 驰入敌营 — the surrendering camp boils over; he rides straight in, cuts down the mutineers, the rest kneel."""
    ph = u / P
    ground(A, GROUND)
    for k in range(5):
        yurt(A, 540 + (k - 2) * 170, GROUND - 120, 120, 100, layer='mid')
    for k in range(14):
        x = 200 + (k % 7) * 110 + 10 * math.sin(t * 6 + k)
        y = GROUND - (k // 7) * 50
        if ph < 3.5:
            person(A, x, y, 100, dir=1 if k % 2 else -1, robe=False, hat='knot', arm=lerp(40, 170, 0.5 + 0.5 * math.sin(t * 8 + k)), layer='ink')
        else:
            fallen = k % 3 == 0
            person(A, x, y, 100, dir=-1, robe=False, hat='knot', kneel=not fallen, fall=-80 if fallen else 0, bow=50, arm=100, layer='mid' if fallen else 'ink')
    x = lerp(-200, 540, ease_out((ph - 1.5) / 1.5))
    huo_rider(A, x, GROUND, 170, dir=1, ph=t * 12, moving=ph < 3.5)
    A.flush(cv)
    lab = '降众哗变' if ph < 1.5 else ('驰入其营' if ph < 3.5 else '斩八千人 · 四万归降')
    paste(cv, text_img(lab, SERIF, 50, ROUGE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

# ================================================================ 第三回 酒泉无家
def art_g_jiuquan(A, cv, t, u):
    """6-beat: 酒泉 — a single jar of the emperor's wine poured into the spring; the whole army drinks."""
    ph = u / P
    A.d['qilian'].ellipse((340, 1260, 740, 1360), fill=200)
    ground(A, GROUND, x0=60, x1=340)
    ground(A, GROUND, x0=740, x1=W - 60)
    huo(A, 380, 1260, 230, dir=1, arm=lerp(40, 120, ease_out(ph / 1.5)))
    jx, jy = 480, 1260 - 230 * 0.7
    A.d['rouge'].ellipse((jx - 40, jy - 50, jx + 40, jy + 30), fill=255)
    if 1.5 <= ph < 4:
        for k in range(8):
            q = (t * 2 + k / 8) % 1
            A.d['gold'].ellipse((jx + 30 + 40 * q - 5, jy + 160 * q - 5, jx + 30 + 40 * q + 5, jy + 160 * q + 5), fill=230)
    n = int(clamp((ph - 3) / 2.5) * 10)
    for k in range(n):
        x = 640 + (k % 5) * 70; y = GROUND - (k // 5) * 40
        person(A, x, y, 100, dir=-1, robe=False, hat='helmet', kneel=True, bow=40, arm=120, layer='ink' if k // 5 == 0 else 'mid')
    A.flush(cv)
    stamp(cv, seal('相传', 46, INK), 860, 860, t, t - u + 0.4, rot=6)
    if ph >= 3:
        paste(cv, text_img('酒泉', BRUSH, 110, ROUGE), 540, 1080, 1, clamp((ph - 3) / 0.4))

def art_g_corridor(A, cv, t, u):
    p = ease_out(u / (2.5 * P))
    A.d['qilian'].polygon([(60, 1300), (W - 60, 1180), (W - 60, 1260), (60, 1380)], fill=150)
    A.d['dune'].polygon([(60, 900), (W - 60, 860), (W - 60, 980), (60, 1040)], fill=110)
    for i, nm in enumerate(('武威', '张掖', '酒泉', '敦煌')):
        x = lerp(880, 200, i / 3); y = lerp(1100, 1180, i / 3)
        if p > i / 4:
            A.d['ink'].rectangle((x - 30, y - 30, x + 30, y + 10), fill=255)
    A.d['red'].line((960, 1080, lerp(960, 160, p), lerp(1080, 1180, p)), fill=220, width=6)
    A.flush(cv)
    for i, nm in enumerate(('武威', '张掖', '酒泉', '敦煌')):
        x = lerp(880, 200, i / 3); y = lerp(1100, 1180, i / 3)
        if p > i / 4 + 0.05:
            stamp(cv, seal(nm, 30, ROUGE), x, y - 70, t, t - u + (i / 4 + 0.05) * 2.5 * P)

def art_g_no_home(A, cv, t, u):
    palace(A, 720, GROUND, 420, layer='rouge')
    ground(A, GROUND)
    person(A, 520, GROUND, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 110, ease_out(u / 0.5)), layer='ink')
    huo(A, 260, GROUND, 230, dir=1, arm=lerp(20, -10, ease_out((u - P) / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('匈奴未灭 无以家为也', SERIF, 48, ROUGE, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)

def art_g_flaw(A, cv, t, u):
    tent(A, 740, GROUND, 420, 300, layer='mid')
    for k in range(6):
        A.d['gold'].ellipse((600 + k * 40, GROUND - 40, 640 + k * 40, GROUND - 10), fill=255)
    ground(A, GROUND)
    for k in range(4):
        person(A, 160 + k * 80, GROUND, 140, dir=1, robe=False, hat='helmet', bow=30, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('史记亦录', 44, INK), 860, 860, t, t - u + P, rot=6)
    paste(cv, text_img('士有饥者', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - 1.5 * P) / 0.3))

def art_g_mobei(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        x = lerp(-200, 900, ease_out(u / (3.5 * P))) - (k % 5) * 110
        rider(A, x, 1240 - (k // 5) * 60, 100, 1, t * 12 + k, layer='ink', spear=True)
    for k in range(10):
        x = lerp(-300, 800, ease_out(u / (3.5 * P))) - (k % 5) * 110
        rider(A, x, GROUND - (k // 5) * 40, 100, 1, t * 12 + k + 5, layer='rouge', spear=True)
    A.flush(cv)
    stamp(cv, seal('卫青', 44, INK), 260, 1100, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('霍去病', 44), 260, 1300, t, t - u + 0.8, rot=-5)
    paste(cv, text_img('各率五万骑', SERIF, 50, ROUGE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_g_left_king(A, cv, t, u):
    ground(A, GROUND)
    for k in range(12):
        x = 640 + (k % 6) * 60; y = GROUND - (k // 6) * 40
        person(A, x, y, 100, dir=-1, robe=False, hat='knot', fall=-80 * ease_out((u - P - k * 0.06) / 0.4), arm=40, layer='mid')
    huo_rider(A, lerp(-100, 480, ease_out(u / (1.5 * P))), GROUND, 170, dir=1, ph=t * 12)
    A.flush(cv)
    stamp(cv, seal('左贤王', 50, INK), 860, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('斩首七万余', SERIF, 52, ROUGE, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - 2 * P) / 0.3))

def art_g_pursuit(A, cv, t, u):
    A.d['dune'].polygon([(60, 1320), (W - 60, 1300), (W - 60, GROUND), (60, GROUND)], fill=120)
    ground(A, GROUND)
    for k in range(5):
        rider(A, lerp(500, 1200, ease_out(u / (3 * P))) + k * 80, GROUND, 100, 1, t * 13 + k, layer='mid')
    huo_rider(A, lerp(-100, 700, ease_out(u / (3 * P))), GROUND, 150, dir=1, ph=t * 13)
    A.flush(cv)
    paste(cv, text_img('追亡逐北', SERIF, 52, ROUGE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 封狼居胥
def art_g_langjuxu(A, cv, t, u):
    """8-beat set piece: 封狼居胥 — the army climbs the mountain; an altar rises; smoke goes up to heaven;
    the view swings north to the 瀚海."""
    ph = u / P
    if ph < 5.5:
        A.d['mid'].polygon([(120, GROUND), (540, 860), (960, GROUND)], fill=210)
        n = int(clamp(ph / 3) * 16)
        for k in range(n):
            f = k / 16
            x = lerp(220, 520, f); y = lerp(GROUND, 900, f)
            person(A, x, y, 60, dir=1, robe=False, hat='helmet', spear=True, ph=t * 5 + k, arm=40, layer='ink')
        alt = ease_out((ph - 2.5) / 1)
        if alt > 0:
            A.d['ink'].rectangle((500, 860 - 40 * alt, 580, 860), fill=255)
            for k in range(6):
                q = (t * 0.6 + k / 6) % 1
                A.d['wash'].ellipse((540 + 30 * math.sin(k + t * 2) - 16, lerp(820, 620, q) - 16, 540 + 30 * math.sin(k + t * 2) + 16, lerp(820, 620, q) + 16), fill=int(200 * (1 - q)))
        if ph >= 3.5:
            huo(A, 600, 860, 120, dir=-1, arm=150)
        ground(A, GROUND)
    else:
        river(A, 1080, t, rows=5, amp=10, speed=1.2)
        huo(A, 300, 1080, 260, dir=1, arm=lerp(40, 150, ease_out((ph - 5.5) / 1)), spear=True)
        A.d['mid'].polygon([(60, GROUND), (60, 1080), (420, 1080), (520, GROUND)], fill=230)
    A.flush(cv)
    if ph >= 3:
        stamp(cv, seal('狼居胥', 50), 860, 860, t, t - u + 3 * P, rot=6)
    if ph >= 6:
        paste(cv, text_img('登临瀚海', SERIF, 52, QILIAN, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((ph - 6) / 0.4))

def art_g_dasima(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    huo(A, 380, GROUND, 230, dir=1, arm=40)
    person(A, 700, GROUND, 240, dir=-1, robe=False, hat='helmet', arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('大司马', 54), 540, 880, t, t - u + P)

def art_g_favour(A, cv, t, u):
    ground(A, GROUND)
    person(A, 200, GROUND, 230, dir=1, robe=False, hat='helmet', arm=-8, layer='mid')
    huo(A, 820, GROUND, 240, dir=-1, arm=40)
    for k in range(5):
        x = lerp(260, 640 + k * 30, ease_out((u - k * 0.15) / (2.5 * P)))
        person(A, x, GROUND, 150, dir=1, robe=True, hat='none', ph=t * 4 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('门客转投', 44, INK), 540, 880, t, t - u + P)

def art_g_ligan(A, cv, t, u):
    tent(A, 540, GROUND, 600, 420, layer='mid')
    ground(A, GROUND)
    person(A, 400, GROUND, 230, dir=1, robe=False, hat='helmet', arm=lerp(40, 150, ease_out((u - 0.5 * P) / 0.3)), layer='ink')
    person(A, 680, GROUND, 230, dir=-1, robe=False, hat='helmet', fall=-30 * ease_out((u - 0.8 * P) / 0.3), arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('李敢', 54, INK), 300, 880, t, t - u + 0.4, rot=-5)

def art_g_hunt(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['grass'].polygon([(x - 120, GROUND), (x, GROUND - 260), (x + 120, GROUND)], fill=180)
    ground(A, GROUND)
    huo(A, 260, GROUND, 230, dir=1, arm=150, arm2=-120)
    ax = lerp(340, 760, ease_out((u - P) / 0.4))
    arrow(A, ax, GROUND - 170, 0.05, 80)
    person(A, 800, GROUND, 220, dir=-1, robe=False, hat='helmet', fall=-80 * ease_out((u - 1.4 * P) / 0.4), arm=40, layer='mid')
    A.flush(cv)
    stamp(cv, seal('甘泉', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('鹿触杀之', SERIF, 48, DIM, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((u - 2.2 * P) / 0.3))

def art_g_illness(A, cv, t, u):
    A.d['mid'].rectangle((300, 1180, 780, 1240), fill=230)
    A.d['ink'].rectangle((280, 1240, 800, 1270), fill=255)
    huo(A, 540, 1180, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('年仅二十三岁', SERIF, 52, ROUGE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_g_grief(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 240, dir=1, robe=True, hat='crown', bow=lerp(0, 30, ease_out(u / P)), arm=lerp(20, 140, ease_out(u / P)), layer='ink')
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=220)
    A.flush(cv)
    stamp(cv, seal('景桓侯', 54), 860, 880, t, t - u + P, rot=6)

# ================================================================ 第五回 冢象祁连
def art_g_funeral(A, cv, t, u):
    """6-beat set piece: 玄甲列阵 — black-armoured troops line the road from 长安 to 茂陵; the coffin carriage passes."""
    ph = u / P
    ground(A, GROUND)
    n = int(clamp(ph / 2.5) * 22)
    for k in range(n):
        x = 80 + (k % 11) * 92
        y = GROUND - 210 if k < 11 else GROUND
        person(A, x, y, 110 if k < 11 else 140, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='mid' if k < 11 else 'ink')
    if ph >= 2:
        x = lerp(1150, 200, ease_out((ph - 2) / 3.5))
        carriage(A, x, GROUND - 100, 140, dir=-1, wheel=u * 4, ph=t * 5, moving=True, layer='ink')
        A.d['rouge'].rectangle((x - 70, GROUND - 260, x + 70, GROUND - 200), fill=255)
    A.flush(cv)
    paste(cv, text_img('自长安至茂陵', SERIF, 48, ROUGE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(ph / 0.4))

def art_g_tomb_shape(A, cv, t, u):
    p = ease_out(u / (2 * P))
    A.d['qilian'].polygon([(160, GROUND), (330, GROUND - 260 * p), (460, GROUND - 160 * p), (600, GROUND - 330 * p), (760, GROUND - 200 * p), (920, GROUND)], fill=200)
    for k in range(6):
        x = 260 + k * 110
        A.d['ink'].ellipse((x - 16, GROUND - 120 * p - 16, x + 16, GROUND - 120 * p + 16), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('祁连', 56), 860, 880, t, t - u + 1.5 * P, rot=6)

def art_g_stone_horse(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((240, GROUND - 60, 840, GROUND), fill=230)
    horse(A, 540, GROUND - 60, 260, dir=1, ph=0, moving=False, layer='mid')
    person(A, 520, GROUND - 60, 120, dir=-1, robe=False, hat='knot', fall=-85, arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('马踏匈奴', 44), 860, 880, t, t - u + P, rot=6)

def art_g_liezhuan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='rouge')
    Sm.sima(A, 300, GROUND, 230, dir=1, beard=False, arm=60)
    Sm.slips(A, 440, GROUND - 74, int(4 + clamp(u / (2 * P)) * 12), 50, layer='candley', tied=False)
    A.flush(cv)
    stamp(cv, seal('卫将军骠骑列传', 30), 860, 880, t, t - u + P, rot=6)

def art_g_maoling(A, cv, t, u):
    A.d['mid'].polygon([(120, GROUND), (380, 1060), (640, GROUND)], fill=200)
    A.d['qilian'].polygon([(600, GROUND), (760, 1120), (960, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(4):
        person(A, 300 + k * 140, GROUND, 120, dir=1, robe=False, hat='knot', ph=t * 3 + k, arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('茂陵', 56), 860, 880, t, t - u + P, rot=6)

def art_g_youth(A, cv, t, u):
    ground(A, GROUND)
    huo_rider(A, lerp(-200, 1200, (u / (2 * P)) % 1), GROUND, 220, dir=1, ph=t * 12)
    A.flush(cv)
    paste(cv, text_img('少年英雄', SERIF, 56, ROUGE, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_g_legacy(A, cv, t, u):
    A.d['qilian'].polygon([(120, GROUND), (330, 1080), (540, 1180), (760, 1020), (960, GROUND)], fill=200)
    flag(A, 760, 1020, 160, t, w=60, layer='rouge')
    ground(A, GROUND)

def art_g_title(A, cv, t, u):
    horse(A, 760, 1460, 320, dir=-1, ph=0, moving=False, layer='mid')
    huo(A, 380, 1460, 680, dir=1, arm=lerp(-5, 45, ease_out(u / (2 * P))), spear=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '私生之子'), 48: ('第二回', '河西之战'), 80: ('第三回', '酒泉无家'),
            112: ('第四回', '封狼居胥'), 144: ('第五回', '冢象祁连')}

CARDS = [
    C(0, 2, 'empire', 'num', num='十七岁', line='封冠军侯', art=art_g_hook_17),
    C(2, 4, 'fate', 'num', num='封狼居胥', line='武将最高荣耀', art=art_g_hook_altar),
    C(4, 6, 'court', 'num', num='匈奴未灭', line='何以家为', art=art_g_hook_house),
    C(6, 8, 'death', 'num', num='二十三岁', line='英年早逝', art=art_g_hook_23),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 私生之子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-140, main='生于平阳', sub='卫少儿与霍仲孺之子', note='私生子 出身卑微', art=art_g_birth),
    C(22, 26, 'court', 'card', year=-139, main='姨母入宫', sub='卫子夫得宠 · 卫家显贵', art=art_g_aunt),
    C(26, 30, 'war', 'card', year=-129, main='舅舅卫青', sub='奴仆出身 · 龙城一战成名', art=art_g_uncle),
    C(30, 34, 'works', 'card', year=-126, main='少年骑射', sub='好骑射 · 不爱读古兵法', note='顾方略何如耳 不至学古兵法', art=art_g_archer),
    C(34, 38, 'court', 'card', year=-124, main='侍中', sub='在汉武帝身边做侍从', art=art_g_shizhong),
    C(38, 46, 'war', 'card', year=-123, main='八百骑', sub='剽姚校尉 · 离大军数百里', note='斩捕首虏二千余人', art=art_g_800),
    C(46, 48, 'empire', 'card', year=-123, main='冠军侯', sub='勇冠三军', art=art_g_marquis),
    # ---- 第二回 河西之战
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=-121, main='骠骑将军', sub='十九岁 · 独领一军', art=art_g_general),
    C(54, 62, 'war', 'hexi', year=-121),
    C(62, 66, 'empire', 'card', year=-121, main='祭天金人', sub='缴获休屠王祭天金人', art=art_g_golden),
    C(66, 70, 'night', 'card', year=-121, main='失我焉支', sub='匈奴悲歌', note='相传 匈奴人所作', art=art_g_lament),
    C(70, 74, 'fate', 'card', year=-121, main='河西受降', sub='浑邪王率众归汉', art=art_g_hunye),
    C(74, 80, 'war', 'card', year=-121, main='驰入敌营', sub='降众哗变 · 他亲自入营', note='斩欲亡者八千人', art=art_g_mutiny),
    # ---- 第三回 酒泉无家
    C(80, 82, 'empire', 'chapter'),
    C(82, 88, 'life', 'card', year=-121, main='酒泉', sub='御酒倾入泉中 · 与将士共饮', note='相传 酒泉由此得名', art=art_g_jiuquan),
    C(88, 92, 'works', 'card', year=-121, main='河西走廊', sub='打通西域之路', note='后设武威 张掖 酒泉 敦煌', art=art_g_corridor),
    C(92, 96, 'court', 'card', year=-120, main='何以家为', sub='武帝要为他建府第', art=art_g_no_home),
    C(96, 100, 'night', 'card', year=-120, main='体恤不足', sub='军中余粮丢弃 · 士卒却挨饿', note='史记亦录其短', art=art_g_flaw),
    C(100, 104, 'war', 'card', year=-119, main='漠北决战', sub='与卫青分兵出塞', art=art_g_mobei),
    C(104, 108, 'war', 'card', year=-119, main='击左贤王', sub='深入大漠两千余里', art=art_g_left_king),
    C(108, 112, 'fate', 'card', year=-119, main='穷追不舍', sub='一路追到狼居胥山', art=art_g_pursuit),
    # ---- 第四回 封狼居胥
    C(112, 114, 'fate', 'chapter'),
    C(114, 122, 'empire', 'card', year=-119, main='封狼居胥', sub='祭天于狼居胥 · 禅于姑衍', note='登临翰海', art=art_g_langjuxu),
    C(122, 126, 'court', 'card', year=-119, main='大司马', sub='与舅舅卫青同为大司马', art=art_g_dasima),
    C(126, 130, 'life', 'card', year=-119, main='恩宠日盛', sub='卫青门下多转投霍去病', art=art_g_favour),
    C(130, 134, 'night', 'card', year=-118, main='李敢', sub='李广之子 · 击伤卫青', art=art_g_ligan),
    C(134, 138, 'death', 'card', year=-118, main='甘泉射杀', sub='狩猎中射杀李敢', note='武帝为之隐讳', art=art_g_hunt),
    C(138, 142, 'death', 'card', year=-117, main='突然病逝', sub='死因不详', art=art_g_illness),
    C(142, 144, 'court', 'card', year=-117, main='武帝悲痛', sub='谥景桓侯', art=art_g_grief),
    # ---- 第五回 冢象祁连
    C(144, 146, 'death', 'chapter'),
    C(146, 152, 'death', 'card', year=-117, main='玄甲列阵', sub='铁甲军列阵送葬', note='发属国玄甲军', art=art_g_funeral),
    C(152, 156, 'fate', 'card', year=-117, main='冢象祁连', sub='墓冢修成祁连山之形', art=art_g_tomb_shape),
    C(156, 160, 'works', 'card', year=-117, main='马踏匈奴', sub='墓前石雕 · 至今尚存', art=art_g_stone_horse),
    C(160, 164, 'court', 'card', year=-91, main='合传', sub='司马迁将卫青霍去病合传', art=art_g_liezhuan),
    C(164, 168, 'empire', 'card', year=1961, main='茂陵', sub='霍去病墓 · 列为全国重点文物', art=art_g_maoling),
    C(168, 170, 'end', 'card', year=2026, main='少年英雄', sub='两千年来的代名词', art=art_g_youth),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾柒', col=ROUGE, acc=QILIAN, born=-140, died=-117,
    born_lab='前140年', died_lab='前117年', years_txt='公元前140 — 前117',
    hook_q='十七岁封侯 · 二十三岁离世 · 他做了什么？',
    name_line='霍去病 · 河东平阳人', name='霍去病', seal='骠骑', title_art=art_g_title,
    q1='天生战神？', q2='时势所造？',
    end_art=art_g_legacy, end_big='封狼居胥', end_seal='景桓',
    end_l1='他只活了二十三年', end_l2='却把汉旗插到了翰海',
    end_brush='匈奴未灭 何以家为', end_ask='如果他活得更久 会怎样？评论区聊聊', next='卫青'),
    scenes=dict(chapter=scene_chapter, hexi=scene_hexi))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
