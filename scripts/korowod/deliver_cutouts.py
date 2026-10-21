"""Scale the cut pieces and write the game WebPs (q82). Points for cutouts.json are added by points.py."""
import json, os
from PIL import Image, ImageOps
CUT = "/home/user/sprite-refs/sheets/korowod/cut"; OUT = "/home/user/MusicGames/fingerpick-warmup/art/korowod"
os.makedirs(OUT, exist_ok=True)
src = {}
for d in os.listdir(CUT):
    for f in os.listdir(os.path.join(CUT, d)):
        if f.endswith(".png") and f != "check.png" and not f.startswith(("spare", "extra")): src[f[:-4]] = os.path.join(CUT, d, f)
PEOPLE = "lech warrior_a warrior_b mieszko dobrawa wojownik_1 wojownik_2 wojownik_3 wojownik_4 boleslaw banner_bearer crowd_1 crowd_2 crowd_3 crowd_4 flag_1 flag_2 flag_3 flag_4 flag_5 worker_1 worker_2 worker_3 worker_4 child_1 child_2 child_3 bishop paderewski goat_l goat_r".split()
BUILD = "oak_nest palatium cathedral hotel_bazar ratusz kamienice factory_gate".split()
ARMS = {"bishop_arm": ("bishop", 0.60, False), "paderewski_arm": ("paderewski", 0.80, True)}
scale = {}
def save(name, im, s, mirror=False):
    if mirror: im = ImageOps.mirror(im)
    if s != 1: im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im.save(os.path.join(OUT, name + ".webp"), "WEBP", quality=82, method=6); scale[name] = s
    return im
for n, p in sorted(src.items()):
    if n in ARMS: continue
    im = Image.open(p)
    if n in PEOPLE: s = min(1, 440 / im.height)
    elif n in BUILD: s = min(1, 820 / im.height)
    elif n == "crown": s = 0.75
    else: s = 1.0      # props, vehicles, martin (horse+rider), banner_pair, bushes: native size
    save(n, im, s)
for n, (body, k, mir) in ARMS.items():
    save(n, Image.open(src[n]), scale[body] * k, mir)
json.dump(scale, open("/home/user/sprite-refs/sheets/korowod/cut/scales.json", "w"), indent=1)
print(len(scale), "pieces")
