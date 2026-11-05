"""千古人物志 · 第陆拾叁集 · 王羲之 (303–361)
Look: 墨池黑 + 鹅黄, 白鹅 corner borders, a 墨池 chapter card: the pond darkens from clear to ink-black over the chapters
(0→1) and in the last chapter a white goose swims across it.
Set pieces: 6-beat 临池学书 (池水尽墨), 6-beat 坦腹东床, custom 8-beat scene 'lanting' (兰亭雅集 · 曲水流觞),
6-beat 书扇, 6-beat 换鹅, 6-beat 昭陵玉匣.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_simayi as Sy          # engine + helpers (previous episode)
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

F.RIPPLE = False
MOCHI = (44, 48, 56)                # 墨池黑
EHUANG = (214, 176, 76)             # 鹅黄
S.LAYERS.append(('mochi', MOCHI, 0.9, 1.0))
S.LAYERS.append(('ehuang', EHUANG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='书', life='王', court='晋', night='墨', war='乱', empire='圣', works='书', fate='隐', death='帖', end='兰')
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
G.THEMES['empire']['sun'] = (EHUANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (EHUANG, 190, (W * 0.5, 720))
G.base_bg.cache_clear()

BAMBOO = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(BAMBOO)
for _x in list(range(80, 260, 28)) + list(range(830, 1010, 28)):    # 茂林修竹 at the margins
    _h = 140 + (_x * 13) % 70
    _d.line((_x, 1480, _x + 4, 1480 - _h), fill=(80, 110, 80, 60), width=5)
    for _k in range(0, _h, 34):
        _d.line((_x - 3, 1480 - _k, _x + 7, 1480 - _k), fill=(60, 90, 60, 70), width=2)
        _d.polygon([(_x + 4, 1480 - _k - 10), (_x + 30, 1480 - _k - 18), (_x + 6, 1480 - _k - 4)], fill=(90, 130, 90, 50))
for _k in range(3):                 # 曲水 winding stream
    _d.line([(260 + i * 20, 1490 + _k * 10 + 8 * math.sin(i * 0.4)) for i in range(29)], fill=(110, 140, 160, 40), width=3)
MTN_COL = {'night': (28, 30, 38), 'death': (60, 60, 62), 'war': (110, 64, 52), 'fate': (90, 98, 96)}
def draw_background(t, theme):
    """会稽山阴: hills, 茂林修竹 and a winding stream at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(188, 190, 186), (154, 164, 156), MTN_COL.get(theme, (108, 120, 110))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.75))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(BAMBOO)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """白鹅: a small white goose in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=MOCHI + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=MOCHI + (220,), width=3)
        cx, cy = x + sx * 60, y + sy * 70
        d.ellipse((cx - 30, cy - 12, cx + 30, cy + 14), fill=(250, 250, 246, 240))
        d.line((cx + sx * 22, cy - 6, cx + sx * 30, cy - 40), fill=(250, 250, 246, 240), width=8)
        d.ellipse((cx + sx * 30 - 8, cy - 48, cx + sx * 30 + 8, cy - 34), fill=(250, 250, 246, 240))
        d.polygon([(cx + sx * 36, cy - 44), (cx + sx * 48, cy - 40), (cx + sx * 36, cy - 37)], fill=EHUANG + (240,))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def xizhi(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, old=0.0, brush=False, **kw):
    """王羲之: Eastern-Jin gentleman — 小冠 with a gauze 幅巾 trailing, loose sleeves, 坦腹 sash; often holding a brush."""
    b = bow + 10 * old
    up = not kneel and abs(b) < 1 and not kw.get('fall')
    hand = person(A, x, y, h, dir=dir, robe=True, hat='knot', layer=layer, kneel=kneel, bow=b, **kw)
    d = A.d[layer]
    if up:
        d.rectangle((x - 0.05 * h, y - 1.04 * h, x + 0.05 * h, y - 0.96 * h), fill=255)
        A.d['wash'].line((x - dir * 0.04 * h, y - 1.0 * h, x - dir * 0.18 * h, y - 0.82 * h), fill=255, width=max(2, int(0.025 * h)))
        A.d['ehuang'].rectangle((x - 0.08 * h, y - 0.56 * h, x + 0.08 * h, y - 0.52 * h), fill=255)
        d.line((x + dir * 0.04 * h, y - 0.84 * h, x + dir * 0.06 * h, y - 0.72 * h), fill=255, width=max(2, int(0.015 * h)))
        if old > 0.4:
            A.d['wash'].line((x + dir * 0.04 * h, y - 0.84 * h, x + dir * 0.06 * h, y - 0.72 * h), fill=255, width=max(2, int(0.012 * h)))
    if brush and hand:
        hx, hy = hand
        A.d['ehuang'].line((hx, hy, hx + dir * 0.04 * h, hy - 0.14 * h), fill=255, width=max(2, int(0.014 * h)))
        A.d['ink'].polygon([(hx - 0.01 * h, hy), (hx + 0.01 * h, hy), (hx, hy + 0.04 * h)], fill=255)
    return hand

def goose(A, x, y, s, t, dir=1, swim=True):
    bob = 3 * math.sin(t * 3) if swim else 0
    A.d['wash'].ellipse((x - s, y - 0.4 * s + bob, x + s, y + 0.3 * s + bob), fill=255)
    A.d['ink'].ellipse((x - s, y - 0.4 * s + bob, x + s, y + 0.3 * s + bob), outline=120, width=2)
    nx = x + dir * 0.7 * s
    A.d['wash'].line((nx, y - 0.2 * s + bob, nx + dir * 0.2 * s, y - 1.2 * s + bob), fill=255, width=max(4, int(0.22 * s)))
    A.d['wash'].ellipse((nx + dir * 0.2 * s - 0.2 * s, y - 1.4 * s + bob, nx + dir * 0.2 * s + 0.2 * s, y - 1.05 * s + bob), fill=255)
    A.d['ehuang'].polygon([(nx + dir * 0.35 * s, y - 1.3 * s + bob), (nx + dir * 0.65 * s, y - 1.22 * s + bob), (nx + dir * 0.35 * s, y - 1.15 * s + bob)], fill=255)

def pond(A, cx, cy, w, inkiness):
    shade = int(lerp(110, 255, inkiness))
    A.d['ocean' if inkiness < 0.5 else 'mochi'].ellipse((cx - w, cy - 0.3 * w, cx + w, cy + 0.3 * w), fill=shade)
    A.d['ink'].ellipse((cx - w, cy - 0.3 * w, cx + w, cy + 0.3 * w), outline=255, width=6)

def calli(cv, text, cx, cy, t, start, size=90, col=INK, vertical=True):
    """Running script reveal, column by column."""
    im = text_img(text, BRUSH, size, col, vertical=vertical)
    type_in(cv, im, cx, cy, t, start, 0.8)

# ================================================================ chapter card
CH = {16: (0.0, 0.25), 48: (0.25, 0.5), 80: (0.5, 0.75), 112: (0.75, 1.0), 144: (1.0, 1.0)}
def art_pond_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b = CH.get(kb, (0.25, 0.5))
    q = ease_out(u / (1.2 * P))
    pond(A, 540, 1140, 300, lerp(a, b, q))
    if kb == 144:
        goose(A, lerp(320, 760, q), 1130, 50, t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_pond_chapter)
    ink_in(cv, text_img(no, SERIF, 56, MOCHI, 'Black', bleed=False, spacing=12), W / 2, 1310, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1435, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_x_hook_324(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((200, 900, 880, 1260), fill=255)
    A.d['ink'].rectangle((200, 900, 880, 1260), outline=255, width=4)
    n = int(clamp(u / (1.6 * P)) * 28)
    for i in range(n):
        x = 850 - (i // 4) * 90; y = 940 + (i % 4) * 80
        A.d['ink'].rectangle((x - 22, y, x + 22, y + 50), fill=160 + (i * 37) % 90)

def art_x_hook_pond(A, cv, t, u):
    pond(A, 540, 1160, 300, clamp(u / (1.6 * P)))
    ground(A, GROUND)

def art_x_hook_goose(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    waves(A, 1210, t, rows=2, amp=3)
    for j in range(3):
        goose(A, 300 + j * 220, 1220, 40, t + j)

def art_x_hook_tomb(A, cv, t, u):
    A.d['mid'].chord((300, 1080, 780, 1320), 180, 360, fill=230)
    A.d['ehuang'].rectangle((500, 1180, 580, 1240), fill=255)
    ground(A, GROUND)

# ================================================================ 第一回 琅琊王氏
def art_x_birth(A, cv, t, u):
    palace(A, 540, 1300, 340, layer='mid')
    ground(A, GROUND)
    for i in range(4):
        person(A, 200 + i * 80 if i < 2 else 760 + (i - 2) * 80, GROUND, 140, dir=1 if i < 2 else -1, robe=True, hat='knot', arm=40, layer='ink')
    A.flush(cv)
    paste(cv, text_img('琅琊王氏 · 王与马共天下', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('琅琊', 56), 860, 1020, t, t - u + P, rot=6)

def art_x_south(A, cv, t, u):
    river(A, 1240, t, rows=2, amp=4)
    for j in range(4):
        boat(A, lerp(-200, 800, ease_out(u / (3 * P))) - j * 160, 1260, 60, t + j, sail=True)
    A.flush(cv)
    paste(cv, text_img('永嘉之乱 · 衣冠南渡', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('南渡', 56, INK), 860, 1020, t, t - u + P, rot=6)

def art_x_shy(A, cv, t, u):
    ground(A, GROUND)
    for i in range(4):
        person(A, 600 + i * 90, GROUND, 170, dir=-1, robe=True, hat='knot', arm=lerp(40, 120, 0.5 + 0.5 * math.sin(t * 3 + i)), layer='mid')
    xizhi(A, 300, GROUND, 140, dir=1, arm=-8)
    A.flush(cv)
    paste(cv, text_img('幼讷于言 · 人未之奇', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_weishuo(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mochi')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='knot', female=True, kneel=True, arm=90, layer='ink')
    xizhi(A, 320, GROUND, 140, dir=1, kneel=True, arm=90, brush=True)
    A.flush(cv)
    paste(cv, text_img('从卫夫人学书', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('卫铄', 56), 860, 1020, t, t - u + P, rot=6)

def art_x_pond(A, cv, t, u):
    """6-beat set piece: 临池学书 — every day he washes his brush in the pond; the seasons pass; the water slowly turns black."""
    ph = u / P
    ink = clamp(ph / 5)
    pond(A, 640, 1180, 260, ink)
    ground(A, GROUND)
    xizhi(A, 280, GROUND, 180, dir=1, kneel=True, bow=30, arm=120, brush=True)
    season = min(3, int(ph / 1.5))
    for k in range(5):
        A.d[['pink', 'grass', 'yellow', 'wash'][season]].ellipse((160 + k * 180 - 20, 900 + (k % 2) * 40 - 20, 160 + k * 180 + 20, 900 + (k % 2) * 40 + 20), fill=200)
    A.flush(cv)
    yrs = min(20, int(ink * 20) + 1)
    paste(cv, text_img(f'临池学书 · 第{cn_num(yrs)}年', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    paste(cv, text_img('池水尽墨', SERIF, 48, ZHU, 'Black', bleed=False, spacing=8), W / 2, 835, 1, clamp((ph - 4.4) / 0.4))
    note_in(cv, '临池之说语出张芝 后世附会于羲之', t, t - u + P)

def art_x_dongchuang(A, cv, t, u):
    """6-beat set piece: 坦腹东床 — a matchmaker visits the Wang house; every young man stands straight; one lies on the east bed eating, belly bare."""
    ph = u / P
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    for i in range(4):
        person(A, 160 + i * 90, GROUND, 160, dir=1, robe=True, hat='knot', arm=-8, layer='ink')
    A.d['mid'].rectangle((620, GROUND - 60, 900, GROUND), fill=230)
    xizhi(A, 760, GROUND - 60, 160, dir=-1, fall=-82, arm=lerp(-8, 60, 0.5 + 0.5 * math.sin(t * 2)))
    if ph < 3:
        person(A, lerp(1100, 960, ease_out(ph / 1.5)), GROUND, 170, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    lab = '郗鉴遣门生求女婿于王氏' if ph < 2 else ('诸郎咸自矜持 · 唯一郎在东床坦腹卧' if ph < 4 else '正此好 · 遂以女妻之')
    paste(cv, text_img(lab, SERIF, 44, ZHU if ph >= 4 else MOCHI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '东床快婿典出世说新语', t, t - u + P)

def art_x_mishu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='ehuang')
    ground(A, GROUND)
    xizhi(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('起家秘书郎', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

# ================================================================ 第二回 右军
def art_x_yuliang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='武昌', layer='mid', open_=1.0)
    ground(A, GROUND)
    xizhi(A, 540, GROUND, 190, dir=1, arm=60)
    A.flush(cv)
    paste(cv, text_img('庾亮请为参军 · 累迁长史', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_bone(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    person(A, 760, GROUND, 190, dir=-1, robe=True, hat='crown', kneel=True, arm=lerp(40, 100, ease_out(u / 0.5)), layer='ink')
    A.d['wash'].rectangle((420, GROUND - 110, 640, GROUND - 76), fill=255)
    A.flush(cv)
    paste(cv, text_img('飘若浮云 矫若惊龙', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '晋书本传之评', t, t - u + P)

def art_x_youjun(A, cv, t, u):
    for k in range(3):
        A.d['mochi'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    xizhi(A, 540, GROUND - 180, 200, dir=1, arm=lerp(-8, 60, ease_out(u / 0.6)))
    A.flush(cv)
    stamp(cv, seal('右军将军', 46), 860, 1020, t, t - u + P, rot=6)
    paste(cv, text_img('拜右军将军 会稽内史 · 世称王右军', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_kuaiji(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 300), (x + 200, GROUND)], fill=170)
    river(A, 1260, t, rows=2, amp=3)
    xizhi(A, lerp(200, 640, ease_out(u / (2.5 * P))), 1260, 170, dir=1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('会稽山水 · 初渡浙江便有终焉之志', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_famine(A, cv, t, u):
    A.d['dune'].rectangle((60, GROUND - 40, W - 60, GROUND), fill=200)
    ground(A, GROUND)
    for i in range(int(clamp(u / (2 * P)) * 6)):
        A.d['yellow'].ellipse((360 + (i % 3) * 70 - 28, GROUND - 60 - (i // 3) * 40, 360 + (i % 3) * 70 + 28, GROUND - 20 - (i // 3) * 40), fill=255)
    xizhi(A, 160, GROUND, 180, dir=1, arm=90)
    for j in range(4):
        person(A, 640 + j * 90, GROUND, 140, dir=-1, robe=True, hat='knot', bow=30, arm=90, layer='mid')
    A.flush(cv)
    paste(cv, text_img('时东土饥荒 · 辄开仓赈贷', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_fan(A, cv, t, u):
    """6-beat set piece: 书扇 — an old woman sells plain bamboo fans; he writes five characters on each; she is angry; then crowds pay a hundred coins each."""
    ph = u / P
    ground(A, GROUND)
    person(A, 760, GROUND, 160, dir=-1, robe=True, hat='knot', female=True, bow=20, arm=lerp(40, 120, clamp((ph - 2) / 0.3)), layer='mid')
    for i in range(5):
        A.d['ehuang'].pieslice((360 + i * 60 - 40, GROUND - 120, 360 + i * 60 + 40, GROUND - 40), 200, 340, fill=255)
    if ph < 3:
        xizhi(A, 220, GROUND, 180, dir=1, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6)), brush=True)
    else:
        for j in range(5):
            person(A, 200 + j * 80, GROUND, 140, dir=1, robe=True, hat='knot', arm=110, layer='ink')
    A.flush(cv)
    for i in range(5):
        if ph > 0.8 + i * 0.3:
            paste(cv, text_img('王', BRUSH, 34, INK), 360 + i * 60, GROUND - 90, 1, 1)
    lab = '蕺山老姥持六角竹扇卖之' if ph < 2 else ('姥初有愠色' if ph < 3 else '但言是王右军书 以求百钱邪 · 人竞买之')
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 3 else MOCHI, 'Black', bleed=False, spacing=2), W / 2, 760, 1, 1)
    note_in(cv, '事见晋书本传', t, t - u + P)

# ================================================================ 第三回 兰亭
def scene_lanting(cv, t, c, k):
    """8-beat custom scene: 兰亭雅集 — on the third day of the third month 永和九年, forty-one guests sit along the winding stream;
    wine cups float down; whoever the cup stops before must compose a poem; the drunk host takes up his brush and the preface flows out."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    pts = [(80 + i * 30, 1180 + 70 * math.sin(i * 0.35)) for i in range(32)]
    A.d['ocean'].line(pts, fill=200, width=40)
    for k2 in range(5):
        q = (t * 0.12 + k2 / 5) % 1
        i = int(q * 31)
        x, y = pts[i]
        A.d['ehuang'].ellipse((x - 12, y - 8, x + 12, y + 8), fill=255)
    for j in range(8):
        x, y = pts[3 + j * 3]
        sitter(A, x, y - 50 if j % 2 else y + 90, 90, dir=1 if j % 2 else -1, bow=15, layer='mid' if j % 3 else 'ink')
    if ph > 4:
        A.d['wash'].rectangle((360, 760, 720, 1000), fill=255)
        A.d['ink'].rectangle((360, 760, 720, 1000), outline=255, width=3)
        xizhi(A, 300, 1000, 160, dir=1, kneel=True, arm=lerp(80, 120, 0.5 + 0.5 * math.sin(t * 5)), brush=True)
    ground(A, GROUND)
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '兰亭雅集', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=63)
    fx.flush(cv)
    if ph > 4:
        calli(cv, '永和九年 岁在癸丑', 620, 880, t, s0 + 4 * P, size=46)
        calli(cv, '暮春之初 会于会稽', 520, 880, t, s0 + 5 * P, size=46)
        calli(cv, '山阴之兰亭 修禊事也', 420, 880, t, s0 + 6 * P, size=46)
    lab = '永和九年三月三日 · 四十一人修禊兰亭' if ph < 2 else ('曲水流觞 · 一觞一咏' if ph < 4 else '乘醉挥毫 · 兰亭集序')
    paste(cv, text_img(lab, SERIF, 42, ZHU if ph >= 4 else MOCHI, 'Black', bleed=False, spacing=4), W / 2, 575, 1, 1)
    paste(cv, text_img('三百二十四字 · 二十个之字无一雷同', SERIF, 40, DIM, 'Black', bleed=False, spacing=2), W / 2, 1448, 1, clamp((ph - 6) / 0.4))

def art_x_zhi(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    n = min(20, int(clamp(u / (2.5 * P)) * 20) + 1)
    for i in range(n):
        size = 50 + (i * 13) % 30
        im = text_img('之', BRUSH, size, INK if i % 3 else ZHU)
        paste(cv, im, 200 + (i % 5) * 170, 940 + (i // 5) * 110, 1, 1, rot=((i * 23) % 30) - 15)
    paste(cv, text_img(f'二十个之字 · 第{cn_num(n)}个', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, 1)

def art_x_rewrite(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mochi')
    xizhi(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=110, brush=True)
    for i in range(int(clamp(u / (2 * P)) * 5)):
        A.d['wash'].rectangle((440 + i * 30, GROUND - 100 - i * 6, 560 + i * 30, GROUND - 78 - i * 6), fill=255)
    A.flush(cv)
    paste(cv, text_img('他日更书数十百本 · 终不能及之', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '见何延之兰亭记 带传说色彩', t, t - u + P)

def art_x_goose(A, cv, t, u):
    """6-beat set piece: 换鹅 — a Daoist at Shanyin keeps fine geese; he wants them; the price is a copy of the 道德经; he writes, cages the geese, and goes home happy."""
    ph = u / P
    A.d['ocean'].rectangle((60, 1200, W - 60, GROUND + 40), fill=120)
    waves(A, 1210, t, rows=2, amp=3)
    for j in range(4):
        goose(A, 200 + j * 160 + 20 * math.sin(t + j), 1230, 34, t + j)
    if ph < 3:
        person(A, 840, 1200, 170, dir=-1, robe=True, hat='knot', arm=60, layer='mid')
        xizhi(A, 560, 1200, 170, dir=1, kneel=ph > 1.5, arm=lerp(60, 120, 0.5 + 0.5 * math.sin(t * 6)) if ph > 1.5 else 40, brush=ph > 1.5)
    else:
        xizhi(A, lerp(560, 1000, ease_out((ph - 3) / 2.5)), 1200, 170, dir=1, ph=t * 3, arm=60)
        A.d['ink'].rectangle((lerp(620, 1060, ease_out((ph - 3) / 2.5)) - 30, 1080, lerp(620, 1060, ease_out((ph - 3) / 2.5)) + 30, 1140), outline=255, width=3)
    A.flush(cv)
    lab = '山阴道士养好鹅' if ph < 1.5 else ('为写道德经' if ph < 3 else '笼鹅而归 甚以为乐')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 3 else MOCHI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '晋书原作道德经 后世讹为黄庭经', t, t - u + P)

def art_x_xianzhi(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 400, layer='mid')
    person(A, 400, GROUND, 120, dir=1, robe=True, hat='knot', kneel=True, arm=110, layer='ink')
    xizhi(A, 300, GROUND, 190, dir=1, arm=lerp(40, 150, ease_out((u - P) / 0.3)))
    A.flush(cv)
    paste(cv, text_img('从后掣献之笔 不得 · 此儿后当复有大名', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('王献之', 50), 860, 1020, t, t - u + P, rot=6)

def art_x_wood(A, cv, t, u):
    A.d['hulu'].rectangle((300, 1000, 780, 1200), fill=230)
    for k in range(6):
        A.d['ink'].line((300, 1020 + k * 30, 780, 1020 + k * 30), fill=80, width=2)
    q = ease_out(u / (2 * P))
    A.d['ink'].rectangle((420, 1000, 660, 1000 + 120 * q), fill=200)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('入木三分', SERIF, 52, ZHU, 'Black', bleed=False, spacing=10), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '出自张怀瓘书断 带传说色彩', t, t - u + P)

# ================================================================ 第四回 誓墓
def art_x_wangshu(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='mid')
    ground(A, GROUND)
    person(A, 760, GROUND - 30, 190, dir=-1, robe=True, hat='crown', arm=lerp(20, 120, ease_out(u / 0.5)), layer='ink')
    xizhi(A, 380, GROUND, 190, dir=1, bow=20, arm=-8)
    A.flush(cv)
    paste(cv, text_img('素轻王述 · 王述为扬州刺史 检察会稽', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_vow(A, cv, t, u):
    A.d['mid'].chord((380, 1100, 700, 1320), 180, 360, fill=230)
    A.d['ink'].rectangle((610, 1040, 670, 1240), fill=255)
    ground(A, GROUND)
    xizhi(A, 300, GROUND, 180, dir=1, kneel=True, bow=40, arm=100)
    A.flush(cv)
    type_in(cv, text_img('自今之后 敢渝此心 贪冒苟进', SERIF, 44, ZHU, 'Black', bleed=False, spacing=4), W / 2, 760, t, t - u + 0.4, 0.5)
    type_in(cv, text_img('是有无尊之心而不子也', SERIF, 44, INK, 'Black', bleed=False, spacing=4), W / 2, 835, t, t - u + 1.6 * P, 0.5)
    stamp(cv, seal('父母墓前', 44), 860, 1020, t, t - u + P, rot=6)

def art_x_resign(A, cv, t, u):
    for k in range(4):
        x = 160 + k * 260
        A.d['mid'].polygon([(x - 200, GROUND), (x, GROUND - 300), (x + 200, GROUND)], fill=170)
    ground(A, GROUND)
    xizhi(A, lerp(540, 900, ease_out(u / (2.5 * P))), GROUND, 170, dir=1, ph=t * 3, arm=-8, old=0.4)
    A.flush(cv)
    paste(cv, text_img('称病去郡 · 誓不再仕', SERIF, 46, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_mountains(A, cv, t, u):
    for k in range(5):
        x = 140 + k * 200
        A.d['mid'].polygon([(x - 150, GROUND), (x, GROUND - 340), (x + 150, GROUND)], fill=180)
    river(A, 1260, t, rows=2, amp=3)
    boat(A, lerp(200, 840, ease_out(u / (3 * P))), 1270, 80, t, sail=False)
    A.flush(cv)
    paste(cv, text_img('与东土人士尽山水之游 弋钓为娱', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_herbs(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 220, GROUND), (x, GROUND - 380), (x + 220, GROUND)], fill=170)
    ground(A, GROUND)
    xizhi(A, 540, GROUND, 170, dir=1, ph=t * 2, arm=120, old=0.6)
    A.flush(cv)
    paste(cv, text_img('与道士许迈共修服食 · 采药石不远千里', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_letters(A, cv, t, u):
    ground(A, GROUND)
    desk(A, 540, GROUND, 420, layer='mochi')
    xizhi(A, 300, GROUND, 180, dir=1, kneel=True, bow=20, arm=110, brush=True, old=0.6)
    A.flush(cv)
    calli(cv, '快雪时晴', 620, 1000, t, t - u + 0.5 * P, size=60)
    paste(cv, text_img('晚年尺牍 · 快雪时晴帖 丧乱帖', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, clamp(u / 0.4))

def art_x_death(A, cv, t, u):
    A.d['mid'].rectangle((300, 1200, 780, 1260), fill=230)
    A.d['ink'].rectangle((280, 1260, 800, 1290), fill=255)
    xizhi(A, 540, 1200, 220, dir=1, fall=-88, arm=-8)
    lamp(A, 860, GROUND, 60, t, glow=clamp(1 - (u - P) / 1))
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('卒 · 年五十九', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '卒年一说三七九年', t, t - u + P)

# ================================================================ 第五回 书圣
def art_x_taizong(A, cv, t, u):
    palace(A, 540, 1300, 320, layer='ehuang')
    ground(A, GROUND)
    emperor(A, 540, GROUND, 210, dir=1, arm=lerp(40, 120, ease_out(u / 0.5)))
    A.d['wash'].rectangle((660, GROUND - 160, 780, GROUND - 120), fill=255)
    A.flush(cv)
    paste(cv, text_img('唐太宗酷爱右军书 · 亲撰晋书传论', SERIF, 44, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '详察古今 研精篆素 尽善尽美 其惟王逸少乎', t, t - u + P)

def art_x_xiaoyi(A, cv, t, u):
    ground(A, GROUND)
    person(A, 380, GROUND, 180, dir=1, robe=True, hat='knot', arm=lerp(40, 120, ease_out(u / 0.5)), layer='ink')
    person(A, 720, GROUND, 180, dir=-1, robe=True, hat='knot', arm=40, layer='mid')
    A.d['ehuang'].rectangle((520, GROUND - 160, 600, GROUND - 130), fill=255)
    A.flush(cv)
    paste(cv, text_img('萧翼赚兰亭 · 从辩才和尚处取得真迹', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '事出何延之兰亭记 属传说', t, t - u + P)

def art_x_zhaoling(A, cv, t, u):
    """6-beat set piece: 昭陵玉匣 — the emperor's dying wish; the scroll is laid in a jade box and sealed into the tomb under the mountain."""
    ph = u / P
    A.d['mid'].polygon([(160, GROUND), (540, 860), (920, GROUND)], fill=200)
    q = ease_out(clamp(ph / 3))
    A.d['ehuang'].rectangle((470, lerp(1000, 1220, q), 610, lerp(1060, 1280, q)), fill=255)
    A.d['ink'].rectangle((470, lerp(1000, 1220, q), 610, lerp(1060, 1280, q)), outline=255, width=3)
    if ph > 3:
        A.d['mid'].rectangle((440, 1200, 640, 1300), fill=int(255 * clamp((ph - 3) / 1)))
    ground(A, GROUND)
    A.flush(cv)
    lab = '贞观二十三年 太宗崩' if ph < 2 else ('兰亭真迹 随葬昭陵' if ph < 4.5 else '从此人间只见摹本')
    paste(cv, text_img(lab, SERIF, 46, ZHU if ph >= 2 else MOCHI, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '随葬之说出自传说', t, t - u + P)

def art_x_fengcheng(A, cv, t, u):
    ground(A, GROUND)
    A.d['wash'].rectangle((200, 900, 880, 1240), fill=255)
    A.d['ink'].rectangle((200, 900, 880, 1240), outline=255, width=4)
    A.d['red'].rectangle((240, 920, 290, 960), fill=230)
    A.flush(cv)
    calli(cv, '永和九年 岁在癸丑', 800, 1070, t, t - u + 0.3, size=44)
    calli(cv, '暮春之初', 700, 1070, t, t - u + P, size=44)
    paste(cv, text_img('冯承素神龙本 · 最接近原迹的摹本', SERIF, 42, MOCHI, 'Black', bleed=False, spacing=2), W / 2, 830, 1, clamp(u / 0.4))

def art_x_shusheng(A, cv, t, u):
    for k in range(3):
        A.d['mochi'].rectangle((300 + k * 60, GROUND - 60 - k * 60, 780 - k * 60, GROUND - k * 60), fill=230 - k * 20)
    ground(A, GROUND)
    xizhi(A, 540, GROUND - 180, 200, dir=1, arm=60, brush=True)
    A.flush(cv)
    paste(cv, text_img('书圣', SERIF, 56, ZHU, 'Black', bleed=False, spacing=12), W / 2, 830, 1, clamp(u / 0.4))

def art_x_first(A, cv, t, u):
    ground(A, GROUND)
    A.flush(cv)
    calli(cv, '天下第一行书', W / 2, 1060, t, t - u + 0.3, size=90, vertical=False)
    paste(cv, text_img('兰亭集序', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_x_pond2(A, cv, t, u):
    pond(A, 540, 1160, 300, 1.0)
    goose(A, lerp(320, 760, ease_out(u / (2 * P))), 1150, 46, t)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('一池墨水 · 千年书风', SERIF, 48, MOCHI, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))

def art_x_legacy(A, cv, t, u):
    A.d['mid'].rectangle((60, 1380, W - 60, 1440), fill=150)
    goose(A, 860, 1390, 34, t)

def art_x_title(A, cv, t, u):
    pond(A, 820, 1420, 200, 1.0)
    goose(A, 820, 1410, 40, t)
    xizhi(A, 380, 1460, 680, dir=1, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '琅琊王氏'), 48: ('第二回', '右军'), 80: ('第三回', '兰亭'),
            112: ('第四回', '誓墓'), 144: ('第五回', '书圣')}

CARDS = [
    C(0, 2, 'works', 'num', num='三百二十四字', line='天下第一行书', art=art_x_hook_324),
    C(2, 4, 'night', 'num', num='一池清水', line='写成墨黑', art=art_x_hook_pond),
    C(4, 6, 'life', 'num', num='一群白鹅', line='一卷道经', art=art_x_hook_goose),
    C(6, 8, 'death', 'num', num='一个皇帝', line='把它带进坟墓', art=art_x_hook_tomb),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 琅琊王氏
    C(16, 18, 'life', 'chapter'),
    C(18, 22, 'court', 'card', year=303, main='生于琅琊', sub='第一高门', art=art_x_birth),
    C(22, 26, 'war', 'card', year=311, main='衣冠南渡', sub='永嘉之乱', art=art_x_south),
    C(26, 30, 'night', 'card', year=313, main='讷于言', sub='不善言辞的孩子', art=art_x_shy),
    C(30, 34, 'works', 'card', year=315, main='师从卫夫人', sub='书法启蒙', art=art_x_weishuo),
    C(34, 40, 'works', 'card', year=318, main='临池学书', sub='池水尽墨', art=art_x_pond),
    C(40, 44, 'life', 'card', year=320, main='东床快婿', sub='坦腹而卧', art=art_x_dongchuang),
    C(44, 48, 'court', 'card', year=322, main='秘书郎', sub='初入仕途', art=art_x_mishu),
    # ---- 第二回 右军
    C(48, 50, 'court', 'chapter'),
    C(50, 54, 'fate', 'card', year=334, main='庾亮参军', sub='武昌', art=art_x_yuliang),
    C(54, 58, 'works', 'card', year=340, main='飘若浮云', sub='书名渐盛', art=art_x_bone),
    C(58, 62, 'empire', 'card', year=351, main='右军将军', sub='会稽内史', art=art_x_youjun),
    C(62, 66, 'life', 'card', year=351, main='会稽山水', sub='终焉之志', art=art_x_kuaiji),
    C(66, 70, 'court', 'card', year=352, main='开仓赈贷', sub='爱民之官', art=art_x_famine),
    C(70, 76, 'life', 'card', year=352, main='书扇', sub='老妪的扇子', art=art_x_fan),
    C(76, 80, 'works', 'card', year=352, main='入木三分', sub='笔力', art=art_x_wood),
    # ---- 第三回 兰亭
    C(80, 82, 'end', 'chapter'),
    C(82, 90, 'end', 'lanting', year=353),
    C(90, 94, 'works', 'card', year=353, main='二十个之字', sub='无一雷同', art=art_x_zhi),
    C(94, 98, 'night', 'card', year=353, main='终不能及', sub='醒后重写', art=art_x_rewrite),
    C(98, 104, 'life', 'card', year=354, main='写经换鹅', sub='爱鹅', art=art_x_goose),
    C(104, 112, 'court', 'card', year=354, main='掣笔不得', sub='小儿王献之', art=art_x_xianzhi),
    # ---- 第四回 誓墓
    C(112, 114, 'fate', 'chapter'),
    C(114, 118, 'death', 'card', year=355, main='王述', sub='宿怨', art=art_x_wangshu),
    C(118, 122, 'night', 'card', year=355, main='誓墓', sub='不再出仕', art=art_x_vow),
    C(122, 126, 'fate', 'card', year=355, main='辞官', sub='归隐', art=art_x_resign),
    C(126, 130, 'life', 'card', year=356, main='山水之游', sub='弋钓为娱', art=art_x_mountains),
    C(130, 134, 'works', 'card', year=358, main='采药', sub='不远千里', art=art_x_herbs),
    C(134, 140, 'works', 'card', year=360, main='尺牍', sub='快雪时晴', art=art_x_letters),
    C(140, 144, 'death', 'card', year=361, main='王羲之去世', sub='金庭', art=art_x_death),
    # ---- 第五回 书圣
    C(144, 146, 'end', 'chapter'),
    C(146, 150, 'empire', 'card', year=646, main='太宗推崇', sub='尽善尽美', art=art_x_taizong),
    C(150, 154, 'night', 'card', year=646, main='萧翼赚兰亭', sub='一个传说', art=art_x_xiaoyi),
    C(154, 160, 'death', 'card', year=649, main='昭陵玉匣', sub='真迹入土', art=art_x_zhaoling),
    C(160, 164, 'works', 'card', year=649, main='神龙本', sub='冯承素摹', art=art_x_fengcheng),
    C(164, 166, 'empire', 'card', year=649, main='书圣', sub='千古一人', art=art_x_shusheng),
    C(166, 168, 'works', 'card', year=649, main='天下第一', sub='行书', art=art_x_first),
    C(168, 170, 'end', 'card', year=649, main='墨池', sub='千年书风', art=art_x_pond2),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='陆拾叁', col=MOCHI, acc=EHUANG, born=303, died=361, age0=302,
    born_lab='303年', died_lab='361年', years_txt='公元303 — 361',
    hook_q='一篇醉后草稿 · 为什么成了天下第一行书？',
    name_line='王羲之 · 字逸少', name='王羲之', seal='书圣', title_art=art_x_title,
    q1='千古书圣？', q2='名门公子？',
    end_art=art_x_legacy, end_big='兰亭', end_seal='书圣',
    end_l1='真迹早已不知去向', end_l2='一笔一画却流传至今',
    end_brush='飘若浮云矫若惊龙', end_ask='你练过王羲之的字吗？评论区聊聊', next='花木兰'),
    scenes=dict(chapter=scene_chapter, lanting=scene_lanting))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
