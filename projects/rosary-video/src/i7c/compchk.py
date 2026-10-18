import sys,json,numpy as np
from PIL import Image
i=sys.argv[1]; J=json.load(open('scripts/i5/work/%s_figs.json'%i))
c=Image.open('pub/i5/%s_plate.jpg'%i).convert('RGBA')
for f in J['figs']: c.alpha_composite(Image.open('pub/'+f['file']),tuple(f['px'][:2]))
F=np.asarray(Image.open('pub/i5/%s_full.jpg'%i).convert('RGB')).astype(float)
print(i,'comp vs full mean abs err',np.abs(np.asarray(c.convert('RGB')).astype(float)-F).mean().round(2))
