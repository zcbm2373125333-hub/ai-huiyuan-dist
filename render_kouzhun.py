"""千古人物志 · 第捌拾肆集 · 寇准 (961–1023)
Look: 澶渊青 + 黄龙金, 展脚幞头 corner borders (the long-winged Song cap), 华山 peaks and the 黄河 behind.
Chapter card: 华山红日 — from his childhood poem: the red sun climbs a little higher over 华山 each chapter and sets in the last.
Set pieces: custom 8-beat scene 'chanyuan' (澶州渡河 · 黄龙旗), 6-beat 咏华山, 6-beat 引裾, 6-beat 立储, 6-beat 南迁之议,
6-beat 床子弩, 6-beat 澶渊之盟, 6-beat 孤注, 6-beat 溜须, 6-beat 雷州蒸羊.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_lishangyin as Ls2     # engine + helpers (previous episode)
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
from render_songtaizu import tent
from render_lishangyin import candle

F.RIPPLE = False
CHANYUAN = (40, 96, 92)             # 澶渊青
HUANGLONG = (196, 152, 40)          # 黄龙金
S.LAYERS.append(('chanyuan', CHANYUAN, 0.9, 1.0))
S.LAYERS.append(('huanglong', HUANGLONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='寇', life='华', court='宋', night='直', war='澶', empire='相', works='诗', fate='贬', death='雷', end='准')
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
G.THEMES['empire']['sun'] = (HUANGLONG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (ZHU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # the 黄河
    _d.line([(40 + i * 30, 1456 + _k * 14 + 5 * math.sin(i * 0.4 + _k)) for i in range(35)], fill=(170, 140, 90, 50 - _k * 10), width=3)
for _x in (110, 970):               # sharp 华山 crags at the margins
    _d.polygon([(_x - 50, 1446), (_x - 20, 1300), (_x, 1250), (_x + 20, 1300), (_x + 50, 1446)], fill=(110, 110, 110, 50))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (96, 100, 104)}
def draw_background(t, theme):
    """华山 and the 黄河: steep crags, the yellow river at the bottom."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(194, 194, 190), (160, 164, 160), MTN_COL.get(theme, (104, 118, 114))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.85))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """展脚幞头: the long-winged Song official cap in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=CHANYUAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=CHANYUAN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.chord((cx - 12, cy - 16, cx + 12, cy + 8), 180, 360, fill=(40, 40, 40, 230))
        d.line((cx - 34, cy - 2, cx + 34, cy - 2), fill=(40, 40, 40, 230), width=4)
        d.ellipse((cx - 6, cy + 6, cx + 6, cy + 18), fill=HUANGLONG + (230,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def kou(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """寇准: Song minister — 展脚幞头 with long straight wings, a full beard (white when old), a red official robe."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.92 * h), 180, 360, fill=255)
        d.line((x - 0.3 * h, y - 0.97 * h, x + 0.3 * h, y - 0.97 * h), fill=255, width=max(2, int(0.014 * h)))
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.1 * h, y - 0.85 * h), (x + dir * 0.06 * h, y - 0.62 * h), (x + dir * 0.0 * h, y - 0.68 * h)], fill=255)
    if not kw.get('fall'):
        A.d['red'].polygon([(x - 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.1 * h, y - (0.48 if kneel else 0.76) * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=110)
    return hand

def song_emperor(A, x, y, h, dir=-1, **kw):
    hand = emperor(A, x, y, h, dir=dir, **kw)
    if not kw.get('kneel') and not kw.get('fall'):
        A.d['huanglong'].polygon([(x - 0.1 * h, y - 0.76 * h), (x + 0.1 * h, y - 0.76 * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=170)
    return hand

def huashan(A, cx, base, s, layer='mid', fill=170):
    A.d[layer].polygon([(cx - 1.4 * s, base), (cx - 0.7 * s, base - 0.9 * s), (cx - 0.4 * s, base - 0.7 * s), (cx, base - 1.5 * s),
                        (cx + 0.35 * s, base - 0.8 * s), (cx + 0.7 * s, base - 1.1 * s), (cx + 1.4 * s, base)], fill=fill)

def dragon_flag(A, x, base, h, t, raised=1.0):
    top = base - h * raised
    A.d['ink'].line((x, base, x, top), fill=255, width=max(4, int(0.02 * h)))
    sw = 12 * math.sin(t * 3)
    A.d['huanglong'].polygon([(x, top), (x + 0.45 * h, top + 0.05 * h + sw), (x + 0.42 * h, top + 0.3 * h + sw), (x, top + 0.26 * h)], fill=255)
    A.d['red'].line([(x + 0.06 * h, top + 0.14 * h), (x + 0.18 * h, top + 0.1 * h + sw / 2), (x + 0.3 * h, top + 0.16 * h + sw / 2)], fill=255, width=max(3, int(0.015 * h)))

def crossbow(A, x, base, s, fired=0.0):
    A.d['huyang'].rectangle((x - s, base - 0.25 * s, x + s, base - 0.15 * s), fill=255)
    A.d['ink'].line((x - 0.8 * s, base - 0.15 * s, x - 0.8 * s, base), fill=255, width=6)
    A.d['ink'].line((x + 0.8 * s, base - 0.15 * s, x + 0.8 * s, base), fill=255, width=6)
    A.d['ink'].arc((x + 0.2 * s, base - 0.8 * s, x + 0.9 * s, base + 0.4 * s), 270, 90, fill=255, width=6)
    if fired < 1:
        A.d['ink'].line((x - 0.6 * s, base - 0.3 * s, x + 1.1 * s, base - 0.3 * s), fill=255, width=6)

# ================================================================ chapter card
CH = {16: (0.0, 0.25), 48: (0.25, 0.5), 80: (0.5, 0.75), 112: (0.75, 1.0), 144: (1.0, 0.0)}
def art_sun_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.25, 0.5))
    q = ease_out(u / (1.2 * P))
    s = lerp(a, b, q)
    A.d['red'].ellipse((640 - 70, 1160 - 260 * s - 70, 640 + 70, 1160 - 260 * s + 70), fill=230)
    huashan(A, 540, 1200, 220)
    for k in range(2):
        x = 320 + k * 380 + 20 * math.sin(t * 0.4 + k)
        A.d['wash'].ellipse((x - 120, 1120 - 30, x + 120, 1120 + 30), fill=200)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_sun_chapter)
    ink_in(cv, text_img(no, SERIF, 56, CHANYUAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_k_hook_robe(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    song_emperor(A, 660, GROUND, 230, dir=1, arm=-8, ph=t * 2 if u < P else None)
    kou(A, 440, GROUND, 220, dir=1, arm=lerp(40, 100, clamp(u / (0.6 * P))))

def art_k_hook_flag(A, cv, t, u):
    city_wall(A, 160, 920, 1100, gate_x=None, label=None, layer='mid')
    ground(A, GROUND)
    dragon_flag(A, 540, 1100, 360, t, raised=ease_out(u / (1.2 * P)))

def art_k_hook_soup(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='mid')
    A.d['qiuhuang'].ellipse((500, GROUND - 100, 580, GROUND - 74), fill=255)
    kou(A, 340, GROUND, 180, dir=1, kneel=True, arm=-8)
    person(A, 420, GROUND - 40, 140, dir=-1, robe=True, hat='knot', bow=40, arm=150, layer='mid')

def art_k_hook_twice(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i, (s, c) in enumerate([('拜相', INK), ('被贬', ZHU), ('拜相', INK), ('被贬', ZHU)]):
        stamp(cv, seal(s, 56, c), 240 + i * 200, 1100 + 40 * (i % 2), t, t - u + i * 0.3 * P)

# ================================================================ 第一回 华山
def art_k_birth(A, cv, t, u):
    huashan(A, 540, GROUND - 40, 260, fill=150)
    A.d['wash'].rectangle((420, GROUND - 160, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 160), (680, GROUND - 160), (540, GROUND - 220)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('华州下邽人 · 父寇湘', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('华州', 56), 860, 1020, t, t - u + P, rot=6)

def art_k_huashan(A, cv, t, u):
    """6-beat set piece: 咏华山 — at seven, at a feast, asked to write on 华山: only the sky above it, no mountain its equal;
    raise the head and the red sun is near, look back and the white clouds are low."""
    ph = u / P
    A.d['red'].ellipse((660 - 80, 820 - 80, 660 + 80, 820 + 80), fill=230)
    huashan(A, 540, GROUND, 300, fill=170)
    for k in range(3):
        x = 260 + k * 280 + 30 * math.sin(t * 0.4 + k)
        A.d['wash'].ellipse((x - 130, 1240 - 30, x + 130, 1240 + 30), fill=220)
    ground(A, GROUND)
    person(A, 200, GROUND, 120, dir=1, robe=True, hat='none', arm=lerp(-8, 150, clamp(ph / 0.6)), layer='chanyuan')
    A.flush(cv)
    lab = '只有天在上 更无山与齐' if ph < 3 else '举头红日近 回首白云低'
    paste(cv, text_img(lab, SERIF, 48, ZHU if ph >= 3 else CHANYUAN, 'Black', bleed=False, spacing=6), W / 2, 700, 1, 1)
    note_in(cv, '相传七岁所作 咏华山', t, t - u + P)

def art_k_mother(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    person(A, 760, GROUND, 180, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 3)), layer='ink')
    person(A, 320, GROUND, 130, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='chanyuan')
    lamp(A, 540, GROUND - 74, 30, t, glow=0.8)
    A.flush(cv)
    paste(cv, text_img('少年丧父 · 母亲纺织伴读', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '寇母课子之事 多见于后世传说', t, t - u + P)

def art_k_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='chanyuan')
    ground(A, GROUND)
    kou(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('太平兴国五年 · 进士及第', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '年未满二十 人劝其增报年岁 答曰 吾初进取 可欺君邪', t, t - u + P)

def art_k_badong(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=2, amp=3)
    boat(A, 540, 1220, 100, t, sail=False)
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, 1200), (x - 30, 860), (x + 30, 860), (x + 160, 1200)], fill=150)
    A.flush(cv)
    paste(cv, text_img('知巴东县 · 野水无人渡 孤舟尽日横', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_k_zhiyan(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    song_emperor(A, 760, GROUND, 210, dir=-1, arm=-8)
    kou(A, 380, GROUND, 190, dir=1, bow=15, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3)))
    A.flush(cv)
    paste(cv, text_img('屡次上疏言事 · 太宗以为可用', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_shumi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='chanyuan')
    ground(A, GROUND)
    kou(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('拜枢密副使 · 时年三十一', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 引裾
def art_k_yinju(A, cv, t, u):
    """6-beat set piece: 引裾 — reporting in the hall, his words displease the emperor, who rises to leave; 寇准 grabs the imperial robe
    and makes him sit down to hear him out. 太宗: I have 寇准 as 太宗 of Tang had 魏征."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    if ph < 2:
        song_emperor(A, lerp(660, 820, clamp((ph - 1) / 1)), GROUND, 220, dir=1, ph=t * 2 if ph > 1 else None, arm=-8)
        kou(A, 440, GROUND, 210, dir=1, bow=15, arm=90)
        lab, col = '奏事不合 太宗拂袖欲去', CHANYUAN
    elif ph < 4:
        song_emperor(A, lerp(820, 640, clamp((ph - 2) / 1)), GROUND, 220, dir=-1, arm=-8)
        kou(A, 440, GROUND, 210, dir=1, arm=lerp(60, 110, clamp((ph - 2) / 0.4)))
        lab, col = '寇准拉住龙袍 令帝复坐 奏毕乃退', ZHU
    else:
        song_emperor(A, 640, GROUND, 220, dir=-1, arm=lerp(-8, 80, clamp((ph - 4) / 0.6)))
        kou(A, 400, GROUND, 200, dir=1, bow=25, arm=90)
        lab, col = '朕得寇准 犹文皇之得魏征也', CHANYUAN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见宋史寇准传', t, t - u + 4 * P)

def art_k_qingzhou(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    kou(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8)
    person(A, 720, GROUND, 190, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4)), layer='mid')
    A.flush(cv)
    paste(cv, text_img('与同僚争执殿上 · 出知青州', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_canzheng(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='chanyuan')
    ground(A, GROUND)
    kou(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('太宗思之 召还 · 拜参知政事', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_lichu(A, cv, t, u):
    """6-beat set piece: 立储 — 太宗 asks whom to make heir; 寇准: choose a ruler for the realm, not by the counsel of women, eunuchs or favourites;
    the prince of 襄 is named — the future 真宗."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 360, layer='mid')
    song_emperor(A, 760, GROUND, 190, dir=-1, kneel=True, arm=60)
    kou(A, 320, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2)))
    lamp(A, 540, GROUND - 74, 30, t, glow=0.7)
    A.flush(cv)
    if ph < 2:
        lab, col = '太宗问 立储之事', CHANYUAN
    elif ph < 4:
        lab, col = '为天下择君 不可谋及妇人宦官近臣', ZHU
    else:
        lab, col = '遂立襄王为太子 即后来的真宗', CHANYUAN
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_k_dengzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='邓州', layer='mid', open_=1.0)
    ground(A, GROUND)
    kou(A, 540, GROUND, 190, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('又因事罢参知政事 · 出知邓州', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_xiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='huanglong')
    ground(A, GROUND)
    kou(A, 540, GROUND, 220, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.3)
    A.flush(cv)
    paste(cv, text_img('真宗起用 · 拜同中书门下平章事', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('宰相', 56), 860, 1020, t, t - u + P, rot=6)

def art_k_liao(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 200), (x + 150, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(6):
        rider(A, lerp(1100, 300, ease_out(u / (2 * P))) + j * 110, GROUND, 110, dir=-1, ph=t * 6 + j, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('辽萧太后与圣宗 · 率大军南侵', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 澶渊
def art_k_nanqian(A, cv, t, u):
    """6-beat set piece: 南迁之议 — 王钦若 urges flight to 金陵, 陈尧叟 to 成都; 寇准: whoever drew up this plan deserves death —
    Your Majesty must lead the army in person."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    song_emperor(A, 540, GROUND, 210, dir=1, arm=-8)
    if ph < 2:
        for j in range(2):
            person(A, 760 + j * 110, GROUND, 180, dir=-1, robe=True, hat='knot', bow=20, arm=90, layer='mid')
        lab, col = '王钦若请幸金陵 陈尧叟请幸成都', CHANYUAN
    elif ph < 4:
        kou(A, 300, GROUND, 210, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 5)))
        lab, col = '谁为陛下画此策者 罪可斩也', ZHU
    else:
        kou(A, 300, GROUND, 210, dir=1, bow=20, arm=90)
        lab, col = '请御驾亲征', CHANYUAN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def scene_chanyuan(cv, t, c, k):
    """8-beat custom scene: 澶州 — the emperor reaches the south city of 澶州 and wants to stop; 寇准 and 高琼 urge him across the river
    to the north city; the yellow dragon banner rises on the wall and the troops' cheers carry for miles."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    A.d['dune'].rectangle((0, 1120, W, 1200), fill=170)
    river(A, 1130, t, rows=2, amp=4)
    city_wall(A, 560, 1040, 980, gate_x=800, label=None, layer='mid')
    ground(A, GROUND)
    if ph < 2.5:
        carriage(A, 260, GROUND, 120, dir=1, wheel=0, ph=0, moving=False, layer='huanglong')
        kou(A, 440, GROUND, 190, dir=-1, arm=lerp(60, 140, 0.5 + 0.5 * math.sin(t * 3)), old=0.3)
        lab, col = '真宗至澶州南城 · 欲驻足不前', CHANYUAN
    elif ph < 5:
        x = lerp(260, 760, clamp((ph - 2.5) / 2))
        y = lerp(GROUND, 1110, clamp((ph - 2.5) / 2))
        carriage(A, x, y, 110, dir=1, wheel=t * 5, ph=t * 6, layer='huanglong')
        kou(A, x - 160, y, 170, dir=1, ph=t * 3, arm=-8, old=0.3)
        lab, col = '寇准 高琼力请 · 渡河登北城', ZHU
    else:
        dragon_flag(A, 800, 980, 300, t, raised=clamp((ph - 5) / 0.8))
        for j in range(8):
            person(A, 120 + j * 110, GROUND, 120, dir=1, robe=False, hat='helmet', spear=True, arm=lerp(40, 150, 0.5 + 0.5 * math.sin(t * 5 + j)), layer='ink')
        lab, col = '诸军望见黄龙旗 · 欢呼声闻数十里', CHANYUAN
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '澶州渡河', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=84)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    note_in(cv, '寇准在城楼上 饮酒谈笑 以安人心', t, s0 + 5 * P)

def art_k_crossbow(A, cv, t, u):
    """6-beat set piece: 床子弩 — the 辽 vanguard general 萧挞凛 rides up to inspect the walls; a hidden bed-crossbow fires;
    the bolt strikes his head; the 辽 army loses heart."""
    ph = u / P
    city_wall(A, 60, 380, 1060, gate_x=None, label='澶州', layer='mid')
    ground(A, GROUND)
    crossbow(A, 260, 1060, 90, fired=1.0 if ph >= 2 else 0.0)
    if ph < 2:
        rider(A, lerp(1100, 760, clamp(ph / 1.5)), GROUND, 140, dir=-1, ph=t * 5, layer='ink')
        lab, col = '辽先锋萧挞凛 至澶州城下察看', CHANYUAN
    elif ph < 3.5:
        q = clamp((ph - 2) / 0.6)
        A.d['ink'].line((lerp(360, 760, q) - 60, lerp(1030, GROUND - 160, q), lerp(360, 760, q), lerp(1030, GROUND - 160, q)), fill=255, width=6)
        rider(A, 760, GROUND, 140, dir=-1, ph=0, moving=False, layer='ink')
        lab, col = '床子弩伏发', ZHU
    else:
        horse(A, 820, GROUND, 120, dir=1, ph=t * 6, layer='ink')
        person(A, 700, GROUND, 150, dir=-1, robe=False, hat='helmet', fall=80, arm=-8, layer='ink')
        lab, col = '中额而死 · 辽军夺气', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('床子弩', 50), 860, 1020, t, t - u + 2 * P, rot=6)

def art_k_meng(A, cv, t, u):
    """6-beat set piece: 澶渊之盟 — 曹利用 is sent to negotiate; 寇准 calls him aside: go past three hundred thousand and I will behead you;
    he comes back with silver one hundred thousand taels and silk two hundred thousand bolts a year."""
    ph = u / P
    tent(A, 540, GROUND, 400, 280, layer='mid', open_=1.0)
    ground(A, GROUND)
    if ph < 2:
        person(A, 640, GROUND, 190, dir=-1, robe=True, hat='knot', bow=15, arm=-8, layer='mid')
        kou(A, 380, GROUND, 200, dir=1, arm=lerp(60, 150, 0.5 + 0.5 * math.sin(t * 4)), old=0.3)
        lab, col = '曹利用奉命往辽营议和', CHANYUAN
    elif ph < 4:
        kou(A, 380, GROUND, 200, dir=1, arm=150, old=0.3)
        person(A, 620, GROUND, 180, dir=-1, robe=True, hat='knot', bow=30, arm=-8, layer='mid')
        lab, col = '寇准召之曰 过三十万 吾斩汝', ZHU
    else:
        for k in range(6):
            A.d['huanglong'].rectangle((300 + (k % 3) * 160, GROUND - 60 - (k // 3) * 60, 420 + (k % 3) * 160, GROUND - 10 - (k // 3) * 60), fill=255)
        lab, col = '岁币 银十万两 绢二十万匹', CHANYUAN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    stamp(cv, seal('澶渊', 56), 860, 1020, t, t - u + 4 * P, rot=6)

def art_k_peace(A, cv, t, u):
    for k in range(5):
        A.d['grass'].rectangle((120 + k * 170, 1240, 270 + k * 170, GROUND - 20), fill=150 + 20 * (k % 2))
    ground(A, GROUND)
    for j in range(3):
        person(A, lerp(-100, 1100, ((t * 0.04 + j / 3) % 1)), GROUND, 120, dir=1, robe=False, hat='knot', load=True, arm=160, ph=t * 3 + j, layer='ink')
    A.flush(cv)
    paste(cv, text_img('此后宋辽之间 · 百余年无大战', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

# ================================================================ 第四回 孤注
def art_k_guzhu(A, cv, t, u):
    """6-beat set piece: 孤注 — 王钦若 whispers: a treaty under the walls is a shame in the 春秋; 寇准 staked Your Majesty like a gambler's last coin."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    song_emperor(A, 680, GROUND, 210, dir=-1, arm=-8)
    person(A, 440, GROUND, 180, dir=1, robe=True, hat='knot', bow=20, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 3)), layer='mid')
    A.flush(cv)
    if ph < 2:
        lab, col = '王钦若进言 城下之盟 春秋耻之', CHANYUAN
    elif ph < 4:
        lab, col = '寇准以陛下为孤注', ZHU
    else:
        lab, col = '真宗不悦 · 寇准罢相', CHANYUAN
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    if ph >= 2:
        stamp(cv, seal('孤注', 60, ZHU), 860, 1020, t, t - u + 2 * P, rot=6)

def art_k_haoshe(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 500, layer='mid')
    for k in range(5):
        candle(A, 380 + k * 80, GROUND - 74, 60, 0.6, t)
    for k in range(int(clamp(u / (3 * P)) * 12)):
        A.d['red'].ellipse((300 + (k * 37) % 480 - 10, GROUND - 20, 300 + (k * 37) % 480 + 10, GROUND), fill=200)
    kou(A, 200, GROUND, 180, dir=1, kneel=True, arm=90, old=0.4)
    A.flush(cv)
    paste(cv, text_img('生平豪侈 · 夜宴燃烛 烛泪成堆', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见欧阳修归田录', t, t - u + P)

def art_k_zaixiang(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='huanglong')
    ground(A, GROUND)
    kou(A, 540, GROUND, 210, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('天禧三年 · 再度入相', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_liuxu(A, cv, t, u):
    """6-beat set piece: 溜须 — at a banquet soup drips on 寇准's beard; his deputy 丁谓 rises to wipe it off;
    寇准 laughs: a minister of state, wiping his superior's beard? 丁谓 never forgives him."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    A.d['qiuhuang'].ellipse((500, GROUND - 100, 580, GROUND - 74), fill=255)
    kou(A, 330, GROUND, 180, dir=1, kneel=True, arm=lerp(40, 90, clamp((ph - 3) / 0.5)), old=0.6)
    if ph < 3:
        person(A, 430, GROUND - 20, 150, dir=-1, robe=True, hat='knot', bow=40, arm=150, layer='mid')
    else:
        person(A, 760, GROUND, 170, dir=-1, robe=True, hat='knot', kneel=True, bow=30, arm=-8, layer='mid')
    A.flush(cv)
    if ph < 1.5:
        lab, col = '席间羹汤沾须', CHANYUAN
    elif ph < 3:
        lab, col = '参知政事丁谓起身为其拂须', CHANYUAN
    elif ph < 4.5:
        lab, col = '参政 国之大臣 乃为官长拂须邪', ZHU
    else:
        lab, col = '丁谓大惭 由是衔恨', CHANYUAN
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '溜须一词由此而来', t, t - u + 3 * P)

def art_k_bamian(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    kou(A, lerp(400, 120, ease_out((u - P) / P)), GROUND, 180, dir=-1 if u > P else 1, ph=t * 3 if u > P else None, arm=-8, old=0.7)
    A.flush(cv)
    paste(cv, text_img('丁谓等构陷 · 寇准罢相', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_leizhou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    for x in (220, 860):
        A.d['huyang'].line([(x, 1240), (x + 10, 1100), (x + 24, 980)], fill=255, width=10)
        for a in (-2.6, -2.0, -1.2, -0.6):
            A.d['grass'].line((x + 24, 980, x + 24 + 110 * math.cos(a), 980 + 60 * math.sin(a) + 50), fill=255, width=8)
    kou(A, 540, 1240, 170, dir=1, arm=-8, old=0.8)
    A.flush(cv)
    paste(cv, text_img('一贬再贬 · 道州司马 雷州司户参军', SERIF, 44, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('雷州', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第五回 雷州
def art_k_zhengyang(A, cv, t, u):
    """6-beat set piece: 雷州蒸羊 — soon 丁谓 himself is banished to 崖州 and must pass through 雷州; 寇准 sends a steamed lamb to the border
    to greet him, and locks his servants indoors gambling so none can take revenge."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        for j in range(3):
            person(A, lerp(-100, 600, clamp(ph / 2)) - j * 100, GROUND, 150, dir=1, robe=True, hat='knot', ph=t * 3 + j, arm=-8, layer='mid')
        lab, col = '丁谓亦贬崖州 · 途经雷州', CHANYUAN
    elif ph < 4:
        A.d['qiuhuang'].ellipse((480, GROUND - 120, 600, GROUND - 60), fill=255)
        person(A, 380, GROUND, 160, dir=1, robe=False, hat='knot', arm=120, layer='ink')
        person(A, 700, GROUND, 170, dir=-1, robe=True, hat='knot', bow=20, arm=-8, layer='mid')
        lab, col = '寇准遣人 送蒸羊于境上', CHANYUAN
    else:
        A.d['wash'].rectangle((260, GROUND - 260, 820, GROUND), fill=230)
        A.d['ink'].rectangle((500, GROUND - 160, 580, GROUND), fill=255)
        for j in range(4):
            person(A, 320 + j * 60 if j < 2 else 640 + (j - 2) * 60, GROUND, 110, dir=1 if j < 2 else -1, robe=False, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 5 + j)), layer='ink')
        lab, col = '闭门纵家僮博戏 · 不许出门寻仇', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见宋史寇准传', t, t - u + 2 * P)

def art_k_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    kou(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    candle(A, 860, GROUND, 120, 0.95, t, lit=False)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于雷州 · 年六十三', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_bamboo(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 180), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    for k in range(7):
        x = 160 + k * 120
        h = lerp(80, 260, clamp(u / (3 * P)))
        A.d['grass'].line((x, GROUND, x, GROUND - h), fill=255, width=6)
        A.d['wash'].rectangle((x - 10, GROUND - h + 20, x + 10, GROUND - h + 50), fill=255)
    A.flush(cv)
    paste(cv, text_img('灵柩北归 百姓插竹挂纸钱 · 竹竟生笋', SERIF, 44, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '相公竹之说出自民间', t, t - u + P)

def art_k_zhongmin(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('忠愍', 90, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('仁宗朝复其爵位 · 谥忠愍', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_k_laigong(A, cv, t, u):
    ground(A, GROUND)
    kou(A, 540, GROUND, 260, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('封莱国公 · 世称寇莱公', SERIF, 46, CHANYUAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_k_end(A, cv, t, u):
    A.d['red'].ellipse((640 - 70, 860 - 70, 640 + 70, 860 + 70), fill=230)
    huashan(A, 540, GROUND, 300)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('只有天在上 更无山与齐', SERIF, 48, CHANYUAN, 'Black', bleed=False, spacing=6), W / 2, 700, 1, clamp(u / 0.4))

def art_k_legacy(A, cv, t, u):
    huashan(A, 860, 1440, 60)

def art_k_title(A, cv, t, u):
    huashan(A, 820, 1440, 120)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    kou(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '华山'), 48: ('第二回', '引裾'), 80: ('第三回', '澶渊'),
            112: ('第四回', '孤注'), 144: ('第五回', '雷州')}

CARDS = [
    C(0, 2, 'court', 'num', num='一拽龙袍', line='逼皇帝坐下听完', art=art_k_hook_robe),
    C(2, 4, 'war', 'num', num='一面黄龙旗', line='换来百年和平', art=art_k_hook_flag),
    C(4, 6, 'night', 'num', num='一碗羹汤', line='溜须一词的由来', art=art_k_hook_soup),
    C(6, 8, 'fate', 'num', num='两次拜相', line='两次被贬', art=art_k_hook_twice),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 华山
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=961, main='生于华州', sub='渭南', art=art_k_birth),
    C(22, 28, 'works', 'card', year=967, main='咏华山', sub='七岁', art=art_k_huashan),
    C(28, 32, 'night', 'card', year=975, main='孤灯伴读', sub='母亲课子', note='年份约略', art=art_k_mother),
    C(32, 36, 'empire', 'card', year=980, main='进士及第', sub='少年登科', art=art_k_jinshi),
    C(36, 40, 'life', 'card', year=981, main='知巴东', sub='野水孤舟', art=art_k_badong),
    C(40, 44, 'court', 'card', year=988, main='直言', sub='太宗器之', note='年份约略', art=art_k_zhiyan),
    C(44, 48, 'empire', 'card', year=991, main='枢密副使', sub='三十一岁', art=art_k_shumi),
    # ---- 第二回 引裾
    C(48, 50, 'court', 'chapter'),
    C(50, 56, 'court', 'card', year=991, main='引裾', sub='令帝复坐', note='年份约略', art=art_k_yinju),
    C(56, 60, 'fate', 'card', year=993, main='出知青州', sub='殿上争执', art=art_k_qingzhou),
    C(60, 64, 'empire', 'card', year=994, main='参知政事', sub='召还', art=art_k_canzheng),
    C(64, 70, 'night', 'card', year=994, main='立储', sub='为天下择君', art=art_k_lichu),
    C(70, 74, 'fate', 'card', year=996, main='出知邓州', sub='再度罢职', art=art_k_dengzhou),
    C(74, 78, 'empire', 'card', year=1004, main='拜相', sub='四十四岁', art=art_k_xiang),
    C(78, 80, 'war', 'card', year=1004, main='辽军南下', sub='兵临黄河', art=art_k_liao),
    # ---- 第三回 澶渊
    C(80, 82, 'war', 'chapter'),
    C(82, 88, 'death', 'card', year=1004, main='南迁之议', sub='罪可斩也', art=art_k_nanqian),
    C(88, 96, 'war', 'chanyuan', year=1004),
    C(96, 102, 'war', 'card', year=1004, main='床子弩', sub='射杀辽将', art=art_k_crossbow),
    C(102, 108, 'court', 'card', year=1005, main='澶渊之盟', sub='岁币', art=art_k_meng),
    C(108, 112, 'life', 'card', year=1005, main='百年和平', sub='宋辽', art=art_k_peace),
    # ---- 第四回 孤注
    C(112, 114, 'fate', 'chapter'),
    C(114, 120, 'fate', 'card', year=1006, main='孤注', sub='谗言', art=art_k_guzhu),
    C(120, 124, 'night', 'card', year=1006, main='烛泪成堆', sub='生平豪侈', note='年份约略', art=art_k_haoshe),
    C(124, 128, 'empire', 'card', year=1019, main='再度拜相', sub='五十九岁', art=art_k_zaixiang),
    C(128, 134, 'court', 'card', year=1019, main='溜须', sub='丁谓衔恨', art=art_k_liuxu),
    C(134, 138, 'death', 'card', year=1020, main='再次罢相', sub='丁谓构陷', art=art_k_bamian),
    C(138, 144, 'fate', 'card', year=1022, main='贬雷州', sub='司户参军', art=art_k_leizhou),
    # ---- 第五回 雷州
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'works', 'card', year=1022, main='蒸羊', sub='不许寻仇', art=art_k_zhengyang),
    C(152, 156, 'death', 'card', year=1023, main='寇准去世', sub='年六十三', art=art_k_death),
    C(156, 160, 'life', 'card', year=1023, main='相公竹', sub='民间传说', art=art_k_bamboo),
    C(160, 164, 'court', 'card', year=1033, main='谥忠愍', sub='平反', art=art_k_zhongmin),
    C(164, 168, 'empire', 'card', year=1033, main='寇莱公', sub='莱国公', art=art_k_laigong),
    C(168, 170, 'end', 'card', year=1033, main='天在上', sub='华山', art=art_k_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾肆', col=CHANYUAN, acc=HUANGLONG, born=961, died=1023, age0=960,
    born_lab='961年', died_lab='1023年', years_txt='公元961 — 1023',
    hook_q='他逼着皇帝上前线 · 为什么最后却被贬到天涯？',
    name_line='寇准 · 字平仲', name='寇准', seal='莱公', title_art=art_k_title,
    q1='社稷之臣？', q2='刚愎之人？',
    end_art=art_k_legacy, end_big='澶渊', end_seal='莱公',
    end_l1='他把皇帝推上了城头', end_l2='自己却被推到了天涯',
    end_brush='刚直', end_ask='澶渊之盟 是屈辱还是明智？评论区聊聊', next='柳永'),
    scenes=dict(chapter=scene_chapter, chanyuan=scene_chanyuan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
