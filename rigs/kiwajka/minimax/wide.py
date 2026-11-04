"""The wide H3 canvases (1344 x 768, the monkey where she stood on the 768 square: x 171, y 199): the home picture and
the drawn ukulele peak (a Nano Banana edit registered on the legs and feet, ground reset to the exact flat blue).
run from the sprite-refs root."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
BLUE = np.array([47, 107, 216.]); W = 1344
cut = Image.open('refs/ukuziom/kiwajka-minimax/home-cut-on-blue-171-199.png')
home = Image.new('RGBA', (W, 768), tuple(BLUE.astype(int)) + (255,)); home.alpha_composite(cut, (171, 199))
home.convert('RGB').save('refs/ukuziom/kiwajka-wide/home-wide-blue.png')
sq = np.asarray(Image.open('refs/ukuziom/kiwajka-home-blue.png').convert('RGB')).astype(float)
ed = Image.open('refs/ukuziom/kiwajka-uke/uke-peak-1.png').convert('RGB')
best = None
LEG = (slice(600, 676), slice(290, 510))          # feet and shins, which the edit must not move
for s in np.arange(0.735, 0.766, 0.003):
    n = round(1024 * s); r = np.asarray(ed.resize((n, n), Image.LANCZOS)).astype(float)
    for dx in range(-8, 9, 2):
        for dy in range(-8, 9, 2):
            can = np.tile(BLUE, (768, 768, 1)); x0, y0 = dx, dy
            sx, sy = max(0, -x0), max(0, -y0); tx, ty = max(0, x0), max(0, y0); w = min(n - sx, 768 - tx); h = min(n - sy, 768 - ty)
            can[ty:ty + h, tx:tx + w] = r[sy:sy + h, sx:sx + w]
            e = np.abs(can[LEG] - sq[LEG]).mean()
            if best is None or e < best[0]: best = (e, s, dx, dy, can)
e, s, dx, dy, can = best
print('uke peak registered: L1 %.2f scale %.3f offset %d,%d' % (e, s, dx, dy))
# the ground: whatever is blue-dominated and near the ground colour becomes the exact ground
dom = can[..., 2] - can[..., :2].max(2)
ground = (np.abs(can - BLUE).max(2) < 40) & (dom > 80)
ground = ndi.binary_opening(ground, iterations=1)
can[ground] = BLUE
wide = np.tile(BLUE, (768, W, 1)); wide[:, :768] = can
Image.fromarray(np.clip(np.round(wide), 0, 255).astype(np.uint8)).save('refs/ukuziom/kiwajka-wide/uke-peak-wide-blue.png')
