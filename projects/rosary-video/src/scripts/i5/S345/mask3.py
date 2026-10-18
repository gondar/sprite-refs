# mask3.py ID T Tlow R : mask2 + low-threshold growth within R px of the strong mask
import sys, numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/scripts/i5/S345/work/'
i=sys.argv[1]; T=float(sys.argv[2]); TL=float(sys.argv[3]); R=int(sys.argv[4])
f=np.array(Image.open(S+f'{i}_full.png').convert('RGB')).astype(float)
p=np.array(Image.open(S+f'{i}_plate.png').convert('RGB')).astype(float)
d=np.abs(ndimage.gaussian_filter(f,(1.5,1.5,0))-ndimage.gaussian_filter(p,(1.5,1.5,0))).max(2)
ds=ndimage.gaussian_filter(d,1.5)
m=ds>T
m=ndimage.binary_closing(m,iterations=5); m=ndimage.binary_fill_holes(m); m=ndimage.binary_opening(m,iterations=4)
lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1)); m=np.isin(lab,[k+1 for k in range(n) if sz[k]>3000])
g=m|(ndimage.binary_dilation(m,iterations=R)&(ndimage.gaussian_filter(d,3)>TL))
g=ndimage.binary_closing(g,iterations=8); g=ndimage.binary_fill_holes(g); g=ndimage.binary_opening(g,iterations=3)
lab,n=ndimage.label(g); sz=ndimage.sum(g,lab,range(1,n+1)); g=np.isin(lab,[k+1 for k in range(n) if sz[k]>3000])
print(i,'strong',m.sum(),'grown',g.sum())
Image.fromarray((g*255).astype(np.uint8)).save(S+f'{i}_mask.png')
ov=f.copy(); ov[~g]*=0.25
Image.fromarray(ov.astype(np.uint8)).save(S+f'{i}_maskov.jpg',quality=85)
