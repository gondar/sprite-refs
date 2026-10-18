import json,numpy as np,sys
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
base=sys.argv[1] if len(sys.argv)>1 else P+'pub/'
c=json.load(open(P+'pub/i7/cut/B5/cut.json'))['mary']; w,h=c['w'],c['h']
H=np.asarray(Image.open(base+c['home'].replace('i7/cut/B5/','i7/cut/B5/') if base.endswith('pub/') else base+'mary_home.png')).astype(int)
for g in c['gestures']:
    f=base+g['file'] if base.endswith('pub/') else base+g['file'].split('/')[-1]
    im=Image.open(f); sh=np.asarray(im.convert('RGBA')).astype(int)
    fr=[sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w] for k in range(g['frames'])]
    e=[np.abs(x-H).max() for x in fr]; m=[round(np.abs(x-H).mean(),3) for x in fr]
    print(g['name'],'lossless' if im.info.get('lossless') else '', 'maxdiff per frame',e[:16])
