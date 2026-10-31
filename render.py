# 秦始皇 · 千古一帝 —— 纯代码卡点视频 (1080x1920, 30fps)
import math, os, sys, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 28.0
BPM = 105.6
P = 60 / BPM
B0 = 0.4
def bt(k): return B0 + k * P

FD = os.path.join(HERE, 'fonts')
BRUSH = os.path.join(FD, 'MaShanZheng-Regular.ttf')
WILD = os.path.join(FD, 'ZhiMangXing-Regular.ttf')
SERIF = os.path.join(FD, 'NotoSerifSC.ttf')

@lru_cache(None)
def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        f.set_variation_by_name(weight)
    return f

# ---------------------------------------------------------------- easing
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_back(x, s=2.2):
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def lerp(a, b, t): return a + (b - a) * t

# ---------------------------------------------------------------- themes
THEMES = {
    'hook':   dict(top=(18, 4, 6),   bot=(60, 8, 10),  acc=(230, 40, 40),  ember=(255, 90, 40),  mtn=(30, 6, 8),   wm='秦'),
    'life':   dict(top=(22, 16, 10), bot=(70, 48, 26), acc=(225, 175, 90), ember=(255, 190, 110), mtn=(36, 26, 16), wm='政'),
    'war':    dict(top=(30, 2, 2),   bot=(120, 14, 6), acc=(255, 60, 30),  ember=(255, 120, 30), mtn=(40, 4, 4),   wm='戰'),
    'empire': dict(top=(26, 16, 2),  bot=(110, 72, 10), acc=(255, 210, 90), ember=(255, 220, 120), mtn=(44, 28, 6), wm='皇'),
    'works':  dict(top=(8, 14, 22),  bot=(40, 58, 74), acc=(170, 210, 235), ember=(200, 230, 255), mtn=(14, 22, 30), wm='城'),
    'death':  dict(top=(10, 10, 12), bot=(48, 48, 52), acc=(200, 200, 205), ember=(190, 190, 190), mtn=(18, 18, 20), wm='亡'),
    'end':    dict(top=(6, 4, 2),    bot=(40, 22, 6),  acc=(240, 196, 100), ember=(255, 200, 110), mtn=(16, 10, 4), wm='帝'),
}
GOLD = (240, 200, 110)
RED = (200, 24, 24)
WHITE = (250, 244, 232)

# ---------------------------------------------------------------- precomputed layers
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
VIGNETTE = np.clip(1.15 - _r ** 2 * 0.9, 0.18, 1.0)[..., None].astype(np.float32)
GRAINS = [rng.normal(0, 7, (H, W, 1)).astype(np.float32) for _ in range(6)]
GRAD = np.linspace(0, 1, H, dtype=np.float32)[:, None, None] ** 1.4

@lru_cache(None)
def gradient(name):
    th = THEMES[name]
    top = np.array(th['top'], np.float32); bot = np.array(th['bot'], np.float32)
    g = top + (bot - top) * GRAD
    return np.broadcast_to(g, (H, W, 3)).copy()

def ridge(seed, base, amp, rough):
    r = np.random.default_rng(seed)
    xs = np.arange(W + 400)
    y = np.zeros_like(xs, dtype=np.float64)
    for o in range(6):
        f = (o + 1) ** 1.7 / 900 * rough
        y += amp / (o + 1) ** 1.25 * np.sin(xs * f * 2 * math.pi + r.uniform(0, 6.28))
    return base + y

MTN = []
for i, (base, amp, rough, shade) in enumerate([(1310, 150, 1.0, 0.45), (1460, 120, 1.4, 0.7), (1620, 90, 1.9, 1.0)]):
    ys = ridge(11 + i, base, amp, rough)
    m = Image.new('L', (W + 400, H), 0)
    d = ImageDraw.Draw(m)
    d.polygon([(0, H)] + [(x, ys[x]) for x in range(0, W + 400, 4)] + [(W + 399, H)], fill=255)
    # mist fade on top edge
    m = m.filter(ImageFilter.GaussianBlur(2))
    MTN.append((m, shade, ys))

# great wall path: smoothed front ridge
SMOOTH_FRONT = np.convolve(np.pad(MTN[2][2], 60, mode='edge'), np.ones(121) / 121, mode='same')[60:-60] - 50

# ember sprites
def soft_dot(r, col):
    s = r * 6
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    a = np.zeros((s, s), np.float32)
    yy_, xx_ = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx_ - s / 2) ** 2 + (yy_ - s / 2) ** 2) / r
    a = np.clip(np.exp(-d ** 2 * 0.5) * 1.0 + (d < 1) * 0.6, 0, 1)
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = col; arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

N_EMB = 90
EMB = dict(x=rng.uniform(0, W, N_EMB), sp=rng.uniform(80, 320, N_EMB), ph=rng.uniform(0, 3000, N_EMB),
           sz=rng.integers(2, 6, N_EMB), wob=rng.uniform(10, 60, N_EMB), wf=rng.uniform(0.3, 1.5, N_EMB))

@lru_cache(None)
def dot_sprite(r, col): return soft_dot(int(r), col)

# rays
def make_rays():
    s = 1200
    a = np.zeros((s, s), np.float32)
    yy_, xx_ = np.mgrid[0:s, 0:s] - s / 2
    ang = np.arctan2(yy_, xx_)
    dist = np.sqrt(xx_ ** 2 + yy_ ** 2) / (s / 2)
    a = (np.cos(ang * 18) * 0.5 + 0.5) ** 6 * np.clip(1 - dist, 0, 1) ** 1.3
    return Image.fromarray((a * 255).astype(np.uint8), 'L')
RAYS = make_rays()

# ---------------------------------------------------------------- text helpers
@lru_cache(512)
def text_img(text, path, size, color, weight=None, glow=None, stroke=0, stroke_col=(0, 0, 0), spacing=0):
    """Render text (supports \n) to RGBA, optionally with coloured glow."""
    f = font(path, size, weight)
    lines = text.split('\n')
    pad = int(size * 0.6) + stroke
    widths, hs = [], []
    for ln in lines:
        bb = f.getbbox(ln, stroke_width=stroke)
        widths.append(bb[2] - bb[0] + spacing * max(0, len(ln) - 1)); hs.append(size * 1.18)
    w = int(max(widths)) + pad * 2; h = int(sum(hs)) + pad * 2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = pad
    for ln, lw in zip(lines, widths):
        x = (w - lw) / 2
        if spacing:
            for ch in ln:
                d.text((x, y), ch, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_col + (255,))
                x += f.getlength(ch) + spacing
        else:
            d.text((x, y), ln, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_col + (255,))
        y += size * 1.18
    if glow:
        a = im.getchannel('A').filter(ImageFilter.GaussianBlur(size * 0.12))
        g = Image.new('RGBA', im.size, glow + (0,)); g.putalpha(a.point(lambda v: min(255, int(v * 1.6))))
        g.alpha_composite(im); im = g
    return im

def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x = int(cx - im.width / 2); y = int(cy - im.height / 2)
    canvas.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H else _safe(canvas, im, x, y)

def _safe(canvas, im, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    canvas.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def slam(canvas, im, cx, cy, t, start, big=1.6, fade=0.0):
    """Beat-slam entrance: scale big->1 with expo ease, quick alpha in."""
    u = t - start
    if u < 0: return
    s = lerp(big, 1.0, ease_expo(u / 0.28))
    a = clamp(u / 0.06) * (1 - fade)
    paste(canvas, im, cx, cy, s, a)

@lru_cache(64)
def seal(text, size, col=(190, 20, 20)):
    """Red square seal with white characters (阴文 印章)."""
    f = font(SERIF, size, 'Black')
    n = len(text)
    cols = 1 if n <= 2 else 2
    rows = math.ceil(n / cols)
    cell = int(size * 1.08)
    w = cols * cell + int(size * 0.5); h = rows * cell + int(size * 0.5)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=int(size * 0.12), fill=col + (255,))
    # traditional reading order: right column top->bottom first
    for i, ch in enumerate(text):
        c = cols - 1 - i // rows; r = i % rows
        x = int(size * 0.25) + c * cell + (cell - f.getlength(ch)) / 2
        y = int(size * 0.25) + r * cell - size * 0.12
        d.text((x, y), ch, font=f, fill=(255, 236, 220, 255))
    # grunge: eat random specks out of alpha
    r = np.random.default_rng(len(text) * 31 + size)
    a = np.array(im.getchannel('A'), np.float32)
    noise = r.random(a.shape)
    a[noise < 0.06] *= 0.25
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im

# ---------------------------------------------------------------- script
# Each card: (beat_start, beat_end, theme, kind, data)
CARDS = [
    # ---- HOOK (b0-7)
    (0, 2, 'hook', 'num', dict(num='13', unit='岁', line='继位 为王')),
    (2, 4, 'hook', 'num', dict(num='39', unit='岁', line='一统 天下')),
    (4, 6, 'hook', 'num', dict(num='50', unit='岁', line='崩于 东巡路上')),
    (6, 8, 'hook', 'title', {}),
    # ---- LIFE (b8-15)
    (8, 10, 'life', 'card', dict(year=259, main='生于邯郸', sub='秦国质子之子 · 生在敌国赵都')),
    (10, 12, 'life', 'card', dict(year=257, main='九死一生', sub='秦赵血战 · 母子藏匿 · 屡遭追杀')),
    (12, 14, 'life', 'card', dict(year=247, main='继位秦王', sub='年仅十三 · 吕不韦为相')),
    (14, 16, 'life', 'card', dict(year=238, main='亲政夺权', sub='平嫪毐之乱 · 罢吕不韦 · 大权独揽')),
    # ---- WAR (b16-23)
    (16, 24, 'war', 'six', {}),
    # ---- EMPIRE (b24-31)
    (24, 26, 'empire', 'card', dict(year=221, main='始皇帝', sub='德兼三皇 · 功过五帝', seal='皇帝')),
    (26, 30, 'empire', 'list', dict(year=221, items=['书同文', '车同轨', '统一度量衡', '废分封 立郡县'])),
    (30, 32, 'empire', 'card', dict(year=221, main='大一统', sub='百代都行秦政法', pre='中国 第一次')),
    # ---- WORKS (b32-39)
    (32, 34, 'works', 'card', dict(year=215, main='北筑长城', sub='蒙恬率三十万大军 · 北击匈奴')),
    (34, 36, 'works', 'card', dict(year=214, main='修驰道 凿灵渠', sub='车马通天下 · 水路连岭南', msize=170)),
    (36, 38, 'works', 'card', dict(year=213, main='焚书坑儒', sub='功过是非 · 争议两千年')),
    (38, 40, 'works', 'card', dict(year=211, main='求仙问药', sub='遣徐福东渡 · 只为长生不老')),
    # ---- DEATH (b40-43)
    (40, 42, 'death', 'card', dict(year=210, main='崩于沙丘', sub='第五次东巡途中 · 终年五十岁')),
    (42, 44, 'death', 'card', dict(year=207, main='二世而亡', sub='大秦帝国 · 仅存十五年')),
    # ---- END (b44 ->)
    (44, 99, 'end', 'end', {}),
]
STATES = ['韩', '赵', '魏', '楚', '燕', '齐']
STATE_YEARS = [230, 228, 225, 223, 222, 221]
# hexagon layout (stylised geography: 燕 north-east, 齐 east, 楚 south ...)
HEX_POS = {'赵': (-1, -1), '燕': (1, -1), '韩': (-2, 0), '齐': (2, 0), '魏': (-1, 1), '楚': (1, 1)}

def card_at(t):
    k = (t - B0) / P
    for c in CARDS:
        if c[0] <= k < c[1]: return c, k
    return CARDS[0], k

def year_at(t):
    """Smooth year for the timeline (life ..death sections)."""
    pts = []
    for c in CARDS:
        if c[3] in ('card', 'list') and c[0] >= 8:
            pts.append((bt(c[0]), c[4]['year']))
        if c[3] == 'six':
            for i, y in enumerate(STATE_YEARS): pts.append((bt(16 + i), y))
    pts.sort()
    if t <= pts[0][0]: return pts[0][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t < t1:
            return lerp(y0, y1, ease_expo((t - t0) / 0.35))
    return pts[-1][1]

# ---------------------------------------------------------------- background
def draw_background(t, theme, k):
    th = THEMES[theme]
    arr = gradient(theme).copy()
    canvas = Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')

    # rays for imperial / end sections
    if theme in ('empire', 'end', 'war'):
        rot = t * (14 if theme != 'war' else -22)
        r = RAYS.rotate(rot, resample=Image.BILINEAR).resize((2300, 2300), Image.BILINEAR)
        strength = {'empire': 0.55, 'end': 0.45, 'war': 0.28}[theme]
        a = r.point(lambda v: int(v * strength))
        layer = Image.new('RGBA', r.size, th['acc'] + (0,)); layer.putalpha(a)
        _safe(canvas, layer, W // 2 - 1150, 880 - 1150)

    # giant watermark character
    wm = text_img(th['wm'], WILD, 900, tuple(min(255, c + 30) for c in th['bot']))
    paste(canvas, wm, W / 2 + 40 * math.sin(t * 0.4), 820, 1.05 + 0.03 * math.sin(t * 0.7), 0.35)

    # mountains with parallax
    for i, (m, shade, ys) in enumerate(MTN):
        off = int(200 + math.sin(t * 0.25 + i) * 30 * (i + 1) - t * 8 * (i + 1)) % 400
        col = tuple(int(c * (0.6 + 0.4 * shade)) for c in th['mtn'])
        layer = Image.new('RGBA', (W, H), col + (255,))
        layer.putalpha(m.crop((off, 0, off + W, H)))
        canvas.alpha_composite(layer)
        if theme == 'works' and i == 2:
            draw_wall(canvas, t, off, SMOOTH_FRONT)
    return canvas

def draw_wall(canvas, t, off, ys):
    prog = ease_out((t - bt(32)) / (P * 4))
    if prog <= 0: return
    d = ImageDraw.Draw(canvas)
    xmax = int(W * prog)
    col = (150, 172, 182, 255)
    pts = [(x, ys[x + off] - 4) for x in range(0, xmax, 6)]
    if len(pts) > 1:
        d.line(pts, fill=col, width=10)
        for x in range(0, xmax, 26):
            y = ys[x + off] - 4
            d.rectangle((x, y - 18, x + 12, y), fill=col)
        for x in range(90, xmax, 260):  # watchtowers
            y = ys[x + off] - 4
            d.rectangle((x - 18, y - 60, x + 18, y), fill=col)
            d.polygon([(x - 26, y - 60), (x + 26, y - 60), (x, y - 84)], fill=col)

def draw_embers(canvas, t, theme):
    th = THEMES[theme]
    falling = theme == 'death'
    for i in range(N_EMB):
        span = H + 300
        y = (EMB['ph'][i] + t * EMB['sp'][i]) % span
        y = (y - 150) if falling else (H + 150 - y)
        x = EMB['x'][i] + EMB['wob'][i] * math.sin(t * EMB['wf'][i] + i)
        r = int(EMB['sz'][i])
        flick = 0.55 + 0.45 * math.sin(t * 6 + i * 1.7)
        spr = dot_sprite(r, th['ember'])
        paste(canvas, spr, x, y, 1.0, flick * 0.9)

# ---------------------------------------------------------------- foreground scenes
def scene_num(canvas, t, c, k):
    s0 = bt(c[0]); s1 = bt(c[0] + 1)
    d = c[4]
    num = text_img(d['num'], SERIF, 520, GOLD, 'Black', glow=(255, 80, 20))
    unit = text_img(d['unit'], BRUSH, 200, WHITE)
    slam(canvas, num, W / 2 - 60, 760, t, s0, big=2.2)
    slam(canvas, unit, W / 2 + 270, 880, t, s0 + 0.08, big=1.8)
    line = text_img(d['line'], BRUSH, 150, WHITE, glow=(200, 20, 20))
    slam(canvas, line, W / 2, 1180, t, s1, big=1.7)
    # thin red underline that draws on
    u = ease_out((t - s1) / 0.3)
    if u > 0:
        dr = ImageDraw.Draw(canvas)
        dr.rectangle((W / 2 - 330 * u, 1300, W / 2 + 330 * u, 1308), fill=(220, 30, 30, 255))
    tag = text_img('他', BRUSH, 110, (255, 220, 200))
    paste(canvas, tag, 170, 470, 1.0, clamp((t - s0) / 0.1) * 0.8)

def scene_title(canvas, t, c, k):
    s0 = bt(c[0]); s1 = bt(c[0] + 1)
    title = text_img('秦始皇', BRUSH, 300, WHITE, glow=(230, 30, 20))
    u = t - s0
    sc = lerp(2.6, 1.0, ease_expo(u / 0.35))
    paste(canvas, title, W / 2, 880, sc, clamp(u / 0.05))
    name = text_img('嬴 政', SERIF, 72, GOLD, 'SemiBold', spacing=10)
    paste(canvas, name, W / 2, 640, 1, clamp((u - 0.15) / 0.2))
    if t >= s1:
        sl = seal('千古一帝', 92)
        v = t - s1
        sc = lerp(2.4, 1.0, ease_expo(v / 0.18))
        paste(canvas, sl, W / 2, 1230, sc, clamp(v / 0.05), rot=-6)

def draw_year(canvas, t, year, start):
    y_im = text_img(f'公元前 {year} 年', SERIF, 64, GOLD, 'Bold', spacing=4)
    u = t - start
    paste(canvas, y_im, W / 2 + lerp(-60, 0, ease_expo(u / 0.3)), 470, 1, clamp(u / 0.1))
    dr = ImageDraw.Draw(canvas)
    w = 240 * ease_out(u / 0.4)
    dr.rectangle((W / 2 - w, 530, W / 2 + w, 533), fill=GOLD + (200,))

def scene_card(canvas, t, c, k):
    s0 = bt(c[0]); s1 = bt(c[0] + 1)
    d = c[4]
    acc = THEMES[c[2]]['acc']
    draw_year(canvas, t, d['year'], s0)
    if 'pre' in d:
        pre = text_img(d['pre'], SERIF, 80, WHITE, 'Bold', spacing=8)
        slam(canvas, pre, W / 2, 690, t, s0, big=1.3)
    msize = d.get('msize', 230)
    main = text_img(d['main'], BRUSH, msize, WHITE, glow=tuple(int(v * 0.8) for v in acc), stroke=0)
    # main: stagger characters? slam whole with slight rotation wobble
    u = t - s0
    sc = lerp(1.9, 1.0, ease_expo(u / 0.3)) + 0.015 * math.sin(t * 3)
    paste(canvas, main, W / 2, 900, sc, clamp(u / 0.05))
    if t >= s1:
        sub = text_img(d['sub'], SERIF, 50, (235, 228, 214), 'Medium', spacing=3)
        v = t - s1
        paste(canvas, sub, W / 2, lerp(1160, 1120, ease_expo(v / 0.3)), 1, clamp(v / 0.12))
        if 'seal' in d:
            sl = seal(d['seal'], 90)
            paste(canvas, sl, W / 2 + 390, 690, lerp(2.5, 1, ease_expo(v / 0.18)), clamp(v / 0.04), rot=8)

def scene_list(canvas, t, c, k):
    s0 = bt(c[0])
    d = c[4]
    draw_year(canvas, t, d['year'], bt(24))
    hdr = text_img('统一天下 · 定万世之制', SERIF, 54, GOLD, 'Bold', spacing=4)
    paste(canvas, hdr, W / 2, 610, 1, 1)
    for i, it in enumerate(d['items']):
        st = bt(c[0] + i)
        if t < st: continue
        cur = (i == int(k - c[0]))
        size = 150 if len(it) <= 3 else (125 if len(it) <= 5 else 105)
        im = text_img(it, BRUSH, size, WHITE, glow=(255, 160, 40))
        y = 790 + i * 205
        u = t - st
        x = W / 2 + lerp(W, 0, ease_expo(u / 0.25)) * (1 if i % 2 == 0 else -1)
        paste(canvas, im, x, y, 1.0 if not cur else lerp(1.25, 1.06, ease_out(u / 0.3)), 1.0 if cur else 0.7)
        num = text_img('壹贰叁肆'[i], SERIF, 46, (40, 20, 0), 'Black')
        dr = ImageDraw.Draw(canvas)
        cx = 110 if i % 2 == 0 else W - 110
        if u > 0.1:
            dr.ellipse((cx - 42, y - 42, cx + 42, y + 42), fill=GOLD + (255,))
            paste(canvas, num, cx, y + 4, 1, 1)

@lru_cache(None)
def state_disc(ch, dead):
    s = 230
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if dead:
        d.ellipse((15, 15, s - 15, s - 15), fill=(30, 8, 6, 220), outline=(90, 30, 25, 255), width=4)
        g = text_img(ch, SERIF, 120, (95, 60, 55), 'Black')
    else:
        d.ellipse((15, 15, s - 15, s - 15), fill=(20, 10, 8, 235), outline=(240, 200, 120, 255), width=5)
        g = text_img(ch, SERIF, 120, WHITE, 'Black')
    im.alpha_composite(g, ((s - g.width) // 2, (s - g.height) // 2 - 10))
    return im

@lru_cache(None)
def half_masks(s):
    a = Image.new('L', (s, s), 0); ImageDraw.Draw(a).polygon([(0, 0), (s, 0), (0, s)], fill=255)
    b = ImageChops.invert(a)
    return a, b

def scene_six(canvas, t, c, k):
    s0 = bt(16)
    cx0, cy0 = W / 2, 1020
    R = 190
    # header
    hdr = text_img('十年 灭六国', BRUSH, 170, WHITE, glow=(255, 40, 10))
    gather = t >= bt(22)
    if not gather:
        paste(canvas, hdr, W / 2, 400, lerp(1.6, 1, ease_expo((t - s0) / 0.3)), clamp((t - s0) / 0.05))
    idx = int(k - 16)  # current beat inside phrase
    # current label
    if 0 <= idx < 6:
        lab = text_img(f'前{STATE_YEARS[idx]} · 灭{STATES[idx]}', SERIF, 74, GOLD, 'Black', spacing=6)
        slam(canvas, lab, W / 2, 1520, t, bt(16 + idx), big=1.5)
    # center Qin
    gu = ease_expo((t - bt(22)) / 0.35) if gather else 0
    qin = seal('秦', 120 + int(0), (200, 20, 20))
    pulse = 1 + 0.08 * math.exp(-((t - B0) % P) / 0.12)
    paste(canvas, qin, cx0, cy0, (1.0 + 1.6 * gu) * pulse, 1)
    # states
    for i, ch in enumerate(STATES):
        hx, hy = HEX_POS[ch]
        px = cx0 + hx * R * 0.92 * 1.0
        py = cy0 + hy * R * 1.55
        if hx in (-2, 2): px = cx0 + hx * R * 0.95
        killed_at = bt(16 + i)
        if gather:
            px = lerp(px, cx0, gu); py = lerp(py, cy0, gu)
            paste(canvas, state_disc(ch, True), px, py, 1 - 0.8 * gu, 1 - gu)
            continue
        if t < killed_at:
            paste(canvas, state_disc(ch, False), px, py, 1, 1)
            continue
        u = t - killed_at
        if u < 0.45:
            # split along diagonal
            disc = state_disc(ch, False)
            a, b = half_masks(disc.width)
            sep = ease_out(u / 0.45) * 60
            for m, sgn in ((a, -1), (b, 1)):
                part = disc.copy(); part.putalpha(ImageChops.multiply(disc.getchannel('A'), m))
                paste(canvas, part, px + sgn * sep, py + sgn * sep * 0.6, 1, 1 - u / 0.45, rot=sgn * u * 40)
            # slash line
            sl = clamp(u / 0.12)
            dr = ImageDraw.Draw(canvas)
            L = 220
            x0, y0 = px + L * 0.8, py - L * 0.8
            x1, y1 = lerp(x0, px - L * 0.8, sl), lerp(y0, py + L * 0.8, sl)
            al = int(255 * clamp(1 - (u - 0.12) / 0.3))
            dr.line((x0, y0, x1, y1), fill=(255, 250, 240, al), width=10)
            dr.line((x0, y0, x1, y1), fill=(255, 40, 30, al), width=4)
            paste(canvas, state_disc(ch, True), px, py, 1, clamp(u / 0.45))
        else:
            paste(canvas, state_disc(ch, True), px, py, 1, 1)
            # red X tick
            dr = ImageDraw.Draw(canvas)
            dr.line((px - 70, py - 70, px + 70, py + 70), fill=(210, 20, 20, 200), width=8)
    if gather:
        l1 = text_img('六王毕', BRUSH, 210, WHITE, glow=(255, 40, 10))
        l2 = text_img('四海一', BRUSH, 210, GOLD, glow=(255, 120, 10))
        slam(canvas, l1, W / 2, 470, t, bt(22), big=1.8)
        slam(canvas, l2, W / 2, 1580, t, bt(23), big=1.8)

def scene_end(canvas, t, c, k):
    s0 = bt(44)
    u = t - s0
    title = text_img('千古一帝', BRUSH, 250, GOLD, glow=(255, 120, 20))
    paste(canvas, title, W / 2, 800, lerp(2.2, 1.0, ease_expo(u / 0.45)) + 0.01 * u, clamp(u / 0.06))
    sl = seal('秦始皇帝', 70)
    if u > 0.5:
        v = u - 0.5
        paste(canvas, sl, W / 2 + 330, 560, lerp(2.2, 1, ease_expo(v / 0.2)), clamp(v / 0.05), rot=7)
    l1 = text_img('王朝只存十五年', SERIF, 58, WHITE, 'Medium', spacing=6)
    l2 = text_img('他定下的“中国” 延续两千年', SERIF, 58, WHITE, 'Bold', spacing=6)
    paste(canvas, l1, W / 2, 1090, 1, clamp((u - 0.7) / 0.3))
    paste(canvas, l2, W / 2, 1180, 1, clamp((u - 1.2) / 0.3))
    nm = text_img('秦始皇 · 嬴政   前259 — 前210', SERIF, 40, (220, 200, 160), 'Regular', spacing=3)
    paste(canvas, nm, W / 2, 1330, 1, clamp((u - 1.6) / 0.4))

SCENES = dict(num=scene_num, title=scene_title, card=scene_card, list=scene_list, six=scene_six, end=scene_end)

# ---------------------------------------------------------------- HUD
def draw_hud(canvas, t, k):
    # top tag
    tag = text_img('中国历史人物 · 一生', SERIF, 36, (235, 220, 190), 'Medium', spacing=6)
    paste(canvas, tag, W / 2, 150, 1, 0.85)
    # timeline (life .. death)
    if bt(8) - 0.15 <= t < bt(44):
        a = clamp((t - (bt(8) - 0.15)) / 0.2)
        y = 1730
        x0, x1 = 140, W - 140
        yr = year_at(t)
        p = (259 - yr) / (259 - 210)
        ov = Image.new('RGBA', (W, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        d.rectangle((x0, 98, x1, 102), fill=(255, 255, 255, 70))
        xp = lerp(x0, x1, clamp(p))
        d.rectangle((x0, 97, xp, 103), fill=GOLD + (255,))
        d.ellipse((xp - 13, 87, xp + 13, 113), fill=(230, 40, 30, 255), outline=GOLD + (255,), width=3)
        age = int(round(260 - yr))
        f = font(SERIF, 34, 'Medium')
        d.text((x0, 125), '前259', font=f, fill=(220, 210, 190, 200))
        d.text((x1 - f.getlength('前210'), 125), '前210', font=f, fill=(220, 210, 190, 200))
        lab = f'{min(age, 50)}岁' if yr >= 210 else '身后'
        fb = font(SERIF, 40, 'Bold')
        d.text((xp - fb.getlength(lab) / 2, 25), lab, font=fb, fill=(255, 235, 200, 255))
        if a < 1:
            ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
        canvas.alpha_composite(ov, (0, y - 100))

# ---------------------------------------------------------------- frame
CUT_BEATS = {c[0] for c in CARDS}
def render(fi):
    t = fi / FPS
    c, k = card_at(t)
    if t < B0:  # pre-roll
        c = CARDS[0]
    theme = c[2]
    canvas = draw_background(t, theme, k)
    draw_embers(canvas, t, theme)
    if t >= B0:
        SCENES[c[3]](canvas, t, c, k)
    draw_hud(canvas, t, k)

    # ------------- post FX
    kb = math.floor((t - B0) / P) if t >= B0 else -1
    since = t - bt(kb) if kb >= 0 else 9
    end_beat = kb >= 45
    strong = kb % 2 == 0
    hit = math.exp(-since / 0.11) if (kb >= 0 and not end_beat) else 0.0
    cut = kb in CUT_BEATS or (16 <= kb <= 23) or (26 <= kb <= 29)

    # zoom punch
    z = 1 + (0.06 if strong else 0.03) * hit
    if t < B0:  # intro push-in
        z = 1.25 - 0.25 * ease_out(t / B0)
    shx = shy = 0
    if hit > 0.05 and strong:
        shx = math.sin(t * 91) * 18 * hit; shy = math.cos(t * 77) * 18 * hit
    if z > 1.001 or shx or shy:
        cw, ch = W / z, H / z
        x0 = (W - cw) / 2 - shx; y0 = (H - ch) / 2 - shy
        canvas = canvas.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

    arr = np.asarray(canvas.convert('RGB'), dtype=np.float32)
    # chromatic aberration
    ca = int((14 if cut else 6) * hit)
    if ca:
        arr = arr.copy()
        arr[..., 0] = np.roll(arr[..., 0], ca, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -ca, axis=1)
    # flash on cuts
    if cut and kb >= 0 and not end_beat:
        fl = math.exp(-since / 0.07) * (0.55 if kb in CUT_BEATS else 0.3)
        arr = arr + (255 - arr) * fl
    arr = arr * VIGNETTE + GRAINS[fi % len(GRAINS)]
    # intro fade from black & outro fade
    fade = 1.0
    if t < 0.12: fade = t / 0.12
    if t > 26.6: fade = clamp(1 - (t - 26.6) / 1.3)
    arr *= fade
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out.mp4')
    nfr = int(DUR * FPS)
    if len(sys.argv) > 2:  # preview stills: render.py out.png t1,t2,...
        for ts in sys.argv[2].split(','):
            fi = int(float(ts) * FPS)
            Image.frombytes('RGB', (W, H), render(fi)).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', os.path.join(HERE, 'music.mp3'),
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                          stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 60 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
