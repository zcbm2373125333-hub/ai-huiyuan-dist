"""千古人物志 · 第肆拾贰集 · 魏征 (580–643)
Look: 铜镜金 + 谏纸白青, 铜镜 corner borders, a 三镜 chapter card: bronze mirror, then a history scroll, then a person —
the three mirrors of 唐太宗 appear one per chapter; in the last the third mirror cracks.
Set pieces: 6-beat 瓦岗, 6-beat 玄武门后, custom 8-beat scene 'jianshu' (二百余谏), 6-beat 怀中鹞, 6-beat 十渐疏,
6-beat 碑倒碑立.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_direnjie as Dr        # engine + helpers (previous episode)
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
from render_kongzi import bundle
from render_songtaizu import tent
from render_baozheng import stele

F.RIPPLE = False
MIRROR = (182, 146, 70)             # 铜镜金
JIAN = (84, 120, 132)               # 谏纸青
S.LAYERS.append(('mirror', MIRROR, 0.9, 1.0))
S.LAYERS.append(('jian', JIAN, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='镜', life='征', court='唐', night='谏', war='乱', empire='唐', works='谏', fate='直', death='镜', end='镜')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['empire']['sun'] = (MIRROR, 230, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JIAN, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

COLS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(COLS)
for _x in (100, 980):
    _d.rectangle((_x - 20, 1180, _x + 20, 1490), fill=JIAN + (40,))
    _d.ellipse((_x - 36, 1150, _x + 36, 1190), fill=MIRROR + (50,))
MTN_COL = {'night': (36, 38, 42), 'death': (60, 60, 62), 'war': (104, 70, 54), 'fate': (86, 98, 104)}
def draw_background(t, theme):
    """太极宫: soft ridges, two hall columns with bronze caps."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 188, 182), (150, 152, 148), MTN_COL.get(theme, (110, 118, 118))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(COLS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """铜镜: a round bronze mirror with a knob and a ribbon in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=JIAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=JIAN + (220,), width=3)
        cx, cy = x + sx * 54, y + sy * 54
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=MIRROR + (230,))
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), outline=(120, 90, 40, 230), width=2)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(120, 90, 40, 240))
        d.line((cx + sx * 6, cy, cx + sx * 50, cy + sy * 50), fill=ZHU + (220,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def wei(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """魏征: thin, upright; 进贤冠; a ribbon of memorial in hand; sparse beard."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.polygon([(x - dir * 0.07 * h, y - 0.95 * h), (x + dir * 0.06 * h, y - 0.95 * h), (x + dir * 0.02 * h, y - 1.12 * h), (x - dir * 0.06 * h, y - 1.06 * h)], fill=255)
        d.line((x + dir * 0.03 * h, y - 0.86 * h, x + dir * 0.06 * h, y - 0.7 * h), fill=255, width=max(2, int(0.02 * h)))
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.03 * h, y - 0.85 * h, x + dir * 0.06 * h, y - 0.72 * h), fill=255, width=max(2, int(0.015 * h)))
        hx, hy = hand
        A.d['jian'].rectangle((hx - 0.03 * h, hy - 0.18 * h, hx + 0.03 * h, hy), fill=255)
    return hand

def taizong(A, x, y, h, dir=1, layer='ink', **kw):
    hand = person(A, x, y, h, dir=dir, robe=True, hat='crown', layer=layer, **kw)
    if not kw.get('kneel') and not kw.get('fall') and not kw.get('bow'):
        A.d['mirror'].rectangle((x - 0.1 * h, y - 0.58 * h, x + 0.1 * h, y - 0.52 * h), fill=255)
        A.d[layer].polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.08 * h, y - 0.86 * h), (x + dir * 0.03 * h, y - 0.72 * h)], fill=255)
    return hand

def bronze_mirror(A, cx, cy, r, crack=0.0):
    A.d['mirror'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    A.d['ink'].ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=max(3, int(0.05 * r)))
    A.d['ink'].ellipse((cx - 0.75 * r, cy - 0.75 * r, cx + 0.75 * r, cy + 0.75 * r), outline=120, width=3)
    A.d['ink'].ellipse((cx - 0.12 * r, cy - 0.12 * r, cx + 0.12 * r, cy + 0.12 * r), fill=255)
    A.d['wash'].arc((cx - 0.6 * r, cy - 0.6 * r, cx + 0.3 * r, cy + 0.3 * r), 200, 260, fill=220, width=6)
    if crack > 0:
        pts = [(cx - 0.9 * r, cy - 0.3 * r), (cx - 0.3 * r, cy - 0.1 * r), (cx, cy + 0.2 * r), (cx + 0.4 * r, cy + 0.15 * r), (cx + 0.85 * r, cy + 0.5 * r)]
        n = max(2, int(len(pts) * crack + 0.5))
        A.d['ink'].line(pts[:n], fill=255, width=max(3, int(0.03 * r)))

def hawk(A, x, y, s, t, layer='ink'):
    d = A.d[layer]
    d.ellipse((x - 0.3 * s, y - 0.18 * s, x + 0.3 * s, y + 0.18 * s), fill=255)
    d.ellipse((x + 0.2 * s, y - 0.3 * s, x + 0.45 * s, y - 0.05 * s), fill=255)
    d.polygon([(x + 0.45 * s, y - 0.2 * s), (x + 0.58 * s, y - 0.14 * s), (x + 0.45 * s, y - 0.1 * s)], fill=255)
    d.polygon([(x - 0.3 * s, y), (x - 0.6 * s, y + 0.1 * s), (x - 0.3 * s, y + 0.12 * s)], fill=255)

# ================================================================ chapter card
def art_mirrors_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = {16: 0, 48: 1, 80: 2, 112: 3, 144: 3}.get(kb, 1)
    q = ease_out(u / (1.2 * P))
    xs = (300, 540, 780)
    for i in range(3):
        if i < n:
            if i == 0:
                bronze_mirror(A, xs[i], 1040, 110)
            elif i == 1:
                scroll(A, xs[i], 1040, 200, 180, 1.0, layer='wash')
            else:
                bronze_mirror(A, xs[i], 1040, 110, crack=q if kb == 144 else 0)
        else:
            A.d['mid'].ellipse((xs[i] - 110, 930, xs[i] + 110, 1150), outline=180, width=4)
    if n == 0:
        wei(A, 540, 1200, 240, dir=1, arm=40)
    ground(A, 1200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_mirrors_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MIRROR, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_m_hook_200(A, cv, t, u):
    ground(A, GROUND)
    n = min(200, int(clamp(u / (1.6 * P)) * 200) + 1)
    for i in range(n):
        x = 100 + (i % 40) * 22; y = GROUND - 10 - (i // 40) * 34
        A.d['jian'].rectangle((x - 8, y - 26, x + 8, y), fill=255)

def art_m_hook_kill(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='mirror')
    ground(A, GROUND)
    taizong(A, 540, GROUND, 260, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 5)))

def art_m_hook_mirror(A, cv, t, u):
    bronze_mirror(A, 540, 1040, 200, crack=ease_out(u / (1.6 * P)))
    ground(A, GROUND)

def art_m_hook_stele(A, cv, t, u):
    q = ease_out(u / (1.6 * P))
    stele(A, 540, GROUND, 240, 380 * (1 - q) + 40)
    ground(A, GROUND)

# ================================================================ 第一回 乱世辗转
def art_m_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 240), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    person(A, 540, GROUND, 150, dir=1, robe=False, hat='knot', arm=lerp(20, 100, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    A.flush(cv)
    stamp(cv, seal('巨鹿下曲阳', 40), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('少孤贫 · 落魄有大志', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_daoshi(A, cv, t, u):
    A.d['mid'].polygon([(300, GROUND), (540, 960), (780, GROUND)], fill=200)
    ground(A, GROUND)
    sitter(A, 540, GROUND - 20, 180, dir=1, bow=10)
    for k in range(12):
        q = (t * 0.3 + k / 12) % 1
        A.d['wash'].ellipse((540 + 60 * math.sin(k + t) - 14, lerp(1260, 900, q) - 10, 540 + 60 * math.sin(k + t) + 14, lerp(1260, 900, q) + 10), fill=int(160 * (1 - q)))
    A.flush(cv)
    stamp(cv, seal('出家为道士', 40), 860, 880, t, t - u + 0.4, rot=6)

def art_m_wagang(A, cv, t, u):
    """6-beat: 瓦岗 — the rebel stronghold on the hill; banners; he presents ten strategies; nobody listens."""
    ph = u / P
    A.d['mid'].polygon([(120, GROUND), (420, 960), (720, GROUND)], fill=210)
    tent(A, 420, 1060, 200, 160, layer='ink')
    for k in range(5):
        flag(A, 200 + k * 90, GROUND - 40 - k * 20, 220, t, w=50, layer='red')
    ground(A, GROUND)
    wei(A, 800, GROUND, 210, dir=-1, arm=lerp(40, 120, ease_out(ph / 1.5)))
    n = min(10, int(ph * 10 / 3) + 1)
    A.flush(cv)
    for i in range(n):
        stamp(cv, seal(cn_num(i + 1), 28, JIAN), 560 + (i % 5) * 70, 1180 + (i // 5) * 70, t, t - u + i * 0.3 * P)
    stamp(cv, seal('瓦岗李密', 44, INK), 260, 880, t, t - u + 0.4, rot=-5)
    if ph >= 3.5:
        paste(cv, text_img('献十策 · 不被采纳', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 3.5) / 0.3))

def art_m_tang(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    wei(A, lerp(-80, 540, ease_out(u / (2 * P))), GROUND, 210, dir=1, ph=t * 4 if u < 2 * P else None, arm=40)
    A.flush(cv)
    stamp(cv, seal('归唐', 54), 860, 880, t, t - u + P, rot=6)

def art_m_shandong(A, cv, t, u):
    city_wall(A, 520, 1000, 1100, gate_x=760, label='黎阳', layer='mid', open_=ease_out((u - P) / P))
    ground(A, GROUND)
    wei(A, 300, GROUND, 220, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    scroll(A, 520, 1000, 160, 60, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('李勣', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('一封信 劝降山东', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_dou(A, cv, t, u):
    ground(A, GROUND)
    for k in range(6):
        rider(A, lerp(1200, 600 + (k % 3) * 100, ease_out(u / (2 * P))), GROUND - (k // 3) * 40, 110, -1, t * 10 + k, layer='ink', spear=True)
    wei(A, 260, GROUND, 200, dir=1, kneel=u > 2 * P, bow=20, arm=-8)
    A.flush(cv)
    stamp(cv, seal('窦建德', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('被俘 · 辗转多主', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_jiancheng(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=40, layer='ink')
    wei(A, 340, GROUND, 220, dir=1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    stamp(cv, seal('太子李建成', 40), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('劝太子早除秦王', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

# ================================================================ 第二回 玄武门后
def art_m_xuanwu(A, cv, t, u):
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    city_wall(A, 160, 920, 1100, gate_x=540, label='玄武门', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        rider(A, lerp(-200, 460, ease_out((u - k * 0.1) / (2 * P))) - k * 70, GROUND, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('玄武门之变 · 太子被杀', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_question(A, cv, t, u):
    """6-beat: 汝何为离间我兄弟 — 李世民 confronts him; everyone fears for him; he answers calmly."""
    ph = u / P
    palace(A, 540, 1140, 560, layer='mirror')
    ground(A, GROUND)
    taizong(A, 720, GROUND - 30, 240, dir=-1, arm=lerp(40, 160, ease_out(ph / 0.8)))
    wei(A, 340, GROUND, 220, dir=1, arm=40)
    for k in range(4):
        person(A, 120 + k * 50, GROUND, 140, dir=1, robe=True, hat='none', bow=40, arm=100, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('汝何为离间我兄弟', SERIF, 46, INK, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.5)
    if ph >= 2.5:
        type_in(cv, text_img('太子早从征言 必无今日之祸', SERIF, 42, JIAN, 'Black', bleed=False, spacing=2), W / 2, 840, t, t - u + 2.5 * P, 0.5)
    if ph >= 4.5:
        paste(cv, text_img('李世民反而敬重他', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.3))

def art_m_zhanshi(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    taizong(A, 720, GROUND - 30, 230, dir=-1, arm=lerp(20, 100, ease_out(u / 0.6)))
    wei(A, 360, GROUND, 220, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('詹事主簿', 44), 260, 880, t, t - u + P, rot=-5)

def art_m_hebei(A, cv, t, u):
    ground(A, GROUND)
    carriage(A, lerp(-150, 540, ease_out(u / (2 * P))), GROUND, 130, dir=1, wheel=t * 4, ph=t * 6, moving=u < 2 * P, layer='ink')
    for k in range(2):
        person(A, 760 + k * 90, GROUND, 160, dir=-1, robe=False, hat='knot', arm=40, layer='mid')
        A.d['ink'].rectangle((730 + k * 90, GROUND - 120, 790 + k * 90, GROUND - 100), fill=255)
    A.flush(cv)
    stamp(cv, seal('安抚河北', 44), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('私放囚车 · 安定人心', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_liangchen(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mirror')
    ground(A, GROUND)
    taizong(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    wei(A, 360, GROUND, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    type_in(cv, text_img('愿陛下使臣为良臣', SERIF, 46, JIAN, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('勿使臣为忠臣', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 840, t, t - u + 1.5 * P, 0.5)

def art_m_jianming(A, cv, t, u):
    ground(A, GROUND)
    taizong(A, 540, GROUND - 30, 230, dir=1, arm=40)
    for k in range(3):
        person(A, 160 + k * 90, GROUND, 160, dir=1, robe=True, hat='none', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + k)), layer='mid')
    wei(A, 860, GROUND, 220, dir=-1, arm=60)
    A.flush(cv)
    type_in(cv, text_img('兼听则明 偏信则暗', SERIF, 52, JIAN, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, 0.5)

# ================================================================ 第三回 犯颜直谏
JIAN_TOPICS = ['罢修洛阳宫', '停封禅', '止选秀女', '戒奢侈', '慎刑罚', '轻徭役', '纳忠言', '居安思危']
def scene_jianshu(cv, t, c, k):
    """8-beat custom scene: 二百余谏 — scrolls fly up one per beat with a topic; the emperor's mood (a small sun/cloud)
    swings; at the end the tally reads 二百余事 数十万言."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    palace(A, 540, 1080, 620, layer='mirror')
    ground(A, GROUND)
    taizong(A, 760, GROUND - 30, 230, dir=-1, arm=lerp(20, 140, 0.5 + 0.5 * math.sin(t * 2)))
    wei(A, 300, GROUND, 230, dir=1, kneel=True, bow=20, arm=lerp(90, 140, 0.5 + 0.5 * math.sin(t * 4)))
    A.flush(cv)
    n = min(len(JIAN_TOPICS), int(ph) + 1)
    for i in range(n):
        x = 160 + (i % 4) * 250; y = 820 + (i // 4) * 90
        stamp(cv, seal(JIAN_TOPICS[i], 26, JIAN if i % 2 else MIRROR), x, y, t, s0 + i * P)
    fx = Art()
    chars_in(cv, fx, '犯颜直谏', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=63)
    fx.flush(cv)
    total = int(lerp(1, 200, clamp(ph / 7.5)))
    paste(cv, text_img(f'第 {total} 谏' if total < 200 else '前后陈谏二百余事', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('贞观年间 · 君臣相得', SERIF, 42, JIAN, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_m_hawk(A, cv, t, u):
    """6-beat legend: 怀中鹞 — the emperor plays with a hawk; sees 魏征 coming, hides it in his robe; 魏征 talks on and on;
    the hawk suffocates."""
    ph = u / P
    ground(A, GROUND)
    x = 700
    taizong(A, x, GROUND - 0, 240, dir=-1, arm=lerp(60, 30, ease_out((ph - 1) / 0.6)))
    if ph < 1.2:
        hawk(A, x - 80, GROUND - 200, 70, t)
    wei(A, lerp(-80, 360, ease_out(ph / 1.5)), GROUND, 220, dir=1, ph=t * 4 if ph < 1.5 else None, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4)))
    A.flush(cv)
    stamp(cv, seal('传说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    if ph >= 2:
        paste(cv, text_img('奏事良久 · 鹞竟死怀中', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 2) / 0.3))

def art_m_kill(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='mid')
    ground(A, GROUND)
    taizong(A, 360, GROUND, 240, dir=1, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 5)))
    person(A, 720, GROUND, 220, dir=-1, robe=True, hat='crown', female=True, kneel=u > 1.5 * P, bow=30, arm=110, layer='ink')
    A.flush(cv)
    type_in(cv, text_img('会须杀此田舍翁', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, t, t - u + 0.4, 0.5)
    if u > 1.5 * P:
        type_in(cv, text_img('主明臣直 · 长孙皇后贺之', SERIF, 42, JIAN, 'Black', bleed=False, spacing=2), W / 2, 840, t, t - u + 1.5 * P, 0.5)

def art_m_luoyang(A, cv, t, u):
    palace(A, 540, GROUND, 580, collapse=ease_out((u - P) / (2 * P)) * 0.5, layer='mirror')
    ground(A, GROUND)
    for k in range(5):
        person(A, 160 + k * 180, GROUND, 110, dir=1, robe=False, hat='knot', load=True, ph=t * 5 + k, arm=160, layer='mid')
    A.flush(cv)
    stamp(cv, seal('罢修宫殿', 46), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('劝止大兴土木', SERIF, 46, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_boat(A, cv, t, u):
    river(A, 1180, t, rows=4, amp=int(lerp(4, 14, 0.5 + 0.5 * math.sin(t))), speed=2.4)
    boat(A, 540, 1240, 160, t * 2, sail=True)
    taizong(A, 540, 1210, 130, dir=1, arm=40)
    A.flush(cv)
    type_in(cv, text_img('水能载舟 亦能覆舟', SERIF, 52, JIAN, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('荀子语', 40, INK), 860, 1040, t, t - u + P, rot=6)

def art_m_shizhen(A, cv, t, u):
    """6-beat set piece: 十渐不克终疏 — ten scrolls unfold side by side; the emperor reads; he has it written on a screen."""
    ph = u / P
    ground(A, GROUND)
    n = min(10, int(ph * 10 / 3.5) + 1)
    for i in range(n):
        x = 120 + i * 92
        A.d['wash'].rectangle((x - 36, 920, x + 36, 1200), fill=255)
        A.d['jian'].rectangle((x - 40, 910, x + 40, 920), fill=255)
        A.d['jian'].rectangle((x - 40, 1200, x + 40, 1210), fill=255)
    if ph >= 4:
        A.d['mirror'].rectangle((300, 1220, 780, 1250), fill=255)
    A.flush(cv)
    for i in range(n):
        paste(cv, text_img('渐' + cn_num(i + 1), SERIF, 30, INK, 'Black', bleed=False, vertical=True), 120 + i * 92, 1060, 1, 1)
    if ph >= 4:
        paste(cv, text_img('太宗书于屏障 朝夕瞻仰', SERIF, 44, JIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 4) / 0.3))

# ================================================================ 第四回 以人为镜
def art_m_house(A, cv, t, u):
    A.d['mid'].rectangle((360, 1080, 720, GROUND), fill=200)
    A.d['ink'].polygon([(330, 1080), (750, 1080), (540, 1000)], fill=255)
    ground(A, GROUND)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        person(A, lerp(-100, 200 + k * 30, ease_out((u - k * 0.1) / P)), GROUND, 110, dir=1, robe=False, hat='knot', load=True, ph=t * 5 + k, arm=160, layer='mid')
    A.flush(cv)
    stamp(cv, seal('家无正堂', 44), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('太宗停建小殿 · 为他造正堂', SERIF, 42, JIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_ill(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wei(A, 540, 1200, 220, dir=1, fall=-80, arm=-8, old=0.8)
    taizong(A, 860, GROUND, 220, dir=-1, arm=lerp(40, 110, ease_out(u / P)))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('太宗亲临探病', SERIF, 48, JIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_m_marry(A, cv, t, u):
    ground(A, GROUND)
    taizong(A, 720, GROUND - 30, 230, dir=-1, arm=40)
    person(A, 460, GROUND, 200, dir=1, robe=True, hat='crown', female=True, arm=40, layer='ink')
    A.d['red'].line((500, GROUND - 160, 660, GROUND - 160), fill=255, width=6)
    A.flush(cv)
    paste(cv, text_img('许以衡山公主 嫁其子', SERIF, 46, MIRROR, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_m_death(A, cv, t, u):
    for k in range(40):
        q = (t * 0.4 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=220)
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wei(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, old=1.0)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('病逝 · 年六十四', SERIF, 50, JIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_three_mirrors(A, cv, t, u):
    """6-beat set piece: 三镜 — 以铜为镜 · 以古为镜 · 以人为镜; the third mirror cracks and falls."""
    ph = u / P
    xs = (240, 540, 840)
    bronze_mirror(A, xs[0], 1040, 100)
    scroll(A, xs[1], 1040, 180, 160, 1.0, layer='wash')
    crack = ease_out((ph - 3.5) / 1)
    bronze_mirror(A, xs[2], 1040 + 160 * ease_out((ph - 4.5) / 1), 100, crack=crack)
    ground(A, GROUND)
    taizong(A, 540, GROUND, 200, dir=1, bow=lerp(0, 30, ease_out((ph - 4) / 1)), arm=lerp(20, 120, ease_out((ph - 4) / 1)))
    A.flush(cv)
    for i, ln in enumerate(('以铜为镜 正衣冠', '以古为镜 知兴替', '以人为镜 明得失')):
        type_in(cv, text_img(ln, SERIF, 30, ZHU if i == 2 else INK, 'Black', bleed=False, vertical=True, spacing=2), xs[i], 820, t, t - u + 0.3 + i * P, 0.4)
    if ph >= 5:
        paste(cv, text_img('遂亡一镜矣', SERIF, 50, ZHU, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((ph - 5) / 0.3))

def art_m_stele_up(A, cv, t, u):
    stele(A, 540, GROUND, 260, 420 * ease_out(u / (1.5 * P)) + 10)
    ground(A, GROUND)
    taizong(A, 860, GROUND, 220, dir=-1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    stamp(cv, seal('亲撰碑文', 44), 260, 880, t, t - u + P, rot=-5)

# ================================================================ 第五回 碑仆碑立
def art_m_stele_fall(A, cv, t, u):
    """6-beat: 推倒碑 — his recommended men fall into a plot; the emperor's suspicion; the stele is pulled down."""
    ph = u / P
    fall = ease_out((ph - 2) / 1.5)
    cx, base = 540, GROUND
    hgt = 420
    ang = fall * math.pi / 2 * 0.95
    pts = [(-130, 0), (130, 0), (130, -hgt), (-130, -hgt)]
    A.d['jian'].polygon([(cx + 130 + (px - 130) * math.cos(ang) - py * math.sin(ang), base + (px - 130) * math.sin(ang) + py * math.cos(ang)) for px, py in pts], fill=230)
    for k in range(3):
        person(A, 200 + k * 60, GROUND, 160, dir=1, robe=False, hat='helmet', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('侯君集', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('所荐之人谋反 · 太宗推倒碑' if ph >= 2 else '杜正伦 侯君集 皆其所荐', SERIF, 44, ZHU if ph >= 2 else JIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_m_liaodong(A, cv, t, u):
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(900, -200, ease_out(u / (3 * P))) + (k % 4) * 90, GROUND - (k // 4) * 40, 100, -1, t * 6 + k, layer='mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('征高句丽', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('无功而返', SERIF, 50, JIAN, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_m_regret(A, cv, t, u):
    for k in range(30):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    tent(A, 540, GROUND, 600, 400, layer='mid')
    ground(A, GROUND)
    taizong(A, 540, GROUND, 240, dir=1, bow=20, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t)))
    A.flush(cv)
    type_in(cv, text_img('魏征若在 不使我有是行也', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)

def art_m_restored(A, cv, t, u):
    q = ease_out(u / (2 * P))
    stele(A, 540, GROUND, 260, 420 * q + 20)
    ground(A, GROUND)
    for k in range(4):
        person(A, 160 + k * 60 if k < 2 else 860 + (k - 2) * 60, GROUND, 140, dir=1 if k < 2 else -1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 4 + k)), layer='mid')
    A.flush(cv)
    stamp(cv, seal('复立其碑', 46), 860, 880, t, t - u + P, rot=6)

def art_m_zhenguan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='jian')
    sitter(A, 300, GROUND, 200, dir=1, bow=15)
    for i in range(int(clamp(u / (2 * P)) * 5) + 1):
        bundle(A, 440 + i * 50, GROUND - 74, 40, layer='mirror')
    A.flush(cv)
    ink_in(cv, text_img('贞观政要', SERIF, 50, JIAN, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.5, dur=0.3)
    paste(cv, text_img('吴兢辑录君臣问答', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

def art_m_legacy(A, cv, t, u):
    bronze_mirror(A, 880, 1380, 90)

def art_m_title(A, cv, t, u):
    bronze_mirror(A, 820, 1200, 140)
    wei(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '乱世辗转'), 48: ('第二回', '玄武门后'), 80: ('第三回', '犯颜直谏'),
            112: ('第四回', '以人为镜'), 144: ('第五回', '碑仆碑立')}

CARDS = [
    C(0, 2, 'works', 'num', num='二百余谏', line='皇帝全听了', art=art_m_hook_200),
    C(2, 4, 'court', 'num', num='会须杀此', line='田舍翁', art=art_m_hook_kill),
    C(4, 6, 'night', 'num', num='一面镜子', line='他死时碎了', art=art_m_hook_mirror),
    C(6, 8, 'death', 'num', num='死后推碑', line='又亲手立起', art=art_m_hook_stele),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 乱世辗转
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=580, main='生于巨鹿', sub='少年孤贫', art=art_m_birth),
    C(22, 26, 'fate', 'card', year=600, main='出家为道', sub='好读书 · 通纵横之术', art=art_m_daoshi),
    C(26, 32, 'war', 'card', year=617, main='投奔瓦岗', sub='隋末天下大乱', art=art_m_wagang),
    C(32, 36, 'court', 'card', year=618, main='随李密降唐', sub='自请安抚山东', art=art_m_tang),
    C(36, 40, 'works', 'card', year=619, main='劝降李勣', sub='黎阳归唐', art=art_m_shandong),
    C(40, 44, 'night', 'card', year=619, main='辗转被俘', sub='窦建德攻陷黎阳', art=art_m_dou),
    C(44, 48, 'court', 'card', year=621, main='太子洗马', sub='辅佐李建成', art=art_m_jiancheng),
    # ---- 第二回 玄武门后
    C(48, 50, 'night', 'chapter'),
    C(50, 54, 'war', 'card', year=626, main='玄武门', sub='秦王夺嫡', art=art_m_xuanwu),
    C(54, 60, 'court', 'card', year=626, main='兄弟之问', sub='生死一线', art=art_m_question),
    C(60, 64, 'empire', 'card', year=626, main='不计前嫌', sub='反被重用', art=art_m_zhanshi),
    C(64, 68, 'works', 'card', year=626, main='安抚河北', sub='赦免旧党', art=art_m_hebei),
    C(68, 74, 'court', 'card', year=627, main='良臣忠臣', sub='他请求做良臣', note='良臣身获美名 君受显号', art=art_m_liangchen),
    C(74, 80, 'works', 'card', year=628, main='兼听则明', sub='何谓明君暗君', art=art_m_jianming),
    # ---- 第三回 犯颜直谏
    C(80, 82, 'works', 'chapter'),
    C(82, 90, 'night', 'jianshu', year=630),
    C(90, 96, 'life', 'card', year=632, main='怀中鹞', sub='皇帝也怕他', art=art_m_hawk),
    C(96, 100, 'death', 'card', year=632, main='田舍翁', sub='太宗退朝大怒', art=art_m_kill),
    C(100, 104, 'works', 'card', year=634, main='罢修洛阳', sub='劝止营建', art=art_m_luoyang),
    C(104, 108, 'fate', 'card', year=636, main='载舟覆舟', sub='常以此告诫太宗', art=art_m_boat),
    C(108, 112, 'works', 'card', year=639, main='十渐疏', sub='十渐不克终疏', art=art_m_shizhen),
    # ---- 第四回 以人为镜
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'life', 'card', year=642, main='家无正堂', sub='一生清俭', art=art_m_house),
    C(118, 122, 'death', 'card', year=643, main='病重', sub='卧床不起', art=art_m_ill),
    C(122, 126, 'court', 'card', year=643, main='许婚', sub='太宗许以公主', art=art_m_marry),
    C(126, 130, 'death', 'card', year=643, main='病逝', sub='谥文贞', art=art_m_death),
    C(130, 136, 'night', 'card', year=643, main='三镜', sub='太宗痛哭', art=art_m_three_mirrors),
    C(136, 144, 'empire', 'card', year=643, main='御书碑文', sub='图像凌烟阁', art=art_m_stele_up),
    # ---- 第五回 碑仆碑立
    C(144, 146, 'death', 'chapter'),
    C(146, 152, 'night', 'card', year=643, main='推倒碑', sub='疑心骤起', note='又悔婚约', art=art_m_stele_fall),
    C(152, 156, 'war', 'card', year=645, main='东征受挫', sub='辽东归来', art=art_m_liaodong),
    C(156, 160, 'fate', 'card', year=645, main='若魏征在', sub='太宗悔叹', art=art_m_regret),
    C(160, 164, 'empire', 'card', year=645, main='复立碑', sub='遣使祭奠', art=art_m_restored),
    C(164, 170, 'works', 'card', year=720, main='贞观政要', sub='后世帝王必读', art=art_m_zhenguan),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾贰', col=JIAN, acc=MIRROR, born=580, died=643,
    hook_q='敢骂皇帝两百次 · 他为什么没被杀？',
    name_line='魏征 · 字玄成', name='魏征', seal='文贞', title_art=art_m_title,
    q1='千古诤臣？', q2='沽名钓誉？',
    end_art=art_m_legacy, end_big='以人为镜', end_seal='文贞',
    end_l1='他敢说 皇帝也敢听', end_l2='这才有了贞观之治',
    end_brush='兼听则明', end_ask='你身边有敢说真话的人吗？评论区聊聊', next='唐玄宗'),
    scenes=dict(chapter=scene_chapter, jianshu=scene_jianshu))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
