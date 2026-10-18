# cmp.py a.png b.png x0 y0 x1 y1 out [Z]  -- side by side bicubic, no grid
import sys,numpy as np,cv2
from PIL import Image
a,b=sys.argv[1:3]; x0,y0,x1,y1=map(int,sys.argv[3:7]); out=sys.argv[7]; Z=int(sys.argv[8]) if len(sys.argv)>8 else 8
fl=lambda p:(lambda q:(q[...,:3]*q[...,3:]/255+128*(1-q[...,3:]/255)).astype(np.uint8))(np.asarray(Image.open(p).convert('RGBA')).astype(np.float32))
t=[cv2.resize(fl(p)[y0:y1,x0:x1],((x1-x0)*Z,(y1-y0)*Z),interpolation=cv2.INTER_CUBIC) for p in (a,b)]
Image.fromarray(np.concatenate([t[0],np.full((t[0].shape[0],4,3),255,np.uint8),t[1]],1)).save(out)
