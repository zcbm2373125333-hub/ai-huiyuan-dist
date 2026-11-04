"""千古人物志 · 第伍拾陆集 · 汉光武帝刘秀 (前5–57)
Look: 炎汉赤 + 洛水碧, 汉瓦当 corner borders, a 坐骑 chapter card: he rides an ox, then a horse, then a war chariot,
then the imperial carriage, and in the last chapter the carriage stands empty.
Set pieces: 6-beat 骑牛起兵, custom 8-beat scene 'kunyang' (昆阳之战), 6-beat 亡命河北, 6-beat 焚书安众,
6-beat 天下一统 map.
Ages are counted in 虚岁 (age0 = born) so that he dies 年六十二 as 后汉书 says.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_xiaohe as Xh          # engine + helpers (previous episode)
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

F.RIPPLE = False
YANHAN = (176, 52, 42)              # 炎汉赤
LUOBI = (66, 118, 108)              # 洛水碧
S.LAYERS.append(('yanhan', YANHAN, 0.9, 1.0))
S.LAYERS.append(('luobi', LUOBI, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='汉', life='秀', court='汉', night='夜', war='昆', empire='汉', works='柔', fate='河', death='终', end='兴')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('night', 'death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = (YANHAN, 230, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (YANHAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (LUOBI, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

FIELD = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(FIELD)
for _k in range(4):                 # 南阳 paddies and the 洛水 lines
    _y = 1450 + _k * 20
    _d.line((60, _y, W - 60, _y), fill=LUOBI + (40 - _k * 6,), width=3)
for _x in range(90, W - 60, 54):    # rice seedlings at the margins only
    if 260 < _x < 820: continue
    for _j in range(2):
        _d.line((_x + _j * 12, 1440, _x + _j * 12 - 6, 1410), fill=(90, 120, 70, 60), width=3)
MTN_COL = {'night': (34, 32, 40), 'death': (62, 56, 58), 'war': (114, 60, 48), 'fate': (90, 100, 98)}
def draw_background(t, theme):
    """南阳 · 洛阳: soft hills, rice seedlings at the margins and the river lines."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 186, 178), (150, 162, 150), MTN_COL.get(theme, (102, 124, 112))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(FIELD)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """汉瓦当: a round eaves tile with a cross and four dots in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=LUOBI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=LUOBI + (220,), width=3)
        cx, cy = x + sx * 54, y + sy * 54
        d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), outline=YANHAN + (230,), width=5)
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=YANHAN + (230,))
        d.line((cx - 34, cy, cx + 34, cy), fill=YANHAN + (200,), width=3); d.line((cx, cy - 34, cx, cy + 34), fill=YANHAN + (200,), width=3)
        for a in range(4):
            ang = math.radians(45 + a * 90)
            d.ellipse((cx + 20 * math.cos(ang) - 4, cy + 20 * math.sin(ang) - 4, cx + 20 * math.cos(ang) + 4, cy + 20 * math.sin(ang) + 4), fill=YANHAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xiu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, emperor=False, armour=False, **kw):
    """刘秀: tall (身长七尺三寸), 美须眉 — as a youth a plain kerchief; as general a helmet; as emperor a 冕 with red ribbons."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hat = 'helmet' if armour else 'none'
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat=hat if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        if emperor:
            d.rectangle((x - 0.15 * h, y - 1.08 * h, x + 0.15 * h, y - 1.03 * h), fill=255)
            d.rectangle((x - 0.05 * h, y - 1.03 * h, x + 0.05 * h, y - 0.95 * h), fill=255)
            for k in range(5):
                A.d['yanhan'].line((x - 0.13 * h + k * 0.065 * h, y - 1.03 * h, x - 0.13 * h + k * 0.065 * h, y - 0.96 * h), fill=255, width=2)
        elif not armour:
            A.d['luobi'].chord((x - 0.08 * h, y - 1.04 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        d.polygon([(x + dir * 0.03 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.06 * h, y - 0.7 * h)], fill=255)
        A.d['yanhan'].rectangle((x - 0.08 * h, y - 0.58 * h, x + 0.08 * h, y - 0.53 * h), fill=255)
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.04 * h, y - 0.82 * h), (x + dir * 0.09 * h, y - 0.82 * h), (x + dir * 0.06 * h, y - 0.72 * h)], fill=255)
    return hand

def ox(A, x, y, s, dir=1, ph=None, layer='ink'):
    A.d[layer].ellipse((x - 0.7 * s, y - 0.8 * s, x + 0.7 * s, y - 0.3 * s), fill=255)
    hx = x + dir * 0.75 * s
    A.d[layer].ellipse((hx - 0.22 * s, y - 0.85 * s, hx + 0.22 * s, y - 0.5 * s), fill=255)
    A.d[layer].arc((hx - 0.35 * s, y - 1.1 * s, hx + 0.35 * s, y - 0.7 * s), 200, 340, fill=255, width=max(3, int(0.06 * s)))
    sw = 0 if ph is None else math.sin(ph)
    for k, lx in enumerate((-0.5, -0.3, 0.3, 0.5)):
        A.d[layer].line((x + lx * s, y - 0.4 * s, x + lx * s + sw * 0.12 * s * (1 if k % 2 else -1), y), fill=255, width=max(4, int(0.12 * s)))
    A.d[layer].line((x - dir * 0.7 * s, y - 0.65 * s, x - dir * 0.85 * s, y - 0.35 * s), fill=255, width=3)

def bounty(A, x, y, s, layer='wash'):
    A.d[layer].rectangle((x - s, y - 1.3 * s, x + s, y + 1.3 * s), fill=255)
    A.d['ink'].rectangle((x - s, y - 1.3 * s, x + s, y + 1.3 * s), outline=255, width=4)
    A.d['ink'].ellipse((x - 0.5 * s, y - 0.9 * s, x + 0.5 * s, y + 0.1 * s), outline=255, width=4)

# ================================================================ chapter card
def art_mount_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    q = ease_out(u / (1.2 * P))
    x = lerp(220, 540, q)
    if kb == 16:
        ox(A, x, 1200, 160, dir=1, ph=t * 4)
        xiu(A, x - 10, 1200 - 120, 140, dir=1, arm=40, armour=True)
    elif kb == 48:
        rider(A, x, 1200, 200, dir=1, ph=t * 8, spear=True)
    elif kb == 80:
        carriage(A, x, 1200, 140, dir=1, wheel=t * 6, ph=t * 8, canopy=False, layer='yanhan')
        xiu(A, x, 1200 - 90, 140, dir=1, arm=60, armour=True)
    elif kb == 112:
        carriage(A, x, 1200, 160, dir=1, wheel=t * 4, ph=t * 6, layer='yanhan')
    else:
        carriage(A, 540, 1200, 160, dir=1, moving=False, horses=False, layer='mid')
    ground(A, 1210)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_mount_chapter)
    ink_in(cv, text_img(no, SERIF, 56, LUOBI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_v_hook_ox(A, cv, t, u):
    ground(A, GROUND)
    x = lerp(160, 620, ease_out(u / (1.6 * P)))
    ox(A, x, GROUND, 170, dir=1, ph=t * 5)
    xiu(A, x - 10, GROUND - 130, 150, dir=1, arm=40, armour=True)

def art_v_hook_10k(A, cv, t, u):
    ground(A, GROUND)
    for i in range(6):
        person(A, 140 + i * 50, GROUND, 90, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='yanhan')
    n = int(clamp(u / (1.4 * P)) * 40) + 1
    for i in range(n):
        person(A, 980 - (i % 10) * 44, GROUND - (i // 10) * 50, 70, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')

def art_v_hook_fire(A, cv, t, u):
    ground(A, GROUND)
    for i in range(8):
        bundle(A, 300 + i * 70, GROUND, 60, layer='mid')
    flames(A, 540, GROUND, 600, 240 * ease_out(u / P), t, n=7, seed=24, smoke=True)

def art_v_hook_bride(A, cv, t, u):
    ground(A, GROUND)
    person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, arm=40, layer='yanhan')
    xiu(A, 400, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / P)))

# ================================================================ 第一回 南阳布衣
def art_v_birth(A, cv, t, u):
    A.d['mid'].rectangle((360, 1080, 720, GROUND), fill=220)
    A.d['ink'].polygon([(320, 1080), (760, 1080), (540, 960)], fill=255)
    q = 0.5 + 0.5 * math.sin(t * 2)
    A.d['yanhan'].ellipse((540 - 160 - 40 * q, 1000 - 120, 540 + 160 + 40 * q, 1200), fill=int(60 + 40 * q))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父刘钦为济阳令 · 生于县舍', SERIF, 44, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('高祖九世孙', 40), 860, 1020, t, t - u + P, rot=6)

def art_v_orphan(A, cv, t, u):
    A.d['mid'].rectangle((600, GROUND - 200, 900, GROUND), fill=200)
    A.d['ink'].polygon([(580, GROUND - 200), (920, GROUND - 200), (750, GROUND - 280)], fill=255)
    ground(A, GROUND)
    person(A, 420, GROUND, 210, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    xiu(A, 520, GROUND, 100, dir=-1, arm=40)
    A.flush(cv)
    paste(cv, text_img('九岁丧父 · 养于叔父刘良', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_taixue(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='luobi')
    ground(A, GROUND)
    for i in range(4):
        sitter(A, 260 + i * 160, GROUND, 130, dir=1, bow=15, layer='mid' if i else 'ink')
    A.flush(cv)
    paste(cv, text_img('之长安 受尚书 略通大义', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('太学', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_jinwu(A, cv, t, u):
    ground(A, GROUND)
    for j in range(6):
        rider(A, (t * 120 + j * 200) % (W + 300) - 150, GROUND, 110, dir=1, ph=t * 8 + j, spear=True, layer='yanhan')
    xiu(A, 200, GROUND, 180, dir=1, arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    type_in(cv, text_img('仕宦当作执金吾 娶妻当得阴丽华', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_v_farm(A, cv, t, u):
    A.d['grass'].rectangle((60, GROUND - 60, W - 60, GROUND), fill=150)
    for k in range(10):
        A.d['luobi'].line((140 + k * 84, GROUND - 60, 150 + k * 84, GROUND - 130), fill=255, width=4)
    ground(A, GROUND)
    xiu(A, lerp(200, 480, ease_out(u / (2.5 * P))), GROUND - 60, 180, dir=1, bow=40, arm=150, ph=t * 3)
    person(A, 860, GROUND - 60, 200, dir=-1, robe=True, hat='knot', arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('性勤于稼穑 · 兄縯好侠 常笑之', SERIF, 44, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_famine(A, cv, t, u):
    A.d['dune'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=200)
    for k in range(8):
        A.d['ink'].line((120 + k * 110, GROUND - 40, 130 + k * 110, GROUND - 70), fill=200, width=3)
    ground(A, GROUND)
    for j in range(5):
        person(A, lerp(-100, 1100, ((t * 0.06 + j / 5) % 1)), GROUND, 120, dir=1, robe=True, hat='knot', bow=30, ph=t * 2 + j, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('王莽乱政 · 南阳荒饥 绿林赤眉蜂起', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_v_rise(A, cv, t, u):
    """6-beat set piece: 骑牛起兵 — the Liu brothers raise their banner at Chongling; he has no horse and rides an ox to war;
    after the first victory he takes a horse from the enemy."""
    ph = u / P
    ground(A, GROUND)
    banner(A, 860, GROUND, 320, t, layer='yanhan')
    for j in range(6):
        person(A, 560 + (j % 3) * 70, GROUND - (j // 3) * 40, 110, dir=-1, robe=False, hat='knot', arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
    if ph < 3.6:
        x = lerp(-100, 320, ease_out(ph / 2))
        ox(A, x, GROUND, 160, dir=1, ph=t * 4)
        xiu(A, x - 10, GROUND - 120, 140, dir=1, arm=60, armour=True)
    else:
        rider(A, lerp(300, 420, clamp((ph - 3.6) / 1)), GROUND, 170, dir=1, ph=t * 8, spear=True)
    A.flush(cv)
    lab = '舂陵起兵 · 时年二十八' if ph < 1.6 else ('初骑牛 杀新野尉 乃得马' if ph < 3.6 else '谨厚者亦复为之')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3.6 else LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    stamp(cv, seal('舂陵', 56), 260, 1020, t, t - u + 0.4, rot=-5)

# ================================================================ 第二回 昆阳
def art_v_gengshi(A, cv, t, u):
    for k in range(3):
        A.d['mid'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    person(A, 540, GROUND - 180, 190, dir=1, robe=True, hat='crown', arm=lerp(-8, 50, ease_out(u / 0.6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('诸将立刘玄为帝 · 年号更始', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('更始', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_horde(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (2.5 * P)) * 60) + 1
    for i in range(n):
        person(A, 980 - (i % 15) * 60, GROUND - (i // 15) * 50, 70, dir=-1, robe=False, hat='helmet', spear=True, arm=40, ph=t * 5 + i, layer='mid')
    for j in range(2):
        A.d['ink'].ellipse((200 + j * 140 - 50, GROUND - 160, 200 + j * 140 + 50, GROUND - 60), fill=255)
    A.flush(cv)
    paste(cv, text_img('王寻王邑 四十二万 号称百万 · 驱虎豹犀象', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def scene_kunyang(cv, t, c, k):
    """8-beat custom scene: 昆阳之战 — the little city is ringed by the huge Xin army; at night he slips out with thirteen riders;
    he returns leading three thousand volunteers straight at the enemy centre; thunder and a storm; the river floods; the host collapses."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    city_wall(A, 420, 660, 1120, gate_x=None, layer='mid')
    if ph < 5.2:
        for j in range(16):
            a = j * 2 * math.pi / 16
            x = 540 + 420 * math.cos(a); y = GROUND - 30 + 40 * math.sin(a)
            if y > GROUND - 70:
                person(A, x, GROUND, 80, dir=-1 if x > 540 else 1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
    if ph < 2:
        for j in range(4):
            rider(A, lerp(540, 1150, ease_out(ph / 2)) + j * 40, GROUND, 90, dir=1, ph=t * 10 + j, layer='yanhan')
    elif ph < 5.2:
        x0 = lerp(1200, 600, ease_out((ph - 2) / 1.6))
        for j in range(6):
            rider(A, x0 + j * 70, GROUND - (j % 2) * 20, 100, dir=-1, ph=t * 10 + j, spear=True, layer='yanhan')
    if ph >= 4:
        for k2 in range(30):
            q = (t * 1.2 + k2 / 30) % 1
            A.d['wash'].line((80 + (k2 * 37) % 920, lerp(620, 1300, q), 80 + (k2 * 37) % 920 - 14, lerp(620, 1300, q) + 50), fill=200, width=3)
        if int(t * 4) % 5 == 0:
            A.d['wash'].line((300, 640, 360, 760, 320, 800, 400, 940), fill=255, width=8)
    if ph >= 5.2:
        q = ease_out((ph - 5.2) / 1.2)
        A.d['luobi'].rectangle((60, GROUND - 40 * q, W - 60, GROUND + 40), fill=180)
        waves(A, GROUND - 40 * q, t, rows=2, amp=8, speed=3)
        for j in range(8):
            person(A, 600 + j * 60 + 40 * math.sin(t * 3 + j), GROUND - 20, 70, dir=1, robe=False, hat='helmet', fall=-60, arm=150, layer='ink')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '昆阳之战', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=56)
    fx.flush(cv)
    lab = '城中八九千人 · 夜与十三骑出城' if ph < 2 else ('还率三千敢死者 冲其中坚' if ph < 4 else ('大雷风 屋瓦皆飞 雨下如注' if ph < 5.2 else '滍川盛溢 莽军大溃'))
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2 else LUOBI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('以少胜多 · 新莽主力尽丧', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 6) / 0.4))

def art_v_brother(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 200, dir=1, robe=False, hat='helmet', kneel=True, bow=lerp(10, 60, ease_out(u / (2 * P))), arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('兄刘縯功高 为更始帝所杀', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_endure(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='luobi')
    ground(A, GROUND)
    person(A, 760, GROUND - 30, 190, dir=-1, robe=True, hat='crown', arm=40, layer='mid')
    xiu(A, 380, GROUND, 200, dir=1, kneel=True, bow=30, arm=100)
    A.flush(cv)
    paste(cv, text_img('不敢为兄服丧 · 饮食言笑如平常', SERIF, 44, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '独居辄不御酒肉 枕席有涕泣处', t, t - u + P)

def art_v_wedding(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='yanhan')
    ground(A, GROUND)
    xiu(A, 420, GROUND, 210, dir=1, arm=60)
    person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='yanhan')
    A.flush(cv)
    paste(cv, text_img('于宛城当成里 娶阴丽华', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('得偿所愿', 44), 860, 1020, t, t - u + P, rot=6)

def art_v_north(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    boat(A, lerp(200, 840, ease_out(u / (1.6 * P))), 1250, 120, t, sail=True)
    A.flush(cv)
    paste(cv, text_img('持节北渡 · 镇慰河北', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第三回 河北
def art_v_flee(A, cv, t, u):
    """6-beat set piece: 亡命河北 — Wang Lang posts a bounty of 十万户; he flees through the snow, half-starved; the Hutuo river
    freezes just long enough for his men to cross."""
    ph = u / P
    for k in range(60):
        q = (t * 0.5 + k / 60) % 1
        A.d['wash'].ellipse((80 + (k * 19) % 920 - 4, lerp(620, 1420, q) - 4, 80 + (k * 19) % 920 + 4, lerp(620, 1420, q) + 4), fill=220)
    if ph < 2:
        ground(A, GROUND)
        bounty(A, 540, 1060, 90)
        lab = '王郎称帝邯郸 · 购秀十万户'
    elif ph < 4:
        ground(A, GROUND)
        for j in range(4):
            rider(A, lerp(-200, 900, ease_out((ph - 2) / 2)) - j * 120, GROUND, 110, dir=1, ph=t * 8 + j, layer='ink')
        lab = '晨夜草舍 · 至饶阳 官属皆乏食'
    else:
        A.d['wash'].rectangle((60, 1200, W - 60, GROUND + 40), fill=230)
        for k2 in range(5):
            A.d['luobi'].line((120 + k2 * 200, 1220, 200 + k2 * 200, 1260), fill=150, width=3)
        for j in range(4):
            rider(A, lerp(100, 1000, ease_out((ph - 4) / 2)) - j * 120, 1220, 100, dir=1, ph=t * 8 + j, layer='ink')
        lab = '至滹沱河 · 冰合得渡'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph < 2 else LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)
    if ph >= 4:
        note_in(cv, '冰合之说见后汉书 带传奇色彩', t, t - u + 4 * P)

def art_v_guo(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='luobi')
    ground(A, GROUND)
    xiu(A, 420, GROUND, 210, dir=1, arm=60, armour=True)
    person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='mid')
    A.flush(cv)
    paste(cv, text_img('娶真定王刘扬之甥女郭圣通', SERIF, 44, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('联姻', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_handan(A, cv, t, u):
    city_wall(A, 520, 1000, 1080, gate_x=760, label='邯郸', layer='mid', open_=clamp((u - 2 * P) / P))
    ground(A, GROUND)
    army(A, lerp(-200, 160, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='yanhan', t=t, march=u < 2 * P, h=110)
    A.flush(cv)
    paste(cv, text_img('拔邯郸 · 诛王郎', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_letters(A, cv, t, u):
    """6-beat set piece: 焚书安众 — thousands of letters to Wang Lang from his own officers are found; he burns them unread before them all."""
    ph = u / P
    ground(A, GROUND)
    n = 12
    for i in range(n):
        x = 300 + (i % 6) * 80; y = GROUND - 20 - (i // 6) * 40
        A.d['wash'].rectangle((x - 30, y - 16, x + 30, y + 16), fill=255)
        A.d['ink'].rectangle((x - 30, y - 16, x + 30, y + 16), outline=200, width=2)
    if ph > 2.4:
        flames(A, 500, GROUND, 520, 280 * ease_out((ph - 2.4) / 1), t, n=7, seed=2401, smoke=True)
    for j in range(5):
        person(A, 780 + (j % 3) * 70, GROUND - (j // 3) * 40, 130, dir=-1, robe=False, hat='helmet', bow=20 if ph > 2.4 else 0, arm=-8, layer='mid')
    xiu(A, 160, GROUND, 200, dir=1, arm=lerp(-8, 140, clamp((ph - 2) / 0.4)), armour=True)
    A.flush(cv)
    lab = '得吏人与王郎交关谤毁者数千章' if ph < 2.4 else '会诸将军烧之 · 令反侧子自安'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2.4 else LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_v_tongma(A, cv, t, u):
    ground(A, GROUND)
    for j in range(10):
        person(A, 480 + (j % 5) * 90, GROUND - (j // 5) * 60, 110, dir=-1, robe=False, hat='helmet', spear=True, arm=40, layer='mid')
    rider(A, lerp(-100, 280, ease_out(u / (2 * P))), GROUND, 140, dir=1, ph=t * 6 if u < 2 * P else 0)
    A.flush(cv)
    type_in(cv, text_img('萧王推赤心置人腹中 安得不投死乎', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + P, 0.5)
    stamp(cv, seal('铜马', 56), 260, 1020, t, t - u + 0.4, rot=-5)

def art_v_crown(A, cv, t, u):
    for k in range(3):
        A.d['yanhan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    xiu(A, 540, GROUND - 180, 200, dir=1, emperor=True, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    paste(cv, text_img('即皇帝位于鄗南千秋亭', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('建武', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_luoyang(A, cv, t, u):
    river(A, 1260, t, rows=2, amp=4)
    city_wall(A, 220, 860, 1100, gate_x=540, label='洛阳', layer='luobi', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('定都洛阳', SERIF, 48, LUOBI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.3))

# ================================================================ 第四回 光武中兴
def art_v_chimei(A, cv, t, u):
    ground(A, GROUND)
    for j in range(12):
        person(A, 500 + (j % 6) * 80, GROUND - (j // 6) * 60, 110, dir=-1, robe=False, hat='knot', kneel=True, bow=40, arm=100, layer='red' if j % 3 == 0 else 'mid')
    xiu(A, 240, GROUND, 210, dir=1, emperor=True, arm=60)
    A.flush(cv)
    paste(cv, text_img('赤眉十余万众 · 宜阳请降', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_merge(A, cv, t, u):
    A.d['wash'].rounded_rectangle((140, 860, 940, 1340), radius=20, fill=170)
    n0 = 40
    q = ease_out(u / (2.5 * P))
    for i in range(n0):
        x = 170 + (i % 10) * 76; y = 890 + (i // 10) * 110
        keep = (i % 4 == 0) or q < (i % 4) / 4
        if keep:
            A.d['luobi'].rectangle((x, y, x + 66, y + 96), fill=200)
    A.flush(cv)
    num = int(lerp(0, 400, q))
    paste(cv, text_img(f'并省 {num} 余县 · 吏职减损 十置其一', SERIF, 42, LUOBI, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)

def art_v_longshu(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 300 - 60 * (k % 2)), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    xiu(A, 300, GROUND, 200, dir=1, emperor=True, arm=lerp(-8, 120, ease_out(u / 0.6)))
    A.flush(cv)
    type_in(cv, text_img('人苦不知足 既平陇 复望蜀', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.5, 0.5)
    stamp(cv, seal('得陇望蜀', 44), 860, 1020, t, t - u + P, rot=6)

def art_v_unify(A, cv, t, u):
    """6-beat set piece: 天下一统 — the map is cleared region by region: 赤眉, 刘永, 隗嚣, 公孙述; the last seal goes red."""
    ph = u / P
    A.d['wash'].rounded_rectangle((110, 760, 970, 1420), radius=24, fill=170)
    regions = [('赤眉', 600, 900, 27), ('刘永', 820, 1000, 29), ('隗嚣', 260, 960, 34), ('公孙述', 240, 1260, 36)]
    A.d['yanhan'].ellipse((560 - 80, 1080 - 80, 560 + 80, 1080 + 80), fill=200)
    k = min(4, int(ph / 1.2) + 1)
    for i, (nm, x, y, yr) in enumerate(regions):
        if i < k:
            A.d['yanhan'].ellipse((x - 70, y - 70, x + 70, y + 70), fill=int(160 * clamp((ph - i * 1.2) / 0.6)))
    A.flush(cv)
    stamp(cv, seal('洛阳', 40, ZHU), 560, 1080, t, t - u + 0.2)
    for i, (nm, x, y, yr) in enumerate(regions):
        stamp(cv, seal(nm, 36, ZHU if i < k else INK), x, y, t, t - u + 0.2)
    nm, _, _, yr = regions[k - 1]
    paste(cv, text_img(f'建武{cn_num(yr - 24)}年 · 平{nm}', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('十二年间 天下复归一统', SERIF, 42, INK, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.8) / 0.4))

def art_v_heroes(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='luobi')
    ground(A, GROUND)
    xiu(A, 760, GROUND - 30, 200, dir=-1, emperor=True, arm=lerp(20, 80, ease_out(u / 0.6)))
    for j in range(4):
        person(A, 200 + j * 90, GROUND, 160, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('功臣皆高秩厚礼 不任以吏职', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('保全功臣', 44), 860, 1020, t, t - u + P, rot=6)

def art_v_dutian(A, cv, t, u):
    A.d['grass'].rectangle((140, 900, 940, 1260), fill=150)
    q = ease_out(u / (2.5 * P))
    for k in range(1, 6):
        A.d['ink'].line((140 + 160 * k, 900, 140 + 160 * k, 900 + 360 * q), fill=200, width=4)
    for k in range(1, 3):
        A.d['ink'].line((140, 900 + 120 * k, 140 + 800 * q, 900 + 120 * k), fill=200, width=4)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('诏下州郡检核垦田顷亩及户口年纪', SERIF, 42, LUOBI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('度田', 56), 860, 1300, t, t - u + P, rot=6)

def art_v_empress(A, cv, t, u):
    palace(A, 540, 1260, 380, layer='yanhan')
    ground(A, GROUND)
    xiu(A, 420, GROUND, 210, dir=1, emperor=True, arm=60, old=0.4)
    person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, arm=60, layer='yanhan')
    A.flush(cv)
    paste(cv, text_img('废郭后 · 立阴丽华为皇后', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 中兴
def art_v_taishan(A, cv, t, u):
    A.d['mid'].polygon([(200, GROUND), (540, 860), (880, GROUND)], fill=200)
    xiu(A, 540, 900, 100, dir=1, emperor=True, arm=120, old=0.6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('东巡封泰山 · 禅梁父', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('封禅', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xiu(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('崩于南宫前殿 · 年六十二', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_frugal(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('皆如孝文皇帝制度 务从约省', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('遗诏', 56), 860, 1020, t, t - u + P, rot=6)

def art_v_yuntai(A, cv, t, u):
    A.d['luobi'].rectangle((140, 900, 940, 1260), fill=170)
    n = min(28, int(clamp(u / (2.5 * P)) * 28) + 1)
    for i in range(n):
        x = 180 + (i % 7) * 106; y = 940 + (i // 7) * 80
        person(A, x, y + 60, 56, dir=1, robe=False, hat='helmet', arm=40, layer='ink' if i % 2 else 'mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img(f'汉明帝图画二十八将于南宫云台 · {n}', SERIF, 40, LUOBI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, 1)

def art_v_wangfuzhi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    sitter(A, 300, GROUND, 190, dir=1, bow=15)
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    type_in(cv, text_img('三代而下 取天下者 唯光武独焉', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('王夫之', 50), 860, 1020, t, t - u + P, rot=6)

def art_v_rou(A, cv, t, u):
    river(A, 1220, t, rows=3, amp=4, speed=0.6)
    A.flush(cv)
    type_in(cv, text_img('吾理天下 亦欲以柔道行之', SERIF, 46, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)

def art_v_zhongxing(A, cv, t, u):
    palace(A, 540, 1260, 440, layer='yanhan')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('东汉一百九十五年', SERIF, 48, LUOBI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_v_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    ox(A, 860, 1380, 80, dir=-1)

def art_v_title(A, cv, t, u):
    ox(A, 820, 1460, 160, dir=-1)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    xiu(A, 380, 1460, 680, dir=1, emperor=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '南阳布衣'), 48: ('第二回', '昆阳'), 80: ('第三回', '河北'),
            112: ('第四回', '光武中兴'), 144: ('第五回', '柔道')}

CARDS = [
    C(0, 2, 'life', 'num', num='骑着牛', line='去造反', art=art_v_hook_ox),
    C(2, 4, 'war', 'num', num='一万人', line='击溃四十万', art=art_v_hook_10k),
    C(4, 6, 'night', 'num', num='一把火', line='烧掉通敌书信', art=art_v_hook_fire),
    C(6, 8, 'empire', 'num', num='娶妻当得', line='阴丽华', art=art_v_hook_bride),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 南阳布衣
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=-5, main='生于济阳', sub='汉室远支', note='赤光满室之说见后汉书', art=art_v_birth),
    C(22, 26, 'night', 'card', year=4, main='幼年丧父', sub='寄人篱下', art=art_v_orphan),
    C(26, 30, 'works', 'card', year=14, main='长安太学', sub='一个普通学生', art=art_v_taixue),
    C(30, 34, 'court', 'card', year=15, main='执金吾', sub='少年的两个愿望', art=art_v_jinwu),
    C(34, 38, 'life', 'card', year=20, main='勤于稼穑', sub='老实种地', art=art_v_farm),
    C(38, 42, 'death', 'card', year=22, main='天下大乱', sub='新莽末年', art=art_v_famine),
    C(42, 48, 'war', 'card', year=22, main='骑牛起兵', sub='舂陵', art=art_v_rise),
    # ---- 第二回 昆阳
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'court', 'card', year=23, main='更始称帝', sub='刘玄', art=art_v_gengshi),
    C(54, 58, 'death', 'card', year=23, main='大军压境', sub='号称百万', art=art_v_horde),
    C(58, 66, 'war', 'kunyang', year=23),
    C(66, 70, 'death', 'card', year=23, main='兄长被杀', sub='功高震主', art=art_v_brother),
    C(70, 74, 'night', 'card', year=23, main='隐忍', sub='不敢服丧', art=art_v_endure),
    C(74, 78, 'life', 'card', year=23, main='娶阴丽华', sub='少年之愿', art=art_v_wedding),
    C(78, 80, 'fate', 'card', year=23, main='持节北渡', sub='蛟龙出渊', art=art_v_north),
    # ---- 第三回 河北
    C(80, 82, 'fate', 'chapter'),
    C(82, 88, 'night', 'card', year=24, main='亡命河北', sub='十万户悬赏', art=art_v_flee),
    C(88, 92, 'court', 'card', year=24, main='真定联姻', sub='借兵', art=art_v_guo),
    C(92, 96, 'war', 'card', year=24, main='攻克邯郸', sub='王郎伏诛', art=art_v_handan),
    C(96, 102, 'works', 'card', year=24, main='焚书安众', sub='不看一封', art=art_v_letters),
    C(102, 106, 'empire', 'card', year=24, main='收编铜马', sub='推心置腹', art=art_v_tongma),
    C(106, 110, 'empire', 'card', year=25, main='登基称帝', sub='东汉开国', art=art_v_crown),
    C(110, 112, 'court', 'card', year=25, main='定都洛阳', sub='东京', art=art_v_luoyang),
    # ---- 第四回 光武中兴
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'war', 'card', year=27, main='赤眉投降', sub='宜阳', art=art_v_chimei),
    C(118, 122, 'works', 'card', year=30, main='并省郡县', sub='精兵简政', art=art_v_merge),
    C(122, 126, 'court', 'card', year=32, main='得陇望蜀', sub='人苦不知足', art=art_v_longshu),
    C(126, 132, 'war', 'card', year=36, main='天下一统', sub='平公孙述', art=art_v_unify),
    C(132, 136, 'life', 'card', year=37, main='退功臣', sub='不杀一个', art=art_v_heroes),
    C(136, 140, 'works', 'card', year=39, main='度田', sub='清查土地', art=art_v_dutian),
    C(140, 144, 'court', 'card', year=41, main='立阴丽华', sub='为皇后', art=art_v_empress),
    # ---- 第五回 柔道
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=56, main='泰山封禅', sub='中兴告成', art=art_v_taishan),
    C(150, 154, 'death', 'card', year=57, main='光武驾崩', sub='南宫', art=art_v_death),
    C(154, 158, 'fate', 'card', year=57, main='遗诏薄葬', sub='务从约省', art=art_v_frugal),
    C(158, 162, 'court', 'card', year=60, main='云台二十八将', sub='功臣善终', art=art_v_yuntai),
    C(162, 166, 'works', 'card', year=1690, main='王夫之曰', sub='三代以下第一人', art=art_v_wangfuzhi),
    C(166, 168, 'life', 'card', year=1690, main='以柔治国', sub='他的治国之道', art=art_v_rou),
    C(168, 170, 'end', 'card', year=1690, main='光武中兴', sub='东汉近二百年', art=art_v_zhongxing),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='伍拾陆', col=LUOBI, acc=YANHAN, born=-5, died=57, age0=-5,
    born_lab='前5年', died_lab='57年', years_txt='公元前5 — 公元57',
    hook_q='他起兵时连马都没有 · 怎么当上了皇帝？',
    name_line='刘秀 · 字文叔', name='汉光武帝', seal='光武', title_art=art_v_title,
    q1='位面之子？', q2='最被低估的皇帝？',
    end_art=art_v_legacy, end_big='光武中兴', end_seal='光武',
    end_l1='他起兵时骑的是一头牛', end_l2='最后赢下的却是整个天下',
    end_brush='有志者事竟成', end_ask='刘秀是不是最被低估的皇帝？评论区聊聊', next='王昭君'),
    scenes=dict(chapter=scene_chapter, kunyang=scene_kunyang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
