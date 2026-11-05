"""千古人物志 · 第陆拾伍集 · 白居易 (772–846)
Look: 江州司马青 + 枫叶红, 琵琶弦 corner borders, a 原上草 chapter card: grass on the plain burns down and grows back
(野火烧不尽 春风吹又生) — green → fire → ash → green, and in the last chapter it waves under a full moon.
Set pieces: 6-beat 长安居大不易, 6-beat 卖炭翁, custom 8-beat scene 'pipa' (浔阳江头夜送客), 6-beat 白堤,
6-beat 老妪能解, 6-beat 香山九老.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_mulan as Ml           # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor

F.RIPPLE = False
SIMA = (60, 108, 116)               # 江州司马青
FENGYE = (184, 70, 48)              # 枫叶红
S.LAYERS.append(('sima', SIMA, 0.9, 1.0))
S.LAYERS.append(('fengye', FENGYE, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='诗', life='白', court='唐', night='月', war='谏', empire='杭', works='诗', fate='贬', death='香', end='乐')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (FENGYE, 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (SIMA, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (FENGYE, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

MAPLE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(MAPLE)
for _x in (130, 950):               # maple trees at the margins
    _d.line((_x, 1480, _x + 4, 1360), fill=(80, 60, 50, 70), width=7)
    for _k in range(8):
        _a = _k * 0.8
        _px, _py = _x + 50 * math.cos(_a), 1350 + 30 * math.sin(_a)
        _d.regular_polygon((_px, _py, 13), 5, rotation=_k * 20, fill=FENGYE + (70,))
for _k in range(3):
    _d.line([(240 + i * 30, 1474 + _k * 14 + 3 * math.sin(i * 0.7)) for i in range(21)], fill=SIMA + (40,), width=2)
MTN_COL = {'night': (28, 32, 42), 'death': (60, 58, 60), 'war': (112, 62, 50), 'fate': (90, 100, 104)}
def draw_background(t, theme):
    """江州 · 长安: hills, maples at the margins and the river lines."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 188, 186), (154, 164, 162), MTN_COL.get(theme, (106, 122, 124))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(MAPLE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """琵琶弦: four strings with a maple leaf in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=SIMA + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=SIMA + (220,), width=3)
        for k in range(4):
            d.line((x + sx * (20 + k * 10), y + sy * 20, x + sx * (20 + k * 10), y + sy * 110), fill=(80, 70, 60, 200), width=2)
        d.regular_polygon((x + sx * 90, y + sy * 46, 20), 5, rotation=18, fill=FENGYE + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def bai(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """白居易: plain 幞头 with soft tails, round face, a blue 司马 robe."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line((x - dir * 0.06 * h, y - 0.97 * h, x - dir * 0.18 * h, y - 0.9 * h), fill=255, width=max(2, int(0.02 * h)))
        A.d['sima'].polygon([(x - 0.11 * h, y - 0.78 * h), (x + 0.11 * h, y - 0.78 * h), (x + 0.14 * h, y - 0.1 * h), (x - 0.14 * h, y - 0.1 * h)], fill=150)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.72 * h)], fill=255)
    return hand

def grass(A, x0, x1, base, h, t, burn=0.0, layer='grass'):
    for i in range(int((x1 - x0) / 16)):
        x = x0 + i * 16
        hh = h * (0.7 + 0.3 * math.sin(i * 1.7))
        sway = 6 * math.sin(t * 2 + i * 0.4)
        lay = 'ink' if burn > 0.5 and (i * 37) % 10 < 10 * burn else layer
        A.d[lay].line((x, base, x + sway, base - hh * (1 - 0.8 * burn)), fill=255, width=4)

def pipa(A, x, y, s, layer='fengye'):
    A.d[layer].ellipse((x - 0.5 * s, y - 0.45 * s, x + 0.5 * s, y + 0.6 * s), fill=255)
    A.d['ink'].line((x, y - 0.4 * s, x, y - 1.4 * s), fill=255, width=max(3, int(0.08 * s)))

# ================================================================ chapter card
CH = {16: (0, 'green'), 48: (1, 'fire'), 80: (2, 'ash'), 112: (3, 'green'), 144: (4, 'moon')}
def art_grass_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    st, kind = CH.get(kb, (0, 'green'))
    q = ease_out(u / (1.2 * P))
    if kind == 'green':
        grass(A, 160, 920, 1200, 140 * (q if st == 3 else 1.0), t)
    elif kind == 'fire':
        grass(A, 160, 920, 1200, 140, t, burn=q * 0.5)
        flames(A, 540, 1200, 600, 200 * q, t, n=7, seed=772, smoke=True)
    elif kind == 'ash':
        grass(A, 160, 920, 1200, 140, t, burn=1.0)
    else:
        r = 70
        A.d['wash'].ellipse((760 - r, 900 - r, 760 + r, 900 + r), fill=int(240 * q))
        grass(A, 160, 920, 1200, 140, t)
    A.d['mid'].rectangle((140, 1200, 940, 1220), fill=150)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_grass_chapter)
    ink_in(cv, text_img(no, SERIF, 56, SIMA, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_b_hook_grass(A, cv, t, u):
    grass(A, 120, 960, GROUND, 160, t, burn=clamp(1 - u / (1.4 * P)))
    ground(A, GROUND)

def art_b_hook_old(A, cv, t, u):
    ground(A, GROUND)
    person(A, 700, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, bow=30, arm=lerp(40, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    bai(A, 380, GROUND, 190, dir=1, kneel=True, arm=90)

def art_b_hook_pipa(A, cv, t, u):
    river(A, 1220, t, rows=2, amp=3)
    boat(A, 540, 1240, 160, t, sail=False)
    pipa(A, 540, 1160, 60)

def art_b_hook_3000(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='sima')
    n = int(clamp(u / (1.4 * P)) * 12) + 1
    for i in range(n):
        bundle(A, 360 + (i % 6) * 70, GROUND - 74 - (i // 6) * 40, 50, layer='fengye')

# ================================================================ 第一回 居大不易
def art_b_birth(A, cv, t, u):
    A.d['mid'].rectangle((360, 1080, 720, GROUND), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 960)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('河南新郑 · 小官之家', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('新郑', 56), 860, 1020, t, t - u + P, rot=6)

def art_b_zhiwu(A, cv, t, u):
    ground(A, GROUND)
    bai(A, 400, GROUND, 110, dir=1, arm=lerp(-8, 80, ease_out(u / 0.5)))
    person(A, 660, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mid')
    scroll(A, 540, GROUND - 260, 140, 50, 1.0, layer='wash')
    A.flush(cv)
    paste(cv, text_img('生六七月 已能指认之无二字', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '自述见与元九书', t, t - u + P)

def art_b_war(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 260), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    person(A, lerp(300, 900, ease_out(u / (3 * P))), GROUND, 190, dir=1, robe=True, hat='knot', female=True, ph=t * 3, arm=-8, layer='mid')
    bai(A, lerp(220, 820, ease_out(u / (3 * P))), GROUND, 110, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('藩镇战乱 · 随母避居江南', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='sima')
    bai(A, 300, GROUND, 170, dir=1, kneel=True, bow=25, arm=90)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    paste(cv, text_img('口舌成疮 手肘成胝', SERIF, 48, SIMA, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '昼课赋 夜课书 间又课诗 不遑寝息', t, t - u + P)

def art_b_guyong(A, cv, t, u):
    """6-beat set piece: 长安居大不易 — the young man hands his poems to 顾况, who jokes about the name; then reads the grass poem and changes his tone."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, clamp((ph - 3) / 0.4)), layer='ink', bow=10 if ph < 3 else 0)
    bai(A, 380, GROUND, 180, dir=1, bow=20, arm=90)
    scroll(A, 600, GROUND - 160, 140, 40, 1.0, layer='wash')
    A.flush(cv)
    lab = '米价方贵 居亦弗易' if ph < 3 else '道得个语 居即易矣'
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3 else SIMA, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp((ph % 3) / 0.4))
    type_in(cv, text_img('野火烧不尽 春风吹又生', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.8 * P, 0.5)
    note_in(cv, '事见幽闲鼓吹 带传说色彩', t, t - u + P)

def art_b_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='fengye')
    ground(A, GROUND)
    bai(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('慈恩塔下题名处 十七人中最少年', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 新乐府
def art_b_yuanzhen(A, cv, t, u):
    ground(A, GROUND)
    bai(A, 400, GROUND, 190, dir=1, arm=lerp(40, 100, ease_out(u / 0.5)))
    person(A, 680, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 100, ease_out(u / 0.5)), layer='sima')
    A.flush(cv)
    paste(cv, text_img('与元稹同登科 · 终生诗友', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('元白', 56), 860, 1020, t, t - u + P, rot=6)

def art_b_changhen(A, cv, t, u):
    palace(A, 540, 1300, 340, layer='fengye')
    ground(A, GROUND)
    emperor(A, 460, GROUND, 190, dir=1, arm=60)
    person(A, 640, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mulanfen')
    A.flush(cv)
    type_in(cv, text_img('在天愿作比翼鸟 在地愿为连理枝', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('长恨歌', 50), 860, 1020, t, t - u + P, rot=6)

def art_b_shiyi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 140, ease_out((u - P) / 0.5)))
    bai(A, 400, GROUND, 190, dir=1, kneel=True, bow=10, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('拜左拾遗 · 屡次直谏', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    type_in(cv, text_img('陛下错', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 1.5 * P, 0.3)

def art_b_charcoal(A, cv, t, u):
    """6-beat set piece: 卖炭翁 — an old man burns charcoal in the south mountains; drives a cartload through snow to the city;
    palace envoys take a thousand jin for half a bolt of red silk."""
    ph = u / P
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 3, lerp(620, 1420, q) - 3, 80 + (k * 19) % 920 + 3, lerp(620, 1420, q) + 3), fill=220)
    ground(A, GROUND)
    if ph < 3:
        x = lerp(100, 520, ease_out(ph / 3))
        carriage(A, x, GROUND, 80, dir=1, wheel=t * 3, ph=t * 3, canopy=False, layer='mid')
        A.d['ink'].ellipse((x - 50, GROUND - 120, x + 50, GROUND - 70), fill=255)
        person(A, x - 140, GROUND, 150, dir=1, robe=True, hat='knot', bow=30, ph=t * 3, arm=150, layer='ink')
        lab = '满面尘灰烟火色 两鬓苍苍十指黑'
    else:
        carriage(A, 520, GROUND, 80, dir=-1, moving=False, canopy=False, layer='mid')
        A.d['ink'].ellipse((470, GROUND - 120, 570, GROUND - 70), fill=255)
        for j in range(2):
            person(A, 700 + j * 80, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 150, clamp((ph - 3) / 0.4)), layer='fengye')
        person(A, 360, GROUND, 150, dir=1, robe=True, hat='knot', bow=40, arm=-8, layer='ink')
        A.d['red'].rectangle((620, GROUND - 160, 680, GROUND - 140), fill=255)
        lab = '半匹红纱一丈绫 系向牛头充炭直'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 3 else SIMA, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    stamp(cv, seal('卖炭翁', 50, INK), 860, 1440, t, t - u + 0.4, rot=6)

def art_b_xinyuefu(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='sima')
    bai(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=90)
    n = min(50, int(clamp(u / (2.5 * P)) * 50) + 1)
    slips(A, 440, GROUND - 74, min(10, n // 5 + 1), 90, layer='fengye')
    A.flush(cv)
    paste(cv, text_img(f'新乐府五十首 · 第{cn_num(n)}首', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('文章合为时而著 歌诗合为事而作', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, 1, clamp((u - 1.5 * P) / 0.4))

def art_b_mother(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    bai(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    paste(cv, text_img('母丧 · 退居下邽守孝', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 江州司马
def art_b_wuyuanheng(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].rectangle((x - 60, GROUND - 160, x + 60, GROUND), fill=170)
    ground(A, GROUND)
    person(A, 540, GROUND, 190, dir=1, robe=True, hat='crown', fall=-80 * ease_out((u - P) / 0.4), arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('宰相武元衡遇刺于长安街头', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_demoted(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    bai(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 190, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('首上疏请急捕贼 · 以越职言事贬江州', SERIF, 42, SIMA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('江州司马', 44, INK), 860, 1020, t, t - u + P, rot=6)

def scene_pipa(cv, t, c, k):
    """8-beat custom scene: 浔阳江头 — maple leaves and reeds in autumn, a farewell party in a boat; a pipa sounds across the water;
    the player is invited over; the music rises like pearls falling on a jade plate; the host weeps until his robe is wet."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    r = 60
    A.d['wash'].ellipse((820 - r, 820 - r, 820 + r, 820 + r), fill=230)
    A.d['sima'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    waves(A, 1190, t, rows=3, amp=3, speed=0.6)
    for k2 in range(20):
        q = (t * 0.15 + k2 / 20) % 1
        A.d['fengye'].regular_polygon((80 + (k2 * 47) % 920, lerp(620, 1180, q), 10), 5, rotation=t * 50 + k2 * 20, fill=220)
    boat(A, 360, 1200, 160, t, sail=False)
    bai(A, 320, 1180, 120, dir=1, kneel=True, arm=-8 if ph < 6 else 150, bow=0 if ph < 6 else 30)
    bx = 760 if ph < 2.5 else lerp(760, 520, ease_out((ph - 2.5) / 1))
    boat(A, bx, 1210, 120, t, sail=False)
    person(A, bx, 1190, 110, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 10)), layer='fengye')
    pipa(A, bx - 30, 1130, 34, layer='mid')
    if 3.5 < ph < 6:
        for j in range(8):
            q = ((t * 1.5 + j / 8) % 1)
            A.d['wash'].ellipse((bx - 140 + j * 30 - 6, lerp(1000, 1180, q) - 6, bx - 140 + j * 30 + 6, lerp(1000, 1180, q) + 6), fill=int(255 * (1 - q)))
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '琵琶行', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=65)
    fx.flush(cv)
    lines = ['浔阳江头夜送客 枫叶荻花秋瑟瑟', '忽闻水上琵琶声', '大珠小珠落玉盘', '同是天涯沦落人 相逢何必曾相识', '江州司马青衫湿']
    k = 0 if ph < 1.5 else 1 if ph < 3.5 else 2 if ph < 5 else 3 if ph < 6.5 else 4
    paste(cv, text_img(lines[k], SERIF, 42, ZHU if k >= 3 else SIMA, 'Black', bleed=False, spacing=2), W / 2, 575, 1, 1)

def art_b_caotang(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 400), (x + 220, GROUND)], fill=170)
    A.d['mid'].rectangle((620, GROUND - 160, 860, GROUND), fill=230)
    A.d['ink'].polygon([(600, GROUND - 160), (880, GROUND - 160), (740, GROUND - 230)], fill=255)
    ground(A, GROUND)
    bai(A, 420, GROUND, 170, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('庐山香炉峰下 · 新置草堂', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('庐山', 56), 860, 1020, t, t - u + P, rot=6)

def art_b_peach(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 420), (x + 220, GROUND)], fill=170)
    for k in range(4):
        A.d['ink'].line((300 + k * 160, GROUND, 296 + k * 160, GROUND - 160), fill=255, width=6)
        A.d['pink'].ellipse((300 + k * 160 - 50, GROUND - 220, 300 + k * 160 + 50, GROUND - 140), fill=220)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('人间四月芳菲尽 山寺桃花始盛开', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('大林寺', 50), 860, 1020, t, t - u + P, rot=6)

def art_b_zhongzhou(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=3)
    for k in range(5):
        A.d['grass'].polygon([(180 + k * 160, 1240), (200 + k * 160, 1120), (220 + k * 160, 1240)], fill=200)
    bai(A, 600, 1240, 170, dir=1, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('迁忠州刺史 · 种花东坡', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '苏轼号东坡 即慕白居易', t, t - u + P)

# ================================================================ 第四回 杭州苏州
def art_b_hangzhou(A, cv, t, u):
    A.d['sima'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150)
    waves(A, 1170, t, rows=3, amp=3, speed=0.6)
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, 1160), (x, 1160 - 200), (x + 220, 1160)], fill=130)
    A.flush(cv)
    paste(cv, text_img('出为杭州刺史 · 最忆是杭州', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('杭州', 56), 860, 1020, t, t - u + P, rot=6)

def art_b_baidi(A, cv, t, u):
    """6-beat set piece: 白堤 — he dredges the lake and raises a dyke so the fields can be watered; willows grow along it."""
    ph = u / P
    A.d['sima'].rectangle((60, 1120, W - 60, GROUND + 40), fill=150)
    waves(A, 1130, t, rows=3, amp=3, speed=0.6)
    q = ease_out(clamp(ph / 3.5))
    A.d['mid'].polygon([(60, 1240), (60 + 900 * q, 1220), (60 + 900 * q, 1250), (60, 1270)], fill=230)
    for k in range(int(q * 8)):
        x = 120 + k * 110
        A.d['ink'].line((x, 1230, x, 1130), fill=255, width=5)
        for j in range(5):
            A.d['grass'].line((x, 1130, x - 20 + j * 10, 1200 + 6 * math.sin(t * 2 + j)), fill=230, width=2)
    for j in range(4):
        person(A, lerp(-100, 600, ((t * 0.08 + j / 4) % 1)), 1236, 80, dir=1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=160, layer='ink')
    A.flush(cv)
    lab = '筑堤捍湖 · 蓄水溉田千余顷' if ph < 4 else '谁开湖寺西南路 草绿裙腰一道斜'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4 else SIMA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '今西湖白堤非其所筑 世人以名纪之', t, t - u + P)

def art_b_suzhou(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=3)
    for k in range(4):
        A.d['mid'].rectangle((140 + k * 220, 1100, 280 + k * 220, 1240), fill=220)
        A.d['ink'].polygon([(120 + k * 220, 1100), (300 + k * 220, 1100), (210 + k * 220, 1050)], fill=255)
    boat(A, lerp(-100, 900, ((t * 0.08) % 1)), 1250, 50, t, sail=False)
    A.flush(cv)
    paste(cv, text_img('转苏州刺史 · 开山塘河 筑七里山塘', SERIF, 42, SIMA, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_b_jiangnan(A, cv, t, u):
    A.d['sima'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150)
    waves(A, 1170, t, rows=3, amp=3)
    r = 80
    A.d['red'].ellipse((800 - r, 900 - r, 800 + r, 900 + r), fill=180)
    for k in range(6):
        A.d['red'].ellipse((160 + k * 140 - 30, 1110, 160 + k * 140 + 30, 1150), fill=200)
    A.flush(cv)
    type_in(cv, text_img('日出江花红胜火 春来江水绿如蓝', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('忆江南', 50), 860, 1020, t, t - u + P, rot=6)

def art_b_oldwoman(A, cv, t, u):
    """6-beat set piece: 老妪能解 — every new poem is read aloud to an old woman; when she frowns he rewrites it."""
    ph = u / P
    ground(A, GROUND)
    A.d['mid'].rectangle((600, GROUND - 180, 900, GROUND), fill=200)
    bai(A, 360, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 4)))
    person(A, 640, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, kneel=True, bow=lerp(30, 0, clamp((ph - 3) / 0.5)), arm=lerp(-8, 80, clamp((ph - 3) / 0.5)), layer='mid')
    A.d['wash'].rectangle((440, GROUND - 180, 520, GROUND - 120), fill=255)
    A.flush(cv)
    lab = '每作诗 令一老妪解之' if ph < 3 else '问曰解否 · 解则录之 不解则易之'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3 else SIMA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '事见墨客挥犀 带传说色彩', t, t - u + P)

def art_b_famous(A, cv, t, u):
    ground(A, GROUND)
    for j in range(5):
        A.d['mid'].rectangle((140 + j * 180, GROUND - 160, 260 + j * 180, GROUND), fill=170)
        A.d['wash'].rectangle((160 + j * 180, GROUND - 140, 240 + j * 180, GROUND - 60), fill=255)
    A.flush(cv)
    paste(cv, text_img('自长安抵江西三四千里 · 凡乡校佛寺逆旅行舟之中 往往有题仆诗者', SERIF, 32, SIMA, 'Black', bleed=False, spacing=1), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 香山居士
def art_b_luoyang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='洛阳', layer='sima', open_=1.0)
    ground(A, GROUND)
    bai(A, 540, GROUND, 180, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('分司东都 · 远离党争', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_yuandies(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    bai(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=100, old=0.6)
    A.flush(cv)
    type_in(cv, text_img('君埋泉下泥销骨 我寄人间雪满头', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('元稹卒', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_b_xiangshan(A, cv, t, u):
    """6-beat set piece: 香山九老 — nine old men drink and write poems at the Xiangshan temple above the Yi river."""
    ph = u / P
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, 1180), (x, 1180 - 300), (x + 220, 1180)], fill=170)
    river(A, 1260, t, rows=2, amp=3)
    n = min(9, int(clamp(ph / 4) * 9) + 1)
    for i in range(n):
        sitter(A, 140 + i * 95, 1250, 90, dir=1 if i % 2 else -1, bow=15, layer='ink' if i == 4 else 'mid')
    A.flush(cv)
    paste(cv, text_img(f'香山九老会 · 第{cn_num(n)}老', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('香山居士', 44), 860, 1440, t, t - u + 0.4, rot=6)

def art_b_longmen(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    for i in range(int(clamp(u / (2 * P)) * 6) + 1):
        person(A, 160 + i * 140, 1240, 110, dir=1, robe=False, hat='knot', load=True, bow=40, arm=150, ph=t * 3 + i, layer='ink')
    A.flush(cv)
    paste(cv, text_img('散尽家财 开龙门八节石滩', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    bai(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于洛阳 · 年七十五', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_xuanzong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 200, dir=1, bow=20, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('童子解吟长恨曲 胡儿能唱琵琶篇', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('唐宣宗', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_b_3000(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='sima')
    n = int(clamp(u / P) * 12) + 1
    for i in range(n):
        bundle(A, 360 + (i % 6) * 70, GROUND - 74 - (i // 6) * 40, 50, layer='fengye')
    A.flush(cv)
    cnt = int(lerp(0, 2800, clamp(u / P)))
    paste(cv, text_img(f'存诗 {cnt} 余首 · 唐人之最', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_b_japan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    boat(A, lerp(200, 860, ease_out(u / (2 * P))), 1220, 120, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('白氏文集远传日本新罗', SERIF, 46, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_grass2(A, cv, t, u):
    grass(A, 120, 960, GROUND, 180 * ease_out(u / P) + 10, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('离离原上草 一岁一枯荣', SERIF, 48, SIMA, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_b_legacy(A, cv, t, u):
    grass(A, 640, 1000, 1440, 60, t)
    A.d['mid'].rectangle((60, 1430, W - 60, 1450), fill=150)

def art_b_title(A, cv, t, u):
    grass(A, 560, 1020, 1460, 120, t)
    A.d['mid'].rectangle((60, 1450, W - 60, 1470), fill=150)
    bai(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '居大不易'), 48: ('第二回', '新乐府'), 80: ('第三回', '江州司马'),
            112: ('第四回', '杭州苏州'), 144: ('第五回', '香山居士')}

CARDS = [
    C(0, 2, 'life', 'num', num='野火烧不尽', line='春风吹又生', art=art_b_hook_grass),
    C(2, 4, 'works', 'num', num='写一首诗', line='先念给老太太听', art=art_b_hook_old),
    C(4, 6, 'night', 'num', num='一曲琵琶', line='泪湿青衫', art=art_b_hook_pipa),
    C(6, 8, 'empire', 'num', num='近三千首', line='唐朝诗人第一', art=art_b_hook_3000),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 居大不易
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=772, main='生于新郑', sub='小官之家', art=art_b_birth),
    C(22, 26, 'works', 'card', year=773, main='识之无', sub='天生慧根', art=art_b_zhiwu),
    C(26, 30, 'fate', 'card', year=782, main='避乱江南', sub='流离', art=art_b_war),
    C(30, 34, 'night', 'card', year=785, main='苦读', sub='口舌成疮', art=art_b_study),
    C(34, 40, 'court', 'card', year=788, main='长安居', sub='大不易', art=art_b_guyong),
    C(40, 48, 'empire', 'card', year=800, main='进士及第', sub='十七人中最少年', art=art_b_jinshi),
    # ---- 第二回 新乐府
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'life', 'card', year=803, main='元白', sub='一生知己', art=art_b_yuanzhen),
    C(54, 58, 'night', 'card', year=806, main='长恨歌', sub='比翼连理', art=art_b_changhen),
    C(58, 62, 'war', 'card', year=808, main='左拾遗', sub='陛下错', note='见旧唐书 宪宗不悦', art=art_b_shiyi),
    C(62, 68, 'death', 'card', year=809, main='卖炭翁', sub='苦宫市也', art=art_b_charcoal),
    C(68, 74, 'works', 'card', year=809, main='新乐府', sub='为时而著', art=art_b_xinyuefu),
    C(74, 80, 'fate', 'card', year=811, main='丁母忧', sub='退居下邽', art=art_b_mother),
    # ---- 第三回 江州司马
    C(80, 82, 'fate', 'chapter'),
    C(82, 86, 'death', 'card', year=815, main='宰相遇刺', sub='长安血案', art=art_b_wuyuanheng),
    C(86, 90, 'fate', 'card', year=815, main='贬江州', sub='越职言事', art=art_b_demoted),
    C(90, 98, 'night', 'pipa', year=816),
    C(98, 102, 'life', 'card', year=817, main='庐山草堂', sub='香炉峰下', art=art_b_caotang),
    C(102, 106, 'works', 'card', year=817, main='大林寺桃花', sub='山寺春迟', art=art_b_peach),
    C(106, 112, 'court', 'card', year=819, main='忠州东坡', sub='种花', art=art_b_zhongzhou),
    # ---- 第四回 杭州苏州
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=822, main='杭州刺史', sub='最忆是杭州', art=art_b_hangzhou),
    C(118, 124, 'works', 'card', year=823, main='筑堤', sub='白堤', art=art_b_baidi),
    C(124, 128, 'court', 'card', year=825, main='苏州刺史', sub='七里山塘', art=art_b_suzhou),
    C(128, 132, 'life', 'card', year=826, main='忆江南', sub='江花江水', art=art_b_jiangnan),
    C(132, 138, 'night', 'card', year=826, main='老妪能解', sub='通俗', art=art_b_oldwoman),
    C(138, 144, 'empire', 'card', year=827, main='处处题诗', sub='流传之广', art=art_b_famous),
    # ---- 第五回 香山居士
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=829, main='分司东都', sub='洛阳', art=art_b_luoyang),
    C(150, 154, 'death', 'card', year=831, main='元稹去世', sub='雪满头', art=art_b_yuandies),
    C(154, 158, 'life', 'card', year=842, main='香山九老', sub='晚年雅集', art=art_b_xiangshan),
    C(158, 160, 'works', 'card', year=844, main='开龙门滩', sub='为民', art=art_b_longmen),
    C(160, 162, 'death', 'card', year=846, main='白居易去世', sub='洛阳', art=art_b_death),
    C(162, 164, 'court', 'card', year=846, main='宣宗悼诗', sub='童子解吟', art=art_b_xuanzong),
    C(164, 166, 'empire', 'card', year=846, main='近三千首', sub='白氏长庆集', art=art_b_3000),
    C(166, 168, 'fate', 'card', year=846, main='远传海外', sub='日本新罗', art=art_b_japan),
    C(168, 170, 'end', 'card', year=846, main='原上草', sub='一岁一枯荣', art=art_b_grass2),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾伍', col=SIMA, acc=FENGYE, born=772, died=846, age0=771,
    born_lab='772年', died_lab='846年', years_txt='公元772 — 846',
    hook_q='他的诗连老太太都听得懂 · 凭什么流传千年？',
    name_line='白居易 · 字乐天', name='白居易', seal='乐天', title_art=art_b_title,
    q1='平民诗人？', q2='太过浅白？',
    end_art=art_b_legacy, end_big='野火烧不尽', end_seal='乐天',
    end_l1='他把诗写得人人能懂', end_l2='于是人人都记住了他',
    end_brush='同是天涯沦落人', end_ask='你最早会背的白居易诗是哪首？评论区聊聊', next='王维'),
    scenes=dict(chapter=scene_chapter, pipa=scene_pipa))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
