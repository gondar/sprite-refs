# python eyepk.py <id> <fig> x0,y0,x1,y1 (full px) scale out : every gesture: home + peak (by box diff) + 2 neighbours, scaled
import json,sys,numpy as np
from PIL import Image,ImageDraw
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id,fig=sys.argv[1],sys.argv[2];box=[int(v) for v in sys.argv[3].split(',')];sc=float(sys.argv[4]);out=sys.argv[5]
C=json.load(open(f'{S}/pub/i7/cut/{id}/cut.json'))[fig];J=json.load(open(f'{S}/pub/i5/{id}.json'))
bb=[f['bbox'] for f in J['figs'] if f['name']==fig][0];ox,oy=bb[0]*1376,bb[1]*768;w,h=C['w'],C['h']
x0,y0,x1,y1=int(box[0]-ox),int(box[1]-oy),int(box[2]-ox),int(box[3]-oy)
def flat(a):a=a.astype(float);return a[...,:3]*a[...,3:]/255+70*(1-a[...,3:]/255)
home=flat(np.asarray(Image.open(f"{S}/pub/{C['home']}").convert('RGBA')))[y0:y1,x0:x1]
rows=[]
for g in C['gestures']:
    sh=np.asarray(Image.open(f"{S}/pub/{g['file']}").convert('RGBA'))
    fr=[flat(sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w])[y0:y1,x0:x1] for k in range(g['frames'])]
    d=np.array([np.abs(f-home).mean() for f in fr]);pk=int(d.argmax())
    ks=[max(0,pk-2),pk,min(len(fr)-1,pk+2)]
    ims=[home]+[fr[k] for k in ks]
    tw,th=int((x1-x0)*sc),int((y1-y0)*sc)
    R=Image.new('RGB',(len(ims)*(tw+3),th+12))
    for k,a in enumerate(ims):R.paste(Image.fromarray(a.clip(0,255).astype('uint8')).resize((tw,th),Image.LANCZOS),(k*(tw+3),12))
    ImageDraw.Draw(R).text((2,0),f'{g["name"]} home|f{ks[0]}|PEAK f{pk}|f{ks[2]}',fill=(255,255,0));rows.append(R)
O=Image.new('RGB',(max(r.size[0] for r in rows),sum(r.size[1] for r in rows)));y=0
for r in rows:O.paste(r,(0,y));y+=r.size[1]
O.save(out,quality=92);print(O.size)
