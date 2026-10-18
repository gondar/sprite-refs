import sys,json,numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
J=json.load(open('jobs.json'))
for job in sys.argv[1:]:
    h=np.asarray(Image.open(P+J[job]['home']).convert('RGBA')).astype(float); f=np.asarray(Image.open(job+'_closed.png').convert('RGBA')).astype(float)
    m=(f[...,3]>200)&(h[...,3]>200); lum=(f[...,:3]-h[...,:3]).mean(-1); H,W=lum.shape; bs=max(8,min(H,W)//12); mx=0;at=None
    for y in range(0,H-bs,bs//2):
        for x in range(0,W-bs,bs//2):
            mm=m[y:y+bs,x:x+bs]
            if mm.mean()>0.9:
                v=lum[y:y+bs,x:x+bs][mm].mean()
                if abs(v)>abs(mx): mx,at=v,(x,y)
    print(job,'shift',round(mx,1),'at',at,'bs',bs)
