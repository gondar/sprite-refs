# python wcmp.py <id> <t> x0,y0,x1,y1 (full px 1376x768) scale out  -> painting | render(warped) | signed diff
import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id,t=sys.argv[1],float(sys.argv[2]);bx=tuple(map(int,sys.argv[3].split(',')));sc=float(sys.argv[4]);out=sys.argv[5]
d=f'{S}/review/{id}/snap';m=[m for m in json.load(open(d+'/dm.json'))['meta'] if abs(m['t']-t)<1e-6][0];b=m['b'];PW,PH=1376,768
w=Image.open(d+'/t_%.2f.png'%t).convert('RGB').transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)
f=Image.open(f'{S}/pub/i5/{id}_full.jpg').convert('RGB').resize((PW,PH))
D=np.asarray(w).astype(float).mean(2)-np.asarray(f).astype(float).mean(2)
dd=Image.fromarray(np.clip(128+D*4,0,255).astype('uint8')).convert('RGB')
ims=[i.crop(bx) for i in (f,w,dd)];ims=[i.resize((int(i.width*sc),int(i.height*sc)),Image.LANCZOS) for i in ims]
O=Image.new('RGB',(sum(i.width+4 for i in ims),ims[0].height));x=0
for i in ims:O.paste(i,(x,0));x+=i.width+4
O.save(out,quality=92);print(O.size)
