from PIL import Image
import numpy as np
from scipy import ndimage as ndi
src=np.array(Image.open('/home/user/MusicGames/ukulele-warmup/art/podstawy/hand-fret-tip.webp').convert('RGBA')).astype(float)
H,W=src.shape[:2]; P=lambda p,n: int(round(p/100*n))
D=P(4.0,W); NT,NB=P(21.6,H),P(53.0,H); FADE=P(9,H)
r,g,b,al=[src[...,i] for i in range(4)]
skin=(al>40)&(r>170)&(r-b>55)&(g<215)
box=np.zeros((H,W),bool); box[P(17,H):P(66,H), P(63.5,W):P(80,W)]=True
m=skin&box
lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=2))
m_move=ndi.binary_dilation(m,iterations=1)&box&(al>0)
m_old=ndi.binary_dilation(m,iterations=4)&box
out=src.copy()
# background for the neck band: board texture from the clean strip 77.4-80.8 % (between finger and nut), tiled
s0,s1=P(77.6,W),P(80.8,W); sw=s1-s0
band=np.zeros((H,W),bool); band[NT:NB]=True
ys,xs=np.nonzero(m_old&band)
out[ys,xs]=src[ys, s0+((xs-xs.min())%sw)]
# fret-1 wire: copy the fret-2 wire columns shifted by the fret spacing
fo=P(18.2,W); x2a,x2b=P(47.15,W),P(48.65,W)
for y in range(NT,NB):
    for x in range(x2a,x2b):
        if m_old[y,x+fo]: out[y,x+fo]=src[y,x]
# below the neck: old finger area -> transparent (it is redrawn shifted)
below=m_old&~band
out[below,3]=0
# shifted finger
fin=np.zeros_like(src)
for y in range(P(17,H),P(66,H)):
    d=D if y<NB else int(round(D*max(0,1-(y-NB)/FADE)))
    xs=np.nonzero(m_move[y])[0]
    if len(xs): fin[y,xs+d]=src[y,xs]
A=fin[...,3:4]/255
out[...,:3]=fin[...,:3]*A+out[...,:3]*(1-A)
out[...,3]=np.maximum(out[...,3]*(1-A[...,0])+fin[...,3]*A[...,0], fin[...,3])
# below the neck: where the old finger was and nothing new lands, but the ORIGINAL had other content (palm/middle finger) -> keep original
keep=below&(fin[...,3]<10)&~m_old  # (empty by construction)
# fill tiny enclosed holes
op=out[...,3]>128; holes=ndi.binary_fill_holes(op)&~op
lab,n=ndi.label(holes); sz=ndi.sum(holes,lab,range(1,n+1)); holes=np.isin(lab,[i+1 for i,v in enumerate(sz) if v<3000])
idx=ndi.distance_transform_edt(~(op&~holes),return_distances=False,return_indices=True)
for c in range(4): out[...,c]=np.where(holes,out[...,c][idx[0],idx[1]],out[...,c])
# drop faint specks below the neck, despill edges
lowa=(out[...,3]<90)&(np.arange(H)[:,None]>=NB); out[lowa,3]=0
near=ndi.distance_transform_edt(out[...,3]>250)<=3
r,g,b=out[...,0],out[...,1],out[...,2]; lim=np.maximum((r+b)/2,np.minimum(r,b))
out[...,1]=np.where(near&(g>lim),lim,g)
out[...,:3][out[...,3]==0]=0
Image.fromarray(out.clip(0,255).astype('uint8'),'RGBA').save('r3fix/tip-new.png')
