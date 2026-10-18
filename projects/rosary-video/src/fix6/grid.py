import sys,numpy as np,cv2
from PIL import Image
f,x0,y0,x1,y1,out=sys.argv[1],*map(int,sys.argv[2:6]),sys.argv[6]
a=np.asarray(Image.open(f).convert('RGBA')).astype(np.float32); al=a[...,3:]/255
c=(a[...,:3]*al+128*(1-al)).astype(np.uint8)[y0:y1,x0:x1]
Z=16; b=cv2.resize(c,(c.shape[1]*Z,c.shape[0]*Z),interpolation=cv2.INTER_NEAREST)
b=np.pad(b,((20,0),(30,0),(0,0)),constant_values=255).copy()
for x in range(x0,x1):
    if x%5==0:
        cv2.line(b,(30+(x-x0)*Z,20),(30+(x-x0)*Z,b.shape[0]),(0,255,0),1); cv2.putText(b,str(x),(30+(x-x0)*Z,14),0,0.4,(0,0,0),1)
for y in range(y0,y1):
    if y%5==0:
        cv2.line(b,(30,20+(y-y0)*Z),(b.shape[1],20+(y-y0)*Z),(0,255,0),1); cv2.putText(b,str(y),(0,24+(y-y0)*Z),0,0.4,(0,0,0),1)
Image.fromarray(b).save(out)
