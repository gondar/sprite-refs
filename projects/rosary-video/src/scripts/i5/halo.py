# add the halo ring (from |full-plate|) into S2 jesus figure
import json, numpy as np
from PIL import Image
from scipy import ndimage
sid='S2'; D='scripts/i5/'+sid
F=np.array(Image.open(f'{D}/full_raw.png').convert('RGB')).astype(float)
P=np.array(Image.open(f'pub/i5/{sid}_plate_raw.png').convert('RGB')).astype(float)
H,W=F.shape[:2]
meta=json.load(open(f'{D}/figs.json')); j=[m for m in meta if m['name']=='jesus'][0]
x,y,w,h=j['bbox']; X0,Y0=round(x*W),round(y*H)
fig=np.array(Image.open('pub/'+j['file'])).astype(float)
A=np.zeros((H,W)); C=F.copy()
A[Y0:Y0+fig.shape[0],X0:X0+fig.shape[1]]=fig[...,3]/255
d=ndimage.gaussian_filter(np.abs(F-P).mean(2),0.8)
# head region: top 30% of jesus box, widened
rx0,rx1=int(X0-0.02*W),int(X0+w*W*0.75); ry0,ry1=int(Y0-0.05*H),int(Y0+0.16*H)
reg=np.zeros((H,W),bool); reg[ry0:ry1,rx0:rx1]=True
hm=(d>14)&reg&(A<0.5)
lab,n=ndimage.label(ndimage.binary_closing(hm,iterations=2)); sz=ndimage.sum(hm,lab,range(1,n+1))
keep=np.isin(lab,1+np.where(sz>40)[0])
ha=np.clip((d-8)/25,0,1)*ndimage.binary_dilation(keep,iterations=1)
A=np.maximum(A,ha)
ys,xs=np.where(A>0.03); pad=3
y0,y1=max(ys.min()-pad,0),min(ys.max()+pad+1,H); x0,x1=max(xs.min()-pad,0),min(xs.max()+pad+1,W)
Image.fromarray(np.dstack([F,A*255]).round().astype(np.uint8)[y0:y1,x0:x1],'RGBA').save('pub/'+j['file'],optimize=True)
j['bbox']=[round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)]; j['px']=[int(x1-x0),int(y1-y0)]
json.dump(meta,open(f'{D}/figs.json','w')); print(j)
comp=Image.fromarray(P.astype(np.uint8)).convert('RGBA')
for mt in meta:
    f=Image.open('pub/'+mt['file']); comp.alpha_composite(f,(round(mt['bbox'][0]*W),round(mt['bbox'][1]*H)))
C=np.array(comp.convert('RGB')).astype(float); print('mean',np.abs(C-F).mean())
Image.fromarray(np.hstack([F,C])[int(0.15*H):int(0.6*H), int(0.4*W):int(0.75*W)].astype(np.uint8) if False else np.hstack([F[ry0:ry1+150,rx0:rx1],C[ry0:ry1+150,rx0:rx1]]).astype(np.uint8)).save(f'{D}/halo_chk.jpg')
