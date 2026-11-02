"""千古人物志 · 第叁拾贰集 · 杜甫 (712–770)
Look: 秋草赭黄 + 烽烟灰, 茅草 (thatch) corner borders, a 茅屋 chapter card: a whole hut, then the roof tears away a
little more each chapter until only the frame remains — then a lamp is lit inside.
Set pieces: 8-beat 望岳, custom 8-beat scene 'sanli' (三吏三别 six poems/six scenes), 6-beat 长安十年,
6-beat 春望, 8-beat 茅屋为秋风所破, 6-beat 登高, 6-beat 湘江孤舟.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_libai as Lb2          # engine + helpers (previous episode)
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
from render_libai import li, wine_jar

F.RIPPLE = False
STRAW = (176, 138, 62)              # 秋草赭黄
SMOKE = (106, 106, 112)             # 烽烟灰
S.LAYERS.append(('straw', STRAW, 0.88, 1.0))
S.LAYERS.append(('smoke', SMOKE, 0.75, 2.4))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='甫', life='杜', court='唐', night='乱', war='烽', empire='唐', works='诗', fate='秋', death='舟', end='圣')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'court', 'empire'):
    G.THEMES[k]['part'] = 'petal'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (STRAW, 220, (W * 0.5, 820))
G.THEMES['war']['sun'] = (ZHU, 220, (W * 0.5, 760))
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (STRAW, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

GRASS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(GRASS)
_r = random.Random(21)
for _k in range(60):
    _x = 60 + _r.uniform(0, W - 120)
    if 240 < _x < 840: continue
    _h = _r.uniform(40, 120)
    _d.line((_x, 1480, _x + _r.uniform(-20, 20), 1480 - _h), fill=STRAW + (60,), width=2)
MTN_COL = {'night': (40, 38, 36), 'death': (62, 60, 58), 'war': (100, 64, 48), 'fate': (110, 92, 66)}
def draw_background(t, theme):
    """秋野: low autumn ridges, dry grass tufts at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 186, 168), (162, 146, 118), MTN_COL.get(theme, (124, 106, 76))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(GRASS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """茅草: a bundle of thatch straws tied at each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    col = STRAW + (220,)
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SMOKE + (200,), width=3); d.line((x, y, x, y + sy * 180), fill=SMOKE + (200,), width=3)
        for k in range(7):
            a = 0.2 + k * 0.17
            d.line((x + sx * 12, y + sy * 12, x + sx * 90 * math.cos(a), y + sy * 90 * math.sin(a)), fill=col, width=3)
        d.line((x + sx * 30, y + sy * 46, x + sx * 46, y + sy * 30), fill=SMOKE + (230,), width=5)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def du(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, cane=False, **kw):
    """杜甫: thin, stooping with age (old 0..1), plain head-cloth, sometimes a cane."""
    b = bow + 18 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.07 * h, y - 1.02 * h, x + 0.07 * h, y - 0.9 * h), 180, 360, fill=255)
    if cane and not kneel and not kw.get('fall'):
        d.line((x + dir * 0.18 * h, y - 0.55 * h, x + dir * 0.24 * h, y), fill=255, width=max(3, int(0.02 * h)))
    if old > 0.3 and not kneel:
        A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.86 * h), (x + dir * 0.08 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
    return hand

def hut(A, cx, base, w, h, roof=1.0, lit=0.0, t=0.0):
    """thatched hut; roof 1 = intact, 0 = bare frame."""
    A.d['straw'].rectangle((cx - w / 2, base - 0.55 * h, cx + w / 2, base), fill=200)
    A.d['ink'].rectangle((cx - 0.12 * w, base - 0.42 * h, cx + 0.12 * w, base), fill=255)
    A.d['ink'].line((cx - 0.62 * w, base - 0.5 * h, cx, base - h, cx + 0.62 * w, base - 0.5 * h), fill=255, width=6)
    n = 14
    for k in range(n):
        if k / n >= roof: break
        f = k / (n - 1)
        x0 = lerp(cx - 0.62 * w, cx + 0.62 * w, f)
        y0 = base - 0.5 * h - (1 - abs(2 * f - 1)) * 0.5 * h
        A.d['straw'].polygon([(x0 - 0.06 * w, y0 + 6), (x0 + 0.06 * w, y0 + 6), (x0 + 0.04 * w, y0 + 0.16 * h), (x0 - 0.05 * w, y0 + 0.16 * h)], fill=255)
    if lit > 0:
        lamp(A, cx, base - 0.02 * h, 0.12 * h, t, glow=lit)

def straw_bits(A, t, n=24, strength=1.0, seed=3):
    r = random.Random(seed)
    for k in range(n):
        q = (t * 0.6 * r.uniform(0.6, 1.4) + k / n) % 1
        x = lerp(200, 1100, q) + r.uniform(-60, 60); y = 900 + r.uniform(-200, 200) + 80 * math.sin(q * 8 + k)
        a = r.uniform(0, 3.14)
        A.d['straw'].line((x, y, x + 30 * math.cos(a), y + 30 * math.sin(a)), fill=int(220 * strength), width=3)

# ================================================================ chapter card
CH = {16: (1.0, 0.0), 48: (0.75, 0.0), 80: (0.45, 0.0), 112: (0.15, 0.0), 144: (0.15, 1.0)}
def art_hut_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    roof, lit = CH.get(kb, (0.75, 0.0))
    hut(A, 540, 1220, 440, 380, roof=roof, lit=lit * ease_out(u / P), t=t)
    if kb in (80, 112):
        straw_bits(A, t, n=16, strength=0.8)
    ground(A, 1220)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_hut_chapter)
    ink_in(cv, text_img(no, SERIF, 56, STRAW, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_d_hook_poems(A, cv, t, u):
    ground(A, GROUND)
    n = min(140, int(clamp(u / (1.6 * P)) * 140) + 1)
    for i in range(n):
        x = 100 + (i % 20) * 45; y = GROUND - 26 - (i // 20) * 36
        A.d['straw' if i % 13 else 'smoke'].rectangle((x - 14, y - 26, x + 14, y), fill=255)

def art_d_hook_roof(A, cv, t, u):
    hut(A, 540, GROUND, 460, 380, roof=lerp(1, 0.2, ease_out(u / (1.6 * P))))
    straw_bits(A, t, n=20)
    ground(A, GROUND)

def art_d_hook_ten(A, cv, t, u):
    city_wall(A, 120, 960, 1100, gate_x=540, label='长安', layer='mid')
    ground(A, GROUND)
    du(A, lerp(200, 880, (u / (1.8 * P)) % 1), GROUND, 200, dir=1, ph=t * 4, arm=-8)

def art_d_hook_boat(A, cv, t, u):
    river(A, 1220, t, rows=3, amp=4, speed=0.8)
    boat(A, 540, 1260, 120, t, sail=False)
    du(A, 540, 1230, 140, dir=1, old=1.0, kneel=True, bow=20, arm=-8)

# ================================================================ 第一回 裘马轻狂
def art_d_birth(A, cv, t, u):
    palace(A, 720, GROUND, 380, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        sitter(A, 200 + k * 140, GROUND, 140 - k * 20, dir=1, bow=15)
    A.flush(cv)
    stamp(cv, seal('杜审言', 44, INK), 200, 1080, t, t - u + 0.4)
    stamp(cv, seal('巩县', 54), 760, 880, t, t - u + P, rot=6)

def art_d_jujube(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].line((580, GROUND, 600, 940), fill=255, width=18)
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.45
        A.d['ink'].line((600, 980, 600 + 200 * math.cos(a), 980 + 140 * math.sin(a)), fill=255, width=6)
    for k in range(14):
        A.d['red'].ellipse((480 + (k * 37) % 240 - 10, 880 + (k * 23) % 120 - 10, 480 + (k * 37) % 240 + 10, 880 + (k * 23) % 120 + 10), fill=255)
    y = GROUND - 200 * abs(math.sin(t * 3))
    person(A, 420, y, 140, dir=1, robe=False, hat='knot', arm=170, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('一日上树能千回', SERIF, 48, STRAW, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_d_fenghuang(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 340, layer='straw')
    sitter(A, 300, GROUND, 180, dir=1, bow=15)
    A.flush(cv)
    type_in(cv, text_img('七龄思即壮 开口咏凤凰', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

def art_d_wuyue(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 260), (x + 200, GROUND)], fill=150)
    A.d['ocean'].line([(60, 1340), (540, 1300), (1020, 1340)], fill=150, width=28)
    boat(A, lerp(200, 800, ease_out(u / (3 * P))), 1340, 90, t, sail=True)
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('漫游吴越', 46), 860, 880, t, t - u + P, rot=6)

def art_d_failed(A, cv, t, u):
    for r in range(3):
        for c2 in range(6):
            x = 200 + c2 * 140; y = 960 + r * 120
            A.d['mid'].rectangle((x - 50, y, x + 50, y + 90), fill=220)
            A.d['ink'].rectangle((x - 50, y, x + 50, y + 90), outline=255, width=4)
    ground(A, GROUND)
    du(A, 860, GROUND, 200, dir=-1, arm=-8)
    A.flush(cv)
    stamp(cv, seal('落第', 60, INK), 540, 880, t, t - u + P, rot=-6)

def art_d_wangyue(A, cv, t, u):
    """8-beat set piece: 望岳 — 泰山 rises out of the mist; he climbs; at the top all hills shrink below."""
    ph = u / P
    if ph < 5:
        h = lerp(300, 560, ease_out(ph / 3))
        A.d['mid'].polygon([(120, GROUND), (540, GROUND - h), (960, GROUND)], fill=210)
        for k in range(12):
            q = (t * 0.2 + k / 12) % 1
            A.d['wash'].ellipse((100 + (k * 79) % 880 - 60, lerp(GROUND - 60, GROUND - 300, q) - 14, 100 + (k * 79) % 880 + 60, lerp(GROUND - 60, GROUND - 300, q) + 14), fill=int(200 * math.sin(math.pi * q)))
        f = clamp((ph - 2) / 3)
        du(A, lerp(200, 520, f), lerp(GROUND, GROUND - h + 40, f), 90, dir=1, ph=t * 4, arm=-8)
        ground(A, GROUND)
    else:
        for k in range(8):
            x = 80 + k * 130
            A.d['mid'].polygon([(x - 80, GROUND), (x, GROUND - 60 - 20 * (k % 3)), (x + 80, GROUND)], fill=180)
        A.d['ink'].polygon([(300, GROUND), (540, 1100), (780, GROUND)], fill=255)
        du(A, 540, 1100, 200, dir=1, arm=lerp(40, 170, ease_out((ph - 5) / 0.8)))
    A.flush(cv)
    if ph >= 1:
        type_in(cv, text_img('岱宗夫如何 齐鲁青未了', SERIF, 44, STRAW, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + P, 0.5)
    if ph >= 5:
        type_in(cv, text_img('会当凌绝顶 一览众山小', SERIF, 50, ZHU, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + 5 * P, 0.5)

def art_d_meet_li(A, cv, t, u):
    ground(A, GROUND)
    li(A, 360, GROUND, 240, dir=1, cup=True, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    du(A, 720, GROUND, 220, dir=-1, arm=lerp(20, 80, ease_out(u / P)))
    wine_jar(A, 540, GROUND, 50)
    A.flush(cv)
    type_in(cv, text_img('白也诗无敌 飘然思不群', SERIF, 46, STRAW, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.6, 0.5)

# ================================================================ 第二回 长安十年
def art_d_changan(A, cv, t, u):
    """6-beat: 长安十年 — knocking at rich gates, eating leftovers; years tick 一 → 十."""
    ph = u / P
    yr = min(10, int(ph * 10 / 5) + 1)
    palace(A, 720, GROUND, 420, layer='mid')
    ground(A, GROUND)
    du(A, 480, GROUND, 210, dir=1, bow=lerp(0, 30, 0.5 + 0.5 * math.sin(t * 2)), arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 2)), old=yr / 20)
    for k in range(int(yr / 2)):
        A.d['mid'].ellipse((160 + k * 50, GROUND - 20, 196 + k * 50, GROUND), fill=200)
    A.flush(cv)
    paste(cv, text_img(f'困居长安 第{cn_num(yr)}年', SERIF, 50, STRAW, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)
    if ph >= 3:
        type_in(cv, text_img('残杯与冷炙 到处潜悲辛', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + 3 * P, 0.5)

def art_d_fake_exam(A, cv, t, u):
    palace(A, 540, 1140, 540, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 30, 220, dir=1, robe=True, hat='crown', arm=lerp(20, 120, ease_out(u / P)), layer='ink')
    for k in range(6):
        person(A, 140 + k * 60 if k < 3 else 760 + (k - 3) * 70, GROUND, 120, dir=1 if k < 3 else -1, robe=True, hat='knot', bow=40, arm=-8, layer='mid')
    A.flush(cv)
    stamp(cv, seal('李林甫', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('野无遗贤', SERIF, 52, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_fu(A, cv, t, u):
    palace(A, 540, 1140, 540, layer='straw')
    ground(A, GROUND)
    du(A, 360, GROUND, 210, dir=1, kneel=True, bow=30, arm=90)
    scroll(A, 560, 1080, 220, 70, u / 0.6)
    A.flush(cv)
    stamp(cv, seal('三大礼赋', 44), 860, 880, t, t - u + P, rot=6)

def art_d_beauties(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=4, speed=1)
    ground(A, 1260, x0=60, x1=W - 60)
    for k in range(5):
        x = lerp(-100, 980, ((t * 0.08 + k * 0.2) % 1))
        person(A, x, 1260, 170, dir=1, robe=True, hat='knot', female=True, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2 + k)), layer='apricot' if k % 2 else 'ink')
    A.flush(cv)
    stamp(cv, seal('丽人行', 50), 860, 880, t, t - u + P, rot=6)

def art_d_chariots(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        carriage(A, lerp(-200, 900, ((t * 0.12 + k * 0.25) % 1)), GROUND, 110, dir=1, wheel=t * 6, ph=t * 8, layer='ink')
    for k in range(5):
        person(A, 160 + k * 120, GROUND - 40, 120, dir=-1, robe=True, hat='knot', female=k % 2 == 0, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 6 + k)), layer='mid')
    A.flush(cv)
    type_in(cv, text_img('车辚辚 马萧萧', SERIF, 52, SMOKE, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, 0.4)

def art_d_frozen(A, cv, t, u):
    for k in range(50):
        q = (t * 0.5 + k / 50) % 1
        x = 80 + (k * 19) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=230)
    palace(A, 760, GROUND, 400, layer='straw')
    ground(A, GROUND)
    person(A, 260, GROUND, 120, dir=1, robe=False, hat='knot', fall=-85, arm=-8, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('朱门酒肉臭', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.4, 0.4)
    type_in(cv, text_img('路有冻死骨', SERIF, 52, INK, 'Black', bleed=False, spacing=8), W / 2, 900, t, t - u + 1.5 * P, 0.4)

def art_d_son(A, cv, t, u):
    hut(A, 640, GROUND, 360, 300, roof=0.9)
    ground(A, GROUND)
    du(A, lerp(1000, 820, ease_out(u / P)), GROUND, 200, dir=-1, arm=-8)
    for k in range(3):
        person(A, 560 + k * 40, GROUND, 120 - k * 20, dir=1, robe=True, hat='knot', female=k == 0, kneel=True, bow=50, arm=100, layer='ink')
    A.flush(cv)
    paste(cv, text_img('幼子饿已卒', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第三回 安史之乱
def art_d_rebellion(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        rider(A, lerp(-200, 1100, ((t * 0.15 + k * 0.1) % 1)), GROUND - (k % 2) * 40, 110, 1, t * 12 + k, layer='ink', spear=True)
    flames(A, 540, GROUND, 900, 240 * ease_out(u / (1.5 * P)), t, n=8, seed=4, smoke=True)
    A.flush(cv)
    stamp(cv, seal('安禄山', 50, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_d_captured(A, cv, t, u):
    city_wall(A, 120, 960, 1100, gate_x=540, label='长安', layer='smoke')
    flames(A, 540, 1100, 800, 160, t, n=6, seed=9, smoke=True)
    ground(A, GROUND)
    du(A, 540, GROUND, 200, dir=1, arm=-8)
    for k in range(2):
        person(A, 380 + k * 320, GROUND, 190, dir=1 if k == 0 else -1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('陷贼', 56, INK), 860, 860, t, t - u + P, rot=6)

def art_d_chunwang(A, cv, t, u):
    """6-beat: 春望 — ruins of 长安; grass grows over the streets; spring flowers that make him weep; he looks at his thin hair."""
    ph = u / P
    palace(A, 540, GROUND, 620, collapse=0.6, layer='smoke')
    g = ease_out(ph / 3)
    for k in range(30):
        x = 80 + k * 32
        A.d['grass'].line((x, GROUND, x + 6 * math.sin(t + k), GROUND - 60 * g - 20 * (k % 3) * g), fill=230, width=4)
    for k in range(int(g * 10)):
        A.d['apricot'].ellipse((140 + k * 86 - 12, GROUND - 90 - 12, 140 + k * 86 + 12, GROUND - 90 + 12), fill=230)
    du(A, 860, GROUND, 220, dir=-1, arm=lerp(40, 160, ease_out((ph - 3.5) / 1)), old=0.4)
    ground(A, GROUND)
    A.flush(cv)
    for i, ln in enumerate(('国破山河在', '城春草木深', '感时花溅泪', '恨别鸟惊心')):
        type_in(cv, text_img(ln, SERIF, 40, ZHU if i == 0 else INK, 'Black', bleed=False, vertical=True, spacing=2), 380 - i * 60, 960, t, t - u + 0.3 + i * 0.6 * P, 0.4)
    if ph >= 4:
        paste(cv, text_img('白头搔更短 浑欲不胜簪', SERIF, 42, STRAW, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_d_escape(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 360), (x + 150, GROUND)], fill=200)
    ground(A, GROUND)
    du(A, lerp(100, 900, ease_out(u / (3 * P))), GROUND, 180, dir=1, ph=t * 6, arm=20)
    A.flush(cv)
    stamp(cv, seal('凤翔', 54), 860, 880, t, t - u + 2 * P, rot=6)
    paste(cv, text_img('麻鞋见天子', SERIF, 50, STRAW, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_d_shiyi(A, cv, t, u):
    palace(A, 540, 1140, 540, layer='straw')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((u - P) / 0.5)), layer='ink')
    du(A, 360, GROUND, 210, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('左拾遗', 54), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('救房琯', 46, INK), 860, 1000, t, t - u + 1.6 * P, rot=6)

SANLI = [('石壕吏', '有吏夜捉人'), ('新安吏', '中男绝短小'), ('潼关吏', '大城铁不如'),
         ('新婚别', '暮婚晨告别'), ('垂老别', '老妻卧路啼'), ('无家别', '何以为蒸黎')]
def scene_sanli(cv, t, c, k):
    """8-beat custom scene: 三吏三别 — one poem per beat: a night arrest, a boy conscript, a wall, a bride, an old man, an
    empty village; each with its seal; the poet watches from the side."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    i = min(5, int(ph * 6 / 7.2))
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if i == 0:
        for k2 in range(30):
            A.d['wash'].ellipse((80 + (k2 * 37) % 920 - 2, 660 + (k2 * 53) % 300 - 2, 80 + (k2 * 37) % 920 + 2, 660 + (k2 * 53) % 300 + 2), fill=255)
        hut(A, 600, GROUND, 320, 280, roof=0.9)
        person(A, 760, GROUND, 190, dir=-1, robe=False, hat='helmet', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 5)), layer='ink')
        person(A, 560, GROUND, 160, dir=1, robe=True, hat='knot', female=True, bow=30, arm=100, layer='mid')
    elif i == 1:
        for k2 in range(6):
            person(A, 300 + k2 * 80, GROUND, 110 + (k2 % 2) * 10, dir=1, robe=False, hat='knot', ph=t * 4 + k2, arm=20, layer='ink')
        person(A, 160, GROUND, 160, dir=1, robe=True, hat='knot', female=True, arm=150, layer='mid')
    elif i == 2:
        city_wall(A, 260, 960, 1060, gate_x=610, label='潼关', layer='smoke')
        person(A, 420, GROUND, 180, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    elif i == 3:
        person(A, 460, GROUND, 190, dir=1, robe=False, hat='helmet', spear=True, ph=t * 3, arm=30, layer='ink')
        person(A, 620, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='red')
    elif i == 4:
        person(A, 460, GROUND, 200, dir=1, robe=False, hat='helmet', bow=25, spear=True, arm=30, layer='ink')
        person(A, 680, GROUND, 60, dir=-1, robe=True, hat='knot', female=True, fall=-85, arm=60, layer='mid')
    else:
        for k2 in range(4):
            hut(A, 220 + k2 * 220, GROUND, 160, 140, roof=0.3)
        person(A, 860, GROUND, 170, dir=-1, robe=False, hat='knot', arm=-8, layer='ink')
    du(A, 140, GROUND, 150, dir=1, old=0.5, arm=-8)
    A.flush(cv)
    for j, (nm, _) in enumerate(SANLI):
        x = 170 + j * 148
        if j <= i:
            stamp(cv, seal(nm, 28, ZHU if j == i else STRAW), x, 830, t, s0 + j * 1.2 * P)
    fx = Art()
    chars_in(cv, fx, '三吏三别', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=88)
    fx.flush(cv)
    paste(cv, text_img(SANLI[i][1], SERIF, 48, SMOKE, 'Black', bleed=False, spacing=6), W / 2, 575, 1, 1)
    paste(cv, text_img('公元七五九年 · 诗史', SERIF, 42, STRAW, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

# ================================================================ 第四回 草堂岁月
def art_d_quit(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].rectangle((300, GROUND - 60, 420, GROUND - 40), fill=255)
    du(A, lerp(500, 900, ease_out(u / (3 * P))), GROUND, 200, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('弃官', 56, INK), 360, 880, t, t - u + 0.4, rot=-5)

def art_d_shu_road(A, cv, t, u):
    for k in range(6):
        x = 120 + k * 170
        A.d['mid'].polygon([(x - 130, GROUND), (x, GROUND - 480 - 80 * (k % 2)), (x + 130, GROUND)], fill=200)
    pts = [(x, GROUND - 180 - 90 * math.sin(x / 120)) for x in range(80, W - 79, 20)]
    A.d['straw'].line(pts, fill=230, width=8)
    i = min(len(pts) - 1, int(clamp(u / (3 * P)) * (len(pts) - 1)))
    du(A, pts[i][0], pts[i][1], 100, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('入蜀', 56), 860, 880, t, t - u + P, rot=6)

def art_d_caotang(A, cv, t, u):
    hut(A, 600, GROUND, 400, 340, roof=ease_out(u / (2.5 * P)))
    for k in range(6):
        x = 160 + k * 40
        A.d['grass'].line((x, GROUND, x + 8 * math.sin(t + k), GROUND - 300), fill=220, width=8)
    ground(A, GROUND)
    du(A, 880, GROUND, 190, dir=-1, arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    stamp(cv, seal('浣花溪', 50), 260, 880, t, t - u + 0.4, rot=-5)

def art_d_rain(A, cv, t, u):
    for k in range(60):
        q = (t * 0.8 + k / 60) % 1
        x = 80 + (k * 17) % 920
        A.d['wash'].line((x, lerp(620, 1420, q), x - 4, lerp(620, 1420, q) + 18), fill=180, width=2)
    hut(A, 600, GROUND, 360, 300, roof=1.0, lit=0.5, t=t)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('好雨知时节 当春乃发生', SERIF, 46, STRAW, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

def art_d_storm(A, cv, t, u):
    """8-beat set piece: 茅屋为秋风所破 — the autumn gale strips the roof; village boys run off with armfuls of thatch;
    rain pours through all night; he dreams of a vast mansion sheltering all the poor."""
    ph = u / P
    if ph < 5.5:
        roof = lerp(1, 0.1, ease_out(ph / 3))
        hut(A, 600, GROUND, 400, 340, roof=roof)
        straw_bits(A, t * 2, n=40, strength=1.0)
        ground(A, GROUND)
        if 1.5 <= ph < 4:
            for k in range(3):
                person(A, lerp(500, 1100, ease_out((ph - 1.5) / 2)) + k * 60, GROUND, 110, dir=1, robe=False, hat='knot', load=True, ph=t * 8 + k, arm=160, layer='mid')
        du(A, 260, GROUND, 200, dir=1, old=0.7, cane=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4)))
        if ph >= 3.5:
            for k in range(60):
                q = (t * 1.0 + k / 60) % 1
                x = 80 + (k * 17) % 920
                A.d['wash'].line((x, lerp(620, 1420, q), x - 5, lerp(620, 1420, q) + 22), fill=200, width=2)
    else:
        q = ease_out((ph - 5.5) / 1.5)
        for k in range(5):
            x = 540 + (k - 2) * 180 * q
            A.d['straw'].rectangle((x - 80, GROUND - 260 * q, x + 80, GROUND), fill=200)
        A.d['ink'].polygon([(540 - 520 * q, GROUND - 260 * q), (540 + 520 * q, GROUND - 260 * q), (540, GROUND - 420 * q)], fill=255)
        for k in range(10):
            person(A, 140 + k * 90, GROUND, 90, dir=1, robe=True, hat='knot', arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
        ground(A, GROUND)
    A.flush(cv)
    if ph < 3:
        type_in(cv, text_img('八月秋高风怒号 卷我屋上三重茅', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.6)
    elif ph < 5.5:
        paste(cv, text_img('床头屋漏无干处', SERIF, 48, SMOKE, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 3) / 0.4))
    else:
        type_in(cv, text_img('安得广厦千万间', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 5.5 * P, 0.5)
        type_in(cv, text_img('大庇天下寒士俱欢颜', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + 6.5 * P, 0.5)

def art_d_yanwu(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=False, hat='helmet', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t)), layer='ink')
    du(A, 360, GROUND, 210, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('严武', 54), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('工部员外郎', 38), 260, 880, t, t - u + 1.6 * P, rot=-5)

def art_d_good_news(A, cv, t, u):
    river(A, 1260, t, rows=3, amp=5, speed=2)
    ground(A, 1260, x0=60, x1=480)
    du(A, 300, 1260, 220, dir=1, arm=lerp(60, 170, 0.5 + 0.5 * math.sin(t * 6)), arm2=lerp(-60, -170, 0.5 + 0.5 * math.sin(t * 6 + 1)))
    boat(A, 780, 1290, 120, t, sail=True)
    A.flush(cv)
    type_in(cv, text_img('剑外忽传收蓟北', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('初闻涕泪满衣裳', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

# ================================================================ 第五回 漂泊西南
def art_d_kuizhou(A, cv, t, u):
    for k, x in enumerate((140, 940)):
        A.d['mid'].polygon([(x - 120, GROUND), (x - 40, 820), (x + 40, 840), (x + 120, GROUND)], fill=210)
    river(A, 1240, t, rows=4, amp=8, speed=3)
    ground(A, 1240, x0=200, x1=500)
    du(A, 360, 1240, 170, dir=1, old=0.8, cane=True, arm=40)
    A.flush(cv)
    stamp(cv, seal('夔州', 56), 760, 880, t, t - u + P, rot=6)

def art_d_denggao(A, cv, t, u):
    """6-beat: 登高 — on a high terrace in autumn wind; leaves stream down; the river rolls on below; he sets down his cup."""
    ph = u / P
    river(A, 1300, t, rows=3, amp=6, speed=2.6)
    A.d['ink'].polygon([(200, 1300), (200, 1100), (640, 1100), (700, 1300)], fill=255)
    du(A, 440, 1100, 200, dir=1, old=1.0, cane=True, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t)))
    for k in range(40):
        q = (t * 0.5 + k / 40) % 1
        x = lerp(1000, 100, q) + 60 * math.sin(k)
        y = lerp(700, 1300, q) + 40 * math.sin(q * 8 + k)
        A.d['straw'].ellipse((x - 8, y - 4, x + 8, y + 4), fill=int(230 * (1 - q * 0.5)))
    for k in range(4):
        crow(A, 760 + k * 50, 800 + 20 * math.sin(t + k), 26, t * 5 + k)
    A.flush(cv)
    type_in(cv, text_img('无边落木萧萧下', SERIF, 48, STRAW, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('不尽长江滚滚来', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

def art_d_ill(A, cv, t, u):
    hut(A, 560, GROUND, 380, 320, roof=0.6, lit=0.4, t=t)
    ground(A, GROUND)
    du(A, 860, GROUND, 190, dir=-1, old=1.0, cane=True, arm=-8)
    A.flush(cv)
    paste(cv, text_img('耳聋 齿落 右臂偏枯', SERIF, 46, SMOKE, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_yueyang(A, cv, t, u):
    river(A, 1180, t, rows=5, amp=8, speed=1.4)
    A.d['ink'].rectangle((420, 900, 660, 1060), fill=255)
    A.d['ink'].polygon([(380, 900), (700, 900), (540, 820)], fill=255)
    A.d['ink'].polygon([(400, 980), (680, 980), (540, 930)], fill=255)
    boat(A, 760, 1240, 100, t, sail=False)
    du(A, 760, 1210, 120, dir=-1, old=1.0, kneel=True, bow=20, arm=-8)
    A.flush(cv)
    stamp(cv, seal('岳阳楼', 50), 260, 880, t, t - u + 0.4, rot=-5)
    type_in(cv, text_img('亲朋无一字 老病有孤舟', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, t, t - u + P, 0.5)

def art_d_last_boat(A, cv, t, u):
    """6-beat: 湘江孤舟 — winter on the 湘江; a small boat drifts; the lamp aboard dims and goes out."""
    ph = u / P
    for k in range(40):
        q = (t * 0.3 + k / 40) % 1
        x = 80 + (k * 23) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=200)
    river(A, 1220, t, rows=3, amp=3, speed=0.5)
    x = lerp(300, 760, ease_out(ph / 5.5))
    boat(A, x, 1260, 120, t, sail=False)
    A.d['straw'].chord((x - 60, 1180, x + 60, 1260), 180, 360, fill=255)
    lamp(A, x + 70, 1240, 30, t, glow=clamp(1 - (ph - 3.5) / 1.5))
    A.flush(cv)
    paste(cv, text_img('卒于舟中 · 年五十八', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 3.5) / 0.4))

def art_d_reburial(A, cv, t, u):
    A.d['mid'].chord((380, 1200, 700, GROUND + 160), 180, 360, fill=230)
    ground(A, GROUND)
    for k in range(3):
        person(A, 800 + k * 60, GROUND, 160 - k * 10, dir=-1, robe=True, hat='knot', bow=30, arm=-8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('偃师', 54), 540, 1100, t, t - u + P)
    paste(cv, text_img('四十三年后 孙儿迁葬', SERIF, 46, STRAW, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_d_shisheng(A, cv, t, u):
    ground(A, GROUND)
    hut(A, 540, GROUND, 400, 340, roof=1.0, lit=1.0, t=t)
    for k in range(6):
        person(A, 120 + k * 60 if k < 3 else 800 + (k - 3) * 60, GROUND, 130, dir=1 if k < 3 else -1, robe=True, hat='knot', bow=20, arm=40, layer='mid')
    A.flush(cv)
    paste(cv, text_img('诗圣 · 诗史', SERIF, 52, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))

def art_d_legacy(A, cv, t, u):
    hut(A, 860, 1440, 200, 170, roof=0.15, lit=1.0, t=t)

def art_d_title(A, cv, t, u):
    hut(A, 820, 1460, 340, 300, roof=0.8)
    du(A, 400, 1460, 680, dir=1, old=0.3, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '裘马轻狂'), 48: ('第二回', '长安十年'), 80: ('第三回', '安史之乱'),
            112: ('第四回', '草堂岁月'), 144: ('第五回', '漂泊西南')}

CARDS = [
    C(0, 2, 'works', 'num', num='一千四百首', line='一部唐朝衰落史', art=art_d_hook_poems),
    C(2, 4, 'fate', 'num', num='屋顶被风掀了', line='他想的是天下寒士', art=art_d_hook_roof),
    C(4, 6, 'court', 'num', num='长安十年', line='求官不得', art=art_d_hook_ten),
    C(6, 8, 'death', 'num', num='一叶孤舟', line='死在漂泊途中', art=art_d_hook_boat),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=712, main='生于巩县', sub='祖父杜审言 · 初唐诗人', note='奉儒守官 未坠素业', art=art_d_birth),
    C(22, 26, 'works', 'card', year=719, main='七岁咏凤', sub='早慧', art=art_d_fenghuang),
    C(26, 30, 'life', 'card', year=726, main='上树千回', sub='少年顽皮', note='忆年十五心尚孩', art=art_d_jujube),
    C(30, 34, 'works', 'card', year=731, main='漫游吴越', sub='南下江南 · 数年', art=art_d_wuyue),
    C(34, 38, 'night', 'card', year=735, main='落第', sub='洛阳应试不第', art=art_d_failed),
    C(38, 46, 'works', 'card', year=736, main='望岳', sub='游齐赵 · 登泰山', note='作年 一说', art=art_d_wangyue),
    C(46, 48, 'life', 'card', year=744, main='遇见李白', sub='洛阳相遇 · 相约同游', art=art_d_meet_li),
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'court', 'card', year=746, main='困居长安', sub='奔走权门 · 处处碰壁', art=art_d_changan),
    C(56, 60, 'night', 'card', year=747, main='野无遗贤', sub='李林甫操纵考试 · 无一人录取', art=art_d_fake_exam),
    C(60, 64, 'empire', 'card', year=751, main='献三大礼赋', sub='玄宗奇之 · 却仍待诏', art=art_d_fu),
    C(64, 68, 'war', 'card', year=751, main='兵车行', sub='征夫与家人诀别', note='作年 一说', art=art_d_chariots),
    C(68, 72, 'life', 'card', year=753, main='丽人行', sub='讽刺杨氏兄妹奢华', art=art_d_beauties),
    C(72, 76, 'night', 'card', year=755, main='朱门酒肉', sub='赴奉先 · 一路所见', art=art_d_frozen),
    C(76, 80, 'death', 'card', year=755, main='幼子饿死', sub='入门闻号啕', art=art_d_son),
    C(80, 82, 'war', 'chapter'),
    C(82, 86, 'war', 'card', year=755, main='安史之乱', sub='渔阳鼙鼓动地来', art=art_d_rebellion),
    C(86, 90, 'night', 'card', year=756, main='陷贼长安', sub='投奔途中被俘', art=art_d_captured),
    C(90, 96, 'fate', 'card', year=757, main='春望', sub='身陷长安的春天', art=art_d_chunwang),
    C(96, 100, 'works', 'card', year=757, main='逃奔凤翔', sub='衣袖露两肘', art=art_d_escape),
    C(100, 104, 'court', 'card', year=757, main='左拾遗', sub='上疏救房琯 · 触怒肃宗', art=art_d_shiyi),
    C(104, 112, 'war', 'sanli', year=759),
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'fate', 'card', year=759, main='弃官', sub='关中饥荒 · 弃官西行', art=art_d_quit),
    C(118, 122, 'works', 'card', year=759, main='入蜀', sub='蜀道之上 · 携家带口', art=art_d_shu_road),
    C(122, 126, 'life', 'card', year=760, main='浣花草堂', sub='成都城西 · 亲友资助', art=art_d_caotang),
    C(126, 130, 'life', 'card', year=761, main='春夜喜雨', sub='难得安稳的日子', art=art_d_rain),
    C(130, 138, 'night', 'card', year=761, main='茅屋秋风', sub='屋漏夜雨 · 心怀天下', note='茅屋为秋风所破歌', art=art_d_storm),
    C(138, 142, 'empire', 'card', year=763, main='闻官军收', sub='一生最快乐的诗', art=art_d_good_news),
    C(142, 144, 'court', 'card', year=764, main='严武幕府', sub='检校工部员外郎', art=art_d_yanwu),
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'fate', 'card', year=766, main='寓居夔州', sub='严武死后 · 再度漂泊', art=art_d_kuizhou),
    C(150, 156, 'fate', 'card', year=767, main='登高', sub='万里悲秋常作客', note='百年多病独登台', art=art_d_denggao),
    C(156, 160, 'death', 'card', year=768, main='贫病交加', sub='出峡东下', art=art_d_ill),
    C(160, 164, 'night', 'card', year=768, main='登岳阳楼', sub='戎马关山北', art=art_d_yueyang),
    C(164, 168, 'death', 'card', year=770, main='湘江孤舟', sub='冬日 · 病逝舟中', note='一说', art=art_d_last_boat),
    C(168, 170, 'end', 'card', year=813, main='归葬偃师', sub='孙儿迁葬', art=art_d_reburial),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾贰', col=STRAW, acc=SMOKE, born=712, died=770,
    hook_q='一辈子没过上好日子 · 他为何被称为诗圣？',
    name_line='杜甫 · 字子美', name='杜甫', seal='少陵', title_art=art_d_title,
    q1='诗圣？', q2='苦命人？',
    end_art=art_d_legacy, end_big='诗圣', end_seal='少陵',
    end_l1='他自己住在漏雨的茅屋', end_l2='心里却装着天下寒士',
    end_brush='安得广厦千万间', end_ask='李白和杜甫 你更喜欢谁？评论区聊聊', next='苏轼'),
    scenes=dict(chapter=scene_chapter, sanli=scene_sanli))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
