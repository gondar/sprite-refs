import sys, glob, numpy as np
from PIL import Image
A="/home/user/sprite-refs/refs/korowod/eagle3/anim"
def th(im):
    t=np.asarray(im.convert("RGBA").resize((128,128),Image.BILINEAR),float)/255; return np.dstack([t[...,:3]*t[...,3:],t[...,3:]])
for d,pose in [a.split(":") for a in sys.argv[1:]]:
    H=th(Image.open(f"{A}/place-{pose}.png")); fs=sorted(glob.glob(f"work/{d}/k_*.png")); out=[]
    for f in fs:
        im=Image.open(f); a=np.asarray(im)[...,3]>128; ys=np.nonzero(a.any(1))[0]
        out.append((np.abs(th(im)-H).mean()*100, ys.min(), ys.max()))
    print(d, " ".join(f"{i}:{x[0]:.1f}/{x[1]}" for i,x in enumerate(out)))
