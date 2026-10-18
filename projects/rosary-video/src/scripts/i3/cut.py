# usage: cut.py SHEET.png OUT1.png [OUT2.png ...]  -> keys flat border colour, finds N largest blobs (left->right), trims, max 900px
import sys, importlib.util, numpy as np
from PIL import Image
from scipy import ndimage
spec=importlib.util.spec_from_file_location("key","/home/user/MusicGames/.claude/skills/asset-sheet/scripts/key.py")
key=importlib.util.module_from_spec(spec); spec.loader.exec_module(key)
sheet, outs = sys.argv[1], sys.argv[2:]
rgb=np.array(Image.open(sheet).convert("RGB")).astype(float)
b=np.concatenate([rgb[:4].reshape(-1,3),rgb[-4:].reshape(-1,3),rgb[:,:4].reshape(-1,3),rgb[:,-4:].reshape(-1,3)])
bg=np.median(b,0); d=np.sqrt(((rgb-bg)**2).sum(2))
LO,HI=float(__import__("os").environ.get("LO",22)),float(__import__("os").environ.get("HI",60))
al=np.clip((d-LO)/(HI-LO),0,1)
solid=ndimage.binary_opening(al>0.5,iterations=2)
holes=ndimage.binary_fill_holes(solid)&~solid
hl,hn=ndimage.label(holes)
if hn:
    hs=ndimage.sum(np.ones_like(al),hl,range(1,hn+1))
    solid|=np.isin(hl,1+np.where(hs<150)[0])
interior=ndimage.binary_erosion(solid,iterations=3)
al=np.where(interior,1.0,al*ndimage.binary_dilation(solid,iterations=2))
a3=np.maximum(al,1e-3)[...,None]
col=np.where(interior[...,None],rgb,np.clip((rgb-(1-al)[...,None]*bg)/a3,0,255))
rgba=np.dstack([col,al*255]); a=rgba[...,3]
mask=ndimage.binary_closing(a>40, iterations=6)
lab,n=ndimage.label(mask)
sizes=ndimage.sum(np.ones_like(a),lab,range(1,n+1))
keep=sorted(np.argsort(sizes)[::-1][:len(outs)]+1, key=lambda l: ndimage.center_of_mass(lab==l)[1])
# merge small blobs (>200px) into nearest kept blob
for l in range(1,n+1):
    if l in keep or sizes[l-1]<200: continue
    cy,cx=ndimage.center_of_mass(lab==l)
    near=min(keep,key=lambda k: abs(ndimage.center_of_mass(lab==k)[1]-cx)); lab[lab==l]=near
for l,o in zip(keep,outs):
    m=ndimage.binary_dilation(lab==l, iterations=3)
    im=rgba.copy(); im[...,3]*=m
    ys,xs=np.where(im[...,3]>8); pad=4
    y0,y1,x0,x1=max(ys.min()-pad,0),ys.max()+pad+1,max(xs.min()-pad,0),xs.max()+pad+1
    out=Image.fromarray(np.round(im[y0:y1,x0:x1]).astype(np.uint8),"RGBA")
    if max(out.size)>900: out.thumbnail((900,900),Image.LANCZOS)
    out.save(o,optimize=True); print(o,out.size)
