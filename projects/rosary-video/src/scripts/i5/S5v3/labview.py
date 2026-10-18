import json, numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
J=json.load(open(P+'scripts/i5/S5v3/work/S5_figs.json'))
f=np.array(Image.open(P+'scripts/i5/S5v3/work/S5_full.png').convert('RGB')).astype(float)
out=f*0.3
C=[(255,60,60),(60,255,60),(60,120,255),(255,255,60),(255,60,255),(60,255,255),(255,150,40)]
for k,fg in enumerate(J['figs']):
    im=np.array(Image.open(P+'pub/'+fg['file'])).astype(float); x,y,w,h=fg['px']
    a=im[...,3:]/255; reg=out[y:y+h,x:x+w]
    out[y:y+h,x:x+w]=reg*(1-a)+(f[y:y+h,x:x+w]*0.5+np.array(C[k])*0.5)*a
    print(k,fg['name'],C[k])
Image.fromarray(out.clip(0,255).astype(np.uint8)).save(P+'scripts/i5/S5v3/work/labels.jpg',quality=85)
