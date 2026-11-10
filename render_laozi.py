"""千古人物志 · 第玖拾叁集 · 老子 (生卒年不详，约春秋末年)
Look: 青牛色 + 紫气, little slip-bundles in the corners, a mountain pass and mist behind.
Chapter card: 八十一章 — rows of bamboo slips that fill up to eighty-one; in the last chapter they roll into one bundle.
Set pieces: custom 8-beat scene 'chuguan' (出函谷关), 6-beat 问礼, 6-beat 上善若水, 6-beat 黄老之治.
Birth and death years are unknown (no_age); every year shown is approximate.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_linjuemin as Lj       # engine + helpers (previous episode)
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
from render_kongzi import kong, slips, bundle
from render_quyuan import river
from render_simayi import emperor

F.RIPPLE = False
QINGNIU = (84, 110, 104)            # 青牛色
ZIQI = (128, 92, 140)               # 紫气
S.LAYERS.append(('qingniu', QINGNIU, 0.9, 1.0))
S.LAYERS.append(('ziqi', ZIQI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='道', life='老', court='周', night='玄', war='兵', empire='德', works='经', fate='关', death='隐', end='道')
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
G.THEMES['empire']['sun'] = (QINGNIU, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZIQI, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(4):                 # drifting mist bands
    _d.ellipse((80 + _k * 200, 1360 + (_k % 2) * 30, 420 + _k * 200, 1420 + (_k % 2) * 30), fill=ZIQI + (26,))
for _x, _s in ((120, 1), (960, -1)):  # cliff edges of a pass at the margins
    _d.polygon([(_x - 60 * _s, 1420), (_x - 60 * _s, 1250), (_x, 1280), (_x + 30 * _s, 1420)], fill=(110, 116, 112, 60))
MTN_COL = {'night': (30, 30, 42), 'death': (62, 60, 64), 'war': (110, 64, 50), 'fate': (96, 94, 104)}
def draw_background(t, theme):
    """函谷: steep hills, a drift of violet mist, cliffs of a pass at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 194, 196), (162, 164, 166), MTN_COL.get(theme, (104, 118, 114))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """竹简: a tied bundle of slips in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINGNIU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINGNIU + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 46
        for k in range(5):
            bx = cx + sx * (k * 9 - 18)
            d.rectangle((bx - 3, cy - 22, bx + 3, cy + 22), fill=(170, 140, 90, 230))
        d.line((cx - 26, cy - 10, cx + 26, cy - 10), fill=ZIQI + (230,), width=3)
        d.line((cx - 26, cy + 10, cx + 26, cy + 10), fill=ZIQI + (230,), width=3)

# ================================================================ primitives
def lao(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, staff=False, **kw):
    """老子: an old man with a bald crown, long white brows and a white beard to the waist; a plain robe; sometimes a staff."""
    b = bow + 6
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', layer=layer, kneel=kneel, bow=b, **kw)
    if kw.get('fall'):
        return hand
    hy = y - (0.6 if kneel else 0.88) * h
    A.d['wash'].polygon([(x + dir * 0.0 * h, hy), (x + dir * 0.09 * h, hy), (x + dir * 0.06 * h, hy + 0.36 * h), (x - dir * 0.02 * h, hy + 0.3 * h)], fill=255)
    A.d['wash'].line((x + dir * 0.02 * h, hy - 0.05 * h, x + dir * 0.1 * h, hy - 0.02 * h), fill=255, width=max(2, int(0.02 * h)))
    A.d['qingniu'].polygon([(x - 0.1 * h, hy + 0.12 * h), (x + 0.1 * h, hy + 0.12 * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=110)
    if staff and not kneel:
        sx = x + dir * 0.22 * h
        A.d['ochre'].line((sx, y, sx + dir * 0.03 * h, y - 1.05 * h), fill=255, width=max(3, int(0.022 * h)))
        A.d['ochre'].ellipse((sx + dir * 0.03 * h - 0.03 * h, y - 1.1 * h, sx + dir * 0.03 * h + 0.03 * h, y - 1.04 * h), fill=255)
    return hand

def ox(A, x, y, s, dir=1, ph=0.0, moving=True, layer='qingniu'):
    """青牛: a heavy ox in side view, curved horns."""
    d = A.d[layer]
    def T(u, v): return (x + dir * u * s, y - v * s)
    bob = 0.02 * math.sin(ph * 2) if moving else 0
    d.polygon([T(*p) for p in ellipse_pts(0.0, 0.5 + bob, 0.42, 0.2)], fill=255)
    d.polygon([T(0.35, 0.62 + bob), T(0.62, 0.56 + bob), T(0.66, 0.4 + bob), T(0.42, 0.38 + bob)], fill=255)
    A.d['ink'].arc((min(T(0.44, 0.78)[0], T(0.62, 0.6)[0]), T(0.44, 0.78)[1], max(T(0.44, 0.78)[0], T(0.62, 0.6)[0]), T(0.62, 0.6)[1]), 180, 330, fill=255, width=max(2, int(0.03 * s)))
    for k, off in enumerate((0, 1.7, 3.1, 4.6)):
        a = 0.3 * math.sin(ph + off) if moving else 0
        hu = -0.3 + 0.55 * (k // 2) + 0.06 * (k % 2)
        d.line([T(hu, 0.36), T(hu + 0.12 * math.sin(a), 0.0)], fill=255, width=max(3, int(0.06 * s)))
    d.line([T(-0.42, 0.55), T(-0.52, 0.3)], fill=255, width=max(2, int(0.02 * s)))

def rider_lao(A, x, y, s, t, dir=1, moving=True):
    ox(A, x, y, s, dir=dir, ph=t * 3, moving=moving)
    lao(A, x - dir * 0.05 * s, y - 0.62 * s, 0.75 * s, dir=dir, kneel=True, arm=-8)

def ziqi(A, x0, x1, y, t, a=1.0):
    for k in range(6):
        cx = lerp(x0, x1, k / 5) + 20 * math.sin(t + k)
        A.d['ziqi'].ellipse((cx - 110, y - 26 + 10 * math.sin(t * 0.7 + k), cx + 110, y + 26 + 10 * math.sin(t * 0.7 + k)), fill=int(120 * a))

def slip_wall(A, cx, cy, n, cols=27, rows=3, w=24, h=150):
    """八十一章: rows of slips, `n` of them written on (darker)."""
    x0 = cx - cols * (w + 4) / 2
    for i in range(cols * rows):
        r, c = i // cols, i % cols
        x = x0 + c * (w + 4); y = cy - rows * (h + 14) / 2 + r * (h + 14)
        A.d['ochre'].rectangle((x, y, x + w, y + h), fill=150 if i >= n else 255)
        if i < n:
            for j in range(5):
                A.d['ink'].line((x + w / 2, y + 12 + j * 26, x + w / 2, y + 26 + j * 26), fill=170, width=3)

# ================================================================ chapter card
CH = {16: (0, 9), 48: (9, 27), 80: (27, 54), 112: (54, 81), 144: (81, 81)}
def art_slip_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (9, 27))
    q = ease_out(u / (1.4 * P))
    if kb == 144 and q > 0.5:
        bundle(A, 540, 1200, 260)
        ziqi(A, 300, 780, 940, t, a=clamp((q - 0.5) / 0.3))
    else:
        slip_wall(A, 540, 1050, int(lerp(a, b, clamp((q - 0.2) / 0.6))), cols=27, rows=3, w=26, h=110)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_slip_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINGNIU, 'Black', bleed=False, spacing=12), W / 2, 1320, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1445, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_d_hook_slips(A, cv, t, u):
    slip_wall(A, 540, 1100, int(clamp(u / (1.4 * P)) * 81), cols=27, rows=3, w=26, h=110)

def art_d_hook_ox(A, cv, t, u):
    ground(A, GROUND)
    rider_lao(A, lerp(300, 900, ease_out(u / (2 * P))), GROUND, 260, t)
    ziqi(A, 200, 880, 1100, t, a=0.6)

def art_d_hook_dragon(A, cv, t, u):
    ground(A, GROUND)
    lao(A, 760, GROUND, 230, dir=-1, arm=-8)
    kong(A, 340, GROUND, 220, dir=1, bow=30, arm=-8)
    for k in range(12):
        f = k / 11
        x = lerp(200, 880, f); y = 960 + 60 * math.sin(f * 6 + t * 2)
        A.d['ziqi'].ellipse((x - 28 + 6 * f, y - 28, x + 28, y + 28), fill=int(80 + 100 * f))

def art_d_hook_water(A, cv, t, u):
    A.d['ink'].ellipse((440, GROUND - 160, 640, GROUND), fill=255)
    A.d['ocean'].rectangle((60, GROUND - 60, W - 60, GROUND + 40), fill=150)
    river(A, GROUND - 56, t, rows=2, amp=4)

# ================================================================ 第一回 守藏
def art_d_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 220), (x + 240, GROUND)], fill=140)
    A.d['wash'].rectangle((420, GROUND - 140, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 140), (680, GROUND - 140), (540, GROUND - 200)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('楚国苦县人 姓李名耳 字聃', SERIF, 46, QINGNIU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '据史记 生卒年皆不可考', t, t - u + P)

def art_d_legend(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, female=True, baby=True, arm=60, layer='mid')
    A.d['wash'].ellipse((470, GROUND - 260, 610, GROUND - 200), fill=200)
    A.flush(cv)
    paste(cv, text_img('相传生而白首 故称老子', SERIF, 48, ZIQI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此为后世神仙传说', t, t - u + P)

def art_d_shouzang(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        A.d['mid'].rectangle((140 + i * 140, GROUND - 330, 250 + i * 140, GROUND), fill=170)
        for j in range(4):
            slips(A, 150 + i * 140, GROUND - 20 - j * 78, 5, 60, layer='ochre')
    lao(A, 540, GROUND, 190, dir=1, arm=120)
    A.flush(cv)
    paste(cv, text_img('任周朝守藏室之史', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '相当于王室图书档案馆的官员', t, t - u + P)

def art_d_read(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 560, GROUND, 420, layer='mid')
    lao(A, 300, GROUND, 180, dir=1, kneel=True, arm=100)
    slips(A, 470, GROUND - 74, 10, 70, layer='ochre', tied=False)
    lamp(A, 760, GROUND - 74, 28, t, glow=0.8)
    A.flush(cv)
    paste(cv, text_img('遍读王室藏书 通晓古今礼制', SERIF, 46, QINGNIU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_zhou(A, cv, t, u):
    palace(A, 540, 1300, 320, collapse=clamp(u / (3 * P)) * 0.3, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('周室衰微 礼崩乐坏', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '诸侯争霸 天子形同虚设', t, t - u + P)

def art_d_think(A, cv, t, u):
    ground(A, GROUND)
    sitter(A, 540, GROUND, 200, dir=1)
    A.d['wash'].polygon([(560, GROUND - 170), (580, GROUND - 170), (575, GROUND - 100)], fill=255)
    A.flush(cv)
    paste(cv, text_img('他开始思考 乱世的根源', SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 问礼
def art_d_wenli(A, cv, t, u):
    """6-beat set piece: 孔子问礼 — Confucius comes to Luoyang to ask about rites; Laozi warns him off pride; Confucius calls him a dragon."""
    ph = u / P
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    lao(A, 760, GROUND, 210, dir=-1, arm=lerp(-8, 60, clamp((ph - 2) / 0.4)) if ph < 4 else -8)
    kong(A, 340, GROUND, 200, dir=1 if ph < 4 else -1, bow=30 if ph < 4 else 0, arm=-8)
    if ph >= 4:
        for k in range(10):
            f = k / 9
            x = lerp(180, 900, f); y = 920 + 50 * math.sin(f * 6 + t * 2)
            A.d['ziqi'].ellipse((x - 26, y - 26, x + 26, y + 26), fill=int(80 + 100 * f))
    A.flush(cv)
    if ph < 2:
        lab, col = '孔子到洛邑 向老子问礼', QINGNIU
    elif ph < 4:
        lab, col = '去子之骄气与多欲', ZIQI
    else:
        lab, col = '孔子叹道 其犹龙邪', ZHU
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '事见史记 年份约略', t, t - u + P)

def art_d_dragon(A, cv, t, u):
    ground(A, GROUND)
    kong(A, 540, GROUND, 210, dir=1, arm=60)
    for k in range(5):
        person(A, 140 + k * 70, GROUND, 130, dir=1, robe=True, hat='knot', arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('鸟能飞 鱼能游 兽能走', SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('至于龙 吾不能知', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_d_wangzi(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        ox(A, lerp(-100, 700, ease_out(u / (3 * P))) + k * 160, GROUND, 120, dir=1, ph=t * 3, layer='mid')
        bundle(A, lerp(-100, 700, ease_out(u / (3 * P))) + k * 160, GROUND - 90, 60)
    A.flush(cv)
    paste(cv, text_img('王子朝作乱 携典籍奔楚', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '周室藏书大量散失', t, t - u + P)

def art_d_leave(A, cv, t, u):
    palace(A, 760, 1300, 240, layer='mid')
    ground(A, GROUND)
    lao(A, lerp(560, 200, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 2, staff=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('辞去官职 离开周都', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见周之衰 乃遂去', t, t - u + P)

def art_d_wander(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 280), (x + 240, GROUND)], fill=150)
    ground(A, GROUND)
    rider_lao(A, lerp(200, 800, clamp(u / (4 * P))), GROUND, 200, t)
    A.flush(cv)
    paste(cv, text_img('一路向西 隐于山野', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '骑青牛为后世画像传说', t, t - u + P)

# ================================================================ 第三回 出关
def scene_chuguan(cv, t, c, k):
    """8-beat custom scene: 出函谷关 — the old man on the ox reaches the pass; the gate warden 尹喜 bows and asks for a book;
    slips are written; he rides out through the gate into the violet mist."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    city_wall(A, 300, 980, 1080, gate_x=640, label='函谷', layer='mid', open_=1.0)
    ground(A, GROUND)
    if ph < 2:
        rider_lao(A, lerp(-80, 330, ease_out(ph / 2)), GROUND, 200, t)
        person(A, 500, GROUND, 180, dir=-1, robe=True, hat='knot', arm=-8, layer='ink')
        lab, col = '西行至关 关令尹喜望见', QINGNIU
    elif ph < 5:
        ox(A, 120, GROUND, 160, dir=1, moving=False)
        lao(A, 300, GROUND, 190, dir=1, kneel=True, arm=lerp(90, 110, 0.5 + 0.5 * math.sin(t * 5)))
        person(A, 500, GROUND, 180, dir=-1, robe=True, hat='knot', kneel=True, bow=20, arm=-8, layer='ink')
        n = int(clamp((ph - 2) / 2.6) * 14)
        slips(A, 330, GROUND - 6, n, 90, layer='ochre', tied=False)
        lab, col = '子将隐矣 强为我著书', QINGNIU
    else:
        go = clamp((ph - 5) / 2.6)
        rider_lao(A, lerp(380, 1100, ease_out(go)), GROUND, 200, t)
        person(A, 380, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=-8, layer='ink')
        bundle(A, 300, GROUND, 80)
        ziqi(A, 600, 1040, 1020, t, a=go)
        lab, col = '著书五千言而去 莫知其所终', ZHU
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '出关', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=93)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '紫气东来出自后世传说 一说所出为散关', t, s0 + 5 * P)

def art_d_shang(A, cv, t, u):
    ground(A, GROUND)
    slips(A, 300, GROUND, 20, 220, layer='ochre')
    A.flush(cv)
    paste(cv, text_img('上篇言道', SERIF, 52, QINGNIU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('道可道 非常道', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_d_xia(A, cv, t, u):
    ground(A, GROUND)
    slips(A, 300, GROUND, 20, 220, layer='ochre')
    A.flush(cv)
    paste(cv, text_img('下篇言德', SERIF, 52, QINGNIU, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('上德不德 是以有德', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_d_where(A, cv, t, u):
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 300), (x + 240, GROUND)], fill=140)
    ziqi(A, 140, 940, 1200, t, a=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('从此不知去向', SERIF, 52, ZIQI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_d_shiji(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('或曰老莱子\n或曰太史儋', SERIF, 50, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('连司马迁也说不清他是谁', SERIF, 46, QINGNIU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '史记 又言其或百六十余岁', t, t - u + P)

def art_d_count(A, cv, t, u):
    slip_wall(A, 540, 1100, 81, cols=27, rows=3, w=26, h=110)
    A.flush(cv)
    paste(cv, text_img('后人分为八十一章', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第四回 五千言
def art_d_water(A, cv, t, u):
    """6-beat set piece: 上善若水 — water flows round a stone without contending; drop by drop it wears the stone hollow."""
    ph = u / P
    hole = clamp((ph - 3) / 2.5)
    A.d['ink'].pieslice((380, GROUND - 260, 700, GROUND + 60), 180, 360, fill=255)
    if hole > 0:
        A.d['wash'].ellipse((520 - 40 * hole, GROUND - 230 + 10, 560 + 40 * hole, GROUND - 230 + 10 + 50 * hole), fill=255)
    A.d['ocean'].rectangle((60, GROUND - 40, W - 60, GROUND + 40), fill=150)
    river(A, GROUND - 36, t, rows=2, amp=4)
    for k in range(3):
        y = (t * 400 + k * 140) % 420 + 760
        if y < GROUND - 240:
            A.d['ocean'].ellipse((532, y, 548, y + 22), fill=255)
    A.flush(cv)
    if ph < 3:
        lab, col = '上善若水 水善利万物而不争', QINGNIU
    else:
        lab, col = '天下莫柔弱于水 而攻坚强者莫之能胜', ZIQI
    paste(cv, text_img(lab, SERIF, 44 if ph >= 3 else 46, col, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_d_zhiren(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].ellipse((380, 940, 700, 1260), fill=255)
    A.d['ink'].ellipse((380, 940, 700, 1260), outline=255, width=6)
    lao(A, 540, GROUND, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('知人者智 自知者明', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_qianli(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(10, int(u / (0.35 * P)) + 1)):
        A.d['ink'].ellipse((140 + k * 80, GROUND - 14 - (k % 2) * 10, 170 + k * 80, GROUND - 2 - (k % 2) * 10), fill=255)
    A.flush(cv)
    paste(cv, text_img('千里之行 始于足下', SERIF, 50, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_huofu(A, cv, t, u):
    ground(A, GROUND)
    a = 0.4 * math.sin(t * 1.2)
    cx, cy = 540, 1160
    A.d['ink'].polygon([(cx - 30, GROUND), (cx + 30, GROUND), (cx, cy)], fill=255)
    for s in (-1, 1):
        ex, ey = cx + s * 260 * math.cos(a), cy + s * 260 * math.sin(a)
        A.d['ink'].line((cx, cy, ex, ey), fill=255, width=8)
        A.d['qingniu' if s < 0 else 'ziqi'].ellipse((ex - 50, ey, ex + 50, ey + 60), fill=255)
    A.flush(cv)
    paste(cv, text_img('祸兮福之所倚 福兮祸之所伏', SERIF, 46, QINGNIU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_xiaoxian(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].chord((380, GROUND - 200, 700, GROUND), 0, 180, fill=255)
    A.d['ink'].rectangle((370, GROUND - 110, 710, GROUND - 96), fill=255)
    flames(A, 540, GROUND, 200, 50, t, n=2, seed=931, smoke=False)
    A.flush(cv)
    paste(cv, text_img('治大国 若烹小鲜', SERIF, 52, QINGNIU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '煎小鱼不可频频翻动', t, t - u + P)

def art_d_wuwei(A, cv, t, u):
    ground(A, GROUND)
    sitter(A, 540, GROUND, 200, dir=1)
    ziqi(A, 280, 800, 1000, t, a=0.6)
    A.flush(cv)
    paste(cv, text_img('道常无为 而无不为', SERIF, 52, QINGNIU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 道
def art_d_zhuang(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    for k in range(3):
        x = 760 + 40 * math.sin(t * 2 + k); y = 1000 + k * 60
        A.d['ziqi'].ellipse((x - 20, y - 12, x + 20, y + 12), fill=200)
    A.flush(cv)
    paste(cv, text_img('庄子承其学说 世称老庄', SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_d_huanglao(A, cv, t, u):
    """6-beat set piece: 黄老之治 — the early Han rule lightly, rest the people; fields refill, granaries overflow."""
    ph = u / P
    ground(A, GROUND)
    for k in range(5):
        A.d['grass'].rectangle((120 + k * 180, GROUND - 26, 260 + k * 180, GROUND - 6), fill=int(120 + 100 * clamp(ph / 3)))
    if ph >= 3:
        for k in range(3):
            x = 300 + k * 240
            A.d['ochre'].chord((x - 70, GROUND - 260 * clamp((ph - 3) / 1.5), x + 70, GROUND + 100), 180, 360, fill=230)
    A.flush(cv)
    lab = '汉初推崇黄老 与民休息' if ph < 3 else '文景之治 仓廪充实'
    paste(cv, text_img(lab, SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '黄老之学 托名黄帝而宗老子', t, t - u + P)

def art_d_laojun(A, cv, t, u):
    ground(A, GROUND)
    lao(A, 540, GROUND, 260, dir=1, arm=-8)
    ziqi(A, 260, 820, 1000, t, a=0.8)
    A.flush(cv)
    paste(cv, text_img('东汉以后 道教奉为太上老君', SERIF, 46, ZIQI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '思想家老子与神仙老君 并非一回事', t, t - u + P)

def art_d_tang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 200, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('唐朝皇室姓李 尊他为始祖', SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '唐高宗追号太上玄元皇帝', t, t - u + P)

def art_d_silk(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((300, 980, 780, 1300), fill=255)
    A.d['ink'].rectangle((300, 980, 780, 1300), outline=200, width=3)
    for k in range(12):
        A.d['ink'].line((740 - k * 36, 1000, 740 - k * 36, 1280 - (k % 3) * 60), fill=170, width=3)
    A.flush(cv)
    paste(cv, text_img('马王堆帛书 郭店楚简相继出土', SERIF, 46, QINGNIU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '最早的道德经写本距今两千多年', t, t - u + P)

def art_d_world(A, cv, t, u):
    ground(A, GROUND)
    for i in range(8):
        book(A, 180 + i * 100, GROUND, 80, 140 + (i % 3) * 30, layer=['qingniu', 'ziqi', 'mid', 'ochre'][i % 4])
    A.flush(cv)
    paste(cv, text_img('译成数十种文字 传遍世界', SERIF, 48, QINGNIU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_d_end(A, cv, t, u):
    ground(A, GROUND)
    rider_lao(A, lerp(500, 980, ease_out(u / (4 * P))), GROUND, 200, t)
    ziqi(A, 300, 1000, 1080, t)
    A.flush(cv)
    paste(cv, text_img('道法自然', SERIF, 56, ZIQI, 'Black', bleed=False, spacing=10), W / 2, 760, 1, clamp(u / 0.4))

def art_d_legacy(A, cv, t, u):
    bundle(A, 860, 1420, 80)

def art_d_title(A, cv, t, u):
    ox(A, 830, 1440, 200, dir=-1, moving=False)
    ziqi(A, 600, 1000, 1150, t, a=0.6)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    lao(A, 380, 1460, 680, dir=1, staff=True, arm=lerp(-5, 30, ease_out(u / (2 * P))))

from render_zhuxi import book

# ================================================================ script
CHAPTERS = {16: ('第一回', '守藏'), 48: ('第二回', '问礼'), 80: ('第三回', '出关'),
            112: ('第四回', '五千言'), 144: ('第五回', '道法自然')}

CARDS = [
    C(0, 2, 'works', 'num', num='五千字', line='读了两千五百年', art=art_d_hook_slips),
    C(2, 4, 'fate', 'num', num='一头青牛', line='出关后再无消息', art=art_d_hook_ox),
    C(4, 6, 'night', 'num', num='孔子见他', line='说他像一条龙', art=art_d_hook_dragon),
    C(6, 8, 'life', 'num', num='一滴水', line='能穿透石头', art=art_d_hook_water),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 守藏
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-571, main='苦县人', sub='姓李名耳', note='年份约略', art=art_d_birth),
    C(22, 26, 'night', 'card', year=-571, main='生而白首', sub='传说', art=art_d_legend),
    C(26, 32, 'court', 'card', year=-545, main='守藏室史', sub='周王室', note='年份约略', art=art_d_shouzang),
    C(32, 38, 'works', 'card', year=-540, main='遍读藏书', sub='通晓礼制', note='年份约略', art=art_d_read),
    C(38, 44, 'fate', 'card', year=-530, main='周室衰微', sub='礼崩乐坏', note='年份约略', art=art_d_zhou),
    C(44, 48, 'night', 'card', year=-525, main='乱从何来', sub='思索', note='年份约略', art=art_d_think),
    # ---- 第二回 问礼
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'empire', 'card', year=-518, main='孔子问礼', sub='洛邑相见', art=art_d_wenli),
    C(56, 62, 'life', 'card', year=-518, main='其犹龙邪', sub='孔子之叹', art=art_d_dragon),
    C(62, 68, 'war', 'card', year=-516, main='王子朝之乱', sub='典籍奔楚', art=art_d_wangzi),
    C(68, 74, 'fate', 'card', year=-510, main='辞官', sub='见周之衰', note='年份无考', art=art_d_leave),
    C(74, 80, 'night', 'card', year=-505, main='西行', sub='隐于山野', note='年份无考', art=art_d_wander),
    # ---- 第三回 出关
    C(80, 82, 'fate', 'chapter'),
    C(82, 90, 'night', 'chuguan', year=-500),
    C(90, 94, 'works', 'card', year=-500, main='上篇', sub='道经', art=art_d_shang),
    C(94, 98, 'empire', 'card', year=-500, main='下篇', sub='德经', art=art_d_xia),
    C(98, 104, 'death', 'card', year=-500, main='莫知所终', sub='不知去向', note='年份无考', art=art_d_where),
    C(104, 108, 'court', 'card', year=-500, main='他是谁', sub='史记存疑', art=art_d_shiji),
    C(108, 112, 'works', 'card', year=-500, main='八十一章', sub='五千言', art=art_d_count),
    # ---- 第四回 五千言
    C(112, 114, 'works', 'chapter'),
    C(114, 120, 'life', 'card', year=-500, main='上善若水', sub='不争之德', art=art_d_water),
    C(120, 124, 'night', 'card', year=-500, main='自知者明', sub='道德经', art=art_d_zhiren),
    C(124, 128, 'life', 'card', year=-500, main='始于足下', sub='道德经', art=art_d_qianli),
    C(128, 134, 'fate', 'card', year=-500, main='祸福相倚', sub='道德经', art=art_d_huofu),
    C(134, 138, 'court', 'card', year=-500, main='若烹小鲜', sub='治国之道', art=art_d_xiaoxian),
    C(138, 144, 'empire', 'card', year=-500, main='无为', sub='无不为', art=art_d_wuwei),
    # ---- 第五回 道法自然
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'works', 'card', year=-300, main='老庄', sub='庄子承之', art=art_d_zhuang),
    C(150, 156, 'life', 'card', year=-170, main='黄老之治', sub='与民休息', art=art_d_huanglao),
    C(156, 160, 'night', 'card', year=150, main='太上老君', sub='道教尊奉', note='年份约略', art=art_d_laojun),
    C(160, 163, 'court', 'card', year=666, main='玄元皇帝', sub='唐朝追号', art=art_d_tang),
    C(163, 166, 'works', 'card', year=1973, main='帛书竹简', sub='重见天日', art=art_d_silk),
    C(166, 168, 'empire', 'card', year=1973, main='传遍世界', sub='数十种译本', art=art_d_world),
    C(168, 170, 'end', 'card', year=1973, main='道法自然', sub='青牛远去', art=art_d_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='玖拾叁', col=QINGNIU, acc=ZIQI, born=-571, died=-471, age0=-572, no_age=True,
    born_lab='生年不详', died_lab='卒年不详', years_txt='约春秋末年 生卒年不详',
    hook_q='他只写了五千字 · 为什么被读了两千五百年？',
    name_line='李耳 · 字聃', name='老子', seal='道德', title_art=art_d_title,
    q1='消极避世？', q2='东方智者？',
    end_art=art_d_legacy, end_big='道德经', end_seal='道德',
    end_l1='他说得最少', end_l2='却被人读得最久',
    end_brush='上善若水', end_ask='道德经里 你最喜欢哪一句？评论区聊聊', next='墨子'),
    scenes=dict(chapter=scene_chapter, chuguan=scene_chuguan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
