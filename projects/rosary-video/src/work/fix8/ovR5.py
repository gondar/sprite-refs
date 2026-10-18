# rebuild ov_R5_mary_blink with the tear mask limited to fig y>=67 (ov y>=103)
import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
cx,cy=270,110; b=(80,73,150,117); thr=14
full=np.asarray(Image.open(S+'/pub/i5/R5_full.jpg').convert('RGB')).astype(np.float32)
E=np.asarray(Image.open(S+'/i7r/ed/R5_mary_blink_reg.png').convert('RGB').resize((200,200),Image.LANCZOS)).astype(np.float32)
E=ndi.gaussian_filter(E,(0.5,0.5,0)); O=full[cy:cy+200,cx:cx+200]
x0,y0,x1,y1=b; box=np.zeros((200,200),bool); box[y0:y1,x0:x1]=True
d=np.abs(ndi.gaussian_filter(E,(1,1,0))-ndi.gaussian_filter(O,(1,1,0))).max(2)
ch=(d>thr)&box; ch=ndi.binary_opening(ch,iterations=1)
lab,k=ndi.label(ch); sz=ndi.sum(ch,lab,range(1,k+1)); ch=np.isin(lab,1+np.nonzero(sz>=6)[0])
ch=ndi.binary_dilation(ch,iterations=3)&box
m=np.clip(ndi.gaussian_filter(ch.astype(np.float32),1.3)*1.6,0,1)*box
ring=ndi.binary_dilation(ch,iterations=10)&~ndi.binary_dilation(ch,iterations=2)
wr=ring.astype(np.float32); den=ndi.gaussian_filter(wr,5)+1e-6
for c in range(3): E[...,c]+=ndi.gaussian_filter((O[...,c]-E[...,c])*wr,5)/den
im=np.dstack([np.clip(E,0,255),m*255]).astype(np.uint8).astype(float)
pre=im.copy()
H,W=im.shape[:2]; Y,X=np.mgrid[0:H,0:W]
def tear(im,ymin):
    im=im.copy(); mm=(((X-100)/6.5)**2+((Y-103)/8.5)**2<=1)&(Y>=ymin)
    k=np.clip(ndi.gaussian_filter(mm.astype(float),1.0)*1.5,0,1)
    if ymin>=103: k[Y<ymin-0]=np.minimum(k[Y<ymin],0)  # hard top: nothing above the lower lid line comes from home
    im[...,3]*=1-k; return im,mm.sum()
old,_=tear(pre,96)
cur=np.asarray(Image.open(S+'/i7r/ov_R5_mary_blink.png')).astype(float)
print('rebuild vs current ov (old tear): max abs diff',np.abs(old-cur).max(),'mean',np.abs(old-cur).mean())
new,n=tear(pre,103)
Image.fromarray(new.clip(0,255).astype(np.uint8)).save('ov_R5_mary_blink_new.png'); print('tear px',n)
