# python life.py <snapdir> '{"name":[x0,y0,x1,y1]}'  -> max abs diff vs previous frame per region (plate coords, stabilised)
import json,sys,numpy as np
from PIL import Image
d=sys.argv[1];meta=json.load(open(d+'/dm.json'))['meta'];PW,PH=1376,768
def warp(m):
    b=m['b'];im=Image.open(d+'/t_%.2f.png'%m['t']).convert('RGB')
    return np.asarray(im.transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)).astype(float)
ws=[warp(m) for m in meta]
for nm,(x0,y0,x1,y1) in json.loads(sys.argv[2]).items():
    x0,y0,x1,y1=[int(v) for v in (x0*PW,y0*PH,x1*PW,y1*PH)]
    r=[]
    for k in range(1,len(ws)):
        D=np.abs(ws[k][y0:y1,x0:x1]-ws[k-1][y0:y1,x0:x1]).mean(2)
        r.append('%.1f:%.0f'%(meta[k]['t'],(D>10).sum()))
    print(nm,' '.join(r))
