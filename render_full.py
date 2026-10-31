# 秦始皇 · 千古一帝 —— 古风故事 · 全长加强动效版（28.1 秒，与音乐等长）
# 在故事版基础上增加：逐字落笔+墨点飞溅、字幕书写式展开、每拍墨韵涟漪、
# 前景流雾、年份滚动、加长结尾动画。整屏依旧不缩放、不震动。
import math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw
import render_gufeng as G
import render_story as S
from render_gufeng import (W, H, FPS, P, bt, INK, ZHU, ZHE, BRUSH, SERIF, font, clamp, lerp,
                           ease_out, ease_expo, cn_num, text_img, paste, ink_in, seal, stamp)
from render_story import Art, ART, LIST_ART, crow, person

HERE = os.path.dirname(os.path.abspath(__file__))
G.DUR = 28.1
END = bt(44)

# ================================================================ motion helpers
def spatter(A, cx, cy, t, start, seed, n=22, width=300):
    """Ink droplets thrown out when a character lands."""
    u = t - start
    if u < 0 or u > 0.7: return
    r = random.Random(seed)
    for _ in range(n):
        x0 = cx + r.uniform(-width / 2, width / 2)
        a = r.uniform(0, 2 * math.pi); v = r.uniform(250, 800); sz = r.uniform(3, 11)
        x = x0 + math.cos(a) * v * u * (1 - u / 1.4)
        y = cy + math.sin(a) * v * u * 0.6 + 700 * u * u
        s = sz * (1 - u / 0.9)
        A.d['ink'].ellipse((x - s, y - s, x + s, y + s), fill=int(255 * (1 - u / 0.7)))

def chars_in(cv, A, text, path, size, color, cx, cy, t, start, stagger=0.07, weight=None, drop=46,
             splash=True, seed=0, alpha=1.0):
    """Each character drops in on its own, ink bleeding outward; settles with a gentle float."""
    f = font(path, size, weight)
    ws = [f.getlength(ch) for ch in text]
    x = cx - sum(ws) / 2
    for i, (ch, w) in enumerate(zip(text, ws)):
        st = start + i * stagger
        if ch != ' ' and t >= st:
            u = t - st
            yoff = -drop * (1 - ease_out(u / 0.28)) + 3 * math.sin(t * 2.2 + i) * clamp((u - 0.3) / 0.3)
            ink_in(cv, text_img(ch, path, size, color, weight), x + w / 2, cy + yoff, t, st, dur=0.24,
                   settle=1.18, alpha=alpha)
            if splash and A is not None:
                spatter(A, x + w / 2, cy + size * 0.3, t, st + 0.08, seed * 31 + i, n=6, width=w * 0.8)
        x += w

def type_in(cv, im, cx, cy, t, start, dur=0.4):
    """Subtitle written left-to-right with a soft brush edge."""
    u = t - start
    if u <= 0: return
    p = clamp(u / dur)
    if p < 1:
        a = np.asarray(im.getchannel('A'), np.float32)
        xs = np.arange(im.width, dtype=np.float32)[None, :]
        m = np.clip((p * im.width * 1.1 - xs) / 40, 0, 1)
        im = im.copy(); im.putalpha(Image.fromarray((a * m).astype(np.uint8)))
    paste(cv, im, cx, cy)

RIPPLE = True   # per-episode switch for the beat ripple rings

def beat_fx(A, t):
    """Ink ripple on every beat + drifting ground mist."""
    if RIPPLE and G.B0 <= t < END + 0.6:
        kb = math.floor((t - G.B0) / P)
        q = (t - bt(kb)) / 0.6
        if q < 1:
            r = lerp(70, 470, ease_out(q))
            A.d['wash'].ellipse((540 - r, 1150 - r * 0.55, 540 + r, 1150 + r * 0.55), outline=int(230 * (1 - q)), width=9)
            if kb % 2 == 0:
                r2 = r * 0.7
                A.d['wash'].ellipse((540 - r2, 1150 - r2 * 0.55, 540 + r2, 1150 + r2 * 0.55), outline=int(160 * (1 - q)), width=5)
    for k in range(3):
        x = (t * (70 + 45 * k) + k * 430) % (W + 900) - 700
        y = 1395 + k * 30
        A.d['wash'].rounded_rectangle((x, y, x + 560 - k * 80, y + 26), radius=13, fill=170)

def year_line(cv, t, year, start):
    yr = int(round(G.year_at(t))) if t >= bt(8) else year
    s = '公元前' + cn_num(yr) + '年'
    im = text_img(s, SERIF, 40, ZHE, 'Bold', bleed=False, spacing=6)
    ink_in(cv, im, W / 2, 300, t, start, dur=0.3, settle=1.0)
    w = 200 * ease_out((t - start) / 0.4)
    ImageDraw.Draw(cv).line((W / 2 - w, 335, W / 2 + w, 335), fill=ZHU + (220,), width=3)

def stage(cv, t, c, fn):
    A = Art()
    u = t - bt(c[0])
    fn(A, cv, t, u)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out(u / 0.35))

# ================================================================ scenes
def scene_num(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    stage(cv, t, c, ART[c[0]])
    d = c[4]
    fx = Art()
    chars_in(cv, fx, d['num'], BRUSH, 150, INK, W / 2, 470, t, s0, stagger=0.06, seed=c[0])
    chars_in(cv, fx, d['line'], BRUSH, 92, ZHU, W / 2, 600, t, s1, stagger=0.05, drop=30, splash=False)
    fx.flush(cv)

def scene_title(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    stage(cv, t, c, S.art_emperor)
    fx = Art()
    ink_in(cv, text_img('嬴 政', SERIF, 50, ZHE, 'Bold', bleed=False, spacing=16), W / 2, 300, t, s0)
    chars_in(cv, fx, '秦始皇', BRUSH, 200, INK, W / 2, 450, t, s0, stagger=0.09, seed=77)
    fx.flush(cv)
    stamp(cv, seal('千古一帝', 58), 880, 640, t, s1, rot=-5)

def scene_card(cv, t, c, k):
    s0, s1 = bt(c[0]), bt(c[0] + 1)
    d = c[4]
    stage(cv, t, c, ART[c[0]])
    year_line(cv, t, d['year'], s0)
    main = d['main'].replace('\n', ' ')
    fx = Art()
    chars_in(cv, fx, main, BRUSH, 150 if len(main) <= 5 else 120, INK, W / 2, 435, t, s0, seed=c[0])
    fx.flush(cv)
    sub = text_img(d['sub'], SERIF, 40, (70, 50, 30), 'SemiBold', bleed=False, spacing=3)
    type_in(cv, sub, W / 2, 555, t, s1, dur=0.38)
    if 'seal' in d and t >= s1:
        stamp(cv, seal(d['seal'], 60), W / 2 + 330, 420, t, s1, rot=6)

def scene_list(cv, t, c, k):
    i = min(3, int(k - c[0]))
    st = bt(c[0] + i)
    A = Art()
    LIST_ART[i](A, cv, t, t - st)
    beat_fx(A, t)
    A.flush(cv, reveal=ease_out((t - st) / 0.25))
    year_line(cv, t, 221, bt(24))
    it = c[4]['items'][i]
    fx = Art()
    chars_in(cv, fx, it, BRUSH, 140 if len(it) <= 5 else 120, INK, W / 2, 440, t, st, stagger=0.05, seed=50 + i)
    fx.flush(cv)
    for j in range(4):
        x = W / 2 + (j - 1.5) * 95
        if j <= i:
            stamp(cv, seal('壹贰叁肆'[j], 36), x, 575, t, bt(c[0] + j))
        else:
            ImageDraw.Draw(cv).rounded_rectangle((x - 30, 545, x + 30, 605), radius=6, outline=ZHU + (110,), width=2)

def scene_end(cv, t, c, k):
    u = t - END
    # backdrop: emperor rises out of the mist, crows cross the sky
    A = Art()
    rise = ease_out(u / 1.6)
    person(A, 230, lerp(1820, 1700, rise), 760, dir=1, hat='crown', arm=lerp(10, 40, rise), layer='wash')
    for i in range(4):
        cx = lerp(-80, W + 120, clamp((u - 0.2 * i) / 2.4)) + i * 40
        crow(A, cx, 470 + 40 * math.sin(u * 2 + i) + i * 28, 20, t * 11 + i)
    beat_fx(A, t)
    A.flush(cv, alpha=clamp(u / 0.6))
    fx = Art()
    chars_in(cv, fx, '千古一帝', BRUSH, 230, INK, W / 2, 760, t, END, stagger=0.1, drop=60, seed=99)
    fx.flush(cv)
    stamp(cv, seal('秦始皇帝', 64), W / 2 + 370, 520, t, END + 0.45, rot=6)
    type_in(cv, text_img('王朝只存十五年', SERIF, 50, (70, 50, 30), 'SemiBold', bleed=False, spacing=6), W / 2, 960, t, END + 0.6, 0.35)
    type_in(cv, text_img('他定下的“中国” 延续两千年', SERIF, 54, INK, 'Bold', bleed=False, spacing=6), W / 2, 1040, t, END + 0.85, 0.45)
    chars_in(cv, None, '暴君？明君？', BRUSH, 120, ZHU, W / 2, 1200, t, END + 1.15, stagger=0.06, drop=30, splash=False)
    type_in(cv, text_img('评论区留下你的看法', SERIF, 42, (70, 50, 30), 'SemiBold', bleed=False, spacing=4), W / 2, 1300, t, END + 1.5, 0.3)
    v = u - 1.75
    if v > 0:
        pulse = 1 + 0.035 * math.sin(v * 7)
        bw, bh, by = 400 * pulse, 92 * pulse, 1430
        a = int(255 * clamp(v / 0.25))
        btn = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(btn)
        d.rounded_rectangle((W / 2 - bw / 2, 100 - bh / 2, W / 2 + bw / 2, 100 + bh / 2), radius=46, fill=ZHU + (a,))
        f = font(SERIF, int(42 * pulse), 'Bold'); s = '＋ 关注 · 看下一集'
        d.text((W / 2 - f.getlength(s) / 2, 100 - 30 * pulse), s, font=f, fill=(252, 240, 226, a))
        # brush circle drawn around the button
        prog = ease_out(v / 0.6)
        pts = [(W / 2 + 250 * math.cos(math.radians(-200 + 380 * prog * j / 40)),
                100 + 75 * math.sin(math.radians(-200 + 380 * prog * j / 40))) for j in range(41)]
        d.line(pts, fill=INK + (200,), width=5)
        cv.alpha_composite(btn, (0, by - 100))
        paste(cv, text_img('下集预告 · 汉武帝刘彻', SERIF, 38, (50, 36, 24), 'Bold', bleed=False, spacing=4),
              W / 2, 1530, 1, clamp((v - 0.2) / 0.3))

G.SCENES.update(num=scene_num, title=scene_title, card=scene_card, list=scene_list, end=scene_end)

# Card changes inside a chapter: dissolve from the last frame of the previous card
# so the screen never flashes empty while the new scene inks in.
CUTS = sorted({c[0] for c in G.CARDS if c[0] not in G.CHAPTER_BEATS} | {27, 28, 29})
DISSOLVE = 0.22
def render(fi):
    t = fi / FPS
    cur = G.render(fi)
    for cb in CUTS:
        s = bt(cb)
        if s <= t < s + DISSOLVE:
            prev_fi = math.ceil(s * FPS) - 1
            a = ease_out((t - s) / DISSOLVE)
            pa = np.frombuffer(G.render(prev_fi), np.uint8).astype(np.float32)
            ca = np.frombuffer(cur, np.uint8).astype(np.float32)
            return np.clip(pa * (1 - a) + ca * a, 0, 255).astype(np.uint8).tobytes()
    return cur

if __name__ == '__main__':
    from multiprocessing import Pool
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for ts in sys.argv[2].split(','):
            Image.frombytes('RGB', (W, H), render(int(float(ts) * FPS))).save(out.replace('.png', f'_{ts}.png'))
        sys.exit()
    nfr = int(round(G.DUR * FPS))
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-i', os.path.join(HERE, 'music_full.wav'),
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, fr in enumerate(pool.imap(render, range(nfr), chunksize=4)):
            ff.stdin.write(fr)
            if i % 120 == 0: print(i, '/', nfr, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', out)
