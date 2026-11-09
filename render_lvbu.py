"""千古人物志 · 第柒拾陆集 · 吕布 (?–199)
Look: 赤兔红 + 方天银, 画戟 corner borders (a crossed halberd blade), 并州 steppe hills behind.
Chapter card: 主公旗 — each chapter a new lord's banner rises behind the red horse (丁 董 王 袁 刘), and the old one falls;
in the last chapter the halberd itself falls.
Set pieces: custom 8-beat scene 'yuanmen' (辕门射戟), 6-beat 诛董卓, 6-beat 常山破张燕 (赤兔), 6-beat 濮阳, 6-beat 水淹下邳, 6-beat 白门楼.
Birth year unknown, so no ages are shown (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_zuozongtang as Zz     # engine + helpers (previous episode)
import render_long as L
import render_gufeng as G
import render_story as S
import render_full as F
import epkit
from render_gufeng import (W, H, FPS, bt, INK, ZHU, ZHE, BRUSH, SERIF, WILD, font, clamp, lerp, ease_out, ease_expo,
                           cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import (Art, person, horse, carriage, palace, flames, waves, boat, crow, arrow, flag, ground,
                          walk_x, ellipse_pts, GROUND)
from render_full import chars_in, type_in, beat_fx
from render_long import C, rider, city_wall, note_in, stage, DIM, P
from render_wangyangming import desk, scroll, lamp, sitter
from render_quyuan import river
from render_simayi import emperor
from render_sunwu import army, banner
from render_songtaizu import tent
from render_huatuo import caocao
from render_guanyu import liubei

F.RIPPLE = False
CHITU = (178, 60, 44)               # 赤兔红
FANGTIAN = (118, 128, 142)          # 方天银
S.LAYERS.append(('chitu', CHITU, 0.9, 1.0))
S.LAYERS.append(('fangtian', FANGTIAN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='吕', life='并', court='汉', night='谋', war='战', empire='侯', works='戟', fate='叛', death='缢', end='将')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (FANGTIAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (CHITU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # steppe grass
    _d.line([(40 + i * 30, 1456 + _k * 14 + 3 * math.sin(i * 0.8 + _k)) for i in range(35)], fill=(120, 120, 90, 46 - _k * 10), width=3)
for _x, _s in ((110, 1), (970, -1)):  # a planted halberd at each margin
    _d.line((_x, 1446, _x, 1270), fill=FANGTIAN + (80,), width=5)
    _d.polygon([(_x - 4, 1270), (_x + 4, 1270), (_x, 1236)], fill=FANGTIAN + (80,))
    _d.chord((_x + _s * 2 - 22, 1278, _x + _s * 2 + 22, 1318), 270 if _s > 0 else 90, 90 if _s > 0 else 270, fill=FANGTIAN + (80,))
    _d.line((_x, 1300, _x - _s * 14, 1320), fill=CHITU + (90,), width=4)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (112, 64, 50), 'fate': (96, 96, 100)}
def draw_background(t, theme):
    """并州: low steppe hills and planted halberds."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 192, 186), (166, 160, 152), MTN_COL.get(theme, (120, 110, 104))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """画戟: a crescent halberd blade in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CHITU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=CHITU + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 26, cy + 26, cx + 26, cy - 26), fill=FANGTIAN + (230,), width=4)
        d.polygon([(cx + 22, cy - 22), (cx + 30, cy - 30), (cx + 34, cy - 14)], fill=FANGTIAN + (230,))
        d.chord((cx - 6, cy - 22, cx + 22, cy + 6), 300, 120, fill=FANGTIAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def halberd(A, x, y, L_, ang, layer='fangtian'):
    """方天画戟 from (x,y) at angle ang (radians, 0 = pointing up)."""
    tx, ty = x + L_ * math.sin(ang), y - L_ * math.cos(ang)
    A.d['ink'].line((x, y, tx, ty), fill=255, width=max(3, int(L_ * 0.018)))
    nx, ny = math.cos(ang), math.sin(ang)
    s = 0.12 * L_
    A.d[layer].polygon([(tx - nx * 0.06 * s, ty - ny * 0.06 * s), (tx + nx * 0.06 * s, ty + ny * 0.06 * s),
                        (tx + 0.5 * s * math.sin(ang), ty - 0.5 * s * math.cos(ang))], fill=255)
    for side in (-1, 1):
        cx, cy = tx + side * nx * 0.35 * s - 0.3 * s * math.sin(ang), ty + side * ny * 0.35 * s + 0.3 * s * math.cos(ang)
        A.d[layer].ellipse((cx - 0.22 * s, cy - 0.22 * s, cx + 0.22 * s, cy + 0.22 * s), fill=255)
    A.d['chitu'].ellipse((tx - 0.9 * s * math.sin(ang) - 6, ty + 0.9 * s * math.cos(ang) - 6, tx - 0.9 * s * math.sin(ang) + 6, ty + 0.9 * s * math.cos(ang) + 6), fill=255)

def lv(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, ji=True, bound=False, **kw):
    """吕布: a tall general — helmet with two long pheasant plumes, a red cloak, the 方天画戟."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=False, hat='helmet', layer=layer, kneel=kneel, bow=bow, **kw)
    if up:
        for k in (-1, 1):
            A.d['chitu'].line([(x + k * 0.03 * h, y - 1.05 * h), (x - dir * 0.12 * h + k * 0.04 * h, y - 1.3 * h), (x - dir * 0.3 * h + k * 0.05 * h, y - 1.36 * h)], fill=255, width=max(2, int(0.014 * h)))
        A.d['chitu'].polygon([(x - dir * 0.04 * h, y - 0.8 * h), (x - dir * 0.2 * h, y - 0.2 * h), (x - dir * 0.06 * h, y - 0.24 * h)], fill=230)
        if ji and not bound:
            halberd(A, x + dir * 0.24 * h, y, 1.25 * h, dir * 0.05)
    if bound:
        A.d['ink'].line((x - 0.12 * h, y - 0.6 * h, x + 0.12 * h, y - 0.5 * h), fill=255, width=max(3, int(0.02 * h)))
        A.d['ink'].line((x - 0.12 * h, y - 0.45 * h, x + 0.12 * h, y - 0.38 * h), fill=255, width=max(3, int(0.02 * h)))
    return hand

def chitu(A, x, y, s, dir=1, ph=0.0, moving=True, rider_=True, ji=True):
    horse(A, x, y, s, dir=dir, ph=ph, layer='chitu', moving=moving)
    if rider_:
        person(A, x - dir * 0.05 * s, y - 0.62 * s, 0.75 * s, dir=dir, robe=False, hat='helmet', arm=60, layer='ink')
        for k in (-1, 1):
            A.d['chitu'].line([(x - dir * 0.05 * s + k * 3, y - 1.4 * s), (x - dir * 0.3 * s, y - 1.6 * s)], fill=255, width=3)
        if ji:
            halberd(A, x + dir * 0.3 * s, y - 0.6 * s, 1.1 * s, dir * 0.6)

def lord_banner(A, x, base, h, t, fallen=0.0, layer='mid'):
    banner(A, x, base, h, t, layer=layer, fallen=fallen)

# ================================================================ chapter card
LORDS = ['丁', '董', '王', '袁', '刘']
CH = {16: 0, 48: 1, 80: 2, 112: 3, 144: 4}
def art_lord_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    i = CH.get(kb, 1)
    q = ease_out(u / (1.2 * P))
    A.d['mid'].rectangle((240, 1200, 840, 1214), fill=200)
    if i > 0:
        lord_banner(A, 360, 1200, 260, t, fallen=clamp(q * 1.2), layer='mid')
    lord_banner(A, 720, 1200, 260 * clamp(q * 1.5), t, layer='chitu')
    if kb == 144 and q > 0.6:
        halberd(A, 540, 1200, 300, lerp(0.2, 1.4, clamp((q - 0.6) / 0.4)))
    else:
        chitu(A, 540, 1200, 140, dir=1, ph=t * 6, rider_=False)
    A.flush(cv)
    if i > 0:
        paste(cv, text_img(LORDS[i - 1], SERIF, 46, INK, 'Black', bleed=False), 410, 1000, 1, clamp(1 - q * 1.5))
    paste(cv, text_img(LORDS[i], SERIF, 46, INK, 'Black', bleed=False), 770, 1000, 1, clamp((q - 0.4) / 0.3))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_lord_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CHITU, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_b_hook_horse(A, cv, t, u):
    ground(A, GROUND)
    chitu(A, lerp(200, 600, ease_out(u / (1.2 * P))), GROUND, 200, dir=1, ph=t * 7)

def art_b_hook_arrow(A, cv, t, u):
    ground(A, GROUND)
    halberd(A, 860, GROUND, 320, 0)
    q = clamp(u / (1.0 * P))
    ax = lerp(160, 860, q)
    A.d['ink'].line((ax - 80, GROUND - 300, ax, GROUND - 300), fill=255, width=4)
    A.d['ink'].polygon([(ax, GROUND - 306), (ax + 18, GROUND - 300), (ax, GROUND - 294)], fill=255)

def art_b_hook_lords(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((340, 740)):
        lord_banner(A, x, GROUND, 360, t, fallen=clamp((u - i * 0.5 * P) / (0.6 * P)), layer='mid')
    lv(A, 540, GROUND, 240, dir=1, arm=60)

def art_b_hook_rope(A, cv, t, u):
    ground(A, GROUND)
    lv(A, 540, GROUND, 260, dir=1, bound=True, arm=-8)

# ================================================================ 第一回 飞将
def art_b_birth(A, cv, t, u):
    for k in range(4):
        x = 140 + k * 260
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 200), (x + 240, GROUND)], fill=150)
    ground(A, GROUND)
    chitu(A, lerp(-100, 700, (t * 0.08) % 1), GROUND, 120, dir=1, ph=t * 6, ji=False)
    A.flush(cv)
    paste(cv, text_img('五原郡九原人 · 以骁武仕于并州', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('九原', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '生年史书无载', t, t - u + P)

def art_b_archery(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].ellipse((840, GROUND - 260, 920, GROUND - 180), outline=255, width=8)
    A.d['ink'].line((880, GROUND - 180, 880, GROUND), fill=255, width=5)
    lv(A, 300, GROUND, 200, dir=1, ji=False, arm=lerp(60, 90, 0.5 + 0.5 * math.sin(t * 3)))
    q = (t * 0.8) % 1
    A.d['ink'].line((lerp(400, 860, q), GROUND - 220, lerp(400, 860, q) + 60, GROUND - 220), fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img('便弓马 膂力过人 · 号为飞将', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_dingyuan(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='mid', open_=1.0)
    person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(-8, 70, ease_out(u / 0.6)), layer='fangtian')
    lv(A, 360, GROUND, 200, dir=1, bow=15, ji=False, arm=60)
    A.flush(cv)
    paste(cv, text_img('并州刺史丁原 · 以为主簿 大见亲待', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_dongzhuo_in(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(5):
        rider(A, lerp(-100, 700, ease_out(u / (2.5 * P))) - j * 120, GROUND, 110, dir=1, ph=t * 6 + j, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('董卓率凉州兵入洛阳 · 诱吕布杀丁原', SERIF, 44, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '以赤兔马相赠一事 出自演义', t, t - u + P)

def art_b_kill_ding(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='mid', open_=1.0)
    q = clamp((u - P) / (0.6 * P))
    person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', fall=lerp(0, 88, q), arm=-8, layer='fangtian')
    lv(A, 420, GROUND, 210, dir=1, arm=lerp(40, 140, q), ji=False, sword=lerp(40, 140, q))
    A.flush(cv)
    paste(cv, text_img('斩丁原首级 · 献于董卓', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('背主', 56, ZHU), 860, 1020, t, t - u + 2 * P, rot=6)

def art_b_father(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND, 230, dir=-1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    A.d['ink'].ellipse((690, GROUND - 170, 750, GROUND - 100), fill=255)
    lv(A, 400, GROUND, 200, dir=1, bow=20, arm=60)
    A.flush(cv)
    paste(cv, text_img('董卓以为骑都尉 · 誓为父子', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_yangren(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(700, 200, ease_out(u / (3 * P))), GROUND, 5, dir=-1, layer='chitu', t=t, march=True, h=100)
    army(A, lerp(-300, 0, ease_out(u / (3 * P))), GROUND, 4, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('与胡轸击孙坚于阳人 · 将帅不和 大败而还', SERIF, 42, CHITU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '三英战吕布出自演义 史无此事', t, t - u + P)

def art_b_xiqian(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (1.5 * P)) * 0.4, layer='mid')
    flames(A, 540, 1200, 600, 220, t, n=6, seed=191, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('董卓焚洛阳 · 挟天子西迁长安', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 诛卓
def art_b_shouji(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 230, dir=-1, robe=True, hat='knot', arm=lerp(-8, 150, clamp(u / (0.5 * P))), layer='ink')
    A.d['ink'].ellipse((730, GROUND - 170, 790, GROUND - 100), fill=255)
    q = clamp((u - 0.5 * P) / (0.6 * P))
    kx, ky = lerp(700, 380, q), lerp(GROUND - 260, GROUND - 230, q)
    A.d['fangtian'].line((kx - 30, ky, kx + 30, ky), fill=255, width=6)
    lv(A, 360, GROUND, 200, dir=1, bow=lerp(0, -20, q), ji=False, arm=lerp(-8, 150, q))
    A.flush(cv)
    paste(cv, text_img('董卓小有不满 · 拔手戟掷之', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '吕布拳捷避之 由是阴怨董卓', t, t - u + P)

def art_b_maid(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    A.d['mid'].rectangle((300, GROUND - 300, 780, GROUND), fill=150)
    lamp(A, 540, GROUND, 40, t, glow=0.6)
    person(A, 620, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='chitu')
    lv(A, 460, GROUND, 200, dir=1, ji=False, arm=-8)
    A.flush(cv)
    paste(cv, text_img('与董卓侍婢私通 · 恐事发 心不自安', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '貂蝉一角由此附会 出自演义', t, t - u + P)

def art_b_wangyun(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='fangtian')
    lv(A, 320, GROUND, 160, dir=1, kneel=True, arm=60, ji=False)
    lamp(A, 540, GROUND - 74, 30, t, glow=0.7)
    A.flush(cv)
    lab = '奈如父子何' if u < 2 * P else '君自姓吕 本非骨肉'
    paste(cv, text_img(lab, SERIF, 48, ZHU if u >= 2 * P else CHITU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    note_in(cv, '司徒王允密谋诛卓 以此劝之', t, t - u + P)

def art_b_zhuzhuo(A, cv, t, u):
    """6-beat set piece: 诛董卓 — at the palace gate the guards strike; 董卓 falls from his carriage and cries for 吕布;
    吕布 answers: 有诏讨贼臣 — and runs him through."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    if ph < 2:
        carriage(A, lerp(-100, 520, ease_out(ph / 2)), GROUND, 110, dir=1, wheel=t * 6, ph=t * 8, layer='ink')
        lv(A, 820, GROUND, 210, dir=-1, arm=40)
        lab, col = '董卓入宫 · 车至北掖门', CHITU
    elif ph < 4:
        carriage(A, 520, GROUND, 110, dir=1, wheel=0, ph=0, moving=False, layer='ink')
        person(A, 600, GROUND, 200, dir=1, robe=True, hat='knot', fall=lerp(0, 30, clamp((ph - 2) / 0.5)), arm=150, layer='ink')
        lv(A, 820, GROUND, 210, dir=-1, arm=60)
        lab, col = '卓大呼 吕布何在', CHITU
    else:
        person(A, 600, GROUND, 200, dir=1, robe=True, hat='knot', fall=lerp(30, 88, clamp((ph - 4) / 0.5)), arm=-8, layer='ink')
        lv(A, 760, GROUND, 210, dir=-1, arm=140, ji=False)
        halberd(A, 760, GROUND - 120, 300, -1.3)
        lab, col = '有诏讨贼臣', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('第二个义父 也死在他手里', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_b_wenhou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='fangtian')
    ground(A, GROUND)
    lv(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('拜奋威将军 封温侯 · 与王允共秉朝政', SERIF, 44, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('温侯', 56), 860, 1020, t, t - u + P, rot=6)

def art_b_lijue(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=clamp((u - 1.5 * P) / P))
    ground(A, GROUND)
    army(A, lerp(-300, 200, ease_out(u / (3 * P))), GROUND, 6, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('董卓旧部李傕 郭汜攻破长安', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_wuguan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 320), (x + 160, GROUND)], fill=160)
    ground(A, GROUND)
    for j in range(4):
        chitu(A, lerp(900, -200, ((t * 0.08 + j / 4) % 1)), GROUND, 100, dir=-1, ph=t * 6 + j, ji=j == 0)
    A.flush(cv)
    paste(cv, text_img('吕布出武关东走 · 王允遇害', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 流离
def art_b_yuanshu(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南阳', layer='mid', open_=0.0)
    ground(A, GROUND)
    lv(A, 400, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('投袁术 · 袁术恶其反复 拒而不受', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_changshan(A, cv, t, u):
    """6-beat set piece: 常山 — with 袁绍 he attacks 张燕's mountain army; on 赤兔 he charges the ranks again and again;
    时人语曰 人中有吕布 马中有赤兔."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 360), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    army(A, 620, GROUND, 5, dir=-1, layer='ink', t=t, march=False, h=100)
    x = lerp(-100, 700, ((ph / 2.0) % 1)) if ph < 4 else lerp(-100, 300, clamp((ph - 4) / 1))
    chitu(A, x, GROUND, 150, dir=1, ph=t * 8)
    A.flush(cv)
    lab = '随袁绍攻张燕于常山' if ph < 1.5 else ('乘赤兔 驰城飞堑' if ph < 3.5 else '一日冲阵三四次 皆斩首而出')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.5 else CHITU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('赤兔', 56), 860, 1020, t, t - u + 1.5 * P, rot=6)
    note_in(cv, '赤兔之名见于正史 非演义虚构', t, t - u + 2 * P)

def art_b_escape(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    tent(A, 400, GROUND, 320, 240, layer='mid', open_=0.4)
    for j in range(4):
        person(A, 640 + j * 80, GROUND, 150, dir=-1, robe=False, hat='helmet', sword=60, arm=60, layer='ink')
    chitu(A, lerp(300, -200, clamp(u / (3 * P))), GROUND, 110, dir=-1, ph=t * 7, ji=False)
    A.flush(cv)
    paste(cv, text_img('袁绍忌之 遣甲士夜刺 · 吕布潜逃', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '令人在帐中鼓筝 甲士以为布仍在', t, t - u + P)

def art_b_puyang(A, cv, t, u):
    """6-beat set piece: 濮阳 — 陈宫 and 张邈 betray 曹操 and invite 吕布 into 兖州; at 濮阳 the city burns; 曹操 falls from his horse and burns his hand."""
    ph = u / P
    city_wall(A, 220, 860, 1060, gate_x=540, label='濮阳', layer='mid', open_=1.0)
    ground(A, GROUND)
    if ph < 2:
        person(A, 300, GROUND, 190, dir=1, robe=True, hat='knot', bow=15, arm=90, layer='fangtian')
        lv(A, 700, GROUND, 210, dir=-1, arm=60)
        lab, col = '陈宫 张邈叛曹 · 迎吕布入兖州', CHITU
    else:
        flames(A, 540, 1060, 600, 200 * clamp((ph - 2) / 1), t, n=6, seed=194, smoke=True)
        q = clamp((ph - 3) / 1)
        caocao(A, 540, GROUND, 190, dir=-1, fall=lerp(0, 50, q), arm=150)
        horse(A, 700, GROUND, 120, dir=1, ph=t * 8, layer='mid')
        lab, col = ('城中火起' if ph < 3 else '曹操坠马 烧伤左手'), ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '曹操几乎丧命 相持百余日', t, t - u + 2 * P)

def art_b_dingtao(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(200, 700, ease_out(u / (3 * P))), GROUND, 5, dir=1, layer='ink', t=t, march=True, h=100)
    chitu(A, lerp(500, 1100, ease_out(u / (3 * P))), GROUND, 110, dir=1, ph=t * 7)
    A.flush(cv)
    paste(cv, text_img('与曹操战于钜野 大败 · 东走徐州', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_liubei(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='徐州', layer='mid', open_=1.0)
    ground(A, GROUND)
    liubei(A, 640, GROUND, 200, dir=-1, arm=lerp(-8, 70, ease_out(u / 0.6)))
    lv(A, 400, GROUND, 210, dir=1, bow=10, arm=60)
    A.flush(cv)
    paste(cv, text_img('东奔徐州 · 投靠刘备', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 辕门
def art_b_xiapi(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    city_wall(A, 160, 920, 1080, gate_x=540, label='下邳', layer='mid', open_=clamp((u - P) / P))
    ground(A, GROUND)
    for j in range(5):
        lv(A, lerp(-100, 480, ease_out(u / (3 * P))) - j * 90, GROUND, 130, dir=1, arm=40, ji=j == 0)
    A.flush(cv)
    paste(cv, text_img('趁刘备与袁术相持 · 袭取下邳', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('背主', 56, ZHU), 860, 1020, t, t - u + 2 * P, rot=6)

def scene_yuanmen(cv, t, c, k):
    """8-beat custom scene: 辕门射戟 — 袁术's general 纪灵 marches on 刘备; 吕布 plants his halberd at the camp gate:
    if I hit its small blade from 150 paces, both sides go home. One arrow — hit."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    tent(A, 200, GROUND, 260, 200, layer='mid', open_=1.0)
    A.d['ink'].line((80, GROUND, 80, GROUND - 260), fill=255, width=8); A.d['ink'].line((320, GROUND, 320, GROUND - 260), fill=255, width=8)
    A.d['ink'].line((60, GROUND - 260, 340, GROUND - 260), fill=255, width=10)
    halberd(A, 880, GROUND, 300, 0)
    if ph < 3:
        liubei(A, 520, GROUND, 170, dir=1, arm=-8)
        person(A, 680, GROUND, 180, dir=-1, robe=False, hat='helmet', arm=40, layer='ink')
        lv(A, 400, GROUND, 210, dir=1, arm=lerp(-8, 120, clamp((ph - 1) / 0.6)))
        lab, col = ('纪灵率三万人攻刘备' if ph < 1.5 else '吕布于辕门立戟'), CHITU
    elif ph < 6:
        lv(A, 400, GROUND, 210, dir=1, ji=False, arm=lerp(60, 90, clamp((ph - 3) / 0.6)))
        A.d['ink'].arc((420, GROUND - 300, 500, GROUND - 160), 270, 90, fill=255, width=5)
        if ph >= 4.5:
            q = clamp((ph - 4.5) / 0.6)
            ax = lerp(470, 860, q)
            A.d['ink'].line((ax - 70, GROUND - 260, ax, GROUND - 260), fill=255, width=4)
        lab, col = ('射中戟上小支 两家罢兵' if ph < 4.5 else '一箭'), ZHU
    else:
        liubei(A, 520, GROUND, 170, dir=1, arm=60)
        person(A, 680, GROUND, 180, dir=-1, robe=False, hat='helmet', bow=20, arm=-8, layer='ink')
        lv(A, 400, GROUND, 210, dir=1, arm=60)
        A.flush(cv)
        lab, col = '正中小支 · 诸将皆惊 将军天威也', CHITU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '辕门射戟', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=76)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '史载射戟之事 距一百五十步', t, s0 + 2 * P)

def art_b_zuojiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='fangtian')
    ground(A, GROUND)
    lv(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('曹操拉拢 · 朝廷拜为左将军', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_chendeng(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    for j, x in enumerate((340, 740)):
        person(A, x, GROUND, 160, dir=1 if j == 0 else -1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2 + j)), layer='fangtian')
    lamp(A, 540, GROUND - 74, 30, t, glow=0.6)
    A.flush(cv)
    paste(cv, text_img('陈珪 陈登父子 · 暗中归心曹操', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_xiaopei(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='小沛', layer='mid', open_=1.0)
    ground(A, GROUND)
    army(A, lerp(-300, 100, ease_out(u / (3 * P))), GROUND, 5, dir=1, layer='chitu', t=t, march=True, h=100)
    liubei(A, lerp(540, 1100, ease_out(u / (3 * P))), GROUND, 160, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    paste(cv, text_img('再攻刘备于小沛 · 刘备投奔曹操', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_flood(A, cv, t, u):
    """6-beat set piece: 水淹下邳 — 曹操 besieges 下邳 for three months, then breaks the 泗 and 沂 rivers into the city."""
    ph = u / P
    city_wall(A, 220, 860, 1000, gate_x=540, label='下邳', layer='mid')
    if ph < 2:
        army(A, -200, GROUND, 4, dir=1, layer='ink', t=t, march=False, h=90)
        lab = '曹操围下邳 · 三月不下'
    else:
        q = clamp((ph - 2) / 2)
        A.d['ocean'].rectangle((60, lerp(GROUND, 1080, q), W - 60, GROUND + 40), fill=200)
        waves(A, lerp(GROUND, 1080, q), t, rows=3, amp=6)
        lab = '决泗水 沂水灌城'
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else CHITU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '吕布屡欲出降 为陈宫所阻', t, t - u + 3 * P)

# ================================================================ 第五回 白门楼
def art_b_baimen(A, cv, t, u):
    """6-beat set piece: 白门楼 — his generals bind 陈宫 and surrender; he comes down and is tied; 缚太急;
    刘备: 明公不见布之事丁建阳及董太师乎; 吕布: 是儿最叵信者."""
    ph = u / P
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=200)
    A.d['ink'].polygon([(180, 900), (900, 900), (820, 820), (260, 820)], fill=255)
    ground(A, GROUND)
    if ph < 1.5:
        lv(A, 540, GROUND, 220, dir=1, bound=True, arm=-8)
        lab, col = '部将宋宪 魏续缚陈宫出降 · 吕布下楼被缚', CHITU
    elif ph < 3:
        lv(A, 400, GROUND, 220, dir=1, bound=True, arm=-8)
        caocao(A, 720, GROUND, 200, dir=-1, arm=-8)
        lab, col = '缚太急 小缓之', CHITU
    elif ph < 4.5:
        lv(A, 300, GROUND, 220, dir=1, bound=True, arm=-8)
        caocao(A, 620, GROUND, 200, dir=-1, arm=-8)
        liubei(A, 820, GROUND, 190, dir=-1, arm=lerp(-8, 80, clamp((ph - 3) / 0.6)))
        lab, col = '明公不见布之事丁建阳及董太师乎', ZHU
    else:
        lv(A, 300, GROUND, 220, dir=1, bound=True, arm=-8, bow=-10)
        caocao(A, 620, GROUND, 200, dir=-1, arm=-8)
        liubei(A, 820, GROUND, 190, dir=-1, arm=-8)
        lab, col = '是儿最叵信者', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42 if ph < 1.5 else 44, col, 'Black', bleed=False, spacing=2), W / 2, 700, 1, 1)
    stamp(cv, seal('白门楼', 50), 860, 1020, t, t - u + 0.4, rot=6)

def art_b_death(A, cv, t, u):
    A.d['mid'].rectangle((200, 900, 880, GROUND), fill=200)
    A.d['ink'].polygon([(180, 900), (900, 900), (820, 820), (260, 820)], fill=255)
    ground(A, GROUND)
    halberd(A, 540, GROUND, 320, lerp(0, 1.5, clamp(u / (1.5 * P))))
    A.flush(cv)
    paste(cv, text_img('吕布被缢杀 · 陈宫 高顺同死', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '高顺至死不降', t, t - u + P)

def art_b_saying(A, cv, t, u):
    ground(A, GROUND)
    chitu(A, 540, GROUND, 220, dir=1, ph=0, moving=False, rider_=False)
    A.flush(cv)
    paste(cv, text_img('人中有吕布 马中有赤兔', SERIF, 50, CHITU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '时人之语 见曹瞒传', t, t - u + P)

def art_b_novel(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((200, 960, 880, 1000), fill=200)
    A.d['ink'].rectangle((200, 1000, 220, GROUND), fill=255); A.d['ink'].rectangle((860, 1000, 880, GROUND), fill=255)
    A.d['dune'].rectangle((200, GROUND - 60, 880, GROUND), fill=230)
    lv(A, 540, GROUND - 60, 220, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('三国演义 · 塑造天下无双的吕奉先', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_jianu(A, cv, t, u):
    ground(A, GROUND)
    for i, x in enumerate((300, 540, 780)):
        lord_banner(A, x, GROUND, 320, t, fallen=0.6 if i < 2 else 0.0, layer='mid')
    A.flush(cv)
    paste(cv, text_img('三姓家奴之骂出自演义', SERIF, 46, CHITU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '史书中 他先后杀了丁原与董卓', t, t - u + P)

def art_b_verdict(A, cv, t, u):
    ground(A, GROUND)
    halberd(A, 540, GROUND, 420, 0)
    A.flush(cv)
    paste(cv, text_img('有虓虎之勇 而无英奇之略', SERIF, 48, CHITU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '陈寿三国志之评', t, t - u + P)

def art_b_legacy(A, cv, t, u):
    halberd(A, 860, 1440, 160, 0.1)

def art_b_title(A, cv, t, u):
    chitu(A, 820, 1440, 180, dir=-1, ph=0, moving=False, rider_=False)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    lv(A, 380, 1460, 640, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '飞将'), 48: ('第二回', '诛卓'), 80: ('第三回', '流离'),
            112: ('第四回', '辕门'), 144: ('第五回', '白门楼')}

CARDS = [
    C(0, 2, 'war', 'num', num='人中吕布', line='马中赤兔', art=art_b_hook_horse),
    C(2, 4, 'works', 'num', num='一支箭', line='射中百五十步外的戟', art=art_b_hook_arrow),
    C(4, 6, 'fate', 'num', num='两个主公', line='都死在他手里', art=art_b_hook_lords),
    C(6, 8, 'death', 'num', num='一句话', line='送他上了刑场', art=art_b_hook_rope),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 飞将
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=184, main='边地骁将', sub='五原九原', art=art_b_birth),
    C(22, 26, 'works', 'card', year=186, main='号为飞将', sub='弓马过人', art=art_b_archery),
    C(26, 30, 'court', 'card', year=188, main='丁原主簿', sub='大见亲待', art=art_b_dingyuan),
    C(30, 34, 'night', 'card', year=189, main='董卓入京', sub='诱反丁原', art=art_b_dongzhuo_in),
    C(34, 38, 'death', 'card', year=189, main='斩丁原', sub='第一次背主', art=art_b_kill_ding),
    C(38, 42, 'empire', 'card', year=189, main='誓为父子', sub='骑都尉', art=art_b_father),
    C(42, 46, 'war', 'card', year=191, main='阳人之战', sub='败于孙坚', art=art_b_yangren),
    C(46, 48, 'fate', 'card', year=191, main='西迁长安', sub='火烧洛阳', art=art_b_xiqian),
    # ---- 第二回 诛卓
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'war', 'card', year=191, main='手戟', sub='阴怨董卓', art=art_b_shouji),
    C(54, 58, 'night', 'card', year=191, main='私通侍婢', sub='心不自安', art=art_b_maid),
    C(58, 62, 'court', 'card', year=192, main='王允之谋', sub='本非骨肉', art=art_b_wangyun),
    C(62, 68, 'death', 'card', year=192, main='诛杀董卓', sub='有诏讨贼', art=art_b_zhuzhuo),
    C(68, 72, 'empire', 'card', year=192, main='封温侯', sub='共秉朝政', art=art_b_wenhou),
    C(72, 76, 'war', 'card', year=192, main='长安失守', sub='董卓旧部', art=art_b_lijue),
    C(76, 80, 'fate', 'card', year=192, main='出走武关', sub='王允遇害', art=art_b_wuguan),
    # ---- 第三回 流离
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'fate', 'card', year=193, main='袁术拒之', sub='恶其反复', art=art_b_yuanshu),
    C(86, 92, 'war', 'card', year=193, main='常山之战', sub='赤兔', art=art_b_changshan),
    C(92, 96, 'night', 'card', year=193, main='袁绍欲杀', sub='夜遁', art=art_b_escape),
    C(96, 102, 'death', 'card', year=194, main='濮阳之战', sub='曹操几死', art=art_b_puyang),
    C(102, 106, 'war', 'card', year=195, main='钜野之败', sub='东走', art=art_b_dingtao),
    C(106, 112, 'court', 'card', year=195, main='投奔刘备', sub='徐州', art=art_b_liubei),
    # ---- 第四回 辕门
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'war', 'card', year=196, main='袭取下邳', sub='第三次背主', art=art_b_xiapi),
    C(118, 126, 'works', 'yuanmen', year=196),
    C(126, 130, 'empire', 'card', year=197, main='左将军', sub='曹操拉拢', art=art_b_zuojiang),
    C(130, 134, 'night', 'card', year=197, main='陈登之谋', sub='暗附曹操', art=art_b_chendeng),
    C(134, 138, 'war', 'card', year=198, main='再攻小沛', sub='刘备投曹', art=art_b_xiaopei),
    C(138, 144, 'death', 'card', year=198, main='水淹下邳', sub='围城三月', art=art_b_flood),
    # ---- 第五回 白门楼
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'death', 'card', year=199, main='白门楼', sub='最叵信者', art=art_b_baimen),
    C(152, 156, 'death', 'card', year=199, main='吕布之死', sub='缢杀', art=art_b_death),
    C(156, 160, 'works', 'card', year=199, main='人中吕布', sub='马中赤兔', art=art_b_saying),
    C(160, 164, 'court', 'card', year=1522, main='三国演义', sub='天下无双', art=art_b_novel),
    C(164, 168, 'fate', 'card', year=1522, main='三姓家奴', sub='演义之骂', art=art_b_jianu),
    C(168, 170, 'end', 'card', year=1522, main='勇而无谋', sub='陈寿之评', art=art_b_verdict),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾陆', col=CHITU, acc=FANGTIAN, born=184, died=199, age0=183, no_age=True,
    born_lab='生年不详', died_lab='199年', years_txt='生年不详 — 公元199',
    hook_q='他是三国第一猛将 · 为什么人人都不敢信他？',
    name_line='吕布 · 字奉先', name='吕布', seal='飞将', title_art=art_b_title,
    q1='天下无双？', q2='反复小人？',
    end_art=art_b_legacy, end_big='人中吕布', end_seal='飞将',
    end_l1='他的武艺天下无双', end_l2='他的信用一文不值',
    end_brush='勇而无谋', end_ask='吕布最大的错 是哪一次背叛？评论区聊聊', next='刘备'),
    scenes=dict(chapter=scene_chapter, yuanmen=scene_yuanmen))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
