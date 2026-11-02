"""千古人物志 · 第叁拾伍集 · 辛弃疾 (1140–1207)
Look: 铁锈红 + 剑光银, 剑穗 corner borders, a 宝剑 chapter card: the sword is drawn further each chapter, then
slowly re-sheathed and hung on the wall ("把吴钩看了 栏杆拍遍").
Set pieces: custom 8-beat scene 'raid' (五十骑闯五万人营 擒叛徒), 6-beat 南归, 6-beat 美芹十论, 8-beat 飞虎军,
6-beat 栏杆拍遍, 6-beat 醉里挑灯看剑, 6-beat 临终呼杀贼.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_liqingzhao as Lq      # engine + helpers (previous episode)
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
from render_quyuan import river
from render_libai import wine_jar, moon_phase
from render_simaqian import bars
from render_kongzi import bundle

F.RIPPLE = False
RUST = (156, 64, 44)                # 铁锈红
STEELB = (150, 166, 180)            # 剑光银
S.LAYERS.append(('rust', RUST, 0.88, 1.0))
S.LAYERS.append(('blade', STEELB, 0.92, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='辛', life='稼', court='宋', night='剑', war='戰', empire='宋', works='词', fate='闲', death='恨', end='辛')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end', 'court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'ash'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'snow'
G.THEMES['war']['sun'] = (RUST, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (STEELB, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['fate']['sun'] = None
G.THEMES['end']['sun'] = (RUST, 200, (W * 0.5, 720))
G.base_bg.cache_clear()

TOWERS = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(TOWERS)
for _x in (110, 970):
    _d.rectangle((_x - 40, 1260, _x + 40, 1480), fill=RUST + (36,))
    _d.polygon([(_x - 60, 1260), (_x + 60, 1260), (_x, 1200)], fill=RUST + (44,))
    _d.line((_x - 60, 1340, _x + 60, 1340), fill=RUST + (60,), width=4)
MTN_COL = {'night': (36, 34, 38), 'death': (60, 58, 58), 'war': (108, 56, 44), 'fate': (86, 90, 96)}
def draw_background(t, theme):
    """江南边楼: ranges with lookout towers (建康赏心亭) at both margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(190, 184, 180), (152, 140, 134), MTN_COL.get(theme, (114, 98, 90))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 7 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(TOWERS)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """剑穗: a sword-tassel hanging from a ring in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=STEELB + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=STEELB + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 30
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), outline=STEELB + (240,), width=4)
        d.line((cx, cy + sy * 12, cx, cy + sy * 50), fill=RUST + (230,), width=4)
        for k in range(5):
            d.line((cx, cy + sy * 50, cx + (k - 2) * 6, cy + sy * 90), fill=RUST + (230,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xin(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, old=0.0, sword_on=True, **kw):
    """辛弃疾: tall and burly ('肌肤丰泽'), beard; armoured in youth, scholar's cap later; sword at the hip."""
    b = bow + 14 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat=('helmet' if armour else 'none') if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        if not armour:
            d.rectangle((x - 0.07 * h, y - 1.04 * h, x + 0.07 * h, y - 0.94 * h), fill=255)
        else:
            A.d['rust'].polygon([(x - dir * 0.05 * h, y - 0.82 * h), (x - dir * 0.26 * h, y - 0.2 * h), (x - dir * 0.06 * h, y - 0.24 * h)], fill=255)
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.09 * h, y - 0.86 * h), (x + dir * 0.05 * h, y - 0.64 * h)], fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.01 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.68 * h)], fill=255)
    if sword_on and up and not kw.get('sword'):
        A.d['blade'].line((x - dir * 0.26 * h, y - 0.2 * h, x + dir * 0.12 * h, y - 0.52 * h), fill=255, width=max(3, int(0.02 * h)))
    return hand

def sword(A, cx, cy, s, drawn, ang=0.0):
    """scabbard + blade; drawn 0..1 = how far the blade slides out to the right."""
    c, sn = math.cos(ang), math.sin(ang)
    def R(u, v): return (cx + u * c - v * sn, cy + u * sn + v * c)
    A.d['rust'].polygon([R(-s, -0.04 * s), R(0.1 * s, -0.04 * s), R(0.1 * s, 0.04 * s), R(-s, 0.04 * s)], fill=255)
    A.d['ink'].polygon([R(0.1 * s, -0.12 * s), R(0.16 * s, -0.12 * s), R(0.16 * s, 0.12 * s), R(0.1 * s, 0.12 * s)], fill=255)
    A.d['ink'].polygon([R(0.16 * s, -0.035 * s), R(0.42 * s, -0.035 * s), R(0.42 * s, 0.035 * s), R(0.16 * s, 0.035 * s)], fill=255)
    off = drawn * 1.0 * s
    if drawn > 0:
        A.d['blade'].polygon([R(0.1 * s - off * 0 - 0, -0.03 * s), R(0.1 * s - off * 0, 0.03 * s), R(-s + off + 0.0 - 0.0, 0.03 * s), R(-s + off - 0.12 * s, 0), R(-s + off, -0.03 * s)], fill=255)
        A.d['rust'].polygon([R(-s + off, -0.045 * s), R(0.1 * s, -0.045 * s), R(0.1 * s, 0.045 * s), R(-s + off, 0.045 * s)], fill=0)

def rail(A, x0, x1, y, layer='rust'):
    A.d[layer].rectangle((x0, y - 12, x1, y), fill=255)
    for k in range(int((x1 - x0) / 60) + 1):
        A.d[layer].rectangle((x0 + k * 60 - 5, y, x0 + k * 60 + 5, y + 90), fill=255)
    A.d[layer].rectangle((x0, y + 80, x1, y + 90), fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.0), 48: (0.6, 0.0), 80: (1.0, 0.0), 112: (0.3, 0.0), 144: (0.0, 1.0)}
def art_sword_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    drawn, hung = CH.get(kb, (0.6, 0.0))
    q = ease_out(u / (1.2 * P))
    if hung:
        A.d['mid'].rectangle((160, 820, 920, 1220), fill=150)
        A.d['ink'].line((540, 840, 540, 880), fill=255, width=4)
        sword(A, 540, 900 + 40 * q, 320, 0.0, ang=0.05)
        A.d['wash'].rectangle((160, 820, 920, 1220), fill=int(60 * q))
    else:
        prev = {48: 0.0, 80: 0.6, 112: 1.0}.get(kb, 0.0)
        sword(A, 640, 1000, 380, lerp(prev, drawn, q), ang=-0.12)
        if drawn >= 1.0:
            for k in range(10):
                a = -0.12 + (k - 5) * 0.03
                A.d['blade'].line((260, 1040, 260 - 120 * math.cos(a), 1040 + 120 * math.sin(a) - 40), fill=int(160 * (0.5 + 0.5 * math.sin(t * 6 + k))), width=2)
    ground(A, GROUND)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_sword_chapter)
    ink_in(cv, text_img(no, SERIF, 56, RUST, 'Black', bleed=False, spacing=12), W / 2, 1290, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_50(A, cv, t, u):
    ground(A, GROUND)
    for i in range(50):
        x = 100 + (i % 10) * 22; y = GROUND - (i // 10) * 22
        A.d['rust'].ellipse((x - 8, y - 16, x + 8, y), fill=255)
    n = min(400, int(clamp(u / (1.6 * P)) * 400))
    for i in range(n):
        x = 440 + (i % 30) * 18; y = GROUND - (i // 30) * 18
        A.d['mid'].ellipse((x - 6, y - 12, x + 6, y), fill=200)

def art_x_hook_words(A, cv, t, u):
    ground(A, GROUND)
    n = min(620, int(clamp(u / (1.6 * P)) * 620) + 1)
    for i in range(0, n, 4):
        x = 100 + ((i // 4) % 25) * 36; y = GROUND - 20 - ((i // 4) // 25) * 40
        A.d['rust' if (i // 4) % 7 else 'blade'].rectangle((x - 12, y - 30, x + 12, y), fill=255)

def art_x_hook_rail(A, cv, t, u):
    rail(A, 160, 920, 1160)
    xin(A, 540, 1160, 260, dir=1, arm=lerp(60, 150, abs(math.sin(t * 4))), old=0.3)
    ground(A, GROUND)

def art_x_hook_kill(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xin(A, 540, 1200, 220, dir=1, fall=-70, arm=lerp(60, 150, ease_out(u / (1.2 * P))), old=1.0)
    ground(A, GROUND)

# ================================================================ 第一回 沦陷区少年
def art_x_birth(A, cv, t, u):
    city_wall(A, 120, 960, 1100, gate_x=540, label='历城', layer='mid')
    ground(A, GROUND)
    flag(A, 540, 1100, 200, t, w=70, layer='ink')
    A.flush(cv)
    stamp(cv, seal('金国治下', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('出生时 北方已沦陷十三年', SERIF, 44, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_grandpa(A, cv, t, u):
    for k in range(3):
        A.d['mid'].polygon([(200 + k * 320 - 200, GROUND), (200 + k * 320, GROUND - 280), (200 + k * 320 + 200, GROUND)], fill=200)
    ground(A, GROUND)
    person(A, 420, GROUND, 250, dir=1, robe=True, hat='none', arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 1.5)), layer='ink')
    person(A, 560, GROUND, 140, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('辛赞', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('登高望远 指画山河', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_scout(A, cv, t, u):
    city_wall(A, 360, 1000, 1100, gate_x=680, label='燕京', layer='mid')
    ground(A, GROUND)
    xin(A, lerp(-80, 300, ease_out(u / (2 * P))), GROUND, 190, dir=1, ph=t * 4, arm=-8)
    A.flush(cv)
    stamp(cv, seal('两赴燕京', 44), 260, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('借赶考之名 察看金国虚实', SERIF, 44, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_rise(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 20) + 1
    for i in range(n):
        x = lerp(-60, 300 + (i % 10) * 50, ease_out((u - i * 0.04) / (2.5 * P))); y = GROUND - (i // 10) * 40
        person(A, x, y, 90, dir=1, robe=False, hat='knot', spear=True, ph=t * 5 + i, arm=40, layer='ink' if i // 10 == 0 else 'mid')
    xin(A, 860, GROUND, 230, dir=-1, armour=True, arm=lerp(40, 160, 0.5 + 0.5 * math.sin(t * 2)), sword=60)
    A.flush(cv)
    paste(cv, text_img('聚众二千 起兵抗金', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_gengjing(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 240, dir=-1, robe=False, hat='helmet', arm=lerp(20, 100, ease_out(u / P)), layer='ink')
    xin(A, 380, GROUND, 230, dir=1, armour=True, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('耿京', 54), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('掌书记', 46), 260, 880, t, t - u + P, rot=-5)

def art_x_yiduan(A, cv, t, u):
    ground(A, GROUND)
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    horse(A, lerp(500, 1150, ease_out(u / (1.5 * P))), GROUND, 140, dir=1, ph=t * 12, layer='mid')
    x = lerp(200, 900, ease_out((u - P) / (2 * P)))
    horse(A, x, GROUND, 160, dir=1, ph=t * 12, layer='ink')
    xin(A, x - 10, GROUND - 125, 150, dir=1, armour=True, arm=150, sword=120)
    A.flush(cv)
    stamp(cv, seal('义端', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('盗印而逃 · 追斩之', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - 2 * P) / 0.3))

def art_x_envoy(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='rust')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 90, ease_out(u / P)), layer='ink')
    xin(A, 360, GROUND, 220, dir=1, armour=True, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('奉表南归', 46), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('宋高宗', 46, INK), 860, 880, t, t - u + P, rot=6)

# ================================================================ 第二回 万人取首
def scene_raid(cv, t, c, k):
    """8-beat custom scene: 五十骑擒叛将 — news that 耿京 was murdered by 张安国; fifty riders gallop to a camp of fifty
    thousand; they burst in, seize the traitor at his banquet, tie him to a horse, and ride out under the moon."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(40):
        A.d['wash'].ellipse((80 + (k2 * 37) % 920 - 2, 640 + (k2 * 53) % 300 - 2, 80 + (k2 * 37) % 920 + 2, 640 + (k2 * 53) % 300 + 2), fill=255)
    moon_phase(A, 860, 760, 60, 1.0)
    for i in range(6):
        tent(A, 300 + i * 120, GROUND - (i % 2) * 40, 110, 90, layer='mid')
    for i in range(30):
        x = 260 + (i % 15) * 46; y = GROUND - 120 - (i // 15) * 30
        A.d['mid'].ellipse((x - 6, y - 12, x + 6, y), fill=180)
    ground(A, GROUND)
    if ph < 3:
        x = lerp(-300, 360, ease_out(ph / 3))
        for j in range(6):
            rider(A, x - j * 70, GROUND - (j % 2) * 30, 110, 1, t * 13 + j, layer='rust' if j else 'ink', spear=True)
    elif ph < 5:
        A.d['gold'].rectangle((520, GROUND - 60, 700, GROUND - 46), fill=255)
        person(A, 640, GROUND, 180, dir=-1, robe=True, hat='none', arm=lerp(40, 150, ease_out((ph - 3) / 0.4)), fall=-30 * ease_out((ph - 3.6) / 0.5), layer='ink')
        xin(A, 480, GROUND, 230, dir=1, armour=True, arm=160, sword=lerp(40, 150, ease_out((ph - 3) / 0.4)))
    else:
        x = lerp(360, 1300, ease_out((ph - 5) / 2.5))
        for j in range(6):
            rider(A, x - j * 70, GROUND - (j % 2) * 30, 110, 1, t * 13 + j, layer='rust' if j else 'ink', spear=True)
        A.d['ink'].line((x - 30, GROUND - 120, x + 30, GROUND - 120), fill=255, width=14)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '万人取首', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=101)
    fx.flush(cv)
    lab = '五十骑 夜闯五万人大营' if ph < 3 else ('缚叛将张安国于席上' if ph < 5 else '渡淮南归 交付朝廷')
    paste(cv, text_img(lab, SERIF, 46, RUST if ph < 5 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元一一六二年 · 年二十三', SERIF, 42, STEELB, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_x_south(A, cv, t, u):
    """6-beat: 南归 — the 淮河; the band crosses on boats; the far bank is 南宋; he looks back north."""
    ph = u / P
    river(A, 1180, t, rows=4, amp=6, speed=1.6)
    ground(A, 1180, x0=60, x1=300)
    ground(A, 1180, x0=780, x1=W - 60)
    for k in range(3):
        x = lerp(260, 820, ease_out((ph - k * 0.3) / 3.5))
        boat(A, x, 1240 + k * 30, 100, t, sail=False)
    xin(A, lerp(260, 820, ease_out(ph / 3.5)), 1210, 130, dir=1 if ph < 4 else -1, armour=True, arm=40)
    A.flush(cv)
    stamp(cv, seal('淮河', 54), 860, 1020, t, t - u + 0.4, rot=6)
    if ph >= 4:
        paste(cv, text_img('此后再未回到北方', SERIF, 50, RUST, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((ph - 4) / 0.4))

def art_x_small_post(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='rust')
    xin(A, 300, GROUND, 210, dir=1, kneel=True, bow=20, arm=90, sword_on=False)
    for k in range(int(clamp(u / (2 * P)) * 8)):
        A.d['wash'].rectangle((420 + (k % 4) * 60, GROUND - 90 - (k // 4) * 14, 470 + (k % 4) * 60, GROUND - 80 - (k // 4) * 14), fill=255)
    A.flush(cv)
    stamp(cv, seal('江阴签判', 44), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('归正人 · 不被信任', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_meiqin(A, cv, t, u):
    """6-beat: 美芹十论 — ten strategy chapters unfold one by one; each gets a seal; then they are rolled up and set aside."""
    ph = u / P
    ground(A, GROUND)
    n = min(10, int(ph * 10 / 4) + 1)
    for i in range(10):
        x = 140 + (i % 5) * 200; y = 960 + (i // 5) * 200
        if i < n:
            scroll(A, x, y, 160, 140, 1.0 if ph < 4.5 else 1 - ease_out((ph - 4.5) / 1))
    A.flush(cv)
    for i in range(min(n, 10)):
        if ph < 4.5:
            stamp(cv, seal(cn_num(i + 1), 30, RUST), 140 + (i % 5) * 200, 960 + (i // 5) * 200, t, t - u + i * 0.4 * P)
    if ph >= 4.5:
        paste(cv, text_img('朝廷不纳', SERIF, 56, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp((ph - 4.5) / 0.3))

def art_x_jiuyi(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='none', arm=lerp(20, 60, 0.5 + 0.5 * math.sin(t)), layer='ink')
    xin(A, 340, GROUND, 220, dir=1, kneel=True, bow=20, arm=110)
    scroll(A, 540, GROUND - 160, 160, 50, u / 0.5)
    A.flush(cv)
    stamp(cv, seal('九议', 54), 860, 880, t, t - u + P, rot=6)

def art_x_shangxin(A, cv, t, u):
    """the 建康赏心亭: he looks north over the river, grips the hilt, pounds the rail."""
    rail(A, 160, 920, 1160)
    river(A, 1320, t, rows=2, amp=4, speed=1)
    hit = abs(math.sin(t * 5))
    xin(A, 540, 1160, 250, dir=1, arm=lerp(80, 150, hit), old=0.2)
    A.flush(cv)
    type_in(cv, text_img('把吴钩看了 栏杆拍遍', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    type_in(cv, text_img('无人会 登临意', SERIF, 52, RUST, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.6 * P, 0.5)

def art_x_chuzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='滁州', layer='mid', open_=1.0)
    ground(A, GROUND)
    for k in range(6):
        person(A, 160 + k * 150, GROUND, 120, dir=1 if k % 2 else -1, robe=False, hat='knot', load=k % 2 == 0, ph=t * 4 + k, arm=40, layer='ink')
    A.flush(cv)
    stamp(cv, seal('知州', 54), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('宽征薄赋 招流散', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 平生塞北江南
def art_x_rebels(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['grass'].polygon([(x - 150, GROUND), (x, GROUND - 360), (x + 150, GROUND)], fill=180)
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(-150, 600, ease_out(u / (2.5 * P))) - k * 80, GROUND, 110, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    stamp(cv, seal('茶商军', 50, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_x_feihu(A, cv, t, u):
    """8-beat set piece: 飞虎军 — barracks rise in the rain; tiles are bought from every household overnight;
    the army drills; the tiger banner flies."""
    ph = u / P
    if ph < 3:
        for k in range(60):
            q = (t * 0.8 + k / 60) % 1
            x = 80 + (k * 17) % 920
            A.d['wash'].line((x, lerp(620, 1420, q), x - 4, lerp(620, 1420, q) + 18), fill=180, width=2)
    ground(A, GROUND)
    h = ease_out(ph / 3)
    for k in range(4):
        x = 180 + k * 240
        A.d['mid'].rectangle((x - 90, GROUND - 160 * h, x + 90, GROUND), fill=220)
        A.d['rust'].polygon([(x - 110, GROUND - 160 * h), (x + 110, GROUND - 160 * h), (x, GROUND - 230 * h)], fill=255)
    if ph < 3:
        for k in range(int(ph * 6)):
            person(A, (t * 120 + k * 160) % 1100 - 50, GROUND, 90, dir=1, robe=False, hat='knot', load=True, ph=t * 7 + k, arm=160, layer='ink')
    else:
        for k in range(14):
            person(A, 120 + (k % 7) * 130, GROUND - (k // 7) * 50, 110, dir=1, robe=False, hat='helmet', spear=True, arm=lerp(30, 90, 0.5 + 0.5 * math.sin(t * 6)), layer='ink' if k // 7 == 0 else 'mid')
        flag(A, 960, GROUND, 360, t, w=110, layer='rust')
    A.flush(cv)
    if ph < 3:
        paste(cv, text_img('一夜征瓦二十万', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(ph / 0.4))
    else:
        ink_in(cv, text_img('飞虎军', BRUSH, 110, RUST), W / 2, 870, t, t - u + 3 * P, dur=0.3, settle=1.2)
        if ph >= 5.5:
            paste(cv, text_img('雄镇一方 为江上诸军之冠', SERIF, 42, STEELB, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 5.5) / 0.3))

def art_x_impeached(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    for k in range(3):
        person(A, 760 + k * 60, GROUND, 170, dir=-1, robe=True, hat='none', bow=20, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 5 + k)), layer='ink')
    xin(A, 300, GROUND, 220, dir=1, arm=-8, sword_on=False)
    A.flush(cv)
    for k in range(int(clamp((u - 0.5 * P) / P) * 3)):
        paste(cv, text_img('劾', BRUSH, 70, ZHU), 760 + k * 60, 1060 - k * 30, 1, 0.9)
    paste(cv, text_img('用钱如泥沙 杀人如草芥', SERIF, 44, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.6 * P) / 0.3))

def art_x_daihu(A, cv, t, u):
    A.d['ocean'].ellipse((160, 1220, 600, 1340), fill=150)
    for k in range(4):
        A.d['grass'].rectangle((620 + k * 80, 1220, 690 + k * 80, GROUND), fill=180)
    A.d['dai'].rectangle((660, 1060, 940, 1220), fill=200)
    A.d['ink'].polygon([(640, 1060), (960, 1060), (800, 980)], fill=255)
    ground(A, GROUND)
    xin(A, 360, GROUND, 210, dir=1, arm=40, sword_on=False, old=0.3)
    A.flush(cv)
    stamp(cv, seal('带湖', 54), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('闲居上饶 · 自号稼轩', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_village(A, cv, t, u):
    for k in range(30):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 300
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    moon_phase(A, 800, 760, 50, 1.0)
    for k in range(12):
        x = 100 + k * 80
        A.d['grass'].polygon([(x - 34, GROUND), (x, GROUND - 90), (x + 34, GROUND)], fill=200)
        A.d['gold'].ellipse((x - 6, GROUND - 100, x + 6, GROUND - 88), fill=230)
    xin(A, 540, GROUND, 190, dir=1, arm=-8, sword_on=False, old=0.3)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('稻花香里说丰年', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('听取蛙声一片', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

def art_x_lantern(A, cv, t, u):
    for k in range(40):
        x = 80 + (k * 37) % 920; y = 640 + (k * 53) % 400
        A.d['wash'].ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
    for k in range(10):
        x = 120 + k * 92; y = 920 + 40 * math.sin(k)
        A.d['gold'].ellipse((x - 18, y - 24, x + 18, y + 24), fill=230)
        A.d['red'].rectangle((x - 4, y + 24, x + 4, y + 34), fill=255)
    for k in range(6):
        person(A, 120 + k * 150, GROUND, 140, dir=1 if k % 2 else -1, robe=True, hat='knot', female=k % 2 == 0, ph=t * 3 + k, arm=20, layer='mid')
    person(A, 900, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, arm=-8, layer='ink')
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('蓦然回首 那人却在 灯火阑珊处', SERIF, 42, RUST, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.6)

def art_x_chenliang(A, cv, t, u):
    for k in range(50):
        q = (t * 0.5 + k / 50) % 1
        x = 80 + (k * 19) % 920
        A.d['wash'].ellipse((x - 4, lerp(620, 1420, q) - 4, x + 4, lerp(620, 1420, q) + 4), fill=230)
    ground(A, GROUND)
    xin(A, 360, GROUND, 220, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)), sword_on=False, old=0.3)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='none', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2 + 1)), layer='ink')
    wine_jar(A, 540, GROUND, 50)
    A.flush(cv)
    stamp(cv, seal('鹅湖之会', 44), 860, 880, t, t - u + 0.4, rot=6)
    stamp(cv, seal('陈亮', 46, INK), 700, 960, t, t - u + P, rot=6)

# ================================================================ 第四回 醉里挑灯
def art_x_tiaodeng(A, cv, t, u):
    """6-beat: 醉里挑灯看剑 — drunk at night, he trims the lamp and draws the sword; in the dream the camps sound
    their horns; the dream fades and he is white-haired."""
    ph = u / P
    if ph < 2.5:
        A.d['mid'].rectangle((200, 900, 880, GROUND), fill=170)
        lamp(A, 400, GROUND - 70, 50, t, glow=0.8)
        desk(A, 420, GROUND, 260, layer='rust')
        xin(A, 620, GROUND, 240, dir=-1, arm=lerp(60, 150, ease_out(ph / 1.5)), sword=lerp(40, 160, ease_out(ph / 1.5)), sword_on=False, old=0.5)
    elif ph < 4.5:
        for k in range(8):
            tent(A, 140 + k * 120, GROUND - (k % 2) * 30, 110, 90, layer='mid')
        for k in range(6):
            rider(A, (t * 140 + k * 200) % 1200 - 100, GROUND, 110, 1, t * 12 + k, layer='ink', spear=True)
        flag(A, 900, GROUND, 360, t, w=110, layer='rust')
    else:
        A.d['mid'].rectangle((200, 900, 880, GROUND), fill=170)
        lamp(A, 400, GROUND - 70, 50, t, glow=0.2)
        desk(A, 420, GROUND, 260, layer='rust')
        sitter(A, 620, GROUND, 200, dir=-1, bow=30)
    ground(A, GROUND)
    A.flush(cv)
    if ph < 2.5:
        type_in(cv, text_img('醉里挑灯看剑', SERIF, 52, INK, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 0.3, 0.5)
    elif ph < 4.5:
        type_in(cv, text_img('梦回吹角连营', SERIF, 52, RUST, 'Black', bleed=False, spacing=8), W / 2, 830, t, t - u + 2.5 * P, 0.5)
    else:
        type_in(cv, text_img('可怜白发生', SERIF, 56, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, t, t - u + 4.5 * P, 0.5)

def art_x_fujian(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1220, W - 60, GROUND), fill=150)
    waves(A, 1230, t, rows=3, amp=6, speed=1.6)
    city_wall(A, 160, 700, 1080, gate_x=430, label='福州', layer='mid')
    xin(A, 860, 1220, 180, dir=-1, arm=40, old=0.4)
    A.flush(cv)
    stamp(cv, seal('福建安抚使', 40), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('起复不久 又遭罢免', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_piaoquan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 300), (x + 200, GROUND)], fill=170)
    A.d['ocean'].ellipse((380, 1300, 700, 1380), fill=170)
    ground(A, GROUND)
    xin(A, 760, GROUND, 200, dir=-1, arm=-8, sword_on=False, old=0.6)
    A.flush(cv)
    stamp(cv, seal('瓢泉', 54), 260, 880, t, t - u + P, rot=-5)
    paste(cv, text_img('前后闲居二十年', SERIF, 50, RUST, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_x_mountain(A, cv, t, u):
    A.d['mid'].polygon([(560, GROUND), (780, 900), (1000, GROUND)], fill=210)
    ground(A, GROUND)
    xin(A, 340, GROUND, 230, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t)), sword_on=False, old=0.6)
    A.flush(cv)
    type_in(cv, text_img('我见青山多妩媚', SERIF, 48, INK, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('料青山见我应如是', SERIF, 46, RUST, 'Black', bleed=False, spacing=6), W / 2, 900, t, t - u + 1.5 * P, 0.5)

def art_x_620(A, cv, t, u):
    ground(A, GROUND)
    for i in range(int(clamp(u / (2.5 * P)) * 5) + 1):
        bundle(A, 260 + i * 140, GROUND - 40, 110, layer='rust')
    A.flush(cv)
    paste(cv, text_img('存词六百二十余首 · 两宋之冠', SERIF, 44, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_hanchou(A, cv, t, u):
    palace(A, 540, 1160, 540, layer='mid')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 230, dir=-1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    xin(A, 340, GROUND, 230, dir=1, arm=40, old=0.8)
    A.flush(cv)
    stamp(cv, seal('韩侂胄', 46, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('六十四岁 被起用', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_beigu(A, cv, t, u):
    """6-beat: 京口北固亭 — on the tower above the 长江, looking north; the line 尚能饭否 lands last."""
    ph = u / P
    river(A, 1260, t, rows=4, amp=7, speed=1.8)
    A.d['ink'].rectangle((200, 1060, 500, 1260), fill=255)
    A.d['ink'].polygon([(170, 1060), (530, 1060), (350, 980)], fill=255)
    xin(A, 350, 1060, 180, dir=1, arm=lerp(40, 150, ease_out(ph / 1.5)), old=0.9)
    A.flush(cv)
    stamp(cv, seal('北固亭', 50), 860, 1060, t, t - u + 0.4, rot=6)
    type_in(cv, text_img('想当年 金戈铁马 气吞万里如虎', SERIF, 42, INK, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.5)
    if ph >= 3:
        type_in(cv, text_img('凭谁问 廉颇老矣 尚能饭否', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 900, t, t - u + 3 * P, 0.5)

# ================================================================ 第五回 了却君王
def art_x_rash(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        person(A, lerp(-100, 900, ease_out(u / (3 * P))) - (k % 5) * 80, GROUND - (k // 5) * 40, 100, dir=1, robe=False, hat='helmet', spear=True, ph=t * 6 + k, arm=40, layer='ink' if k // 5 == 0 else 'mid')
    xin(A, 900, GROUND, 200, dir=-1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 3)), old=0.9)
    A.flush(cv)
    stamp(cv, seal('开禧北伐', 46), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('他劝勿轻率 · 不被听从', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_x_defeat(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        person(A, 160 + k * 80, GROUND, 100, dir=-1, robe=False, hat='helmet', fall=-80 * ease_out((u - k * 0.08 * P) / 0.6), arm=40, layer='mid')
    flames(A, 540, GROUND, 900, 200 * ease_out(u / P), t, n=8, seed=19, smoke=True)
    A.flush(cv)
    stamp(cv, seal('北伐失败', 46, INK), 860, 880, t, t - u + 0.4, rot=6)

def art_x_ill(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xin(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, old=1.0)
    ground(A, GROUND)
    x = lerp(1100, 860, ease_out(u / (1.5 * P)))
    person(A, x, GROUND, 200, dir=-1, robe=True, hat='none', arm=lerp(40, 110, ease_out((u - 1.5 * P) / 0.4)), layer='ink')
    scroll(A, x - 120, GROUND - 170, 140, 50, (u - 1.5 * P) / 0.4, layer='yellow')
    A.flush(cv)
    stamp(cv, seal('枢密都承旨', 38), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('诏书到时 已不能起身', SERIF, 46, RUST, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 2 * P) / 0.3))

def art_x_shazei(A, cv, t, u):
    """6-beat: 临终呼杀贼 — on the deathbed he lifts his hand and shouts three times; the lamp flares and dies."""
    ph = u / P
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    lift = abs(math.sin(min(ph, 4) * math.pi * 0.75))
    xin(A, 540, 1200, 220, dir=1, fall=-88, arm=lerp(-8, 150, lift) if ph < 4.5 else -8, old=1.0)
    lamp(A, 860, GROUND, 60, t, glow=(1.5 if ph < 4 else clamp(1 - (ph - 4) / 1)))
    ground(A, GROUND)
    A.flush(cv)
    for i in range(min(3, int(ph / 1.2) + 1)):
        paste(cv, text_img('杀贼', BRUSH, 90, ZHU), 300 + i * 240, 900 - i * 10, 1, clamp((ph - i * 1.2) / 0.2))
    if ph >= 4:
        paste(cv, text_img('年六十八', SERIF, 50, RUST, 'Black', bleed=False, spacing=8), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

def art_x_poet(A, cv, t, u):
    ground(A, GROUND)
    for k in range(2):
        sitter(A, 380 + k * 320, GROUND, 180, dir=1 if k == 0 else -1, bow=10, layer='ink')
    A.flush(cv)
    stamp(cv, seal('苏', 54), 380, 1060, t, t - u + 0.4)
    stamp(cv, seal('辛', 54, RUST), 700, 1060, t, t - u + P)
    paste(cv, text_img('苏辛并称 · 豪放派', SERIF, 48, RUST, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_never(A, cv, t, u):
    river(A, 1240, t, rows=3, amp=5, speed=1.2)
    A.d['mid'].polygon([(60, 1240), (60, 1000), (1020, 980), (1020, 1240)], fill=110)
    ground(A, 1240, x0=60, x1=W - 60)
    A.flush(cv)
    paste(cv, text_img('至死未能踏上北方故土', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_x_legacy(A, cv, t, u):
    sword(A, 540, 1100, 380, 1.0, ang=-0.12)
    ground(A, GROUND)

def art_x_title(A, cv, t, u):
    sword(A, 820, 1100, 260, 0.6, ang=-1.2)
    xin(A, 400, 1460, 680, dir=1, armour=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '沦陷区少年'), 48: ('第二回', '万人取首'), 80: ('第三回', '塞北江南'),
            112: ('第四回', '醉里挑灯'), 144: ('第五回', '了却君王')}

CARDS = [
    C(0, 2, 'war', 'num', num='五十骑', line='闯五万人大营', art=art_x_hook_50),
    C(2, 4, 'works', 'num', num='六百余首', line='宋代存词最多', art=art_x_hook_words),
    C(4, 6, 'fate', 'num', num='栏杆拍遍', line='无人会登临意', art=art_x_hook_rail),
    C(6, 8, 'death', 'num', num='杀贼', line='临终仍在高呼', art=art_x_hook_kill),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 沦陷区少年
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1140, main='生于历城', sub='济南历城 · 金国治下', art=art_x_birth),
    C(22, 26, 'works', 'card', year=1150, main='祖父教诲', sub='辛赞常带他登高望远', note='尝令登高望远 指画山河', art=art_x_grandpa),
    C(26, 30, 'night', 'card', year=1154, main='两赴燕京', sub='少年刺探敌情', art=art_x_scout),
    C(30, 34, 'war', 'card', year=1161, main='聚众起义', sub='金主完颜亮南侵 · 北方大乱', art=art_x_rise),
    C(34, 38, 'court', 'card', year=1161, main='投奔耿京', sub='任掌书记', art=art_x_gengjing),
    C(38, 44, 'war', 'card', year=1161, main='追斩义端', sub='和尚盗印 · 他连夜追回', art=art_x_yiduan),
    C(44, 48, 'empire', 'card', year=1162, main='奉表南归', sub='代耿京联络南宋', art=art_x_envoy),
    # ---- 第二回 万人取首
    C(48, 50, 'war', 'chapter'),
    C(50, 58, 'war', 'raid', year=1162),
    C(58, 64, 'fate', 'card', year=1162, main='南归', sub='带万余人渡淮', art=art_x_south),
    C(64, 68, 'court', 'card', year=1162, main='归正人', sub='江阴签判 · 一个小官', art=art_x_small_post),
    C(68, 74, 'works', 'card', year=1165, main='美芹十论', sub='上书论恢复大计', art=art_x_meiqin),
    C(74, 78, 'court', 'card', year=1170, main='九议', sub='再上宰相 · 仍不被用', art=art_x_jiuyi),
    C(78, 80, 'empire', 'card', year=1172, main='知滁州', sub='安民理政', art=art_x_chuzhou),
    # ---- 第三回 塞北江南
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'night', 'card', year=1174, main='栏杆拍遍', sub='登建康赏心亭', note='水龙吟', art=art_x_shangxin),
    C(86, 90, 'war', 'card', year=1175, main='平茶商军', sub='江西提点刑狱', art=art_x_rebels),
    C(90, 98, 'war', 'card', year=1180, main='飞虎军', sub='湖南安抚使 · 创建新军', art=art_x_feihu),
    C(98, 102, 'death', 'card', year=1181, main='遭弹劾', sub='言官攻击 · 罢官', art=art_x_impeached),
    C(102, 106, 'fate', 'card', year=1182, main='带湖新居', sub='稼轩', art=art_x_daihu),
    C(106, 110, 'life', 'card', year=1186, main='稻花香里', sub='西江月 · 夜行黄沙道中', note='作年不详', art=art_x_village),
    C(110, 112, 'night', 'card', year=1188, main='鹅湖之会', sub='与陈亮雪中长谈', art=art_x_chenliang),
    # ---- 第四回 醉里挑灯
    C(112, 114, 'night', 'chapter'),
    C(114, 120, 'night', 'card', year=1188, main='醉里挑灯', sub='破阵子 · 为陈同甫赋', art=art_x_tiaodeng),
    C(120, 124, 'empire', 'card', year=1192, main='起复福建', sub='又一次被起用', art=art_x_fujian),
    C(124, 128, 'fate', 'card', year=1196, main='瓢泉', sub='再度罢官闲居', art=art_x_piaoquan),
    C(128, 132, 'life', 'card', year=1198, main='青山妩媚', sub='贺新郎', art=art_x_mountain),
    C(132, 136, 'works', 'card', year=1200, main='六百余首', sub='他把报国写进词里', art=art_x_620),
    C(136, 140, 'court', 'card', year=1203, main='再被起用', sub='韩侂胄筹划北伐', art=art_x_hanchou),
    C(140, 144, 'war', 'card', year=1205, main='北固亭', sub='知镇江府 · 登亭怀古', note='永遇乐 京口北固亭怀古', art=art_x_beigu),
    # ---- 第五回 了却君王
    C(144, 146, 'death', 'chapter'),
    C(146, 150, 'war', 'card', year=1206, main='开禧北伐', sub='仓促出兵', art=art_x_rash),
    C(150, 154, 'death', 'card', year=1206, main='兵败', sub='宋军全线溃退', art=art_x_defeat),
    C(154, 158, 'fate', 'card', year=1207, main='诏书迟到', sub='朝廷想起他时 他已病重', art=art_x_ill),
    C(158, 164, 'death', 'card', year=1207, main='杀贼', sub='临终大呼杀贼数声而逝', note='一说', art=art_x_shazei),
    C(164, 168, 'works', 'card', year=1207, main='苏辛', sub='词中之龙', art=art_x_poet),
    C(168, 170, 'end', 'card', year=1207, main='遗恨', sub='终身未能北还', art=art_x_never),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='叁拾伍', col=RUST, acc=STEELB, born=1140, died=1207,
    hook_q='能文能武的猛人 · 为何一辈子壮志难酬？',
    name_line='辛弃疾 · 号稼轩', name='辛弃疾', seal='稼轩', title_art=art_x_title,
    q1='豪放词宗？', q2='报国无门？',
    end_art=art_x_legacy, end_big='醉里挑灯', end_seal='稼轩',
    end_l1='他本该是战场上的将军', end_l2='却被逼成了最好的词人',
    end_brush='了却君王天下事', end_ask='是时代辜负了他吗？评论区聊聊', next='王安石'),
    scenes=dict(chapter=scene_chapter, raid=scene_raid))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
