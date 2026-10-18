import numpy as np,sys
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
fp=sys.argv[1] if len(sys.argv)>1 else S+'pub/i5/B5_full.jpg'
full=np.asarray(Image.open(fp).convert('RGB')).astype(np.float32)
c=np.asarray(Image.open(S+'pub/i5/B5_plate.jpg').convert('RGB')).astype(np.float32).copy()
for fn,(x,y) in [('B5_fig_mary.png',(853,235)),('B5_fig_john.png',(949,205))]:
    g=np.asarray(Image.open(S+'pub/i5/'+fn)).astype(np.float32); h,w=g.shape[:2]; a=g[...,3:]/255
    c[y:y+h,x:x+w]=c[y:y+h,x:x+w]*(1-a)+g[...,:3]*a
e=np.abs(c-full); print(fp.split('/')[-1],'mean err',e.mean().round(3),'face region',e[230:330,860:960].mean().round(3))
