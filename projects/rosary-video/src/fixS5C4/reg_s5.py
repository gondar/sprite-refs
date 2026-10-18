import numpy as np
from PIL import Image
from scipy import ndimage
import sys
SRC=sys.argv[1] if len(sys.argv)>1 else 'ed_s5a_raw.png'
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
o=np.array(Image.open('crop_in.png').convert('RGB')).astype(float)
e0=Image.open(''+SRC+'').convert('RGB')
best=None
# search scale/offset: resize edit to (605*s, 454*s), shift dx,dy; compare in top band (table/people behind) and left floor
H,W=o.shape[:2]
cmpm=np.zeros((H,W),bool); cmpm[:150,:]=True; cmpm[:, :120]=True
for s in [0.99,0.995,1.0,1.005,1.01]:
  for sy in [0.99,0.995,1.0,1.005,1.01,1.015]:
    w,h=round(W*s),round(H*sy)
    e=np.array(e0.resize((w,h),Image.LANCZOS)).astype(float)
    for dx in range(-4,5):
      for dy in range(-4,5):
        # place e at offset (dx,dy) in crop coords
        X0,Y0=max(0,dx),max(0,dy); X1,Y1=min(W,dx+w),min(H,dy+h)
        a=o[Y0:Y1,X0:X1]; b=e[Y0-dy:Y1-dy,X0-dx:X1-dx]; m=cmpm[Y0:Y1,X0:X1]
        err=np.abs(a-b).mean(2)[m].mean()
        if best is None or err<best[0]: best=(err,s,sy,dx,dy)
print(best)
err,s,sy,dx,dy=best
w,h=round(W*s),round(H*sy)
e=np.array(e0.resize((w,h),Image.LANCZOS)).astype(float)
E=o.copy()
X0,Y0=max(0,dx),max(0,dy); X1,Y1=min(W,dx+w),min(H,dy+h)
E[Y0:Y1,X0:X1]=e[Y0-dy:Y1-dy,X0-dx:X1-dx]
np.save('ed_reg.npy',E)
Image.fromarray(E.astype(np.uint8)).save('ed_reg.png')
