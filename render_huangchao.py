"""千古人物志 · 第壹佰零壹集 · 黄巢 (?–884)
Look: 菊黄 + 血红, little chrysanthemum corners, the walls of 长安 behind.
Chapter card: 菊 — a chrysanthemum that opens a little more each chapter; in the last chapter its petals fall.
Set pieces: custom 8-beat scene 'chongtian' (入长安 满城尽带黄金甲), 6-beat 落第赋菊, 6-beat 转战万里, 6-beat 洗城, 6-beat 狼虎谷.
Birth year unknown (no_age).
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
import render_yanzhenqing as Yz     # engine + helpers (previous episode)
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
from render_simayi import emperor
from render_sunwu import army, banner
from render_zhuxi import book
from render_quyuan import river

F.RIPPLE = False
JUHUANG = (210, 164, 40)            # 菊黄
XUEHONG = (150, 40, 36)             # 血红
JUHUANG_D = (150, 110, 20)          # 菊黄 (text)
S.LAYERS.append(('juhuang', JUHUANG, 0.9, 1.0))
S.LAYERS.append(('xuehong', XUEHONG, 0.9, 1.0))
S.LAYERS.sort(key=lambda l: l[0] in ('ink', 'red'))

WM = dict(hook='菊', life='黄', court='唐', night='秋', war='战', empire='齐', works='诗', fate='落', death='亡', end='菊')
for k, wm in WM.items():
    G.THEMES[k]['wm'] = wm
for k in ('hook', 'life', 'works', 'end', 'night'):
    G.THEMES[k]['part'] = 'petal'
for k in ('court', 'empire'):
    G.THEMES[k]['part'] = 'gold'
for k in ('death', 'fate', 'war'):
    G.THEMES[k]['part'] = 'ash'
G.THEMES['works']['sun'] = None
G.THEMES['war']['sun'] = ((150, 140, 130), 220, (W * 0.5, 760))
G.THEMES['empire']['sun'] = (JUHUANG, 220, (W * 0.5, 820))
G.THEMES['end']['sun'] = (JUHUANG, 170, (W * 0.5, 720))
G.THEMES['night']['sun'] = None
G.base_bg.cache_clear()

STREAM = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_d = ImageDraw.Draw(STREAM)
for _x in (60, 900):                # wall stubs at the margins
    _d.rectangle((_x, 1350, _x + 120, 1420), fill=(120, 110, 96, 60))
    for _k in range(4):
        _d.rectangle((_x + _k * 32, 1334, _x + _k * 32 + 18, 1350), fill=(120, 110, 96, 60))
for _k in range(3):
    _d.line((200, 1424 + _k * 12, 880, 1424 + _k * 12), fill=JUHUANG + (40 - _k * 10,), width=2)
MTN_COL = {'night': (30, 28, 26), 'death': (62, 56, 54), 'war': (112, 64, 50), 'fate': (98, 92, 84)}
def draw_background(t, theme):
    """关中: dry hills, wall stubs at the margins."""
    th = G.THEMES[theme]
    canvas = G.base_bg(theme).copy()
    wm = text_img(th['wm'], WILD, 950, INK, bleed=False)
    paste(canvas, wm, W / 2 + 30 * math.sin(t * 0.3), 900, 1.0 + 0.02 * math.sin(t * 0.5), 0.06)
    cols = [(200, 194, 182), (170, 160, 140), MTN_COL.get(theme, (124, 112, 92))]
    for i, (m, ys) in enumerate(G.MTN):
        off = int(200 + t * 6 * (i + 1)) % 400
        layer = Image.new('RGBA', (W, H), cols[i] + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)).point(lambda v: int(min(255, v * th['mtn'] * 0.72))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(STREAM)
    return canvas
G.draw_background = draw_background

def draw_frame_border(canvas):
    """菊: a small chrysanthemum head in each corner."""
    d = ImageDraw.Draw(canvas)
    m = 44
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line((x, y, x + sx * 180, y), fill=XUEHONG + (220,), width=3); d.line((x, y, x, y + sy * 180), fill=XUEHONG + (220,), width=3)
        cx, cy = x + sx * 50, y + sy * 50
        for k in range(12):
            a = k * math.pi / 6
            d.line((cx, cy, cx + 22 * math.cos(a), cy + 22 * math.sin(a)), fill=JUHUANG + (235,), width=5)
        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(140, 90, 20, 240))
G.draw_frame_border = draw_frame_border

# ================================================================ primitives
def huang_(A, x, y, h, dir=1, layer='ink', kneel=False, bow=0, armour=False, **kw):
    """黄巢: a big, rough man — as a salt trader a short tunic and headcloth; as a rebel king, helmet and a golden cape."""
    hand = person(A, x, y, h, dir=dir, robe=not armour, hat='helmet' if armour else 'knot', layer=layer, kneel=kneel, bow=bow, **kw)
    if kw.get('fall'):
        return hand
    top = y - (0.48 if kneel else 0.78) * h
    if armour:
        A.d['juhuang'].polygon([(x - dir * 0.02 * h, top), (x - dir * 0.12 * h, top), (x - dir * 0.36 * h, y - 0.06 * h), (x - dir * 0.1 * h, y - 0.06 * h)], fill=235)
        A.d['juhuang'].rectangle((x - 0.1 * h, top + 0.04 * h, x + 0.1 * h, top + 0.3 * h), fill=200)
    else:
        A.d['juhuang'].polygon([(x - 0.1 * h, top), (x + 0.1 * h, top), (x + 0.13 * h, y - 0.05 * h), (x - 0.13 * h, y - 0.05 * h)], fill=110)
    return hand

def gold_army(A, x0, y, n, dir=1, t=0.0, march=True, h=100):
    for i in range(n):
        x = x0 + i * h * 0.45 * dir
        person(A, x, y, h, dir=dir, ph=(t * 6 + i) if march else None, robe=False, hat='helmet', spear=True, arm=40, layer='ink')
        A.d['juhuang'].rectangle((x - 0.1 * h, y - 0.74 * h, x + 0.1 * h, y - 0.46 * h), fill=230)

def chrys(A, cx, cy, r, bloom, fall=0.0, t=0.0):
    """菊: a stem and a chrysanthemum head of rays; `bloom` 0..1 opens it, `fall` scatters petals downward."""
    A.d['grass'].line((cx, cy, cx + 10, cy + 2.6 * r), fill=255, width=max(4, int(0.06 * r)))
    A.d['grass'].ellipse((cx + 10 - 0.5 * r, cy + 1.4 * r, cx + 10 + 0.1 * r, cy + 1.7 * r), fill=255)
    rng = random.Random(101)
    n = 36
    for k in range(n):
        a = k * 2 * math.pi / n + rng.uniform(-0.05, 0.05)
        rr = r * (0.35 + 0.65 * bloom) * (0.8 + 0.2 * rng.random())
        if fall > 0 and rng.random() < fall:
            dy = fall * 2.4 * r * rng.random() + 20 * math.sin(t + k)
            px = cx + rr * math.cos(a) + 40 * math.sin(k)
            A.d['juhuang'].ellipse((px - 8, cy + rr * math.sin(a) + dy - 4, px + 8, cy + rr * math.sin(a) + dy + 4), fill=200)
            continue
        A.d['juhuang'].line((cx + 0.15 * r * math.cos(a), cy + 0.15 * r * math.sin(a), cx + rr * math.cos(a), cy + rr * math.sin(a)), fill=255, width=max(4, int(0.08 * r)))
    A.d['zhemo'].ellipse((cx - 0.16 * r, cy - 0.16 * r, cx + 0.16 * r, cy + 0.16 * r), fill=255)

def route(A, cx, cy, s, p):
    """转战万里: a stylised map — the Yellow River and Yangtze, a red route looping south to 广州 and back north to 长安."""
    A.d['wash'].rectangle((cx - s, cy - 0.8 * s, cx + s, cy + 0.8 * s), fill=255)
    A.d['ink'].rectangle((cx - s, cy - 0.8 * s, cx + s, cy + 0.8 * s), outline=200, width=4)
    A.d['ocean'].line([(cx - s, cy - 0.45 * s), (cx - 0.3 * s, cy - 0.5 * s), (cx + 0.2 * s, cy - 0.35 * s), (cx + s, cy - 0.45 * s)], fill=200, width=6)
    A.d['ocean'].line([(cx - s, cy + 0.05 * s), (cx - 0.2 * s, cy + 0.1 * s), (cx + 0.3 * s, cy), (cx + s, cy + 0.1 * s)], fill=200, width=6)
    pts = [(cx + 0.35 * s, cy - 0.38 * s), (cx + 0.55 * s, cy - 0.1 * s), (cx + 0.6 * s, cy + 0.3 * s), (cx + 0.4 * s, cy + 0.6 * s),
           (cx + 0.05 * s, cy + 0.7 * s), (cx - 0.2 * s, cy + 0.4 * s), (cx - 0.1 * s, cy + 0.05 * s), (cx + 0.05 * s, cy - 0.3 * s), (cx - 0.55 * s, cy - 0.4 * s)]
    n = max(2, int(len(pts) * p) + 1)
    seg = pts[:min(n, len(pts))]
    A.d['xuehong'].line(seg, fill=255, width=7)
    for name, (px, py) in (('长安', pts[-1]), ('广州', pts[4]), ('曹州', pts[0])):
        A.d['ink'].ellipse((px - 10, py - 10, px + 10, py + 10), fill=255)

# ================================================================ chapter card
CH = {16: (0.0, 0.2, 0.0), 48: (0.2, 0.5, 0.0), 80: (0.5, 0.8, 0.0), 112: (0.8, 1.0, 0.0), 144: (1.0, 1.0, 0.8)}
def art_chrys_chapter(A, cv, t, u):
    kb = int(round((t - u - G.B0) / P))
    a, b, f = CH.get(kb, (0.2, 0.5, 0.0))
    q = ease_out(u / (1.4 * P))
    chrys(A, 540, 960, 170, lerp(a, b, q), fall=f * q, t=t)

def scene_chapter(cv, t, c, k):
    s0 = bt(c[0])
    no, title = CHAPTERS[c[0]]
    stage(cv, t, c, art_chrys_chapter)
    ink_in(cv, text_img(no, SERIF, 56, XUEHONG, 'Black', bleed=False, spacing=12), W / 2, 1330, t, s0, dur=0.25, settle=1.0)
    fx = Art()
    chars_in(cv, fx, title, BRUSH, 160, INK, W / 2, 1450, t, s0 + 0.1, stagger=0.08, seed=c[0])
    fx.flush(cv)

# ================================================================ hooks
def art_h_hook_chrys(A, cv, t, u):
    chrys(A, 540, 1000, 180, clamp(u / (1.4 * P)), t=t)

def art_h_hook_salt(A, cv, t, u):
    ground(A, GROUND)
    huang_(A, lerp(300, 700, ease_out(u / (2 * P))), GROUND, 220, dir=1, ph=t * 3, load=True, arm=-8)

def art_h_hook_city(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=1.0)
    ground(A, GROUND)
    gold_army(A, lerp(-200, 300, ease_out(u / (2 * P))), GROUND, 8, dir=1, t=t, h=110)

def art_h_hook_end(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 260), (x + 240, GROUND)], fill=150)
    ground(A, GROUND)
    banner(A, 540, GROUND, 300, t, layer='juhuang', fallen=clamp(u / (1.6 * P)))

# ================================================================ 第一回 落第
def art_h_birth(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 180), (x + 240, GROUND)], fill=130)
    A.d['wash'].rectangle((420, GROUND - 140, 660, GROUND), fill=255)
    A.d['ink'].polygon([(400, GROUND - 140), (680, GROUND - 140), (540, GROUND - 200)], fill=255)
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('曹州冤句人 世代贩卖私盐', SERIF, 48, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '生年不详', t, t - u + P)

def art_h_salt(A, cv, t, u):
    ground(A, GROUND)
    for k in range(3):
        person(A, lerp(-100, 600, ease_out(u / (3 * P))) + k * 140, GROUND, 170, dir=1, ph=t * 3 + k, robe=False, hat='knot', load=True, arm=-8, layer='ink' if k == 1 else 'mid')
    A.flush(cv)
    paste(cv, text_img('私盐贩子 结交江湖豪杰', SERIF, 50, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '唐代盐税极重 私盐利厚而风险大', t, t - u + P)

def art_h_ride(A, cv, t, u):
    ground(A, GROUND)
    rider(A, lerp(200, 800, ease_out(u / (3 * P))), GROUND, 160, dir=1, ph=t * 6)
    A.flush(cv)
    paste(cv, text_img('善骑射 粗通笔墨', SERIF, 52, JUHUANG_D, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_h_luodi(A, cv, t, u):
    """6-beat set piece: 落第赋菊 — he fails the 进士 exam again and again; he writes the chrysanthemum poem."""
    ph = u / P
    ground(A, GROUND)
    if ph < 2.5:
        palace(A, 540, 1300, 300, layer='mid')
        huang_(A, lerp(540, 200, clamp(ph / 2.5)), GROUND, 200, dir=-1, ph=t * 2, arm=-8)
        lab, col = '屡试进士 屡次落第', JUHUANG_D
    else:
        chrys(A, 760, 980, 120, clamp((ph - 2.5) / 1.5), t=t)
        huang_(A, 360, GROUND, 210, dir=1, arm=60)
        lab, col = '待到秋来九月八 我花开后百花杀', XUEHONG
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 46, col, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '此诗相传为黄巢所作 最早见于宋人笔记', t, t - u + 2.5 * P)

def art_h_poem2(A, cv, t, u):
    chrys(A, 540, 1000, 150, 1.0, t=t)
    A.flush(cv)
    paste(cv, text_img('冲天香阵透长安', SERIF, 50, XUEHONG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('满城尽带黄金甲', SERIF, 50, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_h_famine(A, cv, t, u):
    ground(A, GROUND)
    for k in range(10):
        A.d['zhemo'].line((120 + k * 90, GROUND, 140 + k * 90 + 20 * (k % 3), GROUND - 14), fill=200, width=3)
    for k in range(4):
        person(A, 240 + k * 180, GROUND, 160, dir=1, robe=False, hat='knot', bow=40, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('关东大旱 官府照样催租', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '民间流离 盗贼蜂起', t, t - u + P)

# ================================================================ 第二回 冲天
def art_h_rise(A, cv, t, u):
    ground(A, GROUND)
    for k in range(min(8, int(u / (0.3 * P)) + 1)):
        person(A, 160 + k * 100, GROUND, 150, dir=1, robe=False, hat='knot', spear=True, arm=60, layer='mid')
    huang_(A, 860, GROUND, 220, dir=-1, arm=140)
    A.flush(cv)
    paste(cv, text_img('响应王仙芝 聚众起兵', SERIF, 50, XUEHONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_title2(A, cv, t, u):
    ground(A, GROUND)
    banner(A, 760, GROUND, 360, t, layer='juhuang')
    huang_(A, 460, GROUND, 230, dir=1, armour=True, arm=60)
    A.flush(cv)
    paste(cv, text_img('王仙芝战死 他自号冲天大将军', SERIF, 46, XUEHONG, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    stamp(cv, seal('冲天', 56), 860, 1020, t, t - u + P, rot=6)

def art_h_route(A, cv, t, u):
    """6-beat set piece: 转战万里 — avoiding strongholds, his army cuts a seven-hundred-li road over the mountains, takes 广州, then turns north."""
    ph = u / P
    route(A, 540, 1100, 380, clamp(ph / 5.5))
    A.flush(cv)
    if ph < 2:
        lab = '避实就虚 渡江南下'
    elif ph < 4:
        lab = '开山路七百里 直入福建 攻破广州'
    else:
        lab = '回师北上 横扫江淮'
    paste(cv, text_img(lab, SERIF, 46, JUHUANG_D, 'Black', bleed=False, spacing=4), W / 2, 760, 1, 1)
    note_in(cv, '流动作战 转战大半个中国', t, t - u + P)

def art_h_canton(A, cv, t, u):
    A.d['ocean'].rectangle((60, 1240, W - 60, GROUND + 40), fill=150)
    waves(A, 1250, t, rows=2, amp=4)
    city_wall(A, 160, 920, 1080, gate_x=540, label='广州', layer='mid', open_=1.0)
    flames(A, 540, 1080, 620, 220, t, n=6, seed=879, smoke=True)
    A.flush(cv)
    paste(cv, text_img('广州城破 大肆屠掠', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '阿拉伯史料称外商死者十余万 数字或有夸大', t, t - u + P)

def art_h_north(A, cv, t, u):
    ground(A, GROUND)
    gold_army(A, lerp(-300, 300, ease_out(u / (3 * P))), GROUND, 10, dir=1, t=t, h=100)
    A.flush(cv)
    paste(cv, text_img('号称六十万大军 渡淮北上', SERIF, 48, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '兵数为史书所记 或有夸张', t, t - u + P)

# ================================================================ 第三回 长安
def art_h_luoyang(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='洛阳', layer='mid', open_=1.0)
    ground(A, GROUND)
    gold_army(A, 160, GROUND, 6, dir=1, t=t, h=100)
    A.flush(cv)
    paste(cv, text_img('攻破东都洛阳 叩关潼关', SERIF, 48, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def art_h_flee(A, cv, t, u):
    for k in range(3):
        x = 260 + k * 280
        A.d['mid'].polygon([(x - 240, GROUND), (x, GROUND - 280), (x + 240, GROUND)], fill=140)
    ground(A, GROUND)
    emperor(A, lerp(700, 200, ease_out(u / (3 * P))), GROUND, 190, dir=-1, ph=t * 3, arm=-8)
    A.flush(cv)
    paste(cv, text_img('唐僖宗仓皇出逃 奔往蜀中', SERIF, 48, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))

def scene_chongtian(cv, t, c, k):
    """8-beat custom scene: 冲天 — the rebel host pours through the gates of 长安 in golden armour; he rides in; crowds line the streets;
    he takes the throne in 含元殿 and names his state 大齐."""
    s0 = bt(c[0])
    ph = (t - s0) / P
    A = Art(); beat_fx(A, t)
    if ph < 4:
        city_wall(A, 100, 980, 1040, gate_x=540, label='长安', layer='mid', open_=1.0)
        ground(A, GROUND)
        gold_army(A, lerp(-400, 600, clamp(ph / 4)), GROUND, 14, dir=1, t=t, h=100)
        for kk in range(6):
            banner(A, lerp(-300, 700, clamp(ph / 4)) + kk * 70, GROUND - 90, 160, t, layer='juhuang')
        lab = '满城尽带黄金甲' if ph >= 2 else '大军开进长安'
        col = JUHUANG_D if ph < 2 else XUEHONG
    else:
        palace(A, 540, 1300, 340, layer='juhuang')
        ground(A, GROUND)
        huang_(A, 540, GROUND, 230, dir=1, armour=True, arm=lerp(-8, 120, clamp((ph - 5) / 0.5)))
        for kk in range(6):
            person(A, 140 + kk * 70 if kk < 3 else 760 + (kk - 3) * 70, GROUND, 140, dir=1 if kk < 3 else -1, robe=False, hat='helmet', kneel=True, bow=20, arm=-8, layer='mid')
        lab, col = '含元殿即位 国号大齐', XUEHONG
    A.flush(cv)
    fx = Art()
    chars_in(cv, fx, '冲天', BRUSH, 150, INK, W / 2, 440, t, s0, stagger=0.06, seed=101)
    fx.flush(cv)
    paste(cv, text_img(lab, SERIF, 48, col, 'Black', bleed=False, spacing=6), W / 2, 575, 1, 1)
    note_in(cv, '他当年的菊花诗 竟成了谶语', t, s0 + 2 * P)

def art_h_promise(A, cv, t, u):
    ground(A, GROUND)
    huang_(A, 360, GROUND, 210, dir=1, armour=True, arm=60)
    for k in range(4):
        person(A, 560 + k * 100, GROUND, 150, dir=-1, robe=False, hat='knot', arm=60, layer='mid')
    A.flush(cv)
    paste(cv, text_img('起初宣告 黄王起兵 本为百姓', SERIF, 46, JUHUANG_D, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '向贫民分发财物', t, t - u + P)

def art_h_xicheng(A, cv, t, u):
    """6-beat set piece: 洗城 — the officials and nobles are slaughtered; when the people help the returning 唐 army he orders the city washed in blood."""
    ph = u / P
    palace(A, 540, 1300, 340, collapse=clamp((ph - 2) / 3) * 0.5, layer='mid')
    flames(A, 540, 1200, 640, 260 * clamp(ph / 2), t, n=7, seed=881, smoke=True)
    ground(A, GROUND)
    A.flush(cv)
    if ph < 3:
        lab = '内库烧为锦绣灰'
    else:
        lab = '天街踏尽公卿骨'
    paste(cv, text_img(lab, SERIF, 54, XUEHONG, 'Black', bleed=False, spacing=10), W / 2, 760, 1, 1)
    note_in(cv, '韦庄 秦妇吟 百姓助官军后 黄巢下令洗城', t, t - u + P)

# ================================================================ 第四回 败亡
def art_h_zhuwen(A, cv, t, u):
    ground(A, GROUND)
    person(A, lerp(540, 900, ease_out(u / (3 * P))), GROUND, 210, dir=1, ph=t * 2, robe=False, hat='helmet', arm=-8, layer='ink')
    A.flush(cv)
    paste(cv, text_img('大将朱温叛变降唐', SERIF, 50, ZHU, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '后来正是朱温灭了唐朝', t, t - u + P)

def art_h_shatuo(A, cv, t, u):
    ground(A, GROUND)
    for k in range(4):
        rider(A, lerp(1100, 600, ease_out(u / (3 * P))) + k * 120, GROUND, 130, dir=-1, ph=t * 6 + k)
    A.flush(cv)
    paste(cv, text_img('李克用沙陀骑兵南下', SERIF, 50, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '号称鸦儿军', t, t - u + P)

def art_h_leave(A, cv, t, u):
    city_wall(A, 160, 920, 1080, gate_x=540, label='长安', layer='mid', open_=1.0)
    flames(A, 540, 1080, 600, 160, t, n=4, seed=883, smoke=True)
    ground(A, GROUND)
    gold_army(A, lerp(500, 1100, ease_out(u / (3 * P))), GROUND, 6, dir=1, t=t, h=100)
    A.flush(cv)
    paste(cv, text_img('兵败退出长安', SERIF, 52, ZHU, 'Black', bleed=False, spacing=8), W / 2, 830, 1, clamp(u / 0.4))

def art_h_langhu(A, cv, t, u):
    """6-beat set piece: 狼虎谷 — chased east into the mountains of 泰山; his last men scatter; he dies in 狼虎谷."""
    ph = u / P
    for k in range(3):
        x = 220 + k * 320
        A.d['mid'].polygon([(x - 260, GROUND), (x, GROUND - 400), (x + 260, GROUND)], fill=160)
    ground(A, GROUND)
    if ph < 3:
        huang_(A, lerp(900, 540, clamp(ph / 3)), GROUND, 200, dir=-1, ph=t * 3, armour=True, arm=-8)
        for kk in range(max(0, 4 - int(ph))):
            person(A, 700 + kk * 70, GROUND, 140, dir=-1, robe=False, hat='helmet', arm=-8, layer='mid')
        lab = '一路东逃 部众离散'
    else:
        banner(A, 700, GROUND, 260, t, layer='juhuang', fallen=clamp((ph - 3) / 1.2))
        huang_(A, 540, GROUND, 200, dir=-1, armour=True, kneel=True, bow=20, arm=-8)
        lab = '死于泰山狼虎谷'
    A.flush(cv)
    paste(cv, text_img(lab, SERIF, 50, XUEHONG, 'Black', bleed=False, spacing=6), W / 2, 760, 1, 1)
    note_in(cv, '一说自刎 一说为外甥林言所杀', t, t - u + 3 * P)

# ================================================================ 第五回 余波
def art_h_tangfall(A, cv, t, u):
    palace(A, 540, 1300, 340, collapse=clamp(u / (2 * P)), layer='mid')
    ground(A, GROUND)
    A.flush(cv)
    paste(cv, text_img('二十三年后 朱温篡唐 唐朝灭亡', SERIF, 46, ZHU, 'Black', bleed=False, spacing=4), W / 2, 830, 1, clamp(u / 0.4))
    note_in(cv, '中国进入五代十国', t, t - u + P)

def art_h_qinfu(A, cv, t, u):
    ground(A, GROUND)
    scroll(A, 540, 1100, 520, 300, ease_out(u / (1.2 * P)), layer='wash')
    A.flush(cv)
    paste(cv, text_img('秦妇吟', SERIF, 64, INK, 'Black', bleed=False, spacing=12), W / 2, 1100, 1, clamp((u - 0.8 * P) / 0.4))
    paste(cv, text_img('韦庄写下乱中长安的惨状', SERIF, 48, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    note_in(cv, '长期失传 二十世纪在敦煌重现', t, t - u + P)

def art_h_eval(A, cv, t, u):
    ground(A, GROUND)
    huang_(A, 540, GROUND, 280, dir=1, armour=True, arm=-8, layer='mid')
    A.flush(cv)
    paste(cv, text_img('他打碎了一个腐朽的王朝', SERIF, 48, JUHUANG_D, 'Black', bleed=False, spacing=6), W / 2, 760, 1, clamp(u / 0.4))
    paste(cv, text_img('也让无数百姓死于战火', SERIF, 48, XUEHONG, 'Black', bleed=False, spacing=6), W / 2, 830, 1, clamp((u - P) / 0.4))

def art_h_end(A, cv, t, u):
    chrys(A, 540, 1000, 170, 1.0, fall=0.7, t=t)
    A.flush(cv)
    paste(cv, text_img('我花开后百花杀', SERIF, 52, XUEHONG, 'Black', bleed=False, spacing=8), W / 2, 760, 1, clamp(u / 0.4))

def art_h_legacy(A, cv, t, u):
    chrys(A, 860, 1360, 40, 1.0, t=t)

def art_h_title(A, cv, t, u):
    chrys(A, 820, 1080, 110, 1.0, t=t)
    A.d['mid'].rectangle((60, 1440, W - 60, 1470), fill=150)
    huang_(A, 380, 1460, 680, dir=1, armour=True, arm=lerp(-5, 40, ease_out(u / (2 * P))))

# ================================================================ script
CHAPTERS = {16: ('第一回', '落第'), 48: ('第二回', '冲天'), 80: ('第三回', '长安'),
            112: ('第四回', '败亡'), 144: ('第五回', '余波')}

CARDS = [
    C(0, 2, 'works', 'num', num='一首菊花诗', line='写尽了落榜的不甘', art=art_h_hook_chrys),
    C(2, 4, 'life', 'num', num='私盐贩子', line='考了几次都落榜', art=art_h_hook_salt),
    C(4, 6, 'empire', 'num', num='黄金甲', line='后来真的开进了长安', art=art_h_hook_city),
    C(6, 8, 'death', 'num', num='大齐皇帝', line='只做了两年多', art=art_h_hook_end),
    C(8, 12, 'hook', 'title'),
    C(12, 16, 'hook', 'question', art=L.art_judge),
    # ---- 第一回 落第
    C(16, 18, 'fate', 'chapter'),
    C(18, 22, 'life', 'card', year=830, main='曹州冤句', sub='盐商之家', note='年份无考', art=art_h_birth),
    C(22, 26, 'works', 'card', year=850, main='贩盐', sub='结交豪杰', note='年份约略', art=art_h_salt),
    C(26, 30, 'war', 'card', year=855, main='善骑射', sub='粗通笔墨', note='年份约略', art=art_h_ride),
    C(30, 36, 'fate', 'card', year=860, main='落第', sub='屡试不中', note='年份约略', art=art_h_luodi),
    C(36, 42, 'night', 'card', year=860, main='黄金甲', sub='菊花诗', note='作年不详', art=art_h_poem2),
    C(42, 48, 'death', 'card', year=874, main='大旱', sub='关东饥荒', art=art_h_famine),
    # ---- 第二回 冲天
    C(48, 50, 'war', 'chapter'),
    C(50, 54, 'war', 'card', year=875, main='起兵', sub='响应王仙芝', art=art_h_rise),
    C(54, 58, 'empire', 'card', year=878, main='冲天大将军', sub='自立名号', art=art_h_title2),
    C(58, 64, 'life', 'card', year=878, main='转战万里', sub='渡江南下', art=art_h_route),
    C(64, 70, 'death', 'card', year=879, main='广州', sub='屠掠', art=art_h_canton),
    C(70, 80, 'war', 'card', year=880, main='北上', sub='渡淮', art=art_h_north),
    # ---- 第三回 长安
    C(80, 82, 'empire', 'chapter'),
    C(82, 86, 'war', 'card', year=880, main='洛阳', sub='叩关潼关', art=art_h_luoyang),
    C(86, 90, 'fate', 'card', year=880, main='僖宗出逃', sub='奔蜀', art=art_h_flee),
    C(90, 98, 'empire', 'chongtian', year=881),
    C(98, 104, 'life', 'card', year=881, main='本为百姓', sub='起初的宣告', art=art_h_promise),
    C(104, 112, 'death', 'card', year=881, main='洗城', sub='秦妇吟', art=art_h_xicheng),
    # ---- 第四回 败亡
    C(112, 114, 'death', 'chapter'),
    C(114, 120, 'fate', 'card', year=882, main='朱温降唐', sub='众叛亲离', art=art_h_zhuwen),
    C(120, 126, 'war', 'card', year=883, main='沙陀骑兵', sub='李克用', art=art_h_shatuo),
    C(126, 132, 'night', 'card', year=883, main='退出长安', sub='兵败', art=art_h_leave),
    C(132, 144, 'death', 'card', year=884, main='狼虎谷', sub='败亡', art=art_h_langhu),
    # ---- 第五回 余波
    C(144, 146, 'end', 'chapter'),
    C(146, 152, 'court', 'card', year=907, main='唐亡', sub='朱温篡唐', art=art_h_tangfall),
    C(152, 158, 'works', 'card', year=1900, main='秦妇吟', sub='敦煌重现', art=art_h_qinfu),
    C(158, 164, 'fate', 'card', year=1900, main='功过', sub='难以评说', art=art_h_eval),
    C(164, 170, 'end', 'card', year=1900, main='百花杀', sub='菊花诗', art=art_h_end),
    C(170, 999, 'end', 'end'),
]

epkit.setup(CARDS, CHAPTERS, dict(
    ep='壹佰零壹', col=XUEHONG, acc=JUHUANG, born=830, died=884, age0=829, no_age=True,
    born_lab='生年不详', died_lab='884年', years_txt='生年不详 — 公元884',
    hook_q='落榜书生写了一首菊花诗 · 后来真的带兵杀进了长安？',
    name_line='黄巢 · 冲天大将军', name='黄巢', seal='冲天', title_art=art_h_title,
    q1='起义英雄？', q2='乱世屠夫？',
    end_art=art_h_legacy, end_big='黄金甲', end_seal='黄巢',
    end_l1='他打碎了一个腐朽的王朝', end_l2='也让无数百姓死于战火',
    end_brush='冲天香阵', end_ask='你怎么评价黄巢？评论区聊聊', next='秦桧'),
    scenes=dict(chapter=scene_chapter, chongtian=scene_chongtian))

render = L.render
if __name__ == '__main__':
    epkit.main(render)
