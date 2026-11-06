"""千古人物志 · 第柒拾贰集 · 海瑞 (1514–1587)
Look: 青天蓝 + 棺木褐, 笔架 corner borders (a three-peaked brush rest), 琼山 coconut palms and sea at the margins.
Chapter card: 笔架 — a brush rest shaped like 山; one more brush hangs on it each chapter; in the last chapter a clear 青天 rises behind it.
Set pieces: custom 8-beat scene 'zhian' (治安疏 · 备棺上疏), 6-beat 笔架博士, 6-beat 胡公子, 6-beat 狱中闻丧,
6-beat 退田, 6-beat 遗物八两.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_lishizhen as Ls       # engine + helpers (previous episode)
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
from render_zhuxi import book

F.RIPPLE = False
QINGTIAN = (54, 90, 140)            # 青天蓝
GUANMU = (120, 78, 52)              # 棺木褐
S.LAYERS.append(('qingtian', QINGTIAN, 0.9, 1.0))
S.LAYERS.append(('guanmu', GUANMU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='海', life='瑞', court='明', night='疏', war='直', empire='清', works='田', fate='罢', death='棺', end='青')
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
G.THEMES['empire']['sun'] = (QINGTIAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (QINGTIAN, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # 琼州 sea line
    _d.line([(60 + i * 30, 1458 + _k * 14 + 4 * math.sin(i * 0.6 + _k)) for i in range(34)], fill=QINGTIAN + (46 - _k * 10,), width=3)
for _x, _s in ((110, 1), (970, -1)):  # coconut palms at the margins
    _d.line([(_x, 1446), (_x + _s * 10, 1380), (_x + _s * 26, 1310)], fill=(110, 90, 70, 70), width=7)
    for _a in (-2.6, -2.0, -1.3, -0.7):
        _d.line((_x + _s * 26, 1310, _x + _s * 26 + 60 * math.cos(_a), 1310 + 34 * math.sin(_a) + 26), fill=(90, 120, 80, 70), width=5)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (92, 96, 104)}
def draw_background(t, theme):
    """琼山: low hills by the sea, palms at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 192, 196), (152, 164, 178), MTN_COL.get(theme, (96, 116, 140))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.7))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """笔架: a three-peaked brush rest in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINGTIAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINGTIAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.polygon([(cx - 32, cy + 14), (cx - 22, cy - 8), (cx - 12, cy + 4), (cx, cy - 22), (cx + 12, cy + 4), (cx + 22, cy - 8), (cx + 32, cy + 14)], fill=QINGTIAN + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def hai(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """海瑞: Ming official — black 乌纱 with side wings, a thin beard (white when old), a patched plain robe."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.07 * h, y - 1.08 * h, x + 0.07 * h, y - 0.93 * h), fill=255)
        d.rectangle((x - 0.17 * h, y - 1.0 * h, x + 0.17 * h, y - 0.97 * h), fill=255)
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.025 * h, y - 0.84 * h), (x + dir * 0.07 * h, y - 0.84 * h), (x + dir * 0.045 * h, y - 0.66 * h)], fill=255)
        A.d['qingtian'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        A.d['wash'].rectangle((x + 0.02 * h, y - 0.36 * h, x + 0.08 * h, y - 0.3 * h), fill=200)
    return hand

def coffin(A, cx, base, w, layer='guanmu', lid=0.0):
    h = 0.42 * w
    A.d[layer].polygon([(cx - w / 2, base), (cx + w / 2, base), (cx + w / 2 + 0.06 * w, base - h), (cx - w / 2 - 0.02 * w, base - 0.8 * h)], fill=255)
    A.d['ink'].polygon([(cx - w / 2 - 0.04 * w, base - 0.8 * h - 0.06 * w - lid * 60), (cx + w / 2 + 0.08 * w, base - h - 0.06 * w - lid * 60),
                        (cx + w / 2 + 0.08 * w, base - h - lid * 60), (cx - w / 2 - 0.04 * w, base - 0.8 * h - lid * 60)], fill=255)

def brush_rack(A, cx, base, w, n):
    A.d['qingtian'].polygon([(cx - w, base), (cx - 0.66 * w, base - 0.4 * w), (cx - 0.33 * w, base - 0.15 * w), (cx, base - 0.6 * w),
                             (cx + 0.33 * w, base - 0.15 * w), (cx + 0.66 * w, base - 0.4 * w), (cx + w, base)], fill=230)
    A.d['ink'].rectangle((cx - 1.05 * w, base, cx + 1.05 * w, base + 0.06 * w), fill=255)
    for i in range(n):
        x = cx - 0.5 * w + i * 0.33 * w
        A.d['guanmu'].line((x, base - 0.48 * w, x, base + 0.32 * w), fill=255, width=max(4, int(0.04 * w)))
        A.d['ink'].polygon([(x - 0.03 * w, base + 0.32 * w), (x + 0.03 * w, base + 0.32 * w), (x, base + 0.46 * w)], fill=255)

def silver(A, cx, cy, s, layer='qiuhuang'):
    A.d[layer].polygon([(cx - s, cy), (cx - 0.6 * s, cy - 0.5 * s), (cx + 0.6 * s, cy - 0.5 * s), (cx + s, cy), (cx + 0.5 * s, cy + 0.3 * s), (cx - 0.5 * s, cy + 0.3 * s)], fill=255)

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 2), 80: (2, 3), 112: (3, 4), 144: (4, 4)}
def art_rack_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 2))
    q = ease_out(u / (1.2 * P))
    if kb == 144:
        A.d['qingtian'].ellipse((540 - 220 * q, 1000 - 220 * q, 540 + 220 * q, 1000 + 220 * q), fill=int(120 * q))
    brush_rack(A, 540, 1100, 300, b if q > 0.5 else a)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_rack_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINGTIAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_coffin(A, cv, t, u):
    ground(A, GROUND)
    coffin(A, 540, GROUND, 420)

def art_h_hook_meat(A, cv, t, u):
    ground(A, GROUND)
    A.d['ink'].line((540, 900, 540, 1040), fill=255, width=4)
    A.d['red'].ellipse((440, 1040, 640, 1200), fill=220)
    A.d['wash'].ellipse((480, 1080, 560, 1140), fill=200)
    A.flush(cv)
    stamp(cv, seal('二斤', 60, ZHU), 760, 1250, t, t - u + 0.6)

def art_h_hook_silver(A, cv, t, u):
    ground(A, GROUND)
    A.d['guanmu'].rectangle((360, GROUND - 200, 720, GROUND), fill=200)
    for k in range(min(8, int(u / (0.15 * P)) + 1)):
        silver(A, 420 + (k % 4) * 80, GROUND - 230 - (k // 4) * 50, 30)

def art_h_hook_kneel(A, cv, t, u):
    ground(A, GROUND)
    for j, x in enumerate((320, 760)):
        person(A, x, GROUND, 200, dir=1 if j == 0 else -1, robe=True, hat='knot', kneel=True, bow=30, layer='mid')
    hai(A, 540, GROUND, 280, dir=1, arm=-8)

# ================================================================ 第一回 琼山
def art_h_birth(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    A.d['wash'].rectangle((420, 1100, 660, 1240), fill=255)
    A.d['ink'].polygon([(400, 1100), (680, 1100), (540, 1030)], fill=255)
    for x in (260, 820):
        A.d['guanmu'].line([(x, 1240), (x + 10, 1100), (x + 24, 980)], fill=255, width=10)
        for a in (-2.6, -2.0, -1.2, -0.6):
            A.d['grass'].line((x + 24, 980, x + 24 + 110 * math.cos(a), 980 + 60 * math.sin(a) + 50), fill=255, width=8)
    A.flush(cv)
    paste(cv, text_img('广东琼山 · 今海南海口', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('琼山', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_orphan(A, cv, t, u):
    ground(A, GROUND)
    person(A, 460, GROUND, 230, dir=1, robe=True, hat='knot', female=True, bow=20, arm=110, layer='ink')
    person(A, 600, GROUND, 100, dir=-1, robe=True, hat='none', arm=-8, layer='qingtian')
    A.flush(cv)
    paste(cv, text_img('四岁丧父 · 母谢氏守节抚孤', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_mother(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='qingtian')
    person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)), layer='ink')
    person(A, 320, GROUND, 120, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='qingtian')
    A.flush(cv)
    paste(cv, text_img('母亲亲授孝经 大学 中庸', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '母教极严 不许嬉戏', t, t - u + P)

def art_h_jiao(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='qingtian')
    person(A, 280, GROUND, 170, dir=1, robe=True, hat='knot', kneel=True, bow=20, arm=90, layer='ink')
    lamp(A, 780, GROUND - 74, 30, t, glow=0.9)
    A.flush(cv)
    type_in(cv, text_img('作严师教戒 · 以圣贤自期', SERIF, 48, QINGTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    note_in(cv, '少年时所作 年份不详', t, t - u + P)

def art_h_juren(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtian')
    ground(A, GROUND)
    hai(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('中举人 · 时年三十六', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('举人', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '考卷中献平黎策 论安定海南', t, t - u + P)

def art_h_huishi(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    hai(A, 540, GROUND, 170, dir=-1, arm=-8, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('进京会试不第 · 遂不复考', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '终其一生 只是举人出身', t, t - u + P)

def art_h_bijia(A, cv, t, u):
    """6-beat set piece: 笔架博士 — as a county school instructor at 南平 he meets the visiting censor: his two assistants kneel, he only bows:
    the three heads make the shape of a brush rest."""
    ph = u / P
    academy_x = 540
    A.d['wash'].rectangle((140, GROUND - 260, 940, GROUND), fill=230)
    A.d['ink'].polygon([(110, GROUND - 260), (970, GROUND - 260), (880, GROUND - 330), (200, GROUND - 330)], fill=255)
    ground(A, GROUND)
    person(A, 860, GROUND, 210, dir=-1, robe=True, hat='knot', arm=lerp(-8, 70, clamp((ph - 3) / 0.6)), layer='qingtian')
    kneel = ph > 1
    person(A, 360, GROUND, 170, dir=1, robe=True, hat='knot', kneel=kneel, bow=30 if kneel else 0, layer='mid')
    person(A, 620, GROUND, 170, dir=1, robe=True, hat='knot', kneel=kneel, bow=30 if kneel else 0, layer='mid')
    hai(A, 490, GROUND, 200, dir=1, bow=12 if ph > 1 else 0, arm=40)
    A.flush(cv)
    if ph < 1:
        lab = '南平县教谕 · 御史来学宫视察'
    elif ph < 3:
        lab = '两名训导跪地 海瑞只长揖'
    else:
        lab = '台宪到此 当以师长之礼相见'
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 3 else QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4:
        paste(cv, text_img('人称 笔架博士', SERIF, 44, INK, 'Black', bleed=False, spacing=6), W / 2, 1448, 1, clamp((ph - 4) / 0.4))

# ================================================================ 第二回 淳安
def art_h_chunan(A, cv, t, u):
    for k in range(4):
        A.d['grass'].rectangle((120 + k * 220, 1240, 300 + k * 220, GROUND - 20), fill=150 + 30 * (k % 2))
    ground(A, GROUND)
    hai(A, lerp(120, 760, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=60)
    A.d['ink'].line((lerp(120, 760, ease_out(u / (3 * P))) - 200, GROUND - 10, lerp(120, 760, ease_out(u / (3 * P))), GROUND - 10), fill=200, width=3)
    A.flush(cv)
    paste(cv, text_img('知淳安县 · 清丈田亩 均平赋役', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('淳安', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_garden(A, cv, t, u):
    ground(A, GROUND)
    for i in range(12):
        x = 200 + (i % 6) * 110; y = GROUND - 10 - (i // 6) * 40
        A.d['grass'].ellipse((x - 26, y - 22, x + 26, y + 4), fill=230)
    person(A, 820, GROUND, 160, dir=-1, robe=False, hat='knot', bow=40, arm=lerp(100, 140, 0.5 + 0.5 * math.sin(t * 4)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('令老仆种菜自给 · 衣食皆俭', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_meat(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((620, GROUND - 160, 860, GROUND), fill=230)
    A.d['ink'].polygon([(600, GROUND - 160), (880, GROUND - 160), (740, GROUND - 220)], fill=255)
    hai(A, lerp(120, 520, ease_out(u / (2 * P))), GROUND, 180, dir=1, ph=t * 3 if u < 2 * P else None, arm=60)
    A.d['red'].ellipse((lerp(120, 520, ease_out(u / (2 * P))) + 30, GROUND - 120, lerp(120, 520, ease_out(u / (2 * P))) + 70, GROUND - 90), fill=230)
    A.flush(cv)
    type_in(cv, text_img('昨闻海令为母寿 市肉二斤矣', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.6)
    note_in(cv, '总督胡宗宪当作奇闻告人', t, t - u + P)

def art_h_hugong(A, cv, t, u):
    """6-beat set piece: 胡公子 — the governor-general's son beats the post-station clerk; 海瑞 has him bound, seizes his silver,
    and writes to 胡宗宪: you ordered frugality, so this must be an impostor."""
    ph = u / P
    ground(A, GROUND)
    A.d['wash'].rectangle((140, GROUND - 240, 540, GROUND), fill=230)
    A.d['ink'].polygon([(120, GROUND - 240), (560, GROUND - 240), (340, GROUND - 300)], fill=255)
    if ph < 2:
        person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 8)), layer='qiuhuang')
        person(A, 460, GROUND, 150, dir=1, robe=False, hat='knot', kneel=True, bow=40, layer='mid')
        lab = '胡宗宪之子过淳安 · 嫌驿站简陋 倒吊驿吏'
    elif ph < 4:
        person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', arm=-8, layer='qiuhuang')
        A.d['ink'].line((600, GROUND - 120, 680, GROUND - 100), fill=255, width=6)
        hai(A, 860, GROUND, 190, dir=-1, arm=lerp(-8, 100, clamp((ph - 2) / 0.6)))
        for k in range(4):
            silver(A, 300 + k * 60, GROUND - 30, 22)
        lab = '海瑞命人缚之 没收其银数千两'
    else:
        desk(A, 540, GROUND, 400, layer='qingtian')
        hai(A, 300, GROUND, 170, dir=1, kneel=True, arm=100)
        lab = '胡公有令 不得铺张 此必假冒'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 42 if ph < 2 else 46, ZHU if ph >= 4 else QINGTIAN, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('胡宗宪无话可说', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))

def art_h_yan(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='qingtian')
    hai(A, 300, GROUND, 170, dir=1, kneel=True, arm=100)
    for j in range(5):
        horse(A, lerp(1100, 700, ((t * 0.1 + j / 5) % 1)) + 300, GROUND, 70, dir=1, ph=t * 6 + j, layer='mid')
    A.flush(cv)
    paste(cv, text_img('都御史鄢懋卿巡察 · 海瑞致书言县小不能容', SERIF, 40, QINGTIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '鄢懋卿绕道而行 却记恨在心', t, t - u + P)

def art_h_xingguo(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='兴国', layer='mid', open_=1.0)
    ground(A, GROUND)
    hai(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('升迁受阻 · 改调兴国知县', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_hubu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    hai(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('调任户部云南司主事', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('户部', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第三回 治安疏
def art_h_jiajing(A, cv, t, u):
    for k in range(6):
        q = (t * 0.3 + k / 6) % 1
        A.d['wash'].ellipse((540 - 40 - 60 * q, 1060 - 260 * q - 30, 540 + 40 + 60 * q, 1060 - 260 * q + 30), fill=int(200 * (1 - q)))
    A.d['qiuhuang'].polygon([(480, GROUND), (600, GROUND), (580, 1100), (500, 1100)], fill=255)
    emperor(A, 760, GROUND, 200, dir=-1, kneel=True)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('嘉靖帝深居西苑修道 · 多年不视朝', SERIF, 44, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_zhian(cv, t, c, k):
    """8-beat custom scene: 治安疏 — he buys a coffin, says farewell to his family and sends his servants away;
    submits the memorial (天下人不直陛下久矣); the emperor throws it down, then picks it up and reads it again and again."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    ground(A, GROUND)
    if ph < 2.5:
        coffin(A, 700, GROUND, 340)
        hai(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 70, clamp(ph / 0.6)))
        for j in range(2):
            person(A, lerp(380, -100, clamp((ph - 1) / 1.5)) - j * 90, GROUND, 140, dir=-1, robe=False, hat='knot', ph=t * 4 + j, arm=-8, layer='mid')
        lab = '先买一口棺材 · 遣散僮仆 诀别妻子'
        col = QINGTIAN
    elif ph < 5:
        palace(A, 540, 1300, 320, layer='mid')
        hai(A, 380, GROUND, 180, dir=1, kneel=True, bow=30, arm=90)
        scroll(A, 560, GROUND - 60, 200, 60, 1.0, layer='wash')
        lab = '天下人不直陛下久矣'
        col = ZHU
    else:
        emperor(A, 700, GROUND, 220, dir=-1)
        q = clamp((ph - 5) / 1)
        sx = lerp(620, 400, q) if ph < 6.5 else lerp(400, 620, clamp((ph - 6.5) / 0.6))
        sy = lerp(GROUND - 160, GROUND - 6, q) if ph < 6.5 else lerp(GROUND - 6, GROUND - 160, clamp((ph - 6.5) / 0.6))
        A.d['wash'].rectangle((sx - 60, sy - 16, sx + 60, sy + 6), fill=255)
        lab = '掷之于地' if ph < 6.5 else '复取读之 日再三'
        col = ZHU if ph < 6.5 else QINGTIAN
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '备棺上疏', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=72)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    if 2.5 <= ph < 5:
        note_in(cv, '嘉靖者 言家家皆净而无财用也', t, s0 + 3 * P)
    elif ph >= 5:
        note_in(cv, '宦官黄锦言 此人已备棺待死 不会逃走', t, s0 + 5 * P)

def art_h_prison(A, cv, t, u):
    ground(A, GROUND)
    for k in range(9):
        A.d['ink'].line((260 + k * 70, 900, 260 + k * 70, GROUND), fill=255, width=10)
    A.d['ink'].rectangle((240, 880, 840, 900), fill=255)
    hai(A, 540, GROUND, 170, dir=1, kneel=True, bow=10, arm=-8)
    A.flush(cv)
    paste(cv, text_img('下诏狱 · 刑部议以死罪', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '嘉靖帝迟迟未批', t, t - u + P)

def art_h_mourn(A, cv, t, u):
    """6-beat set piece: 狱中闻丧 — the jailer brings wine and food; he eats calmly, thinking it his last meal;
    told the emperor is dead, he weeps until he vomits, all night."""
    ph = u / P
    ground(A, GROUND)
    for k in range(9):
        A.d['ink'].line((260 + k * 70, 900, 260 + k * 70, GROUND), fill=120, width=8)
    A.d['ink'].rectangle((240, 880, 840, 900), fill=120)
    desk(A, 540, GROUND, 300, layer='guanmu')
    A.d['qiuhuang'].ellipse((500, GROUND - 100, 540, GROUND - 74), fill=255)
    person(A, 820, GROUND, 180, dir=-1, robe=False, hat='knot', arm=lerp(-8, 80, clamp(ph / 0.6)), layer='mid')
    hai(A, 360, GROUND, 170, dir=1, kneel=True, bow=10 if ph < 3 else lerp(10, 60, 0.5 + 0.5 * math.sin(t * 5)), arm=90 if ph < 3 else -8)
    A.flush(cv)
    if ph < 1.5:
        lab, col = '狱吏忽置酒菜', QINGTIAN
    elif ph < 3:
        lab, col = '以为当赴西市 恣饮啖不顾', QINGTIAN
    else:
        lab, col = '闻帝已崩 大哭 尽呕出所饮食', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4:
        paste(cv, text_img('骂他的人 也是哭他的人', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.3) / 0.4))

def art_h_release(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtian')
    ground(A, GROUND)
    hai(A, lerp(200, 540, ease_out(u / (2 * P))), GROUND, 190, dir=1, ph=t * 3 if u < 2 * P else None, arm=-8)
    A.flush(cv)
    paste(cv, text_img('隆庆帝即位 · 获释复职', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_fame(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        person(A, 140 + j * 115, GROUND, 110 + 20 * (j % 2), dir=1 if j < 4 else -1, robe=True, hat='knot', arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 2 + j)), layer='mid' if j % 2 else 'ink')
    A.flush(cv)
    paste(cv, text_img('海瑞之名 震动天下', SERIF, 48, QINGTIAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('海青天', 50), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 应天
def art_h_yingtian(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 280
        A.d['wash'].rectangle((x - 100, GROUND - 200, x + 100, GROUND), fill=230)
        A.d['red' if u < 2 * P else 'ink'].rectangle((x - 30, GROUND - 120, x + 30, GROUND), fill=255)
    A.flush(cv)
    paste(cv, text_img('巡抚应天十府 · 官吏闻风辞职', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '豪强连夜将朱门漆黑 以避其锋', t, t - u + P)

def art_h_tuitian(A, cv, t, u):
    """6-beat set piece: 退田 — the former 首辅 徐阶 once saved his life; now 海瑞 makes the 徐 family return the land it seized from the people."""
    ph = u / P
    ground(A, GROUND)
    for k in range(5):
        A.d['grass'].rectangle((120 + k * 170, 1240, 270 + k * 170, GROUND - 20), fill=140 + 20 * (k % 2))
    A.d['wash'].rectangle((660, GROUND - 260, 960, GROUND), fill=230)
    A.d['ink'].polygon([(640, GROUND - 260), (980, GROUND - 260), (810, GROUND - 320)], fill=255)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', bow=10 if ph < 2 else 30, arm=-8, layer='qiuhuang', )
    hai(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 110, clamp((ph - 1) / 0.6)), old=0.4)
    n = int(clamp((ph - 3) / 2) * 6)
    for j in range(n):
        person(A, 120 + j * 70, GROUND, 90, dir=1, robe=False, hat='knot', arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3 + j)), layer='mid')
    A.flush(cv)
    if ph < 1:
        lab, col = '徐阶 曾在狱中救过他', QINGTIAN
    elif ph < 3:
        lab, col = '徐家占田数万亩 · 令其退还', ZHU
    else:
        lab, col = '恩归恩 法归法', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '徐家田亩之数 史载不一', t, t - u + 2 * P)

def art_h_wusong(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=5)
    for j in range(6):
        person(A, 120 + j * 160, 1200, 100, dir=1 if j % 2 else -1, robe=False, hat='knot', load=True, ph=t * 4 + j, arm=lerp(120, 160, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('疏浚吴淞江 · 以工代赈 饥民得食', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_dismiss(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    hai(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('遭给事中弹劾 · 罢官归乡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此后家居十六年', t, t - u + P)

def art_h_idle(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    waves(A, 1250, t, rows=2, amp=3)
    A.d['wash'].rectangle((620, 1100, 860, 1240), fill=255)
    A.d['ink'].polygon([(600, 1100), (880, 1100), (740, 1040)], fill=255)
    hai(A, 300, 1240, 170, dir=1, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('张居正当国 · 始终未起用海瑞', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '史称张居正惮其峭直', t, t - u + P)

def art_h_recall(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qingtian')
    ground(A, GROUND)
    hai(A, 540, GROUND, 190, dir=1, arm=-8, old=0.9)
    A.flush(cv)
    paste(cv, text_img('七十二岁再获起用 · 任南京吏部右侍郎', SERIF, 42, QINGTIAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('南京', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_harsh(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='qingtian')
    hai(A, 300, GROUND, 170, dir=1, kneel=True, arm=100, old=0.9)
    scroll(A, 560, GROUND - 160, 280, 100, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('上疏请复太祖重典 · 剥皮实草', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '此议遭朝野非议 斥为迂执', t, t - u + P)

# ================================================================ 第五回 青天
def art_h_legacy8(A, cv, t, u):
    """6-beat set piece: 遗物 — he dies in office at 南京; a colleague opens his bamboo trunk: eight taels of salary silver,
    one bolt of coarse cloth, a few old robes. Colleagues pool money for the funeral."""
    ph = u / P
    ground(A, GROUND)
    if ph < 1.5:
        A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
        A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
        hai(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
        lamp(A, 860, GROUND, 60, t, glow=clamp(1 - ph / 1.2))
        lab, col = '卒于南京任上 · 年七十四', QINGTIAN
    else:
        A.d['bamboo'].rectangle((340, GROUND - 180, 740, GROUND), fill=230)
        for k in range(6):
            A.d['ink'].line((340, GROUND - 180 + k * 30, 740, GROUND - 180 + k * 30), fill=120, width=2)
        n = min(8, int(clamp((ph - 1.5) / 1.5) * 8) + 1)
        for k in range(n):
            silver(A, 400 + (k % 4) * 90, GROUND - 210 - (k // 4) * 40, 26)
        if ph > 3:
            A.d['wash'].rectangle((760, GROUND - 60, 900, GROUND), fill=230)
        person(A, 180, GROUND, 180, dir=1, robe=True, hat='knot', arm=lerp(-8, 80, clamp((ph - 1.5) / 0.6)), layer='ink')
        lab, col = ('竹笼中 · 俸银八两' if ph < 3 else '葛布一端 旧衣数件而已'), ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 4.5:
        paste(cv, text_img('同僚凑钱 才为他收殓', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 1448, 1, clamp((ph - 4.5) / 0.4))
    note_in(cv, '见明史海瑞传', t, t - u + 2 * P)

def art_h_white(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, 1280), fill=150)
    river(A, 1210, t, rows=2, amp=3)
    boat(A, lerp(-100, 1100, (t * 0.04) % 1), 1220, 70, t, sail=False)
    for j in range(14):
        person(A, 60 + j * 72, GROUND, 80 + 10 * (j % 3), dir=1, robe=True, hat='knot', bow=20, arm=-8, layer='wash' if j % 2 else 'mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('南京百姓罢市 · 白衣冠送者夹岸百里', SERIF, 44, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_shi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('忠介', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('赠太子太保 · 谥忠介', SERIF, 46, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_opera(A, cv, t, u):
    ground(A, GROUND)
    A.d['red'].rectangle((200, 960, 880, 1000), fill=200)
    A.d['ink'].rectangle((200, 1000, 220, GROUND), fill=255); A.d['ink'].rectangle((860, 1000, 880, GROUND), fill=255)
    A.d['guanmu'].rectangle((200, GROUND - 60, 880, GROUND), fill=230)
    hai(A, 540, GROUND - 60, 200, dir=1, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('小说戏曲传颂 · 海青天之名遍及民间', SERIF, 44, QINGTIAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '如海刚峰先生居官公案', t, t - u + P)

def art_h_odd(A, cv, t, u):
    ground(A, GROUND)
    for j in range(6):
        person(A, 120 + j * 90 if j < 3 else 700 + (j - 3) * 90, GROUND, 150, dir=1, robe=True, hat='knot', bow=25, arm=-8, layer='mid')
    hai(A, 540, GROUND, 200, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('同僚说他迂 百姓说他清', SERIF, 48, QINGTIAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_tomb(A, cv, t, u):
    for x in (260, 820):
        A.d['guanmu'].line([(x, GROUND), (x + 10, GROUND - 180), (x + 24, GROUND - 320)], fill=255, width=10)
        for a in (-2.6, -2.0, -1.2, -0.6):
            A.d['grass'].line((x + 24, GROUND - 320, x + 24 + 110 * math.cos(a), GROUND - 320 + 60 * math.sin(a) + 50), fill=255, width=8)
    A.d['mid'].chord((420, GROUND - 160, 660, GROUND + 160), 180, 360, fill=230)
    A.d['ink'].rectangle((520, GROUND - 200, 560, GROUND - 60), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('海瑞墓今在海口', SERIF, 48, QINGTIAN, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))

def art_h_legacy(A, cv, t, u):
    brush_rack(A, 860, 1380, 60, 3)

def art_h_title(A, cv, t, u):
    brush_rack(A, 820, 1360, 120, 3)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    hai(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '琼山'), 48: ('第二回', '淳安'), 80: ('第三回', '治安疏'),
            112: ('第四回', '应天'), 144: ('第五回', '青天')}

CARDS = [
    C(0, 2, 'death', 'num', num='一口棺材', line='上疏骂皇帝', art=art_h_hook_coffin),
    C(2, 4, 'life', 'num', num='二斤猪肉', line='惊动了总督', art=art_h_hook_meat),
    C(4, 6, 'fate', 'num', num='八两俸银', line='一生全部家当', art=art_h_hook_silver),
    C(6, 8, 'court', 'num', num='两人下跪', line='他一人站着', art=art_h_hook_kneel),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 琼山
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=1514, main='生于琼山', sub='海南', art=art_h_birth),
    C(22, 26, 'death', 'card', year=1517, main='幼年丧父', sub='四岁', art=art_h_orphan),
    C(26, 30, 'works', 'card', year=1520, main='严母督学', sub='谢氏', note='据其自述 年份约略', art=art_h_mother),
    C(30, 34, 'night', 'card', year=1530, main='严师教戒', sub='以圣贤自期', art=art_h_jiao),
    C(34, 38, 'empire', 'card', year=1549, main='中举人', sub='三十六岁', art=art_h_juren),
    C(38, 42, 'fate', 'card', year=1550, main='会试不第', sub='不复再考', art=art_h_huishi),
    C(42, 48, 'court', 'card', year=1554, main='笔架博士', sub='南平教谕', art=art_h_bijia),
    # ---- 第二回 淳安
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'works', 'card', year=1558, main='知淳安县', sub='清丈田亩', art=art_h_chunan),
    C(54, 58, 'life', 'card', year=1558, main='种菜自给', sub='青菜知县', art=art_h_garden),
    C(58, 62, 'empire', 'card', year=1560, main='二斤肉', sub='母亲寿辰', art=art_h_meat),
    C(62, 68, 'war', 'card', year=1560, main='胡公子', sub='倒吊驿吏', art=art_h_hugong),
    C(68, 72, 'court', 'card', year=1560, main='拒迎巡按', sub='鄢懋卿', art=art_h_yan),
    C(72, 76, 'fate', 'card', year=1562, main='改调兴国', sub='升迁受阻', art=art_h_xingguo),
    C(76, 80, 'court', 'card', year=1564, main='户部主事', sub='进京', art=art_h_hubu),
    # ---- 第三回 治安疏
    C(80, 82, 'night', 'chapter'),
    C(82, 86, 'night', 'card', year=1566, main='嘉靖修道', sub='不视朝政', art=art_h_jiajing),
    C(86, 94, 'death', 'zhian', year=1566),
    C(94, 98, 'death', 'card', year=1566, main='下诏狱', sub='论死', art=art_h_prison),
    C(98, 104, 'fate', 'card', year=1567, main='狱中闻丧', sub='大哭呕血', art=art_h_mourn),
    C(104, 108, 'empire', 'card', year=1567, main='获释复职', sub='隆庆即位', art=art_h_release),
    C(108, 112, 'life', 'card', year=1567, main='名震天下', sub='海青天', art=art_h_fame),
    # ---- 第四回 应天
    C(112, 114, 'empire', 'chapter'),
    C(114, 118, 'empire', 'card', year=1569, main='巡抚应天', sub='十府', art=art_h_yingtian),
    C(118, 124, 'war', 'card', year=1569, main='徐家退田', sub='恩归恩', art=art_h_tuitian),
    C(124, 128, 'works', 'card', year=1570, main='疏浚吴淞', sub='以工代赈', art=art_h_wusong),
    C(128, 132, 'fate', 'card', year=1570, main='被劾罢官', sub='归乡', art=art_h_dismiss),
    C(132, 136, 'night', 'card', year=1572, main='闲居十六年', sub='不被起用', art=art_h_idle),
    C(136, 140, 'court', 'card', year=1585, main='再获起用', sub='七十二岁', art=art_h_recall),
    C(140, 144, 'war', 'card', year=1586, main='请复重典', sub='剥皮实草', art=art_h_harsh),
    # ---- 第五回 青天
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'death', 'card', year=1587, main='海瑞去世', sub='遗物', art=art_h_legacy8),
    C(152, 156, 'life', 'card', year=1587, main='白衣送行', sub='夹岸百里', art=art_h_white),
    C(156, 160, 'court', 'card', year=1587, main='谥号忠介', sub='太子太保', art=art_h_shi),
    C(160, 164, 'works', 'card', year=1606, main='海公案', sub='戏曲小说', art=art_h_opera),
    C(164, 168, 'fate', 'card', year=1606, main='官场异类', sub='不合时宜', art=art_h_odd),
    C(168, 170, 'end', 'card', year=1606, main='海瑞墓', sub='海口', art=art_h_tomb),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='柒拾贰', col=QINGTIAN, acc=GUANMU, born=1514, died=1587, age0=1513,
    born_lab='1514年', died_lab='1587年', years_txt='公元1514 — 1587',
    hook_q='他上疏骂过皇帝 · 为什么皇帝没杀他？',
    name_line='海瑞 · 字汝贤', name='海瑞', seal='刚峰', title_art=art_h_title,
    q1='海青天？', q2='官场异类？',
    end_art=art_h_legacy, end_big='海青天', end_seal='刚峰',
    end_l1='他得罪了整个官场', end_l2='百姓却为他白衣送行百里',
    end_brush='直道而行', end_ask='海瑞这样的官 今天能当下去吗？评论区聊聊', next='徐霞客'),
    scenes=dict(chapter=scene_chapter, zhian=scene_zhian))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
