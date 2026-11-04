"""Małpka Kiwajka's MiniMax-H3 signature moves (scratch, hop, cheer) — the steps, run from the sprite-refs root:
  lock.py OUT --home refs/ukuziom/kiwajka-minimax/home-cut-on-blue-171-199.png --at 171,199 --pose-s 2 \
          --cell 768,768 --pivot 383.5,674 --fig 476 --webp 0 --reach 130 --ease 1 raw/<job>.mp4=a,b
          (cell 768 + that pivot = identity placement: lock.py's frames stay at clip size)
  fit.py                        the similarity clip frame -> the shipped cutout cell, fitted against monkey.webp
  MARGINS=28,44,30,0 pack.py packF "lockA:scratch~0,3" "lockB2:hop~0,3" lockC:cheer
                                into the moves atlas's own cell (288x300, the 230x256 box at 28,44), rebased on monkey.webp
  PEAKS=scratch=7,hop=9,cheer=9 peaks.py packF revF     peak cell next to the raw clip frame
  final.py packF monkey-moves.webp 70                    the shipped atlas + manifest (identical cells stored once)
Fit the similarity blue-frame (768x768 H3 first frame) -> shipped idle cell (276x268), against monkey.webp."""
import numpy as np, json, os
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
MG = os.environ.get('MUSICGAMES', os.path.expanduser('~/MusicGames')) + '/ukulele-warmup/art/jungle/'
cut = Image.open(D + '/../../../refs/ukuziom/kiwajka-minimax/home-cut-on-blue-171-199.png'); big = Image.new('RGBA', (768, 768)); big.paste(cut, (171, 199))
home = np.asarray(Image.open(MG + 'monkey.webp').convert('RGBA')).astype(float)   # 230x256, at cell offset 16,12
cell = np.zeros((268, 276, 4)); cell[12:268, 16:246] = home


def place(img, s, tx, ty, ss=3, CW=276, CH=268):
    """cell = s*frame + t, rendered at ss x and box-averaged (premultiplied)"""
    W, H = CW * ss, CH * ss
    aff = (1 / s / ss, 0, -tx / s, 0, 1 / s / ss, -ty / s)
    im = img.transform((W, H), Image.AFFINE, aff, Image.BICUBIC)
    a = np.asarray(im).astype(float); pm = a.copy(); pm[..., :3] *= a[..., 3:] / 255
    pm = pm.reshape(CH, ss, CW, ss, 4).mean((1, 3))
    out = pm.copy(); out[..., :3] = np.where(pm[..., 3:] > 0, pm[..., :3] * 255 / np.maximum(pm[..., 3:], 1e-3), 0)
    return out


if __name__ == '__main__':
    ys, xs = np.nonzero(cell[..., 3] > 128); print('cell fig bbox', xs.min(), ys.min(), xs.max(), ys.max())
    s0 = (ys.max() - ys.min()) / 475.; best = None
    for s in s0 * np.array([0.99, 0.995, 1, 1.005, 1.01]):
        for tx in np.arange(-3, 3.01, 0.5):
            for ty in np.arange(-3, 3.01, 0.5):
                TX = xs.min() - 171 * s + tx; TY = ys.min() - 199 * s + ty
                o = place(big, s, TX, TY, 2)
                e = np.abs(o[..., 3] - cell[..., 3]).mean() + np.abs((o[..., :3] - cell[..., :3]) * (cell[..., 3:] > 200)).mean()
                if best is None or e < best[0]: best = (e, s, TX, TY)
    print(best); json.dump(dict(zip(['err', 's', 'tx', 'ty'], map(float, best))), open(D + '/fit.json', 'w'))
