# usage: layer.py ID mode(key|diff) name:x0-x1[,...]   -> builds figure PNGs + check
# key: alpha from green-key edit; diff: alpha from |full-plate|. RGB always from full (exact approved pixels).
import sys, json, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/i5/'
id, mode = sys.argv[1], sys.argv[2]
src = sys.argv[3] if len(sys.argv)>3 and not ':' in sys.argv[3] else None
specs=[a for a in sys.argv[3:] if ':' in a]
full=np.array(Image.open(P+f'{id}_full.jpg').convert('RGB')).astype(float)
H,W=full.shape[:2]
def load(f): return np.array(Image.open(f).convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
plate=load(P+f'{id}_gen_plate_raw.png')
if mode=='key':
    g=load(src or P+f'{id}_gen_figs_raw.png')
    k=g[...,1]-np.maximum(g[...,0],g[...,2])
    al=1-np.clip((k-40)/(110-40),0,1)
    diffimg=np.abs(g-full).mean(2)
else:
    d=np.abs(full-plate).max(2)
    d=ndimage.gaussian_filter(d,2.0)
    al=np.clip((d-18)/(40-18),0,1)
solid=ndimage.binary_opening(al>0.5,iterations=2)
solid=ndimage.binary_closing(solid,iterations=4)
solid=ndimage.binary_fill_holes(solid)
lab,n=ndimage.label(solid)
sizes=ndimage.sum(np.ones((H,W)),lab,range(1,n+1))
big=[l+1 for l in range(n) if sizes[l]>1500]
mask=np.isin(lab,big)
if mode=='diff': al=np.where(ndimage.binary_erosion(mask,iterations=2),1.0,al*ndimage.binary_dilation(mask,iterations=2))
else: al=al*ndimage.binary_dilation(mask,iterations=3)
al=np.array(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(float)/255
out={}; selall=np.zeros((H,W),bool); figs=[]
for s in specs:
    name,r,*ry=s.split(':'); x0,x1=[float(v)*W for v in r.split('-')]; ya,yb=[float(v)*H for v in (ry[0].split('-') if ry else '0-1'.split('-'))]
    sel=np.zeros((H,W),bool)
    for l in big:
        cy,cx=ndimage.center_of_mass(lab==l)
        if x0<=cx<x1 and ya<=cy<yb: sel|=lab==l
    sel=ndimage.binary_dilation(sel,iterations=5)
    a=al*sel
    ys,xs=np.where(a>0.03); pad=2
    y0,y1,xa,xb=max(ys.min()-pad,0),min(ys.max()+pad+1,H),max(xs.min()-pad,0),min(xs.max()+pad+1,W)
    rgba=np.dstack([full,a*255])[y0:y1,xa:xb]
    Image.fromarray(np.round(rgba).astype(np.uint8),'RGBA').save(P+f'{id}_fig_{name}.png',optimize=True)
    selall|=a>0.03; figs.append(a)
    out[name]=[round(xa/W,4),round(y0/H,4),round((xb-xa)/W,4),round((y1-y0)/H,4)]
    if mode=='key':
        m=a>0.9; print(name,'key-vs-full mean abs diff inside figure:',round(diffimg[m].mean(),1))
hole=ndimage.gaussian_filter(ndimage.binary_dilation(selall,iterations=18).astype(float),5)[...,None]
plate=full*(1-hole)+plate*hole
Image.fromarray(np.round(plate).astype(np.uint8)).save(P+f'{id}_plate.jpg',quality=82,optimize=True,progressive=True)
comp=plate.copy()
for a in figs: comp=comp*(1-a[...,None])+full*a[...,None]
err=np.abs(comp-full).mean(2)
print('composite vs full: mean',round(err.mean(),2),'p99',round(np.percentile(err,99),1))
# check image: top composite, bottom = figures over magenta + error heat
chk=np.dstack([np.full((H,W),255.),np.zeros((H,W)),np.full((H,W),255.)])
A=al[...,None]*np.isin(lab,big)[...,None]
heat=np.clip(err*4,0,255)
bot=np.concatenate([(chk*(1-A)+full*A),np.dstack([heat,heat,heat])],1)
top=np.concatenate([comp,plate],1)
Image.fromarray(np.concatenate([top,bot],0).astype(np.uint8)).resize((W,H)).save(P+f'{id}_check.jpg',quality=80)
json.dump(out,open(P+f'{id}_bbox_tmp.json','w')); print(out)
