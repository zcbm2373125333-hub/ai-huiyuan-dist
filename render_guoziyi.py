"""千古人物志 · 第肆拾集 · 郭子仪 (697–781)
Look: 朱紫 + 古铜, 笏板 corner borders, a 满床笏 chapter card: more and more ivory tablets are laid on the couch each
chapter (his family's offices).
Set pieces: custom 8-beat scene 'liangjing' (收复两京), 8-beat 疑兵复长安, 8-beat 单骑见回纥, 6-beat 打金枝 (legend),
6-beat 满床笏 (legend).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_xuanzang as Xz        # engine + helpers (previous episode)
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
from render_zhangqian import yurt
from render_quyuan import river

F.RIPPLE = False
ZI = (112, 58, 116)                 # 朱紫
TONG = (176, 120, 62)               # 古铜
S.LAYERS.append(('zi', ZI, 0.88, 1.0))
S.LAYERS.append(('tong', TONG, 0.88, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='郭', life='仪', court='唐', night='夜', war='戰', empire='唐', works='忠', fate='忍', death='寿', end='福')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'end', 'court', 'empire', 'works'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['war']['sun'] = (TONG, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (ZI, 220, (W * 0.5, 820))
G.THEMES['works']['sun'] = None
G.THEMES['end']['sun'] = (TONG, 210, (W * 0.5, 720))
G.base_bg.cache_clear()

GATE = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(GATE)
for _x in (110, 970):
    _d.rectangle((_x - 30, 1220, _x + 30, 1480), fill=ZI + (40,))
    _d.polygon([(_x - 60, 1220), (_x + 60, 1220), (_x, 1170)], fill=ZI + (50,))
MTN_COL = {'night': (36, 32, 42), 'death': (60, 58, 62), 'war': (106, 62, 50), 'fate': (90, 80, 100)}
def draw_background(t, theme):
    """关中: broad ridges, two watch-gates at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(192, 182, 188), (152, 136, 150), MTN_COL.get(theme, (112, 94, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 7 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(GATE)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """笏板: two crossed ivory tablets in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=ZI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=ZI + (220,), width=3)
        for a in (0.55, 1.0):
            ex, ey = x + sx * 110 * math.cos(a), y + sy * 110 * math.sin(a)
            d.line((x + sx * 14 * math.cos(a), y + sy * 14 * math.sin(a), ex, ey), fill=(236, 226, 196, 240), width=12)
            d.line((x + sx * 14 * math.cos(a), y + sy * 14 * math.sin(a), ex, ey), fill=TONG + (200,), width=2)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def guo(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=True, old=0.0, helm=True, **kw):
    """郭子仪: big build, long beard; armour with a bronze helmet crest, or purple court robe when not armoured."""
    b = bow + 12 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat=('helmet' if (armour and helm) else 'none') if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        if armour and helm:
            A.d['tong'].polygon([(x - 0.03 * h, y - 1.06 * h), (x + 0.03 * h, y - 1.06 * h), (x, y - 1.2 * h)], fill=255)
            A.d['zi'].polygon([(x - dir * 0.05 * h, y - 0.82 * h), (x - dir * 0.26 * h, y - 0.2 * h), (x - dir * 0.06 * h, y - 0.24 * h)], fill=255)
        elif not armour:
            d.rectangle((x - 0.065 * h, y - 1.05 * h, x + 0.065 * h, y - 0.94 * h), fill=255)
            A.d['zi'].rectangle((x - 0.1 * h, y - 0.6 * h, x + 0.1 * h, y - 0.55 * h), fill=255)
        d.polygon([(x + dir * 0.0, y - 0.86 * h), (x + dir * 0.1 * h, y - 0.86 * h), (x + dir * 0.06 * h, y - 0.56 * h)], fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.01 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.6 * h)], fill=255)
    return hand

def couch(A, cx, base, w, hu, t=0.0):
    """a low couch with `hu` ivory tablets lying on it."""
    A.d['zi'].rectangle((cx - w / 2, base - 0.18 * w, cx + w / 2, base - 0.1 * w), fill=255)
    A.d['ink'].rectangle((cx - w / 2, base - 0.42 * w, cx - w / 2 + 16, base), fill=255)
    A.d['ink'].rectangle((cx + w / 2 - 16, base - 0.42 * w, cx + w / 2, base), fill=255)
    for sx in (-0.4, 0.4):
        A.d['ink'].rectangle((cx + sx * w - 8, base - 0.1 * w, cx + sx * w + 8, base), fill=255)
    for i in range(hu):
        r, c = i // 8, i % 8
        x = cx - 0.42 * w + c * 0.12 * w + 0.02 * w * r
        y = base - 0.2 * w - r * 0.05 * w
        A.d['wash'].polygon([(x - 0.02 * w, y), (x + 0.02 * w, y), (x + 0.015 * w, y - 0.22 * w), (x - 0.015 * w, y - 0.22 * w)], fill=255)
        A.d['tong'].line((x - 0.02 * w, y, x + 0.02 * w, y), fill=255, width=3)

# ================================================================ chapter card
CH = {16: 0, 48: 3, 80: 6, 112: 12, 144: 24}
def art_hu_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    n = CH.get(kb, 3)
    prev = {48: 0, 80: 3, 112: 6, 144: 12}.get(kb, 0)
    q = ease_out(u / (1.2 * P))
    couch(A, 540, 1200, 640, int(lerp(prev, n, q)), t=t)
    if n == 0:
        guo(A, 540, 1200, 220, dir=1, arm=40, spear=True)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_hu_chapter)
    ink_in(cv, text_img(no, SERIF, 56, ZI, 'Black', bleed=False, spacing=12), W / 2, 1300, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1430, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_g_hook_four(A, cv, t, u):
    palace(A, 540, 1160, 560, layer='zi')
    ground(A, GROUND)
    for k in range(4):
        person(A, 200 + k * 230, GROUND, 160, dir=1, robe=True, hat='crown', arm=40, layer='mid')
    guo(A, 540, GROUND, 260, dir=1, armour=False, arm=40)

def art_g_hook_alone(A, cv, t, u):
    ground(A, GROUND)
    for k in range(20):
        rider(A, 520 + (k % 10) * 54, GROUND - (k // 10) * 40, 90, -1, t * 3 + k, layer='mid', spear=True, moving=False)
    x = lerp(-100, 380, ease_out(u / (1.6 * P)))
    horse(A, x, GROUND, 170, dir=1, ph=t * 6, moving=u < 1.6 * P)
    guo(A, x - 10, GROUND - 130, 160, dir=1, helm=False, arm=60)

def art_g_hook_bed(A, cv, t, u):
    couch(A, 540, 1260, 680, int(clamp(u / (1.6 * P)) * 24))

def art_g_hook_85(A, cv, t, u):
    ground(A, GROUND)
    guo(A, 540, GROUND, 280, dir=1, armour=False, old=1.0, arm=40)
    for k in range(10):
        a = k * 2 * math.pi / 10 + t * 0.3
        A.d['gold'].ellipse((540 + 300 * math.cos(a) - 12, 1100 + 120 * math.sin(a) - 12, 540 + 300 * math.cos(a) + 12, 1100 + 120 * math.sin(a) + 12), fill=230)

# ================================================================ 第一回 大器晚成
def art_g_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['grass'].polygon([(x - 200, GROUND), (x, GROUND - 260), (x + 200, GROUND)], fill=160)
    ground(A, GROUND)
    person(A, 420, GROUND, 230, dir=1, robe=True, hat='none', arm=40, layer='ink')
    person(A, 560, GROUND, 120, dir=1, robe=False, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    stamp(cv, seal('华州郑县', 46), 860, 880, t, t - u + P, rot=6)

def art_g_wuju(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        A.d['zi'].ellipse((760 + k * 50 - 40, 1000 + k * 60 - 40, 760 + k * 50 + 40, 1000 + k * 60 + 40), outline=255, width=6)
    guo(A, 380, GROUND, 230, dir=1, helm=False, arm=150, arm2=-120)
    arrow(A, lerp(460, 760, (t * 2) % 1), 1080, 0.05, 80)
    A.flush(cv)
    stamp(cv, seal('武举高第', 46), 260, 880, t, t - u + P, rot=-5)

def art_g_frontier(A, cv, t, u):
    for k in range(40):
        q = (t * 0.6 + k / 40) % 1
        A.d['wash'].ellipse((80 + (k * 23) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 23) % 920 + 4, lerp(620, 1420, q) + 4), fill=230)
    city_wall(A, 160, 920, 1100, gate_x=540, label=None, layer='mid')
    ground(A, GROUND)
    guo(A, 540, 1100, 180, dir=1, arm=40, spear=True)
    A.flush(cv)
    paste(cv, text_img('戍守边关', SERIF, 50, ZI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_g_slow(A, cv, t, u):
    ground(A, GROUND)
    n = min(20, int(clamp(u / (3 * P)) * 20) + 1)
    for i in range(n):
        x = 140 + i * 42
        A.d['tong'].rectangle((x - 14, GROUND - 30 - i * 6, x + 14, GROUND), fill=255)
    guo(A, 900, GROUND, 210, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img(f'默默无闻 {n} 余年', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, 1)

def art_g_shuofang(A, cv, t, u):
    tent(A, 760, GROUND, 400, 300, layer='mid')
    ground(A, GROUND)
    guo(A, 380, GROUND, 240, dir=1, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 2)), spear=True)
    flag(A, 560, GROUND, 360, t, w=90, layer='zi')
    A.flush(cv)
    stamp(cv, seal('天德军使', 44), 860, 880, t, t - u + P, rot=6)

def art_g_rebellion(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        rider(A, lerp(-300, 1100, ((t * 0.15 + k * 0.1) % 1)), GROUND - (k % 2) * 40, 110, 1, t * 12 + k, layer='ink', spear=True)
    flames(A, 540, GROUND, 900, 240 * ease_out(u / (1.5 * P)), t, n=8, seed=4, smoke=True)
    A.flush(cv)
    stamp(cv, seal('安禄山', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('渔阳鼙鼓动地来', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_jiedu(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    guo(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 160, ease_out(u / (1.5 * P))), spear=True)
    A.flush(cv)
    stamp(cv, seal('朔方节度使', 40), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('年近六十 · 临危受命', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_liguangbi(A, cv, t, u):
    tent(A, 540, GROUND, 620, 420, layer='mid')
    ground(A, GROUND)
    guo(A, 360, GROUND, 240, dir=1, arm=lerp(30, 90, ease_out(u / P)))
    person(A, 720, GROUND, 230, dir=-1, robe=False, hat='helmet', kneel=True, bow=20, arm=90, layer='ink')
    A.flush(cv)
    stamp(cv, seal('李光弼', 50), 860, 880, t, t - u + 0.4, rot=6)

# ================================================================ 第二回 再造唐室
def art_g_jiashan(A, cv, t, u):
    for k in range(3):
        A.d['mid'].polygon([(200 + k * 320 - 200, GROUND), (200 + k * 320, GROUND - 300), (200 + k * 320 + 200, GROUND)], fill=200)
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(-200, 560, ease_out(u / (2 * P))) - (k % 4) * 100, GROUND - (k // 4) * 40, 110, 1, t * 12 + k, layer='zi' if k == 0 else 'ink', spear=True)
    for k in range(8):
        person(A, 700 + k * 40, GROUND, 100, dir=-1, robe=False, hat='helmet', fall=-80 * ease_out((u - 1.5 * P - k * 0.08) / 0.4), arm=40, layer='mid')
    A.flush(cv)
    stamp(cv, seal('嘉山', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('斩首四万 · 河北震动', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

def art_g_lingwu(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND - 40, 210, dir=1, robe=True, hat='crown', arm=40, layer='ink')
    guo(A, 300, GROUND, 210, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    stamp(cv, seal('灵武', 54), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('肃宗即位 · 率兵勤王', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_huihe(A, cv, t, u):
    yurt(A, 760, GROUND, 340, 280, layer='tong')
    ground(A, GROUND)
    for k in range(6):
        rider(A, lerp(1200, 760 + (k % 3) * 100, ease_out((u - k * 0.1) / (2 * P))), GROUND - (k // 3) * 40, 100, -1, t * 9 + k, layer='mid', spear=True, moving=u < 2 * P)
    guo(A, 300, GROUND, 230, dir=1, arm=60)
    A.flush(cv)
    stamp(cv, seal('借兵回纥', 44), 260, 880, t, t - u + 0.4, rot=-5)

LJ = [(0, '香积寺', '十五万大军 鏖战半日'), (3, '长安', '收复西京'), (5.5, '洛阳', '收复东京')]
def scene_liangjing(cv, t, c, k):
    """8-beat custom scene: 收复两京 — a map of 关中 and 河洛; at 香积寺 the battle lines clash; the arrow reaches 长安,
    then rolls east to 洛阳; each city flips from rebel black to Tang purple."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['wash'].rounded_rectangle((110, 780, 970, 1420), radius=24, fill=180)
    A.d['ocean'].line([(130, 1260), (400, 1220), (700, 1240), (950, 1200)], fill=170, width=16)
    cities = {'长安': (300, 1120), '洛阳': (760, 1080), '香积寺': (240, 1220)}
    for nm, (x, y) in cities.items():
        if nm == '香积寺': continue
        taken = (nm == '长安' and ph >= 3) or (nm == '洛阳' and ph >= 5.5)
        A.d['zi' if taken else 'ink'].rectangle((x - 50, y - 40, x + 50, y + 40), fill=255)
    if ph < 3:
        for j in range(8):
            A.d['zi'].line((160 + j * 14, 1300, 220 + j * 14, 1240), fill=255, width=4)
            A.d['ink'].line((320 - j * 14, 1180, 260 - j * 14, 1240), fill=255, width=4)
    q1 = ease_out(ph / 3)
    A.d['zi'].line((140, 1360, lerp(140, 300, q1), lerp(1360, 1170, q1)), fill=255, width=10)
    if ph >= 3:
        q2 = ease_out((ph - 3.5) / 2)
        A.d['zi'].line((350, 1120, lerp(350, 710, q2), lerp(1120, 1080, q2)), fill=255, width=10)
    A.flush(cv)
    for nm, (x, y) in cities.items():
        stamp(cv, seal(nm, 30, ZI if nm != '香积寺' else TONG), x, y - 80, t, s0 + 0.2)
    i = max(j for j, (b, *_) in enumerate(LJ) if ph >= b)
    b, nm, txt = LJ[i]
    fx = Art()
    chars_in(cv, fx, '收复两京', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=57)
    fx.flush(cv)
    paste(cv, text_img(f'{nm} · {txt}', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('公元七五七年', SERIF, 42, TONG, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, 1)

def art_g_zaizao(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='zi')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 110, ease_out(u / P)), layer='ink')
    guo(A, 360, GROUND, 220, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    type_in(cv, text_img('国家再造 卿之力也', SERIF, 50, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + P, 0.5)

def art_g_xiangzhou(A, cv, t, u):
    for k in range(80):
        q = (t * 1.6 + k / 80) % 1
        A.d['dune'].line((lerp(-100, 1200, q), 700 + (k * 37) % 700, lerp(-100, 1200, q) + 60, 700 + (k * 37) % 700), fill=200, width=4)
    city_wall(A, 360, 720, 1100, gate_x=540, label='邺城', layer='mid')
    ground(A, GROUND)
    for k in range(9):
        a = math.pi + k * math.pi / 8
        flag(A, 540 + 420 * math.cos(a), GROUND - 10, 160, t, w=40, layer='zi' if k % 2 else 'tong')
    A.flush(cv)
    stamp(cv, seal('九节度', 50), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('不设元帅 · 大风溃败', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((u - 1.5 * P) / 0.3))

# ================================================================ 第三回 功高被谗
def art_g_stripped(A, cv, t, u):
    palace(A, 760, GROUND, 400, layer='mid')
    ground(A, GROUND)
    guo(A, lerp(540, 200, ease_out(u / (2.5 * P))), GROUND, 220, dir=-1, armour=False, ph=t * 3, arm=-8)
    A.flush(cv)
    stamp(cv, seal('解除兵权', 46, INK), 760, 860, t, t - u + 0.4, rot=6)
    paste(cv, text_img('不发一句怨言', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_yuchaoen(A, cv, t, u):
    palace(A, 540, 1160, 520, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 220, dir=-1, robe=True, hat='none', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    person(A, 420, GROUND - 30, 220, dir=1, robe=True, hat='crown', arm=40, layer='mid')
    A.flush(cv)
    stamp(cv, seal('鱼朝恩', 50, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('宦官屡进谗言', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_hezhong(A, cv, t, u):
    tent(A, 540, GROUND, 600, 400, layer='mid')
    ground(A, GROUND)
    for k in range(8):
        person(A, 160 + k * 100, GROUND, 120, dir=1 if k < 4 else -1, robe=False, hat='helmet', kneel=u > 2 * P, bow=40 if u > 2 * P else 0, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 6 + k)) if u < 2 * P else 100, layer='ink')
    guo(A, 540, GROUND, 240, dir=1, arm=40)
    A.flush(cv)
    stamp(cv, seal('河中兵变', 46), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('一到即平', SERIF, 52, ZI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp((u - 2 * P) / 0.3))

def art_g_tubo(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='长安', layer='mid', open_=1.0)
    flames(A, 540, 1100, 700, 220 * ease_out(u / P), t, n=7, seed=8, smoke=True)
    ground(A, GROUND)
    carriage(A, lerp(540, 1150, ease_out(u / (2.5 * P))), GROUND, 110, dir=1, wheel=t * 6, ph=t * 8, layer='ink')
    A.flush(cv)
    stamp(cv, seal('吐蕃', 54, INK), 260, 880, t, t - u + 0.4, rot=-5)
    paste(cv, text_img('代宗出逃陕州', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_decoy(A, cv, t, u):
    """8-beat set piece: 疑兵复长安 — with a few thousand men he lights fires and beats drums on the hills at night;
    the 吐蕃 think a great army is coming and flee the city."""
    ph = u / P
    for k in range(40):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    city_wall(A, 360, 720, 1180, gate_x=540, label='长安', layer='mid', open_=ease_out((ph - 4) / 1))
    for k in range(4):
        A.d['mid'].polygon([(k * 280 - 80, GROUND), (k * 280 + 60, 1060), (k * 280 + 200, GROUND)], fill=180)
    n = int(clamp(ph / 3.5) * 14)
    for i in range(n):
        x = 100 + (i * 71) % 880; y = 1080 + (i * 37) % 160
        if 340 < x < 740 and y > 1150: continue
        A.d['xia'].ellipse((x - 10, y - 14, x + 10, y + 6), fill=230)
    if ph >= 4:
        for k in range(8):
            rider(A, lerp(560, 1250, ease_out((ph - 4 - k * 0.1) / 2)), GROUND - (k % 2) * 30, 100, 1, t * 12 + k, layer='ink', spear=True)
    ground(A, GROUND)
    A.flush(cv)
    lab = '入夜 · 鸣鼓举火' if ph < 4 else '吐蕃以为大军将至 · 弃城而逃'
    paste(cv, text_img(lab, SERIF, 46, ZI if ph < 4 else ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_g_welcome(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=540, label='长安', layer='zi', open_=1.0)
    ground(A, GROUND)
    carriage(A, lerp(-200, 540, ease_out(u / (2 * P))), GROUND, 120, dir=1, wheel=t * 4, ph=t * 6, moving=u < 2 * P, layer='ink')
    guo(A, 760, GROUND, 210, dir=-1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    paste(cv, text_img('迎代宗还京', SERIF, 50, ZI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_g_pugu(A, cv, t, u):
    tent(A, 760, GROUND, 400, 300, layer='mid')
    ground(A, GROUND)
    person(A, 700, GROUND, 230, dir=-1, robe=False, hat='helmet', sword=lerp(40, 150, ease_out(u / 0.6)), arm=120, layer='ink')
    A.flush(cv)
    stamp(cv, seal('仆固怀恩', 44, INK), 260, 880, t, t - u + 0.4, rot=-5)

# ================================================================ 第四回 单骑退敌
def art_g_300k(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2 * P)) * 30)
    for i in range(n):
        rider(A, 1100 - (i % 10) * 90 - 30 * ((t * 0.5) % 1), GROUND - (i // 10) * 40, 90 - (i // 10) * 10, -1, t * 10 + i, layer='ink' if i // 10 == 0 else 'mid', spear=True)
    A.flush(cv)
    stamp(cv, seal('吐蕃', 44, INK), 260, 880, t, t - u + 0.4, rot=-5)
    stamp(cv, seal('回纥', 44), 400, 880, t, t - u + 0.8, rot=5)
    paste(cv, text_img('三十万大军 逼近长安', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_g_alone(A, cv, t, u):
    """8-beat set piece: 单骑见回纥 — he takes off his helmet and armour, rides alone into the 回纥 camp; the chiefs
    recognise him, dismount and bow; they drink an oath."""
    ph = u / P
    yurt(A, 860, GROUND, 260, 220, layer='tong')
    ground(A, GROUND)
    for k in range(10):
        bow_ = 50 if ph > 4.5 else 0
        person(A, 640 + (k % 5) * 70, GROUND - (k // 5) * 40, 120, dir=-1, robe=False, hat='helmet', spear=ph < 4.5, kneel=ph > 4.5, bow=bow_, arm=100 if ph > 4.5 else 40, layer='ink' if k // 5 == 0 else 'mid')
    x = lerp(-100, 440, ease_out(ph / 3.5))
    horse(A, x, GROUND, 170, dir=1, ph=t * 5, moving=ph < 3.5)
    guo(A, x - 10, GROUND - 130, 160, dir=1, helm=False, armour=ph < 1.2, arm=lerp(40, 120, ease_out((ph - 3.5) / 0.6)), old=0.6)
    if ph >= 6:
        A.d['gold'].chord((480, GROUND - 260, 540, GROUND - 220), 0, 180, fill=255)
    A.flush(cv)
    if ph < 1.5:
        paste(cv, text_img('免胄释甲 · 单骑而出', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(ph / 0.3))
    elif ph < 4.5:
        paste(cv, text_img('回纥将士持弓以待', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    else:
        paste(cv, text_img('果吾父也 · 皆下马拜', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((ph - 4.5) / 0.3))

def art_g_strike(A, cv, t, u):
    ground(A, GROUND)
    for k in range(8):
        rider(A, lerp(-200, 700, ease_out(u / (2.5 * P))) - (k % 4) * 100, GROUND - (k // 4) * 40, 100, 1, t * 12 + k, layer='zi' if k % 2 else 'tong', spear=True)
    for k in range(8):
        rider(A, lerp(900, 1300, ease_out((u - 1.5 * P) / (2 * P))) + (k % 4) * 80, GROUND - (k // 4) * 40, 90, 1, t * 12 + k, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('联合回纥 · 大破吐蕃', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_tomb(A, cv, t, u):
    for k in range(30):
        A.d['wash'].ellipse((80 + (k * 37) % 920 - 2, 640 + (k * 53) % 300 - 2, 80 + (k * 37) % 920 + 2, 640 + (k * 53) % 300 + 2), fill=255)
    A.d['mid'].chord((340, 1180, 740, GROUND + 200), 180, 360, fill=230)
    A.d['ink'].rectangle((500, 1260, 580, GROUND), fill=255)
    ground(A, GROUND)
    guo(A, 860, GROUND, 210, dir=-1, armour=False, arm=-8, old=0.7)
    A.flush(cv)
    stamp(cv, seal('祖坟被掘', 46, INK), 260, 880, t, t - u + 0.4, rot=-5)
    type_in(cv, text_img('此乃天谴 非人事也', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 1.5 * P, 0.5)

def art_g_jinzhi(A, cv, t, u):
    """6-beat legend: 打金枝 — his son strikes the princess; he binds the son and brings him to court; the emperor laughs:
    不痴不聋 不作家翁."""
    ph = u / P
    palace(A, 540, 1140, 560, layer='zi')
    ground(A, GROUND)
    person(A, 740, GROUND - 30, 220, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, ease_out((ph - 3) / 0.6)), layer='ink')
    guo(A, 340, GROUND, 220, dir=1, armour=False, kneel=True, bow=40, arm=110, old=0.7)
    person(A, 480, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, bow=50, arm=-8, layer='mid')
    A.d['tong'].line((440, GROUND - 120, 520, GROUND - 120), fill=255, width=6)
    A.flush(cv)
    stamp(cv, seal('戏曲故事', 40, INK), 860, 880, t, t - u + 0.4, rot=6)
    if ph >= 3:
        type_in(cv, text_img('不痴不聋 不作家翁', SERIF, 50, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 3 * P, 0.5)

def art_g_opendoor(A, cv, t, u):
    A.d['zi'].rectangle((240, 960, 840, GROUND), fill=200)
    A.d['ink'].polygon([(200, 960), (880, 960), (540, 860)], fill=255)
    A.d['wash'].rectangle((440, 1120, 640, GROUND), fill=255)
    ground(A, GROUND)
    for k in range(4):
        person(A, lerp(1100, 520 + k * 30, ((t * 0.12 + k * 0.25) % 1)), GROUND, 110, dir=-1, robe=False, hat='knot', ph=t * 4 + k, arm=20, layer='mid')
    A.flush(cv)
    paste(cv, text_img('府门大开 · 任人出入', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    paste(cv, text_img('坦坦荡荡 · 不留把柄', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((u - P) / 0.3))

# ================================================================ 第五回 满床笏
def art_g_shangfu(A, cv, t, u):
    palace(A, 540, 1140, 560, layer='tong')
    ground(A, GROUND)
    person(A, 720, GROUND - 30, 220, dir=-1, robe=True, hat='crown', bow=20, arm=90, layer='ink')
    guo(A, 360, GROUND, 230, dir=1, armour=False, arm=40, old=0.9)
    A.flush(cv)
    stamp(cv, seal('尚父', 60), 860, 880, t, t - u + P, rot=6)
    paste(cv, text_img('德宗尊为尚父', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_g_bed(A, cv, t, u):
    """6-beat legend: 满床笏 — on his birthday the sons and sons-in-law come; their tablets of office fill the couch."""
    ph = u / P
    couch(A, 540, 1240, 640, int(clamp(ph / 4) * 24), t=t)
    for k in range(int(clamp(ph / 4) * 10)):
        person(A, 120 + k * 90, GROUND, 120, dir=1 if k < 5 else -1, robe=True, hat='none', kneel=True, bow=40, arm=100, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('传说', 44, INK), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('七子八婿 · 皆为朝廷显官', SERIF, 46, ZI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp((ph - 1) / 0.4))

def art_g_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    guo(A, 540, 1200, 220, dir=1, armour=False, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('寿终正寝 · 年八十四', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_jianling(A, cv, t, u):
    A.d['mid'].polygon([(100, GROUND), (360, 1040), (620, GROUND)], fill=200)
    A.d['zi'].chord((640, 1220, 900, GROUND + 140), 180, 360, fill=220)
    ground(A, GROUND)
    for k in range(6):
        person(A, 640 + k * 50, GROUND, 110, dir=1, robe=True, hat='none', kneel=True, bow=50, arm=100, layer='ink')
    A.flush(cv)
    stamp(cv, seal('陪葬建陵', 44), 860, 880, t, t - u + 0.4, rot=6)
    paste(cv, text_img('德宗辍朝五日', SERIF, 48, ZI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.3))

def art_g_fuxing(A, cv, t, u):
    ground(A, GROUND)
    guo(A, 540, GROUND, 280, dir=1, armour=False, arm=60, old=0.8)
    for k in range(12):
        a = k * 2 * math.pi / 12 - t * 0.3
        A.d['gold'].ellipse((540 + 330 * math.cos(a) - 16, 1080 + 140 * math.sin(a) - 16, 540 + 330 * math.cos(a) + 16, 1080 + 140 * math.sin(a) + 16), fill=230)
    A.flush(cv)
    paste(cv, text_img('民间奉为福禄寿之神', SERIF, 46, TONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('一说', 40, INK), 860, 1040, t, t - u + 0.4, rot=6)

def art_g_perfect(A, cv, t, u):
    ground(A, GROUND)
    for i, nm in enumerate(('权倾天下', '朝不之忌', '功盖一代', '主不之疑')):
        x = 200 + i * 230
        A.d['zi' if i % 2 else 'tong'].rectangle((x - 80, GROUND - 60 - 60 * ease_out((u - i * 0.2 * P) / P), x + 80, GROUND), fill=220)
    A.flush(cv)
    for i, nm in enumerate(('权倾天下', '朝不之忌', '功盖一代', '主不之疑')):
        paste(cv, text_img(nm, SERIF, 30, INK, 'Black', bleed=False, vertical=True), 200 + i * 230, 1180, 1, clamp((u - i * 0.2 * P) / 0.4))
    paste(cv, text_img('新唐书 · 评语', SERIF, 42, DIM, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_legacy(A, cv, t, u):
    couch(A, 860, 1440, 260, 12, t=t)

def art_g_title(A, cv, t, u):
    flag(A, 820, 1460, 560, t, w=140, layer='zi')
    guo(A, 400, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), spear=True)

# ================================================================ script
CHAPTERS = {16: ('第一回', '大器晚成'), 48: ('第二回', '再造唐室'), 80: ('第三回', '功高被谗'),
            112: ('第四回', '单骑退敌'), 144: ('第五回', '满床笏')}

CARDS = [
    C(0, 2, 'empire', 'num', num='四朝元老', line='再造大唐', art=art_g_hook_four),
    C(2, 4, 'war', 'num', num='一人一马', line='退三十万大军', art=art_g_hook_alone),
    C(4, 6, 'life', 'num', num='满床笏', line='七子八婿皆显贵', art=art_g_hook_bed),
    C(6, 8, 'end', 'num', num='八十四岁', line='功高却得善终', art=art_g_hook_85),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 大器晚成
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=697, main='生于华州', sub='太原郭氏', art=art_g_birth),
    C(22, 26, 'works', 'card', year=717, main='武举高第', sub='以武举入仕', note='入仕之年 一说', art=art_g_wuju),
    C(26, 30, 'war', 'card', year=730, main='戍守边关', sub='一守就是几十年', art=art_g_frontier),
    C(30, 34, 'fate', 'card', year=745, main='默默无闻', sub='官职升迁缓慢', art=art_g_slow),
    C(34, 38, 'war', 'card', year=754, main='天德军使', sub='朔方前线', art=art_g_shuofang),
    C(38, 42, 'night', 'card', year=755, main='安史之乱', sub='范阳起兵 · 天下震动', art=art_g_rebellion),
    C(42, 46, 'empire', 'card', year=755, main='朔方节度使', sub='受命讨贼', art=art_g_jiedu),
    C(46, 48, 'court', 'card', year=756, main='举荐李光弼', sub='不计前嫌', art=art_g_liguangbi),
    # ---- 第二回 再造唐室
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=756, main='嘉山大捷', sub='与李光弼合击史思明', art=art_g_jiashan),
    C(54, 58, 'court', 'card', year=756, main='灵武勤王', sub='护卫新君', art=art_g_lingwu),
    C(58, 62, 'works', 'card', year=757, main='借兵回纥', sub='兵力不足 · 外借铁骑', art=art_g_huihe),
    C(62, 70, 'war', 'liangjing', year=757),
    C(70, 74, 'empire', 'card', year=757, main='再造之功', sub='肃宗亲迎于灞上', art=art_g_zaizao),
    C(74, 80, 'death', 'card', year=759, main='相州之败', sub='九节度使围邺城', art=art_g_xiangzhou),
    # ---- 第三回 功高被谗
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'fate', 'card', year=759, main='解除兵权', sub='被召回京 · 闲居', art=art_g_stripped),
    C(86, 90, 'night', 'card', year=760, main='宦官谗言', sub='屡遭排挤', art=art_g_yuchaoen),
    C(90, 94, 'war', 'card', year=762, main='复起平乱', sub='河中兵变', art=art_g_hezhong),
    C(94, 98, 'death', 'card', year=763, main='吐蕃入京', sub='长安失陷', art=art_g_tubo),
    C(98, 106, 'war', 'card', year=763, main='疑兵复京', sub='兵不过数千', note='虚张声势 以少胜多', art=art_g_decoy),
    C(106, 110, 'empire', 'card', year=763, main='迎驾还京', sub='再次收复长安', art=art_g_welcome),
    C(110, 112, 'night', 'card', year=764, main='部将反叛', sub='仆固怀恩叛唐', art=art_g_pugu),
    # ---- 第四回 单骑退敌
    C(112, 114, 'war', 'chapter'),
    C(114, 118, 'war', 'card', year=765, main='三十万敌', sub='仆固怀恩引外兵入寇', art=art_g_300k),
    C(118, 126, 'fate', 'card', year=765, main='单骑见回纥', sub='年近七十 · 免胄入营', art=art_g_alone),
    C(126, 130, 'war', 'card', year=765, main='合击吐蕃', sub='化敌为友', art=art_g_strike),
    C(130, 134, 'night', 'card', year=767, main='祖坟被掘', sub='一说宦官所为', art=art_g_tomb),
    C(134, 140, 'court', 'card', year=773, main='打金枝', sub='儿子郭暧与升平公主', note='戏曲故事 一说', art=art_g_jinzhi),
    C(140, 144, 'life', 'card', year=775, main='府门大开', sub='功高不震主', art=art_g_opendoor),
    # ---- 第五回 满床笏
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=779, main='尚父', sub='四朝元老', art=art_g_shangfu),
    C(150, 156, 'life', 'card', year=780, main='满床笏', sub='寿宴之上', note='传说', art=art_g_bed),
    C(156, 160, 'death', 'card', year=781, main='寿终', sub='长安府中', art=art_g_death),
    C(160, 164, 'court', 'card', year=781, main='陪葬建陵', sub='葬礼极尽哀荣', art=art_g_jianling),
    C(164, 168, 'works', 'card', year=1060, main='史家评语', sub='新唐书', art=art_g_perfect),
    C(168, 170, 'end', 'card', year=2026, main='福星', sub='富贵寿考的化身', art=art_g_fuxing),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='肆拾', col=ZI, acc=TONG, born=697, died=781,
    hook_q='功高震主的人大多没好下场 · 他是怎么做到的？',
    name_line='郭子仪 · 华州郑县人', name='郭子仪', seal='汾阳', title_art=art_g_title,
    q1='再造大唐？', q2='明哲保身？',
    end_art=art_g_legacy, end_big='再造大唐', end_seal='汾阳王',
    end_l1='他救了大唐两次', end_l2='也救了自己一辈子',
    end_brush='功盖天下而主不疑', end_ask='你学得会他的隐忍吗？评论区聊聊', next='狄仁杰'),
    scenes=dict(chapter=scene_chapter, liangjing=scene_liangjing))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
