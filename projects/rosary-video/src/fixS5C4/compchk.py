import numpy as np, json, sys
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
full,plate,frontr,bbj,out=sys.argv[1:6]
J=json.load(open(S+'pub/i5/S5.json')); W,H=1376,768
comp=Image.open(plate).convert('RGBA')
for f in J['figs']:
    if f['name']=='frontr':
        im=Image.open(frontr); bb=json.load(open(bbj))['bbox'] if bbj!='-' else f['bbox']
    else:
        im=Image.open(S+'pub/'+f['file']); bb=f['bbox']
    comp.alpha_composite(im.convert('RGBA'),(round(bb[0]*W),round(bb[1]*H)))
c=np.array(comp.convert('RGB')).astype(float); F=np.array(Image.open(full).convert('RGB')).astype(float)
e=np.abs(c-F); print('mean err',e.mean().round(3),'region err',e[400:768,680:940].mean().round(2), 'max local', e.max(2)[400:768,680:940].mean().round(2))
Image.fromarray(np.concatenate([F,c],1).astype(np.uint8)).save(out,quality=85)
Image.fromarray((np.clip(e.max(2)*4,0,255)).astype(np.uint8)).save(out.replace('.jpg','_err.png'))
