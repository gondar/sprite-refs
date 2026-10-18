import numpy as np
from PIL import Image
from scipy import ndimage as ndi
W,H=1376,768
F=np.asarray(Image.open('B3_e1_raw.png').convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
P=np.asarray(Image.open('B3_plateg_raw.png').convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
Y,X=np.mgrid[0:H,0:W]
# --- Jesus mask (diff, outside shadow zone)
d=np.abs(ndi.gaussian_filter(F,(1.5,1.5,0))-ndi.gaussian_filter(P,(1.5,1.5,0))).max(2)
m=ndi.gaussian_filter(d,1.5)>14
m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=5)); m=ndi.binary_opening(m,iterations=4)
lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1))
cx=ndi.center_of_mass(m,lab,range(1,n+1))
jes=np.zeros_like(m)
big=np.isin(lab,[k+1 for k in range(n) if sz[k]>6000])
jes=big&(X<945)&~((X>872)&(Y<430))&((X>=662)|((Y>=495)&(X>=555)))
l2,n2=ndi.label(jes); s2=ndi.sum(jes,l2,range(1,n2+1)); jes=l2==(np.argmax(s2)+1)
jes=ndi.binary_opening(jes,iterations=7); l2,n2=ndi.label(jes); s2=ndi.sum(jes,l2,range(1,n2+1)); jes=ndi.binary_fill_holes(l2==(np.argmax(s2)+1))
print('jes bbox',np.argwhere(jes).min(0),np.argwhere(jes).max(0),int(jes.sum()))
print('jesus comps', [(int(sz[k]),[int(c) for c in cx[k]]) for k in range(n) if sz[k]>3000])
# --- shadow darkness
lf=ndi.gaussian_filter(F,(2.5,2.5,0)); lp=ndi.gaussian_filter(P,(2.5,2.5,0))
R=np.clip(lf.mean(2)/np.maximum(lp.mean(2),1),0,1)
D=np.clip((1-R-0.10)/0.90,0,1)
zone=(X>=100)&(X<705)&(Y>=130)&(((X<415)&(Y<660))|((X>=415)&(Y<495)))
zone&=~ndi.binary_dilation(jes,iterations=2)
D=D*zone
D=ndi.gaussian_filter(D,0.8)
Dbow=D*(X<380); Dpt=D*(X>=380)
# bowing: shift left 40 px ; pointing: mirror around its centre, keep place
Dbow2=Dbow
c=547; Xm=np.clip(2*c-X,0,W-1)
Dpt2=Dpt[Y,Xm]
Dn=np.maximum(Dbow2,Dpt2)
# never shade jug/cup/bench or Jesus
keep=np.zeros((H,W),bool)
keep|=(X>=415)&(Y>=495)
keep|=ndi.binary_dilation(jes,iterations=3)
Dn*=~keep
Dn=ndi.gaussian_filter(Dn,1.0)
# colour of shadow: same as originals (tinted multiply). estimate tint from old shadow
sh=(D>0.35); tint=(F[sh]/np.maximum(P[sh],1)).mean(0); print('tint',tint.round(3))
tint_n=tint/tint.mean()
old=ndi.gaussian_filter(ndi.binary_dilation((D>0.05)|(Dn>0.05),iterations=4).astype(float),3)
old=np.clip(old*2,0,1)[...,None]
k=(Dn/np.maximum(D[sh].mean()*0+1,1))[...,None]
darkmean=1-(F[sh].mean(0)/P[sh].mean(0))   # per-channel darkening at full shadow
okm=(D<0.03).astype(float)
G=np.dstack([ndi.gaussian_filter(F[...,c]*okm,20)/np.maximum(ndi.gaussian_filter(P[...,c]*okm,20),1e-3) for c in range(3)])
G=np.clip(G,0.5,1.5); Pa=P*G
Fn_sh=Pa*(1-Dn[...,None]*np.clip(darkmean/np.maximum(D[sh].mean(),1e-3),0,1))
Fn=F*(1-old)+Fn_sh*old
# --- darken middle wall toward indigo (not on Jesus)
cxw,cyw=0.675*W,0.40*H
g=np.exp(-(((X-cxw)/(0.16*W))**2+((Y-cyw)/(0.20*H))**2))
lamp=np.exp(-(((X-0.835*W)/(0.07*W))**2+((Y-0.52*H)/(0.12*H))**2))
g=np.clip(g-1.2*lamp,0,1)*0.85+0.15*np.clip(1-1.5*lamp,0,1)*(Y<0.85*H)
grade=lambda img,w: img*(1-0.2*w[...,None])+np.array([-16,-8,21])*w[...,None]
jm=ndi.gaussian_filter(ndi.binary_dilation(jes,iterations=1).astype(float),1)[...,None]
Fn2=grade(Fn,g)*(1-jm)+Fn*jm
Pn=grade(P,g)
Image.fromarray(Fn2.clip(0,255).astype(np.uint8)).save('B3_fixed.png')
Image.fromarray(Pn.clip(0,255).astype(np.uint8)).save('B3_plate_fixed.png')
Image.fromarray(Fn2.clip(0,255).astype(np.uint8)).save('B3_fixed.jpg',quality=90)
out=Fn2
print('meanV',np.asarray(Image.fromarray(out.clip(0,255).astype(np.uint8)).convert('HSV'))[...,2].mean().round(1),'wall(0.65,0.35)',out[int(.35*H)-5:int(.35*H)+5,int(.65*W)-5:int(.65*W)+5].reshape(-1,3).mean(0).round(1))
outside=~ndi.binary_dilation((old[...,0]>0.01)|(g>0.02)|jes,iterations=2)
print('mean err outside edited areas',np.abs(out-F)[outside].mean().round(3), 'jesus err', np.abs(out-F)[jes].mean().round(3))
