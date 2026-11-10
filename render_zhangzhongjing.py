"""千古人物志 · 第玖拾陆集 · 张仲景 (约150–约219)
Look: 药炉褐 + 青蒿绿, little herb-sprig corners, a Nanyang village and drying racks behind.
Chapter card: 药碾 — a boat-shaped herb grinder; its wheel rolls a little further each chapter and the powder heap grows.
Set pieces: custom 8-beat scene 'shanghan' (宗族二百余口), 6-beat 王粲, 6-beat 勤求古训, 6-beat 娇耳 (labelled legend).
Birth and death years are approximate (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_hanfeizi as Hf        # engine + helpers (previous episode)
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
from render_kongzi import slips, bundle
from render_zhuxi import book

F.RIPPLE = False
YAOLU = (120, 80, 56)               # 药炉褐
QINGHAO = (96, 128, 96)             # 青蒿绿
S.LAYERS.append(('yaolu', YAOLU, 0.9, 1.0))
S.LAYERS.append(('qinghao', QINGHAO, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='医', life='张', court='汉', night='寒', war='疫', empire='圣', works='方', fate='伤', death='殁', end='医')
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
G.THEMES['empire']['sun'] = (QINGHAO, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YAOLU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (70, 900):                # herb-drying racks at the margins
    _d.line((_x, 1420, _x, 1320), fill=YAOLU + (70,), width=4)
    _d.line((_x + 110, 1420, _x + 110, 1320), fill=YAOLU + (70,), width=4)
    for _k in range(3):
        _d.ellipse((_x + 4, 1324 + _k * 30, _x + 106, 1340 + _k * 30), fill=QINGHAO + (50,))
for _k in range(3):
    _d.line((220, 1424 + _k * 12, 860, 1424 + _k * 12), fill=YAOLU + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 32, 36), 'death': (62, 60, 60), 'war': (110, 70, 56), 'fate': (96, 96, 92)}
def draw_background(t, theme):
    """南阳: gentle hills, herb racks at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 196, 188), (164, 166, 152), MTN_COL.get(theme, (110, 120, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """药草: a little sprig of leaves in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YAOLU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YAOLU + (220,), width=3)
        cx, cy = x + sx * 30, y + sy * 30
        d.line((cx, cy, cx + sx * 50, cy + sy * 50), fill=(90, 70, 50, 230), width=3)
        for k in range(3):
            px, py = cx + sx * (12 + 14 * k), cy + sy * (12 + 14 * k)
            d.ellipse((px - 10 + sx * 8, py - 5 - sy * 6, px + 10 + sx * 8, py + 5 - sy * 6), fill=QINGHAO + (230,))
            d.ellipse((px - 10 - sx * 8, py - 5 + sy * 6, px + 10 - sx * 8, py + 5 + sy * 6), fill=QINGHAO + (230,))

# ================================================================ primitives
def zhang_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, box=False, **kw):
    """张仲景: an Eastern-Han scholar-physician — soft cap, brown robe, grey beard with age; a medicine box at his back."""
    b = bow + 6 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    if up:
        A.d[layer].chord((x - 0.08 * h, y - 1.08 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        A.d['wash' if old > 0.5 else layer].polygon([(x, y - 0.86 * h), (x + dir * 0.07 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.68 * h)], fill=255)
    top = y - (0.48 if kneel else 0.76) * h
    A.d['yaolu'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    if box and up:
        bx0, bx1 = sorted((x - dir * 0.24 * h, x - dir * 0.08 * h))
        A.d['yaolu'].rectangle((bx0, y - 0.72 * h, bx1, y - 0.42 * h), fill=255)
    return hand

def patient(A, x, base, s, layer='mid'):
    A.d['ink'].rectangle((x - s, base - 0.25 * s, x + s, base - 0.18 * s), fill=255)
    for lx in (x - 0.9 * s, x + 0.9 * s):
        A.d['ink'].rectangle((lx - 6, base - 0.18 * s, lx + 6, base), fill=255)
    person(A, x - 0.1 * s, base - 0.25 * s, 1.1 * s, dir=1, fall=-88, arm=-8, layer=layer)

def nian(A, cx, base, s, pos, heap=0.0):
    """药碾: a boat-shaped trough on a low stand; a round wheel with a handle at `pos` (-1..1); a powder heap of `heap`."""
    A.d['yaolu'].polygon([(cx - s, base - 0.32 * s), (cx + s, base - 0.32 * s), (cx + 0.7 * s, base - 0.1 * s), (cx - 0.7 * s, base - 0.1 * s)], fill=255)
    A.d['ink'].rectangle((cx - 0.5 * s, base - 0.1 * s, cx + 0.5 * s, base), fill=255)
    wx = cx + pos * 0.6 * s
    A.d['ink'].ellipse((wx - 0.22 * s, base - 0.66 * s, wx + 0.22 * s, base - 0.22 * s), outline=255, width=max(4, int(0.04 * s)))
    A.d['ink'].line((wx - 0.45 * s, base - 0.44 * s, wx + 0.45 * s, base - 0.44 * s), fill=255, width=max(4, int(0.04 * s)))
    if heap > 0:
        A.d['qinghao'].chord((cx + 0.9 * s, base - 0.25 * s * heap - 4, cx + 1.5 * s, base + 0.25 * s * heap), 180, 360, fill=230)

def jiaoer(A, x, y, s, layer='wash'):
    """娇耳: a crescent dumpling shaped like an ear."""
    A.d[layer].chord((x - s, y - 0.7 * s, x + s, y + 0.7 * s), 180, 360, fill=255)
    A.d['ink'].arc((x - s, y - 0.7 * s, x + s, y + 0.7 * s), 180, 360, fill=160, width=3)
    for k in range(5):
        a = math.pi + (k + 1) * math.pi / 6
        A.d['ink'].line((x + 0.8 * s * math.cos(a), y + 0.56 * s * math.sin(a), x + s * math.cos(a), y + 0.7 * s * math.sin(a)), fill=160, width=2)

def pot(A, x, base, s, t, fire=1.0):
    A.d['ink'].chord((x - s, base - 1.1 * s, x + s, base - 0.1 * s), 0, 180, fill=255)
    A.d['ink'].rectangle((x - 1.05 * s, base - 0.66 * s, x + 1.05 * s, base - 0.56 * s), fill=255)
    if fire > 0:
        flames(A, x, base, 1.4 * s, 0.4 * s * fire, t, n=2, seed=int(x), smoke=False)
    for k in range(3):
        f = (t * 0.5 + k / 3) % 1
        A.d['wash'].ellipse((x - 20 + 20 * math.sin(t + k), base - 0.66 * s - 160 * f - 18, x + 20 + 20 * math.sin(t + k), base - 0.66 * s - 160 * f + 18), fill=int(150 * (1 - f)))

# ================================================================ chapter card
CH = {16: (-1, -0.6, 0.0), 48: (-0.6, -0.2, 0.2), 80: (-0.2, 0.2, 0.45), 112: (0.2, 0.6, 0.7), 144: (0.6, 1.0, 1.0)}
def art_nian_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b, hp = CH.get(kb, (-0.6, -0.2, 0.2))
    q = ease_out(u / (1.4 * P))
    nian(A, 470, 1200, 280, lerp(a, b, q) + 0.08 * math.sin(t * 4) * (1 - q), heap=hp)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_nian_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YAOLU, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_z_hook_clan(A, cv, t, u):
    n = 200
    gone = int(clamp(u / (1.4 * P)) * 133)
    for i in range(n):
        x = 160 + (i % 20) * 40; y = 960 + (i // 20) * 40
        A.d['ink' if i >= gone else 'mid'].ellipse((x - 12, y - 12, x + 12, y + 12), fill=255 if i >= gone else 80)

def art_z_hook_book(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(8, int(u / (0.15 * P)) + 1)):
        bundle(A, 220 + k * 90, GROUND, 80)

def art_z_hook_dumpling(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].ellipse((340, GROUND - 120, 740, GROUND - 20), fill=255)
    for k in range(5):
        jiaoer(A, 400 + k * 70, GROUND - 120 - 10 * (k % 2), 46)

def art_z_hook_hall(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    zhang_(A, 640, GROUND, 190, dir=-1, kneel=True, arm=100)
    person(A, 420, GROUND, 170, dir=1, robe=False, hat='knot', kneel=True, arm=100, layer='mid')

# ================================================================ 第一回 学医
def art_z_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 180), (x + 240, GROUND)], fill=130)
    A.d['wash'].rectangle((420, GROUND - 140, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 140), (680, GROUND - 140), (540, GROUND - 200)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('南阳郡涅阳人 名机 字仲景', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '正史无传 生卒年皆为约数', t, t - u + P)

def art_z_teacher(A, cv, t, u):
    ground(A, GROUND)
    person(A, 760, GROUND, 210, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    zhang_(A, 360, GROUND, 170, dir=1, kneel=True, arm=-8)
    pot(A, 560, GROUND, 60, t)
    A.flush(cv)
    paste(cv, text_img('拜同郡名医张伯祖为师', SERIF, 48, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_heyong(A, cv, t, u):
    ground(A, GROUND)
    person(A, 720, GROUND, 200, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    zhang_(A, 380, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('何颙说他 后将为良医', SERIF, 48, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见何颙别传 或有附会', t, t - u + P)

def art_z_practice(A, cv, t, u):
    ground(A, GROUND)
    patient(A, 640, GROUND, 160)
    zhang_(A, 360, GROUND, 190, dir=1, kneel=True, arm=80)
    A.flush(cv)
    paste(cv, text_img('学成后 在乡里行医', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_chaos(A, cv, t, u):
    palace(A, 540, 1300, 300, collapse=clamp(u / (3 * P)) * 0.3, layer='mid')
    flames(A, 540, 1220, 500, 160, t, n=4, seed=184, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('东汉末年 战乱四起', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '黄巾起义 军阀混战', t, t - u + P)

# ================================================================ 第二回 伤寒
def art_z_wangcan(A, cv, t, u):
    """6-beat set piece: 王粲 — he tells the young poet he is ill and should take a decoction or lose his eyebrows at forty; twenty years later it comes true."""
    ph = u / P
    ground(A, GROUND)
    if ph < 3:
        zhang_(A, 360, GROUND, 190, dir=1, arm=60)
        person(A, 680, GROUND, 180, dir=-1, robe=True, hat='knot', arm=-8, layer='mid')
        lab, col = '他对二十岁的王粲说 你有病', YAOLU
    else:
        A.d['ink'].rectangle((300, GROUND - 74, 780, GROUND - 60), fill=255)
        person(A, 540, GROUND - 74, 180, dir=1, fall=-88, arm=-8, layer='mid')
        lab, col = '四十当眉落 半年而死 后果然', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '据皇甫谧记载 未必尽实', t, t - u + P)

def art_z_plague(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        mound = 180 + k * 220
        A.d['mid'].chord((mound - 70, GROUND - 50, mound + 70, GROUND + 50), 180, 360, fill=220)
    for k in range(8):
        x = (k * 130 + t * 30) % 1000 + 40
        A.d['wash'].ellipse((x - 50, 1000 + 20 * math.sin(t + k), x + 50, 1060 + 20 * math.sin(t + k)), fill=70)
    A.flush(cv)
    paste(cv, text_img('建安年间 疫病流行', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def scene_shanghan(cv, t, c, k):
    """8-beat custom scene: 伤寒 — his clan of more than two hundred; within ten years two thirds die, seven in ten of them of 伤寒."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    gone = int(clamp((ph - 1.5) / 4.5) * 134)
    shang = int(gone * 0.7)
    for i in range(200):
        x = 160 + (i % 20) * 40; y = 900 + (i // 20) * 42
        if i < gone:
            A.d['red' if i < shang else 'mid'].ellipse((x - 12, y - 12, x + 12, y + 12), fill=110)
        else:
            A.d['ink'].ellipse((x - 12, y - 12, x + 12, y + 12), fill=255)
    zhang_(A, 900, GROUND, 160, dir=-1, kneel=ph > 6, bow=30 if ph > 6 else 0, arm=-8)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '伤寒', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=96)
    fx.flush(cv)
    if ph < 1.5:
        lab, col = '宗族素多 向余二百', YAOLU
    elif ph < 6:
        lab, col = f'不到十年 死去{cn_num(gone)}人' if gone < 134 else '死者三分有二', ZHU
    else:
        lab, col = '伤寒十居其七', ZHU
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 575, 1, 1)
    note_in(cv, '出自他本人所写的伤寒杂病论序', t, s0 + 2 * P)

def art_z_resolve(A, cv, t, u):
    ground(A, GROUND)
    zhang_(A, 540, GROUND, 220, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('感往昔之沦丧 伤横夭之莫救', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_z_preface(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('上以疗君亲之疾\n下以救贫贱之厄', SERIF, 42, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('学医的初心', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第三回 著书
def art_z_qiuxun(A, cv, t, u):
    """6-beat set piece: 勤求古训 博采众方 — he reads the old classics, collects prescriptions from everyone, and tests them; the slips pile up into sixteen scrolls."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        desk(A, 560, GROUND, 420, layer='mid')
        zhang_(A, 300, GROUND, 180, dir=1, kneel=True, arm=100)
        slips(A, 460, GROUND - 74, 10, 70, layer='zhujian', tied=False)
        lab = '勤求古训 素问 九卷 难经'
    elif ph < 4:
        person(A, 700, GROUND, 170, dir=-1, robe=False, hat='knot', arm=60, layer='mid')
        zhang_(A, 380, GROUND, 190, dir=1, arm=60)
        pot(A, 540, GROUND, 50, t)
        lab = '博采众方 一试再试'
    else:
        for k in range(min(16, int((ph - 4) * 8) + 1)):
            bundle(A, 160 + (k % 8) * 110, GROUND - (k // 8) * 80, 80)
        lab = '撰成伤寒杂病论 十六卷'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '成书约在建安中期', t, t - u + 4 * P)

def art_z_liujing(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i, w in enumerate(['太阳', '阳明', '少阳', '太阴', '少阴', '厥阴']):
        a = clamp((u - i * 0.25 * P) / 0.3)
        paste(cv, text_img(w, SERIF, 52, YAOLU if i < 3 else INK, 'Black', bleed=False, spacing=6), 330 + (i % 3) * 210, 1040 + (i // 3) * 140, 1, a)
    paste(cv, text_img('六经辨证 按病程分阶段施治', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_z_lifa(A, cv, t, u):
    ground(A, GROUND)
    pot(A, 540, GROUND, 90, t)
    A.flush(cv)
    paste(cv, text_img('理 法 方 药 一线贯通', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '奠定中医辨证论治的基础', t, t - u + P)

def art_z_guizhi(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 260 + k * 140
        A.d['qinghao' if k % 2 else 'yaolu'].ellipse((x - 40, GROUND - 60, x + 40, GROUND - 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('桂枝 芍药 甘草 生姜 大枣', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('桂枝汤 后世称为群方之冠', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_z_fangzu(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(10, int(u / (0.25 * P)) + 1)):
        A.d['wash'].rectangle((160 + k * 80, GROUND - 200, 220 + k * 80, GROUND), fill=255)
        A.d['ink'].rectangle((160 + k * 80, GROUND - 200, 220 + k * 80, GROUND), outline=180, width=2)
    A.flush(cv)
    paste(cv, text_img('许多方剂沿用至今', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '后世称其书为方书之祖', t, t - u + P)

def art_z_changsha(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    zhang_(A, 640, GROUND, 190, dir=-1, kneel=True, arm=100)
    for k in range(4):
        person(A, 180 + k * 80, GROUND, 150, dir=1, robe=False, hat='knot', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('相传任长沙太守 坐堂行医', SERIF, 48, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '长沙太守与坐堂之说多为后世附会', t, t - u + P)

# ================================================================ 第四回 娇耳
def art_z_jiaoer(A, cv, t, u):
    """6-beat set piece: 娇耳 — the legend: in a hard winter he sees the poor with frost-bitten ears; he boils mutton and warming herbs, wraps them in dough shaped like ears and hands them out."""
    ph = u / P
    for k in range(30):
        x = (k * 37 + t * 50) % 1000 + 40; y = (k * 91 + t * 120) % 600 + 800
        A.d['wash'].ellipse((x - 4, y - 4, x + 4, y + 4), fill=230)
    ground(A, GROUND)
    if ph < 2:
        for k in range(4):
            person(A, 300 + k * 150, GROUND, 160, dir=1, robe=False, hat='knot', bow=20, arm=-8, layer='mid')
        lab = '寒冬 穷人的耳朵冻烂了'
    elif ph < 4:
        pot(A, 540, GROUND, 110, t)
        zhang_(A, 300, GROUND, 190, dir=1, arm=80)
        lab = '羊肉与驱寒药材同煮 包成耳朵形状'
    else:
        A.d['ink'].ellipse((340, GROUND - 120, 740, GROUND - 20), fill=255)
        for k in range(5):
            jiaoer(A, 400 + k * 70, GROUND - 120 - 10 * (k % 2), 46)
        lab = '取名祛寒娇耳汤'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '民间传说 饺子起源于此说并无史证', t, t - u + 0.5 * P)

def art_z_dongzhi(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].ellipse((340, GROUND - 120, 740, GROUND - 20), fill=255)
    for k in range(5):
        jiaoer(A, 400 + k * 70, GROUND - 120 - 10 * (k % 2), 46)
    A.flush(cv)
    paste(cv, text_img('冬至不端饺子碗 冻掉耳朵没人管', SERIF, 44, YAOLU, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '河南民谚', t, t - u + P)

def art_z_sizhen(A, cv, t, u):
    ground(A, GROUND)
    zhang_(A, 380, GROUND, 190, dir=1, kneel=True, arm=80)
    person(A, 640, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, arm=80, layer='mid')
    A.flush(cv)
    paste(cv, text_img('望 闻 问 切 四诊合参', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_old(A, cv, t, u):
    ground(A, GROUND)
    zhang_(A, lerp(900, 360, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 2, old=0.8, box=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('晚年仍四处行医', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '年份约略', t, t - u + P)

def art_z_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    zhang_(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('张仲景去世 葬于南阳', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年不详 约在建安末年', t, t - u + P)

def art_z_lost(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        bundle(A, 330 + k * 260, GROUND, 80)
    flames(A, 540, GROUND, 600, 120, t, n=4, seed=96, smoke=True)
    A.flush(cv)
    paste(cv, text_img('战乱中 原书散佚', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 医圣
def art_z_shuhe(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    person(A, 300, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    slips(A, 460, GROUND - 74, 10, 70, layer='zhujian', tied=False)
    A.flush(cv)
    paste(cv, text_img('西晋王叔和搜集整理', SERIF, 50, YAOLU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_z_song(A, cv, t, u):
    ground(A, GROUND)
    book(A, 420, GROUND, 160, 240, layer='yaolu')
    book(A, 660, GROUND, 160, 240, layer='qinghao')
    A.flush(cv)
    paste(cv, text_img('宋代校定为伤寒论 金匮要略', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_z_yisheng(A, cv, t, u):
    ground(A, GROUND)
    zhang_(A, 540, GROUND, 300, dir=1, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('后世尊为医圣', SERIF, 54, YAOLU, 'Black', bleed=False, spacing=10), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '医圣之称明清以后才普遍', t, t - u + P)

def art_z_japan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    boat(A, lerp(200, 800, ease_out(u / (3 * P))), 1260, 100, t)
    A.flush(cv)
    paste(cv, text_img('东传日本 朝鲜 至今仍在使用', SERIF, 46, YAOLU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '日本汉方多用伤寒论方', t, t - u + P)

def art_z_ci(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='qinghao')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('南阳医圣祠', SERIF, 54, YAOLU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('医圣', 56), 860, 1020, t, t - u + P, rot=6)

def art_z_end(A, cv, t, u):
    ground(A, GROUND)
    pot(A, 540, GROUND, 100, t)
    A.flush(cv)
    paste(cv, text_img('下以救贫贱之厄', SERIF, 52, YAOLU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_z_legacy(A, cv, t, u):
    nian(A, 840, 1420, 60, 0.3 * math.sin(t))

def art_z_title(A, cv, t, u):
    pot(A, 820, 1440, 90, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhang_(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '学医'), 48: ('第二回', '伤寒'), 80: ('第三回', '著书'),
            112: ('第四回', '娇耳'), 144: ('第五回', '医圣')}

CARDS = [
    C(0, 2, 'death', 'num', num='二百多口', line='十年死了三分之二', art=art_z_hook_clan),
    C(2, 4, 'works', 'num', num='一部书', line='中医读了一千八百年', art=art_z_hook_book),
    C(4, 6, 'life', 'num', num='一碗饺子', line='相传和他有关', art=art_z_hook_dumpling),
    C(6, 8, 'court', 'num', num='坐堂医生', line='说法相传来自他', art=art_z_hook_hall),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 学医
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=150, main='生于南阳', sub='张机', note='年份约略', art=art_z_birth),
    C(22, 28, 'works', 'card', year=165, main='拜师', sub='张伯祖', note='年份约略', art=art_z_teacher),
    C(28, 34, 'night', 'card', year=170, main='良医之才', sub='名士之评', note='年份约略', art=art_z_heyong),
    C(34, 40, 'life', 'card', year=175, main='行医', sub='乡里', note='年份约略', art=art_z_practice),
    C(40, 48, 'war', 'card', year=184, main='天下大乱', sub='东汉末年', art=art_z_chaos),
    # ---- 第二回 伤寒
    C(48, 50, 'fate', 'chapter'),
    C(50, 56, 'night', 'card', year=197, main='预言王粲', sub='四十眉落', note='年份约略', art=art_z_wangcan),
    C(56, 60, 'war', 'card', year=200, main='建安大疫', sub='疫病流行', note='年份约略', art=art_z_plague),
    C(60, 68, 'death', 'shanghan', year=205),
    C(68, 74, 'fate', 'card', year=205, main='立志', sub='感往昔之沦丧', art=art_z_resolve),
    C(74, 80, 'works', 'card', year=205, main='初心', sub='救贫贱之厄', art=art_z_preface),
    # ---- 第三回 著书
    C(80, 82, 'works', 'chapter'),
    C(82, 88, 'works', 'card', year=206, main='勤求古训', sub='博采众方', note='年份约略', art=art_z_qiuxun),
    C(88, 92, 'night', 'card', year=206, main='六经辨证', sub='分阶段施治', art=art_z_liujing),
    C(92, 96, 'life', 'card', year=206, main='理法方药', sub='一线贯通', art=art_z_lifa),
    C(96, 100, 'empire', 'card', year=206, main='桂枝汤', sub='群方之冠', art=art_z_guizhi),
    C(100, 106, 'court', 'card', year=206, main='方书之祖', sub='沿用至今', art=art_z_fangzu),
    C(106, 112, 'fate', 'card', year=208, main='长沙太守', sub='坐堂之说', note='年份约略', art=art_z_changsha),
    # ---- 第四回 娇耳
    C(112, 114, 'night', 'chapter'),
    C(114, 120, 'life', 'card', year=210, main='娇耳', sub='民间传说', note='年份无考', art=art_z_jiaoer),
    C(120, 124, 'night', 'card', year=210, main='冬至饺子', sub='民谚', art=art_z_dongzhi),
    C(124, 128, 'works', 'card', year=212, main='四诊', sub='望闻问切', art=art_z_sizhen),
    C(128, 134, 'fate', 'card', year=215, main='奔走', sub='晚年行医', art=art_z_old),
    C(134, 140, 'death', 'card', year=219, main='张仲景去世', sub='葬于南阳', art=art_z_death),
    C(140, 144, 'war', 'card', year=219, main='原书散佚', sub='战乱', art=art_z_lost),
    # ---- 第五回 医圣
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=280, main='王叔和', sub='整理编次', note='年份约略', art=art_z_shuhe),
    C(150, 154, 'court', 'card', year=1065, main='伤寒论', sub='宋代校定', art=art_z_song),
    C(154, 158, 'empire', 'card', year=1600, main='医圣', sub='后世尊称', note='年份约略', art=art_z_yisheng),
    C(158, 162, 'life', 'card', year=1700, main='东传', sub='日本 朝鲜', note='年份约略', art=art_z_japan),
    C(162, 166, 'court', 'card', year=1700, main='医圣祠', sub='南阳', art=art_z_ci),
    C(166, 170, 'end', 'card', year=1700, main='救厄', sub='医者初心', art=art_z_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾陆', col=YAOLU, acc=QINGHAO, born=150, died=219, age0=149, no_age=True,
    born_lab='约150年', died_lab='约219年', years_txt='约公元150 — 约219',
    hook_q='家族二百多人死了三分之二 · 他做了什么？',
    name_line='张机 · 字仲景', name='张仲景', seal='医圣', title_art=art_z_title,
    q1='一代医圣？', q2='长沙太守？',
    end_art=art_z_legacy, end_big='伤寒杂病论', end_seal='仲景',
    end_l1='瘟疫夺走了他的亲人', end_l2='他把救命的法子留给了后人',
    end_brush='博采众方', end_ask='冬至你吃饺子吗？评论区聊聊', next='貂蝉'),
    scenes=dict(chapter=scene_chapter, shanghan=scene_shanghan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
