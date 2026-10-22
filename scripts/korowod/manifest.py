import json, os, numpy as np
from PIL import Image
D = "/home/user/MusicGames/fingerpick-warmup/art/korowod"
names = sorted(f[:-5] for f in os.listdir(D) if f.endswith(".webp") and not f.startswith("bg-"))
man = {}
for n in names:
    im = Image.open(os.path.join(D, n + ".webp")); a = np.array(im)[..., 3] > 128
    ys = np.nonzero(a.any(1))[0]; band = a[ys.max() - max(3, int(0.03 * im.height)):ys.max() + 1].any(0)
    xs = np.nonzero(band)[0]
    man[n] = {"src": f"art/korowod/{n}.webp", "w": im.width, "h": im.height, "foot": [int(round(xs.mean())), int(ys.max())]}
man["bishop"]["pin"] = {"arm": "bishop_arm", "at": [62, 268]}
man["bishop_arm"].update(pivot=[39, 27], rest=0, behind=False)
man["paderewski"]["pin"] = {"arm": "paderewski_arm", "at": [50, 288]}
man["paderewski_arm"].update(pivot=[235, 250], rest=0, behind=True)
man["oak_nest"]["nest"] = [340, 335]
man["hotel_bazar"]["balcony"] = [308, 505]
man["banner_pair"]["cloth"] = [60, 40, 630, 110]
for k in ("bishop_arm", "paderewski_arm"): man[k].pop("foot")
json.dump(man, open(os.path.join(D, "cutouts.json"), "w"), indent=1)
print(len(man)); print(json.dumps({k: man[k] for k in ["bishop", "bishop_arm", "lech", "tank"]}))
