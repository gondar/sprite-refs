import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
cx,cy=664,236; ox,oy,ow,oh=777,300,274,373; bx,by,bw,bh=765,282,300,410
full=np.asarray(Image.open('bak/C5_full.jpg')).astype(np.float32)
plate=np.asarray(Image.open(S+'/pub/i5/C5_plate.jpg')).astype(np.float32)
fo=np.asarray(Image.open('bak/C5_fig_mary.png')).astype(np.float32)
aold=np.zeros(full.shape[:2],np.float32); aold[oy:oy+oh,ox:ox+ow]=fo[...,3]/255
B=full*(1-aold[...,None])+plate*aold[...,None]          # scene without Mary
W=np.load(sys.argv[1]+'.reg.npy')                        # new crop 512, registered
HALO=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
Bc=B[cy:cy+512,cx:cx+512]
D=np.abs(ndi.gaussian_filter(W,(1.5,1.5,0))-ndi.gaussian_filter(Bc,(1.5,1.5,0))).max(2)
core=D>30; core=ndi.binary_opening(core,iterations=2)
lab,n=ndi.label(core); sz=ndi.sum(core,lab,range(1,n+1)); core=lab==1+np.argmax(sz)
core|=ndi.binary_erosion(aold[cy:cy+512,cx:cx+512]>0.5,iterations=2)
core=ndi.binary_fill_holes(ndi.binary_closing(core,iterations=4))
near=ndi.binary_dilation(core,iterations=28)
soft=np.clip((D-6)/(30-6),0,1); soft=soft*soft*(3-2*soft)
M=np.where(core,1.0,soft*HALO)*near
M=ndi.gaussian_filter(M,1.0); M[ndi.binary_erosion(core,iterations=2)]=1
# keep inside the figure box, fading over 10 px at its edges
Mf=np.zeros(full.shape[:2],np.float32); Mf[cy:cy+512,cx:cx+512]=M
Y,X=np.mgrid[0:768,0:1376]
edge=np.minimum.reduce([X-bx,bx+bw-1-X,Y-by,by+bh-1-Y]).astype(np.float32)
Mf*=np.clip(edge/10,0,1)
Wf=full.copy(); Wf[cy:cy+512,cx:cx+512]=W
new=B*(1-Mf[...,None])+Wf*Mf[...,None]
ys,xs=np.nonzero(Mf>0.02); print('M bbox',xs.min(),ys.min(),xs.max(),ys.max())
# edge leak check: how much the uncut mask was clipped by the box
Mu=np.zeros_like(Mf); Mu[cy:cy+512,cx:cx+512]=M; print('mask mass clipped by box',round(float((Mu-Mf).sum()/Mu.sum()),4))
Image.fromarray(np.clip(np.round(new),0,255).astype(np.uint8)).save(S+'/pub/i5/C5_full.jpg',quality=95)
fig=np.dstack([Wf[by:by+bh,bx:bx+bw],Mf[by:by+bh,bx:bx+bw]*255])
Image.fromarray(np.clip(np.round(fig),0,255).astype(np.uint8)).save(S+'/pub/i5/C5_fig_mary.png')
# checks
full2=np.asarray(Image.open(S+'/pub/i5/C5_full.jpg')).astype(np.float32)
f2=np.asarray(Image.open(S+'/pub/i5/C5_fig_mary.png')).astype(np.float32)
comp=plate.copy(); a=f2[...,3:]/255; comp[by:by+bh,bx:bx+bw]=comp[by:by+bh,bx:bx+bw]*(1-a)+f2[...,:3]*a
print('composite vs full mean err',round(float(np.abs(comp-full2).mean()),3))
out=(Mf==0)&(aold==0); print('outside old+new figure: max change vs old full',np.abs(full2-full)[out].max(), 'mean',np.abs(full2-full)[out].mean().round(3))
