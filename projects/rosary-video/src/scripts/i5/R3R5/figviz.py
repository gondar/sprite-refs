# figviz.py ID : tinted figure map + layers_check to review/ID/
import sys, json, numpy as np, os
from PIL import Image
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
i=sys.argv[1]; W,H=1376,768
J=json.load(open(B+f'scripts/i5/work/{i}_figs.json'))
f=np.asarray(Image.open(B+f'pub/i5/{i}_full.jpg').convert('RGB')).astype(float)
pl=np.asarray(Image.open(B+f'pub/i5/{i}_plate.jpg').convert('RGB')).astype(float)
cols=[(255,60,60),(60,120,255),(60,255,90),(255,230,40),(255,60,255),(40,240,240)]
tint=f*0.35; comp=Image.fromarray(pl.astype(np.uint8)).convert('RGBA')
for k,fg in enumerate(J['figs']):
    im=Image.open(B+'pub/'+fg['file']); x,y,w,h=fg['px']; a=np.asarray(im)[...,3:]/255.
    reg=tint[y:y+h,x:x+w]; tint[y:y+h,x:x+w]=reg*(1-a*0.8)+(f[y:y+h,x:x+w]*0.5+np.array(cols[k%6])*0.5)*a*0.8
    comp.alpha_composite(im,(x,y))
comp=np.asarray(comp.convert('RGB')).astype(float)
err=np.abs(comp-f).mean(); print(i,'composite vs full mean abs err',round(err,3))
os.makedirs(B+f'review/{i}',exist_ok=True)
top=np.concatenate([f,comp],1); bot=np.concatenate([pl,tint],1)
Image.fromarray(np.concatenate([top,bot],0).clip(0,255).astype(np.uint8)).resize((1600,894)).save(B+f'review/{i}/layers_check.jpg',quality=84)
