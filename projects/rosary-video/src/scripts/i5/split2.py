# usage: split.py ID name:x0,y0,x1,y1 name:... [--pair NAME]
# seeds are boxes (px) inside each figure; watershed on image gradient inside work/ID_mask.png
import sys, json, numpy as np
from PIL import Image
from scipy import ndimage
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
S=B+'scripts/i5/work/'; P=B+'pub/i5/'
i=sys.argv[1]; args=sys.argv[2:]
pair=None
if '--pair' in args: pair=args[args.index('--pair')+1]; args=args[:args.index('--pair')]
f=np.array(Image.open(S+f'{i}_full.png').convert('RGB')).astype(float)
p=np.array(Image.open(S+f'{i}_plate.png').convert('RGB')).astype(float)
M=np.array(Image.open(S+f'{i}_mask.png'))>0
H,W=M.shape
# final plate: generated plate only under the figures (dilated, feathered), full image elsewhere
D=ndimage.gaussian_filter(ndimage.binary_dilation(M,iterations=10).astype(float),4)[...,None]
plate=p*D+f*(1-D)
Image.fromarray(plate.clip(0,255).astype(np.uint8)).save(P+f'{i}_plate.jpg',quality=82,optimize=True,progressive=True)
alpha=ndimage.gaussian_filter(M.astype(float),0.8)
# watershed
grad=ndimage.gaussian_gradient_magnitude(f.mean(2),1.5)
cost=np.clip(grad*4,0,250).astype(np.uint8); cost[~M]=255
markers=np.zeros((H,W),np.int16); names=[]
for a in args:
    n,b=a.split(":"); x0,y0,x1,y1=map(int,b.split(","))
    if n not in names: names.append(n)
    k=names.index(n)
    sub=np.zeros_like(M); sub[y0:y1,x0:x1]=True
    markers[sub&ndimage.binary_erosion(M,iterations=3)]=k+1
# (no background marker: it steals edge pixels)
lab=ndimage.watershed_ift(cost,markers)
figs=[]
def save(name,m):
    m=ndimage.binary_dilation(m,iterations=1)&(alpha>0.01)
    ys,xs=np.where(m); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    a=(alpha*m)[y0:y1,x0:x1]
    rgba=np.dstack([f[y0:y1,x0:x1],a*255]).clip(0,255).astype(np.uint8)
    Image.fromarray(rgba,'RGBA').save(P+f'{i}_fig_{name}.png',optimize=True)
    bb=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]
    print(name,(x1-x0,y1-y0),bb); figs.append(dict(name=name,file=f'i5/{i}_fig_{name}.png',bbox=bb,px=[int(x0),int(y0),int(x1-x0),int(y1-y0)]))
for k,n in enumerate(names):
    m=(lab==k+1)&M
    # keep the biggest piece + pieces attached; drop specks
    l2,n2=ndimage.label(m); sz=ndimage.sum(m,l2,range(1,n2+1))
    big=np.argmax(sz)+1
    for j in range(1,n2+1):   # orphan pieces: give to the figure whose main body is nearest
        if j==big: continue
        piece=l2==j; lab[piece]=0
    lab[(lab==k+1)&~(l2==big)]=0
# reassign orphans (pixels in M with lab 0) to nearest kept figure
own=np.where(M,lab,0); own[own<0]=0
idx=ndimage.distance_transform_edt(own==0,return_distances=False,return_indices=True)
lab2=own[idx[0],idx[1]]
for k,n in enumerate(names):
    m=(lab2==k+1)&M
    l2,n2=ndimage.label(m); sz=ndimage.sum(m,l2,range(1,n2+1))
    m=np.isin(l2,[j+1 for j in range(n2) if sz[j]>150])
    save(n,m)
lab=lab2
if pair: save(pair,M)
json.dump(dict(W=W,H=H,figs=figs),open(S+f'{i}_figs.json','w'))
# check: composite plate + figs at their boxes vs full
comp=Image.open(P+f'{i}_plate.jpg').convert('RGBA')
for fg in figs:
    if fg['name']==pair: continue
    comp.alpha_composite(Image.open(P+f"{i}_fig_{fg['name']}.png"),tuple(fg['px'][:2]))
comp=np.array(comp.convert('RGB')).astype(float)
print('mean abs diff comp vs full',np.abs(comp-f).mean().round(2),'inside figs',np.abs(comp-f)[M].mean().round(2))
pl=np.array(Image.open(P+f'{i}_plate.jpg').convert('RGB'))
tint=f.copy(); tint[lab==1]=tint[lab==1]*0.6+[255,60,60]*np.array(0.4)
tint[lab==2]=tint[lab==2]*0.6+np.array([60,60,255])*0.4
tint[~M]=f[~M]*0.5
top=np.concatenate([f,comp],1); bot=np.concatenate([pl,tint],1)
Image.fromarray(np.concatenate([top,bot],0).astype(np.uint8)).resize((1600,round(1600*2*H/(2*W)))).save(P+f'{i}_check.jpg',quality=82)
