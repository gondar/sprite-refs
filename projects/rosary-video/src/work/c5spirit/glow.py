# gentle breath glow pulse on mary_breath.webp: brighter light-robe + slightly fuller halo at the breath peak; ends = exact home
import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
c=json.load(open(S+'i7/cut/C5/cut.json'))['mary']; w,h=c['w'],c['h']
g=[g for g in c['gestures'] if g['name']=='breath'][0]
sh=np.asarray(Image.open('breath_noglow.webp').convert('RGBA')).astype(np.float32)
HOME=np.asarray(Image.open(S+c['home']).convert('RGBA'))
N=g['frames']; out=np.zeros_like(sh)
L=HOME[...,:3].astype(np.float32).mean(2)
lm=np.clip((L-150)/80,0,1); lm=ndi.gaussian_filter(lm,2)          # luminous robe / veil / skin
for k in range(N):
    t=k/(N-1); gg=np.sin(np.pi*t)**2
    fr=sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w].copy()
    if k in (0,N-1): fr=HOME.astype(np.float32)
    else:
        fr[...,:3]+=gg*0.07*lm[...,None]*(255-fr[...,:3])
        a=fr[...,3]; soft=(a>0)&(a<250); fr[...,3]=np.where(soft,np.minimum(255,a*(1+0.10*gg)),a)
    out[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]=fr
Image.fromarray(np.clip(np.round(out),0,255).astype(np.uint8)).save(S+g['file'],'WEBP',quality=80,method=6)
print('ok',N)
