"""千古人物志 · 第捌拾贰集 · 韩愈 (768–824)
Look: 古文赭 + 木棉红, 笔锋 corner borders (a brush tip), 秦岭 snow peaks and the 韩江 behind.
Chapter card: 古文 — on a sheet, plain columns of writing replace the ornate parallel prose one chapter at a time;
in the last chapter a single 文 seal is pressed.
Set pieces: custom 8-beat scene 'languan' (雪拥蓝关), 6-beat 嫂抚孤, 6-beat 师说, 6-beat 谏迎佛骨, 6-beat 祭鳄鱼, 6-beat 镇州宣慰.
Ages are counted in 虚岁 (age0 = born - 1).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_yangguifei as Yg      # engine + helpers (previous episode)
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
from render_sunwu import army, banner
from render_songtaizu import tent

F.RIPPLE = False
GUWEN = (128, 84, 52)               # 古文赭
MIANHONG = (200, 70, 50)            # 木棉红
S.LAYERS.append(('guwen', GUWEN, 0.9, 1.0))
S.LAYERS.append(('mianhong', MIANHONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='韩', life='愈', court='唐', night='道', war='鳄', empire='文', works='师', fate='贬', death='骨', end='文')
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
G.THEMES['empire']['sun'] = (GUWEN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (MIANHONG, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # the 韩江
    _d.line([(40 + i * 30, 1456 + _k * 14 + 5 * math.sin(i * 0.5 + _k)) for i in range(35)], fill=(80, 110, 120, 46 - _k * 10), width=3)
for _x in (110, 970):               # kapok (木棉) at the margins
    _d.line((_x, 1446, _x, 1320), fill=(110, 80, 60, 70), width=6)
    for _j in range(4):
        _d.ellipse((_x - 30 + _j * 16, 1300 + (_j % 2) * 16, _x - 14 + _j * 16, 1316 + (_j % 2) * 16), fill=MIANHONG + (80,))
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (100, 104, 112)}
def draw_background(t, theme):
    """秦岭 to 潮州: snow-capped ridges, the 韩江, kapok at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 194, 190), (164, 160, 152), MTN_COL.get(theme, (124, 112, 100))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """笔锋: a writing brush tip in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=GUWEN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=GUWEN + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        d.line((cx - 24 * sx, cy - 24 * sy, cx + 8 * sx, cy + 8 * sy), fill=(110, 80, 50, 230), width=6)
        d.polygon([(cx + 4 * sx, cy + 12 * sy), (cx + 12 * sx, cy + 4 * sy), (cx + 28 * sx, cy + 28 * sy)], fill=(40, 40, 40, 230))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def han(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """韩愈: Tang official — black 幞头 with stiff tails, a full beard (grey when old), a heavy build."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line((x - dir * 0.06 * h, y - 0.97 * h, x - dir * 0.18 * h, y - 0.95 * h), fill=255, width=max(2, int(0.016 * h)))
        beard = 'wash' if old > 0.4 else layer
        A.d[beard].polygon([(x + dir * 0.0 * h, y - 0.85 * h), (x + dir * 0.1 * h, y - 0.85 * h), (x + dir * 0.06 * h, y - 0.62 * h), (x + dir * 0.0 * h, y - 0.68 * h)], fill=255)
        A.d['guwen'].rectangle((x - 0.09 * h, y - 0.56 * h, x + 0.09 * h, y - 0.52 * h), fill=255)
    return hand

def sheet(A, cx, cy, w, h, plain, ornate):
    A.d['wash'].rectangle((cx - w, cy - h, cx + w, cy + h), fill=255)
    A.d['ink'].rectangle((cx - w, cy - h, cx + w, cy + h), outline=255, width=4)
    cols = 8
    for k in range(cols):
        x = cx + w - (k + 0.6) * 2 * w / cols
        if k < plain:
            A.d['ink'].line((x, cy - 0.85 * h, x, cy + 0.85 * h - 40 * (k % 3)), fill=230, width=5)
        elif k < plain + ornate:
            for j in range(8):
                y = cy - 0.8 * h + j * 0.2 * h
                A.d['qiuhuang'].ellipse((x - 10, y - 10, x + 10, y + 10), outline=255, width=3)

def croc(A, x, y, s, dir=1, t=0.0, layer='ink'):
    A.d[layer].polygon([(x - dir * s, y), (x - dir * 0.3 * s, y - 0.14 * s), (x + dir * 0.6 * s, y - 0.1 * s), (x + dir * s, y - 0.02 * s), (x + dir * 0.6 * s, y + 0.04 * s), (x - dir * 0.3 * s, y + 0.08 * s)], fill=255)
    for k in range(4):
        lx = x - dir * 0.4 * s + dir * k * 0.3 * s
        A.d[layer].line((lx, y + 0.04 * s, lx - dir * 0.06 * s, y + 0.14 * s + 4 * math.sin(t * 6 + k)), fill=255, width=max(3, int(0.03 * s)))
    A.d['wash'].ellipse((x + dir * 0.5 * s - 4, y - 0.1 * s - 4, x + dir * 0.5 * s + 4, y - 0.1 * s + 4), fill=255)

def snow(A, t, amt=1.0, n=60):
    for i in range(n):
        q = (t * 0.25 + i / n) % 1
        x = 60 + (i * 53) % 960 + 20 * math.sin(t + i)
        A.d['wash'].ellipse((x - 4, lerp(600, 1460, q) - 4, x + 4, lerp(600, 1460, q) + 4), fill=int(230 * amt))

# ================================================================ chapter card
CH = {16: (0, 1), 48: (1, 3), 80: (3, 5), 112: (5, 7), 144: (7, 8)}
def art_wen_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (1, 3))
    q = ease_out(u / (1.2 * P))
    n = int(lerp(a, b, clamp((q - 0.2) / 0.6) + 0.001))
    sheet(A, 540, 1060, 300, 200, n, 8 - n)
    if kb == 144 and q > 0.6:
        A.flush(cv)
        stamp(cv, seal('文', 80, ZHU), 760, 1180, t, t - u + 0.7 * 1.2 * P)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_wen_chapter)
    ink_in(cv, text_img(no, SERIF, 56, GUWEN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_shishuo(A, cv, t, u):
    ground(A, GROUND)
    sheet(A, 540, 1100, 300, 200, min(8, int(u / (0.15 * P)) + 1), 0)

def art_h_hook_8000(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x, GROUND - 360), (x + 160, GROUND)], fill=160)
        A.d['wash'].polygon([(x - 50, GROUND - 250), (x, GROUND - 360), (x + 50, GROUND - 250)], fill=255)
    ground(A, GROUND)
    snow(A, t)
    horse(A, lerp(200, 600, ease_out(u / (1.2 * P))), GROUND, 140, dir=1, ph=t * 3, layer='ink')

def art_h_hook_croc(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    river(A, 1190, t, rows=2, amp=4)
    croc(A, lerp(540, 1000, clamp(u / (1.2 * P))), 1240, 200, dir=1, t=t)

def art_h_hook_river(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    river(A, 1190, t, rows=3, amp=4)
    A.flush(cv)
    stamp(cv, seal('韩江', 80, ZHU), 540, 1000, t, t - u + 0.4)

# ================================================================ 第一回 孤儿
def art_h_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x - 60, GROUND - 220), (x + 60, GROUND - 220), (x + 220, GROUND)], fill=150)
    A.d['ocean'].rectangle((60, GROUND - 30, W - 60, GROUND + 40), fill=140)
    A.d['wash'].rectangle((420, GROUND - 190, 660, GROUND - 30), fill=255)
    A.d['ink'].polygon([(400, GROUND - 190), (680, GROUND - 190), (540, GROUND - 250)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('河阳人 · 三岁丧父 由兄嫂抚养', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('河阳', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '自称郡望昌黎 世称韩昌黎', t, t - u + P)

def art_h_sao(A, cv, t, u):
    """6-beat set piece: 嫂抚孤 — his elder brother 韩会 dies in exile at 韶州; the widow 郑氏 carries the coffin north with the boy and her own son;
    韩氏两世 惟此而已."""
    ph = u / P
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 30, GROUND - 320), (x + 30, GROUND - 320), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    if ph < 2:
        A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
        A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
        person(A, 540, 1200, 220, dir=1, fall=-88, arm=-8, layer='ink')
        lab = '兄韩会贬死韶州'
    elif ph < 4:
        x = lerp(900, 200, clamp((ph - 2) / 2))
        A.d['guwen'].rectangle((x - 100, GROUND - 90, x + 100, GROUND - 40), fill=255)
        person(A, x + 140, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, ph=t * 2, arm=-8, layer='ink')
        person(A, x + 240, GROUND, 100, dir=-1, robe=True, hat='none', ph=t * 2, arm=-8, layer='guwen')
        person(A, x + 320, GROUND, 110, dir=-1, robe=True, hat='none', ph=t * 2 + 1, arm=-8, layer='mid')
        lab = '嫂郑氏扶柩北归 · 抚孤成人'
    else:
        person(A, 640, GROUND, 200, dir=-1, robe=True, hat='knot', female=True, arm=90, layer='ink')
        person(A, 420, GROUND, 110, dir=1, robe=True, hat='none', arm=-8, layer='guwen')
        person(A, 300, GROUND, 120, dir=1, robe=True, hat='none', arm=-8, layer='mid')
        lab = '韩氏两世 惟此而已'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 4 else GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '语出祭十二郎文 侄子韩老成与他一同长大', t, t - u + 4 * P)

def art_h_study(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='guwen')
    person(A, 280, GROUND, 140, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='ink')
    lamp(A, 760, GROUND - 74, 30, t, glow=0.9)
    n = min(14, int(clamp(u / (3 * P)) * 14) + 1)
    slips(A, 420, GROUND - 74, n, 70, layer='guwen')
    A.flush(cv)
    paste(cv, text_img('自知读书 · 日记数千百言', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_changan(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    han(A, lerp(-100, 540, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('十九岁入长安应试', SERIF, 48, GUWEN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='guwen')
    ground(A, GROUND)
    han(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out((u - 1.5 * P) / 0.5)))
    A.flush(cv)
    paste(cv, text_img('四试乃中进士 · 时年二十五', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + 1.5 * P, rot=6)

def art_h_shangshu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    han(A, 400, GROUND, 190, dir=1, bow=25, arm=90)
    A.flush(cv)
    for i in range(min(3, int(u / (0.8 * P)) + 1)):
        stamp(cv, seal('不报', 46, INK), 640 + i * 110, 1100 - i * 40, t, t - u + i * 0.8 * P)
    paste(cv, text_img('博学宏词三试不中 · 三上宰相书 皆无回音', SERIF, 42, GUWEN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_h_mufu(A, cv, t, u):
    ground(A, GROUND)
    tent(A, 760, GROUND, 300, 220, layer='mid', open_=1.0)
    han(A, 420, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('入宣武节度使董晋幕府', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 师说
def art_h_boshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    han(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    paste(cv, text_img('授国子监四门博士', SERIF, 48, GUWEN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_shishuo(A, cv, t, u):
    """6-beat set piece: 师说 — scholars of his day were ashamed to call anyone teacher; he writes 师说 for his student 李蟠."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='guwen')
    han(A, 260, GROUND, 170, dir=1, kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 3)))
    person(A, 820, GROUND, 150, dir=-1, robe=True, hat='none', kneel=True, bow=20, arm=90, layer='mid')
    A.flush(cv)
    if ph < 1.5:
        lab, col = '时人耻于从师', GUWEN
    elif ph < 3.5:
        lab, col = '师者 所以传道受业解惑也', ZHU
    else:
        lab, col = '弟子不必不如师 师不必贤于弟子', GUWEN
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '为赠学生李蟠而作', t, t - u + P)

def art_h_yushi(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['dune'].polygon([(x - 220, GROUND), (x, GROUND - 120), (x + 220, GROUND)], fill=200)
    ground(A, GROUND)
    for j in range(5):
        person(A, 140 + j * 90, GROUND, 120, dir=1, robe=False, hat='knot', bow=40, ph=t * 2 + j, arm=-8, layer='mid')
    han(A, 820, GROUND, 190, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('任监察御史 · 关中大旱 饥民满道', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_yangshan(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 30, GROUND - 400), (x + 30, GROUND - 400), (x + 160, GROUND)], fill=150)
    ground(A, GROUND)
    han(A, lerp(900, 300, ease_out(u / (3 * P))), GROUND, 170, dir=-1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('上疏请免赋税 · 贬连州阳山县令', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_minsheng(A, cv, t, u):
    ground(A, GROUND)
    for j in range(3):
        person(A, 560 + j * 130, GROUND, 170, dir=-1, robe=False, hat='knot', female=j == 1, arm=90 if j == 1 else -8, layer='mid')
    A.d['guwen'].ellipse((660, GROUND - 130, 700, GROUND - 100), fill=255)
    han(A, 300, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('阳山百姓生子 多以韩为名', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见新唐书韩愈传', t, t - u + P)

def art_h_jinxue(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 320, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('业精于勤 荒于嬉\n行成于思 毁于随', SERIF, 50, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('进学解', SERIF, 48, GUWEN, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_h_huaixi(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    snow(A, t, amt=0.7, n=40)
    ground(A, GROUND)
    for j in range(5):
        rider(A, lerp(-100, 700, ease_out(u / (3 * P))) - j * 120, GROUND, 110, dir=1, ph=t * 6 + j, layer='ink', spear=True)
    A.flush(cv)
    paste(cv, text_img('随裴度平淮西 · 任行军司马', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '李愬雪夜入蔡州 韩愈奉诏撰平淮西碑', t, t - u + P)

# ================================================================ 第三回 佛骨
def art_h_xingbu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='guwen')
    ground(A, GROUND)
    han(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.3)
    A.flush(cv)
    paste(cv, text_img('以功迁刑部侍郎', SERIF, 48, GUWEN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_fogu(A, cv, t, u):
    """6-beat set piece: 谏迎佛骨 — the emperor brings a finger bone of the Buddha into the palace; crowds give away fortunes;
    韩愈 memorialises: the Buddha brings no blessing; the emperor, enraged, wants him put to death."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='qiuhuang')
    ground(A, GROUND)
    if ph < 2:
        for j in range(10):
            person(A, lerp(-100, 1100, ((t * 0.05 + j / 10) % 1)), GROUND - 6 * (j % 2), 100, dir=1, robe=True, hat='knot', bow=20, arm=90, ph=t * 2 + j, layer='mid')
        A.d['qiuhuang'].rectangle((500, GROUND - 260, 580, GROUND - 200), fill=255)
        lab, col = '宪宗迎佛骨入宫 · 王公士庶奔走施舍', GUWEN
    elif ph < 4:
        han(A, 420, GROUND, 190, dir=1, kneel=True, bow=25, arm=90, old=0.3)
        scroll(A, 600, GROUND - 60, 220, 60, 1.0, layer='wash')
        lab, col = '上表直言 · 事佛求福 乃更得祸', ZHU
    else:
        emperor(A, 700, GROUND, 230, dir=-1, arm=lerp(-8, 150, clamp((ph - 4) / 0.4)))
        han(A, 380, GROUND, 170, dir=1, kneel=True, bow=40, old=0.3)
        lab, col = '帝大怒 · 将加极法', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '论佛骨表 时年五十二', t, t - u + 2 * P)

def art_h_bian(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for j in range(3):
        person(A, 160 + j * 90, GROUND, 160, dir=1, robe=True, hat='knot', kneel=True, bow=30, arm=90, layer='ink')
    emperor(A, 760, GROUND, 210, dir=-1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('裴度等力救 · 贬潮州刺史', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def scene_languan(cv, t, c, k):
    """8-beat custom scene: 雪拥蓝关 — driven out the same day, he crosses the 秦岭 in snow; at 蓝关 his grand-nephew 韩湘 catches up;
    he writes: 一封朝奏九重天 夕贬潮州路八千 ... 云横秦岭家何在 雪拥蓝关马不前."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    for k2 in range(4):
        x = 160 + k2 * 250 - (ph * 30) % 250
        A.d['mid'].polygon([(x - 180, GROUND), (x, GROUND - 440), (x + 180, GROUND)], fill=150)
        A.d['wash'].polygon([(x - 60, GROUND - 290), (x, GROUND - 440), (x + 60, GROUND - 290)], fill=255)
    for k2 in range(3):
        x = ((k2 * 380 + t * 20) % 1300) - 100
        A.d['wash'].ellipse((x - 160, 820 + k2 * 40, x + 160, 880 + k2 * 40), fill=170)
    snow(A, t, amt=0.9)
    ground(A, GROUND)
    A.d['wash'].rectangle((0, GROUND - 20, W, GROUND + 10), fill=230)
    horse(A, 520, GROUND, 150, dir=1, ph=t * 2 if ph < 5 else 0, moving=ph < 5, layer='ink')
    han(A, 515, GROUND - 95, 120, dir=1, arm=-8, old=0.4)
    if ph >= 4:
        person(A, lerp(-100, 320, clamp((ph - 4) / 1.2)), GROUND, 160, dir=1, robe=True, hat='knot', ph=t * 4, arm=-8, layer='guwen')
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '雪拥蓝关', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=82)
    fx.flush(cv)
    lines = ['一封朝奏九重天', '夕贬潮州路八千', '云横秦岭家何在', '雪拥蓝关马不前']
    for i, line in enumerate(lines):
        st = s0 + (0.4 + i * 1.7) * P
        if t >= st:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else GUWEN, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 64, 1, clamp((t - st) / 0.4))
    note_in(cv, '左迁至蓝关示侄孙湘', t, s0 + 4 * P)

def art_h_daughter(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, GROUND), (x - 30, GROUND - 360), (x + 30, GROUND - 360), (x + 160, GROUND)], fill=150)
    A.d['mid'].chord((460, GROUND - 60, 620, GROUND + 60), 180, 360, fill=230)
    ground(A, GROUND)
    han(A, 300, GROUND, 180, dir=1, bow=30, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('十二岁幼女病死途中 · 草葬层峰驿', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_chaozhou(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=140)
    river(A, 1250, t, rows=2, amp=3)
    city_wall(A, 160, 920, 1100, gate_x=540, label='潮州', layer='mid', open_=1.0)
    A.flush(cv)
    paste(cv, text_img('抵潮州 · 路八千里', SERIF, 48, GUWEN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('潮州', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 潮州
def art_h_eyu(A, cv, t, u):
    """6-beat set piece: 祭鳄鱼 — crocodiles in the 恶溪 eat the people's livestock; he sacrifices a sheep and a pig and reads a proclamation:
    in seven days, go south to the sea. That night, the record says, storm and thunder; the crocodiles left."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1160, W - 60, GROUND + 40), fill=150 + int(60 * clamp((ph - 4) / 0.5)))
    river(A, 1170, t, rows=3, amp=4 + 10 * clamp((ph - 4) / 0.5))
    if ph < 2:
        croc(A, 700, 1240, 200, dir=-1, t=t)
        person(A, 300, 1160, 160, dir=1, robe=False, hat='knot', ph=t * 4, arm=150, layer='mid')
        lab, col = '恶溪有鳄 食民畜产', GUWEN
    elif ph < 4:
        A.d['dune'].rectangle((380, 1110, 520, 1160), fill=255)
        han(A, 260, 1160, 190, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)), old=0.5)
        croc(A, 820, 1260, 160, dir=-1, t=t)
        lab, col = '以羊一猪一投溪 · 限其七日南徙于海', GUWEN
    else:
        for i in range(20):
            q = (t * 2 + i / 20) % 1
            A.d['wash'].line((100 + (i * 47) % 900, lerp(640, 1160, q), 90 + (i * 47) % 900, lerp(640, 1160, q) + 30), fill=160, width=2)
        A.d['wash'].polygon([(700, 640), (660, 760), (700, 760), (640, 920), (740, 720), (700, 720), (760, 640)], fill=255 if int(t * 3) % 2 else 0)
        croc(A, lerp(820, 1200, clamp((ph - 4) / 1.5)), 1260, 140, dir=1, t=t)
        lab, col = '是夕暴风震电 · 鳄鱼西徙', ZHU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '新唐书所载 后人多以为附会', t, t - u + 4 * P)

def art_h_school(A, cv, t, u):
    ground(A, GROUND)
    Yg.Jz.temple(A, 540, GROUND - 40, 240, layer='mid')
    for j in range(6):
        person(A, 140 + j * 70 if j < 3 else 760 + (j - 3) * 70, GROUND, 110, dir=1 if j < 3 else -1, robe=True, hat='none', kneel=True, arm=90, layer='mid')
    han(A, 540, GROUND, 160, dir=1, kneel=True, arm=60, old=0.5)
    A.flush(cv)
    paste(cv, text_img('捐俸兴办州学 · 延请赵德为师', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_nubi(A, cv, t, u):
    ground(A, GROUND)
    for j in range(8):
        person(A, lerp(500, 1100, ((t * 0.06 + j / 8) % 1)), GROUND, 120, dir=1, robe=False, hat='knot', ph=t * 4 + j, arm=-8, layer='mid')
    han(A, 300, GROUND, 190, dir=1, arm=lerp(-8, 100, ease_out(u / 0.6)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('调袁州刺史 · 赎出没为奴婢者七百余人', SERIF, 44, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_jiangshan(A, cv, t, u):
    A.d['mid'].polygon([(560, 1200), (780, 960), (1000, 1200)], fill=170)
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=4)
    A.flush(cv)
    paste(cv, text_img('韩江', SERIF, 44, INK, 'Black', bleed=False, spacing=6), 300, 1300, 1, clamp(u / 0.4))
    paste(cv, text_img('韩山', SERIF, 44, INK, 'Black', bleed=False, spacing=6), 780, 1080, 1, clamp((u - 0.5 * P) / 0.4))
    paste(cv, text_img('潮人感念 · 江名韩江 山名韩山', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_h_jijiu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='guwen')
    ground(A, GROUND)
    han(A, 540, GROUND, 210, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.6)
    A.flush(cv)
    paste(cv, text_img('召回长安 · 任国子祭酒', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_zhenzhou(A, cv, t, u):
    """6-beat set piece: 镇州宣慰 — the 镇州 army mutinies under 王廷凑; the court sends 韩愈 alone to pacify them; men fear for him;
    he faces the armed ranks, speaks of loyalty and history, and the rebels yield."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2:
        carriage(A, lerp(-100, 400, clamp(ph / 2)), GROUND, 120, dir=1, wheel=t * 6, ph=t * 8, layer='guwen')
        lab, col = '镇州兵乱 · 韩愈单车前往宣慰', GUWEN
    elif ph < 4:
        for j in range(8):
            person(A, 560 + (j % 4) * 110, GROUND - (j // 4) * 30, 150, dir=-1, robe=False, hat='helmet', sword=60, arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='ink')
        han(A, 300, GROUND, 200, dir=1, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 2)), old=0.6)
        lab, col = '刀枪环列 · 责以大义 晓以祸福', ZHU
    else:
        for j in range(8):
            person(A, 560 + (j % 4) * 110, GROUND - (j // 4) * 30, 150, dir=-1, robe=False, hat='helmet', bow=25, arm=-8, layer='ink')
        han(A, 300, GROUND, 200, dir=1, arm=60, old=0.6)
        lab, col = '王廷凑为之屈服', GUWEN
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '元稹言 韩愈可惜 时人皆为之危', t, t - u + P)

def art_h_libu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    han(A, 540, GROUND, 210, dir=1, arm=60, old=0.7)
    A.flush(cv)
    paste(cv, text_img('转吏部侍郎 · 世称韩吏部', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 文宗
def art_h_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    han(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于长安 · 年五十七', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_wen(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    stamp(cv, seal('文', 100, ZHU), 540, 1140, t, t - u + 0.6)
    paste(cv, text_img('赠礼部尚书 谥曰文 · 世称韩文公', SERIF, 44, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_guwen(A, cv, t, u):
    ground(A, GROUND)
    sheet(A, 540, 1100, 300, 200, int(clamp(u / (3 * P)) * 8), 8 - int(clamp(u / (3 * P)) * 8))
    A.flush(cv)
    paste(cv, text_img('与柳宗元倡导古文 · 反对浮靡骈文', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_h_baidai(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 560, 320, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('文起八代之衰\n道济天下之溺', SERIF, 52, INK, 'Black', bleed=False, spacing=16), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('苏轼潮州韩文公庙碑', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_h_bada(A, cv, t, u):
    ground(A, GROUND)
    names = ['韩愈', '柳宗元', '欧阳修', '苏洵', '苏轼', '苏辙', '王安石', '曾巩']
    A.flush(cv)
    for i in range(min(8, int(u / (0.4 * P)) + 1)):
        stamp(cv, seal(names[i], 44, ZHU if i == 0 else INK), 220 + (i % 4) * 210, 1000 + (i // 4) * 170, t, t - u + i * 0.4 * P)
    paste(cv, text_img('唐宋八大家 · 韩愈居首', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_h_hanjiang(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    river(A, 1210, t, rows=3, amp=4)
    for x in (220, 860):
        A.d['huyang'].line((x, 1200, x, 1000), fill=255, width=10)
        for j in range(5):
            A.d['mianhong'].ellipse((x - 50 + j * 22, 980 + (j % 2) * 20, x - 30 + j * 22, 1000 + (j % 2) * 20), fill=255)
    A.flush(cv)
    paste(cv, text_img('不虚南谪八千里 赢得江山都姓韩', SERIF, 44, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '后人题潮州韩祠之句', t, t - u + P)

def art_h_teacher(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 440, layer='guwen')
    for j in range(4):
        person(A, 640 + j * 90, GROUND, 130, dir=-1, robe=True, hat='none', kneel=True, arm=90, layer='mid')
    han(A, 300, GROUND, 170, dir=1, kneel=True, arm=100, old=0.5)
    A.flush(cv)
    paste(cv, text_img('师者 所以传道受业解惑也', SERIF, 46, GUWEN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_h_legacy(A, cv, t, u):
    sheet(A, 860, 1380, 70, 50, 8, 0)

def art_h_title(A, cv, t, u):
    sheet(A, 820, 1320, 120, 90, 8, 0)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    han(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '孤儿'), 48: ('第二回', '师说'), 80: ('第三回', '佛骨'),
            112: ('第四回', '潮州'), 144: ('第五回', '文宗')}

CARDS = [
    C(0, 2, 'works', 'num', num='一篇师说', line='读了一千二百年', art=art_h_hook_shishuo),
    C(2, 4, 'fate', 'num', num='一封奏章', line='贬到八千里外', art=art_h_hook_8000),
    C(4, 6, 'war', 'num', num='一篇祭文', line='据说赶走了鳄鱼', art=art_h_hook_croc),
    C(6, 8, 'empire', 'num', num='一条大江', line='至今姓韩', art=art_h_hook_river),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 孤儿
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=768, main='生于河阳', sub='三岁而孤', art=art_h_birth),
    C(22, 28, 'death', 'card', year=777, main='嫂抚孤', sub='韩氏两世', art=art_h_sao),
    C(28, 32, 'works', 'card', year=780, main='自知读书', sub='日记千言', note='年份约略', art=art_h_study),
    C(32, 36, 'fate', 'card', year=786, main='入长安', sub='十九岁', art=art_h_changan),
    C(36, 40, 'empire', 'card', year=792, main='进士', sub='第四次', art=art_h_jinshi),
    C(40, 44, 'night', 'card', year=795, main='三上宰相书', sub='皆无回音', art=art_h_shangshu),
    C(44, 48, 'court', 'card', year=796, main='入幕', sub='汴州', art=art_h_mufu),
    # ---- 第二回 师说
    C(48, 50, 'works', 'chapter'),
    C(50, 54, 'court', 'card', year=801, main='四门博士', sub='国子监', art=art_h_boshi),
    C(54, 60, 'works', 'card', year=802, main='师说', sub='传道受业', art=art_h_shishuo),
    C(60, 64, 'life', 'card', year=803, main='关中大旱', sub='监察御史', art=art_h_yushi),
    C(64, 68, 'fate', 'card', year=803, main='贬阳山', sub='论天旱人饥', art=art_h_yangshan),
    C(68, 72, 'life', 'card', year=805, main='有爱在民', sub='阳山', art=art_h_minsheng),
    C(72, 76, 'night', 'card', year=812, main='进学解', sub='业精于勤', art=art_h_jinxue),
    C(76, 80, 'war', 'card', year=817, main='平淮西', sub='行军司马', art=art_h_huaixi),
    # ---- 第三回 佛骨
    C(80, 82, 'death', 'chapter'),
    C(82, 86, 'empire', 'card', year=818, main='刑部侍郎', sub='以功迁', art=art_h_xingbu),
    C(86, 92, 'death', 'card', year=819, main='谏迎佛骨', sub='将加极法', art=art_h_fogu),
    C(92, 96, 'fate', 'card', year=819, main='贬潮州', sub='裴度营救', art=art_h_bian),
    C(96, 104, 'night', 'languan', year=819),
    C(104, 108, 'death', 'card', year=819, main='幼女夭亡', sub='层峰驿', art=art_h_daughter),
    C(108, 112, 'court', 'card', year=819, main='抵潮州', sub='路八千', art=art_h_chaozhou),
    # ---- 第四回 潮州
    C(112, 114, 'war', 'chapter'),
    C(114, 120, 'war', 'card', year=819, main='祭鳄鱼', sub='限期南徙', art=art_h_eyu),
    C(120, 124, 'works', 'card', year=819, main='兴学', sub='延师授徒', art=art_h_school),
    C(124, 128, 'life', 'card', year=820, main='赎放奴婢', sub='袁州', art=art_h_nubi),
    C(128, 132, 'empire', 'card', year=820, main='江山姓韩', sub='韩江韩山', note='得名年代较晚', art=art_h_jiangshan),
    C(132, 136, 'court', 'card', year=821, main='国子祭酒', sub='回京', art=art_h_jijiu),
    C(136, 142, 'war', 'card', year=822, main='镇州宣慰', sub='单车入营', art=art_h_zhenzhou),
    C(142, 144, 'empire', 'card', year=823, main='吏部侍郎', sub='韩吏部', art=art_h_libu),
    # ---- 第五回 文宗
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=824, main='韩愈去世', sub='年五十七', art=art_h_death),
    C(150, 154, 'court', 'card', year=824, main='谥文', sub='韩文公', art=art_h_wen),
    C(154, 158, 'works', 'card', year=824, main='古文运动', sub='与柳宗元', art=art_h_guwen),
    C(158, 162, 'empire', 'card', year=1092, main='文起八代', sub='苏轼之评', art=art_h_baidai),
    C(162, 166, 'night', 'card', year=1092, main='八大家', sub='居首', art=art_h_bada),
    C(166, 168, 'fate', 'card', year=1092, main='韩江', sub='潮州', art=art_h_hanjiang),
    C(168, 170, 'end', 'card', year=1092, main='传道受业', sub='百代之师', art=art_h_teacher),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾贰', col=GUWEN, acc=MIANHONG, born=768, died=824, age0=767,
    born_lab='768年', died_lab='824年', years_txt='公元768 — 824',
    hook_q='他一辈子说话得罪人 · 为什么被尊为百代文宗？',
    name_line='韩愈 · 字退之', name='韩愈', seal='昌黎', title_art=art_h_title,
    q1='文起八代？', q2='不合时宜？',
    end_art=art_h_legacy, end_big='文起八代', end_seal='昌黎',
    end_l1='一封奏章 他被贬八千里', end_l2='却让一条江从此姓韩',
    end_brush='传道受业', end_ask='师说里你会背哪一句？评论区聊聊', next='李商隐'),
    scenes=dict(chapter=scene_chapter, languan=scene_languan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
