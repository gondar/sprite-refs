# python signdiff.py <id> <t> -> review/<id>/zoom_signdiff_<t>.jpg : 128 + 4*(render - painting), plate coords
import json,sys,numpy as np
from PIL import Image
id,t=sys.argv[1],float(sys.argv[2]);d=f'review/{id}/snap';meta=json.load(open(d+'/dm.json'))['meta'];PW,PH=1376,768
m=[m for m in meta if abs(m['t']-t)<1e-6][0];b=m['b']
w=np.asarray(Image.open(d+'/t_%.2f.png'%t).convert('RGB').transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)).astype(float)
f=np.asarray(Image.open(f'pub/i5/{id}_full.jpg').convert('RGB').resize((PW,PH))).astype(float)
D=(w-f).mean(2);Image.fromarray(np.clip(128+D*4,0,255).astype('uint8')).save(f'review/{id}/zoom_signdiff_{t:.1f}.jpg',quality=88);print(id,t,'mean %.2f'%D.mean())
