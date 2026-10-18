# python bright.py <id> '{"name":[x0,y0,x1,y1]}' (full-image px 1376x768) -> mean luma full vs rendered frames (warped)
import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];d=f'{S}/review/{id}/snap';meta=json.load(open(d+'/dm.json'))['meta'];PW,PH=1376,768
full=np.asarray(Image.open(f'{S}/pub/i5/{id}_full.jpg').convert('L').resize((PW,PH))).astype(float)
def warp(m):
    b=m['b'];im=Image.open(d+'/t_%.2f.png'%m['t']).convert('L')
    return np.asarray(im.transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)).astype(float)
ts=[m for m in meta if 3.0<=m['t']<=8.6]
ws=[warp(m) for m in ts]
for nm,(x0,y0,x1,y1) in json.loads(sys.argv[2]).items():
    f=full[y0:y1,x0:x1].mean(); r=[w[y0:y1,x0:x1].mean() for w in ws]
    print('%-10s full %.1f  render min %.1f mean %.1f max %.1f'%(nm,f,min(r),np.mean(r),max(r)))
