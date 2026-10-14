"""Skala postaci w czasie (zoom H3): dopasowanie głowy z klatki wzorcowej (NCC, OpenCV) w skalach 0.8–1.3.
python3 skala.py JOB [key] → frames/JOB/skala.json  {"s": [na każdą klatkę 24 fps], "raw": [[i, s, score], ...]}"""
import sys, glob, json, numpy as np, cv2
from PIL import Image
sys.path.insert(0, '/home/user/MathGames/.claude/skills/sprite-pipeline/scripts'); import key
REF_JOB, REF_I = '20261014-213834-e96c85', 13
def keyed(path, k='auto'):
    a = np.array(Image.open(path).convert('RGB')); r, _ = key.key_image(a, k); al = r[..., 3:4] / 255
    return (r[..., :3] * al + 128 * (1 - al)).astype(np.uint8), r[..., 3]
def head_template():
    rgb, al = keyed(f'frames/{REF_JOB}/src/f_{REF_I+1:03d}.png')
    ys, xs = np.nonzero(al > 128); top, bot = ys.min(), ys.max(); h = bot - top
    band = (ys < top + 0.2 * h); hx = xs[band]
    x0, x1 = hx.min() - 6, hx.max() + 6
    return rgb[top - 6: int(top + 0.2 * h), x0:x1]
T = head_template()
job = sys.argv[1]; kk = sys.argv[2] if len(sys.argv) > 2 else 'auto'
fs = sorted(glob.glob(f'frames/{job}/src/*.png')); raw = []
for i in range(0, len(fs), 3):
    rgb, al = keyed(fs[i], kk)
    best = (-1, 1)
    for s in np.arange(0.8, 1.31, 0.01):
        t = cv2.resize(T, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        m = cv2.matchTemplate(rgb[:500], t, cv2.TM_CCOEFF_NORMED).max()
        if m > best[0]: best = (float(m), float(s))
    raw.append([i, round(best[1], 3), round(best[0], 3)])
r = np.array(raw); good = r[:, 2] > 0.55
# gładka krzywa: mediana krocząca na dobrych punktach, potem interpolacja
xs, ss = r[good, 0], r[good, 1]
sm = np.array([np.median(ss[max(0, j - 3): j + 4]) for j in range(len(ss))])
full = np.interp(np.arange(len(fs)), xs, sm)
json.dump({"s": [round(float(v), 4) for v in full], "raw": raw}, open(f'frames/{job}/skala.json', 'w'))
print(job, ' '.join(f'{int(a)/24:.1f}:{b:.2f}/{c:.2f}' for a, b, c in raw[::2]))
