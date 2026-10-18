# S1 v2 layering: alpha = green-key ∪ (|full-plate| near the keyed figures); watershed split with seed boxes.
# usage: python3 layer_s1.py   (run from scratchpad root)
import json, numpy as np
from PIL import Image
from scipy import ndimage
D='scripts/i5/S1/'; P='pub/i5/'
F=np.array(Image.open(D+'full_raw.png').convert('RGB')).astype(float)
PL=np.array(Image.open(D+'plate_raw.png').convert('RGB')).astype(float)
G=np.array(Image.open(D+'green_raw.png').convert('RGB')).astype(float)
H,W=F.shape[:2]
# global shift check plate/green vs full
def shift(a,b):
    g1=ndimage.gaussian_filter(a.mean(2),2); g2=ndimage.gaussian_filter(b.mean(2),2); best=None
    for dy in range(-4,5):
        for dx in range(-4,5):
            e=np.median(np.abs(g1[20:-20,20:-20]-np.roll(g2,(dy,dx),(0,1))[20:-20,20:-20]))
            if best is None or e<best[0]: best=(round(e,2),dy,dx)
    return best
print('plate shift',shift(F,PL))
k=G[...,1]-np.maximum(G[...,0],G[...,2])
ka=1-np.clip((k-40)/70,0,1)
kam=ndimage.binary_opening(ka>0.5,iterations=1)
print('key-vs-full diff inside key', np.abs(G-F).mean(2)[ndimage.binary_erosion(kam,iterations=3)].mean().round(1))
d=ndimage.gaussian_filter(np.abs(ndimage.gaussian_filter(F,(1,1,0))-ndimage.gaussian_filter(PL,(1,1,0))).max(2),1.0)
R=ndimage.binary_dilation(kam,iterations=14)
dm=(d>30)&R
M=kam|dm
M=ndimage.binary_closing(M,iterations=3); M=ndimage.binary_fill_holes(M); M=ndimage.binary_opening(M,iterations=1)
lab,n=ndimage.label(M); sz=ndimage.sum(M,lab,range(1,n+1))
M=np.isin(lab,[j+1 for j in range(n) if sz[j]>400])
# below the waterline (bodies end at water) keep only key, not ripples
Image.fromarray((M*255).astype(np.uint8)).save('scripts/i5/work/S1_mask.png')
alpha=ndimage.gaussian_filter(M.astype(float),0.7)*M + ndimage.gaussian_filter(M.astype(float),0.7)*(~M)
# seeds (px boxes) : dove, jesus, john(+hands+stream)
seeds={'dove':[(640,110,740,185)],'jesus':[(620,340,750,590)],'john':[(850,240,1000,600),(700,270,760,335)]}
grad=ndimage.gaussian_gradient_magnitude(F.mean(2),1.5)
cost=np.clip(grad*4,0,250).astype(np.uint8); cost[~M]=255
mk=np.zeros((H,W),np.int16); names=list(seeds)
Me=ndimage.binary_erosion(M,iterations=2)
for i,nm in enumerate(names):
    for (x0,y0,x1,y1) in seeds[nm]:
        s=np.zeros_like(M); s[y0:y1,x0:x1]=True; mk[s&Me]=i+1
lab=ndimage.watershed_ift(cost,mk); lab[~M]=0
figs=[]; final=PL*0
own=np.zeros((H,W),int)
for i,nm in enumerate(names):
    m=lab==i+1
    l2,n2=ndimage.label(m); s2=ndimage.sum(m,l2,range(1,n2+1)); m=l2==(np.argmax(s2)+1)
    own[m]=i+1
for i,nm in enumerate(names):
    m=ndimage.binary_dilation(own==i+1,iterations=1)&(alpha>0.01)
    ys,xs=np.where(m); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    a=(alpha*m)[y0:y1,x0:x1]
    Image.fromarray(np.dstack([F[y0:y1,x0:x1],a*255]).clip(0,255).round().astype(np.uint8),'RGBA').save(P+f'S1_fig_{nm}.png',optimize=True)
    bb=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]
    figs.append(dict(name=nm,file=f'i5/S1_fig_{nm}.png',bbox=bb,px=[int(x0),int(y0),int(x1-x0),int(y1-y0)]))
    print(nm,bb,(x1-x0,y1-y0))
# overlap between figure bboxes' alpha (separability)
# final plate: generated plate under figures (dilated, feathered), full pixels elsewhere
Dm=ndimage.gaussian_filter(ndimage.binary_dilation(M,iterations=10).astype(float),4)[...,None]
plate=PL*Dm+F*(1-Dm)
Image.fromarray(plate.round().astype(np.uint8)).save(P+'S1_plate.jpg',quality=84,optimize=True,progressive=True)
Image.fromarray(F.astype(np.uint8)).save(P+'S1_full.jpg',quality=84,optimize=True,progressive=True)
comp=Image.open(P+'S1_plate.jpg').convert('RGBA')
for fg in figs: comp.alpha_composite(Image.open(P+f"S1_fig_{fg['name']}.png"),tuple(fg['px'][:2]))
comp=np.array(comp.convert('RGB')).astype(float)
err=np.abs(comp-F)
print('composite vs full mean',err.mean().round(2),'inside mask',err[M].mean().round(2),'p99',np.percentile(err.mean(2),99).round(1))
tint=F*0.5; cols=[[255,255,60],[255,60,60],[60,90,255]]
for i in range(3): tint[own==i+1]=F[own==i+1]*0.5+np.array(cols[i])*0.5
top=np.concatenate([F,comp],1); bot=np.concatenate([plate,tint],1)
Image.fromarray(np.concatenate([top,bot],0).astype(np.uint8)).resize((1600,round(1600*H/W))).save(P+'S1_check.jpg',quality=82)
json.dump(figs,open(D+'figs.json','w'))
