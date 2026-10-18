import numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
cx,cy,cs=816,182,192
f=np.asarray(Image.open('backup/B5_full.jpg').convert('RGB')).astype(np.float32)
C=np.load('C.npy'); m=np.load('mask.npy')
f2=f.copy(); f2[cy:cy+cs,cx:cx+cs]=C
out=np.clip(np.round(f2),0,255).astype(np.uint8)
Image.fromarray(out).save(S+'/pub/i5/B5_full.jpg',quality=92,optimize=True,progressive=True)
dec=np.asarray(Image.open(S+'/pub/i5/B5_full.jpg').convert('RGB')).astype(int)
M=np.zeros(f.shape[:2]); M[cy:cy+cs,cx:cx+cs]=m
print('full: change outside mask (re-encode) mean',np.abs(dec-f)[M<0.01].mean().round(3),'max',np.abs(dec-f)[M<0.01].max())
g=np.asarray(Image.open('backup/B5_fig_mary.png')).copy()
ox,oy=853,235; H,W=g.shape[:2]
sub=out[oy:oy+H,ox:ox+W]; Ms=M[oy:oy+H,ox:ox+W]>0
g[...,:3][Ms]=sub[Ms]
Image.fromarray(g).save(S+'/pub/i5/B5_fig_mary.png')
np.save('Mfig.npy',M[oy:oy+H,ox:ox+W])
print('fig changed px',int((np.abs(g.astype(int)-np.asarray(Image.open('backup/B5_fig_mary.png')).astype(int)).max(2)>0).sum()))
