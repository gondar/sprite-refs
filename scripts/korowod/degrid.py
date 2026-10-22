"""Remove drawn grid lines from a sheet: rows/columns that are mostly dark across the sheet are repainted with
the key colour, but only on their dark pixels (figures are untouched). usage: degrid.py IN OUT KEYHEX"""
import sys, numpy as np
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(int)
key = np.array([int(sys.argv[3][i:i+2], 16) for i in (0, 2, 4)])
dark = im.sum(2) < 200
H, W = dark.shape
cols = np.nonzero(dark.mean(0) > 0.8)[0]; rows = np.nonzero(dark.mean(1) > 0.8)[0]
for c in cols:
    for d in range(-4, 5):
        x = c + d
        if 0 <= x < W:
            m = np.abs(im[:, x] - key).sum(1) > 60  # anything not key in a line column
            near = dark[:, max(0,x-6):x+7].any(1)
            im[m & near & (im[:, x].sum(1) < 450), x] = key
for r in rows:
    for d in range(-4, 5):
        y = r + d
        if 0 <= y < H:
            m = np.abs(im[y] - key).sum(1) > 60
            near = dark[max(0,y-6):y+7].any(0)
            im[y, m & near & (im[y].sum(1) < 450)] = key
Image.fromarray(im.astype(np.uint8)).save(sys.argv[2])
print("cols", list(cols), "rows", list(rows))
