from PIL import Image
import numpy as np
from scipy import ndimage as ndi
def despill(a,dist=3):
    op=a[...,3]>10; near=ndi.distance_transform_edt(a[...,3]>250)<=dist
    r,g,b=a[...,0],a[...,1],a[...,2]; lim=np.maximum((r+b)/2, np.minimum(r,b))
    a[...,1]=np.where(near&op&(g>lim),lim,g); return a
im=np.array(Image.open('keyed/fret-flat2.png').convert('RGBA')).astype(float); H,W=im.shape[:2]
src=im.copy(); out=im.copy()
X0,X1,Y0,Y1=842,992,185,575; NB=455
r,g,b,al=[src[...,i] for i in range(4)]
skin=(al>200)&(r>185)&(r-b>80)&(g<210)&(g>110)
for y in range(Y0,Y1):
    s=1.45 if y<NB else 1.45-0.45*min(1,(y-NB)/(Y1-NB))
    row=src[y,X0:X1]; m=skin[y,X0:X1]
    if not m.any(): continue
    xs=np.nonzero(m)[0]; L,R=xs.min(),xs.max()          # finger span in this row (relative)
    seg=row[L:R+1]; n=len(seg); nn=int(round(n*s))
    xi=np.linspace(0,n-1,nn)
    new=np.stack([np.interp(xi,np.arange(n),seg[:,c]) for c in range(4)],1)
    x=X0+L
    dstw=min(nn,W-x)
    # keep the original where the new row would be transparent
    A=(new[:dstw,3:4]/255)
    out[y,x:x+dstw,:3]=new[:dstw,:3]*A+out[y,x:x+dstw,:3]*(1-A)
    out[y,x:x+dstw,3]=np.maximum(out[y,x:x+dstw,3],new[:dstw,3])
# fill small enclosed holes with the nearest pixel
op=out[...,3]>128; holes=ndi.binary_fill_holes(op)&~op
lab,n=ndi.label(holes); sz=ndi.sum(holes,lab,range(1,n+1)); holes=np.isin(lab,[i+1 for i,v in enumerate(sz) if v<6000])
idx=ndi.distance_transform_edt(~op,return_distances=False,return_indices=True)
for c in range(3): out[...,c]=np.where(holes,out[...,c][idx[0],idx[1]],out[...,c])
out[...,3]=np.where(holes,255,out[...,3])
# smooth the row-wise right edge a touch
alc=Image.fromarray(out[...,3].clip(0,255).astype('uint8'))
from PIL import ImageFilter
out[...,3]=np.array(alc.filter(ImageFilter.MedianFilter(5))).astype(float)
out=despill(out)
im2=Image.fromarray(out.clip(0,255).astype('uint8'),'RGBA').resize((1024,687),Image.LANCZOS)
a2=despill(np.array(im2).astype(float)); a2[...,:3][a2[...,3]==0]=0
Image.fromarray(a2.clip(0,255).astype('uint8'),'RGBA').save('r3fix/flat-new.png')
print('holes',holes.sum())
