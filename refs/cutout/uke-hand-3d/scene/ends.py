import numpy as np, sys
from PIL import Image
C={'index':(255,0,0),'middle':(0,255,0),'ring':(0,0,255),'pinky':(255,255,0)}
F={'rest':None,'e1':'index','c1':'index','e2':'middle','c2':'middle','e3':'ring','c3':'ring'}
d=sys.argv[1]
for s in F:
  a=np.asarray(Image.open(f'{d}/{s}-id.png').convert('RGB').resize((1100,619),Image.NEAREST)).astype(int)
  out=[]
  for f,c in C.items():
    m=np.abs(a-c).sum(2)<60; ys,xs=np.nonzero(m); out.append((f[:2],int(xs[ys>ys.max()-6].mean()),int(ys.max())-91))
  print(s,out)
