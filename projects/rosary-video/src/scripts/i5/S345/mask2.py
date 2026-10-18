# usage: mask2.py ID T  -> work/ID_mask.png from |full-plate|: low threshold on edges, close, fill holes
import sys, numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/scripts/i5/S345/work/'
i=sys.argv[1]; T=float(sys.argv[2])
f=np.array(Image.open(S+f'{i}_full.png').convert('RGB')).astype(float)
p=np.array(Image.open(S+f'{i}_plate.png').convert('RGB')).astype(float)
d=np.abs(ndimage.gaussian_filter(f,(1.5,1.5,0))-ndimage.gaussian_filter(p,(1.5,1.5,0))).max(2)
m=ndimage.gaussian_filter(d,1.5)>T
m=ndimage.binary_closing(m,iterations=5)
m=ndimage.binary_fill_holes(m)
m=ndimage.binary_opening(m,iterations=4)
lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1))
print('comps',[int(x) for x in sorted(sz)[::-1][:8]])
keep=[k+1 for k in range(n) if sz[k]>6000]
m=np.isin(lab,keep)
Image.fromarray((m*255).astype(np.uint8)).save(S+f'{i}_mask.png')
ov=f.copy(); ov[~m]*=0.25
Image.fromarray(ov.astype(np.uint8)).save(S+f'{i}_maskov.jpg',quality=85)
