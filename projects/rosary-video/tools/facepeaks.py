# python facepeaks.py <id> '{"fig":[x0,y0,x1,y1] (full-image px)}' -> review/<id>/zoom_faces_<fig>.jpg: home + 3 most-changed frames of each gesture in the face box, 2x
import json,sys,numpy as np
from PIL import Image,ImageDraw
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];C=json.load(open(f'{S}/pub/i7/cut/{id}/cut.json'));J=json.load(open(f'{S}/pub/i5/{id}.json'))
bb={f['name']:f['bbox'] for f in J['figs']}
def flat(a):
    a=a.astype(float);return a[...,:3]*a[...,3:]/255+np.array([70,70,70])*(1-a[...,3:]/255)
for fig,box in json.loads(sys.argv[2]).items():
    c=C[fig];w,h=c['w'],c['h'];ox,oy=bb[fig][0]*1376,bb[fig][1]*768
    x0,y0,x1,y1=[int(v) for v in (box[0]-ox,box[1]-oy,box[2]-ox,box[3]-oy)];x0,y0=max(0,x0),max(0,y0);x1,y1=min(w,x1),min(h,y1)
    home=flat(np.asarray(Image.open(f"{S}/pub/{c['home']}").convert('RGBA')))[y0:y1,x0:x1]
    rows=[]
    for g in c['gestures']:
        sh=np.asarray(Image.open(f"{S}/pub/{g['file']}").convert('RGBA'))
        fr=[flat(sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w])[y0:y1,x0:x1] for k in range(g['frames'])]
        d=np.array([np.abs(f-home).mean() for f in fr]);pk=int(d.argmax())
        picks=[0,pk//2,pk,(pk+len(fr)-1)//2,len(fr)-1]
        ims=[home]+[fr[k] for k in picks]
        s=2 if (x1-x0)<260 else 1.3
        tw,th=int((x1-x0)*s),int((y1-y0)*s)
        R=Image.new('RGB',(len(ims)*(tw+3),th+14))
        for k,a in enumerate(ims):R.paste(Image.fromarray(a.clip(0,255).astype('uint8')).resize((tw,th),Image.LANCZOS),(k*(tw+3),14))
        ImageDraw.Draw(R).text((2,1),f'{fig}.{g["name"]}: home | f0 | f{picks[1]} | PEAK f{pk} | f{picks[3]} | last f{len(fr)-1}   faceΔ peak {d[pk]:.1f}',fill=(255,255,0))
        rows.append(R)
    O=Image.new('RGB',(max(r.size[0] for r in rows),sum(r.size[1] for r in rows)));y=0
    for r in rows:O.paste(r,(0,y));y+=r.size[1]
    O.save(f'{S}/review/{id}/zoom_faces_{fig}.jpg',quality=90);print('ok',fig,O.size)
