"""千古人物志 · 第贰拾玖集 · 班超 (32–102)
Look: 和田玉绿 + 胡杨金, 玉璧 corner borders, a 玉门关 chapter card: more and more little state-flags gather west of
the gate each chapter; in the last chapter the gate opens for one old man.
Set pieces: 8-beat 投笔从戎, custom 8-beat scene 'shanshan' (不入虎穴: fire and drums in the wind),
6-beat 于阗斩巫, 6-beat 抱马脚, 8-beat 五十余国 map, 6-beat 回到洛阳.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_weiqing as Wq         # engine + helpers (previous episode)
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
from render_zhangqian import yurt, sheep
from render_wudi import camel
from render_simaqian import brush
from render_quyuan import river
from render_kongzi import bundle

F.RIPPLE = False
JADE = (56, 138, 108)               # 和田玉绿
POPLAR = (212, 150, 44)             # 胡杨金
S.LAYERS.append(('jade', JADE, 0.88, 1.0))
S.LAYERS.append(('poplar', POPLAR, 0.88, 1.2))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='超', life='班', court='汉', night='夜', war='虎', empire='域', works='笔', fate='守', death='归', end='超')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (POPLAR, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (JADE, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (POPLAR, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

POPLARS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(POPLARS)
_r = random.Random(12)
for _x in (90, 170, 920, 1000):
    _d.line((_x, 1480, _x + _r.uniform(-10, 10), 1300), fill=(110, 80, 50, 60), width=8)
    for _k in range(12):
        _px, _py = _x + _r.uniform(-50, 50), 1300 + _r.uniform(-60, 30)
        _d.ellipse((_px - 16, _py - 12, _px + 16, _py + 12), fill=POPLAR + (60,))
MTN_COL = {'night': (36, 40, 40), 'death': (62, 60, 58), 'war': (110, 72, 40), 'fate': (80, 96, 90)}
def draw_background(t, theme):
    """西域: Tian Shan ridges, golden desert poplars at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 190, 176), (162, 150, 128), MTN_COL.get(theme, (120, 110, 88))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.8))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(POPLARS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """玉璧: a jade disc with a hole, tied by a cord, in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = JADE + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=col, width=3); d.line((x, y, x, y + sy * 180), fill=col, width=3)
        cx, cy = x + sx * 52, y + sy * 52
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=col)
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(0, 0, 0, 0))
        d.line((cx + sx * 30, cy, cx + sx * 70, cy + sy * 20), fill=POPLAR + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def ban(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, old=False, **kw):
    """班超: scholar's 帻 head-cloth turned soldier; broad 'tiger neck', a curved saber at the hip; white beard when old."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.075 * h, y - 1.02 * h, x + 0.075 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line((x - dir * 0.06 * h, y - 0.96 * h, x - dir * 0.14 * h, y - 0.88 * h), fill=255, width=max(2, int(0.02 * h)))
        d.arc((x - dir * 0.3 * h - 0.2 * h, y - 0.62 * h, x - dir * 0.3 * h + 0.2 * h, y - 0.22 * h), 300 if dir > 0 else 200, 340 if dir > 0 else 240, fill=255, width=max(2, int(0.02 * h)))
        if old:
            A.d['wash'].polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.66 * h)], fill=255)
    return hand

def yumen(A, cx, base, s, open_=0.0, layer='poplar'):
    d = A.d[layer]
    d.rectangle((cx - 0.9 * s, base - s, cx + 0.9 * s, base), fill=230)
    for k in range(5):
        d.rectangle((cx - 0.9 * s + k * 0.4 * s, base - 1.12 * s, cx - 0.75 * s + k * 0.4 * s, base - s), fill=230)
    A.d['ink'].rectangle((cx - 0.25 * s, base - 0.55 * s, cx + 0.25 * s, base), fill=255)
    if open_ > 0:
        A.d['wash'].rectangle((cx - 0.25 * s * open_, base - 0.55 * s, cx + 0.25 * s * open_, base), fill=255)

def state_flag(A, x, base, s, t, k=0, layer='jade'):
    A.d['ink'].line((x, base, x, base - s), fill=255, width=3)
    A.d[layer].polygon([(x, base - s), (x + 0.6 * s + 0.08 * s * math.sin(t * 3 + k), base - 0.9 * s), (x, base - 0.75 * s)], fill=255)

def drum(A, x, base, s, hit=0.0):
    A.d['red'].ellipse((x - s, base - 1.2 * s, x + s, base - 0.2 * s), fill=255)
    A.d['ink'].ellipse((x - s, base - 1.2 * s, x + s, base - 0.2 * s), outline=255, width=5)
    A.d['ink'].line((x - 0.8 * s, base - 0.2 * s, x - s, base), fill=255, width=6); A.d['ink'].line((x + 0.8 * s, base - 0.2 * s, x + s, base), fill=255, width=6)
    if hit > 0:
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.5
            A.d['poplar'].line((x + 1.1 * s * math.cos(a), base - 0.7 * s + 1.1 * s * math.sin(a), x + (1.1 + 0.5 * hit) * s * math.cos(a), base - 0.7 * s + (1.1 + 0.5 * hit) * s * math.sin(a)), fill=255, width=4)

# ================================================================ chapter card
CH = {16: 1, 48: 5, 80: 12, 112: 30, 144: 50}
def art_yumen_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 5)
    q = ease_out(u / (1.2 * P))
    yumen(A, 760, 1220, 180, open_=ease_out((u - P) / P) if kb == 144 else 0)
    shown = int(n * q) + 1
    for i in range(min(shown, n)):
        x = 120 + (i % 10) * 46; y = 1220 - (i // 10) * 46
        state_flag(A, x, y, 40, t, i)
    if kb == 144:
        ban(A, lerp(400, 700, ease_out((u - 1.2 * P) / P)), 1220, 120, dir=1, old=True, ph=t * 3, arm=-8)
    ground(A, 1220)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_yumen_chapter)
    ink_in(cv, text_img(no, SERIF, 56, JADE, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_b_hook_36(A, cv, t, u):
    ground(A, GROUND)
    for i in range(36):
        x = 120 + (i % 12) * 28; y = GROUND - (i // 12) * 26
        A.d['ink'].ellipse((x - 9, y - 18, x + 9, y), fill=255)
    n = min(50, int(clamp(u / (1.6 * P)) * 50) + 1)
    for i in range(n):
        x = 520 + (i % 10) * 48; y = GROUND - 30 - (i // 10) * 60
        state_flag(A, x, y, 44, t, i)

def art_b_hook_brush(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 380, GROUND, 300, layer='jade')
    p = ease_out(u / (1.6 * P))
    brush(A, lerp(380, 300, p), lerp(GROUND - 90, GROUND - 6, p), 130, ang=lerp(-1.2, 0.1, p))
    ban(A, 720, GROUND, 260, dir=-1, armour=p > 0.5, arm=lerp(40, 150, p), sword=lerp(40, 160, p) if p > 0.5 else None)

def art_b_hook_31(A, cv, t, u):
    ground(A, GROUND)
    for k in range(31):
        x = 140 + (k % 16) * 52; y = GROUND - 30 - (k // 16) * 100
        A.d['poplar' if k < int(clamp(u / (1.6 * P)) * 31) else 'mid'].ellipse((x - 18, y - 18, x + 18, y + 18), fill=255)

def art_b_hook_gate(A, cv, t, u):
    yumen(A, 540, GROUND, 260, open_=ease_out(u / (1.6 * P)))
    ground(A, GROUND)
    ban(A, 300, GROUND, 160, dir=1, old=True, ph=t * 3, arm=-8)

# ================================================================ 第一回 投笔从戎
def art_b_birth(A, cv, t, u):
    palace(A, 720, GROUND, 360, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        sitter(A, 180 + k * 150, GROUND, 150 - k * 25, dir=1, bow=15)
    A.flush(cv)
    stamp(cv, seal('班彪', 40, INK), 180, 1100, t, t - u + 0.4)
    stamp(cv, seal('班固', 40, INK), 330, 1120, t, t - u + 0.8)
    stamp(cv, seal('平陵', 54), 760, 860, t, t - u + P, rot=6)

def art_b_father(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    for k in range(30):
        q = (t * 0.3 + k / 30) % 1
        x = 80 + (k * 31) % 920
        A.d['mid'].line((x, lerp(620, 1420, q), x - 6, lerp(620, 1420, q) + 26), fill=180, width=2)
    ground(A, GROUND)
    for k in range(3):
        person(A, 780 + k * 70, GROUND, 170 - k * 20, dir=-1, robe=True, hat='knot', female=k == 2, kneel=True, bow=50, arm=100, layer='ink')
    A.flush(cv)
    stamp(cv, seal('家道中落', 44, INK), 300, 900, t, t - u + P, rot=-5)

def art_b_copyist(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='jade')
    sitter(A, 300, GROUND, 220, dir=1, bow=25)
    n = int(clamp(u / (3 * P)) * 30)
    for k in range(n):
        A.d['wash'].rectangle((420 + (k % 10) * 24, GROUND - 76 - (k // 10) * 8, 438 + (k % 10) * 24, GROUND - 70 - (k // 10) * 8), fill=255)
    lamp(A, 760, GROUND - 70, 40, t, glow=0.6)
    person(A, 900, GROUND, 170, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('佣书', 54), 260, 880, t, t - u + P, rot=-5)

def art_b_throw_brush(A, cv, t, u):
    """8-beat set piece: 投笔从戎 — copying by lamplight; he stops, lifts the brush, flings it down; stands; the brush
    gives way to a saber, the lamp to a sunrise over the desert road."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 420, GROUND, 360, layer='jade')
    if ph < 3.5:
        lamp(A, 600, GROUND - 70, 40, t, glow=0.6)
        sitter(A, 200, GROUND, 220, dir=1, bow=lerp(25, 0, ease_out((ph - 1.5) / 1)))
        if ph < 2.5:
            brush(A, 330, GROUND - 120, 100, ang=-1.0)
        else:
            q = ease_out((ph - 2.5) / 1)
            brush(A, lerp(330, 560, q), lerp(GROUND - 160, GROUND - 6, q), 100, ang=lerp(-1.0, 2.6, q))
    else:
        sun(cv, 860, lerp(1300, 980, ease_out((ph - 3.5) / 3)), 120, POPLAR, 140)
        brush(A, 560, GROUND - 6, 100, ang=2.6)
        ban(A, lerp(220, 760, ease_out((ph - 4) / 3)), GROUND, 250, dir=1, armour=True, ph=t * 4, arm=60, sword=40)
    A.flush(cv)
    if ph >= 1.5:
        type_in(cv, text_img('安能久事笔砚间乎', SERIF, 48, JADE, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)
    if ph >= 4:
        paste(cv, text_img('当效张骞 立功异域', SERIF, 46, POPLAR, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_b_physiognomy(A, cv, t, u):
    ground(A, GROUND)
    person(A, 720, GROUND, 220, dir=-1, robe=True, hat='knot', arm=lerp(40, 130, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.d['ink'].line((790, GROUND - 200, 820, GROUND), fill=255, width=6)
    ban(A, 360, GROUND, 250, dir=1, arm=-8)
    A.d['poplar'].ellipse((300, GROUND - 270, 420, GROUND - 200), outline=255, width=4)
    A.flush(cv)
    type_in(cv, text_img('燕颔虎颈 飞而食肉', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('此万里侯相也', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

def art_b_north(A, cv, t, u):
    A.d['ocean'].ellipse((560, 1220, 980, 1320), fill=150)
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(-200, 600, ease_out(u / (3 * P))) - k * 90, GROUND - (k % 2) * 30, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('窦固', 50), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('蒲类海', 46, INK), 780, 1180, t, t - u + 1.6 * P, rot=6)

def art_b_sima(A, cv, t, u):
    tent(A, 760, GROUND, 400, 300, layer='mid')
    ground(A, GROUND)
    ban(A, 360, GROUND, 260, dir=1, armour=True, arm=lerp(40, 150, ease_out(u / P)), sword=60)
    A.flush(cv)
    stamp(cv, seal('假司马', 54), 760, 860, t, t - u + P, rot=6)

# ================================================================ 第二回 不入虎穴
def art_b_36(A, cv, t, u):
    ground(A, GROUND)
    city_wall(A, 60, 360, 1100, gate_x=210, label='玉门', layer='poplar', open_=1.0)
    n = min(36, int(clamp(u / (2.5 * P)) * 36) + 1)
    for i in range(n):
        x = lerp(220, 520 + (i % 12) * 40, ease_out((u - i * 0.03) / (2.5 * P))); y = GROUND - (i // 12) * 36
        if i == 0:
            ban(A, x + 60, y, 130, dir=1, armour=True, ph=t * 5, arm=40)
        else:
            person(A, x, y, 70, dir=1, robe=False, hat='knot', ph=t * 5 + i, arm=20, layer='ink' if i // 12 == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'{n}人', SERIF, 56, JADE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, 1)

def art_b_cold(A, cv, t, u):
    yurt(A, 760, GROUND, 360, 300, layer='jade')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='crown', bow=lerp(30, -5, ease_out((u - P) / P)), arm=lerp(90, 10, ease_out((u - P) / P)), layer='ink')
    ban(A, 360, GROUND, 230, dir=1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('鄯善', 56), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('礼敬骤减', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - 1.6 * P) / 0.3))

def scene_shanshan(cv, t, c, k):
    """8-beat custom scene: 不入虎穴 — night wind; the 匈奴 envoys' tents; ten men with drums behind them; the rest by the
    gate; fire is set upwind; drums roar; the camp burns; dawn, and 鄯善 bows."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(40):
        x = 80 + (k2 * 37) % 920; y = 640 + (k2 * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    for k2 in range(30):
        q = (t * 0.9 + k2 / 30) % 1
        A.d['mid'].line((lerp(-100, 1200, q), 700 + (k2 * 47) % 600, lerp(-100, 1200, q) + 50, 700 + (k2 * 47) % 600), fill=120, width=2)
    for i in range(4):
        tent(A, 400 + i * 150, GROUND, 140, 120, layer='mid')
    ground(A, GROUND)
    if ph >= 1.5:
        for i in range(3):
            drum(A, 940, GROUND - i * 90, 32, hit=(0.5 + 0.5 * math.sin(t * 14 + i)) if ph >= 3 else 0)
    if ph >= 2.5:
        flames(A, 520, GROUND, 600, 340 * ease_out((ph - 2.5) / 1.5), t, n=8, seed=33, smoke=True)
    if ph >= 3.5:
        for i in range(6):
            x = lerp(150, 380 + i * 50, ease_out((ph - 3.5) / 1))
            person(A, x, GROUND, 110, dir=1, robe=False, hat='knot', sword=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 9 + i)), arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 9 + i)), layer='ink')
    ban(A, 150, GROUND, 170, dir=1, armour=True, arm=lerp(40, 160, ease_out((ph - 2) / 0.5)), sword=60)
    A.flush(cv)
    fx = Art()
    if ph < 5:
        chars_in(cv, fx, '不入虎穴', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=58)
    else:
        chars_in(cv, fx, '焉得虎子', BRUSH, 150, ZHU, W / 2, 440, t, s0 + 5 * P, stagger=0.08, seed=59)
    fx.flush(cv)
    lab = '北匈奴使者百余人' if ph < 2.5 else ('顺风纵火 前后鼓噪' if ph < 5 else '斩其使 余众悉烧死')
    paste(cv, text_img(lab, SERIF, 46, POPLAR, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元七十三年 · 鄯善', SERIF, 42, JADE, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_b_shanshan_submits(A, cv, t, u):
    yurt(A, 760, GROUND, 360, 300, layer='jade')
    ground(A, GROUND)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='crown', kneel=True, bow=45, arm=110, layer='ink')
    person(A, 560, GROUND, 110, dir=-1, robe=True, hat='knot', arm=60, layer='ink')
    ban(A, 300, GROUND, 240, dir=1, armour=True, arm=40)
    A.flush(cv)
    stamp(cv, seal('纳子为质', 46), 860, 860, t, t - u + P, rot=6)

def art_b_khotan(A, cv, t, u):
    """6-beat: 于阗斩巫 — the shaman demands the envoy's horse for the gods; 班超 has him fetch it himself and beheads him;
    the king, shaken, kills the 匈奴 envoy and submits."""
    ph = u / P
    yurt(A, 800, GROUND, 320, 280, layer='poplar')
    ground(A, GROUND)
    horse(A, 160, GROUND, 150, dir=1, ph=0, moving=False, layer='mid')
    if ph < 2.5:
        person(A, lerp(700, 380, ease_out(ph / 2)), GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
    else:
        person(A, 380, GROUND, 200, dir=-1, robe=True, hat='knot', fall=-85 * ease_out((ph - 2.5) / 0.4), arm=60, layer='ink')
    ban(A, 260, GROUND, 230, dir=1, armour=True, arm=lerp(40, 160, ease_out((ph - 2.2) / 0.3)), sword=lerp(40, 160, ease_out((ph - 2.2) / 0.3)))
    if ph >= 4:
        person(A, 800, GROUND, 200, dir=-1, robe=True, hat='crown', kneel=True, bow=45, arm=110, layer='ink')
    A.flush(cv)
    stamp(cv, seal('于阗', 54), 860, 1020, t, t - u + 0.4, rot=6)
    lab = '巫言 神怒 索汉使之马' if ph < 2.5 else ('斩巫' if ph < 4 else '于阗王杀匈奴使者 而降')
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2.5 <= ph < 4 else POPLAR, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_b_shule(A, cv, t, u):
    city_wall(A, 520, 1000, 1100, gate_x=760, label='疏勒', layer='jade', open_=1.0)
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='crown', arm=lerp(20, 160, ease_out((u - P) / 0.4)), layer='mid')
    person(A, lerp(500, 700, ease_out(u / P)), GROUND, 200, dir=1, robe=False, hat='helmet', arm=120, layer='ink')
    A.d['ink'].line((640, GROUND - 160, 760, GROUND - 160), fill=255 if u > P else 0, width=6)
    A.flush(cv)
    stamp(cv, seal('劫兜题', 50, INK), 260, 880, t, t - u + P, rot=-5)

# ================================================================ 第三回 孤军坚守
def art_b_chenmu(A, cv, t, u):
    city_wall(A, 300, 780, 1100, gate_x=540, label='都护府', layer='mid')
    flames(A, 540, 1100, 520, 260 * ease_out((u - 0.5 * P) / 0.8), t, n=6, seed=41, smoke=True)
    ground(A, GROUND)
    for k in range(5):
        rider(A, lerp(-150, 240, ease_out(u / (2 * P))) - k * 100, GROUND, 110, 1, t * 11 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('焉耆', 54, INK), 860, 860, t, t - u + 0.4, rot=6)
    stamp(cv, seal('陈睦', 46), 860, 980, t, t - u + 1.5 * P, rot=6)

def art_b_recall(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 230, dir=1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / 0.5)), layer='ink')
    x = lerp(1100, 760, ease_out((u - P) / (1.5 * P)))
    rider(A, x, GROUND, 140, 1, t * 11, layer='ink')
    A.d['wash'].rectangle((x + 30, GROUND - 230, x + 80, GROUND - 200), fill=255)
    A.flush(cv)
    stamp(cv, seal('罢都护', 50), 260, 880, t, t - u + 0.5, rot=-5)

def art_b_clasp(A, cv, t, u):
    """6-beat: 抱马脚 — on the road home the 于阗 nobles throw themselves around his horse's legs; he turns back."""
    ph = u / P
    ground(A, GROUND)
    x = 600 if ph < 4 else lerp(600, 300, ease_out((ph - 4) / 1.5))
    dirn = 1 if ph < 4 else -1
    horse(A, x, GROUND, 180, dir=dirn, ph=t * 6 if ph >= 4 else 0, moving=ph >= 4, layer='ink')
    ban(A, x - dirn * 10, GROUND - 140, 150, dir=dirn, arm=lerp(20, 80, ease_out((ph - 3) / 0.6)))
    if ph < 4:
        for k in range(6):
            side = -1 if k % 2 else 1
            px = x + side * (100 + (k // 2) * 70)
            person(A, px, GROUND, 140, dir=-side, robe=True, hat='crown' if k < 2 else 'knot', kneel=True, bow=60, arm=150, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('依汉使如父母 诚不可去', SERIF, 46, POPLAR, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.8 * P, 0.5)
    if ph >= 4:
        paste(cv, text_img('他调转马头', SERIF, 50, JADE, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((ph - 4) / 0.3))

def art_b_back_shule(A, cv, t, u):
    city_wall(A, 120, 600, 1100, gate_x=360, label='疏勒', layer='jade', open_=1.0)
    ground(A, GROUND)
    ban(A, lerp(1000, 640, ease_out(u / (2 * P))), GROUND, 230, dir=-1, armour=True, ph=t * 4, arm=60, sword=40)
    for k in range(4):
        person(A, 760 + k * 60, GROUND, 120, dir=-1, robe=False, hat='knot', fall=-80 * ease_out((u - 2 * P - k * 0.1) / 0.4), arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('斩反者六百余人', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 2.2 * P) / 0.3))

def art_b_gumo(A, cv, t, u):
    city_wall(A, 560, 1000, 1080, gate_x=780, label='姑墨', layer='mid')
    ground(A, GROUND)
    for i, layer in enumerate(('jade', 'poplar', 'ink', 'mid')):
        for k in range(3):
            person(A, lerp(-100, 200 + i * 90, ease_out((u - i * 0.2) / (2 * P))) - k * 30, GROUND - i * 20, 100, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer=layer)
    A.flush(cv)
    paste(cv, text_img('诸国兵一万', SERIF, 50, JADE, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_b_memorial(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='jade')
    ban(A, 300, GROUND, 230, dir=1, kneel=True, bow=15, arm=90)
    scroll(A, 600, GROUND - 120, 260, 70, u / 0.6)
    lamp(A, 800, GROUND - 70, 40, t, glow=0.6)
    A.flush(cv)
    type_in(cv, text_img('以夷狄攻夷狄', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + P, 0.5)

def art_b_shache(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    ground(A, GROUND)
    ph = u / P
    x = lerp(500, 120, ease_out(ph / 1.5)) if ph < 1.5 else lerp(120, 800, ease_out((ph - 2) / 1.5))
    for k in range(5):
        rider(A, x - k * 70 * (1 if ph >= 1.5 else -1), GROUND, 110, 1 if ph >= 1.5 else -1, t * 12 + k, layer='ink', spear=True)
    for k in range(3):
        yurt(A, 700 + k * 110, GROUND, 100, 90)
    if ph >= 3:
        flames(A, 810, GROUND, 360, 180 * ease_out((ph - 3) / 0.6), t, n=5, seed=8, smoke=True)
    A.flush(cv)
    stamp(cv, seal('莎车', 54, INK), 860, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('佯退 · 夜袭', SERIF, 50, POPLAR, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 五十余国
def art_b_yuezhi(A, cv, t, u):
    city_wall(A, 120, 520, 1100, gate_x=320, label=None, layer='jade', open_=0.0)
    ground(A, GROUND)
    for k in range(12):
        rider(A, lerp(1100, 640, ease_out(u / (2 * P))) + (k % 6) * 70, GROUND - (k // 6) * 40, 100, -1, t * 6 + k, layer='mid', spear=True, moving=u < 2 * P)
    for k in range(4):
        A.d['red'].line((560 + k * 100, 960, 600 + k * 100, 1000), fill=255, width=6); A.d['red'].line((600 + k * 100, 960, 560 + k * 100, 1000), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('月氏七万', 44, INK), 860, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('坚壁清野 断其外援', SERIF, 46, JADE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_duhu(A, cv, t, u):
    city_wall(A, 220, 860, 1100, gate_x=540, label='龟兹', layer='poplar', open_=1.0)
    ground(A, GROUND)
    flag(A, 540, 1100, 200, t, w=70, layer='red')
    ban(A, 540, GROUND, 220, dir=1, armour=True, arm=40)
    for k in range(4):
        person(A, 200 + k * 70 if k < 2 else 760 + (k - 2) * 70, GROUND, 140, dir=1 if k < 2 else -1, robe=True, hat='crown', kneel=True, bow=45, arm=100, layer='mid')
    A.flush(cv)
    stamp(cv, seal('西域都护', 44), 860, 860, t, t - u + P, rot=6)

NATIONS = [(200, 900), (300, 960), (420, 880), (520, 960), (640, 900), (760, 960), (860, 880), (240, 1060), (360, 1120),
           (480, 1060), (600, 1120), (720, 1060), (840, 1120), (180, 1220), (300, 1260), (430, 1220), (560, 1280),
           (690, 1220), (820, 1270), (930, 1200)]
def art_b_fifty(A, cv, t, u):
    """8-beat set piece: 五十余国 — a map of oasis states; one by one they turn jade; 焉耆 last, with 八国兵七万 converging."""
    ph = u / P
    A.d['dune'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=110)
    n = min(len(NATIONS), int(ph * len(NATIONS) / 6))
    for i, (x, y) in enumerate(NATIONS):
        A.d['jade' if i < n else 'mid'].ellipse((x - 34, y - 26, x + 34, y + 26), fill=230)
    if ph >= 6:
        tx, ty = 540, 1360
        for i in range(8):
            a = math.pi + (i + 0.5) * math.pi / 8
            sx, sy = tx + 400 * math.cos(a), ty + 300 * math.sin(a)
            q = ease_out((ph - 6) / 1.2)
            A.d['red'].line((sx, sy, lerp(sx, tx, q), lerp(sy, ty, q)), fill=230, width=5)
        A.d['ink'].ellipse((tx - 40, ty - 30, tx + 40, ty + 30), fill=255)
    A.flush(cv)
    if ph >= 6:
        stamp(cv, seal('焉耆', 40, INK), 540, 1360, t, t - u + 6 * P)
    paste(cv, text_img(f'归附 {int(n * 2.5)} 国' if ph < 6 else '八国兵七万 · 讨平焉耆', SERIF, 48, JADE if ph < 6 else ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_b_marquis(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='poplar')
    ground(A, GROUND)
    x = lerp(1100, 700, ease_out(u / (1.5 * P)))
    rider(A, x, GROUND, 140, -1, t * 11, layer='ink', moving=u < 1.5 * P)
    ban(A, 360, GROUND, 230, dir=1, kneel=True, bow=40, arm=100, old=True)
    A.flush(cv)
    stamp(cv, seal('定远侯', 56), 540, 860, t, t - u + 1.6 * P)

def art_b_ganying(A, cv, t, u):
    river(A, 1220, t, rows=4, amp=8)
    ground(A, 1220, x0=60, x1=520)
    x = lerp(-80, 460, ease_out(u / (2.5 * P)))
    camel(A, x, 1220, 110, 1, t * 5, layer='ink')
    person(A, x - 140, 1220, 150, dir=1, robe=True, hat='knot', ph=t * 4, arm=20, layer='ink')
    A.flush(cv)
    stamp(cv, seal('甘英', 54), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('西海', 54, INK), 800, 1000, t, t - u + 2 * P, rot=6)

def art_b_petition(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='jade')
    ban(A, 300, GROUND, 220, dir=1, kneel=True, bow=25, arm=90, old=True)
    lamp(A, 780, GROUND - 70, 40, t, glow=0.5)
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    A.flush(cv)
    paste(cv, text_img('年近七十', SERIF, 52, POPLAR, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp((u - 0.5 * P) / 0.3))

def art_b_yumen_wish(A, cv, t, u):
    yumen(A, 700, GROUND, 230)
    ground(A, GROUND)
    ban(A, 260, GROUND, 230, dir=1, old=True, arm=lerp(-8, 60, ease_out(u / P)))
    A.flush(cv)
    type_in(cv, text_img('臣不敢望到酒泉郡', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('但愿生入玉门关', SERIF, 52, ZHU, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第五回 生入玉门
def art_b_banzhao(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='crown', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    person(A, 340, GROUND, 210, dir=1, robe=True, hat='knot', female=True, kneel=True, bow=30, arm=100, layer='ink')
    scroll(A, 520, 1080, 160, 60, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('班昭', 54), 260, 880, t, t - u + 0.4, rot=-5)

def art_b_return(A, cv, t, u):
    """6-beat: 回到洛阳 — the 玉门关 opens; an old man on a tired horse rides through; the counter reads 三十一年."""
    ph = u / P
    yumen(A, 540, GROUND, 260, open_=ease_out(ph / 2))
    ground(A, GROUND)
    x = lerp(980, 100, ease_out((ph - 1.5) / 4))
    horse(A, x, GROUND, 130, dir=-1, ph=t * 4, layer='ink')
    ban(A, x + 6, GROUND - 100, 120, dir=-1, old=True, arm=20)
    A.flush(cv)
    paste(cv, text_img('去时四十一岁 · 归来七十岁', SERIF, 46, JADE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(ph / 0.4))
    if ph >= 3:
        paste(cv, text_img('在西域三十一年', SERIF, 52, POPLAR, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((ph - 3) / 0.4))

def art_b_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    ban(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('归来一月即卒', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_b_houhanshu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='jade')
    sitter(A, 300, GROUND, 220, dir=1, bow=15)
    for i in range(int(clamp(u / (2 * P)) * 4) + 1):
        bundle(A, 640 + i * 80, GROUND - 60, 60, layer='poplar')
    A.flush(cv)
    stamp(cv, seal('范晔', 54), 860, 880, t, t - u + 0.4, rot=6)
    ink_in(cv, text_img('班梁列传', SERIF, 48, JADE, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + P, dur=0.3)

def art_b_idioms(A, cv, t, u):
    ground(A, GROUND)
    brush(A, 360, GROUND - 6, 140, ang=2.6)
    ban(A, 660, GROUND, 240, dir=1, armour=True, arm=60, sword=40)
    A.flush(cv)
    type_in(cv, text_img('投笔从戎', SERIF, 50, JADE, 'Black', bleed=False, spacing=8), 330, 830, t, t - u + 0.3, 0.4)
    type_in(cv, text_img('不入虎穴 焉得虎子', SERIF, 46, ZHU, 'Black', bleed=False, spacing=6), W / 2, 910, t, t - u + 1.4 * P, 0.5)

def art_b_road(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = (t * 70 + k * 190) % (W + 300) - 150
        camel(A, x, GROUND, 100, 1, t * 5 + k, layer='ink' if k % 2 else 'poplar')
    yumen(A, 540, 1200, 120)
    A.flush(cv)
    paste(cv, text_img('丝路畅通', SERIF, 52, JADE, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_b_legacy(A, cv, t, u):
    yumen(A, 540, 1260, 260, open_=1.0)
    ground(A, 1260)

def art_b_title(A, cv, t, u):
    yumen(A, 820, 1460, 220)
    ban(A, 400, 1460, 680, dir=1, armour=True, arm=lerp(-5, 40, ease_out(u / (2 * P))), sword=40)

# ================================================================ script
CHAPTERS = {16: ('第一回', '投笔从戎'), 48: ('第二回', '不入虎穴'), 80: ('第三回', '孤军坚守'),
            112: ('第四回', '五十余国'), 144: ('第五回', '生入玉门')}

CARDS = [
    C(0, 2, 'empire', 'num', num='三十六人', line='收服西域五十国', art=art_b_hook_36),
    C(2, 4, 'works', 'num', num='投笔从戎', line='中年弃文从武', art=art_b_hook_brush),
    C(4, 6, 'fate', 'num', num='三十一年', line='孤身镇守西域', art=art_b_hook_31),
    C(6, 8, 'death', 'num', num='玉门关', line='但愿生入', art=art_b_hook_gate),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 投笔从戎
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=32, main='生于平陵', sub='史学世家 · 父班彪 兄班固', art=art_b_birth),
    C(22, 26, 'death', 'card', year=54, main='父亲去世', sub='家道中落', art=art_b_father),
    C(26, 30, 'works', 'card', year=62, main='佣书养母', sub='随兄迁居洛阳 · 为官府抄书', art=art_b_copyist),
    C(30, 38, 'works', 'card', year=62, main='投笔从戎', sub='掷笔而叹', note='时间不详 约在此后十年间', art=art_b_throw_brush),
    C(38, 42, 'life', 'card', year=62, main='万里侯相', sub='相者如此说他', art=art_b_physiognomy),
    C(42, 46, 'war', 'card', year=73, main='随军北征', sub='随窦固击北匈奴', art=art_b_north),
    C(46, 48, 'war', 'card', year=73, main='假司马', sub='初露锋芒', art=art_b_sima),
    # ---- 第二回 不入虎穴
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'empire', 'card', year=73, main='出使西域', sub='一行仅三十六人', art=art_b_36),
    C(54, 58, 'court', 'card', year=73, main='鄯善冷遇', sub='国王礼数骤减', note='必有北虏使来', art=art_b_cold),
    C(58, 66, 'night', 'shanshan', year=73),
    C(66, 70, 'empire', 'card', year=73, main='鄯善归附', sub='举国震怖', art=art_b_shanshan_submits),
    C(70, 76, 'war', 'card', year=73, main='于阗斩巫', sub='巫师索要汉使之马', art=art_b_khotan),
    C(76, 80, 'works', 'card', year=74, main='智取疏勒', sub='劫持龟兹所立之王', art=art_b_shule),
    # ---- 第三回 孤军坚守
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'war', 'card', year=75, main='都护遇害', sub='焉耆攻杀都护陈睦', art=art_b_chenmu),
    C(86, 90, 'court', 'card', year=76, main='朝廷召还', sub='新君下诏 · 罢西域', art=art_b_recall),
    C(90, 96, 'fate', 'card', year=76, main='抱马脚', sub='于阗王侯抱住马腿 · 不让他走', art=art_b_clasp),
    C(96, 100, 'war', 'card', year=76, main='重返疏勒', sub='平定叛乱', art=art_b_back_shule),
    C(100, 104, 'war', 'card', year=78, main='攻破姑墨', sub='率诸国兵 · 破姑墨石城', art=art_b_gumo),
    C(104, 108, 'works', 'card', year=80, main='以夷制夷', sub='上书请兵', note='以夷狄攻夷狄 计之善者也', art=art_b_memorial),
    C(108, 112, 'night', 'card', year=87, main='奇袭莎车', sub='佯退夜袭 · 莎车降', art=art_b_shache),
    # ---- 第四回 五十余国
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'war', 'card', year=90, main='月氏来犯', sub='副王谢率七万人来攻', note='月氏由是大震', art=art_b_yuezhi),
    C(118, 122, 'empire', 'card', year=91, main='西域都护', sub='龟兹等国归降', art=art_b_duhu),
    C(122, 130, 'empire', 'card', year=94, main='五十余国', sub='皆纳质内属', art=art_b_fifty),
    C(130, 134, 'court', 'card', year=95, main='定远侯', sub='应了当年相者之言', art=art_b_marquis),
    C(134, 138, 'works', 'card', year=97, main='甘英西行', sub='遣使大秦 · 抵西海而还', note='一说 西海即波斯湾', art=art_b_ganying),
    C(138, 142, 'fate', 'card', year=100, main='上书求归', sub='久在绝域 · 年老思乡', art=art_b_petition),
    C(142, 144, 'death', 'card', year=100, main='玉门之望', sub='一封求归的奏书', art=art_b_yumen_wish),
    # ---- 第五回 生入玉门
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'court', 'card', year=102, main='班昭上书', sub='妹妹替兄长求情', art=art_b_banzhao),
    C(150, 156, 'end', 'card', year=102, main='回到洛阳', sub='朝廷终于允归', art=art_b_return),
    C(156, 160, 'death', 'card', year=102, main='病逝', sub='享年七十', art=art_b_death),
    C(160, 164, 'works', 'card', year=445, main='后汉书', sub='范晔为其立传', art=art_b_houhanshu),
    C(164, 168, 'life', 'card', year=445, main='成语流传', sub='两个成语 · 一个人', art=art_b_idioms),
    C(168, 170, 'end', 'card', year=2026, main='丝路', sub='他守护过的路', art=art_b_road),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='贰拾玖', col=JADE, acc=POPLAR, born=32, died=102,
    hook_q='带三十六人 · 他怎么收服西域五十国？',
    name_line='班超 · 字仲升', name='班超', seal='定远', title_art=art_b_title,
    q1='孤胆英雄？', q2='运气使然？',
    end_art=art_b_legacy, end_big='投笔从戎', end_seal='定远',
    end_l1='他年过四十才出发', end_l2='在西域守了三十一年',
    end_brush='不入虎穴焉得虎子', end_ask='你敢中年转行吗？评论区聊聊', next='蔡伦'),
    scenes=dict(chapter=scene_chapter, shanshan=scene_shanshan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
