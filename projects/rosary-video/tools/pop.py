# python pop.py <id> : per figure, per gesture: mean|f0-home|, mean|flast-home|, max over frames of mean|f-home| (alpha-premult, rgb)
import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];C=json.load(open(f'{S}/pub/i7/cut/{id}/cut.json'))
def pm(a):a=a.astype(float);return a[...,:3]*a[...,3:]/255
for fig,c in C.items():
    H=pm(np.asarray(Image.open(f"{S}/pub/{c['home']}").convert('RGBA')));w,h=c['w'],c['h']
    for g in c['gestures']:
        sh=np.asarray(Image.open(f"{S}/pub/{g['file']}").convert('RGBA'))
        fr=[pm(sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]) for k in range(g['frames'])]
        if fr[0].shape!=H.shape: fr=[np.asarray(Image.fromarray(f.astype('uint8')).resize((H.shape[1],H.shape[0]))).astype(float) for f in fr]
        d=[np.abs(f-H).mean() for f in fr];st=[np.abs(fr[k]-fr[k-1]).mean() for k in range(1,len(fr))]
        print(f"{fig:12s} {g['name']:8s} n={g['frames']:2d} w={g.get('weight',1)} fps={g.get('fps')} f0-home {d[0]:.2f} last-home {d[-1]:.2f} peak {max(d):.2f} maxstep {max(st):.2f}")
