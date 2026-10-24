"""Home pictures for the Stajenka donkey play on MiniMax-H3 (sprite-pipeline §2: first frame = last frame, flat blue).

  donkey-home.png    the donkey's stand pose (sheet-animals-big2, row 0 col 0) on #2F6BD8, 1280 x 720,
                     the figure ~64 % of the height, feet on a common baseline, room for a kick and a bray
  townsman-src.webp   the lantern walker cut from sheet-movers (row 3 col 0): the identity reference for the
                     Nano Banana edit that frees his hands (townsman-edit.txt) -> townsman-home.png

Run from the repo root: python3 scripts/wintertown_donkey_h3.py
"""
from PIL import Image
import numpy as np

BLUE = (47, 107, 216)
OUT = "refs/wintertown/h3/"


def cut(sheet, cols, rows, c, r):
    im = Image.open(sheet).convert("RGB")
    w, h = im.size
    cell = np.array(im.crop((c * w // cols, r * h // rows, (c + 1) * w // cols, (r + 1) * h // rows))).astype(int)
    R, G, B = cell[..., 0], cell[..., 1], cell[..., 2]
    dom = G - np.maximum(R, B)                      # how much the green ground dominates
    a = np.clip((120 - dom) * 255 / 80, 0, 255)     # 40 -> opaque, 120 -> clear
    keep = a > 8
    rgb = cell.copy()
    spill = keep & (G > np.maximum(R, B))
    rgb[..., 1] = np.where(spill, np.maximum(R, B), G)   # clamp the green fringe
    ys, xs = np.where(keep)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([rgb, a]).astype(np.uint8)[y0:y1, x0:x1]
    return Image.fromarray(rgba, "RGBA")


def on_blue(fig, name, frac=.64, cx=.5, feet=.84):
    W, H = 1280, 720
    k = frac * H / fig.height
    fig = fig.resize((round(fig.width * k), round(fig.height * k)), Image.LANCZOS)
    bg = Image.new("RGB", (W, H), BLUE)
    bg.paste(fig, (round(W * cx - fig.width / 2), round(H * feet - fig.height)), fig)
    bg.save(OUT + name)
    print(OUT + name, fig.size)


if __name__ == "__main__":
    donkey = cut("refs/wintertown/gen/sheet-animals-big2.webp", 4, 3, 0, 0)
    on_blue(donkey, "donkey-home.png", frac=.6, cx=.5)
    town = cut("refs/wintertown/gen/sheet-movers.webp", 4, 4, 0, 3)
    town.save("refs/wintertown/style/townsman-src.webp", lossless=True)
    print("refs/wintertown/style/townsman-src.webp", town.size)
