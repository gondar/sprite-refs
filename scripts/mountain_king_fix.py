"""Mountain King H3 clip (20261015-215628-c72e2d): the background drifted magenta → lavender → teal, so
the per-frame border key leaves a soft shadow ring under the throne and the despill tints the stone.
The throne and legs never move, so (1) below 72% of the reference figure's height every frame's alpha
is clipped to the clean first frame's silhouette (dilated 5 px), and (2) every frame is colour-matched
to that first frame by per-channel gains measured on the same static region."""
import glob, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
root = sys.argv[1]; out = sys.argv[2]
ref = np.asarray(Image.open(os.path.join(root, "idle", "f_00.png")), dtype=float)
ra = ref[..., 3] > 128
ys = np.where(ra.any(1))[0]; top, bot = ys.min(), ys.max()
cut = int(top + 0.72 * (bot - top))
mask = ndi.binary_dilation(ra, iterations=5)
region = np.zeros_like(ra); region[cut:] = True
stat = region & ndi.binary_erosion(ra, iterations=6)
refmean = ref[stat][:, :3].mean(0)
for seg in ["idle", "nod", "cheer"]:
    os.makedirs(os.path.join(out, seg), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(root, seg, "f_*.png"))):
        im = np.asarray(Image.open(f), dtype=float).copy()
        a = im[..., 3]
        a[cut:] = np.where(mask[cut:], a[cut:], 0)
        sel = stat & (a > 200)
        if sel.sum() > 500:
            g = refmean / np.maximum(im[sel][:, :3].mean(0), 1)
            im[..., :3] = np.clip(im[..., :3] * g, 0, 255)
        im[..., 3] = a
        Image.fromarray(im.astype(np.uint8)).save(os.path.join(out, seg, os.path.basename(f)))
print("cut row", cut, "of", top, bot)
