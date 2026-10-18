# python motionmap.py <id> [t0 t1] -> review/<id>/zoom_motionmap.jpg : per-pixel (max-min) luma over warped frames in [t0,t1], overlay on plate coords
import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];t0,t1=(float(sys.argv[2]),float(sys.argv[3])) if len(sys.argv)>3 else (2.6,8.6)
d=f'{S}/review/{id}/snap';meta=json.load(open(d+'/dm.json'))['meta'];PW,PH=1376,768
def warp(m):
    b=m['b'];im=Image.open(d+'/t_%.2f.png'%m['t']).convert('L')
    return np.asarray(im.transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)).astype(float)
ws=np.array([warp(m) for m in meta if t0<=m['t']<=t1]);R=ws.max(0)-ws.min(0)
full=np.asarray(Image.open(f'{S}/pub/i5/{id}_full.jpg').convert('L').resize((PW,PH))).astype(float)*.5
O=np.stack([np.clip(full+R*3,0,255),full,full],2).astype('uint8')
Image.fromarray(O).save(f'{S}/review/{id}/zoom_motionmap.jpg',quality=88);print('ok')
