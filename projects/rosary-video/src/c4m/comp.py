import numpy as np
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
X0,Y0,CS=473,0,480
full=np.asarray(Image.open(S+'/pub/i5/C4_full.jpg').convert('RGB')).astype(np.float32)
O=full[Y0:Y0+CS,X0:X0+CS]; E=np.load('E_bg.npy')
figim=np.asarray(Image.open(S+'/pub/i5/C4_fig_mary.png')).astype(np.float32)
A=np.zeros((CS,CS)); fx,fy=602-X0,26-Y0; A[fy:fy+452,fx:fx+222]=figim[...,3]/255.
D=ndi.gaussian_filter(np.abs(E-O).max(2),2)
ch=D>14
inner=ndi.binary_erosion(A>0.99,iterations=6)
ch&=inner
ch=ndi.binary_closing(ch,iterations=6); ch=ndi.binary_fill_holes(ch)
lab,k=ndi.label(ch); sz=ndi.sum(ch,lab,range(1,k+1)); ch=np.isin(lab,1+np.nonzero(sz>=200)[0])
ch=ndi.binary_dilation(ch,iterations=6)&inner
w=ndi.gaussian_filter(ch.astype(np.float32),3)*(ndi.binary_erosion(A>0.99,iterations=2))
w=np.clip(w*1.5,0,1)
hb=np.zeros((CS,CS),bool)
for (cx,cy) in [(150,278),(312,285)]: hb[cy-32:cy+32,cx-38:cx+38]=True
hw=ndi.gaussian_filter((hb&(D>6)).astype(np.float32),3)
hw=np.clip(ndi.gaussian_filter(ndi.binary_dilation(hb&(D>6),iterations=5).astype(np.float32),2)*1.5,0,1)*(A>0)
w=np.maximum(w,hw)
N=O*(1-w[...,None])+E*w[...,None]
np.save('w.npy',w)
Image.fromarray(N.clip(0,255).astype(np.uint8)).save('newcrop.png')
v=np.hstack([O,N,np.dstack([w*255]*3)])
Image.fromarray(v.clip(0,255).astype(np.uint8)).save('comp_view.jpg')
print('changed px',int((w>0.01).sum()))
