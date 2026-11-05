"""千古人物志 · 第伍拾捌集 · 张衡 (78–139)
Look: 青铜绿 + 星图金, 星宿 corner borders, a 浑天仪 chapter card: one bronze ring is added each chapter (1→4)
and in the last chapter the armillary sphere turns under the stars.
Set pieces: 6-beat 二京赋 十年, 6-beat 漏水转浑天仪, custom 8-beat scene 'didong' (候风地动仪 · 陇西地震),
6-beat 星官 2500 星, 6-beat 张衡星.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_wangzhaojun as Wz     # engine + helpers (previous episode)
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
from render_quyuan import river
from render_wangzhaojun import emperor

F.RIPPLE = False
QINGTONG = (60, 120, 104)           # 青铜绿
XINGJIN = (196, 158, 70)            # 星图金
S.LAYERS.append(('qingtong', QINGTONG, 0.9, 1.0))
S.LAYERS.append(('xingjin', XINGJIN, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='天', life='衡', court='汉', night='星', war='震', empire='天', works='仪', fate='归', death='星', end='衡')
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
G.THEMES['empire']['sun'] = (XINGJIN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (QINGTONG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

MTN_COL = {'night': (28, 34, 44), 'death': (60, 62, 64), 'war': (110, 66, 52), 'fate': (90, 100, 98)}
STARS = [(random.Random(i).randint(80, W - 80), random.Random(i * 7 + 1).randint(1330, 1520), random.Random(i * 3).random()) for i in range(26)]
def draw_background(t, theme):
    """南阳 · 洛阳: hills, and a faint band of twinkling stars with constellation lines along the bottom margin."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(186, 190, 186), (150, 164, 158), MTN_COL.get(theme, (100, 124, 116))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for i in range(0, len(STARS) - 1, 3):
        (x0, y0, _), (x1, y1, _) = STARS[i], STARS[i + 1]
        d.line((x0, y0, x1, y1), fill=XINGJIN + (36,), width=2)
    for x, y, ph in STARS:
        r = max(0.5, 3 + 2 * math.sin(t * 2 + ph * 6))
        d.ellipse((x - r, y - r, x + r, y + r), fill=XINGJIN + (90,))
    canvas.alpha_composite(ov)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """星宿: a small constellation (four stars joined) in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINGTONG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINGTONG + (220,), width=3)
        pts = [(x + sx * 24, y + sy * 30), (x + sx * 56, y + sy * 22), (x + sx * 84, y + sy * 50), (x + sx * 60, y + sy * 84)]
        d.line(pts, fill=XINGJIN + (200,), width=2)
        for px, py in pts:
            d.ellipse((px - 6, py - 6, px + 6, py + 6), fill=XINGJIN + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def heng(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """张衡: Eastern-Han scholar-official — 进贤冠, neat beard, a bronze-green sash."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - 0.07 * h, y - 0.95 * h), (x + 0.07 * h, y - 0.95 * h), (x + dir * 0.08 * h, y - 1.1 * h), (x - dir * 0.03 * h, y - 1.05 * h)], fill=255)
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.68 * h)], fill=255)
        A.d['qingtong'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.04 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.06 * h, y - 0.7 * h)], fill=255)
    return hand

def armillary(A, cx, cy, r, rings, t, spin=0.0):
    """浑天仪: a stand with up to four rings: horizon, meridian, equator, ecliptic."""
    A.d['ink'].line((cx, cy + r, cx, cy + r + 0.6 * r), fill=255, width=12)
    A.d['ink'].line((cx - 0.6 * r, cy + 1.6 * r, cx + 0.6 * r, cy + 1.6 * r), fill=255, width=14)
    if rings >= 1:
        A.d['qingtong'].ellipse((cx - r, cy - 0.25 * r, cx + r, cy + 0.25 * r), outline=255, width=10)
    if rings >= 2:
        A.d['qingtong'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=10)
    if rings >= 3:
        w = abs(math.cos(spin)) * r
        A.d['xingjin'].ellipse((cx - w, cy - r * 0.92, cx + w, cy + r * 0.92), outline=255, width=8)
    if rings >= 4:
        a = 0.4 + 0.2 * math.sin(spin)
        pts = [(cx + 0.9 * r * math.cos(k * math.pi / 20), cy + 0.9 * r * math.sin(k * math.pi / 20) * math.sin(a) + 0.2 * r * math.cos(k * math.pi / 20)) for k in range(41)]
        A.d['xingjin'].line(pts, fill=255, width=6)
    A.d['ink'].ellipse((cx - 0.12 * r, cy - 0.12 * r, cx + 0.12 * r, cy + 0.12 * r), fill=255)

def seismo(A, cx, base, s, t, drop=-1, q=0.0):
    """候风地动仪: a wine-jar shaped vessel with eight dragons, each holding a ball, and eight toads below."""
    A.d['qingtong'].polygon([(cx - 0.55 * s, base), (cx + 0.55 * s, base), (cx + 0.75 * s, base - 0.6 * s), (cx + 0.5 * s, base - 1.1 * s), (cx - 0.5 * s, base - 1.1 * s), (cx - 0.75 * s, base - 0.6 * s)], fill=255)
    A.d['qingtong'].chord((cx - 0.55 * s, base - 1.4 * s, cx + 0.55 * s, base - 0.8 * s), 180, 360, fill=255)
    A.d['ink'].rectangle((cx - 0.2 * s, base - 1.5 * s, cx + 0.2 * s, base - 1.38 * s), fill=255)
    for i in range(8):
        a = math.radians(-180 + i * 25.7)
        dx = math.cos(a) * 0.72 * s
        A.d['ink'].line((cx + dx * 0.9, base - 0.9 * s, cx + dx * 1.1, base - 0.72 * s), fill=255, width=max(4, int(0.05 * s)))
        bx, by = cx + dx * 1.12, base - 0.68 * s
        if i == drop:
            by = lerp(by, base - 0.12 * s, ease_out(q))
        A.d['xingjin'].ellipse((bx - 0.05 * s, by - 0.05 * s, bx + 0.05 * s, by + 0.05 * s), fill=255)
        A.d['ink'].ellipse((cx + dx * 1.12 - 0.09 * s, base - 0.12 * s, cx + dx * 1.12 + 0.09 * s, base), fill=255)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_ring_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    r0, r1 = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    armillary(A, 540, 1040, 150, r1 if q > 0.5 else r0, t, spin=t * (0.8 if kb == 144 else 0.2))
    if kb == 144:
        for i in range(12):
            a = i * 0.52 + t * 0.2
            A.d['xingjin'].ellipse((540 + 260 * math.cos(a) - 5, 1040 + 200 * math.sin(a) - 5, 540 + 260 * math.cos(a) + 5, 1040 + 200 * math.sin(a) + 5), fill=int(255 * q))

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_ring_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINGTONG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_ball(A, cv, t, u):
    ground(A, GROUND)
    seismo(A, 540, GROUND, 300, t, drop=6, q=clamp((u - 0.6 * P) / (0.6 * P)))

def art_h_hook_stars(A, cv, t, u):
    n = int(clamp(u / (1.4 * P)) * 60) + 1
    for i in range(n):
        x = 120 + (i * 97) % 840; y = 760 + (i * 53) % 520
        A.d['xingjin'].ellipse((x - 4, y - 4, x + 4, y + 4), fill=255)
    ground(A, GROUND)

def art_h_hook_book(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='qingtong')
    n = min(10, int(clamp(u / (1.4 * P)) * 10) + 1)
    for i in range(n):
        bundle(A, 380 + (i % 5) * 70, GROUND - 74 - (i // 5) * 40, 50, layer='xingjin')

def art_h_hook_planet(A, cv, t, u):
    r = 110
    A.d['xingjin'].ellipse((540 - r, 1040 - r, 540 + r, 1040 + r), fill=200)
    A.d['ink'].arc((540 - 1.8 * r, 1040 - 0.4 * r, 540 + 1.8 * r, 1040 + 0.4 * r), 160, 380, fill=255, width=4)
    ground(A, GROUND)

# ================================================================ 第一回 南阳少年
def art_h_birth(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    A.d['mid'].rectangle((380, 1100, 700, 1240), fill=220)
    A.d['ink'].polygon([(340, 1100), (740, 1100), (540, 1000)], fill=255)
    A.flush(cv)
    paste(cv, text_img('南阳西鄂 · 世为著姓', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('西鄂', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_grandpa(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 210, dir=-1, robe=True, hat='crown', arm=lerp(20, 80, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    heng(A, 420, GROUND, 110, dir=1, arm=40)
    A.flush(cv)
    paste(cv, text_img('祖父张堪 · 曾任蜀郡太守', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_write(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='qingtong')
    heng(A, 300, GROUND, 170, dir=1, kneel=True, bow=20, arm=90)
    n = int(clamp(u / (2 * P)) * 8) + 1
    slips(A, 440, GROUND - 74, n, 90, layer='xingjin')
    A.flush(cv)
    paste(cv, text_img('少善属文', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_travel(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 280), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    heng(A, lerp(120, 800, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('游于三辅 · 因入京师', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_taixue(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtong')
    ground(A, GROUND)
    for i in range(4):
        sitter(A, 260 + i * 160, GROUND, 120, dir=1, bow=15, layer='mid' if i else 'ink')
    A.flush(cv)
    paste(cv, text_img('观太学 · 遂通五经 贯六艺', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('太学', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_humble(A, cv, t, u):
    ground(A, GROUND)
    heng(A, 540, GROUND, 200, dir=1, arm=-8)
    for i in range(3):
        rider(A, lerp(980, 660, ease_out(u / (2 * P))) + i * 100, GROUND, 110, dir=-1, ph=t * 6 + i, layer='mid')
    A.flush(cv)
    paste(cv, text_img('虽才高于世 而无骄尚之情', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_refuse(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(20, 120, ease_out(u / 0.5)), layer='ink')
    heng(A, 380, GROUND, 190, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('举孝廉不行 · 连辟公府不就', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 二京赋
def art_h_nanyang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='南阳', layer='qingtong', open_=1.0)
    ground(A, GROUND)
    heng(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('南阳太守鲍德请为主簿', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('主簿', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_erjing(A, cv, t, u):
    """6-beat set piece: 二京赋 — two cities, 西京 and 东京, rise on either side as the scroll grows; ten winters pass by the window."""
    ph = u / P
    city_wall(A, 80, 440, 1100, gate_x=260, label='西京', layer='mid', open_=1.0)
    city_wall(A, 640, 1000, 1100, gate_x=820, label='东京', layer='qingtong', open_=1.0)
    ground(A, GROUND)
    scroll(A, 540, 1220, lerp(80, 360, clamp(ph / 5)), 70, 1.0, layer='wash')
    A.flush(cv)
    yrs = min(10, int(clamp(ph / 5) * 10) + 1)
    paste(cv, text_img(f'精思傅会 · 第{cn_num(yrs)}年', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('十年乃成 · 讽谏王侯奢侈', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, 1, clamp((ph - 4.5) / 0.4))

def art_h_mother(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    heng(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=90)
    A.flush(cv)
    paste(cv, text_img('鲍德迁官 · 张衡归乡守制', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_taixuan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='qingtong')
    heng(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    for k in range(9):
        A.d['ink'].line((450 + k * 18, GROUND - 160, 450 + k * 18, GROUND - 90), fill=255 if k % 3 else 120, width=6)
    A.flush(cv)
    paste(cv, text_img('研读扬雄太玄经 · 始好术学', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_called(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    carriage(A, lerp(120, 840, ease_out(u / (3 * P))), GROUND, 100, dir=1, wheel=t * 6, ph=t * 8, layer='qingtong')
    A.flush(cv)
    paste(cv, text_img('安帝闻其善术学 · 公车特征', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_langzhong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 80, ease_out(u / 0.6)))
    heng(A, 380, GROUND, 190, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('郎中', 60), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('拜郎中 · 入京任职', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 太史令
def art_h_taishi(A, cv, t, u):
    for k in range(3):
        A.d['qingtong'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    heng(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 120, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('太史令', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('掌天时 星历', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_hunyi(A, cv, t, u):
    """6-beat set piece: 漏水转浑天仪 — water drips from the clepsydra; a wheel turns; the sphere rotates in step with the sky; stars track."""
    ph = u / P
    A.d['mid'].rectangle((140, 980, 260, 1120), fill=230)
    A.d['ink'].rectangle((140, 980, 260, 1120), outline=255, width=4)
    for k in range(4):
        q = (t * 1.5 + k / 4) % 1
        A.d['ocean'].ellipse((200 - 6, lerp(1120, 1240, q) - 6, 200 + 6, lerp(1120, 1240, q) + 6), fill=220)
    a = t * 0.8
    for k in range(8):
        A.d['ink'].line((300, 1220, 300 + 60 * math.cos(a + k * math.pi / 4), 1220 + 60 * math.sin(a + k * math.pi / 4)), fill=255, width=4)
    A.d['ink'].line((300, 1220, 560, 1120), fill=180, width=4)
    armillary(A, 640, 1000, 170, 4, t, spin=t * 0.8)
    for i in range(10):
        b = t * 0.8 + i * 0.63
        A.d['xingjin'].ellipse((640 + 280 * math.cos(b) - 4, 1000 + 120 * math.sin(b) - 4, 640 + 280 * math.cos(b) + 4, 1000 + 120 * math.sin(b) + 4), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    lab = '以漏水转之' if ph < 2.5 else '某星始见 某星已中 某星今没 · 皆如合符'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2.5 else QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('浑天仪', 50), 860, 1440, t, t - u + 0.4, rot=6)

def art_h_lingxian(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='qingtong')
    heng(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    r = 60
    A.d['xingjin'].ellipse((640 - r, GROUND - 200 - r, 640 + r, GROUND - 200 + r), fill=200)
    A.d['ink'].ellipse((740 - 30, GROUND - 200 - 30, 740 + 30, GROUND - 200 + 30), fill=255)
    A.flush(cv)
    paste(cv, text_img('月光生于日之所照 · 魄生于日之所蔽', SERIF, 42, QINGTONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('灵宪', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_egg(A, cv, t, u):
    A.d['wash'].ellipse((300, 900, 780, 1260), fill=220)
    A.d['ink'].ellipse((300, 900, 780, 1260), outline=255, width=6)
    A.d['xingjin'].ellipse((500, 1040, 580, 1120), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('浑天如鸡子 · 地如鸡中黄', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_stars(A, cv, t, u):
    """6-beat set piece: 星官 — the sky fills with named star groups; the counter climbs toward 2500."""
    ph = u / P
    n = int(clamp(ph / 5) * 120) + 1
    for i in range(n):
        x = 120 + (i * 97) % 840; y = 760 + (i * 61) % 560
        r = 3 + (i % 3)
        A.d['xingjin'].ellipse((x - r, y - r, x + r, y + r), fill=255)
        if i % 5 and i > 0:
            px = 120 + ((i - 1) * 97) % 840; py = 760 + ((i - 1) * 61) % 560
            if abs(px - x) < 200 and abs(py - y) < 200:
                A.d['xingjin'].line((px, py, x, y), fill=120, width=2)
    ground(A, GROUND)
    A.flush(cv)
    cnt = int(lerp(0, 2500, clamp(ph / 5)))
    paste(cv, text_img(f'中外之官 常明者百二十四 · 微星之数 {cnt}', SERIF, 40, QINGTONG, 'Black', bleed=False, spacing=2), W / 2, 700, 1, 1)

def art_h_gonggu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(3):
        person(A, 700 + i * 80, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='ink')
    heng(A, 340, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('作应间 · 安于其位 不慕高升', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '时人讥其不迁 衡作应间以对', t, t - u + P)

# ================================================================ 第四回 地动仪
def scene_didong(cv, t, c, k):
    """8-beat custom scene: 候风地动仪 — in the Luoyang observatory the vessel stands quiet; one dragon drops its ball into a toad's mouth;
    nobody felt a tremor; scholars mock; days later a rider arrives from 陇西 — there was an earthquake."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 5.2:
        seismo(A, 540, GROUND, 340, t, drop=2, q=clamp((ph - 1.4) / 0.6))
        for i in range(3):
            person(A, 160 + i * 60 if i < 2 else 900, GROUND, 150, dir=1 if i < 2 else -1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3 + i)) if ph > 2.5 else 40, layer='mid')
    else:
        seismo(A, 300, GROUND, 220, t, drop=2, q=1.0)
        rider(A, lerp(1200, 680, ease_out((ph - 5.2) / 1.5)), GROUND, 150, dir=-1, ph=t * 10)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '候风地动仪', BRUSH, 140, INK, W / 2, 440, t, s0, stagger=0.06, seed=58)
    fx.flush(cv)
    lab = '尝一龙机发 而地不觉动' if ph < 2.5 else ('京师学者咸怪其无征' if ph < 5.2 else '后数日驿至 果地震陇西')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 5.2 else QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('于是皆服其妙', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.4) / 0.4))
    if ph > 2:
        note_in(cv, '原器已佚 今日所见多为后人复原', t, s0 + 2 * P)

def art_h_build(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='qingtong')
    heng(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    seismo(A, 620, GROUND - 74, 140 * ease_out(u / (2 * P)) + 10, t)
    A.flush(cv)
    paste(cv, text_img('以精铜铸成 员径八尺 合盖隆起 形似酒尊', SERIF, 40, QINGTONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('阳嘉元年', 44), 860, 1020, t, t - u + P, rot=6)

def art_h_dragons(A, cv, t, u):
    seismo(A, 540, GROUND, 400, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('八方各一龙 · 龙口衔铜丸 下有蟾蜍承之', SERIF, 40, QINGTONG, 'Black', bleed=False, spacing=2), W / 2, 760, 1, clamp(u / 0.4))

def art_h_shizhong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtong')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=60)
    heng(A, 380, GROUND, 190, dir=1, kneel=True, bow=20, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('侍中', 60), 260, 1020, t, t - u + P, rot=-5)
    paste(cv, text_img('迁侍中 · 帷幄讽议左右', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_eunuchs(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(3):
        person(A, 700 + i * 80, GROUND, 160, dir=-1, robe=True, hat='knot', bow=15, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='ink')
    heng(A, 340, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('宦官惧其毁己 · 共谗之', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_sixuan(A, cv, t, u):
    for k in range(4):
        q = (t * 0.06 + k / 4) % 1
        A.d['wash'].ellipse((lerp(-200, 1200, q) - 220, 900 + k * 60 - 40, lerp(-200, 1200, q) + 220, 900 + k * 60 + 40), fill=150)
    ground(A, GROUND)
    heng(A, 540, GROUND, 190, dir=1, arm=lerp(-8, 120, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    paste(cv, text_img('作思玄赋 · 以宣寄情志', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_hejian(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='河间', layer='mid', open_=1.0)
    ground(A, GROUND)
    heng(A, 540, GROUND, 200, dir=1, arm=lerp(40, 140, ease_out(u / 0.5)))
    for i in range(3):
        person(A, 760 + i * 70, GROUND, 150, dir=-1, robe=True, hat='knot', kneel=True, bow=40, arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('出为河间相 · 治威严 整法度', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '收禽诸豪侠 上下肃然', t, t - u + P)

# ================================================================ 第五回 归田
def art_h_guitian(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=3, speed=0.6)
    for k in range(4):
        A.d['grass'].line((160 + k * 50, 1240, 170 + k * 50, 1120), fill=255, width=4)
    heng(A, 600, 1240, 180, dir=1, kneel=True, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t)), old=0.6)
    A.d['ink'].line((680, 1100, 900, 1200), fill=255, width=3)
    A.flush(cv)
    paste(cv, text_img('仰飞纤缴 俯钓长流', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('归田赋', 54), 860, 1020, t, t - u + P, rot=6)

def art_h_shangshu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtong')
    ground(A, GROUND)
    heng(A, 540, GROUND, 190, dir=1, arm=60, old=0.8)
    A.flush(cv)
    stamp(cv, seal('尚书', 60), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('征拜尚书', SERIF, 48, QINGTONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    heng(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('永和四年卒 · 年六十二', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_cuiyuan(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    A.d['ink'].rectangle((620, 1060, 680, 1240), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('数术穷天地 制作侔造化', SERIF, 48, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('崔瑗碑', 50), 860, 1020, t, t - u + P, rot=6)

def art_h_wangfu(A, cv, t, u):
    for i in range(int(clamp(u / (2 * P)) * 7) + 1):
        A.d['ink'].line((200 + i * 100, GROUND, 200 + i * 100, GROUND - 120 - (i % 3) * 30), fill=255, width=8)
        A.d['qingtong'].ellipse((200 + i * 100 - 18, GROUND - 140 - (i % 3) * 30, 200 + i * 100 + 18, GROUND - 104 - (i % 3) * 30), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('地动仪复原 历代不绝', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_crater(A, cv, t, u):
    r = 150
    A.d['wash'].ellipse((540 - r, 1040 - r, 540 + r, 1040 + r), fill=230)
    for i in range(5):
        a = i * 1.3
        cr = 20 + i * 6
        cx, cy = 540 + 80 * math.cos(a), 1040 + 80 * math.sin(a)
        A.d['mid'].ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('月球背面 · 张衡环形山', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    stamp(cv, seal('一九七〇', 44), 860, 1020, t, t - u + P, rot=6)

def art_h_asteroid(A, cv, t, u):
    """6-beat set piece: 张衡星 — a small planet crosses the starfield along its orbit; the orbit line draws itself."""
    ph = u / P
    for i in range(50):
        x = 100 + (i * 97) % 880; y = 760 + (i * 53) % 560
        A.d['xingjin'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=180)
    q = clamp(ph / 5)
    pts = [(540 + 360 * math.cos(math.pi + k * math.pi / 40), 1040 + 180 * math.sin(math.pi + k * math.pi / 40)) for k in range(int(80 * q) + 1)]
    if len(pts) > 1:
        A.d['qingtong'].line(pts, fill=255, width=4)
    x, y = pts[-1]
    A.d['xingjin'].ellipse((x - 16, y - 16, x + 16, y + 16), fill=255)
    A.d['xingjin'].ellipse((540 - 40, 1040 - 40, 540 + 40, 1040 + 40), fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('小行星1802号 · 命名为张衡星', SERIF, 46, QINGTONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_h_guo(A, cv, t, u):
    for i in range(3):
        armillary(A, 260 + i * 280, 1080, 80, 4, t, spin=t * 0.5 + i)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('郭沫若题 · 如此全面发展之人物 世界史中亦所罕见', SERIF, 36, QINGTONG, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_h_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    armillary(A, 860, 1300, 50, 4, t, spin=t * 0.5)

def art_h_title(A, cv, t, u):
    armillary(A, 820, 1180, 140, 4, t, spin=t * 0.4)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    heng(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '南阳少年'), 48: ('第二回', '二京赋'), 80: ('第三回', '太史令'),
            112: ('第四回', '地动仪'), 144: ('第五回', '归田')}

CARDS = [
    C(0, 2, 'war', 'num', num='一颗铜丸', line='千里外地震', art=art_h_hook_ball),
    C(2, 4, 'night', 'num', num='两千五百颗星', line='他一颗颗数', art=art_h_hook_stars),
    C(4, 6, 'works', 'num', num='一篇赋', line='写了十年', art=art_h_hook_book),
    C(6, 8, 'empire', 'num', num='一颗行星', line='以他命名', art=art_h_hook_planet),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 南阳少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=78, main='生于西鄂', sub='南阳著姓', art=art_h_birth),
    C(22, 26, 'court', 'card', year=84, main='祖父张堪', sub='家学', art=art_h_grandpa),
    C(26, 30, 'works', 'card', year=90, main='善属文', sub='少年才子', art=art_h_write),
    C(30, 34, 'fate', 'card', year=94, main='游学三辅', sub='入京', art=art_h_travel),
    C(34, 38, 'works', 'card', year=95, main='观太学', sub='通五经', art=art_h_taixue),
    C(38, 42, 'life', 'card', year=96, main='不骄', sub='才高而谦', art=art_h_humble),
    C(42, 48, 'night', 'card', year=97, main='屡辟不就', sub='无意仕途', art=art_h_refuse),
    # ---- 第二回 二京赋
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=100, main='南阳主簿', sub='初入仕', art=art_h_nanyang),
    C(54, 60, 'works', 'card', year=100, main='二京赋', sub='十年一赋', art=art_h_erjing),
    C(60, 64, 'death', 'card', year=108, main='归乡', sub='守制', art=art_h_mother),
    C(64, 68, 'night', 'card', year=108, main='研太玄', sub='由文入术', art=art_h_taixuan),
    C(68, 72, 'fate', 'card', year=111, main='公车特征', sub='帝闻其名', art=art_h_called),
    C(72, 80, 'empire', 'card', year=111, main='拜郎中', sub='入朝', art=art_h_langzhong),
    # ---- 第三回 太史令
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'court', 'card', year=115, main='太史令', sub='观天之官', art=art_h_taishi),
    C(86, 92, 'works', 'card', year=117, main='浑天仪', sub='漏水转之', art=art_h_hunyi),
    C(92, 96, 'night', 'card', year=118, main='灵宪', sub='月光来自太阳', art=art_h_lingxian),
    C(96, 100, 'life', 'card', year=118, main='浑天说', sub='天如鸡子', art=art_h_egg),
    C(100, 106, 'empire', 'card', year=118, main='数星', sub='两千五百', art=art_h_stars),
    C(106, 112, 'fate', 'card', year=126, main='应间', sub='不慕升迁', art=art_h_gonggu),
    # ---- 第四回 地动仪
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'works', 'card', year=132, main='铸地动仪', sub='精铜所造', art=art_h_build),
    C(118, 122, 'life', 'card', year=132, main='八龙八蟾', sub='八方', art=art_h_dragons),
    C(122, 130, 'war', 'didong', year=134),
    C(130, 134, 'court', 'card', year=134, main='迁侍中', sub='近天子', art=art_h_shizhong),
    C(134, 138, 'death', 'card', year=135, main='宦官谗之', sub='朝中暗流', art=art_h_eunuchs),
    C(138, 142, 'night', 'card', year=136, main='思玄赋', sub='心事', art=art_h_sixuan),
    C(142, 144, 'empire', 'card', year=136, main='河间相', sub='整肃豪强', art=art_h_hejian),
    # ---- 第五回 归田
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=138, main='归田赋', sub='想回家了', art=art_h_guitian),
    C(150, 154, 'court', 'card', year=138, main='拜尚书', sub='最后的官职', art=art_h_shangshu),
    C(154, 158, 'death', 'card', year=139, main='张衡去世', sub='年六十二', art=art_h_death),
    C(158, 160, 'works', 'card', year=139, main='崔瑗碑', sub='制作侔造化', art=art_h_cuiyuan),
    C(160, 164, 'life', 'card', year=1951, main='复原', sub='千年之后', art=art_h_wangfu),
    C(164, 166, 'night', 'card', year=1970, main='月球环形山', sub='张衡', art=art_h_crater),
    C(166, 168, 'empire', 'card', year=1977, main='张衡星', sub='小行星', art=art_h_asteroid),
    C(168, 170, 'end', 'card', year=1977, main='全才', sub='世界罕见', art=art_h_guo),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾捌', col=QINGTONG, acc=XINGJIN, born=78, died=139, age0=77,
    born_lab='78年', died_lab='139年', years_txt='公元78 — 139',
    hook_q='一颗铜丸落下 · 他怎么知道千里外地震了？',
    name_line='张衡 · 字平子', name='张衡', seal='平子', title_art=art_h_title,
    q1='东汉科学巨匠？', q2='被埋没的文学家？',
    end_art=art_h_legacy, end_big='数术穷天地', end_seal='平子',
    end_l1='他数过天上的星', end_l2='如今天上也有一颗星叫张衡',
    end_brush='浑天如鸡子', end_ask='你最佩服古人的哪一项发明？评论区聊聊', next='华佗'),
    scenes=dict(chapter=scene_chapter, didong=scene_didong))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
