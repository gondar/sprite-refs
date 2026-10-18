import numpy as np
from PIL import Image
from scipy import ndimage as ndi
W,H=1376,768
F=np.asarray(Image.open('B3_e1_raw.png').convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
P=np.asarray(Image.open('B3_plateg_raw.png').convert('RGB').resize((W,H),Image.LANCZOS)).astype(float)
Y,X=np.mgrid[0:H,0:W]
d=np.abs(ndi.gaussian_filter(F,(1.5,1.5,0))-ndi.gaussian_filter(P,(1.5,1.5,0))).max(2)
m=ndi.gaussian_filter(d,1.5)>14
m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=5)); m=ndi.binary_opening(m,iterations=4)
lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1))
big=np.isin(lab,[k+1 for k in range(n) if sz[k]>6000])
jes=big&(X<945)&~((X>872)&(Y<430))&((X>=662)|((Y>=495)&(X>=555)))
l2,n2=ndi.label(jes); s2=ndi.sum(jes,l2,range(1,n2+1)); jes=l2==(np.argmax(s2)+1)
jes=ndi.binary_opening(jes,iterations=7); l2,n2=ndi.label(jes); s2=ndi.sum(jes,l2,range(1,n2+1)); jes=ndi.binary_fill_holes(l2==(np.argmax(s2)+1))
jes&=~((X<702)&(Y<340))&~(Y<118)
np.save("B3_jes.npy",jes)
# crisp shadow alpha
lf=ndi.gaussian_filter(F,(1.0,1.0,0)); lp=ndi.gaussian_filter(P,(1.0,1.0,0))
R=np.clip(lf.mean(2)/np.maximum(lp.mean(2),1),0,1.2)
A=np.clip((0.82-R)/0.2,0,1)
zone=(X>=100)&(X<705)&(Y>=130)&(((X<415)&(Y<660))|((X>=415)&(Y<495)))
zone&=~ndi.binary_dilation(jes,iterations=2)
A=ndi.binary_opening(A>0.5,iterations=2)&zone
lab,n=ndi.label(A); sz=ndi.sum(A,lab,range(1,n+1)); A=np.isin(lab,[k+1 for k in range(n) if sz[k]>3000])
A=ndi.binary_fill_holes(A)
sh=A.copy()
tint=np.median(F[ndi.binary_erosion(sh,iterations=4)]/np.maximum(P[ndi.binary_erosion(sh,iterations=4)],1),axis=0); print('tint',tint.round(3))
Abow=A&(X<380); Apt=A&(X>=380)
# pointing: extend the back edge that hides behind Jesus by filling to x=700 where rows are shadowed near the cut
c=529; Xm=np.clip(2*c-X,0,W-1); Apt2=Apt[Y,Xm]
Apt2&=X>=398+40*((Y-360)/160.0)**2
Abow2=np.roll(Abow,-28,axis=1)
# jug/cup mask: brownish pixels in the lower-left box
box=(X>=95)&(X<285)&(Y>=520)&(Y<720)
jug=box&((P[...,0]-P[...,2])>6)&(P.mean(2)>40); jug=ndi.binary_closing(jug,iterations=3); jug=ndi.binary_fill_holes(jug); jug=ndi.binary_opening(jug,iterations=2)
An=(Abow2|Apt2)&~jug&~ndi.binary_dilation(jes,iterations=1)&~((X>=415)&(Y>=495))
lab,n=ndi.label(An); sz=ndi.sum(An,lab,range(1,n+1)); An=np.isin(lab,[k+1 for k in range(n) if sz[k]>1500])
a=ndi.gaussian_filter(An.astype(float),1.6)
# shadow-free base: P tone-matched to F
okm=(~ndi.binary_dilation(sh|jes,iterations=8)).astype(float)
G=np.dstack([ndi.gaussian_filter(F[...,k]*okm,35)/np.maximum(ndi.gaussian_filter(P[...,k]*okm,35),1e-3) for k in range(3)]); G=np.clip(G,0.5,1.5)
Pa=P*G
old=ndi.gaussian_filter(ndi.binary_dilation(sh|An,iterations=5).astype(float),3)[...,None]
base=F*(1-old)+Pa*old
Fn=base*(1-a[...,None])+base*tint*a[...,None]
# grade middle wall toward indigo
cxw,cyw=0.675*W,0.40*H
g=np.exp(-(((X-cxw)/(0.16*W))**2+((Y-cyw)/(0.20*H))**2))
lamp=np.exp(-(((X-0.835*W)/(0.07*W))**2+((Y-0.52*H)/(0.12*H))**2))
g=np.clip(g-1.2*lamp,0,1)*0.85+0.15*np.clip(1-1.5*lamp,0,1)*(Y<0.85*H)
sj=ndi.gaussian_filter(ndi.binary_erosion(jes,iterations=4).astype(float),8)
gj=g*(1-0.7*sj)
grade=lambda img,w: img*(1-0.2*w[...,None])+np.array([-16,-8,21])*w[...,None]
Fn2=grade(Fn,gj); Pn=grade(Pa,g)  # plate graded fully (people removed)
for nm,im in [('B3_fixed',Fn2),('B3_plate_fixed',Pn)]:
    Image.fromarray(im.clip(0,255).astype(np.uint8)).save(nm+'.png')
Image.fromarray(Fn2.clip(0,255).astype(np.uint8)).save('B3_fixed.jpg',quality=90)
hv=np.asarray(Image.fromarray(Fn2.clip(0,255).astype(np.uint8)).convert('HSV'))
print('meanV',hv[...,2].mean().round(1),'wall(0.65,0.35)',Fn2[int(.35*H)-5:int(.35*H)+5,int(.65*W)-5:int(.65*W)+5].reshape(-1,3).mean(0).round(1))
print('head tops y', [np.argwhere(z).min(0)[0]/H for z in (Abow2,Apt2) if z.any()])
