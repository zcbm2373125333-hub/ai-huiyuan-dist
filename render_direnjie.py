"""千古人物志 · 第肆拾壹集 · 狄仁杰 (630–700)
Look: 绯袍红 + 案牍青, 獬豸 (justice beast horn) corner borders, a 卷宗 chapter card: the stack of case files
shrinks chapter by chapter as cases are cleared, and the last chapter shows a single closed file.
Set pieces: custom 8-beat scene 'yinian' (一年断案一万七千人), 6-beat 谋反下狱 (血书藏棉衣), 8-beat 劝立庐陵王,
6-beat 举荐张柬之, 6-beat 斗转星移.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_guoziyi as Gz         # engine + helpers (previous episode)
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
from render_kongzi import bundle
from render_libai import moon_phase
from render_songtaizu import tent

F.RIPPLE = False
FEI = (176, 44, 52)                 # 绯袍红
DU = (66, 104, 110)                 # 案牍青
S.LAYERS.append(('fei', FEI, 0.88, 1.0))
S.LAYERS.append(('du', DU, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='案', life='狄', court='周', night='狱', war='边', empire='周', works='断', fate='忠', death='斗', end='狄')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (FEI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (DU, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

SHELF = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(SHELF)
for _x0 in (70, W - 190):
    for _r in range(5):
        _y = 1190 + _r * 58
        _d.rectangle((_x0, _y, _x0 + 120, _y + 5), fill=DU + (44,))
        for _k in range(4):
            _d.rectangle((_x0 + 8 + _k * 28, _y - 30, _x0 + 30 + _k * 28, _y), fill=DU + (30,))
MTN_COL = {'night': (36, 36, 40), 'death': (60, 60, 62), 'war': (104, 66, 54), 'fate': (80, 96, 98)}
def draw_background(t, theme):
    """大理寺: low ridges, case-file shelves at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 186, 184), (148, 150, 150), MTN_COL.get(theme, (108, 118, 120))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(SHELF)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """獬豸角: a single curved horn rising from each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=DU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=DU + (220,), width=3)
        pts = [(x + sx * (20 + 10 * f + 40 * f * f), y + sy * (90 - 80 * f)) for f in np.linspace(0, 1, 12)]
        for i in range(len(pts) - 1):
            d.line((pts[i], pts[i + 1]), fill=FEI + (230,), width=int(10 - 7 * i / 11))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def di(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """狄仁杰: official 幞头 with long straight wings, square beard; red robe sash band."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.065 * h, y - 1.05 * h, x + 0.065 * h, y - 0.94 * h), fill=255)
        d.rectangle((x - 0.28 * h, y - 1.0 * h, x + 0.28 * h, y - 0.985 * h), fill=255)
        d.rectangle((min(x, x + dir * 0.08 * h), y - 0.86 * h, max(x, x + dir * 0.08 * h), y - 0.7 * h), fill=255)
        A.d['fei'].rectangle((x - 0.1 * h, y - 0.56 * h, x + 0.1 * h, y - 0.51 * h), fill=255)
        if old > 0.4:
            A.d['wash'].rectangle((min(x + dir * 0.01 * h, x + dir * 0.07 * h), y - 0.84 * h, max(x + dir * 0.01 * h, x + dir * 0.07 * h), y - 0.74 * h), fill=255)
    return hand

def wuzetian(A, x, y, h, dir=1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', female=True, layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d['gold'].polygon([(x - 0.08 * h, y - 0.98 * h), (x, y - 1.12 * h), (x + 0.08 * h, y - 0.98 * h)], fill=255)
    return hand

def files(A, x, base, n, s=60, layer='du'):
    for i in range(n):
        yy = base - i * 0.22 * s
        A.d[layer if i % 2 else 'mid'].rectangle((x - s, yy - 0.2 * s, x + s, yy), fill=255)
        A.d['ink'].rectangle((x - s, yy - 0.2 * s, x + s, yy), outline=120, width=2)

def stars(A, t, n=50, seed=4):
    r = random.Random(seed)
    for k in range(n):
        x, y = r.uniform(100, 980), r.uniform(640, 1100)
        tw = max(0.5, 2 + 2 * math.sin(t * 2.4 + k))
        A.d['wash'].ellipse((x - tw, y - tw, x + tw, y + tw), fill=255)

# ================================================================ chapter card
CH = {16: 20, 48: 16, 80: 10, 112: 5, 144: 1}
def art_files_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 16)
    prev = {48: 20, 80: 16, 112: 10, 144: 5}.get(kb, n)
    q = ease_out(u / (1.2 * P))
    files(A, 540, 1200, int(lerp(prev, n, q)), s=150)
    if kb == 144:
        A.d['fei'].rectangle((520, 1140, 560, 1200), fill=255)
    ground(A, 1200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_files_chapter)
    ink_in(cv, text_img(no, SERIF, 56, FEI, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_d_hook_17k(A, cv, t, u):
    ground(A, GROUND)
    n = min(170, int(clamp(u / (1.6 * P)) * 170) + 1)
    for i in range(n):
        x = 100 + (i % 34) * 26; y = GROUND - 10 - (i // 34) * 30
        A.d['du'].rectangle((x - 10, y - 20, x + 10, y), fill=255)

def art_d_hook_none(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='du')
    ground(A, GROUND)
    for k in range(int(clamp(u / (1.6 * P)) * 6)):
        person(A, 160 + k * 150, GROUND, 130, dir=1, robe=False, hat='knot', ph=t * 4 + k, arm=40, layer='mid')
    di(A, 540, GROUND, 240, dir=1, arm=40)

def art_d_hook_blood(A, cv, t, u):
    A.d['mid'].rectangle((240, 860, 840, GROUND), fill=190)
    bars(A, 260, 820, 880, GROUND, n=10)
    p = ease_out(u / (1.6 * P))
    A.d['wash'].rectangle((460, 1100, 460 + 160 * p, 1200), fill=255)
    A.d['red'].line((480, 1120, 480 + 120 * p, 1120), fill=255, width=4)
    A.d['red'].line((480, 1150, 480 + 100 * p, 1150), fill=255, width=4)
    ground(A, GROUND)

def art_d_hook_tang(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='fei')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    di(A, 360, GROUND, 230, dir=1, kneel=True, bow=30, arm=100)

# ================================================================ 第一回 明法出身
def art_d_birth(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='太原', layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('并州太原', 46), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('官宦世家', SERIF, 48, FEI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_d_reading(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='du')
    sitter(A, 320, GROUND, 160, dir=1, bow=25)
    for k in range(3):
        person(A, lerp(1100, 700 + k * 80, ease_out(u / (2 * P))), GROUND, 160, dir=-1, robe=False, hat='helmet', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('传说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('正与圣贤对话 何暇与俗吏语', SERIF, 42, FEI, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.5)

def art_d_mingjing(A, cv, t, u):
    for r in range(3):
        for c2 in range(6):
            x = 200 + c2 * 140; y = 960 + r * 120
            A.d['mid'].rectangle((x - 50, y, x + 50, y + 90), fill=220)
            A.d['ink'].rectangle((x - 50, y, x + 50, y + 90), outline=255, width=4)
    ground(A, GROUND)
    di(A, 860, GROUND, 200, dir=-1, arm=40)
    A.flush(cv)
    stamp(cv, seal('明经及第', 46), 540, 880, t, t - u + P)

def art_d_yanliben(A, cv, t, u):
    ground(A, GROUND)
    person(A, 720, GROUND, 230, dir=-1, robe=True, hat='none', arm=lerp(30, 120, ease_out(u / P)), layer='ink')
    di(A, 360, GROUND, 220, dir=1, arm=40)
    scroll(A, 560, 1000, 200, 100, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('阎立本', 50), 860, 880, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('沧海遗珠', SERIF, 52, FEI, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 1.5 * P, 0.5)

def art_d_parents(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 320), (x + 200, GROUND)], fill=200)
    for k in range(5):
        x = lerp(900, 300, (t * 0.06 + k * 0.2) % 1); y = 820 + (k % 3) * 40
        for j in range(3):
            A.d['wash'].ellipse((x + j * 40 - 50, y - 24, x + j * 40 + 50, y + 24), fill=255)
    ground(A, GROUND)
    di(A, 760, GROUND, 230, dir=-1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    type_in(cv, text_img('吾亲所居 在此云下', SERIF, 48, DU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + P, 0.5)
    stamp(cv, seal('望云思亲', 44), 260, 1060, t, t - u + 0.4, rot=-5)

def art_d_substitute(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='none', arm=-8, layer='mid')
    person(A, 860, GROUND, 140, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mid')
    di(A, 360, GROUND, 230, dir=1, arm=lerp(40, 120, ease_out(u / P)))
    A.flush(cv)
    paste(cv, text_img('同僚母老 代其出使远方', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_quanshancai(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fei')
    ground(A, GROUND)
    person(A, 740, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(30, 150, ease_out(u / 0.5)), layer='ink')
    di(A, 330, GROUND, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4)))
    A.d['grass'].line((540, GROUND - 10, 560, GROUND - 200), fill=255, width=10)
    A.flush(cv)
    stamp(cv, seal('误砍昭陵柏', 40, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('高宗欲杀之 · 他据法力争', SERIF, 44, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第二回 神断
def scene_yinian(cv, t, c, k):
    """8-beat custom scene: 一年断案 — the backlog of cases at 大理寺; each beat a column of files is cleared; the counter
    reaches 一万七千人; not one appeal."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    palace(A, 540, 1060, 680, layer='du')
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='fei')
    di(A, 540, GROUND - 60, 160, dir=1, kneel=True, bow=10, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6)))
    cols = 8
    cleared = int(clamp(ph / 7) * cols)
    for i in range(cols):
        h = 0 if i < cleared else 10
        files(A, 110 + i * 70 if i < 4 else 760 + (i - 4) * 70, GROUND, h, s=30)
    A.flush(cv)
    n = int(lerp(0, 17000, clamp(ph / 7)))
    fx = Art()
    chars_in(cv, fx, '一年断案', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=61)
    fx.flush(cv)
    paste(cv, text_img(f'{n} 人', SERIF, 52, FEI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('无一冤诉者' if ph >= 6 else '大理丞 · 积压陈案', SERIF, 46, ZHU if ph >= 6 else DU, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, 1)

def art_d_shiyushi(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    di(A, 330, GROUND, 230, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 760, GROUND, 220, dir=-1, robe=True, hat='none', bow=lerp(0, 40, ease_out((u - P) / 0.6)), arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('侍御史', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('弹劾权臣 不避权贵', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_temples(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        x = 140 + k * 110
        q = ease_out((u - k * 0.15 * P) / 0.6)
        A.d['mid'].rectangle((x - 40, GROUND - 120 * (1 - q), x + 40, GROUND), fill=220)
        A.d['ink'].polygon([(x - 50, GROUND - 120 * (1 - q)), (x + 50, GROUND - 120 * (1 - q)), (x, GROUND - 170 * (1 - q))], fill=255)
    A.flush(cv)
    stamp(cv, seal('江南', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('焚毁淫祠一千七百所', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_ningzhou(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    di(A, 540, GROUND, 220, dir=1, arm=60)
    for k in range(6):
        person(A, 140 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 130, dir=1 if k < 3 else -1, robe=False, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('宁州', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('百姓为他立德政碑', SERIF, 46, DU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_yuzhou(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 20)
    for i in range(n):
        person(A, 980 - (i % 10) * 80, GROUND - (i // 10) * 40, 90, dir=-1, robe=False, hat='knot', ph=t * 4 + i, arm=20, layer='mid')
    di(A, 160, GROUND, 220, dir=1, arm=lerp(40, 120, ease_out(u / P)))
    A.flush(cv)
    stamp(cv, seal('豫州', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('为六七百受牵连者求情', SERIF, 44, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_zhanglin(A, cv, t, u):
    tent(A, 760, GROUND, 360, 280, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=False, hat='helmet', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    di(A, 330, GROUND, 230, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3 + 1)))
    A.flush(cv)
    stamp(cv, seal('张光辅', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('当面斥责乱兵 被贬复州', SERIF, 44, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第三回 入相下狱
def art_d_xiang(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fei')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)))
    di(A, 360, GROUND, 230, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('同平章事', 44), 260, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('武则天拜他为相', SERIF, 46, FEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_slander_q(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    di(A, 360, GROUND, 230, dir=1, arm=40)
    A.flush(cv)
    type_in(cv, text_img('卿欲知谮卿者乎', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('臣不愿知', SERIF, 52, FEI, 'Black', bleed=False, spacing=8), W / 2, 840, t, t - u + 1.8 * P, 0.5)

def art_d_arrest(A, cv, t, u):
    ground(A, GROUND)
    di(A, 540, GROUND, 230, dir=1, arm=-8)
    for k, sx in enumerate((-1, 1)):
        x = lerp(540 + sx * 500, 540 + sx * 160, ease_out(u / (1.5 * P)))
        person(A, x, GROUND, 220, dir=-sx, robe=False, hat='helmet', arm=lerp(20, 100, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('来俊臣', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('诬以谋反', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_confess(A, cv, t, u):
    A.d['mid'].rectangle((200, 860, 880, GROUND), fill=180)
    bars(A, 220, 860, 880, GROUND, n=11)
    di(A, 540, GROUND, 200, dir=1, kneel=True, bow=20, arm=-8)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('大周革命 万物惟新', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('反是实', SERIF, 52, FEI, 'Black', bleed=False, spacing=8), W / 2, 840, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('先认罪 免酷刑', 34, INK), 860, 1060, t, t - u + 2 * P, rot=6)

def art_d_bloodletter(A, cv, t, u):
    """6-beat set piece: 血书 — in the cell he tears his quilt, writes in blood, sews it into his cotton coat, and asks
    the guard to take it home to change for summer."""
    ph = u / P
    A.d['mid'].rectangle((200, 860, 880, GROUND), fill=180)
    bars(A, 220, 860, 880, GROUND, n=11)
    ground(A, GROUND)
    if ph < 3:
        sitter(A, 420, GROUND, 190, dir=1, bow=30)
        p = ease_out(ph / 2.5)
        A.d['wash'].rectangle((500, GROUND - 120, 640, GROUND - 20), fill=255)
        for j in range(int(p * 5)):
            A.d['red'].line((520, GROUND - 100 + j * 16, 620, GROUND - 100 + j * 16), fill=255, width=3)
        lamp(A, 720, GROUND, 40, t, glow=0.4)
    else:
        di(A, 420, GROUND, 190, dir=1, arm=lerp(40, 100, ease_out((ph - 3) / 0.5)))
        person(A, lerp(700, 1100, ease_out((ph - 4) / 1.5)), GROUND, 190, dir=1 if ph > 4 else -1, robe=False, hat='helmet', load=ph > 3.6, ph=t * 5 if ph > 4 else None, arm=160 if ph > 3.6 else 40, layer='ink')
    A.flush(cv)
    lab = '裂帛书冤 · 藏于棉衣' if ph < 3 else '天热 请家人除去棉絮'
    paste(cv, text_img(lab, SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_d_freed(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fei')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 120, ease_out(u / 0.6)))
    di(A, 360, GROUND, 220, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    type_in(cv, text_img('不承反 已死于鞭笞矣', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('贬彭泽', 50, INK), 860, 1060, t, t - u + 2 * P, rot=6)

def art_d_pengze(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=4, speed=1)
    ground(A, 1260, x0=60, x1=W - 60)
    for k in range(10):
        x = 100 + k * 92
        A.d['grass'].rectangle((x, 1260 - 30 - 10 * (k % 3), x + 70, 1260), fill=200)
    di(A, 540, 1260, 210, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('彭泽令', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('大旱 奏请免租', SERIF, 46, DU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 再相
def art_d_weizhou(A, cv, t, u):
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=220)
    city_wall(A, 160, 920, 1100, gate_x=540, label='魏州', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        person(A, lerp(-100, 160 + k * 120, ease_out((u - k * 0.1) / (2 * P))), GROUND, 110, dir=1, robe=False, hat='knot', load=True, ph=t * 5 + k, arm=160, layer='mid')
    A.flush(cv)
    stamp(cv, seal('契丹入寇', 44, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('放百姓归田 · 敌闻而退', SERIF, 44, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_again(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fei')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)))
    di(A, 360, GROUND, 230, dir=1, kneel=True, bow=30, arm=100, old=0.6)
    A.flush(cv)
    stamp(cv, seal('再度拜相', 46), 260, 880, t, t - u + P, rot=-5)

def art_d_guolao(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    wuzetian(A, 740, GROUND - 30, 230, dir=-1, arm=lerp(20, 120, ease_out(u / P)))
    di(A, 360, GROUND, 230, dir=1, arm=40, old=0.7)
    A.flush(cv)
    ink_in(cv, text_img('国老', BRUSH, 130, FEI), W / 2, 900, t, t - u + P, dur=0.3, settle=1.2)
    paste(cv, text_img('武则天不呼其名', SERIF, 44, DU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - 1.5 * P) / 0.3))

def art_d_heir(A, cv, t, u):
    """8-beat set piece: 劝立庐陵王 — the empress dreams of a parrot with broken wings; he says the wings are her two sons;
    the exiled 李显 is quietly brought back behind a curtain."""
    ph = u / P
    palace(A, 540, 1140, 600, layer='fei')
    ground(A, GROUND)
    wuzetian(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    di(A, 340, GROUND, 230, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)), old=0.7)
    if ph < 3:
        bx, by = 540, 900
        A.d['grass'].ellipse((bx - 40, by - 30, bx + 40, by + 30), fill=255)
        A.d['grass'].polygon([(bx - 40, by), (bx - 100, by + 20 + 30 * ph), (bx - 30, by + 20)], fill=255)
        A.d['grass'].polygon([(bx + 40, by), (bx + 100, by + 20 + 30 * ph), (bx + 30, by + 20)], fill=255)
    if ph >= 5:
        A.d['du'].rectangle((860, 900, 980, GROUND), fill=150)
        person(A, 920, GROUND, 200, dir=-1, robe=True, hat='crown', arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('梦鹦鹉折翼', 40, INK), 260, 880, t, t - u + 0.4, rot=-5)
    if 2.5 <= ph < 5:
        type_in(cv, text_img('二翼 陛下二子也', SERIF, 48, FEI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 2.5 * P, 0.5)
    if ph >= 5:
        paste(cv, text_img('庐陵王李显 秘密回京', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 5) / 0.3))

def art_d_peaches(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        x = 160 + k * 150
        A.d['ink'].line((x, GROUND, x + 6, GROUND - 260), fill=255, width=10)
        for j in range(6):
            A.d['apricot'].ellipse((x - 50 + (j * 23) % 100, GROUND - 320 + (j * 17) % 80, x - 30 + (j * 23) % 100, GROUND - 300 + (j * 17) % 80), fill=230)
    di(A, 540, GROUND, 200, dir=1, arm=60, old=0.7)
    A.flush(cv)
    type_in(cv, text_img('天下桃李 悉在公门', SERIF, 50, FEI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_d_zhangjianzhi(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    wuzetian(A, 760, GROUND - 30, 230, dir=-1, arm=40)
    di(A, 320, GROUND, 230, dir=1, arm=lerp(40, 120, ease_out(u / P)), old=0.8)
    person(A, 520, GROUND, 210, dir=1, robe=True, hat='none', arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('张柬之', 50), 520, 880, t, t - u + P)
    paste(cv, text_img('年近八十 · 他仍力荐', SERIF, 46, DU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_d_horse(A, cv, t, u):
    ground(A, GROUND)
    di(A, 460, GROUND, 230, dir=1, kneel=u < 1.5 * P, bow=40 if u < 1.5 * P else 0, arm=100 if u < 1.5 * P else 40, old=0.8)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='crown', female=True, arm=lerp(40, 140, ease_out(u / P)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('朝见免拜 · 宫中不宿直', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 斗转星移
def art_d_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    di(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('病逝 · 年七十一', SERIF, 50, FEI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_empty(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    wuzetian(A, 540, GROUND - 30, 230, dir=1, bow=lerp(0, 30, ease_out(u / P)), arm=lerp(20, 140, ease_out(u / P)))
    A.flush(cv)
    type_in(cv, text_img('朝堂空矣', SERIF, 56, FEI, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + P, 0.5)

def art_d_shenlong(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    city_wall(A, 160, 920, 1100, gate_x=540, label='玄武门', layer='mid', open_=ease_out((u - P) / P))
    ground(A, GROUND)
    for k in range(6):
        person(A, lerp(-100, 480, ease_out((u - k * 0.1) / (2 * P))) - k * 60, GROUND, 140, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('神龙政变', 46), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('他荐的人 恢复了唐朝', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_d_stars(A, cv, t, u):
    """6-beat: 斗转星移 — the night sky rotates; 唐 replaces 周."""
    ph = u / P
    a = ease_out(ph / 4) * math.pi
    r = random.Random(3)
    for k in range(60):
        x0, y0 = r.uniform(-400, 400), r.uniform(-300, 300)
        x = 540 + x0 * math.cos(a) - y0 * math.sin(a); y = 960 + x0 * math.sin(a) + y0 * math.cos(a)
        if 80 < x < 1000 and 640 < y < 1300:
            A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    ink_in(cv, text_img('周', BRUSH, 160, (150, 140, 130)), 380, 960, t, t - u + 0.3, dur=0.3)
    if ph >= 3:
        ink_in(cv, text_img('唐', BRUSH, 180, FEI), 700, 960, t, t - u + 3 * P, dur=0.3, settle=1.3)
    stamp(cv, seal('斗转星移', 44), 860, 1220, t, t - u + 4 * P, rot=6)

def art_d_rehab(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='fei')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 220, dir=1, robe=True, hat='crown', arm=lerp(20, 100, ease_out(u / P)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('梁国公', 54), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('追赠司空 · 封梁国公', SERIF, 46, FEI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_detective(A, cv, t, u):
    ground(A, GROUND)
    di(A, 540, GROUND, 260, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    for k in range(3):
        files(A, 200 + k * 340 if k != 1 else 860, GROUND, 4, s=40)
    A.flush(cv)
    paste(cv, text_img('狄公案 · 后世公案小说', SERIF, 46, DU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('高罗佩', 44, INK), 860, 1040, t, t - u + P, rot=6)

def art_d_legacy(A, cv, t, u):
    files(A, 880, 1440, 3, s=80)

def art_d_title(A, cv, t, u):
    files(A, 820, 1460, 8, s=110)
    di(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '明法出身'), 48: ('第二回', '神断'), 80: ('第三回', '入相下狱'),
            112: ('第四回', '国老'), 144: ('第五回', '斗转星移')}

CARDS = [
    C(0, 2, 'works', 'num', num='一万七千人', line='一年断完无人喊冤', art=art_d_hook_17k),
    C(2, 4, 'court', 'num', num='不愿知', line='谁在背后说他坏话', art=art_d_hook_none),
    C(4, 6, 'night', 'num', num='一件棉衣', line='藏着血书', art=art_d_hook_blood),
    C(6, 8, 'empire', 'num', num='一个人', line='把江山还给了唐', art=art_d_hook_tang),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=630, main='生于太原', sub='字怀英', art=art_d_birth),
    C(22, 26, 'works', 'card', year=642, main='读书不辍', sub='吏来问案 他埋头读书', art=art_d_reading),
    C(26, 30, 'empire', 'card', year=655, main='明经及第', sub='入仕途', note='登科之年 一说', art=art_d_mingjing),
    C(30, 34, 'court', 'card', year=660, main='沧海遗珠', sub='被人诬告 · 反得阎立本赏识', art=art_d_yanliben),
    C(34, 38, 'life', 'card', year=665, main='望云思亲', sub='并州法曹参军', art=art_d_parents),
    C(38, 42, 'fate', 'card', year=668, main='代人远使', sub='孝悌之名', art=art_d_substitute),
    C(42, 48, 'night', 'card', year=676, main='据法力争', sub='将军误砍昭陵柏树', note='高宗乃止', art=art_d_quanshancai),
    C(48, 50, 'works', 'chapter'),
    C(50, 58, 'works', 'yinian', year=677),
    C(58, 62, 'court', 'card', year=679, main='侍御史', sub='监察百官', art=art_d_shiyushi),
    C(62, 66, 'life', 'card', year=686, main='宁州刺史', sub='抚和戎夏', art=art_d_ningzhou),
    C(66, 70, 'works', 'card', year=688, main='焚毁淫祠', sub='江南巡抚使', art=art_d_temples),
    C(70, 74, 'fate', 'card', year=688, main='豫州求情', sub='越王之乱后', art=art_d_yuzhou),
    C(74, 80, 'war', 'card', year=688, main='斥责将帅', sub='乱兵扰民', art=art_d_zhanglin),
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'empire', 'card', year=691, main='初次拜相', sub='地官侍郎', art=art_d_xiang),
    C(86, 90, 'court', 'card', year=691, main='不愿知', sub='武则天问他', art=art_d_slander_q),
    C(90, 94, 'night', 'card', year=692, main='被诬谋反', sub='酷吏当道', art=art_d_arrest),
    C(94, 98, 'fate', 'card', year=692, main='先行认罪', sub='保命之计', art=art_d_confess),
    C(98, 104, 'night', 'card', year=692, main='血书', sub='狱中自救', art=art_d_bloodletter),
    C(104, 108, 'empire', 'card', year=692, main='面见女皇', sub='死里逃生', art=art_d_freed),
    C(108, 112, 'life', 'card', year=693, main='彭泽县令', sub='贬官 仍为民请命', art=art_d_pengze),
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'war', 'card', year=697, main='魏州退敌', sub='不战而退契丹', art=art_d_weizhou),
    C(118, 122, 'empire', 'card', year=697, main='再度拜相', sub='鸾台侍郎', art=art_d_again),
    C(122, 126, 'court', 'card', year=698, main='国老', sub='女皇倚重', art=art_d_guolao),
    C(126, 134, 'fate', 'card', year=698, main='劝立庐陵', sub='一场关于继承人的劝说', note='母子姑侄孰亲', art=art_d_heir),
    C(134, 138, 'works', 'card', year=699, main='桃李满门', sub='举荐贤才数十人', art=art_d_peaches),
    C(138, 142, 'court', 'card', year=700, main='力荐张柬之', sub='一个关键的人', art=art_d_zhangjianzhi),
    C(142, 144, 'life', 'card', year=700, main='免拜', sub='殊荣', art=art_d_horse),
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'death', 'card', year=700, main='病逝', sub='洛阳', art=art_d_death),
    C(150, 154, 'night', 'card', year=700, main='朝堂空矣', sub='武则天痛哭', art=art_d_empty),
    C(154, 158, 'war', 'card', year=705, main='神龙政变', sub='张柬之等拥李显复位', art=art_d_shenlong),
    C(158, 162, 'fate', 'card', year=705, main='斗转星移', sub='周归于唐', art=art_d_stars),
    C(162, 166, 'court', 'card', year=706, main='追封', sub='唐中宗', art=art_d_rehab),
    C(166, 170, 'end', 'card', year=1949, main='狄公案', sub='神探形象 风靡海外', art=art_d_detective),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾壹', col=FEI, acc=DU, born=630, died=700,
    hook_q='他是神探吗 · 真实的狄仁杰做了什么？',
    name_line='狄仁杰 · 字怀英', name='狄仁杰', seal='梁公', title_art=art_d_title,
    q1='一代名相？', q2='女皇宠臣？',
    end_art=art_d_legacy, end_big='斗转星移', end_seal='梁公',
    end_l1='他不是小说里的神探', end_l2='却在女皇身边保住了大唐的根',
    end_brush='天下桃李 悉在公门', end_ask='你心中的狄仁杰是什么样？评论区聊聊', next='魏征'),
    scenes=dict(chapter=scene_chapter, yinian=scene_yinian))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
