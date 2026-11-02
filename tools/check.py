"""Pre-render checks for one episode: python3 tools/check.py render_xxx [extra brush text]
1) brush-font coverage  2) no '·' in brush text  3) no reused art  4) error scan over every scene's opening frames."""
import sys, os, math, collections, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import ImageFont
mod = importlib.import_module(sys.argv[1])
extra = sys.argv[2] if len(sys.argv) > 2 else ''
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ImageFont.truetype(os.path.join(here, 'fonts/MaShanZheng-Regular.ttf'), 64)
nd = bytes(F.getmask('\U000F0000'))
txt = ''.join(c[4].get('main', '') + c[4].get('num', '') + c[4].get('line', '') + ''.join(c[4].get('items', []))
              for c in mod.CARDS) + ''.join(v[1] for v in mod.CHAPTERS.values()) + extra
miss = sorted({ch for ch in txt if ch.strip() and ch != '·' and bytes(F.getmask(ch)) == nd})
dots = '·' in ''.join(c[4].get('main', '') + c[4].get('num', '') + c[4].get('line', '') for c in mod.CARDS)
use = collections.Counter(id(c[4]['art']) for c in mod.CARDS if 'art' in c[4])
dup = [k for k, v in use.items() if v > 1]
fis = set()
for c in mod.CARDS:
    b0 = mod.bt(c[0])
    for k in range(0, min(c[1], c[0] + 10) - c[0] + 1):
        f0 = math.floor((b0 + k * mod.P) * 30); fis.update(range(f0 - 1, f0 + 6))
fis = sorted(f for f in fis if 0 <= f < int(round(mod.G.DUR * 30)))
errs = collections.defaultdict(list)
for fi in fis:
    try: mod.render(fi)
    except Exception as e: errs[repr(e)[:140]].append(fi)
ys = [(c[0], c[4]['year']) for c in sorted(mod.CARDS) if 'year' in c[4]]
back = [(b, y0, y1) for (b, y0), (_, y1) in zip(ys, ys[1:]) if y1 < y0]
print('years going backwards:', back)
print('missing brush glyphs:', miss)
print('dot in brush titles:', dots)
print('duplicate arts:', len(dup))
print('frames checked:', len(fis), 'errors:', {k: v[:6] for k, v in errs.items()})
ok = not miss and not dots and not dup and not errs and not back
print('CHECK', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
