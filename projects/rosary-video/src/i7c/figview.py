# figview.py ID : colour each figure layer over the dimmed full image -> i7c/fv_ID.jpg
import sys,json,numpy as np
from PIL import Image
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
i=sys.argv[1]; J=json.load(open(B+'scripts/i5/work/%s_figs.json'%i))
f=np.asarray(Image.open(B+'pub/i5/%s_full.jpg'%i).convert('RGB')).astype(float); out=f*0.35
C=[(255,60,60),(60,120,255),(60,220,60),(255,200,40),(220,60,255)]
for k,g in enumerate(J['figs']):
    im=np.asarray(Image.open(B+'pub/'+g['file'])).astype(float); x,y,w,h=g['px']; a=im[...,3:]/255
    reg=out[y:y+h,x:x+w]; out[y:y+h,x:x+w]=reg*(1-a)+(im[...,:3]*0.55+np.array(C[k%5])*0.45)*a
Image.fromarray(out.clip(0,255).astype(np.uint8)).save(B+'i7c/fv_%s.jpg'%i,quality=85)
