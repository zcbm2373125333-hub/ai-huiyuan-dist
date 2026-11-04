"""千古人物志 · 第伍拾肆集 · 张良 (约前250–前186)
Look: 黄石金 + 云烟蓝, 铁椎 corner borders, a 圯桥黄石 chapter card: a yellow stone under the old bridge glows a
little brighter every chapter, and in the last chapter clouds roll over it.
Set pieces: custom 8-beat scene 'bolangsha' (博浪沙), 6-beat 圯上纳履, 6-beat 鸿门宴, 6-beat 借箸代筹, 6-beat 商山四皓.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_mengtian as Mt        # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_sunwu import army, banner
from render_quyuan import river
from render_lisi import emperor

F.RIPPLE = False
HUANGSHI = (186, 150, 66)           # 黄石金
YUNYAN = (104, 116, 150)            # 云烟蓝
S.LAYERS.append(('huangshi', HUANGSHI, 0.9, 1.0))
S.LAYERS.append(('yunyan', YUNYAN, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='谋', life='韩', court='汉', night='夜', war='楚', empire='汉', works='谋', fate='隐', death='韩', end='留')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (ZHU, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (HUANGSHI, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (YUNYAN, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (32, 34, 48), 'death': (62, 60, 66), 'war': (110, 62, 52), 'fate': (94, 98, 116)}
def draw_background(t, theme):
    """下邳: low hills, the old stone bridge silhouettes and slow cloud wisps at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 186, 192), (152, 156, 172), MTN_COL.get(theme, (106, 112, 136))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x0 in (60, 820):
        d.arc((x0, 1400, x0 + 200, 1520), 180, 360, fill=(90, 90, 96, 60), width=10)
        d.line((x0 - 10, 1460, x0 + 210, 1460), fill=(90, 90, 96, 50), width=6)
    for k in range(3):
        x = (t * 14 + k * 380) % (W + 500) - 250
        d.ellipse((x - 180, 1330 + k * 24 - 18, x + 180, 1330 + k * 24 + 18), fill=(236, 236, 240, 46))
    canvas.alpha_composite(ov)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """铁椎: an iron hammer on a short chain in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=YUNYAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=YUNYAN + (220,), width=3)
        for k in range(4):
            cx, cy = x + sx * (18 + k * 12), y + sy * (18 + k * 12)
            d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), outline=(60, 60, 64, 220), width=2)
        hx, hy = x + sx * 76, y + sy * 76
        d.ellipse((hx - 18, hy - 18, hx + 18, hy + 18), fill=(52, 52, 56, 235))
        d.ellipse((hx - 6, hy - 10, hx + 2, hy - 4), fill=HUANGSHI + (200,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def zhang(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """张良: slender, beardless (状貌如妇人好女) — soft cap with a long ribbon and a feather fan."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
        A.d['yunyan'].line((x - dir * 0.06 * h, y - 0.98 * h, x - dir * 0.2 * h, y - 0.7 * h), fill=255, width=max(2, int(0.014 * h)))
        A.d['huangshi'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        if old > 0.4:
            A.d['wash'].chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
    return hand

def liubang(A, x, y, h, dir=-1, layer='ink', **kw):
    return person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)

def oldman(A, x, y, h, dir=-1, **kw):
    kw.setdefault('arm', 30)
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=kw.pop('layer', 'ink'), bow=kw.pop('bow', 15), **kw)
    A.d['wash'].polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.1 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.58 * h)], fill=255)
    A.d['ink'].line((x + dir * 0.25 * h, y, x + dir * 0.22 * h, y - 0.8 * h), fill=255, width=max(3, int(0.02 * h)))
    return hand

def hammer(A, x, y, s, layer='ink'):
    A.d[layer].ellipse((x - s, y - s, x + s, y + s), fill=255)
    A.d['huangshi'].ellipse((x - 0.4 * s, y - 0.6 * s, x - 0.1 * s, y - 0.3 * s), fill=200)

def bridge(A, cx, base, w, layer='mid'):
    A.d[layer].arc((cx - w / 2, base - 0.5 * w, cx + w / 2, base + 0.3 * w), 180, 360, fill=255, width=26)
    A.d[layer].rectangle((cx - w / 2 - 60, base - 0.12 * w, cx + w / 2 + 60, base - 0.08 * w), fill=255)

def ystone(A, x, y, s, glow=0.0):
    if glow > 0:
        r = s * (1.4 + 0.8 * glow) + 6 * math.sin(glow * 9)
        A.d['huangshi'].ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=int(90 * glow))
    A.d['huangshi'].polygon([(x - s, y + 0.4 * s), (x - 0.7 * s, y - 0.5 * s), (x + 0.2 * s, y - 0.7 * s), (x + s, y - 0.1 * s), (x + 0.8 * s, y + 0.4 * s)], fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.2), 48: (0.2, 0.45), 80: (0.45, 0.7), 112: (0.7, 1.0), 144: (1.0, 1.0)}
def art_stone_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    g0, g1 = CH.get(kb, (0.2, 0.45))
    q = ease_out(u / (1.2 * P))
    A.d['ocean'].rectangle((60, 1180, W - 60, 1260), fill=120)
    waves(A, 1190, t, rows=2, amp=4)
    bridge(A, 540, 1180, 600)
    ystone(A, 540, 1150, 46, glow=lerp(g0, g1, q))
    if kb == 144:
        for k in range(4):
            x = lerp(-300, 1300, clamp(q * 1.2 - k * 0.1))
            A.d['wash'].ellipse((x - 220, 1040 + k * 40 - 50, x + 220, 1040 + k * 40 + 50), fill=200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_stone_chapter)
    ink_in(cv, text_img(no, SERIF, 56, YUNYAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_hammer(A, cv, t, u):
    ground(A, GROUND)
    for j in range(3):
        carriage(A, 260 + j * 260, GROUND, 80, dir=1, moving=False, layer='mid')
    q = ease_out(u / (1.4 * P))
    hammer(A, lerp(1000, 520, q), lerp(800, GROUND - 120, q), 40)

def art_l_hook_shoe(A, cv, t, u):
    bridge(A, 540, 1180, 600)
    ground(A, GROUND)
    q = ease_out(u / (1.4 * P))
    A.d['ink'].ellipse((540 - 30, lerp(1080, 1240, q) - 12, 540 + 30, lerp(1080, 1240, q) + 12), fill=255)

def art_l_hook_fief(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 30) + 1
    for i in range(n):
        x = 120 + (i % 15) * 60; y = GROUND - 20 - (i // 15) * 60
        A.d['mid'].rectangle((x - 20, y - 20, x + 20, y + 10), fill=200)
    A.d['huangshi'].rectangle((500, GROUND - 200, 580, GROUND - 140), fill=255)

def art_l_hook_tent(A, cv, t, u):
    tent(A, 540, GROUND, 440, 300, layer='yunyan')
    ground(A, GROUND)
    lamp(A, 540, GROUND, 40, t, glow=0.9)

# ================================================================ 第一回 五世相韩
def art_l_birth(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='huangshi')
    ground(A, GROUND)
    person(A, 780, GROUND, 190, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    person(A, 860, GROUND, 90, dir=-1, robe=True, hat='knot', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('祖父 父亲五世相韩', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('韩国', 56), 260, 1020, t, t - u + P, rot=-5)

def art_l_hanfall(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='新郑', layer='mid', open_=1.0)
    flames(A, 540, 1060, 600, 200 * ease_out(u / P), t, n=7, seed=230, smoke=True)
    ground(A, GROUND)
    army(A, lerp(-200, 120, ease_out(u / (2 * P))), GROUND, 5, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('秦灭韩 · 六国第一个', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_vow(A, cv, t, u):
    A.d['mid'].chord((620, 1140, 900, 1300), 180, 360, fill=230)
    ground(A, GROUND)
    zhang(A, 400, GROUND, 190, dir=1, arm=-8)
    n = int(clamp(u / (2 * P)) * 8)
    for i in range(n):
        A.d['gold'].ellipse((lerp(400, 100 + i * 40, 1) - 12, GROUND - 30 - 12, lerp(400, 100 + i * 40, 1) + 12, GROUND - 30 + 12), fill=255)
    A.flush(cv)
    type_in(cv, text_img('弟死不葬 悉以家财求客刺秦王', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('家僮三百', 44, INK), 860, 1020, t, t - u + P, rot=6)

def art_l_strongman(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=160)
    ground(A, GROUND)
    zhang(A, 340, GROUND, 180, dir=1, arm=60)
    person(A, 680, GROUND, 260, dir=-1, robe=False, hat='knot', arm=lerp(40, 160, ease_out((u - P) / 0.4)), layer='ink')
    hammer(A, 600, GROUND - 300 + 60 * ease_out((u - P) / 0.4), 34)
    A.flush(cv)
    paste(cv, text_img('东见仓海君 · 得力士 铁椎重百二十斤', SERIF, 42, YUNYAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def scene_bolangsha(cv, t, c, k):
    """8-beat custom scene: 博浪沙 — the imperial convoy of identical carriages rolls past the dunes; the strongman hurls the hammer;
    it smashes the second carriage — the wrong one; the guards scatter; the two vanish."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['dune'].polygon([(60, GROUND), (200, GROUND - 160), (420, GROUND - 60), (700, GROUND - 200), (W - 60, GROUND)], fill=200)
    ground(A, GROUND)
    move = ph < 3.2
    xs = [lerp(1300, 820, clamp(ph / 3.2)) - j * 230 for j in range(4)]
    for j, x in enumerate(xs):
        carriage(A, x, GROUND, 80, dir=-1, wheel=t * 6 if move else 0, ph=t * 8 + j, moving=move, layer='yunyan' if j != 1 else 'ink')
    if 2.2 <= ph < 3.4:
        q = (ph - 2.2) / 1.0
        hammer(A, lerp(180, xs[1], q), lerp(GROUND - 300, GROUND - 120, q) - 160 * math.sin(q * math.pi), 34)
    if ph >= 3.2:
        x = xs[1]
        for k2 in range(6):
            a = k2 * 1.05
            r = 40 + 120 * ease_out((ph - 3.2) / 0.6)
            A.d['wash'].ellipse((x + r * math.cos(a) - 10, GROUND - 100 + r * math.sin(a) * 0.5 - 10, x + r * math.cos(a) + 10, GROUND - 100 + r * math.sin(a) * 0.5 + 10), fill=200)
        for j in range(4):
            person(A, x + (j - 1.5) * 90, GROUND, 110, dir=-1 if j % 2 else 1, robe=False, hat='helmet', spear=True, ph=t * 6 + j, arm=40, layer='ink')
    hx = 180 if ph < 4.5 else lerp(180, -200, ease_out((ph - 4.5) / 1.5))
    person(A, hx, GROUND - 160, 150, dir=1, robe=False, hat='knot', arm=lerp(-8, 170, clamp((ph - 1.8) / 0.4)), layer='ink')
    zhang(A, hx - 70, GROUND - 150, 130, dir=1, arm=-8, ph=t * 5 if ph >= 4.5 else None)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '博浪沙', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=54)
    fx.flush(cv)
    lab = '始皇东游 · 车驾行至博浪沙' if ph < 2.2 else ('力士狙击' if ph < 3.2 else ('误中副车' if ph < 4.5 else '秦皇大怒 · 张良逃脱'))
    paste(cv, text_img(lab, SERIF, 46, ZHU if 3.2 <= ph < 4.5 else YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('一击不中 · 名动天下', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 5.5) / 0.4))

def art_l_hide(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='下邳', layer='mid', open_=1.0)
    ground(A, GROUND)
    zhang(A, lerp(-60, 400, ease_out(u / (2.5 * P))), GROUND, 180, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    paste(cv, text_img('更名姓 · 亡匿下邳', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_search(A, cv, t, u):
    ground(A, GROUND)
    for j in range(6):
        rider(A, (t * 120 + j * 220) % (W + 300) - 150, GROUND - (j % 2) * 30, 100, dir=1, ph=t * 8 + j, spear=True)
    A.flush(cv)
    paste(cv, text_img('令天下大索十日', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第二回 圯上老人
def art_l_shoe(A, cv, t, u):
    """6-beat set piece: 圯上纳履 — the old man kicks his shoe off the bridge; Zhang fetches it and kneels to put it on;
    three dawns at the bridge; the book is handed over."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    bridge(A, 540, 1200, 700)
    if ph < 3:
        oldman(A, 600, 1080, 180, dir=-1, arm=-8)
        sy = lerp(1060, 1240, clamp(ph / 0.6))
        if ph < 1.6:
            A.d['ink'].ellipse((600 - 26, sy - 10, 600 + 26, sy + 10), fill=255)
        zhang(A, lerp(280, 520, clamp((ph - 0.8) / 0.8)), 1080, 180, dir=1, kneel=ph > 1.8, bow=30 if ph > 1.8 else 0, arm=100 if ph > 1.8 else -8)
        lab = '老父堕履圯下 · 孺子下取履' if ph < 1.8 else '履我 · 良长跪履之'
    elif ph < 4.6:
        k = min(2, int((ph - 3) / 0.55))
        r = 60 + 20 * k
        A.d['red'].ellipse((900 - r, 820 - r, 900 + r, 820 + r), fill=120 + 40 * k)
        zhang(A, 520, 1080, 180, dir=1, arm=-8)
        if k == 2:
            oldman(A, 640, 1080, 180, dir=-1, arm=40)
        lab = ['五日平明 · 老父已先在', '五日鸡鸣 · 又后', '夜未半往 · 老父亦来'][k]
    else:
        oldman(A, 640, 1080, 180, dir=-1, arm=90)
        zhang(A, 480, 1080, 180, dir=1, kneel=True, bow=30, arm=100)
        A.d['huangshi'].rectangle((550, 960, 600, 990), fill=255)
        lab = '读此则为王者师矣'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4.6 else YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见史记留侯世家 带传奇色彩', t, t - u + P)

def art_l_book(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='yunyan')
    sitter(A, 300, GROUND, 190, dir=1, bow=20)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    scroll(A, 540, GROUND - 120, 240, 60, clamp(u / P), layer='huangshi')
    A.flush(cv)
    paste(cv, text_img('太公兵法 · 常习诵读之', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('黄石公', 50), 860, 1020, t, t - u + P, rot=6)

def art_l_xiangbo(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    person(A, lerp(-60, 640, ease_out(u / (2 * P))), GROUND, 180, dir=1, robe=True, hat='knot', ph=t * 5, arm=-8, layer='ink')
    zhang(A, 820, GROUND, 180, dir=-1, arm=80)
    A.flush(cv)
    paste(cv, text_img('项伯杀人 · 从良匿', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('项伯', 54), 260, 1020, t, t - u + P, rot=-5)

def art_l_chaos(A, cv, t, u):
    ground(A, GROUND)
    for j in range(7):
        person(A, 140 + j * 120, GROUND, 120, dir=1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
    banner(A, 880, GROUND, 300, t, layer='red')
    A.flush(cv)
    paste(cv, text_img('陈胜吴广起事 · 良亦聚少年百余人', SERIF, 42, YUNYAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_l_meet(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=160)
    ground(A, GROUND)
    zhang(A, 380, GROUND, 190, dir=1, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)))
    liubang(A, 680, GROUND, 210, dir=-1, arm=lerp(-8, 80, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('他人皆不省 沛公殆天授', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('沛公', 54), 860, 1020, t, t - u + 0.4, rot=6)

def art_l_hanwang(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='huangshi')
    ground(A, GROUND)
    person(A, 700, GROUND, 200, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    zhang(A, 400, GROUND, 190, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    paste(cv, text_img('立韩成为韩王 · 良为韩司徒', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_yaoguan(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='峣关', layer='mid', open_=clamp((u - 2 * P) / P))
    ground(A, GROUND)
    for i in range(int(clamp(u / (2 * P)) * 6)):
        A.d['gold'].rectangle((360 + (i % 3) * 40, GROUND - 30 - (i // 3) * 26, 392 + (i % 3) * 40, GROUND - 8 - (i // 3) * 26), fill=255)
    zhang(A, 260, GROUND, 180, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('秦将贾竖 易动以利 · 啗之而袭', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 鸿门
def art_l_xianyang(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='huangshi')
    ground(A, GROUND)
    liubang(A, 700, GROUND, 210, dir=-1, arm=lerp(20, 120, 0.5 + 0.5 * math.sin(t * 2)))
    for i in range(3):
        person(A, 860 + i * 40, GROUND, 120, dir=-1, robe=True, hat='knot', female=True, arm=30, layer='mid')
    zhang(A, 380, GROUND, 200, dir=1, arm=lerp(40, 120, ease_out((u - P) / 0.4)))
    A.flush(cv)
    type_in(cv, text_img('忠言逆耳利于行 毒药苦口利于病', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('还军霸上', 44), 260, 1020, t, t - u + 2 * P, rot=-5)

def art_l_hongmen(A, cv, t, u):
    """6-beat set piece: 鸿门宴 — the seating; Xiang Zhuang's sword dance; Fan Kuai bursts in; Liu Bang slips out; Zhang Liang stays to offer the jade."""
    ph = u / P
    tent(A, 540, GROUND, 760, 420, layer='mid')
    ground(A, GROUND)
    person(A, 260, GROUND, 180, dir=1, robe=True, hat='crown', kneel=True, arm=40, layer='ink')
    if ph < 3.6:
        liubang(A, 820, GROUND, 180, dir=-1, kneel=True, arm=40)
    zhang(A, 900, GROUND, 170, dir=-1, kneel=True, arm=40)
    if 1 < ph < 3.6:
        x = 540 + 120 * math.sin(t * 3)
        person(A, x, GROUND, 190, dir=1 if math.cos(t * 3) > 0 else -1, robe=False, hat='knot', arm=lerp(60, 170, 0.5 + 0.5 * math.sin(t * 6)), layer='red')
    if 2.4 < ph < 3.6:
        person(A, lerp(1100, 680, ease_out((ph - 2.4) / 0.5)), GROUND, 220, dir=-1, robe=False, hat='helmet', arm=120, layer='ink')
    if ph >= 3.6:
        A.d['wash'].ellipse((480, GROUND - 60, 600, GROUND - 20), fill=255)
    A.flush(cv)
    lab = '项王 亚父 沛公 张良 · 四人入座' if ph < 1 else ('项庄舞剑 意在沛公' if ph < 2.4 else ('樊哙闯帐' if ph < 3.6 else '沛公脱身 · 良留谢 献白璧一双'))
    paste(cv, text_img(lab, SERIF, 44, ZHU if 1 <= ph < 3.6 else YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('鸿门', 56, INK), 860, 1440, t, t - u + 0.4, rot=6)

def art_l_plank(A, cv, t, u):
    for k in range(4):
        x = 140 + k * 280
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 440), (x + 200, GROUND)], fill=170)
    q = ease_out(u / (2 * P))
    A.d['huangshi'].rectangle((60, GROUND - 260, W - 60, GROUND - 240), fill=255)
    flames(A, lerp(900, 300, q), GROUND - 260, 300, 160, t, n=5, seed=206, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('烧绝栈道 · 示天下无还心', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('栈道', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_l_hancheng(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='crown', kneel=True, bow=lerp(10, 60, ease_out(u / (2 * P))), arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('项羽杀韩王成 · 张良间行归汉', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_xiayi(A, cv, t, u):
    ground(A, GROUND)
    liubang(A, 760, GROUND, 200, dir=-1, kneel=True, bow=10, arm=40)
    zhang(A, 340, GROUND, 190, dir=1, kneel=True, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.flush(cv)
    names = ['英布', '彭越', '韩信']
    for i, nm in enumerate(names):
        stamp(cv, seal(nm, 44, ZHU if i == 2 else INK), 340 + i * 200, 1060, t, t - u + (0.5 + i * 0.8) * P)
    paste(cv, text_img('下邑之谋 · 可属大事者三人', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_chopsticks(A, cv, t, u):
    """6-beat set piece: 借箸代筹 — at dinner he borrows the King's chopsticks and lays them out one by one: eight reasons not to restore the six states."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 520, layer='mid')
    liubang(A, 860, GROUND, 190, dir=-1, kneel=True, arm=lerp(40, 160, clamp((ph - 4.8) / 0.3)))
    zhang(A, 220, GROUND, 180, dir=1, kneel=True, arm=100)
    n = min(8, int(ph / 0.55) + 1)
    for i in range(n):
        x = 340 + i * 50
        A.d['huangshi'].line((x, GROUND - 90, x + 20, GROUND - 160), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img(f'臣请借前箸为大王筹之 · 其不可{cn_num(n)}', SERIF, 42, YUNYAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    if ph > 4.8:
        paste(cv, text_img('竖儒 几败而公事', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((ph - 4.8) / 0.3))

def art_l_qiwang(A, cv, t, u):
    ground(A, GROUND)
    liubang(A, 540, GROUND, 210, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)))
    zhang(A, 340, GROUND, 180, dir=1, arm=-8)
    A.d['red'].ellipse((410, GROUND - 16, 470, GROUND + 4), fill=200)
    A.flush(cv)
    paste(cv, text_img('蹑汉王足 · 因而立韩信为齐王', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第四回 运筹帷幄
def art_l_gaixia(A, cv, t, u):
    for k in range(5):
        tent(A, 140 + k * 200, GROUND, 140, 120, layer='mid')
    ground(A, GROUND)
    for j in range(8):
        a = j * 0.8
        person(A, 540 + 380 * math.cos(a), GROUND - 10 * math.sin(a), 90, dir=-1 if math.cos(a) > 0 else 1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('垓下 · 四面楚歌 项羽自刎', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_hanjian(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='huangshi')
    ground(A, GROUND)
    liubang(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 80, ease_out(u / 0.6)))
    A.flush(cv)
    type_in(cv, text_img('运筹策帷帐之中 决胜于千里之外', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('子房功也', 44), 860, 1020, t, t - u + P, rot=6)

def art_l_liu(A, cv, t, u):
    A.d['wash'].rounded_rectangle((110, 860, 970, 1320), radius=20, fill=170)
    q = ease_out(u / (2 * P))
    for i in range(30):
        x = 180 + (i % 10) * 76; y = 920 + (i // 10) * 120
        A.d['huangshi'].rectangle((x, y, x + 60, y + 90), fill=int(200 * (1 - q)) + 30)
    A.d['red'].rectangle((180 + 4 * 76, 920 + 120, 240 + 4 * 76, 1010 + 120), fill=255)
    A.flush(cv)
    paste(cv, text_img('自择齐三万户 · 臣愿封留足矣', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('留', 44), 180 + 4 * 76 + 30, 1100, t, t - u + 2 * P)

def art_l_yongchi(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    liubang(A, 760, GROUND - 30, 200, dir=-1, arm=lerp(20, 100, ease_out((u - P) / 0.5)))
    person(A, 420, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='ink')
    zhang(A, 220, GROUND, 180, dir=1, arm=40)
    A.flush(cv)
    paste(cv, text_img('先封最恨之雍齿 · 群臣乃安', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('雍齿', 54, INK), 860, 1020, t, t - u + P, rot=6)

def art_l_guanzhong(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 140, GROUND), (x, GROUND - 340), (x + 140, GROUND)], fill=180)
    city_wall(A, 360, 720, 1180, gate_x=540, label='长安', layer='yunyan', open_=1.0)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('关中左殽函 右陇蜀 · 金城千里', SERIF, 44, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('定都', 56), 860, 1020, t, t - u + P, rot=6)

def art_l_four(A, cv, t, u):
    """6-beat set piece: 商山四皓 — four white-bearded elders walk in behind the crown prince; the Emperor stares and gives up replacing him."""
    ph = u / P
    palace(A, 540, 1260, 380, layer='huangshi')
    ground(A, GROUND)
    liubang(A, 860, GROUND - 30, 200, dir=-1, arm=lerp(20, 140, clamp((ph - 3) / 0.4)), bow=lerp(0, 20, clamp((ph - 4) / 0.6)))
    person(A, lerp(-60, 520, ease_out(ph / 2.5)), GROUND, 160, dir=1, robe=True, hat='knot', ph=t * 3 if ph < 2.5 else None, arm=-8, layer='ink')
    for i in range(4):
        oldman(A, lerp(-160 - i * 90, 420 - i * 90, ease_out(ph / 2.5)), GROUND, 170, dir=1, ph=t * 3 + i if ph < 2.5 else None, layer='mid')
    A.flush(cv)
    lab = '太子入宫' if ph < 2.5 else ('四人从太子 · 年皆八十有余' if ph < 4 else '羽翼已成 难动矣')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '良为吕后画策 招四皓', t, t - u + P)

def art_l_bigu(A, cv, t, u):
    for k in range(5):
        q = (t * 0.06 + k / 5) % 1
        A.d['wash'].ellipse((lerp(-200, 1200, q) - 200, 900 + k * 60 - 40, lerp(-200, 1200, q) + 200, 900 + k * 60 + 40), fill=150)
    ground(A, GROUND)
    zhang(A, 540, GROUND, 190, dir=1, kneel=True, arm=-8, old=0.6)
    A.flush(cv)
    type_in(cv, text_img('愿弃人间事 欲从赤松子游耳', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('辟谷', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 功成身退
def art_l_death(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ystone(A, 760, 1240, 40, glow=0.6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒 · 并葬黄石', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('文成', 56), 260, 1020, t, t - u + P, rot=-5)

def art_l_looks(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    zhang(A, 800, GROUND, 200, dir=-1, arm=-8, layer='yunyan')
    A.flush(cv)
    type_in(cv, text_img('余以为其人计魁梧奇伟 至见其图 状貌如妇人好女', SERIF, 36, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.6)
    stamp(cv, seal('太史公', 50), 860, 1020, t, t - u + P, rot=6)

def art_l_libai(A, cv, t, u):
    bridge(A, 540, 1200, 640)
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND), fill=120)
    person(A, 540, 1100, 180, dir=1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    A.flush(cv)
    type_in(cv, text_img('我来圯桥上 怀古钦英风', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('李白', 54), 860, 1020, t, t - u + P, rot=6)

def art_l_mousheng(A, cv, t, u):
    for k in range(3):
        A.d['yunyan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    zhang(A, 540, GROUND - 180, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('后世尊为谋圣', SERIF, 48, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_retreat(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    zhang(A, lerp(300, 900, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8, old=0.6)
    A.flush(cv)
    paste(cv, text_img('功遂身退 天之道也', SERIF, 48, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_liuxian(A, cv, t, u):
    A.d['wash'].rounded_rectangle((180, 900, 900, 1300), radius=20, fill=170)
    A.d['huangshi'].ellipse((500, 1060, 580, 1140), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('三万户 不如一个留县', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('留', 60), 540, 1200, t, t - u + P)

def art_l_qianli(A, cv, t, u):
    tent(A, 300, GROUND, 360, 260, layer='yunyan')
    lamp(A, 300, GROUND, 30, t, glow=0.9)
    q = ease_out(u / (1.6 * P))
    for j in range(4):
        rider(A, lerp(500, 1000, q) + j * 30, GROUND - j * 10, 80, dir=1, ph=t * 8 + j, spear=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('运筹帷幄之中 决胜千里之外', SERIF, 46, YUNYAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    ystone(A, 860, 1360, 30, glow=0.5)

def art_l_title(A, cv, t, u):
    bridge(A, 820, 1460, 360)
    ystone(A, 820, 1430, 34, glow=0.5 + 0.3 * math.sin(t))
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    zhang(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '五世相韩'), 48: ('第二回', '圯上老人'), 80: ('第三回', '鸿门'),
            112: ('第四回', '运筹帷幄'), 144: ('第五回', '功成身退')}

CARDS = [
    C(0, 2, 'war', 'num', num='一把铁锤', line='差点砸死秦始皇', art=art_l_hook_hammer),
    C(2, 4, 'life', 'num', num='一只鞋', line='换来一部兵书', art=art_l_hook_shoe),
    C(4, 6, 'empire', 'num', num='三万户', line='他只要一个小县', art=art_l_hook_fief),
    C(6, 8, 'works', 'num', num='运筹帷幄', line='决胜千里', art=art_l_hook_tent),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 五世相韩
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-250, main='生于韩国', sub='相门之后', note='生年不详 约在前二五〇年', art=art_l_birth),
    C(22, 26, 'death', 'card', year=-230, main='韩国灭亡', sub='国破家亡', art=art_l_hanfall),
    C(26, 30, 'night', 'card', year=-229, main='散尽家财', sub='为韩报仇', art=art_l_vow),
    C(30, 34, 'works', 'card', year=-220, main='力士', sub='百二十斤铁椎', art=art_l_strongman),
    C(34, 42, 'war', 'bolangsha', year=-218),
    C(42, 46, 'fate', 'card', year=-218, main='亡匿下邳', sub='隐姓埋名', art=art_l_hide),
    C(46, 48, 'night', 'card', year=-218, main='天下大索', sub='十日', art=art_l_search),
    # ---- 第二回 圯上老人
    C(48, 50, 'fate', 'chapter'),
    C(50, 56, 'life', 'card', year=-217, main='圯上纳履', sub='孺子可教', art=art_l_shoe),
    C(56, 60, 'works', 'card', year=-217, main='太公兵法', sub='王者之师', art=art_l_book),
    C(60, 64, 'night', 'card', year=-212, main='藏匿项伯', sub='一段恩情', art=art_l_xiangbo),
    C(64, 68, 'war', 'card', year=-209, main='天下大乱', sub='揭竿而起', art=art_l_chaos),
    C(68, 72, 'court', 'card', year=-208, main='遇沛公', sub='天授之主', art=art_l_meet),
    C(72, 76, 'empire', 'card', year=-208, main='复立韩王', sub='旧国之梦', art=art_l_hanwang),
    C(76, 80, 'war', 'card', year=-207, main='以利诱将', sub='峣关不战而下', art=art_l_yaoguan),
    # ---- 第三回 鸿门
    C(80, 82, 'court', 'chapter'),
    C(82, 86, 'court', 'card', year=-207, main='入咸阳', sub='还军霸上', art=art_l_xianyang),
    C(86, 92, 'night', 'card', year=-206, main='鸿门宴', sub='千钧一发', art=art_l_hongmen),
    C(92, 96, 'fate', 'card', year=-206, main='烧栈道', sub='示无东意', art=art_l_plank),
    C(96, 100, 'death', 'card', year=-206, main='韩王被杀', sub='彻底归汉', art=art_l_hancheng),
    C(100, 104, 'works', 'card', year=-205, main='下邑之谋', sub='三个人', art=art_l_xiayi),
    C(104, 110, 'court', 'card', year=-204, main='借箸代筹', sub='八不可', art=art_l_chopsticks),
    C(110, 112, 'empire', 'card', year=-203, main='封齐王', sub='踩一脚', art=art_l_qiwang),
    # ---- 第四回 运筹帷幄
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'war', 'card', year=-202, main='垓下', sub='楚歌四起', art=art_l_gaixia),
    C(118, 122, 'empire', 'card', year=-202, main='汉朝建立', sub='高祖论功', art=art_l_hanjian),
    C(122, 126, 'court', 'card', year=-201, main='封留侯', sub='辞三万户', art=art_l_liu),
    C(126, 130, 'life', 'card', year=-201, main='先封雍齿', sub='安定人心', art=art_l_yongchi),
    C(130, 134, 'empire', 'card', year=-200, main='定都关中', sub='金城千里', art=art_l_guanzhong),
    C(134, 140, 'court', 'card', year=-195, main='商山四皓', sub='保太子', art=art_l_four),
    C(140, 144, 'fate', 'card', year=-194, main='辟谷', sub='从赤松子游', art=art_l_bigu),
    # ---- 第五回 功成身退
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=-186, main='留侯去世', sub='谥文成', art=art_l_death),
    C(150, 154, 'works', 'card', year=-91, main='太史公曰', sub='貌如好女', art=art_l_looks),
    C(154, 158, 'life', 'card', year=745, main='李白怀古', sub='圯桥之上', art=art_l_libai),
    C(158, 162, 'empire', 'card', year=745, main='谋圣', sub='后世尊称', art=art_l_mousheng),
    C(162, 166, 'fate', 'card', year=745, main='激流勇退', sub='天之道', art=art_l_retreat),
    C(166, 168, 'court', 'card', year=745, main='只要留县', sub='知足', art=art_l_liuxian),
    C(168, 170, 'end', 'card', year=745, main='决胜千里', sub='运筹帷幄之中', art=art_l_qianli),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾肆', col=YUNYAN, acc=HUANGSHI, born=-250, died=-186, age0=-250,
    born_lab='约前250年', died_lab='前186年', years_txt='约公元前250 — 前186',
    hook_q='他刺杀过秦始皇 · 为什么最后选择归隐？',
    name_line='张良 · 字子房', name='张良', seal='留侯', title_art=art_l_title,
    q1='千古谋圣？', q2='明哲保身？',
    end_art=art_l_legacy, end_big='功成身退', end_seal='留侯',
    end_l1='他刺杀过皇帝 又帮人得了天下', end_l2='最后只想随赤松子去云游',
    end_brush='运筹帷幄之中', end_ask='功成之后 你会选择退吗？评论区聊聊', next='萧何'),
    scenes=dict(chapter=scene_chapter, bolangsha=scene_bolangsha))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
