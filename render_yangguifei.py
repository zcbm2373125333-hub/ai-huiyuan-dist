"""千古人物志 · 第捌拾壹集 · 杨贵妃 (719–756)
Look: 妃红 + 霓裳紫, 披帛 corner borders (a fluttering silk ribbon), 骊山 and the 华清 pools behind.
Chapter card: 荔枝 — a lychee branch; each chapter more fruit ripens red; in the last chapter the fruit falls.
Set pieces: custom 8-beat scene 'nichang' (霓裳羽衣舞), 6-beat 骊山初见, 6-beat 剪发, 6-beat 一骑红尘, 8-beat 马嵬, 6-beat 香囊.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_jianzhen as Jz        # engine + helpers (previous episode)
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
from render_quyuan import river
from render_simayi import emperor
from render_sunwu import army, banner
from render_zhouyu import guqin

F.RIPPLE = False
FEIHONG = (168, 58, 84)             # 妃红
NICHANG = (120, 136, 190)           # 霓裳紫
S.LAYERS.append(('feihong', FEIHONG, 0.9, 1.0))
S.LAYERS.append(('nichang', NICHANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='妃', life='玉', court='唐', night='宠', war='乱', empire='贵', works='舞', fate='遣', death='嵬', end='恨')
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
G.THEMES['empire']['sun'] = (FEIHONG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (NICHANG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # steam over the hot springs
    _d.line([(60 + i * 30, 1450 + _k * 14 + 5 * math.sin(i * 0.6 + _k)) for i in range(34)], fill=NICHANG + (44 - _k * 10,), width=3)
for _x in (110, 970):               # lychee sprigs at the margins
    _d.line((_x, 1446, _x, 1340), fill=(90, 110, 70, 70), width=4)
    for _j in range(3):
        _d.ellipse((_x - 22 + _j * 14, 1330 + (_j % 2) * 10, _x - 8 + _j * 14, 1344 + (_j % 2) * 10), fill=(196, 64, 72, 80))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (100, 96, 104)}
def draw_background(t, theme):
    """骊山: soft hills over the 华清 springs, lychees at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 190, 194), (170, 158, 170), MTN_COL.get(theme, (128, 112, 130))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """披帛: a silk ribbon fluttering in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=FEIHONG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=FEIHONG + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line([(cx - 30 * sx, cy - 20 * sy), (cx - 10 * sx, cy - 30 * sy), (cx + 10 * sx, cy - 10 * sy), (cx + 30 * sx, cy - 20 * sy)], fill=NICHANG + (230,), width=6)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def yu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, dance=0.0, t=0.0, **kw):
    """杨玉环: a Tang court lady — high 云髻 with a hairpin and flower, full figure, a long silk 披帛 that flies when she dances."""
    up = not kneel and abs(bow) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none', female=True, layer=layer, kneel=kneel, bow=bow, **kw)
    if not kw.get('fall'):
        top = y - (0.62 if kneel else 1.0) * h
        A.d[layer].ellipse((x - 0.07 * h, top - 0.12 * h, x + 0.07 * h, top + 0.02 * h), fill=255)
        A.d['feihong'].ellipse((x + 0.03 * h, top - 0.08 * h, x + 0.07 * h, top - 0.04 * h), fill=255)
        A.d['qiuhuang'].line((x - 0.08 * h, top - 0.06 * h, x + 0.1 * h, top - 0.1 * h), fill=255, width=max(2, int(0.01 * h)))
        A.d['feihong'].polygon([(x - 0.12 * h, y - 0.55 * h), (x + 0.12 * h, y - 0.55 * h), (x + 0.18 * h, y - 0.02 * h), (x - 0.18 * h, y - 0.02 * h)], fill=170)
        sw = dance
        pts = [(x - 0.14 * h + 0.5 * h * sw * math.sin(t * 3 + k * 0.6) * k / 6, y - 0.65 * h + k * 0.08 * h - 0.2 * h * sw * math.cos(t * 3 + k * 0.5) * k / 6) for k in range(7)]
        A.d['nichang'].line(pts, fill=255, width=max(3, int(0.018 * h)))
        pts2 = [(x + 0.14 * h - 0.5 * h * sw * math.sin(t * 3 + k * 0.6 + 1) * k / 6, y - 0.65 * h + k * 0.08 * h - 0.2 * h * sw * math.cos(t * 3 + k * 0.5 + 1) * k / 6) for k in range(7)]
        A.d['nichang'].line(pts2, fill=255, width=max(3, int(0.018 * h)))
    return hand

def xuanzong(A, x, y, h, dir=-1, old=0.0, **kw):
    hand = emperor(A, x, y, h, dir=dir, **kw)
    if old > 0.4 and not kw.get('kneel') and not kw.get('fall'):
        A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.09 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.66 * h)], fill=255)
    return hand

def lychee_branch(A, cx, cy, s, ripe, fall=0.0):
    A.d['huyang'].line([(cx - s, cy + 0.3 * s), (cx - 0.3 * s, cy), (cx + 0.6 * s, cy - 0.2 * s)], fill=255, width=max(4, int(0.04 * s)))
    for k in range(6):
        lx, ly = cx - 0.8 * s + k * 0.28 * s, cy + 0.2 * s - k * 0.08 * s
        A.d['grass'].ellipse((lx - 0.12 * s, ly - 0.22 * s, lx + 0.12 * s, ly - 0.12 * s), fill=255)
    r = random.Random(5)
    for k in range(10):
        fx = cx - 0.6 * s + (k % 5) * 0.25 * s + r.uniform(-0.05, 0.05) * s
        fy = cy + 0.1 * s + (k // 5) * 0.14 * s + fall * (300 + 40 * k) * (k % 3 == 0)
        lay = 'red' if k < ripe else 'grass'
        A.d[lay].ellipse((fx - 0.06 * s, fy - 0.06 * s, fx + 0.06 * s, fy + 0.06 * s), fill=255)

def pool(A, cx, base, w, t):
    A.d['wash'].rectangle((cx - w, base - 0.08 * w, cx + w, base), fill=230)
    A.d['ocean'].ellipse((cx - 0.9 * w, base - 0.2 * w, cx + 0.9 * w, base + 0.02 * w), fill=170)
    for k in range(5):
        q = (t * 0.3 + k / 5) % 1
        A.d['wash'].ellipse((cx - 0.6 * w + k * 0.3 * w - 30 - 20 * q, base - 0.2 * w - 200 * q - 20, cx - 0.6 * w + k * 0.3 * w + 30 + 20 * q, base - 0.2 * w - 200 * q + 20), fill=int(180 * (1 - q)))

# ================================================================ chapter card
CH = {16: (0, 2), 48: (2, 5), 80: (5, 8), 112: (8, 10), 144: (10, 10)}
def art_lychee_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (2, 5))
    q = ease_out(u / (1.2 * P))
    lychee_branch(A, 540, 1060, 300, int(lerp(a, b, clamp((q - 0.2) / 0.6))), fall=clamp((q - 0.5) / 0.5) if kb == 144 else 0.0)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_lychee_chapter)
    ink_in(cv, text_img(no, SERIF, 56, FEIHONG, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_g_hook_horse(A, cv, t, u):
    ground(A, GROUND)
    rider(A, lerp(-100, 700, ease_out(u / (1.2 * P))), GROUND, 160, dir=1, ph=t * 8, layer='ink')
    for k in range(8):
        q = (t * 1.5 + k / 8) % 1
        A.d['dune'].ellipse((lerp(-100, 700, ease_out(u / (1.2 * P))) - 120 - 200 * q - 20, GROUND - 30 - 40 * q - 20, lerp(-100, 700, ease_out(u / (1.2 * P))) - 120 - 200 * q + 20, GROUND - 30 - 40 * q + 20), fill=int(160 * (1 - q)))

def art_g_hook_three(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        person(A, 140 + j * 110, GROUND, 120, dir=1, robe=True, hat='none', female=True, arm=-8, layer='mid')
    yu(A, 540, GROUND, 260, dir=1, arm=-8, t=t, dance=0.3)

def art_g_hook_silk(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].line((540, 760, 540, lerp(760, 1200, ease_out(u / (1.0 * P)))), fill=255, width=14)

def art_g_hook_scroll(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.0 * P)), layer='wash')

# ================================================================ 第一回 寿王妃
def art_g_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 240), (x + 60, GROUND - 240), (x + 220, GROUND)], fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('父杨玄琰为蜀州司户', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('蜀州', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '出生地另有容州 永乐等说', t, t - u + P)

def art_g_orphan(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='洛阳', layer='mid', open_=1.0)
    ground(A, GROUND)
    person(A, 460, GROUND, 210, dir=1, robe=True, hat='knot', arm=60, layer='ink')
    yu(A, 600, GROUND, 120, dir=-1, arm=-8, t=t)
    A.flush(cv)
    paste(cv, text_img('幼年丧父 · 寄养于洛阳叔父杨玄璬家', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_talent(A, cv, t, u):
    ground(A, GROUND)
    guqin(A, 360, GROUND - 40, 160, 7, t)
    yu(A, 680, GROUND, 210, dir=-1, arm=lerp(40, 140, 0.5 + 0.5 * math.sin(t * 2)), dance=0.4, t=t)
    A.flush(cv)
    paste(cv, text_img('资质丰艳 · 善歌舞 通音律', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_shouwang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='feihong')
    ground(A, GROUND)
    person(A, 400, GROUND, 210, dir=1, robe=True, hat='crown', arm=-8, layer='ink')
    yu(A, 640, GROUND, 190, dir=-1, bow=15, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('册为寿王李瑁之妃 · 时年十七', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('寿王妃', 50), 860, 1020, t, t - u + P, rot=6)

def art_g_wuhuifei(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    xuanzong(A, 540, GROUND, 220, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('武惠妃去世 · 后宫无当意者', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_lishan(A, cv, t, u):
    """6-beat set piece: 骊山 — at the 温泉宫 on 骊山 someone tells the emperor of the 杨 girl whose beauty is first of her age; he sees her."""
    ph = u / P
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 320), (x + 220, GROUND)], fill=140)
    pool(A, 540, GROUND, 360, t)
    ground(A, GROUND)
    if ph < 2:
        xuanzong(A, 700, GROUND, 210, dir=-1, arm=-8)
        person(A, 480, GROUND, 180, dir=1, robe=True, hat='knot', bow=30, arm=90, layer='mid')
        lab = '骊山温泉宫 · 有人奏言 杨氏女姿色冠代'
    else:
        xuanzong(A, 760, GROUND, 210, dir=-1, arm=lerp(-8, 80, clamp((ph - 2.5) / 0.6)))
        yu(A, 380, GROUND, 200, dir=1, arm=-8, t=t, dance=0.2)
        lab = '玄宗一见倾心' if ph >= 3.5 else '召见于温泉宫'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 3.5 else FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '时玄宗五十六 杨氏二十二', t, t - u + 3 * P)

def art_g_taizhen(A, cv, t, u):
    ground(A, GROUND)
    Jz.temple(A, 540, GROUND - 40, 260, layer='mid')
    yu(A, 540, GROUND, 190, dir=1, arm=60, t=t)
    A.flush(cv)
    paste(cv, text_img('先令出家为女道士 · 号太真', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '以此掩人耳目 寿王另娶韦氏', t, t - u + P)

# ================================================================ 第二回 贵妃
def art_g_guifei(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    yu(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), t=t)
    A.flush(cv)
    paste(cv, text_img('册为贵妃 · 礼数实同皇后', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('贵妃', 56), 860, 1020, t, t - u + P, rot=6)

def scene_nichang(cv, t, c, k):
    """8-beat custom scene: 霓裳羽衣舞 — the emperor beats the 羯鼓; she dances the 霓裳羽衣 suite; ribbons sweep the hall;
    musicians of the 梨园 accompany."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    for i in range(24):
        a = i * 2 * math.pi / 24 + t * 0.2
        A.d['nichang'].ellipse((540 + 380 * math.cos(a) - 6, 1000 + 160 * math.sin(a) - 6, 540 + 380 * math.cos(a) + 6, 1000 + 160 * math.sin(a) + 6), fill=int(180 * clamp(ph / 2)))
    xuanzong(A, 860, GROUND, 170, dir=-1, kneel=True, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 8)))
    A.d['huyang'].ellipse((760, GROUND - 90, 820, GROUND - 40), fill=255)
    for j in range(3):
        person(A, 120 + j * 90, GROUND, 120, dir=1, robe=True, hat='knot', kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
    spin = math.sin(t * 2.4)
    yu(A, 540 + 40 * spin, GROUND, 230, dir=1 if spin > 0 else -1, arm=lerp(60, 160, 0.5 + 0.5 * math.sin(t * 3)), dance=clamp(ph / 1.5), t=t)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '霓裳羽衣', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=81)
    fx.flush(cv)
    lab = '玄宗亲击羯鼓' if ph < 3 else ('贵妃起舞 霓裳羽衣' if ph < 6 else '梨园弟子 和而歌之')
    paste(cv, text_img(lab, SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '霓裳羽衣曲相传为玄宗所作', t, s0 + 3 * P)

def art_g_first_out(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    yu(A, lerp(540, 1100, ease_out(u / (1.6 * P))), GROUND, 190, dir=1, ph=t * 2, arm=-8, t=t)
    xuanzong(A, 400, GROUND, 210, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('以妒悍忤旨 送归杨家 · 当夜召回', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '玄宗不怿 食不下咽 鞭挞左右', t, t - u + P)

def art_g_family(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='feihong')
    ground(A, GROUND)
    for j in range(3):
        yu(A, 240 + j * 300, GROUND, 180, dir=1, arm=60, t=t, layer='ink' if j != 1 else 'mid')
    A.flush(cv)
    paste(cv, text_img('三姊封韩国 虢国 秦国夫人 · 出入宫掖', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '姊妹弟兄皆列土 可怜光彩生门户', t, t - u + P)

def art_g_hair(A, cv, t, u):
    """6-beat set piece: 剪发 — sent home a second time, she cuts a lock of hair: all I have is the emperor's gift but my hair and skin,
    which my parents gave me — and has it carried to him; he calls her back at once."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        yu(A, lerp(540, 1100, clamp(ph / 1.6)), GROUND, 190, dir=1, ph=t * 2, arm=-8, t=t)
        lab, col = '再忤旨意 又被送归', FEIHONG
    elif ph < 4:
        yu(A, 480, GROUND, 200, dir=1, kneel=True, arm=lerp(-8, 120, clamp((ph - 2) / 0.6)), t=t)
        A.d['ink'].line([(560, GROUND - 150), (590, GROUND - 120), (580, GROUND - 90)], fill=255, width=4)
        lab, col = '剪下一缕青丝 托宦官献上', ZHU
    else:
        palace(A, 540, 1300, 320, layer='mid')
        xuanzong(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 100, clamp((ph - 4) / 0.6)))
        lab, col = '玄宗大惊 即命召回', FEIHONG
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '妾罪当死 惟发肤是父母所生', t, t - u + 2 * P)

def art_g_xier(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    yu(A, 360, GROUND, 190, dir=1, arm=60, t=t)
    person(A, 680, GROUND, 230, dir=-1, robe=False, hat='helmet', bow=30, arm=90, layer='ink')
    A.d['ink'].ellipse((640, GROUND - 160, 720, GROUND - 60), fill=255)
    A.flush(cv)
    paste(cv, text_img('安禄山拜贵妃为母 · 出入宫中', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '宫中洗儿之事见资治通鉴 历来存疑', t, t - u + P)

# ================================================================ 第三回 荔枝
def art_g_lizhi(A, cv, t, u):
    """6-beat set piece: 一骑红尘 — she loves fresh lychees; post riders gallop them north across thousands of li so they arrive before the taste turns."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        lychee_branch(A, 540, 1060, 260, 10)
        lab, col = '妃嗜荔枝 · 必欲生致之', FEIHONG
    elif ph < 4.5:
        for j in range(3):
            x = lerp(-100, 1100, ((t * 0.3 + j / 3) % 1))
            rider(A, x, GROUND, 140, dir=1, ph=t * 9 + j, layer='ink')
            A.d['red'].ellipse((x - 70, GROUND - 120, x - 50, GROUND - 100), fill=255)
            for kk in range(6):
                q = (t * 1.5 + kk / 6) % 1
                A.d['dune'].ellipse((x - 120 - 160 * q - 18, GROUND - 30 - 30 * q - 18, x - 120 - 160 * q + 18, GROUND - 30 - 30 * q + 18), fill=int(150 * (1 - q)))
        lab, col = '驿马驰传数千里 · 味未变已至京师', FEIHONG
    else:
        palace(A, 540, 1300, 320, layer='feihong')
        yu(A, 540, GROUND, 210, dir=1, arm=90, t=t)
        A.d['red'].ellipse((600, GROUND - 160, 624, GROUND - 136), fill=255)
        lab, col = '一骑红尘妃子笑 无人知是荔枝来', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '诗为晚唐杜牧所作 荔枝产地有岭南 巴蜀二说', t, t - u + 4.5 * P)

def art_g_guozhong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 540, GROUND, 210, dir=1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('族兄杨国忠拜相 · 专权误国', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('宰相', 56), 860, 1020, t, t - u + P, rot=6)

def art_g_bath(A, cv, t, u):
    pool(A, 540, GROUND, 380, t)
    ground(A, GROUND)
    yu(A, 760, GROUND, 190, dir=-1, arm=-8, t=t)
    A.flush(cv)
    paste(cv, text_img('春寒赐浴华清池 温泉水滑洗凝脂', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '白居易长恨歌之句', t, t - u + P)

def art_g_chong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(8):
        person(A, 120 + j * 120, GROUND, 110, dir=1, robe=True, hat='none', female=True, arm=-8, layer='wash')
    yu(A, 540, GROUND, 230, dir=1, arm=60, t=t, dance=0.2)
    A.flush(cv)
    paste(cv, text_img('后宫佳丽三千人 三千宠爱在一身', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_zaochao(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(5):
        person(A, 140 + j * 90, GROUND, 140, dir=1, robe=True, hat='knot', bow=20, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('从此君王不早朝', SERIF, 48, FEIHONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '玄宗晚年倦政 大权先后归于李林甫 杨国忠', t, t - u + P)

def art_g_yuyang(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 240), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    army(A, lerp(-300, 400, ease_out(u / (5 * P))), GROUND, 7, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('渔阳鼙鼓动地来 · 安禄山以讨杨国忠为名起兵', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第四回 马嵬
def art_g_tongguan(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='潼关', layer='mid', open_=1.0)
    flames(A, 540, 1080, 400, 140 * clamp(u / (2 * P)), t, n=4, seed=756, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('哥舒翰兵败 潼关失守 · 长安震动', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_flee(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    carriage(A, lerp(200, 900, ease_out(u / (3 * P))), GROUND, 120, dir=1, wheel=t * 6, ph=t * 8, layer='feihong')
    for j in range(4):
        rider(A, lerp(200, 900, ease_out(u / (3 * P))) - 200 - j * 120, GROUND, 100, dir=1, ph=t * 6 + j, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('玄宗携贵妃姊妹 · 凌晨出延秋门西逃', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_mawei(A, cv, t, u):
    """8-beat set piece: 马嵬 — the soldiers refuse to march and kill 杨国忠; 陈玄礼 says the root of the trouble remains;
    the emperor yields; 高力士 strangles her in the Buddhist hall of the post station. She is thirty-eight."""
    ph = u / P
    A.d['mid'].rectangle((620, GROUND - 260, 960, GROUND), fill=200)
    A.d['ink'].polygon([(600, GROUND - 260), (980, GROUND - 260), (790, GROUND - 330)], fill=255)
    ground(A, GROUND)
    if ph < 2:
        for j in range(8):
            person(A, 80 + j * 70, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5 + j)), layer='ink')
        person(A, 640, GROUND, 160, dir=-1, robe=True, hat='knot', fall=lerp(0, 88, clamp((ph - 1) / 0.5)), arm=-8, layer='mid')
        lab, col = '六军不发 · 杀杨国忠', ZHU
    elif ph < 4:
        for j in range(6):
            person(A, 80 + j * 70, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
        person(A, 560, GROUND, 180, dir=1, robe=False, hat='helmet', bow=20, arm=90, layer='mid')
        xuanzong(A, 800, GROUND, 200, dir=-1, arm=-8, bow=20, old=0.7)
        lab, col = '陈玄礼请诛贵妃 · 贼本尚在', FEIHONG
    elif ph < 6:
        xuanzong(A, 440, GROUND, 200, dir=1, arm=-8, bow=40, old=0.7)
        yu(A, 680, GROUND, 190, dir=-1, bow=20, arm=-8, t=t)
        lab, col = '玄宗掩面 · 不得已', FEIHONG
    else:
        A.d['wash'].line((790, GROUND - 250, 790, GROUND - 120), fill=255, width=6)
        lab, col = '缢死于佛堂 · 年三十八', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 6.3:
        paste(cv, text_img('一个王朝的过错 落在一个女子身上', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 6.3) / 0.4))
    stamp(cv, seal('马嵬', 56), 860, 1020, t, t - u + 0.4, rot=6)

def art_g_bury(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 180), (x + 220, GROUND)], fill=150)
    A.d['mid'].chord((440, GROUND - 100, 640, GROUND + 100), 180, 360, fill=230)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('以紫褥裹之 · 草草葬于马嵬道侧', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_suzong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 210, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('太子即位于灵武 · 玄宗成了太上皇', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_xiangnang(A, cv, t, u):
    """6-beat set piece: 香囊 — back in 长安 the old emperor secretly has her reburied; the body has decayed, only her scent pouch remains;
    he weeps over it."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        A.d['mid'].chord((440, GROUND - 100, 640, GROUND + 100), 180, 360, fill=230)
        for j in range(2):
            person(A, 300 + j * 480, GROUND, 150, dir=1 if j == 0 else -1, robe=False, hat='knot', bow=50, arm=150, layer='ink')
        lab = '玄宗回銮 · 密令改葬'
    elif ph < 4:
        A.d['feihong'].ellipse((500, GROUND - 160, 580, GROUND - 60), fill=255)
        A.d['qiuhuang'].line((540, GROUND - 160, 540, GROUND - 200), fill=255, width=4)
        lab = '肌肤已坏 · 香囊犹在'
    else:
        xuanzong(A, 540, GROUND, 230, dir=1, bow=30, arm=90, old=0.9)
        A.d['feihong'].ellipse((600, GROUND - 160, 640, GROUND - 110), fill=255)
        lab = '上皇视之 凄惋流涕'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if 2 <= ph < 4 else FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见旧唐书杨贵妃传', t, t - u + 2 * P)

# ================================================================ 第五回 长恨
def art_g_xzdeath(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    xuanzong(A, 540, GROUND, 210, dir=1, bow=30, arm=-8, old=1.0)
    A.flush(cv)
    paste(cv, text_img('玄宗晚年幽居西内 · 七十八岁卒', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_changhen(A, cv, t, u):
    ground(A, GROUND)
    for k in range(2):
        x = 400 + k * 280
        A.d['huyang'].line((x, GROUND, x + 10, GROUND - 300), fill=255, width=12)
        A.d['grass'].ellipse((x - 120, GROUND - 440, x + 140, GROUND - 260), fill=200)
    for k in range(2):
        q = (t * 0.2 + k * 0.1) % 1
        A.d['nichang'].polygon([(lerp(200, 900, q) + k * 40, 900), (lerp(200, 900, q) + k * 40 + 30, 890), (lerp(200, 900, q) + k * 40 + 10, 910)], fill=255)
    A.flush(cv)
    paste(cv, text_img('在天愿作比翼鸟 在地愿为连理枝', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '白居易长恨歌 作于其身后五十年', t, t - u + P)

def art_g_mianmian(A, cv, t, u):
    ground(A, GROUND)
    lychee_branch(A, 540, 1100, 280, 10, fall=clamp(u / (3 * P)))
    A.flush(cv)
    paste(cv, text_img('天长地久有时尽 此恨绵绵无绝期', SERIF, 44, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_g_huoshui(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('红颜祸水', SERIF, 64, DIM, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 0.6 * P) / 0.4))
    paste(cv, text_img('后世史书多以此责之', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_g_japan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    Jz.tangship(A, lerp(200, 700, ease_out(u / (3 * P))), 1220, 110, t)
    A.flush(cv)
    paste(cv, text_img('民间传说她未死 · 东渡日本', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '纯属传说 日本山口县有所谓杨贵妃之墓', t, t - u + 0.4)

def art_g_xiuhua(A, cv, t, u):
    ground(A, GROUND)
    for k in range(5):
        x = 640 + k * 70
        A.d['grass'].line((x, GROUND, x, GROUND - 160 - 20 * (k % 2)), fill=255, width=4)
        A.d['pink'].ellipse((x - 26, GROUND - 200 - 20 * (k % 2), x + 26, GROUND - 150 - 20 * (k % 2)), fill=255)
    yu(A, 420, GROUND, 220, dir=1, arm=lerp(-8, 100, ease_out(u / 0.8)), t=t)
    A.flush(cv)
    paste(cv, text_img('位列四大美女 · 羞花之说出自民间', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_g_huaqing(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 320), (x + 220, GROUND)], fill=140)
    pool(A, 540, GROUND, 360, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('华清池 · 今在西安骊山脚下', SERIF, 46, FEIHONG, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_g_legacy(A, cv, t, u):
    lychee_branch(A, 860, 1380, 80, 10)

def art_g_title(A, cv, t, u):
    lychee_branch(A, 820, 1300, 140, 10)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    yu(A, 380, 1460, 640, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))), t=t, dance=0.3)

# ================================================================ script
CHAPTERS = {16: ('第一回', '寿王妃'), 48: ('第二回', '贵妃'), 80: ('第三回', '荔枝'),
            112: ('第四回', '马嵬'), 144: ('第五回', '长恨')}

CARDS = [
    C(0, 2, 'war', 'num', num='一骑红尘', line='只为一颗荔枝', art=art_g_hook_horse),
    C(2, 4, 'empire', 'num', num='三千宠爱', line='在一身', art=art_g_hook_three),
    C(4, 6, 'death', 'num', num='一条白绫', line='结束在三十八岁', art=art_g_hook_silk),
    C(6, 8, 'works', 'num', num='一首长恨歌', line='唱了一千多年', art=art_g_hook_scroll),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 寿王妃
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=719, main='杨家有女', sub='父杨玄琰', art=art_g_birth),
    C(22, 26, 'death', 'card', year=728, main='幼年丧父', sub='寄养叔家', note='年份约略', art=art_g_orphan),
    C(26, 30, 'works', 'card', year=732, main='善歌舞', sub='通音律', note='年份约略', art=art_g_talent),
    C(30, 34, 'empire', 'card', year=735, main='寿王妃', sub='十七岁', art=art_g_shouwang),
    C(34, 38, 'death', 'card', year=737, main='武惠妃薨', sub='玄宗郁郁', art=art_g_wuhuifei),
    C(38, 44, 'night', 'card', year=740, main='骊山', sub='温泉宫', art=art_g_lishan),
    C(44, 48, 'fate', 'card', year=740, main='女道士', sub='号太真', art=art_g_taizhen),
    # ---- 第二回 贵妃
    C(48, 50, 'empire', 'chapter'),
    C(50, 54, 'empire', 'card', year=745, main='册为贵妃', sub='二十七岁', art=art_g_guifei),
    C(54, 62, 'works', 'nichang', year=745),
    C(62, 66, 'fate', 'card', year=746, main='初次遣归', sub='当夜召回', art=art_g_first_out),
    C(66, 70, 'court', 'card', year=748, main='一门显贵', sub='三位夫人', art=art_g_family),
    C(70, 76, 'night', 'card', year=750, main='剪发', sub='青丝寄情', art=art_g_hair),
    C(76, 80, 'war', 'card', year=751, main='安禄山', sub='拜为养母', art=art_g_xier),
    # ---- 第三回 荔枝
    C(80, 82, 'works', 'chapter'),
    C(82, 88, 'works', 'card', year=752, main='荔枝', sub='一骑红尘', note='年份约略', art=art_g_lizhi),
    C(88, 92, 'court', 'card', year=752, main='杨国忠', sub='拜相', art=art_g_guozhong),
    C(92, 96, 'life', 'card', year=753, main='华清赐浴', sub='温泉水滑', note='年份约略', art=art_g_bath),
    C(96, 100, 'empire', 'card', year=754, main='三千宠爱', sub='在一身', art=art_g_chong),
    C(100, 106, 'fate', 'card', year=754, main='不早朝', sub='春宵苦短', art=art_g_zaochao),
    C(106, 112, 'war', 'card', year=755, main='渔阳鼙鼓', sub='安史之乱', art=art_g_yuyang),
    # ---- 第四回 马嵬
    C(112, 114, 'death', 'chapter'),
    C(114, 118, 'war', 'card', year=756, main='潼关失守', sub='长安震动', art=art_g_tongguan),
    C(118, 122, 'fate', 'card', year=756, main='仓皇西逃', sub='延秋门', art=art_g_flee),
    C(122, 130, 'death', 'card', year=756, main='马嵬驿', sub='六军不发', art=art_g_mawei),
    C(130, 134, 'fate', 'card', year=756, main='草草掩埋', sub='马嵬道侧', art=art_g_bury),
    C(134, 138, 'empire', 'card', year=756, main='肃宗即位', sub='灵武', art=art_g_suzong),
    C(138, 144, 'night', 'card', year=757, main='香囊犹在', sub='密令改葬', art=art_g_xiangnang),
    # ---- 第五回 长恨
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'fate', 'card', year=762, main='玄宗去世', sub='幽居西内', art=art_g_xzdeath),
    C(150, 154, 'works', 'card', year=806, main='长恨歌', sub='白居易', art=art_g_changhen),
    C(154, 158, 'night', 'card', year=806, main='此恨绵绵', sub='无绝期', art=art_g_mianmian),
    C(158, 162, 'court', 'card', year=1060, main='红颜祸水', sub='千年骂名', art=art_g_huoshui),
    C(162, 166, 'fate', 'card', year=1060, main='东渡之说', sub='民间传说', art=art_g_japan),
    C(166, 168, 'life', 'card', year=1060, main='羞花', sub='四大美女', art=art_g_xiuhua),
    C(168, 170, 'end', 'card', year=1060, main='华清池', sub='今在西安', art=art_g_huaqing),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾壹', col=FEIHONG, acc=NICHANG, born=719, died=756, age0=718,
    born_lab='719年', died_lab='756年', years_txt='公元719 — 756',
    hook_q='她被说成红颜祸水 · 一个女子真能亡了盛唐吗？',
    name_line='杨玉环 · 号太真', name='杨贵妃', seal='太真', title_art=art_g_title,
    q1='倾国之色？', q2='替罪之羊？',
    end_art=art_g_legacy, end_big='长恨歌', end_seal='太真',
    end_l1='盛唐的错 她只占了一小份', end_l2='骂名却让她一个人背了千年',
    end_brush='此恨绵绵', end_ask='安史之乱 该怪杨贵妃吗？评论区聊聊', next='韩愈'),
    scenes=dict(chapter=scene_chapter, nichang=scene_nichang))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
