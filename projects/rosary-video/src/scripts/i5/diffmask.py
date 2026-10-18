# usage: diffmask.py ID  -> work/ID_diff.png, work/ID_mask.png (fallback mask from |full-plate|)
import sys, numpy as np
from PIL import Image
from scipy import ndimage
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
i=sys.argv[1]; T=float(sys.argv[2]) if len(sys.argv)>2 else 40
f=np.array(Image.open(S+f'scripts/i5/work/{i}_full.png').convert('RGB')).astype(float)
p=np.array(Image.open(S+f'scripts/i5/work/{i}_plate.png').convert('RGB').resize(f.shape[1::-1],Image.LANCZOS)).astype(float)
# global alignment check: best integer shift
g1=ndimage.gaussian_filter(f.mean(2),2); g2=ndimage.gaussian_filter(p.mean(2),2)
best=None
for dy in range(-6,7,2):
  for dx in range(-6,7,2):
    e=np.median(np.abs(g1[20:-20,20:-20]-np.roll(g2,(dy,dx),(0,1))[20:-20,20:-20]))
    if best is None or e<best[0]: best=(e,dy,dx)
print('shift',best)
d=np.abs(ndimage.gaussian_filter(f,(2,2,0))-ndimage.gaussian_filter(p,(2,2,0))).max(2)
Image.fromarray(np.clip(d*2,0,255).astype(np.uint8)).save(S+f'scripts/i5/work/{i}_diff.png')
m=ndimage.gaussian_filter(d,3)>T
m=ndimage.binary_opening(m,iterations=3)
lab,n=ndimage.label(m); sz=ndimage.sum(m,lab,range(1,n+1))
keep=[k+1 for k in np.argsort(sz)[::-1] if sz[k]>4000]
print('comps',sorted(sz)[::-1][:8])
m=np.isin(lab,keep); m=ndimage.binary_closing(m,iterations=8); m=ndimage.binary_fill_holes(m)
Image.fromarray((m*255).astype(np.uint8)).save(S+f'scripts/i5/work/{i}_mask.png')
