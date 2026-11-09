"""千古人物志 · 第捌拾伍集 · 柳永 (约984–约1053)
Look: 青楼绛 + 残月黄, 拍板 corner borders (a pair of clapper boards), 汴河 willows and a waning moon behind.
Chapter card: 杨柳岸 晓风残月 — a willow bank under the moon; the moon wanes chapter by chapter to a thin crescent at dawn.
Set pieces: custom 8-beat scene 'yulin' (雨霖铃 · 长亭送别), 6-beat 望海潮, 6-beat 教坊新声, 6-beat 鹤冲天, 6-beat 奉旨填词,
6-beat 八声甘州, 6-beat 煮海歌, 6-beat 吊柳七.
Birth and death years are uncertain, so no ages are shown (no_age); uncertain dates are labelled.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_kouzhun as Kz         # engine + helpers (previous episode)
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
from render_zuozongtang import willow
from render_zhouyu import guqin
from render_yangguifei import yu
from render_lishangyin import candle

F.RIPPLE = False
QINLOU = (146, 78, 82)              # 青楼绛
CANYUE = (214, 196, 136)            # 残月黄
S.LAYERS.append(('qinlou', QINLOU, 0.9, 1.0))
S.LAYERS.append(('canyue', CANYUE, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='柳', life='永', court='宋', night='月', war='海', empire='词', works='曲', fate='落', death='吊', end='柳')
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
G.THEMES['empire']['sun'] = (QINLOU, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (CANYUE, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _k in range(3):                 # the 汴河
    _d.line([(40 + i * 30, 1456 + _k * 14 + 4 * math.sin(i * 0.5 + _k)) for i in range(35)], fill=(90, 110, 120, 46 - _k * 10), width=3)
for _x in (110, 970):               # willows at the margins
    _d.line((_x, 1446, _x, 1330), fill=(110, 90, 70, 70), width=6)
    for _j in range(6):
        _d.line((_x, 1336, _x - 40 + _j * 16, 1420 - 10 * (_j % 2)), fill=(110, 140, 90, 70), width=3)
MTN_COL = {'night': (28, 32, 40), 'death': (60, 60, 62), 'war': (110, 64, 50), 'fate': (100, 96, 104)}
def draw_background(t, theme):
    """汴河: low distant hills, the river, willows at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(196, 192, 192), (166, 160, 162), MTN_COL.get(theme, (126, 114, 116))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.6))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """拍板: a pair of clapper boards tied with a red cord in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=QINLOU + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=QINLOU + (220,), width=3)
        cx, cy = x + sx * 62, y + sy * 62
        for k in (-1, 1):
            d.rounded_rectangle((cx + k * 9 - 6, cy - 28, cx + k * 9 + 6, cy + 28), radius=4, fill=(140, 100, 60, 230))
        d.line((cx - 16, cy - 20, cx + 16, cy - 20), fill=QINLOU + (240,), width=3)
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def liu(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """柳永: a dashing Song scholar — soft 幞头 with long tails, a light moustache, a wine-red robe; grey when old."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.075 * h, y - 1.05 * h, x + 0.075 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line([(x - dir * 0.05 * h, y - 0.97 * h), (x - dir * 0.16 * h, y - 0.92 * h + 0.02 * h * math.sin(x * 0.1)), (x - dir * 0.2 * h, y - 0.8 * h)], fill=255, width=max(2, int(0.014 * h)))
        if old > 0.4:
            A.d['wash'].polygon([(x + dir * 0.02 * h, y - 0.84 * h), (x + dir * 0.08 * h, y - 0.84 * h), (x + dir * 0.05 * h, y - 0.72 * h)], fill=255)
    if not kw.get('fall'):
        A.d['qinlou'].polygon([(x - 0.1 * h, y - (0.48 if kneel else 0.75) * h), (x + 0.1 * h, y - (0.48 if kneel else 0.75) * h), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=150)
    return hand

def moon(A, cx, cy, r, phase):
    """phase 1 = full, 0 = thin crescent."""
    A.d['canyue'].ellipse((cx - r, cy - r, cx + r, cy + r), fill=230)
    off = lerp(2 * r * 0.85, 0, phase) if phase < 1 else 2.5 * r
    if phase < 1:
        A.d['canyue'].ellipse((cx - r + off * 0.0 + (2 * r - off) * 0.0 - r * 0.0 + (1 - phase) * 0.0, cy - r, cx + r, cy + r), fill=230)
        A.d['canyue'].ellipse((cx - r - (1 - phase) * 1.7 * r, cy - r, cx + r - (1 - phase) * 1.7 * r, cy + r), fill=0)

def pavilion(A, cx, base, w, layer='mid'):
    A.d['ink'].rectangle((cx - 0.4 * w, base - 0.6 * w, cx - 0.34 * w, base), fill=255)
    A.d['ink'].rectangle((cx + 0.34 * w, base - 0.6 * w, cx + 0.4 * w, base), fill=255)
    A.d['ink'].polygon([(cx - 0.6 * w, base - 0.58 * w), (cx + 0.6 * w, base - 0.58 * w), (cx, base - 0.9 * w)], fill=255)
    A.d[layer].rectangle((cx - 0.34 * w, base - 0.12 * w, cx + 0.34 * w, base), fill=200)

def singers(A, n, t, x0=600, step=110, h=150):
    for j in range(n):
        yu(A, x0 + j * step, GROUND, h, dir=-1, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 3 + j)), t=t, dance=0.3, layer='ink' if j % 2 else 'mid')

# ================================================================ chapter card
CH = {16: (1.0, 0.8), 48: (0.8, 0.6), 80: (0.6, 0.4), 112: (0.4, 0.2), 144: (0.2, 0.0)}
def art_moon_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.8, 0.6))
    q = ease_out(u / (1.2 * P))
    moon(A, 680, 960, 90, lerp(a, b, q))
    A.d['ocean'].rectangle((240, 1150, 840, 1214), fill=120)
    willow(A, 380, 1200, 300, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_moon_chapter)
    ink_in(cv, text_img(no, SERIF, 56, QINLOU, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_l_hook_city(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    for k in range(7):
        A.d['mid'].rectangle((140 + k * 120, 1080 - 40 * (k % 3), 220 + k * 120, 1200), fill=200)
    for k in range(10):
        A.d['pink'].ellipse((100 + k * 90, 1230 + (k % 2) * 30, 140 + k * 90, 1260 + (k % 2) * 30), fill=230)

def art_l_hook_decree(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 420, 240, ease_out(u / (1.0 * P)), layer='wash')
    A.flush(cv)
    stamp(cv, seal('奉旨', 70, ZHU), 540, 1100, t, t - u + 0.6)

def art_l_hook_well(A, cv, t, u):
    ground(A, GROUND)
    A.d['dune'].rectangle((440, GROUND - 120, 640, GROUND), fill=255)
    A.d['ink'].rectangle((440, GROUND - 120, 640, GROUND), outline=255, width=6)
    A.d['ink'].line((460, GROUND - 120, 540, GROUND - 260), fill=255, width=5)
    A.d['ink'].line((620, GROUND - 120, 540, GROUND - 260), fill=255, width=5)
    for j in range(2):
        yu(A, 300 + j * 480, GROUND, 170, dir=1 if j == 0 else -1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 3 + j)), t=t, dance=0.2, layer='mid')

def art_l_hook_moon(A, cv, t, u):
    moon(A, 680, 900, 100, lerp(0.6, 0.0, clamp(u / (1.2 * P))))
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    willow(A, 340, 1200, 380, t)
    ground(A, GROUND)

# ================================================================ 第一回 崇安
def art_l_birth(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 90, GROUND), (x - 40, GROUND - 400), (x + 40, GROUND - 420), (x + 90, GROUND)], fill=160)
    A.d['ocean'].line([(60, GROUND - 30), (300, GROUND - 60), (540, GROUND - 30), (800, GROUND - 60), (1020, GROUND - 30)], fill=200, width=18)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('崇安五夫里人 · 本名柳三变', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('崇安', 56), 860, 1020, t, t - u + P, rot=6)
    note_in(cv, '生年约在984至987年间 史无确载', t, t - u + P)

def art_l_family(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='mid')
    person(A, 780, GROUND, 190, dir=-1, robe=True, hat='knot', kneel=True, arm=100, layer='ink')
    for j in range(3):
        person(A, 240 + j * 90, GROUND, 120 + 10 * j, dir=1, robe=True, hat='none', kneel=True, arm=90, layer='qinlou' if j == 2 else 'mid')
    A.flush(cv)
    paste(cv, text_img('官宦之家 · 兄弟三人皆有文名', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '与兄三复 三接 号称柳氏三绝', t, t - u + P)

def art_l_music(A, cv, t, u):
    ground(A, GROUND)
    guqin(A, 700, GROUND - 40, 140, 7, t)
    person(A, 800, GROUND, 150, dir=-1, robe=True, hat='knot', kneel=True, arm=100, layer='mid')
    liu(A, 340, GROUND, 150, dir=1, arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    paste(cv, text_img('少年随父宦游 · 喜听市井乐曲', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_wanghai(A, cv, t, u):
    """6-beat set piece: 望海潮 — passing 杭州 on his way to the capital, he writes 望海潮 for the prefect: the city of the south-east,
    autumn osmanthus, ten li of lotus. Legend says a 金 emperor read it and resolved to march south."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=150)
    waves(A, 1210, t, rows=2, amp=4)
    for k in range(7):
        A.d['mid'].rectangle((140 + k * 120, 1080 - 40 * (k % 3), 220 + k * 120, 1200), fill=200)
    if ph >= 2:
        for k in range(10):
            A.d['pink'].ellipse((100 + k * 90, 1230 + (k % 2) * 30, 140 + k * 90, 1260 + (k % 2) * 30), fill=230)
    if ph >= 3.5:
        for k in range(12):
            A.d['qiuhuang'].ellipse((120 + (k * 79) % 840 - 6, 900 + (k * 37) % 120 - 6, 120 + (k * 79) % 840 + 6, 900 + (k * 37) % 120 + 6), fill=255)
    A.flush(cv)
    if ph < 2:
        lab, col = '东南形胜 三吴都会 钱塘自古繁华', QINLOU
    elif ph < 3.5:
        lab, col = '烟柳画桥 风帘翠幕 参差十万人家', QINLOU
    else:
        lab, col = '三秋桂子 十里荷花', ZHU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '相传金主完颜亮读此词 遂起投鞭渡江之志', t, t - u + 3.5 * P)

def art_l_jiangnan(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=140)
    river(A, 1210, t, rows=2, amp=3)
    boat(A, lerp(100, 800, ease_out(u / (3 * P))), 1220, 90, t)
    willow(A, 200, 1200, 260, t)
    A.flush(cv)
    paste(cv, text_img('流连苏杭扬州 · 一路填词', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_bianjing(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='汴京', layer='mid', open_=1.0)
    ground(A, GROUND)
    liu(A, lerp(-100, 540, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('入汴京应试 · 满怀抱负', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_fail(A, cv, t, u):
    ground(A, GROUND)
    for r in range(2):
        for i in range(6):
            x = 160 + i * 150; y = GROUND - r * 170
            A.d['mid'].rectangle((x - 55, y - 130, x + 55, y), fill=200)
    liu(A, 540, GROUND, 170, dir=-1, arm=-8, ph=t * 2)
    A.flush(cv)
    paste(cv, text_img('初次应考 · 名落孙山', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 落第
def art_l_fangqu(A, cv, t, u):
    for i in range(30):
        x = 120 + (i * 97) % 840; y = 640 + (i * 61) % 300
        A.d['wash'].ellipse((x - 3, y - 3, x + 3, y + 3), fill=200)
    ground(A, GROUND)
    A.d['qinlou'].rectangle((140, GROUND - 320, 940, GROUND), fill=120)
    for k in range(5):
        A.d['red'].ellipse((200 + k * 170 - 20, GROUND - 330, 200 + k * 170 + 20, GROUND - 280), fill=230)
    singers(A, 2, t, x0=620, step=140)
    liu(A, 340, GROUND, 170, dir=1, kneel=True, arm=100)
    A.flush(cv)
    paste(cv, text_img('浪迹汴京坊曲 · 为乐工歌伎填词', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_xinsheng(A, cv, t, u):
    """6-beat set piece: 新声 — whenever the court musicians had a new tune they came to 柳永 for words; the long slow lyric (慢词) flourished from him."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    liu(A, 280, GROUND, 170, dir=1, kneel=True, arm=lerp(80, 110, 0.5 + 0.5 * math.sin(t * 3)))
    for j in range(3):
        person(A, lerp(1100, 680, clamp(ph / 2)) + j * 110, GROUND, 150, dir=-1, robe=True, hat='knot', bow=20, arm=90, layer='ink')
    n = min(14, int(clamp((ph - 2) / 3) * 14))
    for k in range(n):
        A.d['wash'].rectangle((420 + (k % 7) * 34, GROUND - 120 - (k // 7) * 30, 446 + (k % 7) * 34, GROUND - 96 - (k // 7) * 30), fill=255)
    A.flush(cv)
    lab = '教坊乐工 每得新腔' if ph < 2 else ('必求柳永为之填词' if ph < 4 else '慢词长调 由此大兴')
    paste(cv, text_img(lab, SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见叶梦得避暑录话', t, t - u + P)

def art_l_hechongtian(A, cv, t, u):
    """6-beat set piece: 鹤冲天 — failing again, he writes: why trade a little wine and song for an empty name? a talented poet is a minister in plain clothes."""
    ph = u / P
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    A.d['qiuhuang'].ellipse((500, GROUND - 100, 540, GROUND - 74), fill=255)
    liu(A, 300, GROUND, 170, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 2)))
    A.flush(cv)
    if ph < 2:
        lab, col = '再次落榜 · 作鹤冲天', QINLOU
    elif ph < 4:
        lab, col = '忍把浮名 换了浅斟低唱', ZHU
    else:
        lab, col = '才子词人 自是白衣卿相', QINLOU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)

def art_l_fengzhi(A, cv, t, u):
    """6-beat set piece: 奉旨填词 — legend: when his name came up for the list, the emperor struck it: let him go and sip and sing, what does he want with fame?
    From then on he signed himself 奉旨填词柳三变."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    if ph < 3:
        emperor(A, 680, GROUND, 220, dir=-1, kneel=True, arm=90)
        scroll(A, 460, GROUND - 60, 220, 60, 1.0, layer='wash')
        if ph > 1.5:
            A.d['ink'].line((380, GROUND - 80, 540, GROUND - 40), fill=255, width=6)
        lab, col = '且去浅斟低唱 何要浮名', ZHU
    else:
        A.d['qinlou'].rectangle((140, GROUND - 320, 940, GROUND), fill=120)
        singers(A, 2, t, x0=620, step=140)
        liu(A, 340, GROUND, 180, dir=1, arm=lerp(60, 130, 0.5 + 0.5 * math.sin(t * 3)))
        lab, col = '自称 奉旨填词柳三变', QINLOU
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '见吴曾能改斋漫录 系笔记传闻', t, t - u + P)

def art_l_lufail(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    for i in range(min(4, int(u / (0.5 * P)) + 1)):
        stamp(cv, seal('落第', 50, ZHU), 240 + i * 200, 1100 + 30 * (i % 2), t, t - u + i * 0.5 * P)
    paste(cv, text_img('前后数次应试 · 皆不第', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_leave(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='汴京', layer='mid', open_=1.0)
    ground(A, GROUND)
    liu(A, lerp(540, 1100, ease_out(u / (3 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('心灰意冷 · 离京南下', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 晓风
def scene_yulin(cv, t, c, k):
    """8-beat custom scene: 雨霖铃 — cicadas in the cold, dusk at the long pavilion after rain; the boatman urges departure;
    hand in hand, tearful eyes; where will I wake tonight from wine? the willow bank, the dawn wind, the waning moon."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph >= 5:
        moon(A, 760, 860, 80, 0.1)
    A.d['ocean'].rectangle((0, 1180, W, GROUND + 40), fill=130)
    river(A, 1190, t, rows=2, amp=3)
    willow(A, 160, 1180, 320, t)
    willow(A, 920, 1180, 300, t)
    pavilion(A, 340, 1180, 260)
    if ph < 3:
        liu(A, 300, 1180, 160, dir=1, arm=90)
        yu(A, 400, 1180, 150, dir=-1, arm=90, t=t, layer='mid')
        boat(A, 700, 1200, 90, t, sail=False)
    else:
        boat(A, lerp(700, 1000, clamp((ph - 3) / 4)), 1200, 90, t, sail=False)
        yu(A, 380, 1180, 150, dir=1, arm=-8, t=t, layer='mid')
    if ph < 2:
        for i in range(30):
            q = (t * 1.4 + i / 30) % 1
            x = 60 + (i * 53) % 960
            A.d['wash'].line((x, lerp(600, 1180, q), x - 6, lerp(600, 1180, q) + 26), fill=120, width=2)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '雨霖铃', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=85)
    fx.flush(cv)
    lines = ['寒蝉凄切 对长亭晚', '执手相看泪眼', '今宵酒醒何处', '杨柳岸 晓风残月']
    for i, line in enumerate(lines):
        st = s0 + (0.4 + i * 1.7) * P
        if t >= st:
            paste(cv, text_img(line, SERIF, 44, ZHU if i == 3 else QINLOU, 'Black', bleed=False, spacing=6), W / 2, 590 + i * 64, 1, clamp((t - st) / 0.4))
    note_in(cv, '离京时别情人之作 作年不详', t, s0 + 3 * P)

def art_l_drift(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=140)
    river(A, 1210, t, rows=2, amp=3)
    boat(A, lerp(-100, 900, (t * 0.04) % 1), 1220, 80, t)
    for k in range(4):
        x = 160 + k * 250
        A.d['mid'].polygon([(x - 160, 1200), (x, 980), (x + 160, 1200)], fill=150)
    A.flush(cv)
    paste(cv, text_img('漂泊江南 · 羁旅行役', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_ganzhou(A, cv, t, u):
    """6-beat set piece: 八声甘州 — evening rain sweeps the river sky; he leans on the rail and thinks of her at the window, mistaking sail after sail for his."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1180, W - 60, GROUND + 40), fill=150)
    river(A, 1190, t, rows=2, amp=4)
    for i in range(40):
        q = (t * 1.4 + i / 40) % 1
        x = 60 + (i * 53) % 960
        A.d['wash'].line((x, lerp(600, 1180, q), x - 6, lerp(600, 1180, q) + 26), fill=int(140 * clamp(1 - (ph - 3) / 1)), width=2)
    A.d['mid'].rectangle((120, 1000, 360, 1180), fill=200)
    A.d['ink'].rectangle((100, 980, 380, 1000), fill=255)
    liu(A, 260, 1180, 150, dir=1, arm=60, old=0.3)
    for k in range(3):
        boat(A, 560 + k * 160, 1200, 50, t)
    A.flush(cv)
    if ph < 3:
        lab, col = '对潇潇暮雨洒江天 一番洗清秋', QINLOU
    else:
        lab, col = '想佳人 妆楼颙望 误几回 天际识归舟', ZHU
    paste(cv, text_img(lab, SERIF, 42, col, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '苏轼赞其中数句 不减唐人高处', t, t - u + 2 * P)

def art_l_dielian(A, cv, t, u):
    ground(A, GROUND)
    A.d['mid'].rectangle((300, GROUND - 300, 600, GROUND), fill=200)
    liu(A, 450, GROUND - 300, 160, dir=1, arm=-8, old=0.3)
    A.flush(cv)
    paste(cv, text_img('衣带渐宽终不悔 为伊消得人憔悴', SERIF, 44, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '蝶恋花 作年不详', t, t - u + P)

def art_l_rename(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 420, 260, 1.0, layer='wash')
    A.flush(cv)
    paste(cv, text_img('柳三变', SERIF, 60, DIM, 'Black', bleed=False, spacing=8), W / 2, 1060, 1, clamp(1 - (u - P) / 0.5))
    paste(cv, text_img('柳永', SERIF, 66, INK, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 1.5 * P) / 0.5))
    paste(cv, text_img('改名柳永 字耆卿 · 再赴考场', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='qinlou')
    ground(A, GROUND)
    liu(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)), old=0.5)
    A.flush(cv)
    paste(cv, text_img('景祐元年恩科及第 · 已年近半百', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第四回 宦游
def art_l_muzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='睦州', layer='mid', open_=1.0)
    ground(A, GROUND)
    liu(A, 540, GROUND, 190, dir=1, arm=-8, old=0.5)
    A.flush(cv)
    paste(cv, text_img('任睦州团练推官', SERIF, 48, QINLOU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_l_yuhang(A, cv, t, u):
    ground(A, GROUND)
    for j in range(4):
        person(A, 600 + j * 100, GROUND, 140, dir=-1, robe=False, hat='knot', bow=15, arm=-8, layer='mid')
    liu(A, 340, GROUND, 190, dir=1, arm=60, old=0.5)
    A.flush(cv)
    paste(cv, text_img('任余杭县令 · 抚民清静', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_zhuhai(A, cv, t, u):
    """6-beat set piece: 煮海歌 — overseeing the 晓峰 salt field, he sees the salt boilers: no silk to weave, no field to plough;
    they boil the sea to pay the tax — and writes their song."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1100, W - 60, 1180), fill=150)
    waves(A, 1110, t, rows=2, amp=4)
    ground(A, GROUND)
    for k in range(3):
        x = 260 + k * 260
        A.d['ink'].rectangle((x - 70, GROUND - 60, x + 70, GROUND - 20), fill=255)
        flames(A, x, GROUND - 20, 120, 60, t, n=2, seed=k + 85, smoke=True)
    for j in range(3):
        person(A, 200 + j * 260, GROUND, 130, dir=1, robe=False, hat='knot', bow=30, arm=lerp(90, 140, 0.5 + 0.5 * math.sin(t * 4 + j)), layer='mid')
    A.flush(cv)
    if ph < 2:
        lab, col = '监定海晓峰盐场', QINLOU
    elif ph < 4:
        lab, col = '煮海之民何所营 妇无蚕织夫无耕', ZHU
    else:
        lab, col = '衣食之源太寥落 牢盆鬻就汝输征', QINLOU
    paste(cv, text_img(lab, SERIF, 44, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '浪子词人 也写下了民间疾苦', t, t - u + 2 * P)

def art_l_jingshui(A, cv, t, u):
    art_l_hook_well(A, cv, t, u)
    A.flush(cv)
    paste(cv, text_img('凡有井水饮处 即能歌柳词', SERIF, 48, QINLOU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '西夏归朝官之语 见叶梦得避暑录话', t, t - u + P)

def art_l_tuntian(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    liu(A, 540, GROUND, 200, dir=1, arm=60, old=0.6)
    A.flush(cv)
    paste(cv, text_img('官至屯田员外郎 · 世称柳屯田', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_l_stop(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 380, layer='mid')
    liu(A, 300, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8, old=0.8)
    candle(A, 600, GROUND - 74, 80, 0.8, t)
    A.flush(cv)
    paste(cv, text_img('终未得重用 · 晚年潦倒', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第五回 吊柳
def art_l_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    liu(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    candle(A, 860, GROUND, 100, 1.0, t, lit=False)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒于润州 一说襄阳', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年地点均无定论', t, t - u + P)

def art_l_diaoliu(A, cv, t, u):
    """6-beat set piece: 吊柳七 — he dies poor; the singing girls, the story goes, pool their money to bury him, and every 清明 bring wine to his grave."""
    ph = u / P
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 180), (x + 220, GROUND)], fill=150)
    A.d['mid'].chord((440, GROUND - 100, 640, GROUND + 100), 180, 360, fill=230)
    willow(A, 780, GROUND, 300, t)
    ground(A, GROUND)
    n = 0 if ph < 1.5 else min(5, int((ph - 1.5) / 0.5) + 1)
    for j in range(n):
        yu(A, 180 + j * 70, GROUND, 140, dir=1, bow=20, arm=90, t=t, layer='mid' if j % 2 else 'ink')
    A.flush(cv)
    if ph < 1.5:
        lab, col = '身后萧条 无以为葬', QINLOU
    elif ph < 3.5:
        lab, col = '相传歌伎们集资葬之', QINLOU
    else:
        lab, col = '每逢清明 携酒吊之 谓之吊柳七', ZHU
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '吊柳七之说出自民间传说', t, t - u + 1.5 * P)

def art_l_sushi(A, cv, t, u):
    ground(A, GROUND)
    person(A, 540, GROUND, 230, dir=1, robe=True, hat='knot', arm=lerp(-8, 80, ease_out(u / 0.6)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('苏轼称其八声甘州 不减唐人高处', SERIF, 44, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_manci(A, cv, t, u):
    ground(A, GROUND)
    n = min(8, int(clamp(u / (2.5 * P)) * 8) + 1)
    for k in range(n):
        A.d['wash'].rectangle((200 + k * 90, 1300 - 40 * k, 270 + k * 90, 1300), fill=255)
        A.d['qinlou'].rectangle((200 + k * 90, 1300 - 40 * k, 270 + k * 90, 1300 - 40 * k + 10), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('大量创作慢词长调 · 拓宽宋词疆域', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_wangguowei(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mid')
    person(A, 280, GROUND, 170, dir=1, robe=False, hat='none', kneel=True, arm=100, layer='ink')
    A.d['wash'].rectangle((440, GROUND - 140, 640, GROUND - 76), fill=255)
    A.flush(cv)
    paste(cv, text_img('王国维以 衣带渐宽 为治学第二境界', SERIF, 44, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '人间词话 三种境界之说', t, t - u + P)

def art_l_end(A, cv, t, u):
    moon(A, 720, 900, 90, 0.05)
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    river(A, 1210, t, rows=2, amp=3)
    willow(A, 340, 1200, 380, t)
    A.flush(cv)
    paste(cv, text_img('今宵酒醒何处 杨柳岸 晓风残月', SERIF, 46, QINLOU, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_l_legacy(A, cv, t, u):
    willow(A, 860, 1440, 140, t)

def art_l_title(A, cv, t, u):
    willow(A, 820, 1440, 280, t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    liu(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '崇安'), 48: ('第二回', '落第'), 80: ('第三回', '晓风'),
            112: ('第四回', '宦游'), 144: ('第五回', '吊柳')}

CARDS = [
    C(0, 2, 'war', 'num', num='一首望海潮', line='据说引来金兵南下', art=art_l_hook_city),
    C(2, 4, 'court', 'num', num='奉旨填词', line='皇帝亲手划掉了他', art=art_l_hook_decree),
    C(4, 6, 'works', 'num', num='凡有井水处', line='皆能歌柳词', art=art_l_hook_well),
    C(6, 8, 'night', 'num', num='杨柳岸', line='晓风残月', art=art_l_hook_moon),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 崇安
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=984, main='生于崇安', sub='武夷五夫', art=art_l_birth),
    C(22, 26, 'works', 'card', year=990, main='柳氏三绝', sub='兄弟有文名', note='年份约略', art=art_l_family),
    C(26, 30, 'night', 'card', year=998, main='少年听曲', sub='随父宦游', note='年份约略', art=art_l_music),
    C(30, 36, 'empire', 'card', year=1002, main='望海潮', sub='钱塘繁华', note='年份约略', art=art_l_wanghai),
    C(36, 40, 'life', 'card', year=1003, main='江南流连', sub='苏杭扬州', note='年份约略', art=art_l_jiangnan),
    C(40, 44, 'court', 'card', year=1008, main='入汴京', sub='应试', note='年份约略', art=art_l_bianjing),
    C(44, 48, 'fate', 'card', year=1009, main='初试落第', sub='名落孙山', note='年份约略', art=art_l_fail),
    # ---- 第二回 落第
    C(48, 50, 'fate', 'chapter'),
    C(50, 54, 'night', 'card', year=1010, main='坊曲', sub='为歌伎填词', note='年份约略', art=art_l_fangqu),
    C(54, 60, 'works', 'card', year=1012, main='新声', sub='慢词大兴', note='年份约略', art=art_l_xinsheng),
    C(60, 66, 'fate', 'card', year=1018, main='鹤冲天', sub='白衣卿相', note='年份约略', art=art_l_hechongtian),
    C(66, 72, 'court', 'card', year=1018, main='奉旨填词', sub='且去低唱', note='系笔记传闻', art=art_l_fengzhi),
    C(72, 76, 'death', 'card', year=1020, main='屡试不第', sub='四次落榜', note='次数说法不一', art=art_l_lufail),
    C(76, 80, 'fate', 'card', year=1024, main='离京南下', sub='心灰意冷', note='年份约略', art=art_l_leave),
    # ---- 第三回 晓风
    C(80, 82, 'night', 'chapter'),
    C(82, 90, 'night', 'yulin', year=1024),
    C(90, 94, 'life', 'card', year=1025, main='漂泊江南', sub='羁旅行役', note='年份约略', art=art_l_drift),
    C(94, 100, 'war', 'card', year=1030, main='八声甘州', sub='潇潇暮雨', note='作年不详', art=art_l_ganzhou),
    C(100, 104, 'works', 'card', year=1030, main='蝶恋花', sub='衣带渐宽', note='作年不详', art=art_l_dielian),
    C(104, 108, 'fate', 'card', year=1033, main='改名柳永', sub='字耆卿', note='年份约略', art=art_l_rename),
    C(108, 112, 'empire', 'card', year=1034, main='暮年及第', sub='恩科', art=art_l_jinshi),
    # ---- 第四回 宦游
    C(112, 114, 'works', 'chapter'),
    C(114, 118, 'court', 'card', year=1035, main='睦州推官', sub='初入仕途', art=art_l_muzhou),
    C(118, 122, 'life', 'card', year=1038, main='余杭县令', sub='抚民清静', note='年份约略', art=art_l_yuhang),
    C(122, 128, 'war', 'card', year=1040, main='煮海歌', sub='盐民之苦', note='年份约略', art=art_l_zhuhai),
    C(128, 132, 'night', 'card', year=1043, main='井水处', sub='皆歌柳词', note='年份约略', art=art_l_jingshui),
    C(132, 138, 'empire', 'card', year=1045, main='柳屯田', sub='屯田员外郎', note='年份约略', art=art_l_tuntian),
    C(138, 144, 'fate', 'card', year=1049, main='晚年潦倒', sub='终未重用', note='年份约略', art=art_l_stop),
    # ---- 第五回 吊柳
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'death', 'card', year=1053, main='柳永去世', sub='约在此年', art=art_l_death),
    C(150, 156, 'fate', 'card', year=1053, main='吊柳七', sub='民间传说', art=art_l_diaoliu),
    C(156, 160, 'works', 'card', year=1090, main='不减唐人', sub='苏轼之评', note='年份约略', art=art_l_sushi),
    C(160, 164, 'court', 'card', year=1090, main='慢词', sub='开一代词风', art=art_l_manci),
    C(164, 168, 'empire', 'card', year=1908, main='人间词话', sub='三境界', art=art_l_wangguowei),
    C(168, 170, 'end', 'card', year=1908, main='晓风残月', sub='杨柳岸', art=art_l_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='捌拾伍', col=QINLOU, acc=CANYUE, born=984, died=1053, age0=983, no_age=True,
    born_lab='约984年', died_lab='约1053年', years_txt='约公元984 — 约1053',
    hook_q='皇帝一句话断了他的仕途 · 他为何反成词坛宗师？',
    name_line='柳永 · 字耆卿', name='柳永', seal='柳七', title_art=art_l_title,
    q1='白衣卿相？', q2='浪子词人？',
    end_art=art_l_legacy, end_big='晓风残月', end_seal='柳七',
    end_l1='考场不要他', end_l2='井水边却处处唱着他',
    end_brush='白衣卿相', end_ask='柳永哪句词你最喜欢？评论区聊聊', next='陆游'),
    scenes=dict(chapter=scene_chapter, yulin=scene_yulin))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
