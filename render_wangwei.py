"""千古人物志 · 第陆拾陆集 · 王维 (约701–761)
Look: 空山青 + 红豆红, 松针 corner borders, a 辋川 chapter card: the Wangchuan villa painting is drawn stroke by stroke
(mountain → stream → pavilion → pines) and in the last chapter the moon rises over it.
Set pieces: 6-beat 郁轮袍 (演义), custom 8-beat scene 'wangchuan' (辋川二十景), 6-beat 凝碧池, 6-beat 阳关三叠,
6-beat 诗中有画.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_baijuyi as Bj         # engine + helpers (previous episode)
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
from render_sunwu import army

F.RIPPLE = False
KONGSHAN = (90, 124, 110)           # 空山青
HONGDOU = (180, 40, 50)             # 红豆红
S.LAYERS.append(('kongshan', KONGSHAN, 0.88, 1.0))
S.LAYERS.append(('hongdou', HONGDOU, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='禅', life='维', court='唐', night='月', war='乱', empire='画', works='诗', fate='禅', death='空', end='山')
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
G.THEMES['empire']['sun'] = (KONGSHAN, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (HONGDOU, 170, (W * 0.5, 720))
G.base_bg.cache_clear()

PINES = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(PINES)
for _x in (110, 200, 880, 970):     # 明月松间照 pines at the margins
    _d.line((_x, 1480, _x - 6, 1340), fill=(60, 60, 56, 70), width=6)
    for _k in range(4):
        _y = 1350 + _k * 30
        _d.polygon([(_x - 46 + _k * 6, _y), (_x + 40 - _k * 6, _y), (_x - 3, _y - 30)], fill=(70, 100, 80, 60))
for _k in range(3):
    _d.line([(260 + i * 28, 1478 + _k * 12 + 4 * math.sin(i * 0.5 + _k)) for i in range(21)], fill=(120, 150, 160, 40), width=2)
MTN_COL = {'night': (26, 32, 36), 'death': (60, 62, 60), 'war': (110, 64, 52), 'fate': (90, 104, 98)}
def draw_background(t, theme):
    """辋川: misty hills, pines at the margins and a stream."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 192, 188), (156, 170, 162), MTN_COL.get(theme, (106, 130, 118))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(PINES)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """红豆: a sprig with red beans in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=KONGSHAN + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=KONGSHAN + (220,), width=3)
        d.line((x + sx * 20, y + sy * 100, x + sx * 90, y + sy * 24), fill=(70, 60, 50, 220), width=3)
        for k in range(5):
            bx, by = x + sx * (30 + k * 14), y + sy * (88 - k * 15)
            d.ellipse((bx - 8, by - 6, bx + 8, by + 6), fill=HONGDOU + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def wei(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, **kw):
    """王维: slender poet-painter — 幞头, clean face, a Buddhist rosary at the wrist in later years."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='none' if up else 'knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.chord((x - 0.08 * h, y - 1.06 * h, x + 0.08 * h, y - 0.9 * h), 180, 360, fill=255)
        d.line((x - dir * 0.06 * h, y - 0.97 * h, x - dir * 0.16 * h, y - 0.88 * h), fill=255, width=max(2, int(0.02 * h)))
        A.d['kongshan'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        if old > 0.3:
            for k in range(6):
                a = k * 1.05
                A.d['hongdou'].ellipse((x + 0.12 * h * math.cos(a) - 0.012 * h, y - 0.45 * h + 0.05 * h * math.sin(a) - 0.012 * h,
                                        x + 0.12 * h * math.cos(a) + 0.012 * h, y - 0.45 * h + 0.05 * h * math.sin(a) + 0.012 * h), fill=255)
    return hand

def qin(A, x, y, s):
    A.d['ink'].rounded_rectangle((x - s, y - 0.12 * s, x + s, y + 0.06 * s), radius=int(0.06 * s), fill=255)
    for k in range(5):
        A.d['wash'].line((x - 0.9 * s, y - 0.08 * s + k * 0.03 * s, x + 0.9 * s, y - 0.08 * s + k * 0.03 * s), fill=200, width=1)

def wangchuan(A, cx, cy, w, p, t):
    """the Wangchuan villa scroll, drawn progressively p in 0..1."""
    A.d['wash'].rectangle((cx - w, cy - 0.5 * w, cx + w, cy + 0.5 * w), fill=255)
    A.d['ink'].rectangle((cx - w, cy - 0.5 * w, cx + w, cy + 0.5 * w), outline=255, width=4)
    if p > 0:
        q = clamp(p / 0.3)
        for k in range(3):
            x = cx - 0.6 * w + k * 0.55 * w
            A.d['kongshan'].polygon([(x - 0.35 * w, cy + 0.2 * w), (x, cy + 0.2 * w - 0.5 * w * q), (x + 0.35 * w, cy + 0.2 * w)], fill=180)
    if p > 0.3:
        q = clamp((p - 0.3) / 0.25)
        A.d['ocean'].line([(cx - w + 10, cy + 0.32 * w), (lerp(cx - w + 10, cx + w - 10, q), cy + 0.28 * w)], fill=200, width=10)
    if p > 0.55:
        A.d['ink'].polygon([(cx - 0.1 * w, cy + 0.2 * w), (cx + 0.1 * w, cy + 0.2 * w), (cx, cy + 0.08 * w)], fill=255)
        A.d['ink'].line((cx - 0.08 * w, cy + 0.2 * w, cx - 0.08 * w, cy + 0.3 * w), fill=255, width=3)
        A.d['ink'].line((cx + 0.08 * w, cy + 0.2 * w, cx + 0.08 * w, cy + 0.3 * w), fill=255, width=3)
    if p > 0.8:
        for k in range(4):
            x = cx - 0.8 * w + k * 0.5 * w
            A.d['pine'].polygon([(x - 0.06 * w, cy + 0.3 * w), (x, cy + 0.1 * w), (x + 0.06 * w, cy + 0.3 * w)], fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.3), 48: (0.3, 0.55), 80: (0.55, 0.8), 112: (0.8, 1.0), 144: (1.0, 1.0)}
def art_scroll_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.3, 0.55))
    q = ease_out(u / (1.2 * P))
    wangchuan(A, 540, 1080, 280, lerp(a, b, q), t)
    if kb == 144:
        r = 30
        A.d['wash'].ellipse((760 - r, 980 - r - 60 * q, 760 + r, 980 + r - 60 * q), fill=255)
        A.d['ink'].ellipse((760 - r, 980 - r - 60 * q, 760 + r, 980 + r - 60 * q), outline=160, width=2)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_scroll_chapter)
    ink_in(cv, text_img(no, SERIF, 56, KONGSHAN, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_w_hook_17(A, cv, t, u):
    ground(A, GROUND)
    wei(A, 540, GROUND, lerp(130, 190, ease_out(u / (1.4 * P))), dir=1, arm=40)

def art_w_hook_beans(A, cv, t, u):
    ground(A, GROUND)
    n = int(clamp(u / (1.4 * P)) * 14) + 1
    for i in range(n):
        A.d['hongdou'].ellipse((340 + (i % 7) * 60 - 18, GROUND - 40 - (i // 7) * 40 - 14, 340 + (i % 7) * 60 + 18, GROUND - 40 - (i // 7) * 40 + 14), fill=255)

def art_w_hook_painting(A, cv, t, u):
    wangchuan(A, 540, 1100, 300, clamp(u / (1.6 * P)), t)

def art_w_hook_prison(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    wei(A, 540, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8)
    ground(A, GROUND)

# ================================================================ 第一回 少年才子
def art_w_birth(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('太原王氏 · 母崔氏奉佛三十余年', SERIF, 44, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('河东蒲州', 46), 860, 1020, t, t - u + P, rot=6)

def art_w_genius(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='kongshan')
    wei(A, 300, GROUND, 140, dir=1, kneel=True, arm=110)
    qin(A, 600, GROUND - 90, 100)
    A.flush(cv)
    paste(cv, text_img('九岁知属辞 · 工草隶 闲音律', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_double9(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 320), (x + 220, GROUND)], fill=170)
    ground(A, GROUND)
    for j in range(3):
        person(A, 640 + j * 90, GROUND - 200, 80, dir=1, robe=True, hat='knot', arm=40, layer='mid')
        A.d['hongdou'].ellipse((640 + j * 90 - 6, GROUND - 290, 640 + j * 90 + 6, GROUND - 278), fill=255)
    wei(A, 300, GROUND, 170, dir=1, arm=-8)
    A.flush(cv)
    type_in(cv, text_img('独在异乡为异客 每逢佳节倍思亲', SERIF, 42, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('十七岁', 50), 860, 1020, t, t - u + P, rot=6)

def art_w_yulunpao(A, cv, t, u):
    """6-beat set piece: 郁轮袍 — dressed as a musician he plays the pipa at a princess's banquet; she asks his name; his poems are presented. (Anecdote.)"""
    ph = u / P
    palace(A, 540, 1300, 300, layer='hongdou')
    ground(A, GROUND)
    person(A, 820, GROUND - 30, 190, dir=-1, robe=True, hat='knot', female=True, arm=lerp(20, 90, clamp((ph - 3) / 0.4)), layer='mulanfen')
    wei(A, 480, GROUND, 180, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 9)) if ph < 3 else 90)
    Bj.pipa(A, 540, GROUND - 110, 40, layer='fengye')
    if ph > 3.5:
        scroll(A, 680, GROUND - 160, 120, 40, 1.0, layer='wash')
    A.flush(cv)
    lab = '为伶人 · 独奏新曲 声调哀切' if ph < 3 else '此生何名 · 郁轮袍'
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3 else KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '事见集异记 多认为小说家言', t, t - u + 0.5 * P)

def art_w_jinshi(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='kongshan')
    ground(A, GROUND)
    wei(A, 540, GROUND, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.5)))
    A.flush(cv)
    stamp(cv, seal('进士', 56), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('进士及第 · 授太乐丞', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_lion(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    A.d['yellow'].ellipse((420, GROUND - 160, 660, GROUND - 40), fill=255)
    A.d['yellow'].ellipse((600, GROUND - 200, 700, GROUND - 110), fill=255)
    for j in range(2):
        person(A, 460 + j * 120, GROUND, 120, dir=1, robe=False, hat='knot', arm=60, layer='ink')
    A.flush(cv)
    paste(cv, text_img('伶人舞黄狮子 · 坐累贬济州', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('济州', 56, INK), 860, 1020, t, t - u + P, rot=6)

# ================================================================ 第二回 大漠孤烟
def art_w_wife(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    wei(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    paste(cv, text_img('妻亡不再娶 · 三十年孤居一室', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见旧唐书本传', t, t - u + P)

def art_w_zhangjiuling(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='kongshan')
    ground(A, GROUND)
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='crown', arm=lerp(40, 100, ease_out(u / 0.5)), layer='ink')
    wei(A, 400, GROUND, 180, dir=1, kneel=True, bow=20, arm=100)
    A.flush(cv)
    paste(cv, text_img('张九龄擢为右拾遗', SERIF, 48, KONGSHAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_w_desert(A, cv, t, u):
    A.d['dune'].polygon([(60, GROUND), (300, GROUND - 120), (700, GROUND - 40), (W - 60, GROUND)], fill=210)
    A.d['ink'].line((420, GROUND - 90, 424 + 6 * math.sin(t), 700), fill=200, width=8)
    A.d['ocean'].line((60, GROUND - 20, W - 60, GROUND - 30), fill=200, width=10)
    r = 80
    A.d['red'].ellipse((760 - r, GROUND - 60 - r, 760 + r, GROUND - 60 + r), fill=200)
    A.flush(cv)
    type_in(cv, text_img('大漠孤烟直 长河落日圆', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('使至塞上', 48), 860, 1020, t, t - u + P, rot=6)

def art_w_liangzhou(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='凉州', layer='mid', open_=1.0)
    ground(A, GROUND)
    wei(A, 540, GROUND, 180, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('出使河西 · 为节度判官', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_hongdou(A, cv, t, u):
    A.d['ink'].line((540, GROUND, 530, GROUND - 300), fill=255, width=12)
    q = ease_out(u / P)
    for k in range(16):
        a = k * 0.39
        px, py = 530 + 140 * math.cos(a) * q, GROUND - 330 + 80 * math.sin(a) * q
        A.d['hongdou'].ellipse((px - 12, py - 9, px + 12, py + 9), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    type_in(cv, text_img('红豆生南国 春来发几枝', SERIF, 46, INK, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('愿君多采撷 此物最相思', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)

def art_w_mengcheng(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 300), (x + 220, GROUND)], fill=150)
    ground(A, GROUND)
    for i in range(4):
        person(A, 320 + i * 140, GROUND, 140, dir=1 if i % 2 else -1, robe=True, hat='knot', kneel=True, arm=lerp(60, 110, 0.5 + 0.5 * math.sin(t * 2 + i)), layer='kongshan' if i == 0 else 'mid')
    A.flush(cv)
    paste(cv, text_img('与裴迪 孟浩然诸友唱和', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第三回 辋川
def art_w_buy(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 380), (x + 220, GROUND)], fill=170)
    river(A, 1260, t, rows=2, amp=3)
    A.d['mid'].rectangle((620, 1120, 860, 1260), fill=230)
    A.d['ink'].polygon([(600, 1120), (880, 1120), (740, 1060)], fill=255)
    A.flush(cv)
    paste(cv, text_img('得宋之问蓝田别墅 · 辋川', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('蓝田', 56), 860, 1020, t, t - u + P, rot=6)

def scene_wangchuan(cv, t, c, k):
    """8-beat custom scene: 辋川 — the camera drifts across the villa: 鹿柴, 竹里馆, 辛夷坞, 木兰柴; one quatrain each."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    spots = ['鹿柴', '竹里馆', '辛夷坞', '鸟鸣涧']
    k2 = min(3, int(ph / 2))
    lp = ph - 2 * k2
    for kk in range(3):
        x = 260 + kk * 280 - lp * 30
        A.d['kongshan'].polygon([(x - 220, GROUND), (x, GROUND - 360), (x + 220, GROUND)], fill=150)
    if k2 == 0:
        for j in range(30):
            A.d['wash'].line((200 + j * 24, 700, 200 + j * 24 - 60, GROUND), fill=40, width=3)
        A.d['wash'].ellipse((300, GROUND - 120, 400, GROUND - 60), fill=200)
    elif k2 == 1:
        for j in range(12):
            A.d['pine'].line((160 + j * 70, GROUND, 170 + j * 70, GROUND - 320), fill=230, width=8)
        wei(A, 540, GROUND, 140, dir=1, kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6)))
        qin(A, 610, GROUND - 60, 60)
    elif k2 == 2:
        for j in range(6):
            x = 200 + j * 130
            A.d['ink'].line((x, GROUND, x - 6, GROUND - 200), fill=255, width=6)
            for m in range(4):
                A.d['mulanfen'].ellipse((x - 30 + m * 16 - 10, GROUND - 230 + (m % 2) * 20 - 14, x - 30 + m * 16 + 10, GROUND - 230 + (m % 2) * 20 + 6), fill=230)
    else:
        r = 60
        A.d['wash'].ellipse((760 - r, 820 - r, 760 + r, 820 + r), fill=240)
        for j in range(3):
            crow(A, 300 + j * 140, 980 - j * 30, 20, t * 4 + j)
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '辋川', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.08, seed=66)
    fx.flush(cv)
    poems = ['空山不见人 但闻人语响', '独坐幽篁里 弹琴复长啸', '木末芙蓉花 山中发红萼', '月出惊山鸟 时鸣春涧中']
    stamp(cv, seal(spots[k2], 44, ZHU), 860, 1440, t, s0 + 2 * k2 * P + 0.2, rot=6)
    paste(cv, text_img(poems[k2], SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 575, 1, clamp(lp / 0.4))
    paste(cv, text_img('辋川集 二十景 二十首', SERIF, 40, DIM, 'Black', bleed=False, spacing=4), W / 2, 680, 1, clamp((ph - 0.5) / 0.4))

def art_w_paint(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 460, layer='kongshan')
    wei(A, 260, GROUND, 180, dir=1, kneel=True, bow=20, arm=110)
    A.d['wash'].rectangle((360, GROUND - 120, 760, GROUND - 76), fill=255)
    q = ease_out(u / (2 * P))
    for k in range(3):
        x = 420 + k * 120
        A.d['kongshan'].polygon([(x - 50, GROUND - 80), (x, GROUND - 80 - 36 * q), (x + 50, GROUND - 80)], fill=200)
    A.flush(cv)
    paste(cv, text_img('辋川图 · 山水画南宗之祖', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '南宗之说出自明代董其昌', t, t - u + P)

def art_w_mother(A, cv, t, u):
    A.d['mid'].chord((380, 1120, 700, 1320), 180, 360, fill=230)
    ground(A, GROUND)
    wei(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    paste(cv, text_img('母丧 · 柴毁骨立 殆不胜丧', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_chan(A, cv, t, u):
    for k in range(5):
        q = (t * 0.2 + k / 5) % 1
        A.d['kongshan'].ellipse((540 - 300 * q, 1100 - 160 * q, 540 + 300 * q, 1100 + 160 * q), outline=int(160 * (1 - q)), width=4)
    ground(A, GROUND)
    wei(A, 540, GROUND, 170, dir=1, kneel=True, arm=60, old=0.4)
    A.flush(cv)
    paste(cv, text_img('晚年长斋 不衣文彩', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('摩诘', 56), 860, 1020, t, t - u + P, rot=6)

def art_w_sit(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 400), (x + 220, GROUND)], fill=170)
    for k in range(6):
        q = (t * 0.06 + k / 6) % 1
        A.d['wash'].ellipse((lerp(-200, 1200, q) - 160, 820 + k * 30 - 30, lerp(-200, 1200, q) + 160, 820 + k * 30 + 30), fill=170)
    ground(A, GROUND)
    wei(A, 600, GROUND, 160, dir=1, kneel=True, arm=-8, old=0.5)
    A.flush(cv)
    type_in(cv, text_img('行到水穷处 坐看云起时', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, t, t - u + 0.4, 0.5)

# ================================================================ 第四回 凝碧池
def art_w_anshi(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=1.0)
    flames(A, 540, 1060, 600, 200 * ease_out(u / P), t, n=7, seed=756, smoke=True)
    ground(A, GROUND)
    army(A, lerp(-200, 140, ease_out(u / (2 * P))), GROUND, 6, dir=1, layer='ink', t=t, march=True, h=100)
    A.flush(cv)
    paste(cv, text_img('安禄山陷长安 · 玄宗西奔', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_captured(A, cv, t, u):
    A.d['ink'].rectangle((320, 900, 760, GROUND), outline=255, width=8)
    for k in range(9):
        A.d['ink'].line((320 + k * 55, 900, 320 + k * 55, GROUND), fill=200, width=4)
    wei(A, 540, GROUND, 170, dir=1, kneel=True, bow=30, arm=-8)
    A.d['hulu'].ellipse((600, GROUND - 40, 640, GROUND), fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('为贼所得 · 服药取痢 伪称瘖病', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_ningbi(A, cv, t, u):
    """6-beat set piece: 凝碧池 — the rebels feast and force the court musicians to play; one musician hurls his instrument and weeps;
    in the temple prison Wang Wei hears of it and writes a poem in secret."""
    ph = u / P
    A.d['ocean'].ellipse((160, 1160, 920, 1300), fill=160)
    palace(A, 540, 1160, 260, layer='mid')
    for j in range(4):
        person(A, 260 + j * 170, 1260, 110, dir=1, robe=True, hat='knot', kneel=True, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6 + j)), layer='ink')
    if ph > 2:
        person(A, 760, 1260, 130, dir=-1, robe=True, hat='knot', arm=lerp(60, 170, clamp((ph - 2) / 0.3)), layer='hongdou')
    ground(A, GROUND)
    A.flush(cv)
    lab = '贼宴凝碧池 · 逼梨园弟子奏乐' if ph < 2 else ('乐工雷海青掷乐器 西向恸哭' if ph < 3.6 else '万户伤心生野烟 百官何日再朝天')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 2 else KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '王维闻之 潜为凝碧诗', t, t - u + 3.6 * P)

def art_w_official(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    wei(A, 400, GROUND, 180, dir=1, bow=30, arm=-8)
    person(A, 760, GROUND - 30, 190, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, ease_out(u / 0.5)), layer='ink')
    A.flush(cv)
    paste(cv, text_img('被迫受伪职 · 给事中', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_pardon(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='kongshan')
    ground(A, GROUND)
    emperor(A, 760, GROUND - 30, 190, dir=-1, arm=lerp(20, 80, ease_out(u / 0.5)))
    wei(A, 360, GROUND, 180, dir=1, kneel=True, bow=40, arm=100)
    person(A, 520, GROUND, 180, dir=1, robe=True, hat='knot', kneel=True, bow=40, arm=100, layer='mid')
    A.flush(cv)
    paste(cv, text_img('凝碧诗闻于行在 · 弟王缙请削己官以赎兄罪', SERIF, 40, KONGSHAN, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('特宥之', 50), 260, 1020, t, t - u + P, rot=-5)

def art_w_yangguan(A, cv, t, u):
    """6-beat set piece: 阳关三叠 — morning rain in Weicheng settles the dust; willows fresh by the inn; one more cup; the friend rides west past Yangguan."""
    ph = u / P
    for k in range(30):
        q = (t * 1.0 + k / 30) % 1
        A.d['wash'].line((80 + (k * 37) % 920, lerp(620, 1300, q), 80 + (k * 37) % 920 - 6, lerp(620, 1300, q) + 24), fill=int(140 * clamp(1 - ph / 3)), width=2)
    for k in range(3):
        x = 200 + k * 120
        A.d['ink'].line((x, GROUND, x, GROUND - 260), fill=255, width=8)
        for j in range(6):
            A.d['grass'].line((x, GROUND - 260, x - 40 + j * 16, GROUND - 120 + 8 * math.sin(t * 2 + j)), fill=230, width=2)
    A.d['mid'].rectangle((600, GROUND - 180, 900, GROUND), fill=220)
    ground(A, GROUND)
    if ph < 3.5:
        wei(A, 520, GROUND, 170, dir=1, arm=110)
        person(A, 640, GROUND, 170, dir=-1, robe=True, hat='knot', arm=110, layer='mid')
    else:
        wei(A, 520, GROUND, 170, dir=1, arm=60)
        rider(A, lerp(640, 1150, ease_out((ph - 3.5) / 2)), GROUND, 130, dir=1, ph=t * 6, layer='mid')
    A.flush(cv)
    type_in(cv, text_img('渭城朝雨浥轻尘 客舍青青柳色新', SERIF, 40, INK, 'Black', bleed=False, spacing=2), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('劝君更尽一杯酒 西出阳关无故人', SERIF, 40, ZHU, 'Black', bleed=False, spacing=2), W / 2, 835, t, t - u + 2.2 * P, 0.5)

# ================================================================ 第五回 诗佛
def art_w_youcheng(A, cv, t, u):
    for k in range(3):
        A.d['kongshan'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    wei(A, 540, GROUND - 180, 190, dir=1, arm=60, old=0.6)
    A.flush(cv)
    stamp(cv, seal('尚书右丞', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('官至尚书右丞 · 世称王右丞', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    wei(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('作书与亲故别 · 舍笔而绝', SERIF, 46, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '生年一说六九九年 卒年七六一年', t, t - u + P)

def art_w_daizong(A, cv, t, u):
    palace(A, 540, 1300, 300, layer='mid')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 200, dir=1, arm=lerp(40, 100, ease_out(u / 0.5)))
    A.flush(cv)
    type_in(cv, text_img('卿之伯氏 天宝中诗名冠代', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, t, t - u + 0.4, 0.5)
    stamp(cv, seal('唐代宗', 50, INK), 860, 1020, t, t - u + P, rot=6)

def art_w_sushi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='kongshan')
    person(A, 300, GROUND, 190, dir=1, robe=True, hat='knot', kneel=True, arm=110, layer='ink')
    wangchuan(A, 600, GROUND - 160, 100, 1.0, t)
    A.flush(cv)
    type_in(cv, text_img('味摩诘之诗 诗中有画 · 观摩诘之画 画中有诗', SERIF, 38, ZHU, 'Black', bleed=False, spacing=2), W / 2, 830, t, t - u + 0.4, 0.6)
    stamp(cv, seal('苏轼', 54), 860, 1020, t, t - u + P, rot=6)

def art_w_three(A, cv, t, u):
    ground(A, GROUND)
    for i, (lay, nm) in enumerate((('fengye', '诗仙'), ('mid', '诗圣'), ('kongshan', '诗佛'))):
        person(A, 300 + i * 240, GROUND, 180, dir=1, robe=True, hat='knot', arm=40, layer=lay)
    A.flush(cv)
    for i, nm in enumerate(('诗仙', '诗圣', '诗佛')):
        stamp(cv, seal(nm, 40, ZHU if i == 2 else INK), 300 + i * 240, 1020, t, t - u + i * 0.4 * P)
    paste(cv, text_img('李白 杜甫 王维', SERIF, 48, KONGSHAN, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_w_empty(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['kongshan'].polygon([(x - 220, GROUND), (x, GROUND - 380), (x + 220, GROUND)], fill=150)
    q = ease_out(u / P)
    A.d['gold'].line((200, 700, lerp(200, 700, q), lerp(700, GROUND - 200, q)), fill=200, width=6)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('返景入深林 复照青苔上', SERIF, 48, KONGSHAN, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_w_legacy(A, cv, t, u):
    wangchuan(A, 860, 1360, 70, 1.0, t)

def art_w_title(A, cv, t, u):
    wangchuan(A, 800, 1280, 180, 1.0, t)
    wei(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '少年才子'), 48: ('第二回', '大漠孤烟'), 80: ('第三回', '辋川'),
            112: ('第四回', '凝碧池'), 144: ('第五回', '诗佛')}

CARDS = [
    C(0, 2, 'life', 'num', num='十七岁', line='写下千古思乡句', art=art_w_hook_17),
    C(2, 4, 'night', 'num', num='一颗红豆', line='此物最相思', art=art_w_hook_beans),
    C(4, 6, 'works', 'num', num='诗中有画', line='画中有诗', art=art_w_hook_painting),
    C(6, 8, 'death', 'num', num='安史之乱', line='他差点身败名裂', art=art_w_hook_prison),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 少年才子
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'life', 'card', year=701, main='生于蒲州', sub='太原王氏', note='生年一说六九九年', art=art_w_birth),
    C(22, 26, 'works', 'card', year=709, main='神童', sub='诗书琴画', art=art_w_genius),
    C(26, 30, 'night', 'card', year=717, main='九月九日', sub='忆山东兄弟', art=art_w_double9),
    C(30, 36, 'court', 'card', year=720, main='郁轮袍', sub='一则轶事', art=art_w_yulunpao),
    C(36, 42, 'empire', 'card', year=721, main='进士及第', sub='太乐丞', art=art_w_jinshi),
    C(42, 48, 'fate', 'card', year=721, main='黄狮子', sub='贬谪济州', art=art_w_lion),
    # ---- 第二回 大漠孤烟
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'death', 'card', year=730, main='丧妻', sub='终身不娶', art=art_w_wife),
    C(54, 58, 'court', 'card', year=734, main='右拾遗', sub='张九龄提携', art=art_w_zhangjiuling),
    C(58, 62, 'war', 'card', year=737, main='使至塞上', sub='大漠孤烟', art=art_w_desert),
    C(62, 66, 'fate', 'card', year=737, main='河西判官', sub='凉州', art=art_w_liangzhou),
    C(66, 72, 'night', 'card', year=740, main='相思', sub='红豆', art=art_w_hongdou),
    C(72, 80, 'works', 'card', year=740, main='诗友', sub='孟浩然 裴迪', art=art_w_mengcheng),
    # ---- 第三回 辋川
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'empire', 'card', year=742, main='辋川别业', sub='半官半隐', art=art_w_buy),
    C(86, 94, 'works', 'wangchuan', year=745),
    C(94, 98, 'empire', 'card', year=746, main='辋川图', sub='南宗之祖', art=art_w_paint),
    C(98, 102, 'death', 'card', year=750, main='丁母忧', sub='哀毁骨立', art=art_w_mother),
    C(102, 106, 'fate', 'card', year=752, main='奉佛', sub='字摩诘', art=art_w_chan),
    C(106, 112, 'night', 'card', year=754, main='云起时', sub='终南别业', art=art_w_sit),
    # ---- 第四回 凝碧池
    C(112, 114, 'death', 'chapter'),
    C(114, 118, 'war', 'card', year=756, main='安史之乱', sub='长安失陷', art=art_w_anshi),
    C(118, 122, 'night', 'card', year=756, main='被俘', sub='服药装哑', art=art_w_captured),
    C(122, 128, 'death', 'card', year=756, main='凝碧池', sub='一首诗救了他', art=art_w_ningbi),
    C(128, 132, 'court', 'card', year=756, main='受伪职', sub='人生污点', art=art_w_official),
    C(132, 136, 'fate', 'card', year=758, main='获宥', sub='兄弟情深', art=art_w_pardon),
    C(136, 144, 'life', 'card', year=758, main='阳关三叠', sub='送元二使安西', note='作年不详', art=art_w_yangguan),
    # ---- 第五回 诗佛
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'court', 'card', year=759, main='尚书右丞', sub='王右丞', art=art_w_youcheng),
    C(150, 154, 'death', 'card', year=761, main='王维去世', sub='舍笔而绝', art=art_w_death),
    C(154, 158, 'empire', 'card', year=763, main='诗名冠代', sub='代宗之语', art=art_w_daizong),
    C(158, 162, 'works', 'card', year=1080, main='诗中有画', sub='苏轼之评', art=art_w_sushi),
    C(162, 166, 'life', 'card', year=1080, main='诗佛', sub='三大诗人', art=art_w_three),
    C(166, 170, 'end', 'card', year=1080, main='空山', sub='返景入深林', art=art_w_empty),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾陆', col=KONGSHAN, acc=HONGDOU, born=701, died=761, age0=700,
    born_lab='约701年', died_lab='761年', years_txt='约公元701 — 761',
    hook_q='他是诗佛 · 为什么却做过叛军的官？',
    name_line='王维 · 字摩诘', name='王维', seal='摩诘', title_art=art_w_title,
    q1='诗佛？', q2='失节？',
    end_art=art_w_legacy, end_big='诗中有画', end_seal='摩诘',
    end_l1='他把山水写进了诗', end_l2='也把人生的无奈藏进了空山',
    end_brush='行到水穷处', end_ask='李白杜甫王维 你最爱谁的诗？评论区聊聊', next='欧阳修'),
    scenes=dict(chapter=scene_chapter, wangchuan=scene_wangchuan))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
